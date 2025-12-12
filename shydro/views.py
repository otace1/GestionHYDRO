import base64
import datetime
import io
import json
import uuid
from datetime import date

import pandas as pd
from celery.result import AsyncResult
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, Sum, Prefetch, Value, Max, OuterRef, Subquery, Count
from django.db.models.fields import CharField
from django.db.models.functions import Round, Coalesce, Cast
from django.forms import FloatField
from django.http import JsonResponse
from django.shortcuts import render, redirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport
from django_tables2.paginators import LazyPaginator
from openpyxl import Workbook
from django.utils import timezone

from accounts.models import *
from enreg.uploadToStorage import download_file_from_space
from entrepot.calculs import densite15, vcf, gsv, mta
from hydrocarbures.celery import app
from shydro.utils import render_to_pdf
from .forms import *
from .numact import num_cert_inspection
# from .numact import numeroactcurrent
from .numdossier import numDossier
from .tables import *

from django.core.cache import cache
import hashlib


# Class de gestion des codifacations des cargaisons
class GestionCodification():

    @login_required(login_url='login')
    def affichageTableau(request):
        user = request.user
        id = user.id
        role = user.role_id

        if role == 7 or role == 1 or role == 11:
            template = 'shydro.html'

            e = Cargaison.objects.filter(
                etat="En attente d'echantillonage",
                entrepot__ville__affectationville__username_id=id
            ).count()

            d = ImpressionResultat.objects.filter(
                idcargaison__etat="Conforme aux exigences",
                idcargaison__entrepot__ville__affectationville__username_id=id
            ).count()

            l = Cargaison.objects.filter(
                etat="Analyse Labo en cours",
                entrepot__ville__affectationville__username_id=id
            ).count()

            n = ImpressionResultat.objects.filter(
                idcargaison__entrepot__ville__affectationville__username_id=id,
                isConforme=0, control=0
            ).count()

            p = Entrepot_echantillon.objects.filter(
                idcargaison__etat='Echantillonner',
                idcargaison__entrepot__ville__affectationville__username_id=id
            ).count()

            c = Cargaison.objects.filter(
                entrepot__ville__affectationville__username_id=id
            ).count()

            i = Cargaison.objects.filter(
                etatInspection=1,
                entrepot__ville__affectationville__username_id=id
            ).count()

            context = {'e': e, 'd': d, 'l': l, 'n': n, 'p': p, 'c': c, 'i': i}
            return render(request, template, context)

        return render(request, 'shydro.html', {})  # fallback


    @login_required(login_url='login')
    def responseAffichageTableau(request):
        user = request.user
        uid = user.id

        # -----------------------------
        # BASE QUERYSET
        # -----------------------------
        base_qs = Cargaison.objects.filter(
            etat="En attente requisition",
            entrepot__ville__affectationville__username_id=uid
        )

        # -----------------------------
        # CACHE: recordsTotal (longer TTL)
        # -----------------------------
        total_cache_key = f"carg_table:records_total:u{uid}"
        records_total = cache.get(total_cache_key)
        if records_total is None:
            records_total = base_qs.count()
            cache.set(total_cache_key, records_total, timeout=120)

        # -----------------------------
        # VALUES QUERYSET (include FRONTIERE and related ones for extra columns)
        # -----------------------------
        # Local import for aggregations (keeps global imports untouched)
        from django.db.models import Sum, Avg

        qs = base_qs.select_related(
            'importateur',
            'entrepot',
            'produit',
            'frontiere',
            # one-to-one reverse relations
            'inspection',  # Cargaison -> Inspection
            'entrepot_echantillon',  # Cargaison -> Entrepot_echantillon
            'entrepot_echantillon__laboreception',  # -> LaboReception
            'entrepot_echantillon__laboreception__resultat',  # -> Resultat
            'entrepot_echantillon__laboreception__resultat__dechargement',  # -> Dechargement
        ).annotate(
            # Inspection-based aggregates from Compartiments
            vcf_ins=Avg('inspection__compartiment__vcf'),
            mta_ins=Sum('inspection__compartiment__mta'),
            mtv_ins=Sum('inspection__compartiment__mtv'),
            gsv_ins=Sum('inspection__compartiment__gsv'),
        ).values(
            'idcargaison',
            'dateheurecargaison',
            'dateheurecargaison__date',
            'frontiere__nomville',
            'importateur__nomimportateur',
            'entrepot__nomentrepot',
            'produit__nomproduit',
            'volume',
            'immatriculation',
            'declaration',
            'numreq',
            # extra raw fields for display/computed columns
            'requisitiondackdate',  # requisition date
            'entrepot_echantillon__dateechantillonage',
            'entrepot_echantillon__laboreception__datereceptionlabo',
            'entrepot_echantillon__laboreception__resultat__dateanalyse',
            'inspection__dateinspection',
            'inspection__dens',
            'entrepot_echantillon__laboreception__resultat__dechargement__datedechargement',
            # volumetrics
            'entrepot_echantillon__laboreception__resultat__dechargement__govjaugee',
            'entrepot_echantillon__laboreception__resultat__massevolumique15',
            'inspection__temp',
            # inspection-based aggregates (annotated above)
            'vcf_ins',
            'mta_ins',
            'mtv_ins',
            'gsv_ins',
        )

        # -----------------------------
        # ADVANCED FILTERS (from modal)
        # -----------------------------
        flt_date_from = request.GET.get('flt_date_from', '').strip()
        flt_date_to = request.GET.get('flt_date_to', '').strip()
        flt_frontiere = request.GET.get('flt_frontiere', '').strip()
        flt_importateur = request.GET.get('flt_importateur', '').strip()
        flt_entrepot = request.GET.get('flt_entrepot', '').strip()
        flt_produit = request.GET.get('flt_produit', '').strip()
        flt_immat = request.GET.get('flt_immat', '').strip()
        flt_declaration = request.GET.get('flt_declaration', '').strip()
        flt_numdos = request.GET.get('flt_numdos', '').strip()

        if flt_date_from:
            qs = qs.filter(dateheurecargaison__date__gte=flt_date_from)
        if flt_date_to:
            qs = qs.filter(dateheurecargaison__date__lte=flt_date_to)
        if flt_frontiere:
            qs = qs.filter(frontiere__nomville=flt_frontiere)
        if flt_importateur:
            qs = qs.filter(importateur__nomimportateur=flt_importateur)
        if flt_entrepot:
            qs = qs.filter(entrepot__nomentrepot=flt_entrepot)
        if flt_produit:
            qs = qs.filter(produit__nomproduit=flt_produit)
        if flt_immat:
            qs = qs.filter(immatriculation__icontains=flt_immat)
        if flt_declaration:
            qs = qs.filter(declaration__icontains=flt_declaration)
        if flt_numdos:
            qs = qs.filter(numreq__icontains=flt_numdos)

        # -----------------------------
        # GLOBAL SEARCH (datatables)
        # -----------------------------
        search_value = request.GET.get('search[value]', '').strip()
        search_key = hashlib.md5(search_value.lower().encode("utf-8")).hexdigest() if search_value else "_"

        if search_value:
            qs = qs.filter(
                Q(dateheurecargaison__date__icontains=search_value) |
                Q(frontiere__nomville__icontains=search_value) |
                Q(importateur__nomimportateur__icontains=search_value) |
                Q(entrepot__nomentrepot__icontains=search_value) |
                Q(produit__nomproduit__icontains=search_value) |
                Q(volume__icontains=search_value) |
                Q(immatriculation__icontains=search_value) |
                Q(declaration__icontains=search_value) |
                Q(numreq__icontains=search_value)
            )

        # -----------------------------
        # ORDERING (match your 22 columns)
        # NOTE: Keep ONLY orderable fields here.
        # -----------------------------
        dt_columns_to_fields = [
            'dateheurecargaison__date',         # 0 DATE ENTREE
            'frontiere__nomville',              # 1 FRONTIERE
            'importateur__nomimportateur',      # 2 FOURNISSEUR
            'entrepot__nomentrepot',            # 3 ENTREPOT
            'produit__nomproduit',              # 4 PRODUIT
            'volume',                           # 5 VOL.DECL.
            'immatriculation',                  # 6 IMMATR.
            'declaration',                      # 7 #.DECLARATION
            'numreq',                           # 8 #.DOSSIER

            # The next columns exist in your HTML but may not exist in your model.
            # If they exist, add them here and include them in values() above.
            # 'daterequisition',                 # 9
            # 'dateechantillonnage',             # 10
            # 'datereceptionlabo',               # 11
            # 'dateanalyse',                     # 12
            # 'dateinspection',                  # 13
            # 'datedechargement',                # 14
            # 'voljauge_gov',                    # 15
            # 'densite_15',                      # 16
            # 'temperature',                     # 17
            # 'vcf',                             # 18
            # 'mta',                             # 19
            # 'mtv',                             # 20
            # 'gsv',                             # 21
        ]

        order_by_fields = []
        order_idx = 0
        while True:
            col_key = f'order[{order_idx}][column]'
            dir_key = f'order[{order_idx}][dir]'
            if col_key not in request.GET:
                break

            try:
                col_index = int(request.GET.get(col_key))
            except (TypeError, ValueError):
                order_idx += 1
                continue

            order_dir = request.GET.get(dir_key, 'asc')

            if 0 <= col_index < len(dt_columns_to_fields):
                field_name = dt_columns_to_fields[col_index]
                if order_dir == 'desc':
                    field_name = f'-{field_name}'
                order_by_fields.append(field_name)

            order_idx += 1

        # SAFE default ordering (no missing joins)
        default_ordering = ['-dateheurecargaison__date']

        qs = qs.order_by(*(order_by_fields or default_ordering))

        # -----------------------------
        # recordsFiltered (cached longer)
        # include filters in cache key so it doesn't lie
        # -----------------------------
        filters_sig = "|".join([
            search_key,
            flt_date_from, flt_date_to, flt_frontiere, flt_importateur,
            flt_entrepot, flt_produit, flt_immat, flt_declaration, flt_numdos
        ])
        filters_hash = hashlib.md5(filters_sig.encode("utf-8")).hexdigest()

        filtered_cache_key = f"carg_table:records_filtered:u{uid}:f{filters_hash}"
        records_filtered = cache.get(filtered_cache_key)
        if records_filtered is None:
            records_filtered = qs.count()
            cache.set(filtered_cache_key, records_filtered, timeout=120)

        # -----------------------------
        # PAGINATION (clamp to 20)
        # -----------------------------
        draw = int(request.GET.get('draw', 1))
        try:
            start = int(request.GET.get('start', 0))
        except (TypeError, ValueError):
            start = 0
        try:
            length = int(request.GET.get('length', 20))
        except (TypeError, ValueError):
            length = 20

        if length <= 0:
            length = 20
        if length > 20:
            length = 20

        end = start + length

        # -----------------------------
        # PAGE CACHE (include ordering + filters + window)
        # -----------------------------
        order_key = ",".join(order_by_fields) if order_by_fields else ",".join(default_ordering)
        page_sig = f"{filters_hash}|{order_key}|{start}|{length}"
        page_hash = hashlib.md5(page_sig.encode("utf-8")).hexdigest()

        page_cache_key = f"carg_table:page:u{uid}:k{page_hash}"
        data = cache.get(page_cache_key)

        # -----------------------------
        # BUILD RESPONSE DATA
        # -----------------------------
        def _fmt_dt(val):
            try:
                if val is None:
                    return ""
                if isinstance(val, datetime.datetime):
                    if timezone.is_aware(val):
                        val = timezone.localtime(val)
                    return val.strftime('%d/%m/%Y %H:%M')
                if isinstance(val, datetime.date):
                    return val.strftime('%d/%m/%Y')
            except Exception:
                return ""
            return str(val)

        def _round3(v):
            try:
                if v is None:
                    return ''
                return round(float(v), 3)
            except Exception:
                return ''

        def _to_float(v):
            try:
                if v is None:
                    return None
                if isinstance(v, (int, float)):
                    return float(v)
                s = str(v).strip().replace(',', '.')
                return float(s) if s else None
            except Exception:
                return None

        if data is None:
            rows = list(qs[start:end])
            data = []
            for row in rows:
                row = dict(row)
                dt_full = row.get('dateheurecargaison')
                dt_date = row.get('dateheurecargaison__date')
                row['date_entree_display'] = _fmt_dt(dt_full) or _fmt_dt(dt_date)

                # Populate additional display fields
                row['date_requisition_display'] = _fmt_dt(row.get('requisitiondackdate'))
                row['date_echantillonnage_display'] = _fmt_dt(row.get('entrepot_echantillon__dateechantillonage'))
                row['date_reception_labo_display'] = _fmt_dt(row.get('entrepot_echantillon__laboreception__datereceptionlabo'))
                row['date_analyse_display'] = _fmt_dt(row.get('entrepot_echantillon__laboreception__resultat__dateanalyse'))
                row['date_inspection_display'] = _fmt_dt(row.get('inspection__dateinspection'))
                row['date_dechargement_display'] = _fmt_dt(row.get('entrepot_echantillon__laboreception__resultat__dechargement__datedechargement'))

                # Volumetric/computed columns with safe rounding
                row['vol_jauge_gov'] = row.get('entrepot_echantillon__laboreception__resultat__dechargement__govjaugee') or ''
                # densite @15: compute from inspection dens + temp when possible, else fall back to labo value
                insp_dens = _to_float(row.get('inspection__dens'))
                temp_val = _to_float(row.get('inspection__temp'))
                d15_val = None
                try:
                    if insp_dens is not None and temp_val is not None:
                        # calculs.densite15 expects (temperature, density_at_ambient)
                        d15_val = densite15(temp_val, insp_dens)
                except Exception:
                    d15_val = None
                if d15_val is None:
                    d15_val = _to_float(row.get('entrepot_echantillon__laboreception__resultat__massevolumique15'))
                row['densite_15'] = _round3(d15_val)
                # alias for base template
                row['densite15'] = row['densite_15']
                # prefer Inspection temperature if present
                row['temperature'] = _round3(temp_val)
                # alias for base template which binds directly to inspection__temp
                row['inspection__temp'] = temp_val
                # vcf/mta/mtv/gsv must come from Inspection -> Compartiments aggregates
                row['vcf'] = _round3(row.get('vcf_ins'))
                row['mta'] = _round3(row.get('mta_ins'))
                row['mtv'] = _round3(row.get('mtv_ins'))
                row['gsv'] = _round3(row.get('gsv_ins'))

                # Additional aliases expected by the other template variant
                # dates: provide both verbose and short keys
                row['date_echant_display'] = row.get('date_echantillonnage_display')
                row['date_recep_labo_display'] = row.get('date_reception_labo_display')
                # vol jauge alias
                row['vol_jauge'] = row.get('vol_jauge_gov')
                # dossier number alias (fallback numreq -> numdos key if missing)
                if 'numdos' not in row or row.get('numdos') in (None, ''):
                    row['numdos'] = row.get('numreq')

                data.append(row)

            cache.set(page_cache_key, data, timeout=120)

        return JsonResponse({
            'data': data,
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
        })


# Fonction numrequisition
@login_required(login_url='login')
def numreq(request):
    # url = request.session['url']
    user = request.user
    role = user.role_id
    if role == 7 or role == 1 or role == 11:
        if request.method == 'POST':
            data = json.loads(request.body)
            numreq = data.get('jsonData')
            pk = data.get('idcargaison')
            c = Cargaison.objects.get(idcargaison=pk)
            numreq = numreq.upper()

            # Get Town du point de dechargement pour l'attribution automatique des numeros
            # c = Cargaison.objects.get(idcargaison=pk)
            e = c.entrepot_id
            e = Entrepot.objects.get(identrepot=e)
            ville = e.ville_id

            td = datetime.datetime.now()
            name = MyUser.objects.get(id=user.id)
            name = name.username

            # Numerotation auto des Dossier
            numDos = numDossier(ville, int(pk))

            c.numdos = numDos
            c.numreq = numreq
            c.requisitiondackdate = td
            c.requisitionack = name
            c.etat = "En attente d'echantillonage"
            c.save(update_fields=['numreq', 'requisitiondackdate', 'requisitionack', 'numdos', 'etat'])

            UserActivityLog.objects.create(
                user=user,
                action="Control order data creation",
                description=f"User has authorize a control on the record {c.idcargaison}",
            )

            context = {
                'num': c.numdos
            }

            return JsonResponse(context)
        else:
            return JsonResponse({'error': 'Invalid request method'}, status=400)
    else:
        return redirect('logout')


# Fonction codecam
@login_required(login_url='login')
def codecam(request, pk):
    user = request.user
    id = user.id
    role = user.role_id
    url = request.session['url']
    if role == 7 or role == 1:
        if request.method == 'POST':
            codecargaison = request.POST['codecargaison']
            c = Cargaison.objects.get(pk=pk)
            c.codecargaison = codecargaison
            c.save(update_fields=['codecargaison'])
            return redirect(url)
        else:
            return redirect(url)
    else:
        return redirect('logout')


# Methode pour la codification d'une cargaison
@login_required(login_url='login')
def lineupdate(request, pk):
    url = request.session['url']
    user = request.user
    id = user.id
    name = MyUser.objects.get(id=id)
    name = name.username

    # Get Town du point de dechargement pour l'attribution automatique des numeros
    c = Cargaison.objects.get(idcargaison=pk)
    c = c.entrepot_id
    c = Entrepot.objects.get(identrepot=c)
    ville = c.ville_id

    print(ville)
    # ville = AffectationVille.objects.get(username_id=id)
    # ville = ville.ville_id
    role = user.role_id
    td = datetime.datetime.now()
    if role == 7 or role == 1:
        c = Cargaison.objects.get(idcargaison=pk)
        c.numdos = numDossier(pk, ville)
        c.requisitiondackdate = td
        c.requisitionack = name
        c.etat = "En attente d'echantillonage"
        c.save(update_fields=['requisitiondackdate', 'requisitionack', 'numdos', 'etat'])
        return redirect(url)
    else:
        return redirect('logout')


# Methode pour l'affichage des details d'un ligne
@login_required(login_url='login')
def linedetails(request, pk):
    user = request.user
    id = user.id
    role = user.role_id
    if role == 7 or role == 1:
        a = Cargaison.objects.get(pk=pk)
        return render(request, 'shydroview.html')
    else:
        return redirect('logout')


# Gestion des Go apres avoir obtenu le statut de la cargaison
class GestionResultatLabo():
    # Methode pour l'affichage des resultats venant Labo conforme
    @login_required(login_url='login')
    def affichagetableauresultat(request):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 7 or role == 1:
            table = ResultatGoLabo(Cargaison.objects.raw('SELECT c.idcargaison,r.dateanalyse, c.importateur_id ,c.immatriculation, c.entrepot_id, c.immatriculation, c.produit_id, c.numdossier, c.codecargaison, c.conformite \
                                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_resultat r,  hydro_occ.accounts_affectationville a \
                                                          WHERE c.idcargaison = r.idcargaison_id \
                                                          AND c.frontiere_id = a.ville_id \
                                                          AND a.username_id = %s \
                                                          AND c.etat = "Conforme aux exigences" \
                                                          ORDER BY r.dateanalyse DESC', [id, ]))

            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            return render(request, 'shydro_result.html', {'cargaison': table})
        else:
            return redirect('logout')

    # Methode pour l'affichage des resultats venant du Labo Avarie
    @login_required(login_url='login')
    def affichageNonConforme(request):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 7 or role == 1:
            qs1 = Entrepot_echantillon.objects.filter(idcargaison__etat="Non conforme aux exigences",
                                                      idcargaison__entrepot__ville__affectationville__username=id,
                                                      idcargaison__impressionresultat__isConforme=0,
                                                      idcargaison__impressionresultat__control=0)

            # table = NonConformeOrganoleptique(qs)
            table1 = NonConformeLaboratoire(qs1)
            # RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table1)
            context = {
                # 'table': table,
                'table1': table1,
            }
            return render(request, 'shydro_avarie.html', context)
        else:
            return redirect('logout')


# Class pour la gestion des dechargements
class GestionDecharger():
    # Methode pour l'envoi du Go de dechargement aux entrepots
    @login_required(login_url='login')
    def godechargement(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 7 or role == 1:
            c = Cargaison.objects.get(idcargaison=pk)
            c.etat = "En attente de dechargement"
            c.save(update_fields=['etat'])
            return redirect('laboresult')
        else:
            return redirect('logout')

    # Methode pour l'affichage des elements dont les ACT sont prets a etre imprimer
    @login_required(login_url='login')
    def gestionact(request):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 7 or role == 1:
            table = Act(Cargaison.objects.raw('SELECT c.idcargaison, d.datedechargement, c.numdossier, c.codecargaison, c.importateur_id , c.entrepot_id, c.immatriculation, l.numcertificatqualite, d.gsv\
                                                   FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d, hydro_occ.enreg_laboreception l, hydro_occ.accounts_affectationville a\
                                                   WHERE c.idcargaison = d.idcargaison_id \
                                                   AND l.idcargaison_id = d.idcargaison_id \
                                                   AND c.frontiere_id = a.ville_id \
                                                   AND a.username_id = %s \
                                                   AND c.numact IS NULL \
                                                   ORDER BY d.datedechargement DESC', [id, ]), prefix="100_")

            table1 = Act2(Cargaison.objects.raw('SELECT c.idcargaison, c.printactdate, c.numdossier, c.codecargaison, c.importateur_id , c.entrepot_id, c.immatriculation, l.numcertificatqualite, d.gsv\
                                                   FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d, hydro_occ.enreg_laboreception l,hydro_occ.accounts_affectationville a\
                                                   WHERE c.idcargaison = d.idcargaison_id \
                                                   AND l.idcargaison_id = d.idcargaison_id \
                                                   AND c.frontiere_id = a.ville_id \
                                                   AND a.username_id = %s \
                                                   AND c.numact IS NOT NULL \
                                                   ORDER BY c.printactdate DESC', [id, ]), prefix="200_")

            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            RequestConfig(request, paginate={"per_page": 15}).configure(table1)

            return render(request, 'shydro_act.html', {
                'act': table,
                'act1': table1,
            })
        else:
            return redirect('logout')

    # Impression des ACT
    @login_required(login_url='login')
    def printact(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 7 or role == 1:
            template = 'report/act.html'

            # Recuperation Cargaison
            c = Cargaison.objects.get(idcargaison=pk)
            d = Dechargement.objects.get(idcargaison=pk)
            e = Entrepot.objects.get(cargaison=pk)
            r = Resultat.objects.get(idcargaison=pk)
            p = Produit.objects.get(cargaison=pk)
            i = Importateur.objects.get(cargaison=pk)
            en = Entrepot_echantillon.objects.get(idcargaison=pk)
            re = LaboReception.objects.get(idcargaison=pk)

            # Elements de l'ACT
            t1d = c.t1d
            codecargaison = c.codecargaison
            numdossier = c.numdossier
            importateur = i.nomimportateur
            addressimport = i.adresseimportateur
            provenance = c.provenance
            produit = p.nomproduit
            immatriculation = c.immatriculation
            voldecl = c.volume
            voldecl15 = c.volume_decl15
            entrepot = e.nomentrepot
            chauffeur = c.nomchauffeur
            nationalite = c.nationalite
            numrappech = en.numrappech
            dateech = en.dateechantillonage
            datedech = d.datedechargement
            nature = p.nomproduit
            gov = d.gov
            gsv = d.gsv
            diffvolume = round(((gov - gsv) / (gov)) * 100, 2)
            numerore = re.numcertificatqualite
            datecert = r.dateanalyse

            # Numéro ACT
            numact = numeroactcurrent(pk)
            year = c.dateheurecargaison
            year = datetime.datetime.date(year)
            year = year.year

            # Date impression ACT
            now = date.today()
            printactdate = now

            c.printactdate = printactdate
            c.numact = numact
            c.impression = "1"
            c.save(update_fields=['impression', 'printactdate', 'numact'])

            data = {
                'year': year,
                'numact': numact,
                't1d': t1d,
                'codecargaison': codecargaison,
                'numdossier': numdossier,
                'importateur': importateur,
                'addressimport': addressimport,
                'provenance': provenance,
                'produit': produit,
                'immatriculation': immatriculation,
                'voldecl': voldecl,
                'voldecl15': voldecl15,
                'entrepot': entrepot,
                'chauffeur': chauffeur,
                'nationalite': nationalite,
                'numrappech': numrappech,
                'dateech': dateech,
                'datedech': datedech,
                'nature': nature,
                'gov': gov,
                'gsv': gsv,
                'numerore': numerore,
                'datecert': datecert,
                # 'diffvolume':diffvolume,
                'printactdate': printactdate
            }

            # Render PDF report
            pdf = render_to_pdf(template, data)
            return HttpResponse(pdf, content_type='application/pdf')
        else:
            return redirect('logout')

    # Impression des ACT
    @login_required(login_url='login')
    def reprintact(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 7 or role == 1:
            template = 'report/act.html'

            # Recuperation Cargaison
            c = Cargaison.objects.get(idcargaison=pk)
            d = Dechargement.objects.get(idcargaison=pk)
            e = Entrepot.objects.get(cargaison=pk)
            r = Resultat.objects.get(idcargaison=pk)
            p = Produit.objects.get(cargaison=pk)
            i = Importateur.objects.get(cargaison=pk)
            en = Entrepot_echantillon.objects.get(idcargaison=pk)
            re = LaboReception.objects.get(idcargaison=pk)

            # Elements de l'ACT
            t1d = c.t1d
            codecargaison = c.codecargaison
            numdossier = c.numdossier
            importateur = i.nomimportateur
            addressimport = i.adresseimportateur
            provenance = c.provenance
            produit = p.nomproduit
            immatriculation = c.immatriculation
            voldecl = c.volume
            voldecl15 = c.volume_decl15
            entrepot = e.nomentrepot
            chauffeur = c.nomchauffeur
            nationalite = c.nationalite
            numrappech = en.numrappech
            dateech = en.dateechantillonage
            datedech = d.datedechargement
            nature = p.nomproduit
            gov = d.gov
            gsv = d.gsv
            diffvolume = round(((gov - gsv) / (gov)) * 100, 2)
            numerore = re.numcertificatqualite
            datecert = r.dateanalyse
            numact = c.numact
            printactdate = c.printactdate

            # Year Num
            year = c.dateheurecargaison
            year = datetime.datetime.date(year)
            year = year.year

            data = {
                'year': year,
                'numact': numact,
                't1d': t1d,
                'codecargaison': codecargaison,
                'numdossier': numdossier,
                'importateur': importateur,
                'addressimport': addressimport,
                'provenance': provenance,
                'produit': produit,
                'immatriculation': immatriculation,
                'voldecl': voldecl,
                'voldecl15': voldecl15,
                'entrepot': entrepot,
                'chauffeur': chauffeur,
                'nationalite': nationalite,
                'numrappech': numrappech,
                'dateech': dateech,
                'datedech': datedech,
                'nature': nature,
                'gov': gov,
                'gsv': gsv,
                'numerore': numerore,
                'datecert': datecert,
                'diffvolume': diffvolume,
                'printactdate': printactdate
            }

            # Render PDF report
            pdf = render_to_pdf(template, data)
            return HttpResponse(pdf, content_type='application/pdf')
        else:
            return redirect('logout')

    # Recherche ACT par numéro dossier, Codecargaison, Numéro ACT
    def rechercheact(request):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 7 or role == 1:
            if request.method == 'GET':
                q = request.GET.get('valeur')

                if q == '':
                    table = Act(Cargaison.objects.raw('SELECT c.idcargaison, d.datedechargement, c.numdossier, c.codecargaison, c.importateur_id , c.entrepot_id, c.immatriculation, l.numcertificatqualite, d.gsv\
                                                                                   FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d, hydro_occ.enreg_laboreception l\
                                                                                   WHERE c.idcargaison = d.idcargaison_id \
                                                                                   AND l.idcargaison_id = d.idcargaison_id \
                                                                                   AND c.numact IS NULL \
                                                                                   ORDER BY d.datedechargement ASC '),
                                prefix="1_")

                    table1 = Act2(Cargaison.objects.raw('SELECT c.idcargaison, c.printactdate, c.numdossier, c.codecargaison, c.importateur_id , c.entrepot_id, c.immatriculation, l.numcertificatqualite, d.gsv\
                                                                       FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d, hydro_occ.enreg_laboreception l\
                                                                       WHERE c.idcargaison = d.idcargaison_id \
                                                                       AND l.idcargaison_id = d.idcargaison_id \
                                                                       AND c.numact IS NOT NULL \
                                                                       ORDER BY c.printactdate DESC '), prefix="2_")

                    RequestConfig(request, paginate={"per_page": 10}).configure(table)
                    RequestConfig(request, paginate={"per_page": 10}).configure(table1)

                    return render(request, 'shydro_act.html', {
                        'act': table,
                        'act1': table1,
                    })
                else:

                    table = Act(Cargaison.objects.raw('SELECT c.idcargaison, d.datedechargement, c.numdossier, c.codecargaison, c.importateur_id , c.entrepot_id, c.immatriculation, l.numcertificatqualite, d.gsv\
                                                                       FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d, hydro_occ.enreg_laboreception l, hydro_occ.accounts_affectationville a\
                                                                       WHERE c.idcargaison = d.idcargaison_id \
                                                                       AND l.idcargaison_id = d.idcargaison_id \
                                                                       AND c.numact IS NULL \
                                                                       AND frontiere_id = a.ville_id \
                                                                       AND a.username_id = %s \
                                                                       ORDER BY d.datedechargement ASC', [id, ]),
                                prefix="1_")

                    table1 = Act2(Cargaison.objects.raw('SELECT c.idcargaison, c.printactdate, c.numdossier, c.codecargaison, c.importateur_id , c.entrepot_id, c.immatriculation, l.numcertificatqualite, d.gsv\
                                                                       FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d, hydro_occ.enreg_laboreception l, hydro_occ.accounts_affectationville a\
                                                                       WHERE c.idcargaison = d.idcargaison_id \
                                                                       AND l.idcargaison_id = d.idcargaison_id \
                                                                       AND c.numact IS NOT NULL \
                                                                       AND frontiere_id = a.ville_id \
                                                                       AND a.username_id = %s \
                                                                       AND ((c.numdossier = %s) \
                                                                       OR (c.codecargaison = %s) \
                                                                       OR (c.numact = %s)) \
                                                                       ORDER BY c.printactdate DESC ', [q, q, q]),
                                  prefix="2_")

                    RequestConfig(request, paginate={"per_page": 10}).configure(table)
                    RequestConfig(request, paginate={"per_page": 10}).configure(table1)

                    return render(request, 'shydro_act.html', {
                        'act': table,
                        'act1': table1,
                    })
            else:

                return redirect('logout')
        else:
            return redirect('logout')


@login_required(login_url='login')
def enAttenteEchantillonnage(request):
    user = request.user.id
    template = 'enAttenteEchantillonnage.html'
    qs = Cargaison.objects.filter(etat="En attente d'echantillonage",
                                  entrepot__ville__affectationville__username_id=user).order_by('-requisitiondackdate')
    table = EnAttenteEchantillonage(qs)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enAttenteEchantillonnage1(request):
    user = request.user.id
    template = 'enAttenteEchantillonnage1.html'
    qs = Cargaison.objects.filter(etat="En attente d'echantillonage",
                                  entrepot__ville__affectationville__username_id=user).order_by('-requisitiondackdate')
    table = EnAttenteEchantillonage(qs)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enAttenteDechargement(request):
    user = request.user.id
    template = 'enAttenteDechargement.html'
    # qs = ImpressionResultat.objects.filter(idcargaison__etat="Conforme aux exigences",idcargaison__entrepot__ville__affectationville__username_id=user)
    qs = ImpressionResultat.objects.raw("SELECT ei.idImpression ,ei.idcargaison_id, ec.numdos, ec.declaration , i.nomimportateur, ec.immatriculation, ee.nomentrepot, ep.nomproduit, ec.requisitiondackdate, eee.dateechantillonage, el.datereceptionlabo, ei.printDate \
            FROM enreg_impressionresultat ei, enreg_cargaison ec, enreg_importateur i, enreg_entrepot ee, enreg_produit ep, enreg_entrepot_echantillon eee, enreg_laboreception el, accounts_affectationville aa  \
            WHERE ei.idcargaison_id = ec.idcargaison \
            AND ec.importateur_id = i.idimportateur \
            AND ec.entrepot_id = ee.identrepot \
            AND ec.produit_id = ep.idproduit \
            AND ec.idcargaison = eee.idcargaison_id \
            AND eee.idcargaison_id = el.idcargaison_id \
            AND ec.etat = 'Conforme aux exigences' \
            AND aa.username_id = %s", [user, ])

    table = EnAttenteDechargement(qs)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enAttenteDechargement1(request):
    user = request.user.id
    template = 'enAttenteDechargement1.html'
    # qs = ImpressionResultat.objects.filter(idcargaison__etat="Conforme aux exigences",idcargaison__entrepot__ville__affectationville__username_id=user)
    qs = ImpressionResultat.objects.raw("SELECT ei.idImpression ,ei.idcargaison_id, ec.numdos, ec.declaration , i.nomimportateur, ec.immatriculation, ee.nomentrepot, ep.nomproduit, ec.requisitiondackdate, eee.dateechantillonage, el.datereceptionlabo, ei.printDate \
            FROM enreg_impressionresultat ei, enreg_cargaison ec, enreg_importateur i, enreg_entrepot ee, enreg_produit ep, enreg_entrepot_echantillon eee, enreg_laboreception el, accounts_affectationville aa  \
            WHERE ei.idcargaison_id = ec.idcargaison \
            AND ec.importateur_id = i.idimportateur \
            AND ec.entrepot_id = ee.identrepot \
            AND ec.produit_id = ep.idproduit \
            AND ec.idcargaison = eee.idcargaison_id \
            AND eee.idcargaison_id = el.idcargaison_id \
            AND ec.etat = 'Conforme aux exigences' \
            AND aa.username_id = %s", [user, ])

    table = EnAttenteDechargement(qs)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enAttenteResultatLabo(request):
    user = request.user.id
    template = 'enAttenteResultatLabo.html'
    qs = LaboReception.objects.filter(idcargaison__idcargaison__etat="Analyse Labo en cours",
                                      idcargaison__idcargaison_id__entrepot__ville__affectationville__username_id=user)
    table = EnAttenteResultatLabo(qs)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enAttenteResultatLabo1(request):
    user = request.user.id
    template = 'enAttenteResultatLabo1.html'
    qs = LaboReception.objects.filter(idcargaison__idcargaison__etat="Analyse Labo en cours",
                                      idcargaison__idcargaison_id__entrepot__ville__affectationville__username_id=user)
    table = EnAttenteResultatLabo(qs)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enAttenteReceptionLabo(request):
    user = request.user.id
    template = 'enAttenteReceptionLabo.html'
    qs = Entrepot_echantillon.objects.filter(
        idcargaison__etat="Echantillonner",
        idcargaison__entrepot__ville__affectationville__username_id=user,
    ).values(
        'idcargaison__numdos',
        'idcargaison__declaration',
        'idcargaison__importateur__nomimportateur',
        'idcargaison__entrepot__nomentrepot',
        'idcargaison__produit__nomproduit',
        'idcargaison__immatriculation',
        'idcargaison__requisitiondackdate',
        'dateechantillonage__date',
    )
    table = EnAttenteReceptionLabo(qs)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enAttenteReceptionLabo1(request):
    user = request.user.id
    template = 'enAttenteReceptionLabo1.html'
    qs = Entrepot_echantillon.objects.filter(
        idcargaison__etat="Echantillonner",
        idcargaison__entrepot__ville__affectationville__username_id=user,
    ).values(
        'idcargaison__numdos',
        'idcargaison__declaration',
        'idcargaison__importateur__nomimportateur',
        'idcargaison__entrepot__nomentrepot',
        'idcargaison__produit__nomproduit',
        'idcargaison__immatriculation',
        'idcargaison__requisitiondackdate',
        'dateechantillonage__date',
    )
    table = EnAttenteReceptionLabo(qs)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enAttenteInspection(request):
    user = request.user.id
    template = 'enAttenteInspection.html'
    qs = Entrepot_echantillon.objects.filter(
        idcargaison__etatInspection=True,
        # idcargaison__inspection__dateinspection__isnull=True,
        idcargaison__entrepot__ville__affectationville__username_id=user,
    ).values(
        'idcargaison__numdos',
        'idcargaison__declaration',
        'idcargaison__importateur__nomimportateur',
        'idcargaison__entrepot__nomentrepot',
        'idcargaison__produit__nomproduit',
        'idcargaison__immatriculation',
        'idcargaison__requisitiondackdate',
        'dateechantillonage__date',
    )
    table = EnAttenteInspection(qs)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enAttenteInspection1(request):
    user = request.user.id
    template = 'enAttenteInspection1.html'
    qs = Entrepot_echantillon.objects.filter(
        idcargaison__etatInspection=True,
        # idcargaison__inspection__dateinspection__isnull=True,
        idcargaison__entrepot__ville__affectationville__username_id=user,
    ).values(
        'idcargaison__numdos',
        'idcargaison__declaration',
        'idcargaison__importateur__nomimportateur',
        'idcargaison__entrepot__nomentrepot',
        'idcargaison__produit__nomproduit',
        'idcargaison__immatriculation',
        'idcargaison__requisitiondackdate',
        'dateechantillonage__date',
    )
    table = EnAttenteInspection(qs)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def rapportActivite(request):
    user_id = request.user.id
    template = 'rapportActiviteFirst.html'
    form = Filters(user=user_id)

    # Render the JS-driven DataTable page. All data is loaded via
    # the server-side endpoint `responseRapportActivite`.
    # Populate dropdown data for advanced filters
    try:
        # Import here to avoid circulars in some environments
        from enreg.models import Ville, Importateur, Entrepot, Produit
        # Use 'pk' alias to be agnostic of legacy PK field names (e.g., idville, idproduit, ...)
        frontieres = list(Ville.objects.all().order_by('nomville').values('pk', 'nomville'))
        fournisseurs = list(Importateur.objects.all().order_by('nomimportateur').values('pk', 'nomimportateur'))
        entrepots = list(Entrepot.objects.filter(
            ville__affectationville__username_id=user_id
        ).order_by('nomentrepot').values('pk', 'nomentrepot'))
        produits = list(Produit.objects.all().order_by('nomproduit').values('pk', 'nomproduit'))
    except Exception:
        frontieres, fournisseurs, entrepots, produits = [], [], [], []

    return render(request, template, {
        'form': form,
        'frontieres': frontieres,
        'fournisseurs': fournisseurs,
        'entrepots': entrepots,
        'produits': produits,
    })



@login_required(login_url='login')
@require_POST
def responseRapportActivite(request):

    """
    Server-side endpoint for Rapport d'activités DataTable.
    - True lazy pagination via LIMIT/OFFSET using queryset slicing
    - Server-side search and ordering
    - Short‑TTL caching for counts and page slices
    - Streaming Excel export respecting current filters
    """


    user_id = request.user.id

    # Base queryset for counts and subsequent projection
    base_qs = (
        Cargaison.objects
        .select_related(
            'entrepot', 'entrepot__ville', 'frontiere', 'importateur', 'produit', 'inspection'
        )
        .filter(entrepot__ville__affectationville__username_id=user_id)
    )

    # Annotation required by this report
    # Note: Do not alias related-paths directly in annotate (must be an expression).
    # We keep sums here; raw density/temperature come from projection fields below.
    annotated_qs = base_qs.annotate(
        volConst=Sum('inspection__compartiment__gov'),
        gsvT=Sum('inspection__compartiment__gsv'),
        mtaT=Sum('inspection__compartiment__mta'),
        mtvT=Sum('inspection__compartiment__mtv'),
    )

    # Helper to read params from POST only (no GET fallback for safety)
    def P(name, default=''):
        try:
            val = request.POST.get(name)
            return val if val is not None else default
        except Exception:
            return default

    # Optional advanced filters (server-side)
    # Supported params: date_from, date_to (YYYY-MM-DD),
    # frontiere, importateur, entrepot, produit (name contains),
    # immatriculation (exact contains), declaration, numdos (contains)
    date_from = (P('date_from') or '').strip()
    date_to = (P('date_to') or '').strip()
    ft_name = (P('frontiere') or '').strip()
    imp_name = (P('importateur') or '').strip()
    ent_name = (P('entrepot') or '').strip()
    prod_name = (P('produit') or '').strip()
    immat = (P('immatriculation') or '').strip()
    decl = (P('declaration') or '').strip()
    numd = (P('numdos') or '').strip()

    adv_filters = Q()
    if date_from and date_to:
        try:
            adv_filters &= Q(dateheurecargaison__date__range=[date_from, date_to])
        except Exception:
            pass
    elif date_from:
        try:
            adv_filters &= Q(dateheurecargaison__date__gte=date_from)
        except Exception:
            pass
    elif date_to:
        try:
            adv_filters &= Q(dateheurecargaison__date__lte=date_to)
        except Exception:
            pass

    if ft_name:
        adv_filters &= Q(frontiere__nomville__icontains=ft_name)
    if imp_name:
        adv_filters &= Q(importateur__nomimportateur__icontains=imp_name)
    if ent_name:
        adv_filters &= Q(entrepot__nomentrepot__icontains=ent_name)
    if prod_name:
        adv_filters &= Q(produit__nomproduit__icontains=prod_name)
    if immat:
        adv_filters &= Q(immatriculation__icontains=immat)
    if decl:
        adv_filters &= Q(declaration__icontains=decl)
    if numd:
        adv_filters &= Q(numdos__icontains=numd)

    if adv_filters:
        annotated_qs = annotated_qs.filter(adv_filters)

    # Projection (only send needed fields to the client)
    qs = annotated_qs.values(
        'idcargaison',
        'numdos',
        'declaration',
        'frontiere__nomville',
        'entrepot__nomentrepot',
        'inspection__dateinspection',
        'inspection__dens',
        'inspection__temp',
        'importateur__nomimportateur',
        'immatriculation',
        'produit__nomproduit',
        'dateheurecargaison',
        'dateheurecargaison__date',
        'requisitiondackdate__date',
        'entrepot_echantillon__dateechantillonage__date',
        'entrepot_echantillon__laboreception__datereceptionlabo__date',
        'dateDechargement',
        'impressionresultat__printDate',
        'volume',
        'volConst',
        'gsvT',
        'mtaT',
        'mtvT',

    )

    # DataTables params
    # 'draw' must be echoed back to DataTables; parse defensively
    try:
        draw = int(P('draw', '1'))
    except (TypeError, ValueError):
        draw = 1
    try:
        start = max(int(P('start', '0')), 0)
    except ValueError:
        start = 0

    # Always show 15 per page, ignore client length; hard-cap deep pagination window
    length = 15

    # Total count (cached per user)
    total_cache_key = f"rapport_activ:total:u{user_id}"
    records_total = cache.get(total_cache_key)
    if records_total is None:
        records_total = base_qs.count()
        cache.set(total_cache_key, records_total, timeout=20)

    # Search
    search_value = (P('search[value]', '') or '').strip()
    if search_value:
        # Apply filter on projected fields
        qs = qs.filter(
            Q(frontiere__nomville__icontains=search_value) |
            Q(importateur__nomimportateur__icontains=search_value) |
            Q(entrepot__nomentrepot__icontains=search_value) |
            Q(produit__nomproduit__icontains=search_value) |
            Q(immatriculation__icontains=search_value) |
            Q(declaration__icontains=search_value) |
            Q(numdos__icontains=search_value)
        )
    search_key = hashlib.md5(search_value.lower().encode('utf-8')).hexdigest() if search_value else '_'

    # Advanced filter hash for cache keys
    def _mk_hash(parts: list[str]) -> str:
        try:
            return hashlib.md5(('|'.join(parts)).encode('utf-8')).hexdigest()
        except Exception:
            return '_'

    filter_key = _mk_hash([
        date_from, date_to, ft_name, imp_name, ent_name, prod_name, immat, decl, numd
    ])

    # Server-side ordering
    # Map DataTables visible columns -> model fields, in the SAME ORDER as front-end columns
    # Front-end columns must match this order:
    #   0: DATE ENTREE
    #   1: FRONTIERE
    #   2: FOURNISSEUR
    #   3: ENTREPOT
    #   4: PRODUIT
    #   5: VOL.DECL.
    #   6: IMMATR.
    #   7: #.DECLARATION
    #   8: #.DOSSIER
    #   9: DATE REQUISITION
    #  10: DATE ECHANTILLONNAGE
    #  11: DATE RECEPTION LABO
    #  12: DATE D'ANALYSE (mapped to printDate here)
    #  13: DATE D'INSPECTION
    #  14: DATE DE DECHARGEMENT
    #  15: VOL JAUGE (GOV)
    #  16: DENSITE @15 (computed)
    #  17: TEMPERATURE
    #  18: VCF (computed)
    #  19: MTA
    #  20: MTV
    #  21: GSV
    #  22: ACTIONS (UI only)
    dt_columns_to_fields = [
        'dateheurecargaison__date',            # 0
        'frontiere__nomville',                 # 1
        'importateur__nomimportateur',         # 2
        'entrepot__nomentrepot',               # 3
        'produit__nomproduit',                 # 4
        'volume',                               # 5 (vol déclaré)
        'immatriculation',                      # 6
        'declaration',                          # 7
        'numdos',                               # 8
        'requisitiondackdate__date',           # 9
        'entrepot_echantillon__dateechantillonage__date', # 10
        'entrepot_echantillon__laboreception__datereceptionlabo__date', # 11
        'impressionresultat__printDate',       # 12 (used as analysis date)
        'inspection__dateinspection',          # 13
        'dateDechargement',                    # 14
        'volConst',                             # 15 (vol jauge / GOV)
        None,                                   # 16 densite15 (computed, not orderable)
        'inspection__temp',                     # 17 temperature
        None,                                   # 18 vcf (computed)
        'mtaT',                                 # 19 MTA
        'mtvT',                                 # 20 MTV
        'gsvT',                                 # 21 GSV
        None,                                   # 22 Actions (UI only)
    ]
    order_by_fields = []
    i = 0
    while True:
        col_index = P(f'order[{i}][column]')
        if col_index is None:
            break
        dir_value = P(f'order[{i}][dir]', 'asc')
        try:
            col_index = int(col_index)
        except ValueError:
            i += 1
            continue
        if 0 <= col_index < len(dt_columns_to_fields):
            field = dt_columns_to_fields[col_index]
            # Skip computed-only columns (None mapping)
            if field:
                if dir_value == 'desc':
                    field = f'-{field}'
                order_by_fields.append(field)
        i += 1

    default_ordering = ['-dateheurecargaison__date']
    if order_by_fields:
        qs = qs.order_by(*order_by_fields)
    else:
        qs = qs.order_by(*default_ordering)

    # recordsFiltered (cached per user+search+filters)
    filtered_cache_key = f"rapport_activ:filtered:u{user_id}:s{search_key}:f{filter_key}"
    records_filtered = cache.get(filtered_cache_key)
    if records_filtered is None:
        records_filtered = qs.count()
        cache.set(filtered_cache_key, records_filtered, timeout=20)

    # Slice for paginated window (cached per page window + order)
    order_key_src = ','.join(order_by_fields) if order_by_fields else ','.join(default_ordering)
    order_key = hashlib.md5(order_key_src.encode('utf-8')).hexdigest()
    page_cache_key = f"rapport_activ:page:u{user_id}:s{search_key}:f{filter_key}:o{order_key}:p{start}_{length}"
    # If start is outside the filtered range, return empty page quickly
    # Prevent pathological deep scans
    if start > 100000:
        start = 100000
    if start >= max(records_filtered, 0):
        data = []
    else:
        data = cache.get(page_cache_key)
    if data is None:
        end = start + length
        page_slice = list(qs[start:end])

        # Helpers to format date/datetime
        def _fmt_dt(val):
            try:
                if val is None:
                    return None
                if isinstance(val, datetime.datetime):
                    if timezone.is_aware(val):
                        val = timezone.localtime(val)
                    return val.strftime('%d/%m/%Y %H:%M')
                if isinstance(val, (datetime.date,)):
                    return val.strftime('%d/%m/%Y')
            except Exception:
                return None
            return str(val)

        # Helper to coerce numeric fields that may come as strings like '0,835' or with spaces
        def _to_float(val):
            try:
                if val is None:
                    return None
                # If already a number
                if isinstance(val, (int, float)):
                    return float(val)
                s = str(val).strip()
                if s == '':
                    return None
                # Replace comma decimal separator
                s = s.replace(',', '.')
                return float(s)
            except Exception:
                return None

        # Compute per-row derived values without touching the DB again
        enriched = []
        for row in page_slice:
            row = dict(row)
            dens = _to_float(row.get('inspection__dens'))
            temp = _to_float(row.get('inspection__temp'))
            d15 = None
            vcf_val = None
            try:
                if dens is not None and temp is not None:
                    # Compute density @15 and VCF
                    # NOTE: calculs.densite15 expects (temperature, density_at_ambient)
                    d15 = densite15(temp, dens)
                    print("DENSITE 15", d15)
                    # Prefer using d15 for VCF if available
                    vcf_input_density = d15 if d15 is not None else dens
                    vcf_val = vcf(vcf_input_density, temp)
            except Exception:
                d15 = None
                vcf_val = None

            # Optional rounding for display consistency (does not affect ordering)
            if isinstance(d15, (int, float)):
                try:
                    d15 = round(float(d15), 5)
                except Exception:
                    pass
            if isinstance(vcf_val, (int, float)):
                try:
                    vcf_val = round(float(vcf_val), 6)
                except Exception:
                    pass

            # Helper: round to 3 decimals when numeric
            def _round3(v):
                try:
                    if v is None:
                        return None
                    return round(float(v), 3)
                except Exception:
                    return v

            # Aliases expected by UI
            row['vol_jauge'] = row.get('volConst')
            row['densite15'] = d15
            row['vcf'] = vcf_val
            row['mta'] = _round3(row.get('mtaT'))
            row['mtv'] = _round3(row.get('mtvT'))
            row['gsv'] = _round3(row.get('gsvT'))

            # Human-readable dates
            row['date_entree_display'] = _fmt_dt(row.get('dateheurecargaison')) or _fmt_dt(row.get('dateheurecargaison__date'))
            row['date_requisition_display'] = _fmt_dt(row.get('requisitiondackdate__date'))
            row['date_echant_display'] = _fmt_dt(row.get('entrepot_echantillon__dateechantillonage__date'))
            row['date_recep_labo_display'] = _fmt_dt(row.get('entrepot_echantillon__laboreception__datereceptionlabo__date'))
            row['date_analyse_display'] = _fmt_dt(row.get('impressionresultat__printDate'))
            row['date_inspection_display'] = _fmt_dt(row.get('inspection__dateinspection'))
            row['date_dechargement_display'] = _fmt_dt(row.get('dateDechargement'))

            enriched.append(row)

        data = enriched
        cache.set(page_cache_key, data, timeout=20)

    # Excel export (streaming) respecting current filters (ignores pagination)
    return JsonResponse({
        'data': data,
        'draw': draw,
        'recordsTotal': records_total,
        'recordsFiltered': records_filtered,
    })


@login_required(login_url='login')
def filterOptionsRapportActivite(request):
    """
    JSON endpoint to populate Filters modal dropdowns for Rapport d'activités.
    Returns lists for: frontieres, fournisseurs, entrepots (scoped to user), produits.
    Each item contains: id, label, value (label duplicated for convenience on client side).
    """
    try:
        from django.core.cache import cache
        from enreg.models import Ville, Importateur, Entrepot, Produit
        user_id = request.user.id

        cache_key = f"rapport_activ:filters:u{user_id}"
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse(cached)

        # Use 'pk' alias so this works regardless of actual PK field names
        frontieres = [
            {'id': v['pk'], 'label': v['nomville'], 'value': v['nomville']}
            for v in Ville.objects.all().order_by('nomville').values('pk', 'nomville')
        ]
        fournisseurs = [
            {'id': i['pk'], 'label': i['nomimportateur'], 'value': i['nomimportateur']}
            for i in Importateur.objects.all().order_by('nomimportateur').values('pk', 'nomimportateur')
        ]
        entrepots = [
            {'id': e['pk'], 'label': e['nomentrepot'], 'value': e['nomentrepot']}
            for e in Entrepot.objects.filter(
                ville__affectationville__username_id=user_id
            ).order_by('nomentrepot').values('pk', 'nomentrepot')
        ]
        produits = [
            {'id': p['pk'], 'label': p['nomproduit'], 'value': p['nomproduit']}
            for p in Produit.objects.all().order_by('nomproduit').values('pk', 'nomproduit')
        ]

        payload = {
            'frontieres': frontieres,
            'fournisseurs': fournisseurs,
            'entrepots': entrepots,
            'produits': produits,
        }
        # Cache for 1 hour (adjust as needed); cheap to rebuild if missed
        cache.set(cache_key, payload, timeout=3600)
        return JsonResponse(payload)
    except Exception as exc:
        return JsonResponse({'error': 'Failed to load filter options', 'detail': str(exc)}, status=500)


@login_required(login_url='login')
def startRapportActiviteExport(request):
    """
    Start async export of Rapport d'activités using current filters/search/order.
    Expects POST (JSON body recommended) containing DataTables-like params and our advanced filters.
    Returns { task_id } to poll via checkExportTaskStatus.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    user_id = request.user.id
    try:
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except Exception:
            payload = {}

        # Normalize expected params
        params = {
            'search[value]': (payload.get('search', {}) or {}).get('value') or payload.get('search_value') or (request.POST.get('search[value]') or ''),
            'date_from': payload.get('date_from') or request.POST.get('date_from') or request.GET.get('date_from') or '',
            'date_to': payload.get('date_to') or request.POST.get('date_to') or request.GET.get('date_to') or '',
            'frontiere': payload.get('frontiere') or request.POST.get('frontiere') or request.GET.get('frontiere') or '',
            'importateur': payload.get('importateur') or request.POST.get('importateur') or request.GET.get('importateur') or '',
            'entrepot': payload.get('entrepot') or request.POST.get('entrepot') or request.GET.get('entrepot') or '',
            'produit': payload.get('produit') or request.POST.get('produit') or request.GET.get('produit') or '',
            'immatriculation': payload.get('immatriculation') or request.POST.get('immatriculation') or request.GET.get('immatriculation') or '',
            'declaration': payload.get('declaration') or request.POST.get('declaration') or request.GET.get('declaration') or '',
            'numdos': payload.get('numdos') or request.POST.get('numdos') or request.GET.get('numdos') or '',
            'order': payload.get('order') or [],
        }

        # Enqueue Celery task
        from shydro.tasks import export_rapport_activites_task
        res = export_rapport_activites_task.delay(params, user_id)
        return JsonResponse({'task_id': res.id})
    except Exception as exc:
        return JsonResponse({'error': 'Failed to start export', 'detail': str(exc)}, status=500)


@login_required(login_url='login')
def regularisation(request):
    user = request.user.id
    template = 'regularisation.html'
    form = ChangementDestination()
    form1 = Transbordement()
    form2 = ChangementNatureProduit()
    form3 = ImportateurRegularisationForm()
    form4 = EntrepotRegularisationForm()
    form5 = RegularisationNouvelleEntree()
    form6 = ChangementImportateur()
    qs = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user).filter(
        Q(etat='En attente requisition') | Q(etat="En attente d'echantillonage")
    ).order_by('-dateheurecargaison')

    table = Regularisation(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
    context = {
        'table': table,
        'form': form,
        'form1': form1,
        'form2': form2,
        'form3': form3,
        'form4': form4,
        'form5': form5,
        'form6': form6,
    }
    return render(request, template, context)


@login_required(login_url='login')
def regularisation_response(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user).filter(
        Q(etat='En attente requisition') | Q(etat="En attente d'echantillonage")
    ).order_by('-dateheurecargaison').values(
        'dateheurecargaison__date',
        'importateur__nomimportateur',
        'entrepot__nomentrepot',
        'produit__nomproduit',
        'volume',
        'immatriculation',
        'declaration',
        'idcargaison'
    )

    # Get the search value from the request's GET parameters
    search_value = request.GET.get('search[value]', '')

    # Apply search filter to the QuerySet
    if search_value:
        qs = qs.filter(Q(immatriculation__icontains=search_value) |
                       Q(declaration__icontains=search_value) |
                       Q(importateur__nomimportateur__icontains=search_value) |
                       Q(entrepot__nomentrepot__icontains=search_value))

    # Number of items to show per page
    items_per_page = 15

    # Initialize the Paginator with the QuerySet and the number of items per page
    paginator = Paginator(qs, items_per_page)

    # Get the current page number from the request's GET parameters
    draw = int(request.GET.get('draw', 1))  # Get the draw value for proper AJAX handling
    start = int(request.GET.get('start', 0))  # Get the starting index for pagination
    length = int(request.GET.get('length', items_per_page))  # Get the number of items per page

    # Calculate the current page number based on start and length
    current_page = (start // length) + 1

    try:
        # Get the current page from the Paginator
        page = paginator.page(current_page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), return an empty JSON response.
        return JsonResponse({'data': [], 'draw': draw, 'recordsTotal': 0, 'recordsFiltered': 0})

    # Convert the page object to a list of dictionaries
    data = list(page)

    # Return JSON response with the data
    return JsonResponse({
        'data': data,
        'draw': draw,
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
    })


@login_required(login_url='login')
def regularisationDestination(request):
    user = request.user
    id = user.id

    if request.method == 'POST':
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            pk = request.POST.get('pk', None)
            nouvelleDestination = request.POST.get('nouvelleDestination', None)
            confirm = request.POST.get('confirm', None)  # Get the confirmation status
            ville = AffectationVille.objects.get(username_id=user.id)
            cargaison = Cargaison.objects.get(idcargaison=pk)
            entrepot = Entrepot.objects.get(identrepot=nouvelleDestination)
            print('VOIR LES DONNEES')
            print(ville.ville_id)
            print(entrepot.ville_id)

            if ville.ville_id != entrepot.ville_id:
                # If the cities don't match and the user didn't confirm, return warning
                if not confirm:
                    return JsonResponse({
                        'status': 'warning',
                        'message': "La ville de la nouvelle destination ne correspond pas à votre ville assignée. Confirmez-vous ?"
                    })
                else:
                    # If user confirms, proceed with the update even though the cities don't match
                    print("User confirmed the city mismatch.")

            print('WE ARE HERE !!!!')
            cargaison.entrepot = entrepot
            cargaison.save(update_fields=['entrepot'])
            # Return a JSON response indicating success
            return JsonResponse({'status': 'success'})

        else:
            return redirect('regularisation')
    else:
        return redirect('regularisation')




@login_required(login_url='login')
def transbordement(request):
    # template = 'regularisationDestination.html'
    # form = ChangementDestination(request.POST or None)
    # Getting Logged in user detail for filtering
    user = request.user
    id = user.id
    role = user.role_id

    # cargaison = Cargaison.objects.get(idcargaison=pk)
    if request.method == 'POST':
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            pk = request.POST.get('pk', None)
            nouvelleImmatriculation = request.POST.get('nouvelleImmatriculation', None)
            nouveauVolume = request.POST.get('nouveauVolume', None)
            cargaison = Cargaison.objects.get(idcargaison=pk)
            cargaison.immatriculation = nouvelleImmatriculation
            cargaison.volume = nouveauVolume
            cargaison.save(update_fields=['immatriculation', 'volume'])
            # Return a JSON response indicating success
            return JsonResponse({'status': 'success'})
        else:
            return redirect('regularisation')
    else:
        return redirect('regularisation')


@login_required(login_url='login')
def changementNature(request):
    # template = 'regularisationDestination.html'
    # form = ChangementDestination(request.POST or None)
    # Getting Logged in user detail for filtering
    user = request.user
    id = user.id
    role = user.role_id

    # cargaison = Cargaison.objects.get(idcargaison=pk)
    if request.method == 'POST':
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            pk = request.POST.get('pk', None)
            nouvelleNatureProduit = request.POST.get('nouvelleNatureProduit', None)
            p = Produit.objects.get(idproduit=nouvelleNatureProduit)
            cargaison = Cargaison.objects.get(idcargaison=pk)
            cargaison.produit = p
            cargaison.save(update_fields=['produit'])
            # Return a JSON response indicating success
            return JsonResponse({'status': 'success'})
        else:
            return redirect('regularisation')
    else:
        return redirect('regularisation')


@login_required(login_url='login')
def del_record(request):
    user = request.user
    if request.method == 'POST':
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            pk = request.POST.get('pk', None)
            print("DELETED")
            print(pk)
            Cargaison.objects.get(idcargaison=pk).delete()
            return JsonResponse({'status': 'success'})
        else:
            return redirect('regularisation')
    else:
        return redirect('regularisation')


    # log = UserActivityLog(
    #     user=user,
    #     action= "Delete",
    #     description= "User has delete a record"
    # )
    # log.save()



def checkExportTaskStatus(request, task_id):
    parameter = int(request.GET.get('parameter', 5))  # Get the parameter value from the request query parameters
    task = AsyncResult(task_id, app=app)

    if task.state in ['PENDING', 'SUCCESS', 'FAILURE']:
        # Task is in a known state
        if task.state == 'SUCCESS':
            # Task completed successfully
            result_value = task.get()
            response_data = {
                'state': 'SUCCESS',
                'progress': 100,  # Assuming progress is 100% when task is successful
                'result': result_value
            }
        elif task.state == 'FAILURE':
            # Task failed
            response_data = {
                'state': 'FAILURE',
                'progress': None,  # No progress if task failed
                'error': str(task.result)  # Include error message
            }
        else:
            # Task is in progress
            # Calculate progress based on the parameter value (modify this according to your logic)
            progress = parameter * 10  # Assuming each increment of parameter increases progress by 10%
            response_data = {
                'state': 'PENDING',
                'progress': min(progress, 80)  # Cap progress at 100%
            }
    else:
        # Task state is unknown or invalid
        response_data = {
            'state': 'UNKNOWN',
            'progress': None
        }

    return JsonResponse(response_data)


@login_required(login_url='login')
def rapportActiviteFiltrePost(request):
    user = request.user.id
    template = 'rapportActivite.html'
    form = Filters(user=user)

    if request.method == 'POST':
        fournisseur = request.session['fournisseur']
        entrepot = request.session['entrepot']
        dateDebut = request.session['dateDebut']
        dateFin = request.session['dateFin']

        qs = Cargaison.objects.annotate(
            volConst=Sum('inspection__compartiment__gov'),
            gsvT=Sum('inspection__compartiment__gsv'),
            mtaTotal=Sum('inspection__compartiment__mta'),
            mtvTotal=Sum('inspection__compartiment__mtv')
        ).values(
            'inspection__idinspection',  # Group by idinspection_id
            'idcargaison', 'numdos', 'declaration', 'frontiere__nomville', 'inspection__dens', 'inspection__temp',
            'entrepot__nomentrepot', 'inspection__dateinspection', 'importateur__nomimportateur', 'immatriculation',
            'produit__nomproduit', 'dateheurecargaison', 'requisitiondackdate',
            'entrepot_echantillon__dateechantillonage__date',
            'entrepot_echantillon__laboreception__datereceptionlabo__date', 'impressionresultat__printDate', 'volume',
            'volConst', 'gsvT', 'mtaTotal', 'mtvTotal'
        ).order_by('-inspection__dateinspection')

        if fournisseur and entrepot and dateDebut and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           entrepot_id=entrepot,
                           dateheurecargaison__date__range=[dateDebut, dateFin]
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and entrepot and dateDebut:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           entrepot_id=entrepot,
                           dateheurecargaison__date=dateDebut
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and entrepot:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           entrepot_id=entrepot,
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and dateDebut and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           dateheurecargaison__date__range=[dateDebut, dateFin]
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and dateDebut:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           dateheurecargaison__date=dateDebut
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           dateheurecargaison__date=dateFin
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur:
            qs = qs.filter(
                entrepot__ville__affectationville__username_id=user,
                importateur_id=fournisseur,
            )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if entrepot and dateDebut and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           entrepot_id=entrepot,
                           dateheurecargaison__date__range=[dateDebut, dateFin]
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if entrepot and dateDebut:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           entrepot_id=entrepot,
                           dateheurecargaison__date=dateDebut
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if entrepot and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           entrepot_id=entrepot,
                           dateheurecargaison__date=dateFin
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if entrepot:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           entrepot_id=entrepot,
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if dateDebut and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           dateheurecargaison__date__range=[dateDebut, dateFin]
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if dateDebut:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           dateheurecargaison__date=dateDebut
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           dateheurecargaison__date=dateFin
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = 'xlsx'
            if TableExport.is_valid_format(export_format):
                serialized_qs = list(qs)

                # Start Celery task to export report asynchronously
                result = app.send_task('shydro.tasks.export_report_task', args=[export_format, serialized_qs])

                # Retrieve the task ID
                task_id = result.id

                message = "Export task started. Task ID: {}".format(task_id)
                return JsonResponse({'task_id': task_id})

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)


@login_required(login_url='login')
def rapportActiviteFiltre(request):
    user = request.user.id
    template = 'rapportActivite.html'
    form = Filters(user=user)

    if request.method == 'POST':
        fournisseur = request.POST['fournisseur']
        entrepot = request.POST['entrepot']
        dateDebut = request.POST['dateDebut']
        dateFin = request.POST['dateFin']

        request.session['fournisseur'] = fournisseur
        request.session['entrepot'] = entrepot
        request.session['dateDebut'] = dateDebut
        request.session['dateFin'] = dateFin

        qs = Cargaison.objects.annotate(
            volConst=Sum('inspection__compartiment__gov'),
            gsvT=Sum('inspection__compartiment__gsv'),
            mtaTotal=Sum('inspection__compartiment__mta'),
            mtvTotal=Sum('inspection__compartiment__mtv')
        ).values(
            'inspection__idinspection',  # Group by idinspection_id
            'idcargaison', 'numdos', 'declaration', 'frontiere__nomville', 'inspection__dens', 'inspection__temp',
            'entrepot__nomentrepot', 'inspection__dateinspection', 'importateur__nomimportateur', 'immatriculation',
            'produit__nomproduit', 'dateheurecargaison', 'requisitiondackdate',
            'entrepot_echantillon__dateechantillonage__date',
            'entrepot_echantillon__laboreception__datereceptionlabo__date', 'impressionresultat__printDate', 'volume',
            'volConst', 'gsvT', 'mtaTotal', 'mtvTotal'
        ).order_by('-inspection__dateinspection')

        if fournisseur and entrepot and dateDebut and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           entrepot_id=entrepot,
                           dateheurecargaison__date__range=[dateDebut, dateFin]
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and entrepot and dateDebut:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           entrepot_id=entrepot,
                           dateheurecargaison__date=dateDebut
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and entrepot and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           entrepot_id=entrepot,
                           dateheurecargaison__date=dateFin
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and entrepot:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           entrepot_id=entrepot,
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and dateDebut and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           dateheurecargaison__date__range=[dateDebut, dateFin]
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and dateDebut:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           dateheurecargaison__date=dateDebut
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           dateheurecargaison__date=dateFin
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if entrepot and dateDebut and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           entrepot_id=entrepot,
                           dateheurecargaison__date__range=[dateDebut, dateFin]
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if entrepot and dateDebut:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           entrepot_id=entrepot,
                           dateheurecargaison__date=dateDebut
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if entrepot and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           entrepot_id=entrepot,
                           dateheurecargaison__date=dateFin
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if entrepot:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           entrepot_id=entrepot,
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if dateDebut and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           dateheurecargaison__date__range=[dateDebut, dateFin]
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if dateDebut:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           dateheurecargaison__date=dateDebut
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           dateheurecargaison__date=dateFin
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        qs = qs.filter(entrepot__ville__affectationville__username_id=user)
        table = RapportActivite(qs)
        RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
        export_format = request.GET.get("_export", None)
        if TableExport.is_valid_format(export_format):
            exporter = TableExport(export_format, table)
            return exporter.response("table.{}".format(export_format))

        context = {
            'table': table,
            'form': form
        }
        return render(request, template, context)


    else:
        fournisseur = request.session['fournisseur']
        entrepot = request.session['entrepot']
        dateDebut = request.session['dateDebut']
        dateFin = request.session['dateFin']

        qs = Cargaison.objects.annotate(
            volConst=Sum('inspection__compartiment__gov'),
            gsvT=Sum('inspection__compartiment__gsv'),
            mtaTotal=Sum('inspection__compartiment__mta'),
            mtvTotal=Sum('inspection__compartiment__mtv')
        ).values(
            'inspection__idinspection',  # Group by idinspection_id
            'idcargaison', 'numdos', 'declaration', 'frontiere__nomville', 'inspection__dens', 'inspection__temp',
            'entrepot__nomentrepot', 'inspection__dateinspection', 'importateur__nomimportateur', 'immatriculation',
            'produit__nomproduit', 'dateheurecargaison', 'requisitiondackdate',
            'entrepot_echantillon__dateechantillonage__date',
            'entrepot_echantillon__laboreception__datereceptionlabo__date', 'impressionresultat__printDate', 'volume',
            'volConst', 'gsvT', 'mtaTotal', 'mtvTotal'
        ).order_by('-inspection__dateinspection')

        if fournisseur and entrepot and dateDebut and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           entrepot_id=entrepot,
                           dateheurecargaison__date__range=[dateDebut, dateFin]
                           ).annotate(
                volConst=Sum('inspection__compartiment__gov'),
                gsvT=Sum('inspection__compartiment__gsv'),
                mtaTotal=Sum('inspection__compartiment__mta'),
                mtvTotal=Sum('inspection__compartiment__mtv'),
            ).values('inspection__compartiment__vcf',
                     'idcargaison', 'numdos', 'declaration', 'frontiere__nomville', 'inspection__idinspection',
                     'entrepot__ville__nomville',
                     'inspection__dateinspection', 'importateur__nomimportateur', 'entrepot__nomentrepot',
                     'immatriculation',
                     'produit__nomproduit', 'dateheurecargaison__date', 'requisitiondackdate__date',
                     'entrepot_echantillon__dateechantillonage__date', 'inspection__dens', 'inspection__temp',
                     'entrepot_echantillon__laboreception__datereceptionlabo__date', 'mtaTotal', 'mtvTotal',
                     'impressionresultat__printDate', 'inspection__dateinspection', 'volume', 'volConst', 'gsvT'
                     ).order_by('-inspection__dateinspection')

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and entrepot and dateDebut:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           entrepot_id=entrepot,
                           dateheurecargaison__date=dateDebut
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and entrepot and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           entrepot_id=entrepot,
                           dateheurecargaison__date=dateFin
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and entrepot:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           entrepot_id=entrepot,
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and dateDebut and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           dateheurecargaison__date__range=[dateDebut, dateFin]
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and dateDebut:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           dateheurecargaison__date=dateDebut
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           dateheurecargaison__date=dateFin
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if fournisseur:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           importateur_id=fournisseur,
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if entrepot and dateDebut and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           entrepot_id=entrepot,
                           dateheurecargaison__date__range=[dateDebut, dateFin]
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if entrepot and dateDebut:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           entrepot_id=entrepot,
                           dateheurecargaison__date=dateDebut
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if entrepot and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           entrepot_id=entrepot,
                           dateheurecargaison__date=dateFin
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if entrepot:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           entrepot_id=entrepot,
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if dateDebut and dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           dateheurecargaison__date__range=[dateDebut, dateFin]
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if dateDebut:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           dateheurecargaison__date=dateDebut
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        if dateFin:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user,
                           dateheurecargaison__date=dateFin
                           )

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table': table,
                'form': form
            }
            return render(request, template, context)

        qs = qs.filter(entrepot__ville__affectationville__username_id=user)
        table = RapportActivite(qs)
        RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
        export_format = request.GET.get("_export", None)
        if TableExport.is_valid_format(export_format):
            exporter = TableExport(export_format, table)
            return exporter.response("table.{}".format(export_format))

        context = {
            'table': table,
            'form': form
        }
        return render(request, template, context)


@login_required(login_url='login')
def rapportRe(request, pk):
    c = Cargaison.objects.get(idcargaison=pk)
    ville = c.entrepot.ville
    # Generer le rapport d'echantillonage
    template = 'rapportechantillonage.html'
    try:
        e = Entrepot_echantillon.objects.get(idcargaison=pk)
        entrepot = c.entrepot
        dateechantillonage = e.dateechantillonage
        dateech = dateechantillonage
        methodeutilisee = e.methodeutilisee
        matricule = e.matricule
        numdos = c.numdos
        importateur = c.importateur
        adresseimportateur = c.importateur_id
        adresseimportateur = Importateur.objects.get(idimportateur=adresseimportateur).adresseimportateur
        produit = c.produit
        volume = c.volume
        provenance = c.provenance.name
        voie = c.voie.nomvoie
        immatriculation = c.immatriculation
        qtelabo = e.qte
        numrappechauto = e.numrappechauto

        data = {
            'dateechantillonage': dateechantillonage,
            'dateech': dateech,
            'entrepot': entrepot,
            'numdos': numdos,
            'methodeutilisee': methodeutilisee,
            'importateur': importateur,
            'adresseimportateur': adresseimportateur,
            'produit': produit,
            'volume': volume,
            'provenance': provenance,
            'voie': voie,
            'immatriculation': immatriculation,
            'matricule': matricule,
            'qtelabo': qtelabo,
            'numrappechauto': numrappechauto,
        }

        # Render PDF Files
        pdf = render_to_pdf(template, data)
        return HttpResponse(pdf, content_type='application/pdf')
    except:
        return redirect('rapportActivite')


@login_required(login_url='login')
def rapportIs(request, pk):
    user = request.user
    ville = AffectationVille.objects.get(username_id=user.id)
    ville = ville.ville_id
    province = Ville.objects.get(idville=ville)
    province = province.province
    province = province.upper()

    template = 'rapport.html'

    # Request to fecth data into database
    cargaison = Cargaison.objects.get(idcargaison=pk)

    print('DEBUG')

    if cargaison.numCertInspection == None:
        numCertInspection = num_cert_inspection(ville)
        cargaison.numCertInspection = numCertInspection
        cargaison.save(update_fields=['numCertInspection'])
    else:
        numCertInspection = cargaison.numCertInspection

    # print('DEBUG')
    # print(numact)

    try:
        inspection = Inspection.objects.get(idcargaison=pk)
        if inspection.meterbefore is None:
            inspection.meterbefore = 0
        if inspection.meterafter is None:
            inspection.meterafter = 0
        seal = InspectionSeal.objects.filter(idcargaison=pk)
        if Resultat.objects.filter(idcargaison_id=pk).exists():
            resultat_data = Resultat.objects.get(idcargaison_id=pk)

        compartiment = Compartiment.objects.filter(
            idinspection=inspection.idinspection)  # Filter Database for all the save compartiment
        govTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('gov', flat=True)), 3))  # gov Total Tanker
        gsvTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('gsv', flat=True)), 3))  # gsv Total Tanker
        mtaTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('mta', flat=True)), 3))  # mta Total Tanker
        mtvTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('mtv', flat=True)), 3))  # mtv Total Tanker

        densite = densite15(inspection.temp, inspection.dens)  # densite 15c
        govMeter = round((inspection.meterafter - inspection.meterbefore) / 1000, 3)  # govmeter
        vcfMeter = vcf(densite, inspection.temp)  # vcfMeter
        gsvMeter = gsv(vcfMeter, govMeter)  # gsvMeter
        mtaMeter = mta(gsvMeter, densite)  # mta Meter

        govLt = float(cargaison.volume)  # gov LT
        vcfLt = vcf(densite, inspection.temp)  # VCF LT
        gsvLt = (cargaison.volume15)  # GSV LT
        if gsvLt is None:
            gsvLt = 0
        # gsvLt = gsv(vcfLt, govLt)  # GSV LT
        mtvLt = (cargaison.tonnagevide)  # MTV LT
        if mtvLt is None:
            mtvLt = 0
        # mtvLt = mtv(gsvLt, densite)  # MTV LT
        mtaLt = (cargaison.tonnageair)  # MTA LT
        if mtaLt is None:
            mtaLt = 0
        # mtaLt = mta(gsvLt, densite)  # MTA LT

        govLtTanker = round((govLt - float(govTotal)), 3)  # Difference LT/Tanker
        gsvLtTanker = round((float(gsvLt) - float(gsvTotal)), 3)  # Difference GSV LT/Tanker
        mtvLtTanker = round((float(mtvLt) - float(mtvTotal)), 3)  # Difference mtv LT/Tanker
        mtaLtTanker = round((float(mtaLt) - float(mtaTotal)), 3)  # Difference mtv LT/Tanker
        prLtTanker = round((govLtTanker * 100) / govLt, 3)
        if gsvLt == 0:
            gsvLt = 1
        prGsvLtTanker = round((gsvLtTanker * 100) / float(gsvLt), 3)
        if mtaLt == 0:
            mtaLt = 1
        prMtaLtTanker = round((mtaLtTanker / (float(mtaLt)) * 100), 3)
        if mtvLt == 0:
            mtvLt = 1
        prMtvLtTanker = round((mtvLtTanker / (float(mtvLt)) * 100), 3)

        govTankerMeter = float(govTotal) - float(govMeter)  # Difference Tanker/Meter
        gsvTankerMeter = float(gsvTotal) - float(gsvMeter)  # Difference GSV Tanker/Meter
        mtaTankerMeter = round((float(mtaTotal) - mtaMeter), 3)  # Difference MTA Tanker/Meter
        prTankerMeter = round((govTankerMeter * 100) / float(govTotal), 3)

        govLtMeter = govLt - govMeter  # Diff LT/Meter
        gsvLtMeter = round((float(gsvLt) - gsvMeter), 3)  # Diff GSV LT/Meter
        mtaLtMeter = float(mtaLt) - mtaMeter  # Diff mta LT/Meter
        if govLt == 0:
            govLt = 1
        prLtMeter = round((govLtMeter * 100) / govLt, 3)
        if gsvLt == 0:
            gsvLt = 1
        prGsvLtMeter = round((gsvLtMeter * 100) / float(gsvLt), 3)
        if mtaLt == 0:
            mtaLt = 1
        prMtaLtMeter = round((mtaLtMeter * 100) / float(mtaLt), 3)

        # Certified Quantity
        if govMeter > 0:
            govMax = govMeter
            gsvMax = gsvMeter
            mtaMax = mtaMeter
        else:
            if float(govTotal) > 0:
                govMax = govTotal
                gsvMax = gsvTotal
                mtaMax = mtaTotal
            else:
                if govLt > 0:
                    govMax = govLt
                    gsvMax = gsvLt
                    mtaMax = mtaLt

        # govMax = round((max(govTotal, govMeter, govLt)),3)  # Max value of GOV
        # gsvMax = round((max(gsvTotal, gsvMeter, gsvLt)),3)  # Max value of GSV
        # mtaMax = round((max(mtaTotal, mtaMeter, mtaLt)),3)  # Max value of MTA

        fraisOcc = round((11 * float(gsvMax)), 3)  # Frais occ a Payer

        # Getting data from laboratory
        if Resultat.objects.filter(idcargaison_id=pk).exists():
            labo_data = Resultat.objects.get(idcargaison=pk)
            color = labo_data.couleurastm
            aspect = labo_data.aspect
            odor = labo_data.odeur
        else:
            color = '-'
            aspect = '-'
            odor = '-'

        # Last 3 Cargo Data Fetch
        lastthreecargo = Cargaison.objects.filter(immatriculation=cargaison.immatriculation).order_by(
            '-dateheurecargaison')[:3]

        data = {
            'cargaison': cargaison,
            'numCertInspection': numCertInspection,
            'inspection': inspection,
            'densite': densite,
            'prGsvLtTanker': prGsvLtTanker,
            'prMtaLtTanker': prMtaLtTanker,
            'prMtvLtTanker': prMtvLtTanker,
            'prGsvLtMeter': prGsvLtMeter,
            'prMtaLtMeter': prMtaLtMeter,
            'prLtTanker': prLtTanker,
            'prTankerMeter': prTankerMeter,
            'prLtMeter': prLtMeter,
            'govmeter': govMeter,
            'govTotal': govTotal,
            'gsvTotal': gsvTotal,
            'mtaTotal': mtaTotal,
            'gsvMeter': gsvMeter,
            'govLt': govLt,
            'govLtTanker': govLtTanker,
            'govTankerMeter': govTankerMeter,
            'gsvTankerMeter': gsvTankerMeter,
            'mtaTankerMeter': mtaTankerMeter,
            'govLtMeter': govLtMeter,
            'gsvLtTanker': gsvLtTanker,
            'mtvLtTanker': mtvLtTanker,
            'mtaLtTanker': mtaLtTanker,
            'gsvLtMeter': gsvLtMeter,
            'mtaLtMeter': mtaLtMeter,
            'gsvLt': gsvLt,
            'mtvLt': mtvLt,
            'mtaLt': mtaLt,
            'govMax': govMax,
            'gsvMax': gsvMax,
            'mtaMax': mtaMax,
            'fraisOcc': fraisOcc,
            'seal': seal,
            'lastthreecargo': lastthreecargo,
            # 'flast': flast,
            # 'slast': slast,
            # 'tlast': tlast,
            'color': color,
            'aspect': aspect,
            'odor': odor,
            'compartiment': compartiment,
            'province': province,

        }
        # Render PDF Files
        pdf = render_to_pdf(template, data)
        return HttpResponse(pdf, content_type='application/pdf')
    except:
        return redirect('rapportActivite')


@login_required(login_url='login')
def consignation(request, pk):
    c = Cargaison.objects.get(idcargaison=pk)
    i = ImpressionResultat.objects.get(idcargaison=c)
    i.control = 1
    c.toBeConsignated = 1
    i.save(update_fields=['control'])
    c.save(update_fields=['toBeConsignated'])
    return redirect('affichageNonConforme')


@login_required(login_url='login')
def regularisationCargaison(request):
    user = request.user
    role = user.role_id
    u = user.id
    form = RegularisationNouvelleEntree(request.POST or None)
    if form.is_valid():
        instance = form.save(commit=False)
        qrcode = str(uuid.uuid4())
        instance.qrcode = qrcode
        instance.user = u
        instance.etat = "En attente requisition"
        instance.save()
        return redirect('regularisation')
    else:
        return redirect('logout')


@login_required(login_url='login')
def regularisationImportateur(request):
    user = request.user
    role = user.role_id
    u = user.id
    if request.method == 'POST':
        i = Importateur(
            nomimportateur=request.POST['nomimportateur'],
            nifimportateur=request.POST['nifimportateur'],
            adresseimportateur=request.POST['adresseimportateur'],
            email=request.POST['email']
        )
        i.save()
        return redirect('regularisation')
    else:
        return redirect('logout')


@login_required(login_url='login')
def regularisationEntrepot(request):
    user = request.user
    role = user.role_id
    u = user.id
    if request.method == 'POST':
        v = Ville.objects.get(idville=request.POST['ville'])
        e = Entrepot(
            nomentrepot=request.POST['nomentrepot'],
            ville=v,
            adresseentrepot=request.POST['adresseentrepot']
        )
        e.save()
        return redirect('regularisation')
    else:
        return redirect('logout')


@login_required(login_url='login')
def changementImportateur(request):
    # cargaison = Cargaison.objects.get(idcargaison=pk)
    if request.method == 'POST':
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            pk = request.POST.get('pk', None)
            print('TEST')
            nouvelImportateur = request.POST.get('importateur', None)
            print(nouvelImportateur)
            i = Importateur.objects.get(idimportateur=nouvelImportateur)
            cargaison = Cargaison.objects.get(idcargaison=pk)
            cargaison.importateur = i
            cargaison.save(update_fields=['importateur'])
            # Return a JSON response indicating success
            return JsonResponse({'status': 'success'})
        else:
            return redirect('regularisation')
    else:
        return redirect('regularisation')


@login_required(login_url='login')
def regularisationRecherche(request):
    user = request.user
    role = user.role_id
    u = user.id
    template = 'regularisation.html'
    form = ChangementDestination()
    form1 = Transbordement()
    form2 = ChangementNatureProduit()
    form3 = ImportateurRegularisationForm()
    form4 = EntrepotRegularisationForm()
    form5 = RegularisationNouvelleEntree()
    form6 = ChangementImportateur()
    if request.method == 'GET':
        search_value = request.GET.get('search_query', '')
        # search_value = request.GET['search_query']
        if search_value:
            qs = Cargaison.objects.filter(
                entrepot__ville__affectationville__username_id=u).filter(
                Q(etat='En attente requisition') | Q(etat="En attente d'echantillonage") | Q(
                    etat="Conforme aux exigences"),
                Q(frontiere__nomville__icontains=search_value) |
                Q(importateur__nomimportateur__icontains=search_value) |
                Q(entrepot__nomentrepot__icontains=search_value) |
                Q(produit__nomproduit__icontains=search_value) |
                Q(immatriculation__icontains=search_value) |
                Q(declaration__icontains=search_value) |
                Q(numreq__icontains=search_value)
            ).order_by('-dateheurecargaison')

            table = Regularisation(qs)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            context = {
                'table': table,
                'form': form,
                'form1': form1,
                'form2': form2,
                'form3': form3,
                'form4': form4,
                'form5': form5,
                'form6': form6,
            }
            return render(request, template, context)
        else:
            return redirect('regularisation')
    else:
        return redirect('regularisation')


@login_required(login_url='login')
def rechercheRapportActivite(request):
    user = request.user.id
    search = request.GET.get('search', None)
    print("SEARCH")
    print(search)
    template = 'rapportActiviteFirst.html'
    form = Filters(user=user)
    #
    qs = Cargaison.objects.annotate(
        volConst=Sum('inspection__compartiment__gov'),
        gsvT=Sum('inspection__compartiment__gsv'),
        mtaTotal=Sum('inspection__compartiment__mta'),
        mtvTotal=Sum('inspection__compartiment__mtv'),
    ).values('idcargaison', 'mtvTotal',
             'numdos', 'declaration', 'frontiere__nomville', 'inspection__dens', 'inspection__temp', 'mtaTotal',
             'entrepot__nomentrepot', 'inspection__dateinspection', 'importateur__nomimportateur', 'immatriculation',
             'produit__nomproduit', 'dateheurecargaison',
             'requisitiondackdate', 'entrepot_echantillon__dateechantillonage',
             'entrepot_echantillon__laboreception__datereceptionlabo', 'impressionresultat__printDate',
             'inspection__dateinspection', 'volume', 'volConst', 'gsvT'
             ).order_by('-dateheurecargaison')

    filter = qs.filter(
        Q(immatriculation__icontains=search) |
        Q(declaration__icontains=search) |
        Q(numdos__icontains=search)
    )

    # qs = list(qs)
    table = RapportActivite(filter)
    RequestConfig(request, paginate={"per_page": 7}).configure(table)
    context = {
        'table': table,
        'form': form
    }
    return render(request, template, context)


@login_required(login_url='login')
def reInspecter(request):
    user = request.user.id
    if request.method == 'POST':
        data = json.loads(request.body)
        pk = data.get('rowId')
        print(pk)
        cargaison = Cargaison.objects.get(idcargaison=pk)
        try:
            inspection = Inspection.objects.get(idcargaison=cargaison)
            if Compartiment.objects.filter(idinspection=inspection).exists():
                Compartiment.objects.filter(idinspection=inspection).delete()
                cargaison.etatInspection = 1
                cargaison.save(update_fields=['etatInspection'])
                return redirect('rapportActivite')
            else:
                cargaison.etatInspection = 1
                cargaison.save(update_fields=['etatInspection'])
                return redirect('rapportActivite')
        except:
            return redirect('rapportActivite')
    else:
        return redirect('rapportActivite')


@login_required(login_url='login')
def impressionRappEch(request):
    # Generer le rapport d'echantillonage
    data = json.loads(request.body)
    pk = data.get('rowId')
    # print('TEST IMPRESSION')
    # print(pk)

    try:
        # Generer le rapport d'echantillonage
        template = 'rapportechantillonage.html'
        c = Cargaison.objects.get(idcargaison=pk)
        e = Entrepot_echantillon.objects.get(idcargaison=pk)
        entrepot = c.entrepot
        dateechantillonage = e.dateechantillonage
        dateech = dateechantillonage
        methodeutilisee = e.methodeutilisee
        matricule = e.matricule
        numdos = c.numdos
        importateur = c.importateur
        adresseimportateur = c.importateur_id
        adresseimportateur = Importateur.objects.get(idimportateur=adresseimportateur).adresseimportateur
        produit = c.produit
        volume = c.volume
        provenance = c.provenance.name
        voie = c.voie.nomvoie
        immatriculation = c.immatriculation
        qtelabo = e.qte
        numrappechauto = e.numrappechauto

        data = {
            'dateechantillonage': dateechantillonage,
            'dateech': dateech,
            'entrepot': entrepot,
            'numdos': numdos,
            'methodeutilisee': methodeutilisee,
            'importateur': importateur,
            'adresseimportateur': adresseimportateur,
            'produit': produit,
            'volume': volume,
            'provenance': provenance,
            'voie': voie,
            'immatriculation': immatriculation,
            'matricule': matricule,
            'qtelabo': qtelabo,
            'numrappechauto': numrappechauto,
        }

        # Render PDF Files
        pdf = render_to_pdf(template, data)

        # Convert PDF content to Base64-encoded string
        pdf_base64 = base64.b64encode(pdf.getvalue()).decode('utf-8')
        return JsonResponse({'status': 'success', 'pdf_base64': pdf_base64})
    except:
        return JsonResponse({'status': 'error'})


@login_required(login_url='login')
def impressionRappInsp(request):
    user = request.user
    ville = AffectationVille.objects.get(username_id=user.id)
    ville = ville.ville_id
    province = Ville.objects.get(idville=ville)
    province = province.province
    province = province.upper()

    template = 'rapport.html'
    # Generer le rapport d'echantillonage
    data = json.loads(request.body)
    pk = data.get('rowId')

    # Request to fecth data into database
    try:
        cargaison = Cargaison.objects.get(idcargaison=pk)
        voie_entree = cargaison.voie.nomvoie

        if cargaison.numCertInspection is None:
            numCertInspection = num_cert_inspection(ville)
            cargaison.numCertInspection = numCertInspection
            cargaison.save(update_fields=['numCertInspection'])
        else:
            numCertInspection = cargaison.numCertInspection

        inspection = Inspection.objects.get(idcargaison=pk)
        if inspection.meterbefore is None:
            inspection.meterbefore = 0
        if inspection.meterafter is None:
            inspection.meterafter = 0
        seal = InspectionSeal.objects.filter(idcargaison=pk)
        if Resultat.objects.filter(idcargaison_id=pk).exists():
            resultat_data = Resultat.objects.get(idcargaison_id=pk)

        compartiment = Compartiment.objects.filter(
            idinspection=inspection.idinspection)  # Filter Database for all the save compartiment
        govTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('gov', flat=True)), 3))  # gov Total Tanker
        gsvTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('gsv', flat=True)), 3))  # gsv Total Tanker
        mtaTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('mta', flat=True)), 3))  # mta Total Tanker
        mtvTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('mtv', flat=True)), 3))  # mtv Total Tanker

        densite = densite15(inspection.temp, inspection.dens)  # densite 15c
        govMeter = round((inspection.meterafter - inspection.meterbefore) / 1000, 3)  # govmeter
        vcfMeter = vcf(densite, inspection.temp)  # vcfMeter
        gsvMeter = gsv(vcfMeter, govMeter)  # gsvMeter
        mtaMeter = mta(gsvMeter, densite)  # mta Meter

        govLt = float(cargaison.volume)  # gov LT
        vcfLt = vcf(densite, inspection.temp)  # VCF LT
        gsvLt = (cargaison.volume15)  # GSV LT
        if gsvLt is None:
            gsvLt = 0
        # gsvLt = gsv(vcfLt, govLt)  # GSV LT
        mtvLt = (cargaison.tonnagevide)  # MTV LT
        if mtvLt is None:
            mtvLt = 0
        # mtvLt = mtv(gsvLt, densite)  # MTV LT
        mtaLt = (cargaison.tonnageair)  # MTA LT
        if mtaLt is None:
            mtaLt = 0
        # mtaLt = mta(gsvLt, densite)  # MTA LT

        govLtTanker = round((govLt - float(govTotal)), 3)  # Difference LT/Tanker
        gsvLtTanker = round((float(gsvLt) - float(gsvTotal)), 3)  # Difference GSV LT/Tanker
        mtvLtTanker = round((float(mtvLt) - float(mtvTotal)), 3)  # Difference mtv LT/Tanker
        mtaLtTanker = round((float(mtaLt) - float(mtaTotal)), 3)  # Difference mtv LT/Tanker
        prLtTanker = round((govLtTanker * 100) / govLt, 3)
        if gsvLt == 0:
            gsvLt = 1
        prGsvLtTanker = round((gsvLtTanker * 100) / float(gsvLt), 3)
        if mtaLt == 0:
            mtaLt = 1
        prMtaLtTanker = round((mtaLtTanker / (float(mtaLt)) * 100), 3)
        if mtvLt == 0:
            mtvLt = 1
        prMtvLtTanker = round((mtvLtTanker / (float(mtvLt)) * 100), 3)

        govTankerMeter = float(govTotal) - float(govMeter)  # Difference Tanker/Meter
        gsvTankerMeter = float(gsvTotal) - float(gsvMeter)  # Difference GSV Tanker/Meter
        mtaTankerMeter = round((float(mtaTotal) - mtaMeter), 3)  # Difference MTA Tanker/Meter
        prTankerMeter = round((govTankerMeter * 100) / float(govTotal), 3)

        govLtMeter = govLt - govMeter  # Diff LT/Meter
        gsvLtMeter = round((float(gsvLt) - gsvMeter), 3)  # Diff GSV LT/Meter
        mtaLtMeter = float(mtaLt) - mtaMeter  # Diff mta LT/Meter
        if govLt == 0:
            govLt = 1
        prLtMeter = round((govLtMeter * 100) / govLt, 3)
        if gsvLt == 0:
            gsvLt = 1
        prGsvLtMeter = round((gsvLtMeter * 100) / float(gsvLt), 3)
        if mtaLt == 0:
            mtaLt = 1
        prMtaLtMeter = round((mtaLtMeter * 100) / float(mtaLt), 3)

        # Certified Quantity
        if govMeter > 0:
            govMax = govMeter
            gsvMax = gsvMeter
            mtaMax = mtaMeter
        else:
            if float(govTotal) > 0:
                govMax = govTotal
                gsvMax = gsvTotal
                mtaMax = mtaTotal
            else:
                if govLt > 0:
                    govMax = govLt
                    gsvMax = gsvLt
                    mtaMax = mtaLt

        # govMax = round((max(govTotal, govMeter, govLt)),3)  # Max value of GOV
        # gsvMax = round((max(gsvTotal, gsvMeter, gsvLt)),3)  # Max value of GSV
        # mtaMax = round((max(mtaTotal, mtaMeter, mtaLt)),3)  # Max value of MTA

        fraisOcc = round((11 * float(gsvMax)), 3)  # Frais occ a Payer

        # Getting data from laboratory
        if Resultat.objects.filter(idcargaison_id=pk).exists():
            labo_data = Resultat.objects.get(idcargaison=pk)
            color = labo_data.couleurastm
            aspect = labo_data.aspect
            odor = labo_data.odeur
        else:
            color = '-'
            aspect = '-'
            odor = '-'

        # Last 3 Cargo Data Fetch
        lastthreecargo = Cargaison.objects.filter(immatriculation=cargaison.immatriculation).order_by(
            '-dateheurecargaison')[:3]

        data = {
            'voie': voie_entree,
            'cargaison': cargaison,
            'province': province,
            'numCertInspection': numCertInspection,
            'inspection': inspection,
            'densite': densite,
            'prGsvLtTanker': prGsvLtTanker,
            'prMtaLtTanker': prMtaLtTanker,
            'prMtvLtTanker': prMtvLtTanker,
            'prGsvLtMeter': prGsvLtMeter,
            'prMtaLtMeter': prMtaLtMeter,
            'prLtTanker': prLtTanker,
            'prTankerMeter': prTankerMeter,
            'prLtMeter': prLtMeter,
            'govmeter': govMeter,
            'govTotal': govTotal,
            'gsvTotal': gsvTotal,
            'mtaTotal': mtaTotal,
            'gsvMeter': gsvMeter,
            'govLt': govLt,
            'govLtTanker': govLtTanker,
            'govTankerMeter': govTankerMeter,
            'gsvTankerMeter': gsvTankerMeter,
            'mtaTankerMeter': mtaTankerMeter,
            'govLtMeter': govLtMeter,
            'gsvLtTanker': gsvLtTanker,
            'mtvLtTanker': mtvLtTanker,
            'mtaLtTanker': mtaLtTanker,
            'gsvLtMeter': gsvLtMeter,
            'mtaLtMeter': mtaLtMeter,
            'gsvLt': gsvLt,
            'mtvLt': mtvLt,
            'mtaLt': mtaLt,
            'govMax': govMax,
            'gsvMax': gsvMax,
            'mtaMax': mtaMax,
            'fraisOcc': fraisOcc,
            'seal': seal,
            'lastthreecargo': lastthreecargo,
            # 'flast': flast,
            # 'slast': slast,
            # 'tlast': tlast,
            'color': color,
            'aspect': aspect,
            'odor': odor,
            'compartiment': compartiment,

        }
        # Render PDF Files
        pdf = render_to_pdf(template, data)
        # Convert PDF content to Base64-encoded string
        pdf_base64 = base64.b64encode(pdf.getvalue()).decode('utf-8')
        return JsonResponse({'status': 'success', 'pdf_base64': pdf_base64})
    except:
        return JsonResponse({'status': 'error'})


def tasks(request):
    qs = Cargaison.objects.annotate(
        volConst=Sum('inspection__compartiment__gov'),
        gsvT=Sum('inspection__compartiment__gsv'),
        mtaTotal=Sum('inspection__compartiment__mta'),
        mtvTotal=Sum('inspection__compartiment__mtv'),
    ).values('inspection__compartiment__vcf',
             'idcargaison', 'numdos', 'declaration', 'frontiere__nomville', 'inspection__idinspection',
             'entrepot__ville__nomville',
             'inspection__dateinspection', 'importateur__nomimportateur', 'entrepot__nomentrepot', 'immatriculation',
             'produit__nomproduit', 'dateheurecargaison__date', 'requisitiondackdate__date',
             'entrepot_echantillon__dateechantillonage__date', 'inspection__dens', 'inspection__temp',
             'entrepot_echantillon__laboreception__datereceptionlabo__date', 'mtaTotal', 'mtvTotal',
             'impressionresultat__printDate', 'inspection__dateinspection', 'volume', 'volConst', 'gsvT'
             ).order_by('-inspection__dateinspection')

    # Convert QuerySet to list of dictionaries
    data = list(qs)

    df = pd.DataFrame(list(qs))

    # Rename the columns
    df = df.rename(columns={
        'idcargaison': 'ID CARGAISON',
        'inspection__idinspection': 'ID INSPECTION',
        'numdos': 'NUM.DOSSIER',
        'declaration': 'DECLARATION (T1E OU TR8)',
        'frontiere__nomville': 'FRONTIERE',
        'entrepot__ville__nomville': 'ENTREPOT',
        'frontiere__nomville': 'FRONTIERE',
        'importateur__nomimportateur': 'IMPORTATEUR',
        'entrepot__nomentrepot': 'ENTREPOT',
        'immatriculation': 'IMMATRICULATION',
        'produit__nomproduit': 'PRODUIT',
        'dateheurecargaison__date': 'DATE ENTREE',
        'requisitiondackdate__date': 'DATE REQUISITION',
        'entrepot_echantillon__dateechantillonage__date': 'DATE ECHANTILLONNAGE',
        'entrepot_echantillon__laboreception__datereceptionlabo__date': 'DATE RECEPTION LABO',
        'inspection__dateinspection': 'DATE INSPECTION',
        'inspection__dens': 'DENSITE',
        'inspection__temp': 'TEMPERATURE',
        'volume': 'VOL DECLARE',
        'volConst': 'VOL JAUGE',
        'volConst': 'VOL JAUGE',
        'inspection__compartiment__vcf': 'VCF',
        'gsvT': 'GSV',
        'mtaTotal': 'MTA',
        'mtvTotal': 'MTV',
    })

    # Create a BytesIO object to store the Excel file
    excel_file = pd.ExcelWriter('data.xlsx', engine='xlsxwriter')
    df.to_excel(excel_file, index=False)
    excel_file.save()

    # Open the file for reading
    with open('data.xlsx', 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=data.xlsx'
        return response

    # df = pd.DataFrame(qs)
    # df = df.to_json()
    #
    # # Trigger the Celery task
    # task = export_to_excel.delay(data)
    #
    # # Context
    # context = {'task_id':task.id}
    #
    # # Redirect the user to a page indicating that the export is in progress
    # return JsonResponse(context, status=200)


@csrf_exempt
def get_status(request, task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return JsonResponse(result, status=200)


@login_required(login_url='login')
def gestionGo(request):
    # # template = 'display_progress.html'
    template = 'gestionGo.html'
    user = request.user
    id = user.id
    role = user.role_id

    if role == 7 or role == 1:
        e = Cargaison.objects.filter(etat="En attente d'echantillonage",
                                     entrepot__ville__affectationville__username_id=id).count()
        d = ImpressionResultat.objects.filter(isConforme=1, idcargaison__etat="Conforme aux exigences",
                                              idcargaison__entrepot__ville__affectationville__username_id=id).count()
        l = Cargaison.objects.filter(etat="Analyse Labo en cours",
                                     entrepot__ville__affectationville__username_id=id).count()
        n = ImpressionResultat.objects.filter(idcargaison__entrepot__ville__affectationville__username_id=id,
                                              isConforme=0, control=1).count()
        p = Entrepot_echantillon.objects.filter(
            idcargaison__etat='Echantillonner',
            idcargaison__entrepot__ville__affectationville__username_id=id
        ).count()

        c = Cargaison.objects.filter(
            entrepot__ville__affectationville__username_id=id
        ).count()

        context = {
            'e': e,
            'd': d,
            'l': l,
            'n': n,
            'p': p,
            'c': c,

        }
        return render(request, template, context)
    else:
        return redirect('logout')


@login_required(login_url='login')
def gestionGoResponse(request):
    user = request.user
    id = user.id
    qs = Cargaison.objects.filter(
        etat="En attente requisition",
        entrepot__ville__affectationville__username_id=id
    ).select_related(
        'dateheurecargaison',
        'importateur',
        'entrepot',
        'produit'
    ).values(
        'idcargaison',
        'dateheurecargaison__date',
        'importateur__nomimportateur',
        'entrepot__nomentrepot',
        'produit__nomproduit',
        'volume',
        'immatriculation',
        'declaration',
        'numreq'
    ).order_by('-dateheurecargaison', 'frontiere__nomville')

    # Get the search value from the request's GET parameters
    search_value = request.GET.get('search[value]', '')

    # Apply search filter to the QuerySet
    if search_value:
        qs = qs.filter(
            Q(dateheurecargaison__date__icontains=search_value) |
            Q(importateur__nomimportateur__icontains=search_value) |
            Q(entrepot__nomentrepot__icontains=search_value) |
            Q(produit__nomproduit__icontains=search_value) |
            Q(volume__icontains=search_value) |
            Q(immatriculation__icontains=search_value) |
            Q(declaration__icontains=search_value) |
            Q(numreq__icontains=search_value)
        )

    # Number of items to show per page
    items_per_page = 8

    # Initialize the Paginator with the QuerySet and the number of items per page
    paginator = Paginator(qs, items_per_page)

    # Get the current page number from the request's GET parameters
    draw = int(request.GET.get('draw', 1))  # Get the draw value for proper AJAX handling
    start = int(request.GET.get('start', 0))  # Get the starting index for pagination
    length = int(request.GET.get('length', items_per_page))  # Get the number of items per page

    # Calculate the current page number based on start and length
    current_page = (start // length) + 1

    try:
        # Get the current page from the Paginator
        page = paginator.page(current_page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), return an empty JSON response.
        return JsonResponse({'data': [], 'draw': draw, 'recordsTotal': 0, 'recordsFiltered': 0})

    # Convert the page object to a list of dictionaries
    data = list(page)

    # Check if it's an AJAX request and if the export flag is set
    export = request.GET.get('export', None)
    if export == 'excel':
        # Retrieve all data (no lazy pagination) and store it in a list
        data = list(qs)

        # Create a new Excel workbook
        workbook = Workbook()
        sheet = workbook.active

        # Write headers to the Excel file
        header_row = ['DATE ENTREE', 'FOURNISSEUR', 'ENTREPOT', 'PRODUIT', 'VOL.DECL.', 'IMMATR.',
                      '#.T1D',
                      '#.REQ.']
        sheet.append(header_row)

        # Write data rows to the Excel file
        for row in data:
            sheet.append([
                row['dateheurecargaison__date'],
                row['importateur__nomimportateur'],
                row['entrepot__nomentrepot'],
                row['produit__nomproduit'],
                row['volume'],
                row['immatriculation'],
                row['declaration'],
                row['numreq'],
            ])

        # Create an in-memory stream to hold the Excel file data
        excel_stream = io.BytesIO()
        workbook.save(excel_stream)
        excel_stream.seek(0)

        # Prepare the response to return the Excel file
        response = HttpResponse(excel_stream,
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="rapport_brut_journalier.xlsx"'
        return response

    # Return JSON response with the data
    return JsonResponse({
        'data': data,
        'draw': draw,
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
    })


@login_required(login_url='login')
def tableaudeBordHydro(request):
    user_id = request.user.id
    current_year = date.today().year

    base = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user_id
    )
    year_qs = base.filter(dateheurecargaison__year=current_year)

    agg = year_qs.aggregate(
        e=Count('idcargaison', filter=Q(etat="En attente d'echantillonage")),
        l=Count('idcargaison', filter=Q(etat="Analyse Labo en cours")),
        p=Count('idcargaison', filter=Q(etat="Echantillonner")),
        i=Count('idcargaison', filter=Q(etatInspection=True)),
        c=Count('idcargaison'),

        gasoilVolume=Cast(
            Coalesce(Sum('volume', filter=Q(produit_id=2)), Value(0.0)),
            CharField()
        ),
        mogasVolume=Cast(
            Coalesce(Sum('volume', filter=Q(produit_id=1)), Value(0.0)),
            CharField()
        ),
        jetVolume=Cast(
            Coalesce(Sum('volume', filter=Q(produit_id=3)), Value(0.0)),
            CharField()
        ),
        petroleVolume=Cast(
            Coalesce(Sum('volume', filter=Q(produit_id=4)), Value(0.0)),
            CharField()
        ),
        totalVolume=Cast(
            Coalesce(Sum('volume'), Value(0.0)),
            CharField()
        ),
    )

    imp_agg = ImpressionResultat.objects.filter(
        idcargaison__in=year_qs.values('idcargaison')
    ).aggregate(
        d=Count('idImpression', filter=Q(idcargaison__etat="Conforme aux exigences")),
        n=Count('idImpression', filter=Q(isConforme=False, control=False)),
    )

    # Percentages must still use numeric values, so recalc from floats
    tv = float(year_qs.aggregate(total=Coalesce(Sum('volume'), Value(0.0)))['total'] or 0.0)
    def pct(x):
        x = float(x or 0.0)
        return round((x/tv)*100) if tv else 0

    context = {
        'e': agg['e'], 'l': agg['l'], 'p': agg['p'], 'i': agg['i'], 'c': agg['c'],
        'd': imp_agg['d'], 'n': imp_agg['n'],
        'gasoilVolume': agg['gasoilVolume'],
        'mogasVolume':  agg['mogasVolume'],
        'jetVolume':    agg['jetVolume'],
        'petroleVolume':agg['petroleVolume'],
        'totalVolume':  agg['totalVolume'],
        'gasoilPercentage':  pct(agg['gasoilVolume']),
        'mogasPercentage':   pct(agg['mogasVolume']),
        'jetPercentage':     pct(agg['jetVolume']),
        'petrolePercentage': pct(agg['petroleVolume']),
        'current_year': current_year,
    }
    return render(request, 'dashboardHydro.html', context)



@login_required(login_url='login')
def lastrecordShydro(request):
    user = request.user
    user_id = getattr(user, "id", None)
    if not user_id:
        # Not authenticated or no id — return empty dataset
        return JsonResponse({"data": []})

    qs = (
        Cargaison.objects
        .select_related("frontiere", "importateur", "entrepot", "produit")
        .filter(
            etat="En attente requisition",
            entrepot__ville__affectationville__username_id=user_id,
        )
        .order_by("-dateheurecargaison")[:5]   # limit first, then serialize
    )

    data = [
        {
            "dateheurecargaison": (
                c.dateheurecargaison.isoformat() if c.dateheurecargaison else None
            ),
            "frontiere__nomville": c.frontiere.nomville if c.frontiere_id else "",
            "importateur__nomimportateur": (
                c.importateur.nomimportateur if c.importateur_id else ""
            ),
            "entrepot__nomentrepot": c.entrepot.nomentrepot if c.entrepot_id else "",
            "produit__nomproduit": c.produit.nomproduit if c.produit_id else "",
            "volume": float(c.volume) if c.volume is not None else None,
        }
        for c in qs
    ]

    return JsonResponse({"data": data})


@login_required(login_url='login')
def topImportersShydro(request):
    user = request.user
    id = user.id
    # Get the sum of volume for each product type
    top_importers = Cargaison.objects.filter(entrepot__ville__affectationville__username_id=id).values(
        'importateur__nomimportateur').annotate(
        total_volume=Round(Sum('volume'), 2)
    ).order_by('-total_volume')[:10]

    # Serialize the queryset as a list of dictionaries
    data = list(top_importers)

    # Return JSON response with the data
    return JsonResponse({
        'data': data
    })


@login_required(login_url='login')
def productCountShydro(request):
    user = request.user
    id = user.id
    gasoilCount = Cargaison.objects.filter(entrepot__ville__affectationville__username_id=id, produit=2).count()
    mogasCount = Cargaison.objects.filter(entrepot__ville__affectationville__username_id=id, produit=1).count()
    jetCount = Cargaison.objects.filter(entrepot__ville__affectationville__username_id=id, produit=3).count()
    petroleCount = Cargaison.objects.filter(entrepot__ville__affectationville__username_id=id, produit=4).count()

    data = {
        'gasoilCount': gasoilCount,
        'mogasCount': mogasCount,
        'jetCount': jetCount,
        'petroleCount': petroleCount,
    }

    # Return JSON response with the data
    return JsonResponse({
        'data': data
    })


@login_required(login_url='login')
def afficherDossImport(request):
    if request.method == 'POST':
        user = request.user
        id = user.id

        data = json.loads(request.body)
        pk = data.get('rowId')

        cargaison = Cargaison.objects.get(idcargaison=pk)

        file_path = cargaison.files_path  # Specify the path to your file in the Space

        # Fetch file content from DigitalOcean Space
        file_content = download_file_from_space(file_path)

        if file_content:
            # Encode the file content as Base64
            encoded_content = base64.b64encode(file_content).decode('utf-8')

            # Return the encoded file content in the JSON response
            return JsonResponse({'file_content': encoded_content}, status=200)
        else:
            return JsonResponse({'error': "File not found or unable to download."}, status=404)
    else:
        return JsonResponse({'error': "Invalid request method."}, status=400)


@login_required(login_url='login')
def dataSanitizing(request):
    template='data_sanitizing.html'
    context = {}
    return render( request, template, context)


@login_required(login_url='login')
@csrf_exempt
def data_duplicate(request):
    # template='data_sanitizing.html'
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        # Load Excel into pandas
        df = pd.read_excel(excel_file)
        df.columns = df.columns.str.strip()  # Clean column names

        try:
            entry_date_col = df.columns[1]   # Column 2
            decl_col = df.columns[3]         # Column 4
            immatriculation_col = df.columns[6]  # Column 7
            date_req_col = df.columns[8]     # Column 9
        except IndexError:
            return HttpResponse("The Excel file does not contain the required number of columns.", status=400)

        # Identify duplicates
        df['Duplicate'] = df.duplicated(
            subset=[entry_date_col, decl_col, immatriculation_col],
            keep=False
        )

        # Get only duplicates with missing DATE REQ.
        duplicates_missing_req = df[
            (df['Duplicate']) & (df[date_req_col].isna())
        ]

        # Remove from main dataframe
        cleaned_df = df.drop(duplicates_missing_req.index)

        # Save to Excel in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            cleaned_df.drop(columns='Duplicate').to_excel(writer, index=False, sheet_name='Cleaned Data')
            duplicates_missing_req.drop(columns='Duplicate').to_excel(writer, index=False, sheet_name='Removed Duplicates')

        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=cleaned_duplicates_report.xlsx'
        return response

    # context = {}
    # return render( request, template, context)


@login_required(login_url='login')
def data_merge(request):
    template='data_sanitizing.html'
    context = {}
    return render( request, template, context)


def _rapport_base_qs(request):
    """
    Build the base queryset with safe float aggregates and explicit subquery types.
    """

    # Aggregate Compartiment per Cargaison through Inspection (O2O):
    #   Compartiment.idinspection -> Inspection
    #   Inspection.idcargaison_id == Cargaison.idcargaison
    comp_agg = (
        Compartiment.objects
        .filter(idinspection__idcargaison_id=OuterRef('idcargaison'))
        .values('idinspection__idcargaison_id')  # group by cargaison
        .annotate(
            # Important: put output_field=FloatField on Coalesce to avoid MySQL issues
            total_gov=Coalesce(Sum('gov'), Value(0.0), output_field=FloatField()),
            total_gsv=Coalesce(Sum('gsv'), Value(0.0), output_field=FloatField()),
            total_mta=Coalesce(Sum('mta'), Value(0.0), output_field=FloatField()),
            total_mtv=Coalesce(Sum('mtv'), Value(0.0), output_field=FloatField()),
        )
    )

    qs = (
        Cargaison.objects
        .select_related(
            # single-valued FKs/O2O:
            'entrepot', 'entrepot__ville',
            'frontiere', 'importateur', 'produit',
            'inspection',  # OneToOne from Inspection to Cargaison
        )
        .prefetch_related(
            # reverse O2O + its O2O:
            'entrepot_echantillon',
            'entrepot_echantillon__laboreception',
        )
        .annotate(
            # pull subquery aggregates (force FloatField result)
            volConst = Subquery(comp_agg.values('total_gov')[:1], output_field=FloatField()),
            gsvT     = Subquery(comp_agg.values('total_gsv')[:1], output_field=FloatField()),
            mtaTotal = Subquery(comp_agg.values('total_mta')[:1], output_field=FloatField()),
            mtvTotal = Subquery(comp_agg.values('total_mtv')[:1], output_field=FloatField()),

            # dates along O2O chains
            echantillon_date = Max('entrepot_echantillon__dateechantillonage'),
            labo_recep_date  = Max('entrepot_echantillon__laboreception__datereceptionlabo'),
            print_date       = Max('impressionresultat__printDate'),
        )
        .order_by('-dateheurecargaison')
    )

    # Optional per-user filter (leave wrapped in try in case that relation doesn't exist in your DB)
    user_id = request.user.id if request.user.is_authenticated else None
    if user_id:
        try:
            qs = qs.filter(entrepot__ville__affectationville__username_id=user_id)
        except Exception:
            # If no AffectationVille relation is present, just skip filtering
            pass

    # Optional search (?search=…)
    search = (request.GET.get('search') or '').strip()
    if search:
        qs = qs.filter(
            Q(immatriculation__icontains=search) |
            Q(numdos__icontains=search) |
            Q(declaration__icontains=search)
        )

    return qs


@login_required
def rapportActiviteData(request):
    """
    JSON endpoint for the JS table.
    Accepts: page, page_size, search (handled in _rapport_base_qs)
    """
    page = int(request.GET.get('page', 1) or 1)
    page_size = int(request.GET.get('page_size', 15) or 15)

    # Only pick the fields your table needs
    qs = _rapport_base_qs(request).values(
        'idcargaison',
        'numdos',
        'declaration',
        'frontiere__nomville',
        'inspection__dens',
        'inspection__temp',
        'mtaTotal',
        'mtvTotal',
        'entrepot__nomentrepot',
        'inspection__dateinspection',
        'importateur__nomimportateur',
        'immatriculation',
        'produit__nomproduit',
        'dateheurecargaison',
        'requisitiondackdate',
        'echantillon_date',
        'labo_recep_date',
        'print_date',
        'volume',
        'volConst',
        'gsvT',
    )

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    # DjangoJSONEncoder handles date/datetime → string for JsonResponse
    return JsonResponse({
        "results": list(page_obj.object_list),
        "page": page_obj.number,
        "num_pages": paginator.num_pages,
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
        "next_page_number": page_obj.next_page_number() if page_obj.has_next() else None,
        "previous_page_number": page_obj.previous_page_number() if page_obj.has_previous() else None,
    })