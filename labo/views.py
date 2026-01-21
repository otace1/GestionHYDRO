import base64
import io
import json
from datetime import datetime, timedelta, time

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.db.models import Q, F, Case, When, Value, CharField, Count, Subquery, OuterRef, Exists
from django.db.models.functions import ExtractMonth, ExtractYear, Coalesce
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
import boto3
from django.core.files.storage import default_storage
from django.views.decorators.http import require_POST
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport
from django_tables2.paginators import LazyPaginator
from openpyxl import Workbook

from accounts.models import AffectationVille, AffectationLaboratoire, ListeLaboratoire, MyUser, UserActivityLog
from enreg.models import *
from hydrocarbures.celery import app
from celery.result import AsyncResult
from labo.utils import render_to_pdf
from .codeLabo import generate_labo_code
from .forms import *
from .numCq import numCq
from .tables import *
from .tasks import export_reception_rapports_to_xlsx, generate_certificates_pdf_task
import os
import tempfile


# Sending email

# from django.core.mail import send_mail #Sending Email
#

# Class de gestion pouir le laboratoire
# Methode d'affichage des echantillons a la reception
@login_required(login_url='login')
def affichageenchantillon(request):
    template = 'labo.html'
    # Build Entrepôt choices filtered by user's ville affectations
    user = request.user
    try:
        # User's allowed villes via AffectationVille
        user_ville_ids = list(
            AffectationVille.objects.filter(username_id=user.id).values_list('ville_id', flat=True)
        )
    except Exception:
        user_ville_ids = []

    # Import Entrepot model from enreg app if not already
    try:
        from enreg.models import Entrepot
    except Exception:
        Entrepot = None

    entrepots_qs = []
    if Entrepot:
        entrepots_qs = Entrepot.objects.filter(ville_id__in=user_ville_ids).order_by('nomentrepot')

    selected_entrepot_id = request.GET.get('entrepot_id', 'all')

    # Determine if any filter has been applied to control table visibility
    has_filters_applied = False
    if (
            selected_entrepot_id not in (None, '', 'all') or
            (request.GET.get('num_dossier') or '').strip() or
            (request.GET.get('num_re') or '').strip() or
            (request.GET.get('immatriculation') or '').strip() or
            (request.GET.get('qrcode') or '').strip()
    ):
        has_filters_applied = True

    context = {
        "entrepots": entrepots_qs,
        "selected_entrepot_id": selected_entrepot_id,
        "has_filters_applied": has_filters_applied,
    }
    return render(request, template, context)


# If you use these exceptions elsewhere; otherwise remove try/except blocks
# from django.core.paginator import EmptyPage, PageNotAnInteger


@login_required(login_url="login")
@require_POST
def affichageenchantillonResponse(request):
    user = request.user
    user_id = user.id
    role = getattr(user, "role_id", None)

    # Only allowed roles
    if role not in (1, 4):
        return JsonResponse({"success": False, "error": "Forbidden"}, status=403)

    # ---------------------------
    # Read POST payload safely
    # ---------------------------
    def get_payload():
        ct = (request.headers.get("Content-Type") or "").lower()
        if "application/json" in ct:
            try:
                return json.loads(request.body.decode("utf-8") or "{}") or {}
            except Exception:
                return {}
        # regular form POST
        return request.POST

    params = get_payload()

    def _s(key, default=""):
        v = params.get(key, default)
        if v is None:
            return default
        return str(v).strip()

    def _i(key, default=0):
        try:
            return int(str(params.get(key, default)).strip())
        except Exception:
            return default

    # ---------------------------
    # Base scope (security)
    # ---------------------------
    base_scope = (
        Cargaison.objects
        .filter(
            etat="Echantillonner",
            entrepot__ville__affectationville__username_id=user_id
        )
    )

    qs = base_scope

    # ---------------------------
    # Filters (POST only)
    # ---------------------------
    # Accept both new keys and legacy keys (so frontend variations still work)
    entrepot_name = _s("entrepot")  # legacy text
    num_dossier = _s("num_dossier")
    num_re = _s("num_re")
    immat = _s("immatriculation")
    qrcode = _s("qrcode")
    f = _s("f")

    entrepot_id_param = _s("entrepot_id")
    try:
        entrepot_id_selected = int(entrepot_id_param) if entrepot_id_param not in ("", "all", "0") else 0
    except Exception:
        entrepot_id_selected = 0

    if entrepot_name:
        qs = qs.filter(nom_entrepot__iexact=entrepot_name)
    if num_dossier:
        qs = qs.filter(numdos__iexact=num_dossier)
    if num_re:
        qs = qs.filter(entrepot_echantillon__numrappechauto__iexact=num_re)
    if immat:
        qs = qs.filter(immatriculation__iexact=immat)
    if qrcode:
        qs = qs.filter(qrcode__iexact=qrcode)
    if f:
        qs = qs.filter(Q(immatriculation=f) | Q(numdos=f) | Q(declaration=f))
    if entrepot_id_selected > 0:
        qs = qs.filter(entrepot_id=entrepot_id_selected)

    # Optional: generic search text (POST key = search)
    search_value = _s("search") or _s("search[value]")
    if search_value:
        # qs = qs.filter(
        #     Q(nom_entrepot__icontains=search_value) |
        #     Q(immatriculation__icontains=search_value) |
        #     Q(numdos__icontains=search_value) |
        #     Q(entrepot_echantillon__numrappechauto__icontains=search_value) |
        #     Q(qrcode__icontains=search_value)
        # )
        qs = qs.filter(
            Q(nom_entrepot__iexact=search_value) |
            Q(immatriculation__iexact=search_value) |
            Q(numdos__iexact=search_value) |
            Q(entrepot_echantillon__numrappechauto__iexact=search_value) |
            Q(qrcode__iexact=search_value)
        )

    # ---------------------------
    # Ordering (whitelist)
    # ---------------------------
    # Accept either:
    # - DataTables keys: order[0][column], order[0][dir]
    # - Simple keys: sort, dir
    order_col = _s("order[0][column]") or _s("sort")
    order_dir = (_s("order[0][dir]") or _s("dir", "desc")).lower()

    ordering_map = {
        "0": "dateheurecargaison",
        "1": "date_echantillon",
        "2": "nom_entrepot",
        "3": "nom_produit",
        "4": "immatriculation",
        "5": "numdos",
        "6": "entrepot_echantillon__numrappechauto",

        # also allow named sort keys (if frontend sends sort=entrepot etc.)
        "date_entree": "dateheurecargaison",
        "date_echant": "date_echantillon",
        "entrepot": "nom_entrepot",
        "produit": "nom_produit",
        "immat": "immatriculation",
        "dossier": "numdos",
        "re": "entrepot_echantillon__numrappechauto",
    }

    order_field = ordering_map.get(order_col, "date_echantillon")
    if order_dir == "desc":
        order_field = f"-{order_field}"

    qs = qs.order_by(order_field)

    # ---------------------------
    # Pagination (POST only)
    # ---------------------------
    # Accept both:
    # - DataTables: start/length
    # - Page style: page/page_size
    start = max(_i("start", 0), 0)
    length = _i("length", 10)

    if "page" in params or "page_size" in params:
        page = max(_i("page", 1), 1)
        length = _i("page_size", 10)
        start = (page - 1) * length

    if length <= 0:
        length = 10
    length = min(length, 200)  # hard cap for safety

    # ---------------------------
    # Build response (fast)
    # ---------------------------
    total = base_scope.count()
    filtered = qs.count()

    rows = list(
        qs.values(
            "idcargaison",
            "dateheurecargaison__date",
            "date_echantillon__date",
            "nom_entrepot",
            "nom_produit",
            "immatriculation",
            "numdos",
            "entrepot_echantillon__numrappechauto",
        )[start:start + length]
    )

    # Rename keys for frontend compatibility
    for r in rows:
        r["entrepot_echantillon__dateechantillonage__date"] = r.pop("date_echantillon__date", None)
        r["entrepot__nomentrepot"] = r.pop("nom_entrepot", None)
        r["produit__nomproduit"] = r.pop("nom_produit", None)

    return JsonResponse({
        "success": True,
        "recordsTotal": total,
        "recordsFiltered": filtered,
        "data": rows,
    })


@login_required(login_url='login')
def receptionechantillon(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        pk = data.get('idcargaison')

        if pk is None:
            response_data = {
                'success': False,
                'error': 'Missing primary key (pk)',
            }
            return JsonResponse(response_data, status=400)

        user = request.user
        id = user.id

        # Get Town du point de dechargement pour l'attribution automatique des numeros

        c = Cargaison.objects.get(idcargaison=pk)
        c = c.entrepot_id
        c = Entrepot.objects.get(identrepot=c)
        v = c.ville_id

        role = user.role_id
        if role == 4 or role == 1:
            # Getting current Year & Month
            now = datetime.now()

            numcertificatqualite = numCq(v)

            # Changement de l'etat de la cargaison
            d = Cargaison.objects.get(idcargaison=pk)
            d.etat = "Analyse Labo en cours"
            d.save(update_fields=['etat'])

            # Sauvegarde de l'instruction dans la Table LaboReception
            codelabo = generate_labo_code(v)

            p = LaboReception(idcargaison_id=pk, codelabo=codelabo,
                              numcertificatqualite=numcertificatqualite, datereceptionlabo=now)
            p.save()

            UserActivityLog.objects.create(
                user=user,
                action="Sample receiving acknowledgement",
                description=f"User has confirm reception of the sample of the record {d.idcargaison}",
            )

            # Prepare the JSON response
            response_data = {
                'success': True,
                'codeLabo': codelabo,
            }
            return JsonResponse(response_data)
        else:
            response_data = {
                'success': False,
                'error': 'Unauthorized',
            }
            return JsonResponse(response_data, status=401)
    else:
        response_data = {
            'success': False,
            'error': 'Invalid request method',
        }
        return JsonResponse(response_data, status=405)


# Modification echantillone receptionner
@login_required(login_url='login')
def modification(request):
    user = request.user
    id = user.id
    role = user.role_id
    if role == 1 or role == 4:
        if request.method == 'POST':
            pk = request.POST['pk']
            c = LaboReception.objects.get(idcargaison=pk)
            e = Entrepot_echantillon.objects.get(idcargaison=pk)
            codelabo = request.POST['codelabo']
            datereceptionlabo = request.POST['datereception']
            dateprelevement = request.POST['dateprelevement']
            c.codelabo = codelabo
            c.datereceptionlabo = datereceptionlabo
            c.save(update_fields=['codelabo', 'datereceptionlabo'])
            e.dateechantillonage = dateprelevement
            e.save(update_fields=['dateechantillonage'])
            response = {'valid': True}
            return JsonResponse(response, status=200)
    else:
        return redirect('logout')


# Methode de recherche par qrcode avec scanner
@login_required(login_url='login')
def rechercheqrcode(request):
    user = request.user
    id = user.id
    ville = AffectationVille.objects.get(username_id=id)
    ville = ville.ville_id
    role = user.role_id
    form = ReceptionEchantillon()
    form1 = ModificationEchantillon()
    if role == 4 or role == 1:
        q = request.GET.get('q')
        if q == "":
            return redirect('labo')
        else:
            a = '%' + q + '%'
            qs1 = Entrepot_echantillon.objects.filter(idcargaison__qrcode=q, idcargaison__etat="Echantillonner",
                                                      idcargaison__entrepot__ville=ville)
            table = LaboratoireReception(qs1, prefix='1_')

            qs = LaboReception.objects.filter(idcargaison__idcargaison__etat="Analyse Labo en cours",
                                              idcargaison__idcargaison__entrepot__ville=ville).order_by(
                '-datereceptionlabo')
            table1 = TableauEchantillonRecu(qs, prefix='2_')

            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 21}).configure(table1)

            return render(request, 'labo.html', {
                'labo': table,
                'labo1': table1,
                'form': form,
                'form1': form1,
            })
        return redirect('labo')
    else:
        return redirect('logout')


# #Recherche du code Labo
@login_required(login_url='login')
def recherchecode(request):
    user = request.user
    id = user.id
    ville = AffectationVille.objects.get(username_id=id)
    ville = ville.ville_id
    role = user.role_id
    form1 = ModificationEchantillon()
    form = ReceptionEchantillon()
    if role == 4 or role == 1:
        q = request.GET.get('q')
        if q == "":
            return redirect('labo')
        else:
            qs = Entrepot_echantillon.objects.filter(idcargaison__etat="Echantillonner",
                                                     idcargaison__entrepot__ville=ville).order_by(
                '-dateechantillonage')
            table = LaboratoireReception(qs)

            qs1 = LaboReception.objects.filter(idcargaison__idcargaison__etat="Analyse Labo en cours",
                                               idcargaison__idcargaison__entrepot__ville=ville,
                                               codelabo=q).order_by(
                '-datereceptionlabo')
            table1 = TableauEchantillonRecu(qs1, prefix='2_')

            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 21}).configure(table1)
            return render(request, 'labo.html', {
                'labo': table,
                'labo1': table1,
                'form': form,
                'form1': form1,
            })
        return redirect('labo')
    else:
        return redirect('logout')


# Class de gestion des analyses au Laboratoire
class GestionAnalyse():
    # Fontion affichage tableau encodage des resultat Labo
    @login_required(login_url='login')
    def affichageanalyse(request):
        user = request.user
        role = user.role_id
        if role == 5 or role == 1:
            form = CorrectionProduit()
            
            # Optimized scoping
            allowed_entrepot_ids = Entrepot.objects.filter(
                ville__affectationville__username_id=user.id
            ).values_list('identrepot', flat=True)
            
            count = Cargaison.objects.filter(
                etat='Refaire',
                entrepot_id__in=allowed_entrepot_ids
            ).count()

            context = {
                'count': count,
                'form': form
            }
            return render(request, 'labo_analyse.html', context)
        else:
            return redirect('logout')

    # Fonction de recherche pour encodage résultat
    @login_required(login_url='login')
    def rechercheencodage1(request):
        user = request.user
        id = user.id
        role = user.role_id
        ville = AffectationVille.objects.get(username_id=id)
        v = ville.ville_id

        if role == 5 or role == 1:
            q = request.GET.get('codelabo')
            if q == "":
                return redirect('analyse')
            else:
                qs = LaboReception.objects.filter(idcargaison__idcargaison__etat='Analyse Labo en cours',
                                                  idcargaison__idcargaison__entrepot__ville=v, codelabo=q).order_by(
                    '-datereceptionlabo')
                table1 = AffichageAnalyse(qs, prefix='1_')
                qs2 = LaboReception.objects.filter(idcargaison__idcargaison__etat='Refaire',
                                                   idcargaison__idcargaison__entrepot__ville=v).order_by(
                    '-datereceptionlabo')
                table2 = AffichageAnalyseRefaire(qs2, prefix='2_')

                RequestConfig(request, paginate={"per_page": 15}).configure(
                    table1)
                RequestConfig(request, paginate={"per_page": 15}).configure(
                    table2)

                return render(request, 'labo_analyse.html', {
                    'analyse': table1,
                    'refaire': table2,
                })
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def rechercheencodage2(request):
        user = request.user
        id = user.id
        role = user.role_id
        ville = AffectationVille.objects.get(username_id=id)
        v = ville.ville_id

        if role == 5 or role == 1:
            q = request.GET.get('codelabo')
            if q == "":
                return redirect('analyse')
            else:
                qs = LaboReception.objects.filter(idcargaison__idcargaison__etat='Analyse Labo en cours',
                                                  idcargaison__idcargaison__entrepot__ville=v).order_by(
                    '-datereceptionlabo')
                table1 = AffichageAnalyse(qs, prefix='1_')
                qs2 = LaboReception.objects.filter(idcargaison__idcargaison__etat='Refaire',
                                                   idcargaison__idcargaison__entrepot__ville=v, codelabo=q).order_by(
                    '-datereceptionlabo')
                table2 = AffichageAnalyseRefaire(qs2, prefix='2_')

                RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(
                    table1)
                RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(
                    table2)

                return render(request, 'labo_analyse.html', {
                    'analyse': table1,
                    'refaire': table2,
                })
        else:
            return redirect('logout')

    # Fontion pour encodage des resulats labo
    @login_required(login_url='login')
    def encodageresultat(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 5 or role == 1:
            form = ResultatAnalyse()
            if request.method == 'POST':
                aspect = request.POST['aspect']
                odeur = request.POST['odeur']
                couleursaybolt = request.POST['couleursaybolt']
                couleurastm = request.POST['couleurastm']
                aciditetotal = request.POST['aciditetotal']
                soufre = request.POST['soufre']
                soufremercaptan = request.POST['soufremercaptan']
                docteurtest = request.POST['docteurtest']
                massevolumique = request.POST['massevolumique']
                distillation = request.POST['distillation']
                distillation10 = request.POST['distillation10']
                distillation20 = request.POST['distillation20']
                distillation50 = request.POST['distillation50']
                distillation90 = request.POST['distillation90']
                pointinitial = request.POST['pointinitial']
                pointfinal = request.POST['pointfinal']
                pointeclair = request.POST['pointeclair']
                pointfumee = request.POST['pointfumee']
                freezingpoint = request.POST['freezingpoint']
                residu = request.POST['residu']
                perte = request.POST['perte']
                viscosite = request.POST['viscosite']
                pointinflammabilite = request.POST['pointinflammabilite']
                pointecoulement = request.POST['pointecoulement']
                teneureau = request.POST['teneureau']
                sediment = request.POST['sediment']
                corrosion = request.POST['corrosion']
                conductivite = request.POST['conductivite']
                pourcent10 = request.POST['pourcent10']
                pourcent20 = request.POST['pourcent20']
                pourcent50 = request.POST['pourcent50']
                pourcent70 = request.POST['pourcent70']
                pourcent90 = request.POST['pourcent90']
                difftemperature = request.POST['difftemperature']
                tensionvapeur = request.POST['tensionvapeur']
                plomb = request.POST['plomb']
                indiceoctane = request.POST['indiceoctane']
                vol10 = request.POST['vol10']
                vol20 = request.POST['vol20']
                vol30 = request.POST['vol30']
                vol40 = request.POST['vol40']
                vol50 = request.POST['vol50']
                vol60 = request.POST['vol60']
                vol70 = request.POST['vol70']
                vol80 = request.POST['vol80']
                vol90 = request.POST['vol90']
                indicecetane = request.POST['indicecetane']
                densite = request.POST['densite']
                recuperation362 = request.POST['recuperation362']
                cendre = request.POST['cendre']

                # Gestion des cles etrangeres
                a = LaboReception.objects.get(idcargaison=pk)
                b = Cargaison.objects.get(idcargaison=pk)
                b.etat = "Validation en cours 1"
                b.save(update_fields=['etat'])

                p = Resultat(idcargaison=a, aspect=aspect, odeur=odeur, couleursaybolt=couleursaybolt,
                             couleurastm=couleurastm, aciditetotal=aciditetotal, soufre=soufre,
                             soufremercaptan=soufremercaptan,
                             docteurtest=docteurtest, massevolumique=massevolumique, distillation=distillation,
                             distillation10=distillation10,
                             distillation20=distillation20, distillation50=distillation50,
                             distillation90=distillation90,
                             pointinitial=pointinitial, pointfinal=pointfinal, pointeclair=pointeclair,
                             pointfumee=pointfumee,
                             freezingpoint=freezingpoint, residu=residu, perte=perte, viscosite=viscosite,
                             pointinflammabilite=pointinflammabilite,
                             pointecoulement=pointecoulement, teneureau=teneureau, sediment=sediment,
                             corrosion=corrosion, conductivite=conductivite,
                             pourcent10=pourcent10, pourcent20=pourcent20, pourcent50=pourcent50, pourcent70=pourcent70,
                             pourcent90=pourcent90,
                             difftemperature=difftemperature, tensionvapeur=tensionvapeur, plomb=plomb,
                             indicecetane=indicecetane,
                             indiceoctane=indiceoctane, vol10=vol10, vol20=vol20, vol30=vol30, vol40=vol40, vol50=vol50,
                             vol60=vol60, vol70=vol70,
                             vol80=vol80, vol90=vol90, densite=densite, recuperation362=recuperation362, cendre=cendre)
                p.save()
                return redirect('analyse')
            else:
                form = ResultatAnalyse()
                return render(request, 'labo_analyse_form.html', {'form': form})
        else:
            return redirect('logout')

    # Fonction pour encodage type produit MOGAS
    @login_required(login_url='login')
    def encodagemogas(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        url = request.session['url']
        td = datetime.today()
        today = td.date()

        if role == 5 or role == 1:
            form = Mogas()
            if request.method == 'POST':
                formSave = Mogas(request.POST)
                if formSave.is_valid():
                    aspect = formSave.cleaned_data['aspect']
                    odeur = formSave.cleaned_data['odeur']
                    couleursaybolt = formSave.cleaned_data['couleursaybolt']
                    soufre = formSave.cleaned_data['soufre']
                    distillation = formSave.cleaned_data['distillation']
                    pointfinal = formSave.cleaned_data['pointfinal']
                    residu = formSave.cleaned_data['residu']
                    corrosion = formSave.cleaned_data['corrosion']
                    pourcent10 = formSave.cleaned_data['pourcent10']
                    pourcent20 = formSave.cleaned_data['pourcent20']
                    pourcent50 = formSave.cleaned_data['pourcent50']
                    pourcent70 = formSave.cleaned_data['pourcent70']
                    pourcent90 = formSave.cleaned_data['pourcent90']
                    tensionvapeur = formSave.cleaned_data['tensionvapeur']
                    difftemperature = formSave.cleaned_data['difftemperature']
                    plomb = formSave.cleaned_data['plomb']
                    indiceoctane = formSave.cleaned_data['indiceoctane']
                    massevolumique15 = formSave.cleaned_data['massevolumique15']
                    dateimpression = today

                    # Gestion des cles etrangeres
                    a = LaboReception.objects.get(idcargaison=pk)

                    b = Cargaison.objects.get(idcargaison=pk)
                    b.produit_id = 1
                    b.etat = "Validation en cours 1"
                    b.save(update_fields=['etat', 'produit_id'])

                    p = Resultat(idcargaison=a, aspect=aspect, odeur=odeur, couleursaybolt=couleursaybolt,
                                 soufre=soufre,
                                 distillation=distillation, pointfinal=pointfinal,
                                 residu=residu, corrosion=corrosion, pourcent10=pourcent10, pourcent20=pourcent20,
                                 pourcent50=pourcent50, pourcent70=pourcent70, pourcent90=pourcent90,
                                 tensionvapeur=tensionvapeur, difftemperature=difftemperature, plomb=plomb,
                                 indiceoctane=indiceoctane, massevolumique15=massevolumique15,
                                 dateimpression=dateimpression)
                    p.save()

                    # Getting Parameters ID
                    #
                    #
                    #
                    #
                    # m = Produit.objects.get(idproduit=b.produit_id)
                    #
                    # n = ResultatAnalyse(idcargaison=b,)

                    return redirect(url)
                return redirect(url)
            else:
                form = Mogas()
                nom = 'MOGAS'
                return render(request, 'labo_analyse_form.html', {
                    'form': form,
                    'nom': nom,
                })
        else:
            return redirect('logout')

    # Fontion pour Re-encodage type produit MOGAS
    @login_required(login_url='login')
    def encodagemogasr(request, pk):
        user = request.user
        id = user.id
        role = user.role_id

        url = request.session['url']
        td = datetime.today()
        today = td.date()

        if role == 5 or role == 1:

            form = Mogas()
            now = datetime.today()
            today = now.date()
            if request.method == 'POST':
                formSave = Mogas(request.POST)
                aspect = request.POST['aspect']
                odeur = request.POST['odeur']
                couleursaybolt = request.POST['couleursaybolt']
                soufre = request.POST['soufre']
                distillation = request.POST['distillation']
                pointfinal = request.POST['pointfinal']
                residu = request.POST['residu']
                corrosion = request.POST['corrosion']
                pourcent10 = request.POST['pourcent10']
                pourcent20 = request.POST['pourcent20']
                pourcent50 = request.POST['pourcent50']
                pourcent70 = request.POST['pourcent70']
                pourcent90 = request.POST['pourcent90']
                tensionvapeur = request.POST['tensionvapeur']
                difftemperature = request.POST['difftemperature']
                plomb = request.POST['plomb']
                indiceoctane = request.POST['indiceoctane']
                massevolumique15 = request.POST['massevolumique15']
                dateimpression = today

                # Gestion des cles etrangeres
                a = LaboReception.objects.get(idcargaison=pk)

                b = Cargaison.objects.get(idcargaison=pk)
                b.produit_id = 1
                b.etat = "Validation en cours 1"
                b.save(update_fields=['etat', 'produit_id'])

                p = Resultat.objects.get(idcargaison_id=pk)
                p.aspect = aspect
                p.odeur = odeur
                p.couleursaybolt = couleursaybolt
                p.soufre = soufre
                p.residu = residu
                p.corrosion = corrosion
                p.pourcent10 = pourcent10
                p.distillation = distillation
                p.pointfinal = pointfinal
                p.pourcent20 = pourcent20
                p.pourcent50 = pourcent50
                p.pourcent70 = pourcent70
                p.pourcent90 = pourcent90
                p.tensionvapeur = tensionvapeur
                p.difftemperature = difftemperature
                p.plomb = plomb
                p.indiceoctane = indiceoctane
                p.massevolumique15 = massevolumique15
                p.dateimpression = dateimpression

                p.save(
                    update_fields=['aspect', 'odeur', 'couleursaybolt', 'soufre', 'residu', 'corrosion', 'pourcent10',
                                   'distillation', 'pointfinal',
                                   'pourcent20', 'pourcent50', 'pourcent70', 'pourcent90', 'tensionvapeur',
                                   'difftemperature',
                                   'plomb', 'indiceoctane', 'massevolumique15', 'dateimpression'])

                return redirect(url)
            else:
                form = Mogas()
                nom = 'MOGAS'
                return render(request, 'labo_analyse_form.html', {
                    'form': form,
                    'nom': nom,
                })
        else:
            return redirect('logout')

    # Fontion pour encodage type produit GASOIL
    @login_required(login_url='login')
    def encodagegasoil(request, pk):
        user = request.user
        id = user.id
        role = user.role_id

        url = request.session['url']
        td = datetime.today()
        today = td.date()

        if role == 5 or role == 1:
            if request.method == 'POST':
                formSave = Gasoil(request.POST)
                if formSave.is_valid():
                    couleurastm = formSave.cleaned_data['couleurastm']
                    aciditetotal = formSave.cleaned_data['aciditetotal']
                    soufre = formSave.cleaned_data['soufre']
                    massevolumique = formSave.cleaned_data['massevolumique']
                    massevolumique15 = formSave.cleaned_data['massevolumique15']
                    pointinitial = formSave.cleaned_data['pointinitial']
                    distillation10 = formSave.cleaned_data['distillation10']
                    distillation20 = formSave.cleaned_data['distillation20']
                    distillation50 = formSave.cleaned_data['distillation50']
                    distillation90 = formSave.cleaned_data['distillation90']
                    pointfinal = formSave.cleaned_data['pointfinal']
                    pointeclair = formSave.cleaned_data['pointeclair']
                    viscosite = formSave.cleaned_data['viscosite']
                    pointecoulement = formSave.cleaned_data['pointecoulement']
                    teneureau = formSave.cleaned_data['teneureau']
                    sediment = formSave.cleaned_data['sediment']
                    corrosion = formSave.cleaned_data['corrosion']
                    indicecetane = formSave.cleaned_data['indicecetane']

                    recuperation362 = formSave.cleaned_data['recuperation362']
                    cendre = formSave.cleaned_data['cendre']
                    dateimpression = today

                    # Gestion des cles etrangeres
                    a = LaboReception.objects.get(idcargaison=pk)
                    b = Cargaison.objects.get(idcargaison=pk)
                    b.produit_id = 2
                    b.etat = "Validation en cours 1"
                    b.save(update_fields=['etat', 'produit_id'])

                    p = Resultat(idcargaison=a, couleurastm=couleurastm, aciditetotal=aciditetotal, soufre=soufre,
                                 pointinitial=pointinitial,
                                 massevolumique=massevolumique, massevolumique15=massevolumique15,
                                 distillation10=distillation10, distillation20=distillation20,
                                 distillation50=distillation50, distillation90=distillation90,
                                 pointfinal=pointfinal, pointeclair=pointeclair, viscosite=viscosite,
                                 pointecoulement=pointecoulement, teneureau=teneureau,
                                 sediment=sediment, corrosion=corrosion, indicecetane=indicecetane,
                                 recuperation362=recuperation362, cendre=cendre, dateimpression=dateimpression)
                    p.save()
                    return redirect(url)
                return redirect(url)
            else:
                form = Gasoil()
                nom = 'GASOIL'
                return render(request, 'labo_analyse_form.html', {
                    'form': form,
                    'nom': nom,
                })
        else:
            return redirect('logout')

    # Fontion pour Re-encodage type produit GASOIL
    @login_required(login_url='login')
    def encodagegasoilr(request, pk):
        user = request.user
        id = user.id
        role = user.role_id

        url = request.session['url']
        td = datetime.today()
        today = td.date()

        if role == 5 or role == 1:
            form = Gasoil()
            if request.method == 'POST':
                couleurastm = request.POST['couleurastm']
                aciditetotal = request.POST['aciditetotal']
                soufre = request.POST['soufre']
                massevolumique = request.POST['massevolumique']
                massevolumique15 = request.POST['massevolumique15']
                pointinitial = request.POST['pointinitial']
                distillation10 = request.POST['distillation10']
                distillation20 = request.POST['distillation20']
                distillation50 = request.POST['distillation50']
                distillation90 = request.POST['distillation90']
                pointfinal = request.POST['pointfinal']
                pointeclair = request.POST['pointeclair']
                viscosite = request.POST['viscosite']
                pointecoulement = request.POST['pointecoulement']
                teneureau = request.POST['teneureau']
                sediment = request.POST['sediment']
                corrosion = request.POST['corrosion']
                indicecetane = request.POST['indicecetane']

                recuperation362 = request.POST['recuperation362']
                cendre = request.POST['cendre']
                dateimpression = today

                # Gestion des cles etrangeres
                a = LaboReception.objects.get(idcargaison=pk)
                b = Cargaison.objects.get(idcargaison=pk)
                b.produit_id = 2
                b.etat = "Validation en cours 1"
                b.save(update_fields=['etat', 'produit_id'])

                p = Resultat.objects.get(idcargaison=pk)
                p.couleurastm = couleurastm
                p.aciditetotal = aciditetotal
                p.soufre = soufre
                p.massevolumique = massevolumique
                p.massevolumique15 = massevolumique15
                p.pointinitial = pointinitial
                p.distillation10 = distillation10
                p.distillation20 = distillation20
                p.distillation50 = distillation50
                p.distillation90 = distillation90
                p.pointfinal = pointfinal
                p.pointeclair = pointeclair
                p.viscosite = viscosite
                p.pointecoulement = pointecoulement
                p.teneureau = teneureau
                p.sediment = sediment
                p.corrosion = corrosion
                p.indicecetane = indicecetane
                p.recuperation362 = recuperation362
                p.cendre = cendre
                p.dateimpression = dateimpression

                p.save(update_fields=['couleurastm', 'aciditetotal', 'soufre', 'massevolumique', 'massevolumique15',
                                      'distillation10', 'distillation20', 'distillation50', 'pointinitial',
                                      'distillation90', 'pointfinal', 'pointeclair', 'viscosite', 'pointecoulement',
                                      'teneureau', 'sediment', 'corrosion',
                                      'indicecetane', 'recuperation362', 'cendre', 'dateimpression'])

                return redirect(url)
            else:
                form = Gasoil()
                nom = 'GASOIL'
                return render(request, 'labo_analyse_form.html', {
                    'form': form,
                    'nom': nom,
                })
        else:
            return redirect('logout')

    # Fontion pour encodage type produit JETA1
    @login_required(login_url='login')
    def encodagejeta1(request, pk):
        user = request.user
        id = user.id
        role = user.role_id

        url = request.session['url']
        td = datetime.today()
        today = td.date()

        if role == 5 or role == 1:
            if request.method == 'POST':
                formSave = JetA1(request.POST)
                if formSave.is_valid():
                    aspect = formSave.cleaned_data['aspect']
                    couleursaybolt = formSave.cleaned_data['couleursaybolt']
                    aciditetotal = formSave.cleaned_data['aciditetotal']
                    soufre = formSave.cleaned_data['soufre']
                    soufremercaptan = formSave.cleaned_data['soufremercaptan']
                    docteurtest = formSave.cleaned_data['docteurtest']
                    # distillation = formSave.cleaned_data['distillation']
                    pointinitial = formSave.cleaned_data['pointinitial']
                    pointfinal = formSave.cleaned_data['pointfinal']
                    pointfumee = formSave.cleaned_data['pointfumee']
                    pointeclair = formSave.cleaned_data['pointeclair']
                    freezingpoint = formSave.cleaned_data['freezingpoint']
                    residu = formSave.cleaned_data['residu']
                    perte = formSave.cleaned_data['perte']
                    massevolumique15 = formSave.cleaned_data['massevolumique15']
                    viscosite = formSave.cleaned_data['viscosite']
                    pointinflammabilite = formSave.cleaned_data['pointinflammabilite']
                    teneureau = formSave.cleaned_data['teneureau']
                    corrosion = formSave.cleaned_data['corrosion']
                    conductivite = formSave.cleaned_data['conductivite']
                    vol10 = formSave.cleaned_data['vol10']
                    vol90 = formSave.cleaned_data['vol90']
                    dateimpression = today

                    # Gestion des cles etrangeres
                    a = LaboReception.objects.get(idcargaison=pk)
                    b = Cargaison.objects.get(idcargaison=pk)
                    b.produit_id = 3
                    b.etat = "Validation en cours 1"
                    b.save(update_fields=['etat', 'produit_id'])

                    p = Resultat(idcargaison=a, aspect=aspect, couleursaybolt=couleursaybolt, aciditetotal=aciditetotal,
                                 soufre=soufre, soufremercaptan=soufremercaptan, docteurtest=docteurtest,
                                 pointfinal=pointfinal, pointinitial=pointinitial, pointeclair=pointeclair,
                                 pointfumee=pointfumee, freezingpoint=freezingpoint, residu=residu, perte=perte,
                                 massevolumique15=massevolumique15, viscosite=viscosite,
                                 pointinflammabilite=pointinflammabilite, teneureau=teneureau, corrosion=corrosion,
                                 conductivite=conductivite,
                                 vol10=vol10, vol90=vol90, dateimpression=dateimpression
                                 )
                    p.save()
                    return redirect(url)
                return redirect(url)
            else:
                form = JetA1()
                nom = 'JET A1'
                return render(request, 'labo_analyse_form.html', {
                    'form': form,
                    'nom': nom,
                })
        else:
            return redirect('logout')

    # Fontion pour Re-encodage type produit JETA1
    @login_required(login_url='login')
    def encodagejeta1r(request, pk):
        user = request.user
        id = user.id
        role = user.role_id

        url = request.session['url']
        td = datetime.today()
        today = td.date()

        if role == 5 or role == 1:
            if request.method == 'POST':
                aspect = request.POST['aspect']
                couleursaybolt = request.POST['couleursaybolt']
                aciditetotal = request.POST['aciditetotal']
                soufre = request.POST['soufre']
                soufremercaptan = request.POST['soufremercaptan']
                docteurtest = request.POST['docteurtest']
                # distillation = request.POST['distillation']
                pointinitial = request.POST['pointinitial']
                pointfinal = request.POST['pointfinal']
                pointfumee = request.POST['pointfumee']
                pointeclair = request.POST['pointeclair']
                freezingpoint = request.POST['freezingpoint']
                residu = request.POST['residu']
                perte = request.POST['perte']
                massevolumique15 = request.POST['massevolumique15']
                viscosite = request.POST['viscosite']
                pointinflammabilite = request.POST['pointinflammabilite']
                teneureau = request.POST['teneureau']
                corrosion = request.POST['corrosion']
                conductivite = request.POST['conductivite']
                vol10 = request.POST['vol10']
                vol90 = request.POST['vol90']
                dateimpression = today

                # Gestion des cles etrangeres
                a = LaboReception.objects.get(idcargaison=pk)
                b = Cargaison.objects.get(idcargaison=pk)
                b.produit_id = 3
                b.etat = "Validation en cours 1"
                b.save(update_fields=['etat', 'produit_id'])

                p = Resultat.objects.get(idcargaison=pk)
                p.aspect = aspect
                p.couleursaybolt = couleursaybolt
                p.aciditetotal = aciditetotal
                p.soufre = soufre
                p.soufremercaptan = soufremercaptan
                p.docteurtest = docteurtest
                p.pointfinal = pointfinal
                p.pointinitial = pointinitial
                p.pointeclair = pointeclair
                p.pointfumee = pointfumee
                p.freezingpoint = freezingpoint
                p.residu = residu
                p.perte = perte
                p.massevolumique15 = massevolumique15
                p.viscosite = viscosite
                p.pointinflammabilite = pointinflammabilite
                p.teneureau = teneureau
                p.corrosion = corrosion
                p.conductivite = conductivite
                p.vol10 = vol10
                p.vol90 = vol90
                p.dateimpression = dateimpression

                p.save(update_fields=['aspect', 'couleursaybolt', 'aciditetotal', 'soufre', 'soufremercaptan',
                                      'docteurtest', 'pointfinal', 'pointinitial',
                                      'pointeclair', 'pointfumee', 'freezingpoint', 'residu', 'perte',
                                      'massevolumique15', 'viscosite', 'pointinflammabilite',
                                      'teneureau', 'corrosion', 'conductivite', 'vol10', 'vol90', 'dateimpression'])

                return redirect(url)
            else:
                form = JetA1()
                nom = 'JET A1'
                return render(request, 'labo_analyse_form.html', {
                    'form': form,
                    'nom': nom,
                })
        else:
            return redirect('logout')

    # Fonction pour encodage type produit Petrole
    @login_required(login_url='login')
    def encodagepetrole(request, pk):
        user = request.user
        id = user.id
        role = user.role_id

        url = request.session['url']
        td = datetime.today()
        today = td.date()

        if role == 5 or role == 1:
            if request.method == 'POST':
                formSave = PetroleLampant(request.POST)
                if formSave.is_valid():
                    aspect = request.POST['aspect']
                    couleursaybolt = request.POST['couleursaybolt']
                    aciditetotal = request.POST['aciditetotal']
                    soufre = request.POST['soufre']
                    soufremercaptan = request.POST['soufremercaptan']
                    docteurtest = request.POST['docteurtest']
                    # distillation = request.POST['distillation']
                    pointinitial = request.POST['pointinitial']
                    pointfinal = request.POST['pointfinal']
                    pointfumee = request.POST['pointfumee']
                    pointeclair = request.POST['pointeclair']
                    freezingpoint = request.POST['freezingpoint']
                    residu = request.POST['residu']
                    perte = request.POST['perte']
                    massevolumique15 = request.POST['massevolumique15']
                    viscosite = request.POST['viscosite']
                    pointinflammabilite = request.POST['pointinflammabilite']
                    teneureau = request.POST['teneureau']
                    corrosion = request.POST['corrosion']
                    conductivite = request.POST['conductivite']
                    vol10 = request.POST['vol10']
                    vol90 = request.POST['vol90']
                    dateimpression = today

                    # Gestion des cles etrangeres
                    a = LaboReception.objects.get(idcargaison=pk)
                    b = Cargaison.objects.get(idcargaison=pk)
                    b.etat = "Validation en cours 1"
                    b.produit_id = 4
                    b.save(update_fields=['etat', 'produit_id'])

                    p = Resultat(idcargaison=a, aspect=aspect, couleursaybolt=couleursaybolt, aciditetotal=aciditetotal,
                                 soufre=soufre, soufremercaptan=soufremercaptan, docteurtest=docteurtest,
                                 pointfinal=pointfinal, pointinitial=pointinitial, pointeclair=pointeclair,
                                 pointfumee=pointfumee, freezingpoint=freezingpoint, residu=residu, perte=perte,
                                 massevolumique15=massevolumique15, viscosite=viscosite,
                                 pointinflammabilite=pointinflammabilite, teneureau=teneureau, corrosion=corrosion,
                                 conductivite=conductivite,
                                 vol10=vol10, vol90=vol90, dateimpression=dateimpression
                                 )
                    p.save()
                    return redirect(url)
                return redirect(url)
            else:
                form = PetroleLampant()
                nom = 'PETROLE'
                return render(request, 'labo_analyse_form.html', {
                    'form': form,
                    'nom': nom,
                })
        else:
            return redirect('logout')

    # Fonction pour Re-encodage type produit Petrole
    @login_required(login_url='login')
    def encodagepetroler(request, pk):
        user = request.user
        id = user.id
        role = user.role_id

        url = request.session['url']
        td = datetime.today()
        today = td.date()

        if role == 5 or role == 1:
            if request.method == 'POST':
                aspect = request.POST['aspect']
                couleursaybolt = request.POST['couleursaybolt']
                aciditetotal = request.POST['aciditetotal']
                soufre = request.POST['soufre']
                soufremercaptan = request.POST['soufremercaptan']
                docteurtest = request.POST['docteurtest']
                # distillation = request.POST['distillation']
                pointinitial = request.POST['pointinitial']
                pointfinal = request.POST['pointfinal']
                pointfumee = request.POST['pointfumee']
                pointeclair = request.POST['pointeclair']
                freezingpoint = request.POST['freezingpoint']
                residu = request.POST['residu']
                perte = request.POST['perte']
                massevolumique15 = request.POST['massevolumique15']
                viscosite = request.POST['viscosite']
                pointinflammabilite = request.POST['pointinflammabilite']
                teneureau = request.POST['teneureau']
                corrosion = request.POST['corrosion']
                conductivite = request.POST['conductivite']
                vol10 = request.POST['vol10']
                vol90 = request.POST['vol90']
                dateimpression = today

                # Gestion des cles etrangeres
                a = LaboReception.objects.get(idcargaison=pk)
                b = Cargaison.objects.get(idcargaison=pk)
                b.produit_id = 4
                b.etat = "Validation en cours 1"
                b.save(update_fields=['etat', 'produit_id'])

                p = Resultat.objects.get(idcargaison=pk)
                p.aspect = aspect
                p.couleursaybolt = couleursaybolt
                p.aciditetotal = aciditetotal
                p.soufre = soufre
                p.soufremercaptan = soufremercaptan
                p.docteurtest = docteurtest
                p.pointfinal = pointfinal
                p.pointinitial = pointinitial
                p.pointeclair = pointeclair
                p.pointfumee = pointfumee
                p.freezingpoint = freezingpoint
                p.residu = residu
                p.perte = perte
                p.massevolumique15 = massevolumique15
                p.viscosite = viscosite
                p.pointinflammabilite = pointinflammabilite
                p.teneureau = teneureau
                p.corrosion = corrosion
                p.conductivite = conductivite
                p.vol10 = vol10
                p.vol90 = vol90
                p.dateimpression = dateimpression

                p.save(update_fields=['aspect', 'couleursaybolt', 'aciditetotal', 'soufre', 'soufremercaptan',
                                      'docteurtest', 'pointfinal', 'pointinitial',
                                      'pointeclair', 'pointfumee', 'freezingpoint', 'residu', 'perte',
                                      'massevolumique15', 'viscosite', 'pointinflammabilite',
                                      'teneureau', 'corrosion', 'conductivite', 'vol10', 'vol90', 'dateimpression'])

                return redirect(url)
            else:
                form = PetroleLampant()
                nom = 'PETROLE'
                return render(request, 'labo_analyse_form.html', {
                    'form': form,
                    'nom': nom,
                })
        else:
            return redirect('logout')


# Class gestion des validations au niveau du labo
class GestionValidation():
    # Fonction affichage des resultats sur Validation 1
    @login_required(login_url='login')
    def affichagetableauvalidation1(request):
        user = request.user
        role = user.role_id
        if role in (5, 1, 6):
            request.session['url'] = request.get_full_path()
            form = RapportLabo()
            return render(request, 'labo_validation1.html', {'form': form})
        else:
            return redirect('logout')

    # Fonction encodage du code Labo
    @login_required(login_url='login')
    def codecertificat(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        url = request.session['url']
        if role == 5 or role == 1 or role == 6:
            if request.method == 'POST':
                numcertificatqualite = request.POST['numcertificatqualite']
                c = LaboReception.objects.get(idcargaison=pk)
                c.numcertificatqualite = numcertificatqualite
                c.save()

                return redirect(url)
            else:
                return redirect(url)
        else:
            return redirect('logout')

    # Fontion affichage des rapports en HTML avant conversion en PDF
    @login_required(login_url='login')
    def affichagerapportpdf(request, pk):
        user = request.user
        id = user.id

        # Get Town du point de dechargement pour l'attribution automatique des numeros
        c = Cargaison.objects.get(idcargaison=pk)
        c = c.entrepot_id
        c = Entrepot.objects.get(identrepot=c)
        ville = c.ville_id

        print(ville)
        # ville = AffectationVille.objects.get(username_id=id)
        # ville = ville.ville_id
        province = Ville.objects.get(idville=ville)
        province = province.province
        province = province.upper()
        role = user.role_id

        if role == 5 or role == 1 or role == 6 or role == "v2":
            # Récuperation des dates
            cargaison = Cargaison.objects.get(idcargaison=pk)
            if cargaison.date_reception_labo:
                mois = cargaison.date_reception_labo.month
                annee = cargaison.date_reception_labo.year
            else:
                # Fallback to current date or handle missing date
                mois = datetime.today().month
                annee = datetime.today().year

            # Recuperation du produit de la cargaison
            p = Produit.objects.get(cargaison=pk)
            produit = p.nomproduit

            # Fecthing object with pk corresponding into database
            a = Cargaison.objects.get(idcargaison=pk)
            b = Entrepot_echantillon.objects.get(idcargaison=pk)
            c = LaboReception.objects.get(idcargaison=pk)
            d = Resultat.objects.get(idcargaison_id=pk)

            # Fetching into DBS general results
            numcertificatqualite = c.numcertificatqualite
            codelabo = c.codelabo
            dateanalyse = d.dateanalyse
            importateur = a.importateur
            # declarant = a.declarant
            dateechantillonage = b.dateechantillonage
            entrepot = a.entrepot
            provenance = a.provenance.name
            qte = b.qte
            datereceptionlabo = c.datereceptionlabo
            codelabo = c.codelabo
            numdossier = a.numdos
            immatriculation = a.immatriculation
            numrappech = b.numrappech

            # Test pour afficher les differents rapports
            if produit == 'GASOIL':
                template = 'report/gasoilreport.html'

                # Resultat Gasoil Fetching data into Database
                couleurastm = d.couleurastm
                aciditetotal = d.aciditetotal
                soufre = d.soufre
                massevolumique = d.massevolumique
                massevolumique15 = d.massevolumique15
                distillation = d.distillation
                distillation10 = d.distillation10
                distillation20 = d.distillation20
                distillation50 = d.distillation50
                distillation90 = d.distillation90
                pointinitial = d.pointinitial
                pointfinal = d.pointfinal
                pointeclair = d.pointeclair
                viscosite = d.viscosite
                pointecoulement = d.pointecoulement
                teneureau = d.teneureau
                sediment = d.sediment
                corrosion = d.corrosion
                indicecetane = d.indicecetane
                densite = d.densite
                recuperation362 = d.recuperation362
                cendre = d.cendre

                data = {
                    'numcertificatqualite': numcertificatqualite,
                    'dateanalyse': dateanalyse,
                    'importateur': importateur,
                    # 'declarant': declarant,
                    'entrepot': entrepot,
                    'dateechantillonage': dateechantillonage,
                    'provenance': provenance,
                    'qte': qte,
                    'datereceptionlabo': datereceptionlabo,
                    'codelabo': codelabo,
                    'numdossier': numdossier,
                    'immatriculation': immatriculation,
                    'couleurastm': couleurastm,
                    'aciditetotal': aciditetotal,
                    'soufre': soufre,
                    'massevolumique': massevolumique,
                    'distillation': distillation,
                    'distillation10': distillation10,
                    'distillation20': distillation20,
                    'distillation50': distillation50,
                    'distillation90': distillation90,
                    'pointfinal': pointfinal,
                    'pointeclair': pointeclair,
                    'pointinitial': pointinitial,
                    'viscosite': viscosite,
                    'pointecoulement': pointecoulement,
                    'teneureau': teneureau,
                    'sediment': sediment,
                    'corrosion': corrosion,
                    'indicecetane': indicecetane,
                    'densite': densite,
                    'recuperation362': recuperation362,
                    'cendre': cendre,
                    'massevolumique15': massevolumique15,
                    'numrappech': numrappech,
                    'produit': produit,
                    'mois': mois,
                    'annee': annee,
                    'province': province,
                }

                # Rendered PDF report
                pdf = render_to_pdf(template, data)
                return HttpResponse(pdf, content_type='application/pdf')

            else:
                if produit == 'MOGAS':
                    template = 'report/mogasreport.html'
                    # Resultat Gasoil Fetching data into Database
                    aspect = d.aspect
                    odeur = d.odeur
                    couleursaybolt = d.couleursaybolt
                    soufre = d.soufre
                    distillation = d.distillation
                    pointfinal = d.pointfinal
                    residu = d.residu
                    corrosion = d.corrosion
                    pourcent10 = d.pourcent10
                    pourcent20 = d.pourcent20
                    pourcent50 = d.pourcent50
                    pourcent70 = d.pourcent70
                    pourcent90 = d.pourcent90
                    tensionvapeur = d.tensionvapeur
                    difftemperature = d.difftemperature
                    plomb = d.plomb
                    indiceoctane = d.indiceoctane
                    massevolumique15 = d.massevolumique15

                    data = {
                        'numcertificatqualite': numcertificatqualite,
                        'dateanalyse': dateanalyse,
                        'importateur': importateur,
                        # 'declarant': declarant,
                        'entrepot': entrepot,
                        'dateechantillonage': dateechantillonage,
                        'provenance': provenance,
                        'qte': qte,
                        'datereceptionlabo': datereceptionlabo,
                        'codelabo': codelabo,
                        'numdossier': numdossier,
                        'immatriculation': immatriculation,
                        'numrappech': numrappech,
                        'aspect': aspect,
                        'odeur': odeur,
                        'couleursaybolt': couleursaybolt,
                        'soufre': soufre,
                        'distillation': distillation,
                        'pointfinal': pointfinal,
                        'residu': residu,
                        'corrosion': corrosion,
                        'pourcent10': pourcent10,
                        'pourcent20': pourcent20,
                        'pourcent50': pourcent50,
                        'pourcent70': pourcent70,
                        'pourcent90': pourcent90,
                        'tensionvapeur': tensionvapeur,
                        'difftemperature': difftemperature,
                        'plomb': plomb,
                        'indiceoctane': indiceoctane,
                        'massevolumique15': massevolumique15,
                        'produit': produit,
                        'mois': mois,
                        'annee': annee,
                        'province': province,
                    }

                    # Rendered PDF report
                    pdf = render_to_pdf(template, data)
                    return HttpResponse(pdf, content_type='application/pdf')
                else:
                    if produit == 'JET A1':
                        template = 'report/jeta1report.html'

                        # Resultat Gasoil Fetching data into Database
                        aspect = d.aspect
                        couleursaybolt = d.couleursaybolt
                        aciditetotal = d.aciditetotal
                        soufre = d.soufre
                        soufremercaptan = d.soufremercaptan
                        docteurtest = d.docteurtest
                        distillation = d.distillation
                        pointinitial = d.pointinitial
                        pointfinal = d.pointfinal
                        pointfumee = d.pointfumee
                        pointeclair = d.pointeclair
                        freezingpoint = d.freezingpoint
                        residu = d.residu
                        perte = d.perte
                        massevolumique15 = d.massevolumique15
                        viscosite = d.viscosite
                        pointinflammabilite = d.pointinflammabilite
                        teneureau = d.teneureau
                        corrosion = d.corrosion
                        conductivite = d.conductivite
                        vol10 = d.vol10
                        vol20 = d.vol20
                        vol30 = d.vol30
                        vol40 = d.vol40
                        vol50 = d.vol50
                        vol60 = d.vol60
                        vol70 = d.vol70
                        vol80 = d.vol80
                        vol90 = d.vol90

                        data = {
                            'numcertificatqualite': numcertificatqualite,
                            'dateanalyse': dateanalyse,
                            'importateur': importateur,
                            # 'declarant': declarant,
                            'entrepot': entrepot,
                            'dateechantillonage': dateechantillonage,
                            'provenance': provenance,
                            'qte': qte,
                            'datereceptionlabo': datereceptionlabo,
                            'codelabo': codelabo,
                            'numdossier': numdossier,
                            'immatriculation': immatriculation,
                            'numrappech': numrappech,
                            'aspect': aspect,
                            'couleursaybolt': couleursaybolt,
                            'aciditetotal': aciditetotal,
                            'soufre': soufre,
                            'soufremercaptan': soufremercaptan,
                            'docteurtest': docteurtest,
                            'distillation': distillation,
                            'pointinitial': pointinitial,
                            'pointfinal': pointfinal,
                            'pointfumee': pointfumee,
                            'freezingpoint': freezingpoint,
                            'residu': residu,
                            'perte': perte,
                            'pointeclair': pointeclair,
                            'massevolumique15': massevolumique15,
                            'viscosite': viscosite,
                            'pointinflammabilite': pointinflammabilite,
                            'teneureau': teneureau,
                            'corrosion': corrosion,
                            'conductivite': conductivite,
                            'vol10': vol10,
                            'vol20': vol20,
                            'vol30': vol30,
                            'vol40': vol40,
                            'vol50': vol50,
                            'vol60': vol60,
                            'vol70': vol70,
                            'vol80': vol80,
                            'vol90': vol90,
                            'produit': produit,
                            'mois': mois,
                            'annee': annee,
                            'province': province,
                        }
                        # Rendered PDF report
                        pdf = render_to_pdf(template, data)
                        return HttpResponse(pdf, content_type='application/pdf')

                    else:
                        if produit == 'PETROLE LAMPANT':
                            template = 'report/petrolereport.html'

                            # Resultat Gasoil Fetching data into Database
                            aspect = d.aspect
                            couleursaybolt = d.couleursaybolt
                            aciditetotal = d.aciditetotal
                            soufre = d.soufre
                            soufremercaptan = d.soufremercaptan
                            docteurtest = d.docteurtest
                            distillation = d.distillation
                            pointinitial = d.pointinitial
                            pointfinal = d.pointfinal
                            pointfumee = d.pointfumee
                            pointeclair = d.pointeclair
                            freezingpoint = d.freezingpoint
                            residu = d.residu
                            perte = d.perte
                            massevolumique15 = d.massevolumique15
                            viscosite = d.viscosite
                            pointinflammabilite = d.pointinflammabilite
                            teneureau = d.teneureau
                            corrosion = d.corrosion
                            conductivite = d.conductivite
                            vol10 = d.vol10
                            vol20 = d.vol20
                            vol30 = d.vol30
                            vol40 = d.vol40
                            vol50 = d.vol50
                            vol60 = d.vol60
                            vol70 = d.vol70
                            vol80 = d.vol80
                            vol90 = d.vol90

                            data = {
                                'numcertificatqualite': numcertificatqualite,
                                'dateanalyse': dateanalyse,
                                'importateur': importateur,
                                # 'declarant': declarant,
                                'entrepot': entrepot,
                                'dateechantillonage': dateechantillonage,
                                'provenance': provenance,
                                'qte': qte,
                                'datereceptionlabo': datereceptionlabo,
                                'codelabo': codelabo,
                                'numdossier': numdossier,
                                'immatriculation': immatriculation,
                                'numrappech': numrappech,
                                'aspect': aspect,
                                'couleursaybolt': couleursaybolt,
                                'aciditetotal': aciditetotal,
                                'soufre': soufre,
                                'soufremercaptan': soufremercaptan,
                                'docteurtest': docteurtest,
                                'distillation': distillation,
                                'pointinitial': pointinitial,
                                'pointfinal': pointfinal,
                                'pointfumee': pointfumee,
                                'freezingpoint': freezingpoint,
                                'residu': residu,
                                'perte': perte,
                                'pointeclair': pointeclair,
                                'massevolumique15': massevolumique15,
                                'viscosite': viscosite,
                                'pointinflammabilite': pointinflammabilite,
                                'teneureau': teneureau,
                                'corrosion': corrosion,
                                'conductivite': conductivite,
                                'vol10': vol10,
                                'vol20': vol20,
                                'vol30': vol30,
                                'vol40': vol40,
                                'vol50': vol50,
                                'vol60': vol60,
                                'vol70': vol70,
                                'vol80': vol80,
                                'vol90': vol90,
                                'produit': produit,
                                'mois': mois,
                                'annee': annee,
                                'province': province,
                            }

                            # Rendered PDF report
                            pdf = render_to_pdf(template, data)
                            return HttpResponse(pdf, content_type='application/pdf')
                    return redirect('logout')
        else:
            return redirect('logout')

    # Validation du responsable service Labo PP
    @login_required(login_url='login')
    def validationv1(request, pk):
        user = request.user
        role = user.role_id

        if role in (1, 6):
            try:
                with transaction.atomic():
                    c = Cargaison.objects.select_for_update().get(idcargaison=pk)
                    c.etat = "En attente validation 2"
                    c.save(update_fields=['etat'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Validation 1: Transmission",
                        description=f"Cargaison {pk}: Dossier transmis pour validation Niveau 2.",
                    )
                return redirect('validation1')
            except Cargaison.DoesNotExist:
                return redirect('validation1')
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def refaire(request):
        user = request.user
        role = user.role_id
        url = request.session.get('url', 'validation1')
        pk = request.session.get('pk')

        if not pk:
            return redirect(url)

        if role in (1, 6, 10):
            try:
                with transaction.atomic():
                    c = Cargaison.objects.select_for_update().get(idcargaison=pk)
                    c.etat = "Refaire"
                    c.save(update_fields=['etat'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Validation: Request Re-analysis",
                        description=f"Cargaison {pk}: User requested re-analysis via legacy view.",
                    )
                return redirect(url)
            except Cargaison.DoesNotExist:
                return redirect(url)
        else:
            return redirect('logout')

    # Validation du responsable Division LABO OCC
    @login_required(login_url='login')
    def conforme(request):
        user = request.user
        role = user.role_id
        url = request.session.get('url', 'validation1')
        pk = request.session.get('pk')

        if not pk:
            return redirect(url)

        # Accommodate both string 'v2' and integer role IDs (1, 6)
        if role == "v2" or role in (1, 6):
            try:
                with transaction.atomic():
                    c = Cargaison.objects.select_for_update().get(idcargaison=pk)
                    c.etat = "Validation en cours 2"
                    c.conformite = "Conforme aux exigences"
                    c.impression = "0"
                    c.save(update_fields=['etat', 'conformite', 'impression'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Validation 1: CONFORME",
                        description=f"Cargaison {pk}: First validation set to CONFORME via legacy view.",
                    )
                return redirect(url)
            except Cargaison.DoesNotExist:
                return redirect(url)
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def nonconforme(request):
        user = request.user
        role = user.role_id
        url = request.session.get('url', 'validation1')
        pk = request.session.get('pk')

        if not pk:
            return redirect(url)

        if role == "v2" or role in (1, 6):
            try:
                with transaction.atomic():
                    c = Cargaison.objects.select_for_update().get(idcargaison=pk)
                    c.etat = "Validation en cours 2"
                    c.conformite = "Non conforme aux exigences"
                    c.impression = "0"
                    c.save(update_fields=['etat', 'conformite', 'impression'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Validation 1: NON CONFORME",
                        description=f"Cargaison {pk}: First validation set to NON CONFORME via legacy view.",
                    )
                return redirect(url)
            except Cargaison.DoesNotExist:
                return redirect(url)
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def conforme2(request):
        user = request.user
        role = user.role_id
        pk = request.session.get('pk')

        if not pk:
            return redirect('validation2')

        if role in (1, 10):
            try:
                now = timezone.now()
                with transaction.atomic():
                    c = Cargaison.objects.select_for_update().get(idcargaison=pk)

                    # Check if ImpressionResultat exists for the Cargaison
                    if not ImpressionResultat.objects.filter(idcargaison=c).exists():
                        # Create and save ImpressionResultat
                        ImpressionResultat.objects.create(
                            printDate=now.date(),
                            isConforme=True,
                            isPrinted=False,
                            idcargaison=c
                        )

                        # Update Cargaison fields
                        c.etat = "Conforme aux exigences"
                        c.conformite = "Conforme aux exigences"
                        c.impression = "0"
                        c.dateHeureAnalyseLabo = now
                        c.save(update_fields=['etat', 'impression', 'conformite', 'dateHeureAnalyseLabo'])

                        UserActivityLog.objects.create(
                            user=user,
                            action="Validation 2: CONFORME",
                            description=f"Cargaison {pk}: Final validation set to CONFORME via legacy view.",
                        )

                return redirect('validation2')
            except Cargaison.DoesNotExist:
                return redirect('validation2')
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def nonconforme2(request):
        user = request.user
        pk = request.session.get('pk')
        role = user.role_id

        if not pk:
            return redirect('validation2')

        if role in (1, 10):
            try:
                now = timezone.now()
                with transaction.atomic():
                    c = Cargaison.objects.select_for_update().get(idcargaison=pk)

                    if not ImpressionResultat.objects.filter(idcargaison=c).exists():
                        # Create and save ImpressionResultat
                        ImpressionResultat.objects.create(
                            printDate=now.date(),
                            isConforme=False,
                            isPrinted=False,
                            idcargaison=c
                        )

                        c.etat = "Non conforme aux exigences"
                        c.conformite = "Non conforme aux exigences"
                        c.impression = "0"
                        c.dateHeureAnalyseLabo = now
                        c.save(update_fields=['etat', 'impression', 'conformite', 'dateHeureAnalyseLabo'])

                        UserActivityLog.objects.create(
                            user=user,
                            action="Validation 2: NON CONFORME",
                            description=f"Cargaison {pk}: Final validation set to NON CONFORME via legacy view.",
                        )

                return redirect('validation2')
            except Cargaison.DoesNotExist:
                return redirect('validation2')
        else:
            return redirect('logout')

    # Fonction affichage des resultats sur Validation 2
    @login_required(login_url='login')
    def affichagetableauvalidation2(request):
        user = request.user
        role = user.role_id
        if role in (5, 1, 6, 10):
            return render(request, 'labo_validation2.html')
        else:
            return redirect('logout')


# Gestion des impression des CQ
class GestionImpressionLabo():

    # Fonction pour affichage tableu impression des certificats
    @login_required(login_url='login')
    def affichagetableauimpression(request):
        user = request.user
        id = user.id
        role = user.role_id

        if role not in (1, 5):
            return redirect('logout')

        # Leverage denormalized scoping (Consistent with optimized DataTables view)
        allowed_entrepot_ids = Entrepot.objects.filter(
            ville__affectationville__username_id=id
        ).values_list('identrepot', flat=True)

        base_qs = Cargaison.objects.filter(
            entrepot_id__in=allowed_entrepot_ids,
            etat="Conforme aux exigences"
        )

        # Robust printed status control using Exists
        printed_exists = ImpressionResultat.objects.filter(idcargaison=OuterRef('pk'), isPrinted=True)
        base_qs = base_qs.annotate(has_been_printed=Exists(printed_exists))

        cqNotPrinted = base_qs.filter(has_been_printed=False).count()
        cqPrinted = base_qs.filter(has_been_printed=True).count()

        # Lists for report filters
        entrepots_list = Entrepot.objects.filter(identrepot__in=allowed_entrepot_ids).order_by('nomentrepot')
        # Efficiently get importateurs linked to these cargaisons
        importateur_ids = base_qs.values_list('importateur_id', flat=True).distinct()
        importateurs_list = Importateur.objects.filter(idimportateur__in=importateur_ids).order_by('nomimportateur')

        request.session['url'] = request.get_full_path()
        template = 'labo_impression.html'

        context = {
            'cqNotPrinted': cqNotPrinted,
            'cqPrinted': cqPrinted,
            'entrepots_list': entrepots_list,
            'importateurs_list': importateurs_list,
        }
        return render(request, template, context)

    # Fonction de recherche des certificat à imprimer
    @login_required(login_url='login')
    def recherchecq(request):
        user = request.user
        role = user.role_id
        request.session['url'] = request.get_full_path()
        template = 'labo_impression.html'
        if role == 5 or role == 1 or role == 6 or role == "v2":
            numcode = request.GET.get('codelabo')
            if numcode != "":
                # Leverage denormalized scoping (Consistent with optimized DataTables view)
                allowed_entrepot_ids = Entrepot.objects.filter(
                    ville__affectationville__username_id=user.id
                ).values_list('identrepot', flat=True)

                qs = Cargaison.objects.filter(
                    entrepot_id__in=allowed_entrepot_ids,
                    code_labo=numcode,
                    impressionresultat__isPrinted=False
                ).annotate(
                    idImpression=F('impressionresultat__idImpression'),
                    numcertificatqualite=F('num_certificat_qualite'),
                    codelabo=F('code_labo'),
                    nomproduit=F('nom_produit'),
                    nomimportateur=F('nom_importateur'),
                    nomentrepot=F('nom_entrepot')
                )

                table = AffichageTableauImpression(qs, prefix='2_')
                RequestConfig(request, paginate={"per_page": 10}).configure(table)
                context = {'labo': table}
                return render(request, template, context)
            else:
                return redirect('impression')
        else:
            return redirect('logout')

    # Fonction de recherche des certificat à Re-imprimer
    @login_required(login_url='login')
    def recherchecqr(request):
        user = request.user
        role = user.role_id
        request.session['url'] = request.get_full_path()
        if role == 5 or role == 1 or role == "v1" or role == "v2":
            numcode = request.GET.get('codelabo')
            if numcode != "":
                # Leverage denormalized scoping (Consistent with optimized DataTables view)
                allowed_entrepot_ids = Entrepot.objects.filter(
                    ville__affectationville__username_id=user.id
                ).values_list('identrepot', flat=True)

                qs = Cargaison.objects.filter(
                    entrepot_id__in=allowed_entrepot_ids,
                    code_labo=numcode,
                    impressionresultat__isPrinted=True
                ).annotate(
                    idImpression=F('impressionresultat__idImpression'),
                    numcertificatqualite=F('num_certificat_qualite'),
                    codelabo=F('code_labo'),
                    nomproduit=F('nom_produit'),
                    nomimportateur=F('nom_importateur'),
                    nomentrepot=F('nom_entrepot')
                )

                table = AffichageTableauImpression(qs)

                RequestConfig(request, paginate={"per_page": 10}).configure(table)

                return render(request, 'labo_impression.html',
                              {
                                  'labo': table,
                              })
            else:
                return redirect('impression')
        else:
            return redirect('logout')


    @login_required(login_url='login')
    def reimpressioncertificat(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        url = request.session['url']
        if role == 5 or role == 1:
            td = datetime.today()
            today = td.date()

            # Récuperation des dates
            cargaison = Cargaison.objects.get(idcargaison=pk)
            if cargaison.date_reception_labo:
                mois = cargaison.date_reception_labo.month
                annee = cargaison.date_reception_labo.year
            else:
                mois = datetime.today().month
                annee = datetime.today().year

            # Recuperation du produit de la cargaison
            p = Produit.objects.get(cargaison=pk)
            produit = p.nomproduit

            # Fecthing object with pk corresponding into database
            a = Cargaison.objects.get(idcargaison=pk)
            b = Entrepot_echantillon.objects.get(idcargaison=pk)
            c = LaboReception.objects.get(idcargaison=pk)
            d = Resultat.objects.get(idcargaison=pk)

            # Fetching into DBS general results
            numcertificatqualite = c.numcertificatqualite
            codelabo = c.codelabo
            dateanalyse = d.dateanalyse
            importateur = a.importateur
            declarant = a.declarant
            dateechantillonage = b.dateechantillonage
            entrepot = a.entrepot
            provenance = a.provenance.name
            qte = b.qte
            datereceptionlabo = c.datereceptionlabo
            codelabo = c.codelabo
            numdossier = a.numdossier
            immatriculation = a.immatriculation
            numrappech = b.numrappech

            # Putting printing counter to 1
            a.impression = "1"
            a.save(update_fields=['impression'])

            # # Saving print date into DBS
            # d.dateimpression = today
            # d.save(update_fields=['dateimpression'])
            #
            dateimpression = d.dateimpression

            # Test pour afficher les differents rapports
            if produit == 'GASOIL':
                template = 'report/rapportvalide/gasoilreport.html'

                # Resultat Gasoil Fetching data into Database
                couleurastm = d.couleurastm
                aciditetotal = d.aciditetotal
                soufre = d.soufre
                massevolumique = d.massevolumique
                massevolumique15 = d.massevolumique15
                distillation = d.distillation
                distillation10 = d.distillation10
                distillation20 = d.distillation20
                distillation50 = d.distillation50
                distillation90 = d.distillation90
                pointinitial = d.pointinitial
                pointfinal = d.pointfinal
                pointeclair = d.pointeclair
                viscosite = d.viscosite
                pointecoulement = d.pointecoulement
                teneureau = d.teneureau
                sediment = d.sediment
                corrosion = d.corrosion
                indicecetane = d.indicecetane
                densite = d.densite
                recuperation362 = d.recuperation362
                cendre = d.cendre

                data = {
                    'numcertificatqualite': numcertificatqualite,
                    'dateanalyse': dateanalyse,
                    'dateimpression': dateimpression,
                    'importateur': importateur,
                    'declarant': declarant,
                    'entrepot': entrepot,
                    'dateechantillonage': dateechantillonage,
                    'provenance': provenance,
                    'qte': qte,
                    'datereceptionlabo': datereceptionlabo,
                    'codelabo': codelabo,
                    'numdossier': numdossier,
                    'immatriculation': immatriculation,
                    'couleurastm': couleurastm,
                    'aciditetotal': aciditetotal,
                    'soufre': soufre,
                    'massevolumique': massevolumique,
                    'distillation': distillation,
                    'distillation10': distillation10,
                    'distillation20': distillation20,
                    'distillation50': distillation50,
                    'distillation90': distillation90,
                    'pointfinal': pointfinal,
                    'pointeclair': pointeclair,
                    'pointinitial': pointinitial,
                    'viscosite': viscosite,
                    'pointecoulement': pointecoulement,
                    'teneureau': teneureau,
                    'sediment': sediment,
                    'corrosion': corrosion,
                    'indicecetane': indicecetane,
                    'densite': densite,
                    'recuperation362': recuperation362,
                    'cendre': cendre,
                    'massevolumique15': massevolumique15,
                    'numrappech': numrappech,
                    'produit': produit,
                    'mois': mois,
                    'annee': annee
                }

                # Rendered PDF report
                pdf = render_to_pdf(template, data)
                return HttpResponse(pdf, content_type='application/pdf')

            else:
                if produit == 'MOGAS':
                    template = 'report/rapportvalide/mogasreport.html'
                    # Resultat Gasoil Fetching data into Database
                    aspect = d.aspect
                    odeur = d.odeur
                    couleursaybolt = d.couleursaybolt
                    soufre = d.soufre
                    distillation = d.distillation
                    pointfinal = d.pointfinal
                    residu = d.residu
                    corrosion = d.corrosion
                    pourcent10 = d.pourcent10
                    pourcent20 = d.pourcent20
                    pourcent50 = d.pourcent50
                    pourcent70 = d.pourcent70
                    pourcent90 = d.pourcent90
                    tensionvapeur = d.tensionvapeur
                    difftemperature = d.difftemperature
                    plomb = d.plomb
                    indiceoctane = d.indiceoctane
                    massevolumique15 = d.massevolumique15

                    data = {
                        'numcertificatqualite': numcertificatqualite,
                        'dateanalyse': dateanalyse,
                        'dateimpression': dateimpression,
                        'importateur': importateur,
                        'declarant': declarant,
                        'entrepot': entrepot,
                        'dateechantillonage': dateechantillonage,
                        'provenance': provenance,
                        'qte': qte,
                        'datereceptionlabo': datereceptionlabo,
                        'codelabo': codelabo,
                        'numdossier': numdossier,
                        'immatriculation': immatriculation,
                        'numrappech': numrappech,
                        'aspect': aspect,
                        'odeur': odeur,
                        'couleursaybolt': couleursaybolt,
                        'soufre': soufre,
                        'distillation': distillation,
                        'pointfinal': pointfinal,
                        'residu': residu,
                        'corrosion': corrosion,
                        'pourcent10': pourcent10,
                        'pourcent20': pourcent20,
                        'pourcent50': pourcent50,
                        'pourcent70': pourcent70,
                        'pourcent90': pourcent90,
                        'tensionvapeur': tensionvapeur,
                        'difftemperature': difftemperature,
                        'plomb': plomb,
                        'indiceoctane': indiceoctane,
                        'massevolumique15': massevolumique15,
                        'produit': produit,
                        'mois': mois,
                        'annee': annee
                    }

                    # Rendered PDF report
                    pdf = render_to_pdf(template, data)
                    return HttpResponse(pdf, content_type='application/pdf')
                else:
                    if produit == 'JET A1':
                        template = 'report/rapportvalide/jeta1report.html'

                        # Resultat Gasoil Fetching data into Database
                        aspect = d.aspect
                        couleursaybolt = d.couleursaybolt
                        aciditetotal = d.aciditetotal
                        soufre = d.soufre
                        soufremercaptan = d.soufremercaptan
                        docteurtest = d.docteurtest
                        distillation = d.distillation
                        pointinitial = d.pointinitial
                        pointfinal = d.pointfinal
                        pointfumee = d.pointfumee
                        pointeclair = d.pointeclair
                        freezingpoint = d.freezingpoint
                        residu = d.residu
                        perte = d.perte
                        massevolumique15 = d.massevolumique15
                        viscosite = d.viscosite
                        pointinflammabilite = d.pointinflammabilite
                        teneureau = d.teneureau
                        corrosion = d.corrosion
                        conductivite = d.conductivite
                        vol10 = d.vol10
                        vol20 = d.vol20
                        vol30 = d.vol30
                        vol40 = d.vol40
                        vol50 = d.vol50
                        vol60 = d.vol60
                        vol70 = d.vol70
                        vol80 = d.vol80
                        vol90 = d.vol90

                        data = {
                            'numcertificatqualite': numcertificatqualite,
                            'dateanalyse': dateanalyse,
                            'dateimpression': dateimpression,
                            'importateur': importateur,
                            'declarant': declarant,
                            'entrepot': entrepot,
                            'dateechantillonage': dateechantillonage,
                            'provenance': provenance,
                            'qte': qte,
                            'datereceptionlabo': datereceptionlabo,
                            'codelabo': codelabo,
                            'numdossier': numdossier,
                            'immatriculation': immatriculation,
                            'numrappech': numrappech,
                            'aspect': aspect,
                            'couleursaybolt': couleursaybolt,
                            'aciditetotal': aciditetotal,
                            'soufre': soufre,
                            'soufremercaptan': soufremercaptan,
                            'docteurtest': docteurtest,
                            'distillation': distillation,
                            'pointinitial': pointinitial,
                            'pointfinal': pointfinal,
                            'pointfumee': pointfumee,
                            'freezingpoint': freezingpoint,
                            'residu': residu,
                            'perte': perte,
                            'pointeclair': pointeclair,
                            'massevolumique15': massevolumique15,
                            'viscosite': viscosite,
                            'pointinflammabilite': pointinflammabilite,
                            'teneureau': teneureau,
                            'corrosion': corrosion,
                            'conductivite': conductivite,
                            'vol10': vol10,
                            'vol20': vol20,
                            'vol30': vol30,
                            'vol40': vol40,
                            'vol50': vol50,
                            'vol60': vol60,
                            'vol70': vol70,
                            'vol80': vol80,
                            'vol90': vol90,
                            'produit': produit,
                            'mois': mois,
                            'annee': annee
                        }
                        # Rendered PDF report
                        pdf = render_to_pdf(template, data)
                        return HttpResponse(pdf, content_type='application/pdf')

                    else:
                        if produit == 'PETROLE LAMPANT':
                            template = 'report/rapportvalide/petrolereport.html'

                            # Resultat Gasoil Fetching data into Database
                            aspect = d.aspect
                            couleursaybolt = d.couleursaybolt
                            aciditetotal = d.aciditetotal
                            soufre = d.soufre
                            soufremercaptan = d.soufremercaptan
                            docteurtest = d.docteurtest
                            distillation = d.distillation
                            pointinitial = d.pointinitial
                            pointfinal = d.pointfinal
                            pointfumee = d.pointfumee
                            pointeclair = d.pointeclair
                            freezingpoint = d.freezingpoint
                            residu = d.residu
                            perte = d.perte
                            massevolumique15 = d.massevolumique15
                            viscosite = d.viscosite
                            pointinflammabilite = d.pointinflammabilite
                            teneureau = d.teneureau
                            corrosion = d.corrosion
                            conductivite = d.conductivite
                            vol10 = d.vol10
                            vol20 = d.vol20
                            vol30 = d.vol30
                            vol40 = d.vol40
                            vol50 = d.vol50
                            vol60 = d.vol60
                            vol70 = d.vol70
                            vol80 = d.vol80
                            vol90 = d.vol90

                            data = {
                                'numcertificatqualite': numcertificatqualite,
                                'dateanalyse': dateanalyse,
                                'dateimpression': dateimpression,
                                'importateur': importateur,
                                'declarant': declarant,
                                'entrepot': entrepot,
                                'dateechantillonage': dateechantillonage,
                                'provenance': provenance,
                                'qte': qte,
                                'datereceptionlabo': datereceptionlabo,
                                'codelabo': codelabo,
                                'numdossier': numdossier,
                                'immatriculation': immatriculation,
                                'numrappech': numrappech,
                                'aspect': aspect,
                                'couleursaybolt': couleursaybolt,
                                'aciditetotal': aciditetotal,
                                'soufre': soufre,
                                'soufremercaptan': soufremercaptan,
                                'docteurtest': docteurtest,
                                'distillation': distillation,
                                'pointinitial': pointinitial,
                                'pointfinal': pointfinal,
                                'pointfumee': pointfumee,
                                'freezingpoint': freezingpoint,
                                'residu': residu,
                                'perte': perte,
                                'pointeclair': pointeclair,
                                'massevolumique15': massevolumique15,
                                'viscosite': viscosite,
                                'pointinflammabilite': pointinflammabilite,
                                'teneureau': teneureau,
                                'corrosion': corrosion,
                                'conductivite': conductivite,
                                'vol10': vol10,
                                'vol20': vol20,
                                'vol30': vol30,
                                'vol40': vol40,
                                'vol50': vol50,
                                'vol60': vol60,
                                'vol70': vol70,
                                'vol80': vol80,
                                'vol90': vol90,
                                'produit': produit,
                                'mois': mois,
                                'annee': annee
                            }

                            # Rendered PDF report
                            pdf = render_to_pdf(template, data)
                            return HttpResponse(pdf, content_type='application/pdf')
                    return redirect('logout')
        else:
            return redirect('logout')

    # Fontion pour impression des fiches de resultats
    @login_required(login_url='login')
    def impressionficheresultat(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 5 or role == 1 or role == 6 or role == "v2":

            # Récuperation des dates
            cargaison = Cargaison.objects.get(idcargaison=pk)
            if cargaison.date_reception_labo:
                mois = cargaison.date_reception_labo.month
                annee = cargaison.date_reception_labo.year
            else:
                mois = datetime.today().month
                annee = datetime.today().year
            # Recuperation du produit de la cargaison
            p = Produit.objects.get(cargaison=pk)
            produit = p.nomproduit

            # Fecthing object with pk corresponding into database
            a = Cargaison.objects.get(idcargaison=pk)
            b = Entrepot_echantillon.objects.get(idcargaison=pk)
            c = LaboReception.objects.get(idcargaison=pk)
            d = Resultat.objects.get(idcargaison=pk)

            # Fetching into DBS general results
            numcertificatqualite = c.numcertificatqualite
            codelabo = c.codelabo
            dateanalyse = d.dateanalyse
            importateur = a.importateur
            declarant = a.declarant
            dateechantillonage = b.dateechantillonage
            entrepot = a.entrepot
            provenance = a.provenance.name
            qte = b.qte
            datereceptionlabo = c.datereceptionlabo
            codelabo = c.codelabo
            numdossier = a.numdossier
            immatriculation = a.immatriculation
            numrappech = b.numrappech

            # Test pour afficher les differents rapports
            if produit == 'GASOIL':
                template = 'report/encodage/gasoilreport.html'

                # Resultat Gasoil Fetching data into Database
                couleurastm = d.couleurastm
                aciditetotal = d.aciditetotal
                soufre = d.soufre
                massevolumique = d.massevolumique
                massevolumique15 = d.massevolumique15
                distillation = d.distillation
                distillation10 = d.distillation10
                distillation20 = d.distillation20
                distillation50 = d.distillation50
                distillation90 = d.distillation90
                pointinitial = d.pointinitial
                pointfinal = d.pointfinal
                pointeclair = d.pointeclair
                viscosite = d.viscosite
                pointecoulement = d.pointecoulement
                teneureau = d.teneureau
                sediment = d.sediment
                corrosion = d.corrosion
                indicecetane = d.indicecetane
                densite = d.densite
                recuperation362 = d.recuperation362
                cendre = d.cendre

                data = {
                    'numcertificatqualite': numcertificatqualite,
                    'dateanalyse': dateanalyse,
                    'importateur': importateur,
                    'declarant': declarant,
                    'entrepot': entrepot,
                    'dateechantillonage': dateechantillonage,
                    'provenance': provenance,
                    'qte': qte,
                    'datereceptionlabo': datereceptionlabo,
                    'codelabo': codelabo,
                    'numdossier': numdossier,
                    'immatriculation': immatriculation,
                    'couleurastm': couleurastm,
                    'aciditetotal': aciditetotal,
                    'soufre': soufre,
                    'massevolumique': massevolumique,
                    'distillation': distillation,
                    'distillation10': distillation10,
                    'distillation20': distillation20,
                    'distillation50': distillation50,
                    'distillation90': distillation90,
                    'pointfinal': pointfinal,
                    'pointeclair': pointeclair,
                    'pointinitial': pointinitial,
                    'viscosite': viscosite,
                    'pointecoulement': pointecoulement,
                    'teneureau': teneureau,
                    'sediment': sediment,
                    'corrosion': corrosion,
                    'indicecetane': indicecetane,
                    'densite': densite,
                    'recuperation362': recuperation362,
                    'cendre': cendre,
                    'massevolumique15': massevolumique15,
                    'numrappech': numrappech,
                    'produit': produit,
                    'mois': mois,
                    'annee': annee
                }

                # Rendered PDF report
                pdf = render_to_pdf(template, data)
                return HttpResponse(pdf, content_type='application/pdf')

            else:
                if produit == 'MOGAS':
                    template = 'report/encodage/mogasreport.html'
                    # Resultat Gasoil Fetching data into Database
                    aspect = d.aspect
                    odeur = d.odeur
                    couleursaybolt = d.couleursaybolt
                    soufre = d.soufre
                    distillation = d.distillation
                    pointfinal = d.pointfinal
                    residu = d.residu
                    corrosion = d.corrosion
                    pourcent10 = d.pourcent10
                    pourcent20 = d.pourcent20
                    pourcent50 = d.pourcent50
                    pourcent70 = d.pourcent70
                    pourcent90 = d.pourcent90
                    tensionvapeur = d.tensionvapeur
                    difftemperature = d.difftemperature
                    plomb = d.plomb
                    indiceoctane = d.indiceoctane
                    massevolumique15 = d.massevolumique15

                    data = {
                        'numcertificatqualite': numcertificatqualite,
                        'dateanalyse': dateanalyse,
                        'importateur': importateur,
                        'declarant': declarant,
                        'entrepot': entrepot,
                        'dateechantillonage': dateechantillonage,
                        'provenance': provenance,
                        'qte': qte,
                        'datereceptionlabo': datereceptionlabo,
                        'codelabo': codelabo,
                        'numdossier': numdossier,
                        'immatriculation': immatriculation,
                        'numrappech': numrappech,
                        'aspect': aspect,
                        'odeur': odeur,
                        'couleursaybolt': couleursaybolt,
                        'soufre': soufre,
                        'distillation': distillation,
                        'pointfinal': pointfinal,
                        'residu': residu,
                        'corrosion': corrosion,
                        'pourcent10': pourcent10,
                        'pourcent20': pourcent20,
                        'pourcent50': pourcent50,
                        'pourcent70': pourcent70,
                        'pourcent90': pourcent90,
                        'tensionvapeur': tensionvapeur,
                        'difftemperature': difftemperature,
                        'plomb': plomb,
                        'indiceoctane': indiceoctane,
                        'massevolumique15': massevolumique15,
                        'produit': produit,
                        'mois': mois,
                        'annee': annee
                    }

                    # Rendered PDF report
                    pdf = render_to_pdf(template, data)
                    return HttpResponse(pdf, content_type='application/pdf')
                else:
                    if produit == 'JET A1':
                        template = 'report/encodage/jeta1report.html'

                        # Resultat Gasoil Fetching data into Database
                        aspect = d.aspect
                        couleursaybolt = d.couleursaybolt
                        aciditetotal = d.aciditetotal
                        soufre = d.soufre
                        soufremercaptan = d.soufremercaptan
                        docteurtest = d.docteurtest
                        distillation = d.distillation
                        pointinitial = d.pointinitial
                        pointfinal = d.pointfinal
                        pointfumee = d.pointfumee
                        pointeclair = d.pointeclair
                        freezingpoint = d.freezingpoint
                        residu = d.residu
                        perte = d.perte
                        massevolumique15 = d.massevolumique15
                        viscosite = d.viscosite
                        pointinflammabilite = d.pointinflammabilite
                        teneureau = d.teneureau
                        corrosion = d.corrosion
                        conductivite = d.conductivite
                        vol10 = d.vol10
                        vol20 = d.vol20
                        vol30 = d.vol30
                        vol40 = d.vol40
                        vol50 = d.vol50
                        vol60 = d.vol60
                        vol70 = d.vol70
                        vol80 = d.vol80
                        vol90 = d.vol90

                        data = {
                            'numcertificatqualite': numcertificatqualite,
                            'dateanalyse': dateanalyse,
                            'importateur': importateur,
                            'declarant': declarant,
                            'entrepot': entrepot,
                            'dateechantillonage': dateechantillonage,
                            'provenance': provenance,
                            'qte': qte,
                            'datereceptionlabo': datereceptionlabo,
                            'codelabo': codelabo,
                            'numdossier': numdossier,
                            'immatriculation': immatriculation,
                            'numrappech': numrappech,
                            'aspect': aspect,
                            'couleursaybolt': couleursaybolt,
                            'aciditetotal': aciditetotal,
                            'soufre': soufre,
                            'soufremercaptan': soufremercaptan,
                            'docteurtest': docteurtest,
                            'distillation': distillation,
                            'pointinitial': pointinitial,
                            'pointfinal': pointfinal,
                            'pointfumee': pointfumee,
                            'freezingpoint': freezingpoint,
                            'residu': residu,
                            'perte': perte,
                            'pointeclair': pointeclair,
                            'massevolumique15': massevolumique15,
                            'viscosite': viscosite,
                            'pointinflammabilite': pointinflammabilite,
                            'teneureau': teneureau,
                            'corrosion': corrosion,
                            'conductivite': conductivite,
                            'vol10': vol10,
                            'vol20': vol20,
                            'vol30': vol30,
                            'vol40': vol40,
                            'vol50': vol50,
                            'vol60': vol60,
                            'vol70': vol70,
                            'vol80': vol80,
                            'vol90': vol90,
                            'produit': produit,
                            'mois': mois,
                            'annee': annee
                        }
                        # Rendered PDF report
                        pdf = render_to_pdf(template, data)
                        return HttpResponse(pdf, content_type='application/pdf')

                    else:
                        if produit == 'PETROLE LAMPANT':
                            template = 'report/encodage/petrolereport.html'

                            # Resultat Gasoil Fetching data into Database
                            aspect = d.aspect
                            couleursaybolt = d.couleursaybolt
                            aciditetotal = d.aciditetotal
                            soufre = d.soufre
                            soufremercaptan = d.soufremercaptan
                            docteurtest = d.docteurtest
                            distillation = d.distillation
                            pointinitial = d.pointinitial
                            pointfinal = d.pointfinal
                            pointfumee = d.pointfumee
                            pointeclair = d.pointeclair
                            freezingpoint = d.freezingpoint
                            residu = d.residu
                            perte = d.perte
                            massevolumique15 = d.massevolumique15
                            viscosite = d.viscosite
                            pointinflammabilite = d.pointinflammabilite
                            teneureau = d.teneureau
                            corrosion = d.corrosion
                            conductivite = d.conductivite
                            vol10 = d.vol10
                            vol20 = d.vol20
                            vol30 = d.vol30
                            vol40 = d.vol40
                            vol50 = d.vol50
                            vol60 = d.vol60
                            vol70 = d.vol70
                            vol80 = d.vol80
                            vol90 = d.vol90

                            data = {
                                'numcertificatqualite': numcertificatqualite,
                                'dateanalyse': dateanalyse,
                                'importateur': importateur,
                                'declarant': declarant,
                                'entrepot': entrepot,
                                'dateechantillonage': dateechantillonage,
                                'provenance': provenance,
                                'qte': qte,
                                'datereceptionlabo': datereceptionlabo,
                                'codelabo': codelabo,
                                'numdossier': numdossier,
                                'immatriculation': immatriculation,
                                'numrappech': numrappech,
                                'aspect': aspect,
                                'couleursaybolt': couleursaybolt,
                                'aciditetotal': aciditetotal,
                                'soufre': soufre,
                                'soufremercaptan': soufremercaptan,
                                'docteurtest': docteurtest,
                                'distillation': distillation,
                                'pointinitial': pointinitial,
                                'pointfinal': pointfinal,
                                'pointfumee': pointfumee,
                                'freezingpoint': freezingpoint,
                                'residu': residu,
                                'perte': perte,
                                'pointeclair': pointeclair,
                                'massevolumique15': massevolumique15,
                                'viscosite': viscosite,
                                'pointinflammabilite': pointinflammabilite,
                                'teneureau': teneureau,
                                'corrosion': corrosion,
                                'conductivite': conductivite,
                                'vol10': vol10,
                                'vol20': vol20,
                                'vol30': vol30,
                                'vol40': vol40,
                                'vol50': vol50,
                                'vol60': vol60,
                                'vol70': vol70,
                                'vol80': vol80,
                                'vol90': vol90,
                                'produit': produit,
                                'mois': mois,
                                'annee': annee
                            }

                            # Rendered PDF report
                            pdf = render_to_pdf(template, data)
                            return HttpResponse(pdf, content_type='application/pdf')
                    return redirect('logout')
        else:
            return redirect('logout')


# Systèmes de bypass pour l'envoi du GO à la cellule Hydro

class EnvoiGoHydro():

    def gohydro(request):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 6 or role == 1:
            table = TableEnvoiGo(
                Resultat.objects.filter(idcargaison__idcargaison__idcargaison__etat="En attente validation 2",
                                        idcargaison__idcargaison__idcargaison__entrepot_id__ville_id=user.ville))
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 10}).configure(table)
            return render(request, 'labo_validation2.html', {'labo': table})
        else:
            return redirect('logout')


@login_required(login_url='login')
def labdashboard(request):
    user = request.user
    role = user.role_id
    id = user.id
    u = user.username
    username = user.username
    ville = AffectationVille.objects.get(username=id)
    ville = ville.ville_id
    template = 'labodashboard.html'
    form = RapportLabo()

    # compteur de nombre de cargaison en attente de reception

    data = {'form': form}
    return render(request, template, data)


@login_required(login_url='login')
def labdashboardrapport(request):
    user = request.user
    id = user.id
    ville = AffectationVille.objects.get(username=id)
    v_id = ville.ville_id
    template = 'labodashboardrapport.html'

    if request.method == 'POST':
        datedebut = request.POST['datedebut']
        datefin = request.POST['datefin']
        request.session['datedebut'] = datedebut
        request.session['datefin'] = datefin
    else:
        datedebut = request.session.get('datedebut')
        datefin = request.session.get('datefin')

    if not datedebut or not datefin:
        # Fallback if no dates in session or post
        return render(request, template, {'table': None})

    # Use Cargaison with denormalized fields
    qs = Cargaison.objects.filter(
        entrepot__ville_id=v_id,
        date_reception_labo__date__range=(datedebut, datefin)
    ).only(
        'idcargaison',
        'date_echantillon',
        'date_reception_labo',
        'nom_importateur',
        'nom_entrepot',
        'immatriculation',
        'numdossier',
        'codecargaison',
        'entrepot_echantillon__numrappech',
        'code_labo',
        'date_analyse',
        'resultat__dateimpression',
        'num_certificat_qualite'
    ).order_by('-date_reception_labo')

    table1 = RapportLaboTable(qs, prefix='1_')
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table1)

    if request.method == 'GET':
        export_format = request.GET.get('_export', None)
        if TableExport.is_valid_format(export_format):
            exporter = TableExport(export_format, table1)
            return exporter.response('table.{}'.format(export_format))

    return render(request, template, {'table': table1})


@login_required(login_url='login')
def echantCount(request):
    user = request.user
    role = user.role_id
    id = user.id
    u = user.username
    username = user.username
    ville = AffectationVille.objects.get(username=id)
    ville = ville.ville_id
    template = 'validationCompteur.html'
    qs = LaboReception.objects.filter(idcargaison__idcargaison__entrepot__ville=ville,
                                      idcargaison__idcargaison__etat='Echantillonner').order_by('-datereceptionlabo')
    table = EchantReception(qs, prefix='1_')
    RequestConfig(request, paginate={"per_page": 20}).configure(table)
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def echantAnalyse(request):
    user = request.user
    role = user.role_id
    id = user.id
    u = user.username
    username = user.username
    ville = AffectationVille.objects.get(username=id)
    ville = ville.ville_id
    template = 'AnalyseCompteur.html'
    qs = LaboReception.objects.filter(idcargaison__idcargaison__entrepot__ville=ville,
                                      idcargaison__idcargaison__etat='Analyse Labo en cours').order_by(
        '-datereceptionlabo')
    table = EchantReception(qs, prefix='1_')
    RequestConfig(request, paginate={"per_page": 20}).configure(table)
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def natureProduitLabo(request, pk):
    user = request.user.id
    template = 'natureProduitLaboratoire.html'
    cargaison = Cargaison.objects.get(idcargaison=pk)
    form = NatureProduitLaboratoire(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            produit = request.POST['natureProduit']
            if int(produit) == int(cargaison.produit.idproduit):
                return redirect('reception', pk=pk)
            else:
                produit = Produit.objects.get(idproduit=produit)
                try:
                    c = ControlNatureProduit.objects.get(idcargaison=pk)
                    c.natureProduitLabo = produit.nomproduit
                    c.userLabo = user
                    c.save(update_fields=['natureProduitLabo', 'userLabo'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Product denomination update",
                        description=f"User has changed the nature of the product for the record {cargaison.idcargaison}"
                    )

                    return redirect('reception', pk=pk)
                except:
                    c = ControlNatureProduit(idcargaison=cargaison, natureProduitLabo=produit.nomproduit, userLabo=user)
                    c.save()

                    UserActivityLog.objects.create(
                        user=user,
                        action="Product denomination update",
                        description=f"User has changed the nature of the product for the record {cargaison.idcargaison}"
                    )

                    return redirect('reception', pk=pk)
    else:
        context = {'form': form}
        return render(request, template, context)


# Saisie saisieResultat
@login_required(login_url='login')
def saisieResultat(request, pk):
    template = 'labo_analyse_form.html'
    request.session['pk'] = pk
    e = Entrepot_echantillon.objects.get(idcargaison=pk)
    a = LaboReception.objects.get(idcargaison=e)
    a = a.codelabo
    # c = Cargaison.objects.get(idcargaison=pk)

    qs = ParametresProduits.objects.raw('SELECT pp.idParametre, c.idcargaison, p.nomproduit, pp.nomParametre, r.valeurResultat, r.valeurResultatChar \
            FROM enreg_cargaison c \
            LEFT JOIN enreg_produit p \
            ON c.produit_id = p.idproduit \
            LEFT JOIN enreg_affectationparametre a \
            ON p.idproduit = a.idproduit_id \
            LEFT JOIN enreg_parametresproduits pp \
            ON a.idParametre_id = pp.idParametre \
            LEFT JOIN enreg_resultatanalyse r \
            ON pp.idParametre = r.idParametre_id \
            AND r.idcargaison_id = c.idcargaison \
            WHERE c.idcargaison = %s \
            ORDER BY a.id ASC', [pk, ])

    table = SaisieResultat(qs)
    # RequestConfig(request, paginate={"per_page": 10}).configure(table)
    context = {
        'table': table,
        'codeLabo': a,
    }
    return render(request, template, context)


@login_required(login_url='login')
def saisieResultatParametre(request, pk):
    user = request.user
    id = request.session['pk']
    cargaison = Cargaison.objects.get(idcargaison=id)
    parametre = ParametresProduits.objects.get(idParametre=pk)
    if request.method == 'POST':
        valeurResultat = request.POST['valeurResultat']
        if parametre.idParametre == 2 or parametre.idParametre == 8 or parametre.idParametre == 22:
            try:
                r = ResultatAnalyse.objects.get(idParametre=parametre, idcargaison=cargaison)
                r.valeurResultatChar = valeurResultat
                r.save(update_fields=['valeurResultatChar'])

                UserActivityLog.objects.create(
                    user=user,
                    action="Test result input",
                    description=f"User has input the test result for the record {cargaison.idcargaison}",
                )
                # print('OK')
                return redirect('saisieResultat', id)
            except:
                r = ResultatAnalyse(valeurResultatChar=valeurResultat, idParametre=parametre, idcargaison=cargaison)
                r.save()
                UserActivityLog.objects.create(
                    user=user,
                    action="Test result input",
                    description=f"User has input the test result for the record {cargaison.idcargaison}",
                )
                # print('OK')
                return redirect('saisieResultat', id)
        else:
            try:
                r = ResultatAnalyse.objects.get(idParametre=parametre, idcargaison=cargaison)
                r.valeurResultat = valeurResultat
                r.save(update_fields=['valeurResultat'])
                UserActivityLog.objects.create(
                    user=user,
                    action="Test result input",
                    description=f"User has input the test result for the record {cargaison.idcargaison}",
                )
                # print('OK')
                return redirect('saisieResultat', id)
            except:
                r = ResultatAnalyse(valeurResultat=valeurResultat, idParametre=parametre, idcargaison=cargaison)
                r.save()
                UserActivityLog.objects.create(
                    user=user,
                    action="Test result input",
                    description=f"User has input the test result for the record {cargaison.idcargaison}",
                )
                # print('OK')
                return redirect('saisieResultat', id)
    else:
        return redirect('saisieResultat', id)


@login_required(login_url='login')
def validationResulat(request):
    user = request.user
    if request.method == 'POST':
        idcargaison = request.POST.get('idcargaison')
        if not idcargaison:
            return JsonResponse({'status': 'error', 'message': 'Missing ID'}, status=400)

        # Efficient update
        updated = Cargaison.objects.filter(idcargaison=idcargaison).update(etat='Validation en cours 1')
        
        if updated:
            UserActivityLog.objects.create(
                user=user,
                action="Test result form confirmation",
                object_id=str(idcargaison),
                description=f"User {user.get_full_name()} confirmed results for cargaison {idcargaison}",
            )
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Cargaison not found'}, status=404)
    else:
        return redirect('analyse')


# KPI details (Dashboard modal, POST-only JSON)
@login_required(login_url='login')
@require_POST
def laboValidationKPIs(request):
    user_id = request.user.id
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = now - timedelta(days=1)

    # Leverage denormalized scoping
    allowed_entrepot_ids = Entrepot.objects.filter(
        ville__affectationville__username_id=user_id
    ).values_list('identrepot', flat=True)

    base_qs = Cargaison.objects.filter(entrepot_id__in=allowed_entrepot_ids)

    # Level 1 Stats (SCE Hydro)
    lvl1_pending = base_qs.filter(etat="Validation en cours 1").count()
    lvl1_late = base_qs.filter(etat="Validation en cours 1", date_reception_labo__lt=yesterday).count()
    
    # We can't filter Cargaison by UserActivityLog directly (no FK). 
    # We count the logs for the current user today.
    lvl1_done_today = UserActivityLog.objects.filter(
        user_id=user_id,
        action__icontains="Validation 1",
        timestamp__gte=today_start
    ).count()

    # Level 2 Stats (Chef Labo)
    lvl2_pending = base_qs.filter(etat="Validation en cours 2").count()
    lvl2_done_today = base_qs.filter(
        etat="Conforme aux exigences",
        dateHeureAnalyseLabo__gte=today_start
    ).count()

    return JsonResponse({
        'lvl1': {
            'pending': lvl1_pending,
            'late': lvl1_late,
            'done_today': lvl1_done_today,
        },
        'lvl2': {
            'pending': lvl2_pending,
            'done_today': lvl2_done_today,
        }
    })


@login_required(login_url='login')
@require_POST
def laboImpressionKPIs(request):
    user_id = request.user.id
    
    # Leverage denormalized scoping
    allowed_entrepot_ids = Entrepot.objects.filter(
        ville__affectationville__username_id=user_id
    ).values_list('identrepot', flat=True)

    base_qs = Cargaison.objects.filter(
        entrepot_id__in=allowed_entrepot_ids,
        etat="Conforme aux exigences"
    )

    # Robust printed status control using Exists to handle ForeignKey relationship correctly
    printed_exists = ImpressionResultat.objects.filter(idcargaison=OuterRef('pk'), isPrinted=True)
    base_qs = base_qs.annotate(has_been_printed=Exists(printed_exists))

    not_printed = base_qs.filter(has_been_printed=False).count()
    printed = base_qs.filter(has_been_printed=True).count()

    return JsonResponse({
        'not_printed': not_printed,
        'printed': printed
    })


@login_required(login_url='login')
def affichageDetailsResultats(request, pk):
    try:
        # Use only needed fields
        cargaison = Cargaison.objects.only('idcargaison', 'produit_id', 'code_labo').get(idcargaison=pk)
    except Cargaison.DoesNotExist:
        return HttpResponse("Cargaison introuvable.", status=404)

    # Fetch parameters linked to this product via AffectationParametre
    params_qs = (
        AffectationParametre.objects
        .filter(idproduit=cargaison.produit_id)
        .select_related('idParametre')
        .order_by('id')
    )

    # Fetch results for this cargaison in a single query
    results_dict = {
        r.idParametre_id: r 
        for r in ResultatAnalyse.objects.filter(idcargaison_id=pk)
    }

    data_list = []
    for ap in params_qs:
        param = ap.idParametre
        res = results_dict.get(param.idParametre)

        val_num = res.valeurResultat if res else None
        val_char = res.valeurResultatChar if res else None

        # Clean up based on parameter type (IDs 2, 8, 22 are Alpha)
        is_alpha = param.idParametre in [2, 8, 22]
        if is_alpha:
            val_num = None
        else:
            val_char = None

        # Conformance check logic
        status = "En attente"
        if val_num is not None:
            is_out = False
            if ap.valeurMax is not None and val_num > ap.valeurMax:
                is_out = True
            if ap.valeurMin is not None and val_num < ap.valeurMin:
                is_out = True
            
            status = "Hors norme" if is_out else "Conforme"
        elif val_char:
            status = "Conforme"

        data_list.append({
            'codelabo': cargaison.code_labo,
            'nomParametre': param.nomParametre,
            'valeurMin': ap.valeurMin,
            'valeurMax': ap.valeurMax,
            'valeurResultatChar': val_char,
            'valeurResultat': val_num,
            'etatValeur': status
        })

    table = AffichageDetailResultat(data_list, prefix='_1')
    # No pagination needed for a single analysis details modal usually, but keeping it if list is long
    RequestConfig(request, paginate=False).configure(table)

    return render(request, 'laboDetailsResultat.html', {'table': table})


@login_required(login_url='login')
def affichageDetailsResultatsDroite(request, pk):
    # Same logic as above, can reuse if exactly identical, 
    # but often specialized for different validation stages.
    # For now, optimizing similarly.
    try:
        cargaison = Cargaison.objects.only('idcargaison', 'produit_id', 'code_labo').get(idcargaison=pk)
    except Cargaison.DoesNotExist:
        return HttpResponse("Cargaison introuvable.", status=404)

    params_qs = (
        AffectationParametre.objects
        .filter(idproduit=cargaison.produit_id)
        .select_related('idParametre')
        .order_by('id')
    )

    results_dict = {
        r.idParametre_id: r 
        for r in ResultatAnalyse.objects.filter(idcargaison_id=pk)
    }

    data_list = []
    for ap in params_qs:
        param = ap.idParametre
        res = results_dict.get(param.idParametre)

        val_num = res.valeurResultat if res else None
        val_char = res.valeurResultatChar if res else None

        # Clean up based on parameter type (IDs 2, 8, 22 are Alpha)
        is_alpha = param.idParametre in [2, 8, 22]
        if is_alpha:
            val_num = None
        else:
            val_char = None

        status = "En attente"
        if val_num is not None:
            is_out = False
            if ap.valeurMax is not None and val_num > ap.valeurMax:
                is_out = True
            if ap.valeurMin is not None and val_num < ap.valeurMin:
                is_out = True
            status = "Hors norme" if is_out else "Conforme"
        elif val_char:
            status = "Conforme"

        data_list.append({
            'codelabo': cargaison.code_labo,
            'nomParametre': param.nomParametre,
            'valeurMin': ap.valeurMin,
            'valeurMax': ap.valeurMax,
            'valeurResultatChar': val_char,
            'valeurResultat': val_num,
            'etatValeur': status
        })

    table = AffichageDetailResultat(data_list, prefix='_1')
    RequestConfig(request, paginate=False).configure(table)

    return render(request, 'laboDetailsResultatDroite.html', {'table': table})


@login_required(login_url='login')
def receptionRapports(request):
    template = 'laboReceptionRapports.html'
    form = FiltresDate()
    context = {'form': form}
    return render(request, template, context)


@login_required(login_url='login')
@require_POST
def receptionRapportsResponse(request):
    user_id = request.user.id
    params = request.POST

    # ---------- Helpers ----------
    def _s(key, default=""):
        return (params.get(key) or default).strip()

    def _i(key, default=0):
        try:
            return int(params.get(key, default))
        except Exception:
            return default

    def _parse_date_range(value: str):
        """
        Expects: 'YYYY-MM-DD - YYYY-MM-DD'
        Returns: (start_date, end_date) as date objects, or (None, None)
        """
        try:
            if not value or " - " not in value:
                return None, None
            a, b = value.split(" - ", 1)
            start = datetime.strptime(a.strip(), "%Y-%m-%d").date()
            end = datetime.strptime(b.strip(), "%Y-%m-%d").date()
            return start, end
        except Exception:
            return None, None

    # ---------- Base scope ----------
    # Leverage denormalized scoping to avoid deep joins in the main QuerySet
    allowed_entrepot_ids = Entrepot.objects.filter(
        ville__affectationville__username_id=user_id
    ).values_list('identrepot', flat=True)

    qs = Cargaison.objects.filter(
        entrepot_id__in=allowed_entrepot_ids,
        date_reception_labo__isnull=False
    )

    # recordsTotal BEFORE filters/search
    records_total = qs.count()

    # ---------- Filters from modal ----------
    date_type = _s("date_type", "reception")  # 'reception' | 'echantillon'
    date_range = _s("date_range")  # 'YYYY-MM-DD - YYYY-MM-DD'
    entrepot = _s("entrepot")
    num_re = _s("num_re")
    immat = _s("immatriculation")
    code_labo_param = _s("code_labo")

    # Date range filter (mandatory on frontend)
    start_date, end_date = _parse_date_range(date_range)
    if start_date and end_date:
        if date_type == "echantillon":
            # Using __date on DateTimeField triggers a join or DB-specific extraction.
            # However, start_date/end_date are date objects, and date_echantillon is a DateTimeField.
            # Using range with date objects on a DateTimeField works efficiently in Django.
            qs = qs.filter(date_echantillon__date__range=(start_date, end_date))
        else:
            qs = qs.filter(date_reception_labo__date__range=(start_date, end_date))

    # Other filters (leveraging denormalized fields)
    if entrepot:
        qs = qs.filter(nom_entrepot__iexact=entrepot)
    if num_re:
        # Check if we have a denormalized num_re? In models.py Entrepot_echantillon has numrappechauto.
        # Cargaison doesn't seem to have numrappechauto denormalized yet, but it HAS it via Entrepot_echantillon (OneToOne).
        # Wait, I should check models.py again.
        qs = qs.filter(entrepot_echantillon__numrappechauto__iexact=num_re)
    if immat:
        qs = qs.filter(immatriculation__iexact=immat)
    if code_labo_param:
        qs = qs.filter(code_labo__iexact=code_labo_param)

    # ---------- Global search (DataTables) ----------
    search_value = _s("search[value]")
    if search_value:
        qs = qs.filter(
            Q(numdos__iexact=search_value) |
            Q(entrepot_echantillon__numrappechauto__iexact=search_value) |
            Q(code_labo__iexact=search_value) |
            Q(nom_entrepot__iexact=search_value) |
            Q(nom_importateur__iexact=search_value) |
            Q(immatriculation__iexact=search_value) |
            Q(nom_produit__iexact=search_value)
        )

    # ---------- Ordering (DataTables) ----------
    order_col = _s("order[0][column]")
    order_dir = _s("order[0][dir]", "desc").lower()

    ordering_map = {
        "0": "numdos",
        "1": "entrepot_echantillon__numrappechauto",
        "2": "code_labo",
        "3": "date_echantillon",
        "4": "date_reception_labo",
        "5": "nom_entrepot",
        "6": "nom_importateur",
        "7": "immatriculation",
        "8": "nom_produit",
    }

    order_field = ordering_map.get(order_col, "date_reception_labo")
    if order_dir == "desc":
        order_field = f"-{order_field}"
    qs = qs.order_by(order_field)

    # ---------- Export (POST) ----------
    export = _s("export")
    if export == "excel":
        rows = qs.values(
            'numdos',
            'entrepot_echantillon__numrappechauto',
            'code_labo',
            'date_echantillon',
            'date_reception_labo',
            'nom_entrepot',
            'nom_importateur',
            'immatriculation',
            'nom_produit',
        )

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Rapports"

        header_row = [
            'NUM.DOSS', 'NUM.RE', 'CODE LABO', 'DATE ECHANT.',
            'DATE RECEP.', 'ENTREPOT', 'FOURNISSEUR',
            'IMMATRICULATION', 'PRODUIT'
        ]
        sheet.append(header_row)

        for r in rows:
            sheet.append([
                r['numdos'],
                r['entrepot_echantillon__numrappechauto'],
                r['code_labo'],
                r['date_echantillon'].date() if r['date_echantillon'] else None,
                r['date_reception_labo'].date() if r['date_reception_labo'] else None,
                r['nom_entrepot'],
                r['nom_importateur'],
                r['immatriculation'],
                r['nom_produit'],
            ])

        excel_stream = io.BytesIO()
        workbook.save(excel_stream)
        excel_stream.seek(0)

        response = HttpResponse(
            excel_stream.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="rapport_reception.xlsx"'
        return response

    # recordsFiltered AFTER filters/search (Moved after export check to avoid double count if exporting)
    records_filtered = qs.count()

    # Apply values BEFORE pagination to avoid AttributeError on sliced QuerySet
    qs = qs.values(
        'numdos',
        'entrepot_echantillon__numrappechauto',
        'code_labo',
        'date_echantillon',
        'date_reception_labo',
        'nom_entrepot',
        'nom_importateur',
        'immatriculation',
        'nom_produit',
    )

    # ---------- Pagination (server-side) ----------
    draw = _i("draw", 1)
    start = max(_i("start", 0), 0)
    length = _i("length", 25)

    if length <= 0:
        return JsonResponse({
            "data": [],
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
        })

    length = min(length, 200)

    # Use LazyPaginator
    paginator = LazyPaginator(qs, length)
    current_page = (start // length) + 1

    try:
        page = paginator.page(current_page)
    except (PageNotAnInteger, EmptyPage):
        page = paginator.page(1)

    # Convert the page object to a list of dictionaries (already dicts because of .values())
    data = list(page.object_list)

    # Rename keys for frontend compatibility
    for r in data:
        r["entrepot_echantillon__laboreception__codelabo"] = r.pop("code_labo", None)

        # Convert DateTime to Date for frontend
        dt_echantillon = r.pop("date_echantillon", None)
        r["entrepot_echantillon__dateechantillonage__date"] = dt_echantillon.date() if dt_echantillon else None

        dt_reception = r.pop("date_reception_labo", None)
        r[
            "entrepot_echantillon__laboreception__datereceptionlabo__date"] = dt_reception.date() if dt_reception else None

        r["entrepot__nomentrepot"] = r.pop("nom_entrepot", None)
        r["importateur__nomimportateur"] = r.pop("nom_importateur", None)
        r["produit__nomproduit"] = r.pop("nom_produit", None)

    return JsonResponse({
        "data": data,
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
    })


# ===================== Async Excel export endpoints for Reception Rapports =====================
@login_required(login_url='login')
@require_POST
def receptionRapportsExportStart(request):
    """Start Celery export task for Reception Rapports. Accepts same POST params as the data endpoint.
    Returns { task_id } for polling.
    """

    # Accept both form and JSON
    def get_payload():
        ct = (request.headers.get("Content-Type") or "").lower()
        if "application/json" in ct:
            try:
                return json.loads(request.body.decode("utf-8") or "{}") or {}
            except Exception:
                return {}
        return request.POST

    params = get_payload()

    # Only pass the filters we support
    filters = {
        "date_type": (params.get("date_type") or "reception").strip(),
        "date_range": (params.get("date_range") or "").strip(),
        "entrepot": (params.get("entrepot") or "").strip(),
        "num_re": (params.get("num_re") or "").strip(),
        "immatriculation": (params.get("immatriculation") or "").strip(),
        "code_labo": (params.get("code_labo") or "").strip(),
        # optional global search
        "search": (params.get("search[value]") or params.get("search") or "").strip(),
    }

    user_id = request.user.id
    async_result = export_reception_rapports_to_xlsx.delay(user_id, filters)
    return JsonResponse({"task_id": async_result.id})


@login_required(login_url='login')
def receptionRapportsExportStatus(request, task_id: str):
    """Poll Celery task state and return progress. When finished, include a time-limited
    pre-signed download URL to the XLSX stored in S3-compatible storage.
    """
    result = AsyncResult(task_id, app=app)
    state = result.state
    meta = result.info or {}
    # Support both legacy "progress" (int) and new {percent, done, total}
    percent = 0
    if isinstance(meta, dict):
        if 'percent' in meta:
            try:
                percent = float(meta.get('percent') or 0)
            except Exception:
                percent = 0
        elif 'progress' in meta:
            try:
                percent = float(meta.get('progress') or 0)
            except Exception:
                percent = 0

    payload = {
        "state": state,
        "progress": percent,
        "ready": result.successful(),
    }
    # Optionally echo done/total if available
    if isinstance(meta, dict):
        if 'done' in meta: payload['done'] = meta.get('done')
        if 'total' in meta: payload['total'] = meta.get('total')
    if result.successful():
        # Prefer storage_key for S3/Spaces
        storage_key = None
        file_url = None
        if isinstance(meta, dict):
            storage_key = meta.get("storage_key") or meta.get("key")
            file_url = meta.get("file_url")
        # Some Celery backends may store the return value separately
        if not storage_key and hasattr(result, 'result') and isinstance(result.result, dict):
            storage_key = result.result.get("storage_key")
            if not file_url:
                file_url = result.result.get("file_url")

        # Try to provide a download URL
        # 1. Use default_storage.url() - it handles prefixes and pre-signing automatically
        if storage_key:
            try:
                payload["download_url"] = default_storage.url(storage_key)
            except Exception as e:
                print(f"default_storage.url failed: {storage_key}, error: {e}")

        # 2. Try manual S3 presigned URL as a fallback or if default_storage.url() didn't work as expected
        if not payload.get("download_url") and storage_key:
            try:
                import boto3
                expires = 24 * 3600
                bucket = getattr(settings, 'SPACE_NAME', getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None))
                region = getattr(settings, 'SPACE_REGION', getattr(settings, 'AWS_S3_REGION_NAME', None))
                endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
                if not endpoint:
                    space_endpoint = getattr(settings, 'SPACE_ENDPOINT', 'digitaloceanspaces.com')
                    if region:
                        endpoint = f"https://{region}.{space_endpoint}"

                access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', getattr(settings, 'SPACE_ACCESS_KEY', None))
                secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', getattr(settings, 'SPACE_SECRET', None))

                if access_key and secret_key and bucket:
                    s3 = boto3.client(
                        's3',
                        endpoint_url=endpoint,
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key,
                        region_name=region,
                    )

                    # Robust key handling for manual S3 presigning
                    full_key = storage_key
                    # Prepend 'media/' if using MediaRootS3BotoStorage and it's missing
                    if not full_key.startswith("media/") and getattr(settings, 'DEFAULT_FILE_STORAGE', '').endswith(
                            'MediaRootS3BotoStorage'):
                        full_key = f"media/{full_key}"

                    url = s3.generate_presigned_url(
                        ClientMethod='get_object',
                        Params={'Bucket': bucket, 'Key': full_key},
                        ExpiresIn=expires,
                    )
                    payload["download_url"] = url
            except Exception as e:
                # Log but don't fail, we have other options
                print(f"S3 presign failed: {e}")

        # 2. Use file_url from task result if no download_url yet
        if not payload.get("download_url") and file_url:
            payload["download_url"] = file_url

        # 3. Last resort: legacy fallback to local /tmp path served by Django
        if not payload.get("download_url"):
            download_url = request.build_absolute_uri(
                reverse('receptionRapportsExportDownload', kwargs={"task_id": task_id})
            )
            payload["download_url"] = download_url
    elif result.failed():
        payload["error"] = str(meta.get("error", "Export failed")) if isinstance(meta, dict) else "Export failed"
    return JsonResponse(payload)


@login_required(login_url='login')
def receptionRapportsExportDownload(request, task_id: str):
    """Serve the generated XLSX for a completed export task if owned by the current user."""
    user_id = request.user.id
    # Our task saves file to system temp dir with pattern rapport_reception_{user_id}_{task_id}.xlsx
    fname = f"rapport_reception_{user_id}_{task_id}.xlsx"
    fpath = os.path.join(tempfile.gettempdir(), fname)
    if not os.path.exists(fpath):
        return JsonResponse({"error": "File not found or not ready yet"}, status=404)

    with open(fpath, 'rb') as fh:
        data = fh.read()
    resp = HttpResponse(data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="rapport_reception.xlsx"'
    return resp


@login_required(login_url='login')
def receptionRapportsGenerate(request):
    template = 'laboReceptionRapportsFiltres.html'
    # Get the search value from the request's GET parameters
    if request.method == 'POST':
        date_d = request.POST['date_d']
        date_f = request.POST['date_f']

        request.session['date_d'] = date_d
        request.session['date_f'] = date_f

        form = FiltresDate()
        context = {'form': form}
        return render(request, template, context)
    else:
        return redirect('receptionRapports')


@login_required(login_url='login')
def receptionRapportsResponseFiltres(request):
    user = request.user.id
    ville = AffectationVille.objects.filter(username_id=user).values_list('ville_id', flat=True)
    qs = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user,
    ).values(
        'numdos',
        'entrepot_echantillon__numrappechauto',
        'code_labo',
        'date_echantillon__date',
        'date_reception_labo__date',
        'nom_entrepot',
        'nom_importateur',
        'immatriculation',
        'nom_produit',
    ).order_by('-dateheurecargaison')

    date_d = request.session['date_d']
    date_f = request.session['date_f']

    # Apply search filter to the QuerySet
    if date_d and date_f:
        qs = qs.filter(
            date_reception_labo__date__range=(date_d, date_f)
        )

    if date_d:
        qs = qs.filter(
            date_reception_labo__date=(date_d)
        )
        print(date_d)

    if date_f:
        qs = qs.filter(
            date_reception_labo__date=(date_f)
        )

    # Number of items to show per page
    items_per_page = 10

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

    export = request.GET.get('export', None)
    if export == 'excel':
        # Retrieve all data (no lazy pagination) and store it in a list
        data = list(qs)

        # Create a new Excel workbook
        workbook = Workbook()
        sheet = workbook.active

        # Write headers to the Excel file
        header_row = ['NUM.DOSS', 'NUM.RE', 'CODE LABO', 'DATE ECHANT.', 'DATE RECEP.', 'ENTREPOT',
                      'FOURNISSEUR',
                      'IMMATRICULATION', 'PRODUIT']

        # Combine header and data rows using zip
        all_rows = [header_row] + [
            [
                row['numdos'],
                row['entrepot_echantillon__numrappechauto'],
                row['code_labo'],
                row['date_echantillon__date'],
                row['date_reception_labo__date'],
                row['nom_entrepot'],
                row['nom_importateur'],
                row['immatriculation'],
                row['nom_produit'],
            ] for row in data
        ]

        # Write data rows to the Excel file
        for row in all_rows:
            sheet.append(row)

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


### Ajax Handlers
@login_required(login_url='login')
@require_POST
def refaireAjx(request):
    user = request.user
    role = user.role_id
    if role in (1, 6, 10):
        idcargaison = request.POST.get('idcargaison')
        if not idcargaison:
            return JsonResponse({'status': 'failure', 'message': 'Missing idcargaison'}, status=400)

        try:
            # Efficient update
            updated = Cargaison.objects.filter(idcargaison=idcargaison).update(etat="Refaire")
            
            if updated:
                UserActivityLog.objects.create(
                    user=user,
                    action="Validation: Request Re-analysis",
                    object_id=str(idcargaison),
                    description=f"Cargaison {idcargaison}: User requested re-analysis.",
                )
                return JsonResponse({'status': 'success', 'message': 'Cargaison marked as REFAIRE'})
            else:
                return JsonResponse({'status': 'failure', 'message': 'Cargaison not found'}, status=404)
        except Cargaison.DoesNotExist:
            return JsonResponse({'status': 'failure', 'message': 'Cargaison not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'failure', 'message': 'Unauthorized'}, status=403)


# Validation du responsable Division LABO OCC
@login_required(login_url='login')
@require_POST
def conformeAjx(request):
    user = request.user
    role = user.role_id

    if role in (1, 6):
        idcargaison = request.POST.get('idcargaison')
        if not idcargaison:
            return JsonResponse({'status': 'failure', 'message': 'Missing idcargaison'}, status=400)

        try:
            # Efficient update
            updated = Cargaison.objects.filter(idcargaison=idcargaison).update(
                etat="Validation en cours 2",
                conformite="Conforme aux exigences",
                impression="0"
            )
            
            if updated:
                UserActivityLog.objects.create(
                    user=user,
                    action="Validation 1: CONFORME",
                    object_id=str(idcargaison),
                    description=f"Cargaison {idcargaison}: First validation set to CONFORME.",
                )
                return JsonResponse({'status': 'success', 'message': 'Cargaison marked as CONFORME'})
            else:
                return JsonResponse({'status': 'failure', 'message': 'Cargaison not found'}, status=404)

        except Cargaison.DoesNotExist:
            return JsonResponse({'status': 'failure', 'message': 'Cargaison not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'failure', 'message': 'Unauthorized'}, status=403)


@login_required(login_url='login')
@require_POST
def nonconformeAjx(request):
    user = request.user
    role = user.role_id
    if role in (1, 6):
        idcargaison = request.POST.get('idcargaison')
        if not idcargaison:
            return JsonResponse({'status': 'failure', 'message': 'Missing idcargaison'}, status=400)

        try:
            # Efficient update
            updated = Cargaison.objects.filter(idcargaison=idcargaison).update(
                etat="Validation en cours 2",
                conformite="Non conforme aux exigences",
                impression="0"
            )
            
            if updated:
                UserActivityLog.objects.create(
                    user=user,
                    action="Validation 1: NON CONFORME",
                    object_id=str(idcargaison),
                    description=f"Cargaison {idcargaison}: First validation set to NON CONFORME.",
                )
                return JsonResponse({'status': 'success', 'message': 'Cargaison marked as NON CONFORME'})
            else:
                return JsonResponse({'status': 'failure', 'message': 'Cargaison not found'}, status=404)

        except Cargaison.DoesNotExist:
            return JsonResponse({'status': 'failure', 'message': 'Cargaison not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'failure', 'message': 'Unauthorized'}, status=403)


@login_required(login_url='login')
@require_POST
def affichagetableauvalidation1Response(request):
    user = request.user
    id = user.id
    role = user.role_id
    if role in (5, 1, 6):
        def get_payload():
            ct = (request.headers.get("Content-Type") or "").lower()
            if "application/json" in ct:
                try:
                    return json.loads(request.body.decode("utf-8") or "{}") or {}
                except Exception:
                    return {}
            return request.POST

        params = get_payload()

        # 1. Optimize allowed Entrepots (Denormalized scoping)
        allowed_entrepot_ids = Entrepot.objects.filter(
            ville__affectationville__username_id=id
        ).values_list('identrepot', flat=True)

        # 2. Base QuerySet
        qs = Cargaison.objects.filter(
            etat="Validation en cours 1",
            entrepot_id__in=allowed_entrepot_ids,
        )

        # recordsTotal for DataTables
        recordsTotal = qs.count()

        # 3. Global search (leveraging denormalized fields and index-friendly queries)
        search_value = params.get('search', {}).get('value') if isinstance(params.get('search'), dict) else params.get('search[value]')
        search_value = search_value or params.get('q')
        
        if search_value:
            search_q = Q(nom_importateur__icontains=search_value) | \
                       Q(nom_entrepot__icontains=search_value) | \
                       Q(nom_produit__icontains=search_value) | \
                       Q(immatriculation__icontains=search_value)
            
            if search_value.isdigit():
                val = int(search_value)
                search_q |= Q(code_labo=val) | Q(num_certificat_qualite=val)
                
            qs = qs.filter(search_q)

        # recordsFiltered for DataTables
        recordsFiltered = qs.count()

        # 4. Final projection and ordering
        qs = qs.values(
            'idcargaison',
            'date_reception_labo',
            'nom_importateur',
            'nom_entrepot',
            'code_labo',
            'num_certificat_qualite',
            'nom_produit'
        ).order_by('-date_reception_labo')

        # 5. Pagination
        draw = int(params.get('draw', 1))
        start = int(params.get('start', 0))
        length = int(params.get('length', 10))

        if length <= 0:
            return JsonResponse({
                'data': [],
                'draw': draw,
                'recordsTotal': recordsTotal,
                'recordsFiltered': recordsFiltered,
            })

        # Paging using direct slice for performance
        data = list(qs[start:start+length])

        # 6. Key mapping for frontend compatibility
        for r in data:
            dt = r.pop("date_reception_labo", None)
            r["entrepot_echantillon__laboreception__datereceptionlabo__date"] = dt.date() if dt and hasattr(dt, 'date') else dt
            
            r["importateur__nomimportateur"] = r.pop("nom_importateur", None)
            r["entrepot__nomentrepot"] = r.pop("nom_entrepot", None)
            r["entrepot_echantillon__laboreception__codelabo"] = r.pop("code_labo", None)
            r["entrepot_echantillon__laboreception__numcertificatqualite"] = r.pop("num_certificat_qualite", None)
            r["produit__nomproduit"] = r.pop("nom_produit", None)

        return JsonResponse({
            'data': data,
            'draw': draw,
            'recordsTotal': recordsTotal,
            'recordsFiltered': recordsFiltered,
        })
    else:
        return redirect('logout')


@login_required(login_url='login')
@require_POST
def affichagetableauvalidation2Response(request):
    user = request.user
    id = user.id
    role = user.role_id
    if role in (5, 1, 6, 10):
        def get_payload():
            ct = (request.headers.get("Content-Type") or "").lower()
            if "application/json" in ct:
                try:
                    return json.loads(request.body.decode("utf-8") or "{}") or {}
                except Exception:
                    return {}
            return request.POST

        params = get_payload()

        # 1. Optimize allowed Entrepots (Denormalized scoping)
        allowed_entrepot_ids = Entrepot.objects.filter(
            ville__affectationville__username_id=id
        ).values_list('identrepot', flat=True)

        # 2. Base QuerySet
        qs = Cargaison.objects.filter(
            etat="Validation en cours 2",
            entrepot_id__in=allowed_entrepot_ids,
        )

        # recordsTotal for DataTables
        recordsTotal = qs.count()

        # 3. Global search (leveraging denormalized fields and index-friendly queries)
        search_value = params.get('search', {}).get('value') if isinstance(params.get('search'), dict) else params.get('search[value]')
        search_value = search_value or params.get('q')
        
        if search_value:
            search_q = Q(nom_importateur__icontains=search_value) | \
                       Q(nom_entrepot__icontains=search_value) | \
                       Q(nom_produit__icontains=search_value) | \
                       Q(immatriculation__icontains=search_value)
            
            if search_value.isdigit():
                val = int(search_value)
                search_q |= Q(code_labo=val) | Q(num_certificat_qualite=val)
                
            qs = qs.filter(search_q)

        # recordsFiltered for DataTables
        recordsFiltered = qs.count()

        # 4. Final projection and ordering
        qs = qs.values(
            'idcargaison',
            'date_reception_labo',
            'nom_importateur',
            'nom_entrepot',
            'code_labo',
            'num_certificat_qualite',
            'nom_produit'
        ).order_by('-date_reception_labo')

        # 5. Pagination
        draw = int(params.get('draw', 1))
        start = int(params.get('start', 0))
        length = int(params.get('length', 10))

        if length <= 0:
            return JsonResponse({
                'data': [],
                'draw': draw,
                'recordsTotal': recordsTotal,
                'recordsFiltered': recordsFiltered,
            })

        # Paging using direct slice for performance
        data = list(qs[start:start+length])

        # 6. Key mapping for frontend compatibility
        for r in data:
            dt = r.pop("date_reception_labo", None)
            r["entrepot_echantillon__laboreception__datereceptionlabo__date"] = dt.date() if dt and hasattr(dt, 'date') else dt
            
            r["importateur__nomimportateur"] = r.pop("nom_importateur", None)
            r["entrepot__nomentrepot"] = r.pop("nom_entrepot", None)
            r["entrepot_echantillon__laboreception__codelabo"] = r.pop("code_labo", None)
            r["entrepot_echantillon__laboreception__numcertificatqualite"] = r.pop("num_certificat_qualite", None)
            r["produit__nomproduit"] = r.pop("nom_produit", None)

        return JsonResponse({
            'data': data,
            'draw': draw,
            'recordsTotal': recordsTotal,
            'recordsFiltered': recordsFiltered,
        })
    else:
        return redirect('logout')


@login_required(login_url='login')
@require_POST
def conformeAjx2(request):
    user = request.user
    role = user.role_id

    if role in (1, 10):
        idcargaison = request.POST.get('idcargaison')
        if not idcargaison:
            return JsonResponse({'status': 'failure', 'message': 'Missing idcargaison'}, status=400)

        try:
            with transaction.atomic():
                c = Cargaison.objects.select_for_update().get(idcargaison=idcargaison)

                # Check if ImpressionResultat exists for the Cargaison
                if not ImpressionResultat.objects.filter(idcargaison=c).exists():
                    now = timezone.now()
                    ImpressionResultat.objects.create(
                        printDate=now.date(),
                        isConforme=True,
                        isPrinted=False,
                        idcargaison=c
                    )

                    c.etat = "Conforme aux exigences"
                    c.conformite = "Conforme aux exigences"
                    c.impression = "0"
                    c.dateHeureAnalyseLabo = now
                    c.save(update_fields=['etat', 'impression', 'conformite', 'dateHeureAnalyseLabo'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Validation 2: CONFORME",
                        description=f"Cargaison {c.idcargaison}: Final validation set to CONFORME.",
                    )

                    return JsonResponse({'status': 'success', 'message': 'Cargaison marked as CONFORME'})

                return JsonResponse({'status': 'failure', 'message': 'Impression result already exists'}, status=400)
        except Cargaison.DoesNotExist:
            return JsonResponse({'status': 'failure', 'message': 'Cargaison not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'failure', 'message': 'Unauthorized'}, status=403)


@login_required(login_url='login')
@require_POST
def nonconformeAjx2(request):
    user = request.user
    role = user.role_id
    if role in (1, 10):
        idcargaison = request.POST.get('idcargaison')
        if not idcargaison:
            return JsonResponse({'status': 'failure', 'message': 'Missing idcargaison'}, status=400)

        try:
            with transaction.atomic():
                c = Cargaison.objects.select_for_update().get(idcargaison=idcargaison)

                if not ImpressionResultat.objects.filter(idcargaison=c).exists():
                    now = timezone.now()
                    ImpressionResultat.objects.create(
                        printDate=now.date(),
                        isConforme=False,
                        isPrinted=False,
                        idcargaison=c
                    )

                    c.etat = "Non conforme aux exigences"
                    c.conformite = "Non conforme aux exigences"
                    c.impression = "0"
                    c.dateHeureAnalyseLabo = now
                    c.save(update_fields=['etat', 'impression', 'conformite', 'dateHeureAnalyseLabo'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Validation 2: NON CONFORME",
                        description=f"Cargaison {c.idcargaison}: Final validation set to NON CONFORME.",
                    )

                    return JsonResponse({'status': 'success', 'message': 'Cargaison marked as NON CONFORME'})

                return JsonResponse({'status': 'failure', 'message': 'Impression result already exists'}, status=400)
        except Cargaison.DoesNotExist:
            return JsonResponse({'status': 'failure', 'message': 'Cargaison not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'failure', 'message': 'Unauthorized'}, status=403)


# Fonction pour affichage tableu impression des certificats
@login_required(login_url='login')
@require_POST
def responseAffichagetableauimpression(request):
    user = request.user
    role = user.role_id

    if role not in (1, 5):
        return JsonResponse({"error": "Forbidden"}, status=403)

    # Payload reading
    def get_payload():
        ct = (request.headers.get("Content-Type") or "").lower()
        if "application/json" in ct:
            try:
                return json.loads(request.body.decode("utf-8") or "{}") or {}
            except Exception:
                return {}
        return request.POST

    params = get_payload()

    # 1. Optimize allowed Entrepots (Denormalized scoping)
    allowed_entrepot_ids = Entrepot.objects.filter(
        ville__affectationville__username_id=user.id
    ).values_list('identrepot', flat=True)

    # 2. Base QuerySet with mandatory filters
    qs = Cargaison.objects.filter(
        entrepot_id__in=allowed_entrepot_ids,
        etat="Conforme aux exigences"
    )

    # recordsTotal for DataTables (count before optional filters)
    recordsTotal = qs.count()

    # 3. Optional Filters from toolbar
    date_start = params.get('date_start')
    date_end = params.get('date_end')
    printed_status = params.get('printed_status', 'not_printed')

    if date_start:
        qs = qs.filter(date_reception_labo__gte=date_start)
    if date_end:
        qs = qs.filter(date_reception_labo__date__lte=date_end)

    # Printed status subquery - we only care about records where isPrinted is True
    print_records = ImpressionResultat.objects.filter(
        idcargaison=OuterRef('pk'), 
        isPrinted=True
    ).order_by('-idImpression')

    if printed_status == 'not_printed':
        qs = qs.filter(~Exists(print_records))
    elif printed_status == 'printed':
        qs = qs.filter(Exists(print_records))

    # 4. Global search (leveraging denormalized fields and indexes)
    search_value = params.get('search', {}).get('value') if isinstance(params.get('search'), dict) else params.get('search[value]')
    search_value = search_value or params.get('q')
    if search_value:
        search_q = Q(code_labo__icontains=search_value) | \
                   Q(num_certificat_qualite__icontains=search_value) | \
                   Q(nom_importateur__icontains=search_value) | \
                   Q(nom_entrepot__icontains=search_value) | \
                   Q(nom_produit__icontains=search_value) | \
                   Q(immatriculation__icontains=search_value)
        
        if search_value.isdigit():
            val = int(search_value)
            search_q |= Q(code_labo=val) | Q(num_certificat_qualite=val)
            
        qs = qs.filter(search_q)

    # recordsFiltered for DataTables
    recordsFiltered = qs.count()

    # 5. Final projection and pagination
    qs = qs.values(
        'idcargaison',
        'date_reception_labo',
        'num_certificat_qualite',
        'code_labo',
        'nom_produit',
        'nom_importateur',
        'nom_entrepot',
        'immatriculation'
    ).order_by('date_reception_labo')

    draw = int(params.get('draw', 1))
    start = int(params.get('start', 0))
    length = int(params.get('length', 10))

    if length <= 0:
        return JsonResponse({
            'data': [],
            'draw': draw,
            'recordsTotal': recordsTotal,
            'recordsFiltered': recordsFiltered,
        })

    # Paging using direct slice for performance
    data = list(qs[start:start+length])

    # 6. Formatting result for legacy compatibility
    for r in data:
        dt = r.pop("date_reception_labo", None)
        r["dateReceptionLabo"] = dt.date() if dt and hasattr(dt, 'date') else dt
        
        r["codelabo"] = r.pop("code_labo", None)
        r["numcertificatqualite"] = r.pop("num_certificat_qualite", None)
        r["nomproduit"] = r.pop("nom_produit", None)
        r["nomimportateur"] = r.pop("nom_importateur", None)
        r["nomentrepot"] = r.pop("nom_entrepot", None)
        r["immatriculation"] = r.pop("immatriculation", None)

    return JsonResponse({
        'data': data,
        'draw': draw,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
    })



@login_required(login_url='login')
@require_POST
def responseArchivesTableau(request):
    user = request.user
    role = user.role_id

    if role not in (1, 5):
        return JsonResponse({"error": "Forbidden"}, status=403)

    def get_payload():
        ct = (request.headers.get("Content-Type") or "").lower()
        if "application/json" in ct:
            try:
                return json.loads(request.body.decode("utf-8") or "{}") or {}
            except Exception:
                return {}
        return request.POST

    params = get_payload()

    # 1. Optimize Scoping (Consistent with main printing table)
    allowed_entrepot_ids = Entrepot.objects.filter(
        ville__affectationville__username_id=user.id
    ).values_list('identrepot', flat=True)

    # 2. Base QuerySet: Only certificates that have been printed
    # Optimization: Use Exists on a restricted ImpressionResultat queryset
    print_records = ImpressionResultat.objects.filter(
        idcargaison=OuterRef('pk'), 
        isPrinted=True
    ).order_by('-idImpression')

    qs = Cargaison.objects.filter(
        entrepot_id__in=allowed_entrepot_ids
    ).annotate(has_been_printed=Exists(print_records)).filter(has_been_printed=True)

    # recordsTotal for DataTables (within user's scope)
    recordsTotal = qs.count()

    # 3. Apply Filters
    code_labo = params.get('code_labo')
    num_certificat = params.get('num_certificat')
    date_start = params.get('date_start')
    date_end = params.get('date_end')

    if code_labo:
        qs = qs.filter(code_labo=code_labo)
    if num_certificat:
        qs = qs.filter(num_certificat_qualite=num_certificat)

    # Subquery for the latest print date (needed for range filtering and ordering)
    latest_print_date = print_records.values('printDate')[:1]
    qs = qs.annotate(print_date_val=Subquery(latest_print_date))

    if date_start:
        qs = qs.filter(print_date_val__gte=date_start)
    if date_end:
        qs = qs.filter(print_date_val__lte=date_end)

    # Global search (leveraging denormalized fields and index-friendly queries)
    search_value = params.get('search', {}).get('value') if isinstance(params.get('search'), dict) else params.get('search[value]')
    search_value = search_value or params.get('q')
    if search_value:
        search_q = Q(nom_importateur__icontains=search_value) | \
                   Q(nom_entrepot__icontains=search_value) | \
                   Q(nom_produit__icontains=search_value) | \
                   Q(immatriculation__icontains=search_value)
        
        # Numeric fields optimized
        if search_value.isdigit():
            val = int(search_value)
            search_q |= Q(code_labo=val) | Q(num_certificat_qualite=val)
        else:
            search_q |= Q(nom_frontiere__icontains=search_value)

        qs = qs.filter(search_q)

    # recordsFiltered after all filters applied
    recordsFiltered = qs.count()

    # 4. Final selection and Ordering
    qs = qs.values(
        'idcargaison',
        'date_reception_labo',
        'print_date_val',
        'num_certificat_qualite',
        'code_labo',
        'nom_produit',
        'nom_importateur',
        'nom_entrepot',
        'immatriculation'
    ).order_by('-print_date_val')

    # 5. Pagination (Direct slicing for performance)
    draw = int(params.get('draw', 1))
    start = int(params.get('start', 0))
    length = int(params.get('length', 10))

    if length > 0:
        data = list(qs[start:start+length])
    else:
        data = []

    # 6. Legacy Key Mapping and Formatting
    for r in data:
        dt_reception = r.pop("date_reception_labo", None)
        r["dateReceptionLabo"] = dt_reception.date() if dt_reception and hasattr(dt_reception, 'date') else dt_reception
        
        pdate = r.pop("print_date_val", None)
        r["impressionresultat__printDate"] = pdate.strftime('%Y-%m-%d') if pdate and hasattr(pdate, 'strftime') else (pdate or "—")

        r["codelabo"] = r.pop("code_labo", None)
        r["numcertificatqualite"] = r.pop("num_certificat_qualite", None)
        r["nomproduit"] = r.pop("nom_produit", None)
        r["nomimportateur"] = r.pop("nom_importateur", None)
        r["nomentrepot"] = r.pop("nom_entrepot", None)
        r["immatriculation"] = r.pop("immatriculation", None)

    return JsonResponse({
        'data': data,
        'draw': draw,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
    })



@login_required(login_url='login')
def responseImpressionReport(request):
    user = request.user
    role = user.role_id
    if role not in (1, 5):
        return JsonResponse({"error": "Forbidden"}, status=403)

    # Scoping
    allowed_entrepot_ids = Entrepot.objects.filter(
        ville__affectationville__username_id=user.id
    ).values_list('identrepot', flat=True)

    # Base query for printed certificates
    qs = ImpressionResultat.objects.filter(
        idcargaison__entrepot_id__in=allowed_entrepot_ids,
        isPrinted=True
    ).select_related('idcargaison', 'idcargaison__importateur', 'idcargaison__entrepot', 'idcargaison__produit')

    # Apply filters
    date_start = request.GET.get('date_start')
    date_end = request.GET.get('date_end')
    importateur_id = request.GET.get('importateur')
    entrepot_id = request.GET.get('entrepot')
    export_format = request.GET.get('format', 'pdf')

    if date_start:
        qs = qs.filter(printDate__gte=date_start)
    if date_end:
        qs = qs.filter(printDate__lte=date_end)
    if importateur_id:
        qs = qs.filter(idcargaison__importateur_id=importateur_id)
    if entrepot_id:
        qs = qs.filter(idcargaison__entrepot_id=entrepot_id)

    # Order by date
    qs = qs.order_by('-printDate', '-idImpression')

    # Prepare data for report
    data_list = []
    cargaison_ids = [obj.idcargaison_id for obj in qs]
    
    # Batch fetch logs
    logs = UserActivityLog.objects.filter(
        action="Certificat Imprimé",
        object_id__in=[str(cid) for cid in cargaison_ids]
    ).select_related('user').order_by('timestamp')
    
    from collections import defaultdict
    logs_by_cid = defaultdict(list)
    for log in logs:
        logs_by_cid[log.object_id].append(log)

    for imp in qs:
        cid_str = str(imp.idcargaison_id)
        cid_logs = logs_by_cid.get(cid_str, [])
        num_prints = len(cid_logs)
        
        if cid_logs:
            last_log = cid_logs[-1]
            print_time = last_log.timestamp
            printed_by = last_log.user.get_full_name() if last_log.user else "N/A"
        else:
            # Fallback for historical data
            # print_time is a DateField (date object), we convert to datetime to avoid 
            # template errors with time format specifiers (like 'H')
            print_time = datetime.combine(imp.printDate, time.min) if imp.printDate else None
            printed_by = "N/A"
            num_prints = 1

        data_list.append({
            'reference': imp.idcargaison.num_certificat_qualite or imp.idcargaison.code_labo,
            'type': imp.idcargaison.nom_produit,
            'beneficiary': imp.idcargaison.nom_importateur,
            'fournisseur': imp.idcargaison.nom_importateur,
            'entrepot': imp.idcargaison.nom_entrepot,
            'print_time': print_time,
            'printed_by': printed_by,
            'status': "Réimprimé" if num_prints > 1 else "Imprimé",
            'num_prints': num_prints
        })

    if export_format == 'xlsx':
        wb = Workbook()
        ws = wb.active
        ws.title = "Certificats Imprimés"
        headers = ["Référence", "Type", "Bénéficiaire", "Fournisseur", "Entrepôt", "Date/Heure Impression", "Imprimé par", "Statut", "Nbr Impressions"]
        ws.append(headers)
        for row in data_list:
            ws.append([
                row['reference'],
                row['type'],
                row['beneficiary'],
                row['fournisseur'],
                row['entrepot'],
                row['print_time'].strftime('%Y-%m-%d %H:%M') if (row['print_time'] and hasattr(row['print_time'], 'strftime')) else "—",
                row['printed_by'],
                row['status'],
                row['num_prints']
            ])
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="rapport_impressions.xlsx"'
        wb.save(response)
        return response

    else:
        context = {
            'data': data_list,
            'date_start': date_start,
            'date_end': date_end,
            'generated_at': timezone.now(),
            'user': user
        }
        return render_to_pdf('report/impression_report.html', context)



# Fonction pour impression Certificat
@login_required(login_url='login')
def impressioncertificat(request):
    user = request.user
    role = user.role_id

    # Optimization: Use select_related to get ville and province in one query
    try:
        aff_ville = AffectationVille.objects.select_related('ville').get(username_id=user.id)
        ville_id = aff_ville.ville_id
        province = (aff_ville.ville.province or "").upper()
    except (AffectationVille.DoesNotExist, AttributeError):
        return redirect('logout')

    # Optimization: Fetch signers and lab data in one pass
    signGauche = None
    signDroite = None
    laboratoireData = None

    affects = AffectationLaboratoire.objects.filter(ville_id=ville_id).select_related('userId', 'idLaboratoire')
    for aff in affects:
        if aff.signGauche:
            signGauche = aff.userId
        else:
            signDroite = aff.userId
            laboratoireData = aff.idLaboratoire

    if not signGauche or not signDroite or not laboratoireData:
        # Handle missing configuration if necessary
        pass

    # Recuperation des donnees liees a l'Impression
    if request.method == 'POST':
        dataJson = json.loads(request.body)
        pk = dataJson.get('idcargaison')
        
        try:
            # Use select_related and leverage denormalized fields
            cargaison = Cargaison.objects.select_related(
                'entrepot_echantillon', 
                'entrepot_echantillon__laboreception'
            ).get(idcargaison=pk)
        except Cargaison.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Cargaison not found'})

        impressionData = ImpressionResultat.objects.filter(idcargaison_id=pk).first()

        # Extract month/year from denormalized date or related object
        labo_rec = cargaison.entrepot_echantillon.laboreception
        mois = labo_rec.datereceptionlabo.month if labo_rec and labo_rec.datereceptionlabo else None
        annee = labo_rec.datereceptionlabo.year if labo_rec and labo_rec.datereceptionlabo else None

        if role == 5 or role == 1:
            # Denormalized fields
            produit = cargaison.nom_produit
            echantillon = cargaison.entrepot_echantillon
            laboratoire = labo_rec

            # Optimization: Fetch all analysis results in one query
            results = ResultatAnalyse.objects.filter(idcargaison=pk).values('idParametre_id', 'valeurResultat', 'valeurResultatChar')
            res_dict = {r['idParametre_id']: r for r in results}

            # Test pour afficher les differents rapports
            template = ""
            data = {
                'laboratoire': laboratoire,
                'cargaison': cargaison,
                'echantillon': echantillon,
                'annee': annee,
                'mois': mois,
                'province': province,
                'signGauche': signGauche,
                'signDroite': signDroite,
                'impressionData': impressionData,
                'laboratoireData': laboratoireData,
            }

            if produit == 'GASOIL':
                template = 'report/Report1/gasoilreport.html'

                # Resultat Gasoil Fetching data from the dictionary
                data.update({
                    'couleurastm': res_dict.get(8, {}).get('valeurResultatChar', ''),
                    'aciditetotal': res_dict.get(1, {}).get('valeurResultat', ''),
                    'soufre': res_dict.get(34, {}).get('valeurResultat', ''),
                    'massevolumique': res_dict.get(21, {}).get('valeurResultat', ''),
                    'massevolumique15': res_dict.get(20, {}).get('valeurResultat', ''),
                    'distillation': res_dict.get(100, {}).get('valeurResultat', ''),
                    'distillation10': res_dict.get(11, {}).get('valeurResultat', ''),
                    'distillation20': res_dict.get(12, {}).get('valeurResultat', ''),
                    'distillation50': res_dict.get(13, {}).get('valeurResultat', ''),
                    'distillation90': res_dict.get(15, {}).get('valeurResultat', ''),
                    'pointinitial': res_dict.get(30, {}).get('valeurResultat', ''),
                    'pointfinal': res_dict.get(29, {}).get('valeurResultat', ''),
                    'pointeclair': res_dict.get(25, {}).get('valeurResultat', ''),
                    'viscosite': res_dict.get(38, {}).get('valeurResultat', ''),
                    'pointecoulement': res_dict.get(26, {}).get('valeurResultat', ''),
                    'teneureau': res_dict.get(35, {}).get('valeurResultat', ''),
                    'sediment': res_dict.get(32, {}).get('valeurResultat', ''),
                    'indicecetane': res_dict.get(19, {}).get('valeurResultat', ''),
                    'recuperation362': res_dict.get(10, {}).get('valeurResultat', ''),
                    'cendre': res_dict.get(3, {}).get('valeurResultat', ''),
                })
                
                try:
                    corrosion_str = res_dict.get(6, {}).get('valeurResultat', '')
                    data['corrosion'] = int(corrosion_str) if corrosion_str != '' else ''
                except (ValueError, TypeError):
                    data['corrosion'] = ''

            elif produit == 'MOGAS':
                template = 'report/Report1/mogasreport.html'
                # Resultat MOGAS Fetching data from the dictionary
                data.update({
                    'aspect': res_dict.get(2, {}).get('valeurResultatChar', ''),
                    'odeur': res_dict.get(22, {}).get('valeurResultatChar', ''),
                    'couleursaybolt': res_dict.get(8, {}).get('valeurResultatChar', ''),
                    'soufre': res_dict.get(34, {}).get('valeurResultat', ''),
                    'distillation': res_dict.get(100, {}).get('valeurResultat', ''),
                    'pointfinal': res_dict.get(29, {}).get('valeurResultat', ''),
                    'residu': res_dict.get(31, {}).get('valeurResultat', ''),
                    'pourcent10': res_dict.get(11, {}).get('valeurResultat', ''),
                    'pourcent20': res_dict.get(12, {}).get('valeurResultat', ''),
                    'pourcent50': res_dict.get(13, {}).get('valeurResultat', ''),
                    'pourcent70': res_dict.get(14, {}).get('valeurResultat', ''),
                    'pourcent90': res_dict.get(15, {}).get('valeurResultat', ''),
                    'tensionvapeur': res_dict.get(36, {}).get('valeurResultat', ''),
                    'difftemperature': res_dict.get(9, {}).get('valeurResultat', ''),
                    'plomb': res_dict.get(24, {}).get('valeurResultat', ''),
                    'indiceoctane': res_dict.get(18, {}).get('valeurResultat', ''),
                    'massevolumique15': res_dict.get(20, {}).get('valeurResultat', ''),
                })
                
                try:
                    corrosion_str = res_dict.get(7, {}).get('valeurResultat', '')
                    data['corrosion'] = int(corrosion_str) if corrosion_str != '' else ''
                except (ValueError, TypeError):
                    data['corrosion'] = ''

            elif produit == 'JET A1':
                template = 'report/Report1/jeta1report.html'

                # Resultat JET A1 Fetching data from the dictionary
                data.update({
                    'aspect': res_dict.get(2, {}).get('valeurResultatChar', ''),
                    'couleursaybolt': res_dict.get(8, {}).get('valeurResultatChar', ''),
                    'aciditetotal': res_dict.get(1, {}).get('valeurResultat', ''),
                    'soufre': res_dict.get(34, {}).get('valeurResultat', ''),
                    'soufremercaptan': res_dict.get(33, {}).get('valeurResultat', ''),
                    'docteurtest': res_dict.get(16, {}).get('valeurResultat', ''),
                    'distillation': res_dict.get(100, {}).get('valeurResultat', ''),
                    'pointinitial': res_dict.get(30, {}).get('valeurResultat', ''),
                    'pointfinal': res_dict.get(29, {}).get('valeurResultat', ''),
                    'pointfumee': res_dict.get(28, {}).get('valeurResultat', ''),
                    'pointeclair': res_dict.get(25, {}).get('valeurResultat', ''),
                    'freezingpoint': res_dict.get(17, {}).get('valeurResultat', ''),
                    'residu': res_dict.get(31, {}).get('valeurResultat', ''),
                    'perte': res_dict.get(23, {}).get('valeurResultat', ''),
                    'massevolumique15': res_dict.get(20, {}).get('valeurResultat', ''),
                    'viscosite': res_dict.get(37, {}).get('valeurResultat', ''),
                    'pointinflammabilite': res_dict.get(27, {}).get('valeurResultat', ''),
                    'teneureau': res_dict.get(35, {}).get('valeurResultat', ''),
                    'conductivite': res_dict.get(4, {}).get('valeurResultat', ''),
                    'vol10': res_dict.get(11, {}).get('valeurResultat', ''),
                    'vol20': res_dict.get(12, {}).get('valeurResultat', ''),
                    'vol30': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol40': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol50': res_dict.get(13, {}).get('valeurResultat', ''),
                    'vol60': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol70': res_dict.get(14, {}).get('valeurResultat', ''),
                    'vol80': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol90': res_dict.get(15, {}).get('valeurResultat', ''),
                })
                
                try:
                    corrosion_str = res_dict.get(5, {}).get('valeurResultat', '')
                    data['corrosion'] = int(corrosion_str) if corrosion_str != '' else ''
                except (ValueError, TypeError):
                    data['corrosion'] = ''

            elif produit == 'PETROLE LAMPANT':
                template = 'report/Report1/petrolereport.html'

                # Resultat PETROLE LAMPANT Fetching data from the dictionary
                data.update({
                    'aspect': res_dict.get(2, {}).get('valeurResultatChar', ''),
                    'couleursaybolt': res_dict.get(8, {}).get('valeurResultatChar', ''),
                    'aciditetotal': res_dict.get(1, {}).get('valeurResultat', ''),
                    'soufre': res_dict.get(34, {}).get('valeurResultat', ''),
                    'soufremercaptan': res_dict.get(33, {}).get('valeurResultat', ''),
                    'docteurtest': res_dict.get(16, {}).get('valeurResultat', ''),
                    'distillation': res_dict.get(100, {}).get('valeurResultat', ''),
                    'pointinitial': res_dict.get(30, {}).get('valeurResultat', ''),
                    'pointfinal': res_dict.get(29, {}).get('valeurResultat', ''),
                    'pointfumee': res_dict.get(28, {}).get('valeurResultat', ''),
                    'pointeclair': res_dict.get(25, {}).get('valeurResultat', ''),
                    'freezingpoint': res_dict.get(17, {}).get('valeurResultat', ''),
                    'residu': res_dict.get(31, {}).get('valeurResultat', ''),
                    'perte': res_dict.get(23, {}).get('valeurResultat', ''),
                    'massevolumique15': res_dict.get(20, {}).get('valeurResultat', ''),
                    'viscosite': res_dict.get(37, {}).get('valeurResultat', ''),
                    'pointinflammabilite': res_dict.get(27, {}).get('valeurResultat', ''),
                    'teneureau': res_dict.get(35, {}).get('valeurResultat', ''),
                    'conductivite': res_dict.get(4, {}).get('valeurResultat', ''),
                    'vol10': res_dict.get(11, {}).get('valeurResultat', ''),
                    'vol20': res_dict.get(12, {}).get('valeurResultat', ''),
                    'vol30': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol40': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol50': res_dict.get(13, {}).get('valeurResultat', ''),
                    'vol60': res_dict.get(44, {}).get('valeurResultat', ''),
                    'vol70': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol80': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol90': res_dict.get(15, {}).get('valeurResultat', ''),
                })
                
                try:
                    corrosion_str = res_dict.get(5, {}).get('valeurResultat', '')
                    data['corrosion'] = int(corrosion_str) if corrosion_str != '' else ''
                except (ValueError, TypeError):
                    data['corrosion'] = ''

            if template:
                pdf = render_to_pdf(template, data)
                if pdf:
                    # Update isPrinted only after successfully PDF generation
                    ImpressionResultat.objects.filter(idcargaison=pk).update(isPrinted=1)
                    
                    # Log activity
                    UserActivityLog.objects.create(
                        user=user,
                        action="Certificat Imprimé",
                        object_id=str(pk),
                        description=f"Certificat pour cargaison {pk} (Produit: {produit}) imprimé par {user.get_full_name()}."
                    )

                    pdf_base64 = base64.b64encode(pdf.getvalue()).decode('utf-8')
                    return JsonResponse({'status': 'success', 'pdf_base64': pdf_base64})

        else:
            return ('logout')
    else:
        return redirect('logout')



# Ajax response
@login_required(login_url='login')
@require_POST
def responseAffichageanalyse(request):
    user = request.user
    id = user.id
    role = user.role_id
    if role == 5 or role == 1:
        # ---------------------------
        # Read POST payload safely
        # ---------------------------
        def get_payload():
            ct = (request.headers.get("Content-Type") or "").lower()
            if "application/json" in ct:
                try:
                    return json.loads(request.body.decode("utf-8") or "{}") or {}
                except Exception:
                    return {}
            # regular form POST
            return request.POST

        params = get_payload()

        # Get filter parameters
        date_debut = params.get('date_debut')
        date_fin = params.get('date_fin')
        code_labo_filter = params.get('code_labo_filter')

        # Leverage denormalized scoping to avoid deep joins in the main QuerySet
        allowed_entrepot_ids = Entrepot.objects.filter(
            ville__affectationville__username_id=id
        ).values_list('identrepot', flat=True)

        # Subqueries to calculate completion percentage
        total_params_sq = AffectationParametre.objects.filter(
            idproduit=OuterRef('produit_id')
        ).values('idproduit').annotate(count=Count('idParametre')).values('count')

        done_params_sq = ResultatAnalyse.objects.filter(
            idcargaison=OuterRef('pk')
        ).values('idcargaison').annotate(count=Count('idParametre')).values('count')

        qs = Cargaison.objects.filter(
            etat='Analyse Labo en cours',
            entrepot_id__in=allowed_entrepot_ids
        ).annotate(
            total_params=Coalesce(Subquery(total_params_sq), 0),
            done_params=Coalesce(Subquery(done_params_sq), 0)
        )

        # Apply filters (leveraging denormalized fields)
        has_filter = False
        if date_debut:
            qs = qs.filter(date_reception_labo__gte=date_debut)
            has_filter = True
        if date_fin:
            qs = qs.filter(date_reception_labo__date__lte=date_fin)
            has_filter = True
        if code_labo_filter:
            if code_labo_filter.isdigit():
                qs = qs.filter(code_labo=int(code_labo_filter))
            else:
                qs = qs.filter(code_labo__icontains=code_labo_filter)
            has_filter = True

        # recordsTotal for DataTables (count before search/filters but within scope)
        recordsTotal = qs.count()

        # Get the search value from the request's GET parameters
        search_value = params.get('search', {}).get('value') if isinstance(params.get('search'), dict) else params.get('search[value]')
        search_value = search_value or params.get('q')

        # If no filter is applied, return empty data (as requested "before display... a filter has to be applied")
        if not has_filter and not search_value:
            return JsonResponse({
                'data': [],
                'draw': int(params.get('draw', 1)),
                'recordsTotal': recordsTotal,
                'recordsFiltered': 0,
            })

        # Apply search filter to the QuerySet (leveraging denormalized fields and indexes)
        if search_value:
            search_q = Q(immatriculation__icontains=search_value) | \
                       Q(nom_produit__icontains=search_value) | \
                       Q(nom_importateur__icontains=search_value) | \
                       Q(nom_entrepot__icontains=search_value)
            
            if search_value.isdigit():
                val = int(search_value)
                search_q |= Q(code_labo=val) | Q(numdos=val)
            else:
                search_q |= Q(code_labo__icontains=search_value)
                
            qs = qs.filter(search_q)

        # recordsFiltered for DataTables
        recordsFiltered = qs.count()

        qs = qs.values(
            'idcargaison',
            'date_reception_labo',
            'code_labo',
            'entrepot_echantillon__numrappechauto',
            'numdos',
            'immatriculation',
            'nom_produit',
            'total_params',
            'done_params'
        ).order_by('date_reception_labo')

        # Pagination parameters
        draw = int(params.get('draw', 1))
        start = int(params.get('start', 0))
        length = int(params.get('length', 13))

        if length <= 0:
            return JsonResponse({
                'data': [],
                'draw': draw,
                'recordsTotal': recordsTotal,
                'recordsFiltered': recordsFiltered,
            })

        # Use direct slicing for performance
        data = list(qs[start:start+length])

        # Rename keys for frontend compatibility
        for r in data:
            # Date handling
            dt_rec = r.pop("date_reception_labo", None)
            if dt_rec:
                r["date_reception_labo__date"] = dt_rec.date()
                r["entrepot_echantillon__laboreception__datereceptionlabo__date"] = dt_rec.date()
            else:
                r["date_reception_labo__date"] = None
                r["entrepot_echantillon__laboreception__datereceptionlabo__date"] = None

            # Keep both original and legacy keys for compatibility
            r["entrepot_echantillon__laboreception__codelabo"] = r.get("code_labo")
            r["produit__nomproduit"] = r.get("nom_produit")

            # Completion Percentage
            total = r.pop("total_params", 0) or 0
            done = r.pop("done_params", 0) or 0
            r["completion_percent"] = round((done / total * 100), 1) if total > 0 else 0
            r["completion_text"] = f"{done}/{total}"

        # Return JSON response with the data
        return JsonResponse({
            'data': data,
            'draw': draw,
            'recordsTotal': recordsTotal,
            'recordsFiltered': recordsFiltered,
        })

    else:
        return redirect('logout')


# Saisie saisieResultat Ajax
@login_required(login_url='login')
@require_POST
def saisieResultatAjax(request):
    pk = request.POST.get('idcargaison', '')
    try:
        # Use only needed fields from Cargaison
        cargaison = Cargaison.objects.only('idcargaison', 'nom_produit', 'code_labo', 'produit_id').get(idcargaison=pk)
    except Cargaison.DoesNotExist:
        return JsonResponse({'data': [], 'codeLabo': None}, status=404)

    nom_produit = cargaison.nom_produit
    code_labo = cargaison.code_labo

    # Get all parameters assigned to this product
    params_qs = AffectationParametre.objects.filter(
        idproduit=cargaison.produit_id
    ).select_related('idParametre').order_by('id')

    # Fetch existing results for this cargaison to avoid N+1 in the loop
    results = ResultatAnalyse.objects.filter(idcargaison_id=pk).values('idParametre_id', 'valeurResultat', 'valeurResultatChar')
    results_dict = {r['idParametre_id']: r for r in results}

    data = []
    for ap in params_qs:
        param = ap.idParametre
        res = results_dict.get(param.idParametre)

        data.append({
            'idParametre': param.idParametre,
            'idcargaison': cargaison.idcargaison,
            'nomproduit': nom_produit,
            'nomParametre': param.nomParametre,
            'valeurResultat': res['valeurResultat'] if res else None,
            'valeurResultatChar': res['valeurResultatChar'] if res else None
        })

    # Return JSON response with the data
    return JsonResponse({
        'data': data,
        'codeLabo': code_labo,
    })


@login_required(login_url='login')
@require_POST
def saisieResultatParametreAjax(request):
    user = request.user
    parametre_id = request.POST.get('idParametre')
    idcargaison = request.POST.get('idcargaison')
    input_value = request.POST.get('inputValue')

    if not all([parametre_id, idcargaison]):
        return JsonResponse({'status': 'error', 'message': 'Missing parameters'}, status=400)

    # Determine which field to update based on parametreId
    # Hardcoded IDs 2, 8, 22 use valeurResultatChar (string)
    # Others use valeurResultat (float)
    defaults = {}
    if parametre_id in ['2', '8', '22']:
        defaults['valeurResultatChar'] = input_value
    else:
        try:
            # Ensure it's a valid float if it's supposed to be numeric
            defaults['valeurResultat'] = float(input_value) if input_value else None
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid numeric value'}, status=400)

    ResultatAnalyse.objects.update_or_create(
        idcargaison_id=idcargaison,
        idParametre_id=parametre_id,
        defaults=defaults
    )

    UserActivityLog.objects.create(
        user=user,
        action="Test result input",
        object_id=str(idcargaison),
        description=f"User {user.get_full_name()} input result for param {parametre_id} on cargaison {idcargaison}",
    )

    return JsonResponse({'status': 'success'})


@login_required(login_url='login')
def affichageAnalyseRefaire(request):
    user = request.user
    role = user.role_id
    template = 'labo_analyse_refaire.html'
    if role == 5 or role == 1:
        count = Cargaison.objects.filter(
            etat='Refaire',
            entrepot__ville__affectationville__username_id=user.id
        ).count()
        print(count)
        context = {
            'count': count
        }
        return render(request, template, context)
    else:
        return redirect('logout')


@login_required(login_url='login')
@require_POST
def affichageAnalyseRefaireResponse(request):
    user = request.user
    id = user.id
    role = user.role_id
    if role == 5 or role == 1:
        # ---------------------------
        # Read POST payload safely
        # ---------------------------
        def get_payload():
            ct = (request.headers.get("Content-Type") or "").lower()
            if "application/json" in ct:
                try:
                    return json.loads(request.body.decode("utf-8") or "{}") or {}
                except Exception:
                    return {}
            # regular form POST
            return request.POST

        params = get_payload()

        # Leverage denormalized scoping to avoid deep joins in the main QuerySet
        allowed_entrepot_ids = Entrepot.objects.filter(
            ville__affectationville__username_id=id
        ).values_list('identrepot', flat=True)

        qs = Cargaison.objects.filter(
            etat="Refaire",
            entrepot_id__in=allowed_entrepot_ids
        ).values(
            'idcargaison',
            'date_reception_labo',
            'code_labo',
            'entrepot_echantillon__numrappechauto',
            'numdos',
            'immatriculation',
            'nom_produit',
        ).order_by('date_echantillon')

        # Get the search value from the request's GET parameters
        search_value = params.get('search[value]', '')

        # Apply search filter to the QuerySet (leveraging denormalized fields and indexes)
        if search_value:
            search_q = Q(immatriculation__icontains=search_value) | \
                       Q(nom_produit__icontains=search_value)
            
            if search_value.isdigit():
                val = int(search_value)
                search_q |= Q(code_labo=val) | Q(numdos=val)
            else:
                search_q |= Q(code_labo__icontains=search_value)
                
            qs = qs.filter(search_q)

        # recordsTotal / recordsFiltered for DataTables
        total_count = qs.count()

        # Pagination parameters
        draw = int(params.get('draw', 1))
        start = int(params.get('start', 0))
        length = int(params.get('length', 10))

        if length <= 0:
            return JsonResponse({
                'data': [],
                'draw': draw,
                'recordsTotal': total_count,
                'recordsFiltered': total_count,
            })

        # Use direct slicing for performance
        data = list(qs[start:start+length])

        # Rename keys for frontend compatibility
        for r in data:
            if r.get("date_reception_labo"):
                r["date_reception_labo__date"] = r.pop("date_reception_labo").date()
            else:
                r["date_reception_labo__date"] = r.pop("date_reception_labo", None)

            # Ensure compatibility with redo-table expectations
            r["code_labo"] = r.get("code_labo", None)
            r["entrepot_echantillon__numrappechauto"] = r.get("entrepot_echantillon__numrappechauto", None)
            r["nom_produit"] = r.get("nom_produit", None)

        # Since DataTables and the redo-count badge require the total count,
        # we still perform a count, but we've optimized the QuerySet above.
        total_count = qs.count()

        # Return JSON response with the data
        return JsonResponse({
            'data': data,
            'draw': draw,
            'recordsTotal': total_count,
            'recordsFiltered': total_count,
        })


@login_required(login_url='login')
def echantillonRecus(request):
    user = request.user
    role = user.role_id
    if role == 5 or role == 1 or role == 6:
        template = 'labo_rapport.html'
        context = {}
        return render(request, template, context)
    else:
        return redirect('logout')


@login_required(login_url='login')
def echantillonRecusResponse(request):
    user = request.user
    role = user.role_id
    if role == 5 or role == 1 or role == 6:
        qs = Cargaison.objects.filter(
            etat="Analyse Labo en cours",
            entrepot__ville__affectationville__username_id=user.id
        ).values(
            'dateheurecargaison__date',
            'date_echantillon__date',
            'date_reception_labo__date',
            'code_labo',
            'entrepot_echantillon__numrappechauto',
            'num_certificat_qualite',
            'nom_produit',
            'numdos',
        ).order_by('date_reception_labo')

        # Get the search value from the request's GET parameters
        search_value = request.GET.get('search[value]', '')

        # Apply search filter to the QuerySet
        if search_value:
            qs = qs.filter(
                Q(code_labo__iexact=search_value)
            )

        # Number of items to show per page
        items_per_page = 10

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
    else:
        return redirect('logout')


@login_required(login_url='login')
def correctionNature(request):
    if request.method == 'POST':
        produit_id = request.POST.get('produit')
        idcargaison = request.POST.get('idcargaison')
        
        if not produit_id or not idcargaison:
            return JsonResponse({"message": "Données manquantes"}, status=400)
            
        try:
            # We need the full object to call save() which handles denormalization
            c = Cargaison.objects.get(idcargaison=idcargaison)
            c.produit_id = produit_id
            c.save() # This will update nom_produit and other fields
            
            # Log the change
            UserActivityLog.objects.create(
                user=request.user,
                action="Correction Nature Produit",
                object_id=str(idcargaison),
                description=f"User {request.user.get_full_name()} corrected product for cargaison {idcargaison} to product ID {produit_id}."
            )
            
            return JsonResponse({"message": "Changement de produit effectué avec succès"}, status=200)
        except Cargaison.DoesNotExist:
            return JsonResponse({"message": "Cargaison introuvable"}, status=404)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Méthode non autorisée"}, status=405)


@login_required(login_url='login')
def clearSaisie(request):
    if request.method == 'POST':
        parametreId = request.POST.get('rowId')
        idcargaison = request.POST.get('idcargaison')
        
        if not all([parametreId, idcargaison]):
            return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)

        # Efficient clear (delete or set to null)
        # Using update allows us to be efficient if the record exists
        # Hardcoded IDs 2, 8, 22 use valeurResultatChar (string)
        if parametreId in ['2', '8', '22']:
            ResultatAnalyse.objects.filter(idcargaison_id=idcargaison, idParametre_id=parametreId).update(valeurResultatChar="")
        else:
            ResultatAnalyse.objects.filter(idcargaison_id=idcargaison, idParametre_id=parametreId).update(valeurResultat=None)

        UserActivityLog.objects.create(
            user=request.user,
            action="Clear test result",
            object_id=str(idcargaison),
            description=f"User {request.user.get_full_name()} cleared result for param {parametreId} on cargaison {idcargaison}",
        )

        return JsonResponse({'status': 'success'})
    else:
        return redirect('logout')


@login_required(login_url='login')
def enchAttenteReception(request):
    user = request.user.id
    template = 'laboRapport.html'
    qs = Cargaison.objects.filter(
        etat='Echantillonner',
        entrepot__ville__affectationville__username_id=user
    ).values(
        'numdos', 'entrepot_echantillon__numrappechauto', 'date_echantillon',
        'nom_entrepot', 'nom_importateur',
        'nom_produit', 'entrepot_echantillon__qte'
    )
    table = RapportLaboratoireEnAttenteReception(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)

    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enchAttenteReception2(request):
    user = request.user.id
    template = 'laboRapport2.html'
    qs = Cargaison.objects.filter(
        etat='Echantillonner',
        entrepot__ville__affectationville__username_id=user
    ).values(
        'numdos', 'entrepot_echantillon__numrappechauto', 'date_echantillon',
        'nom_entrepot', 'nom_importateur',
        'nom_produit', 'entrepot_echantillon__qte'
    )
    table = RapportLaboratoireEnAttenteReception(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)

    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enchAttenteReceptionExport(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        etat='Echantillonner',
        entrepot__ville__affectationville__username_id=user
    ).values(
        'numdos', 'entrepot_echantillon__numrappechauto', 'date_echantillon',
        'nom_entrepot', 'nom_importateur',
        'nom_produit', 'entrepot_echantillon__qte'
    )
    table = RapportLaboratoireEnAttenteReception(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)

    export_format = 'xlsx'

    serialized_qs = list(qs)

    # Start Celery task to export report asynchronously
    result = app.send_task('labo.tasks.export_report_task', args=[export_format, serialized_qs])

    # Retrieve the task ID
    task_id = result.id

    message = "Export task started. Task ID: {}".format(task_id)
    return JsonResponse({'task_id': task_id})


@login_required(login_url='login')
def enchAttenteReceptionExport2(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        etat='Echantillonner',
        entrepot__ville__affectationville__username_id=user
    ).values(
        'numdos', 'entrepot_echantillon__numrappechauto', 'date_echantillon',
        'nom_entrepot', 'nom_importateur',
        'nom_produit', 'entrepot_echantillon__qte'
    )
    table = RapportLaboratoireEnAttenteReception(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)

    export_format = 'xlsx'

    serialized_qs = list(qs)

    # Start Celery task to export report asynchronously
    result = app.send_task('labo.tasks.export_report_task', args=[export_format, serialized_qs])

    # Retrieve the task ID
    task_id = result.id

    message = "Export task started. Task ID: {}".format(task_id)
    return JsonResponse({'task_id': task_id})


@login_required(login_url='login')
def enchAttenteResultat(request):
    user = request.user.id
    template = 'laboRapportEnAttenteAnalyse.html'
    qs = Cargaison.objects.filter(
        etat='Analyse Labo en cours',
        entrepot__ville__affectationville__username_id=user,
    ).values(
        'date_echantillon', 'date_reception_labo', 'numdos',
        'entrepot_echantillon__numrappechauto', 'code_labo', 'nom_entrepot',
        'nom_importateur', 'nom_produit',
        'entrepot_echantillon__qte'
    )
    table = RapportLaboratoireEnAttenteResultat(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enchAttenteResultat2(request):
    user = request.user.id
    template = 'laboRapportEnAttenteAnalyse2.html'
    qs = Cargaison.objects.filter(
        etat='Analyse Labo en cours',
        entrepot__ville__affectationville__username_id=user,
    ).values(
        'date_echantillon', 'date_reception_labo', 'numdos',
        'entrepot_echantillon__numrappechauto', 'code_labo', 'nom_entrepot',
        'nom_importateur', 'nom_produit',
        'entrepot_echantillon__qte'
    )
    table = RapportLaboratoireEnAttenteResultat(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enchAttenteResultatExport(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        etat='Analyse Labo en cours',
        entrepot__ville__affectationville__username_id=user,
    ).values(
        'date_echantillon', 'date_reception_labo', 'numdos',
        'entrepot_echantillon__numrappechauto', 'code_labo', 'nom_entrepot',
        'nom_importateur', 'nom_produit',
        'entrepot_echantillon__qte'
    )
    table = RapportLaboratoireEnAttenteResultat(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)

    export_format = 'xlsx'

    serialized_qs = list(qs)

    # Start Celery task to export report asynchronously
    result = app.send_task('labo.tasks.export_report_task_Attente_Res', args=[export_format, serialized_qs])

    # Retrieve the task ID
    task_id = result.id

    message = "Export task started. Task ID: {}".format(task_id)
    return JsonResponse({'task_id': task_id})


@login_required(login_url='login')
def enchAttenteResultatExport2(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        etat='Analyse Labo en cours',
        entrepot__ville__affectationville__username_id=user,
    ).values(
        'date_echantillon', 'date_reception_labo', 'numdos',
        'entrepot_echantillon__numrappechauto', 'code_labo', 'nom_entrepot',
        'nom_importateur', 'nom_produit',
        'entrepot_echantillon__qte'
    )
    table = RapportLaboratoireEnAttenteResultat(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)

    export_format = 'xlsx'

    serialized_qs = list(qs)

    # Start Celery task to export report asynchronously
    result = app.send_task('labo.tasks.export_report_task_Attente_Res', args=[export_format, serialized_qs])

    # Retrieve the task ID
    task_id = result.id

    message = "Export task started. Task ID: {}".format(task_id)
    return JsonResponse({'task_id': task_id})


@login_required(login_url='login')
def enchAttenteValidation(request):
    user = request.user.id
    template = 'laboRapportEnAttenteValidation.html'
    qs = Cargaison.objects.filter(
        etat='Validation en cours 2',
        entrepot__ville__affectationville__username_id=user,
    ).values(
        'date_echantillon', 'date_reception_labo', 'numdos',
        'entrepot_echantillon__numrappechauto', 'code_labo', 'num_certificat_qualite',
        'nom_entrepot', 'nom_importateur',
        'nom_produit'
    )
    table = RapportLaboratoireEnAttenteValidation(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enchAttenteValidation2(request):
    user = request.user.id
    template = 'laboRapportEnAttenteValidation2.html'
    qs = Cargaison.objects.filter(
        etat='Validation en cours 2',
        entrepot__ville__affectationville__username_id=user,
    ).values(
        'date_echantillon', 'date_reception_labo', 'numdos',
        'entrepot_echantillon__numrappechauto', 'code_labo', 'num_certificat_qualite',
        'nom_entrepot', 'nom_importateur',
        'nom_produit'
    )
    table = RapportLaboratoireEnAttenteValidation(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enchPrintedCert(request):
    user = request.user.id
    template = 'laboRapportCertImprimer.html'
    qs = Cargaison.objects.filter(
        impressionresultat__isPrinted=1,
        entrepot__ville__affectationville__username_id=user,
    ).values(
        'date_echantillon', 'date_reception_labo', 'numdos',
        'entrepot_echantillon__numrappechauto', 'code_labo', 'num_certificat_qualite',
        'nom_entrepot', 'nom_importateur', 'impressionresultat__printDate',
        'nom_produit'
    )
    table = RapportLaboratoireEnchPrintedCert(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enchPrintedCert2(request):
    user = request.user.id
    template = 'laboRapportCertImprimer.html'
    qs = Cargaison.objects.filter(
        impressionresultat__isPrinted=1,
        entrepot__ville__affectationville__username_id=user,
    ).values(
        'date_echantillon', 'date_reception_labo', 'numdos',
        'entrepot_echantillon__numrappechauto', 'code_labo', 'num_certificat_qualite',
        'nom_entrepot', 'nom_importateur', 'impressionresultat__printDate',
        'nom_produit'
    )
    table = RapportLaboratoireEnchPrintedCert(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def enchPrintedCertExport(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        impressionresultat__isPrinted=1,
        entrepot__ville__affectationville__username_id=user,
    ).values(
        'date_echantillon', 'date_reception_labo', 'numdos',
        'entrepot_echantillon__numrappechauto', 'code_labo', 'num_certificat_qualite',
        'nom_entrepot', 'nom_importateur', 'impressionresultat__printDate',
        'nom_produit'
    )
    table = RapportLaboratoireEnchPrintedCert(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)

    export_format = 'xlsx'
    serialized_qs = list(qs)

    # Start Celery task to export report asynchronously
    result = app.send_task('labo.tasks.export_report_task_cert_imprimer', args=[export_format, serialized_qs])

    # Retrieve the task ID
    task_id = result.id

    message = "Export task started. Task ID: {}".format(task_id)
    return JsonResponse({'task_id': task_id})


@login_required(login_url='login')
def enchPrintedCertExport2(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        impressionresultat__isPrinted=1,
        entrepot__ville__affectationville__username_id=user,
    ).values(
        'date_echantillon', 'date_reception_labo', 'numdos',
        'entrepot_echantillon__numrappechauto', 'code_labo', 'num_certificat_qualite',
        'nom_entrepot', 'nom_importateur', 'impressionresultat__printDate',
        'nom_produit'
    )
    table = RapportLaboratoireEnchPrintedCert(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)

    export_format = 'xlsx'
    serialized_qs = list(qs)

    # Start Celery task to export report asynchronously
    result = app.send_task('labo.tasks.export_report_task_cert_imprimer', args=[export_format, serialized_qs])

    # Retrieve the task ID
    task_id = result.id

    message = "Export task started. Task ID: {}".format(task_id)
    return JsonResponse({'task_id': task_id})


@login_required(login_url='login')
def rapportCq(request):
    template = 'laboRapportsCq.html'
    form = FiltresDate()
    context = {'form': form}
    return render(request, template, context)


@login_required(login_url='login')
def rapportCq2(request):
    template = 'laboRapportsCq2.html'
    form = FiltresDate()
    context = {'form': form}
    return render(request, template, context)


@login_required(login_url='login')
def rapportCqResponse(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user,
        date_reception_labo__isnull=False
        # impressionresultat__isnull=False
    ).annotate(
        conformiteProduit=Case(
            When(impressionresultat__isConforme__isnull=True, then=Value('EN ATTENTE')),
            When(impressionresultat__isConforme=False, then=Value('NON CONFORME')),
            When(impressionresultat__isConforme=True, then=Value('CONFORME')),
            default=Value('AUTRE CAS'),  # Handle other cases if necessary
            output_field=CharField()
        )
    ).values(
        'numdos',
        'entrepot_echantillon__numrappechauto',
        'code_labo',
        'date_echantillon__date',
        'num_certificat_qualite',
        'date_reception_labo__date',
        'conformiteProduit',
        'nom_entrepot',
        'nom_importateur',
        'immatriculation',
        'nom_produit'
    ).order_by('-date_reception_labo')

    # Number of items to show per page
    items_per_page = 20

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
def rapportCQExport(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user,
        date_reception_labo__isnull=False
        # impressionresultat__isnull=False
    ).annotate(
        conformiteProduit=Case(
            When(impressionresultat__isConforme__isnull=True, then=Value('EN ATTENTE')),
            When(impressionresultat__isConforme=False, then=Value('NON CONFORME')),
            When(impressionresultat__isConforme=True, then=Value('CONFORME')),
            default=Value('AUTRE CAS'),  # Handle other cases if necessary
            output_field=CharField()
        )
    ).values(
        'numdos',
        'entrepot_echantillon__numrappechauto',
        'code_labo',
        'date_echantillon',
        'num_certificat_qualite',
        'date_reception_labo',
        'conformiteProduit',
        'nom_entrepot',
        'nom_importateur',
        'immatriculation',
        'nom_produit',
    ).order_by('-date_reception_labo')

    table = rapportActiviteCQ(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)

    export_format = 'xlsx'
    serialized_qs = list(qs)

    # Start Celery task to export report asynchronously
    result = app.send_task('labo.tasks.export_report_task_rapport_cq', args=[export_format, serialized_qs])

    # Retrieve the task ID
    task_id = result.id

    message = "Export task started. Task ID: {}".format(task_id)
    return JsonResponse({'task_id': task_id})


@login_required(login_url='login')
def rapportCqfiltres(request):
    template = 'laboRapportsCQFiltres.html'
    # Get the search value from the request's GET parameters
    if request.method == 'POST':
        date_d = request.POST['date_d']
        date_f = request.POST['date_f']

        request.session['date_d'] = date_d
        request.session['date_f'] = date_f

        form = FiltresDate()
        context = {'form': form}
        return render(request, template, context)
    else:
        return redirect('receptionRapports')


@login_required(login_url='login')
def rapportCqfiltres2(request):
    template = 'laboRapportsCQFiltres2.html'
    # Get the search value from the request's GET parameters
    if request.method == 'POST':
        date_d = request.POST['date_d']
        date_f = request.POST['date_f']

        request.session['date_d'] = date_d
        request.session['date_f'] = date_f

        form = FiltresDate()
        context = {'form': form}
        return render(request, template, context)
    else:
        return redirect('receptionRapports')


@login_required(login_url='login')
def rapportCqfiltresResponse(request):
    user = request.user.id
    ville = AffectationVille.objects.filter(username_id=user).values_list('ville_id', flat=True)
    qs = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user,
        date_reception_labo__isnull=False
        # impressionresultat__isnull=False
    ).annotate(
        conformiteProduit=Case(
            When(impressionresultat__isConforme__isnull=True, then=Value('EN ATTENTE')),
            When(impressionresultat__isConforme=False, then=Value('NON CONFORME')),
            When(impressionresultat__isConforme=True, then=Value('CONFORME')),
            default=Value('AUTRE CAS'),  # Handle other cases if necessary
            output_field=CharField()
        )
    ).values(
        'numdos',
        'entrepot_echantillon__numrappechauto',
        'code_labo',
        'date_echantillon',
        'num_certificat_qualite',
        'date_reception_labo',
        'conformiteProduit',
        'nom_entrepot',
        'nom_importateur',
        'immatriculation',
        'nom_produit',
    ).order_by('-date_reception_labo')

    date_d = request.session['date_d']
    date_f = request.session['date_f']

    # Apply search filter to the QuerySet
    if date_d and date_f:
        qs = qs.filter(
            date_reception_labo__date__range=(date_d, date_f)
        )
    else:
        if date_d:
            qs = qs.filter(
                date_reception_labo__date=(date_d)
            )
        else:
            if date_f:
                qs = qs.filter(
                    date_reception_labo__date=(date_f)
                )

    # Number of items to show per page
    items_per_page = 20

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
def rapportCqfiltresResponseExport(request):
    user = request.user.id
    ville = AffectationVille.objects.filter(username_id=user).values_list('ville_id', flat=True)
    qs = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user,
        date_reception_labo__isnull=False
        # impressionresultat__isnull=False
    ).annotate(
        conformiteProduit=Case(
            When(impressionresultat__isConforme__isnull=True, then=Value('EN ATTENTE')),
            When(impressionresultat__isConforme=False, then=Value('NON CONFORME')),
            When(impressionresultat__isConforme=True, then=Value('CONFORME')),
            default=Value('AUTRE CAS'),  # Handle other cases if necessary
            output_field=CharField()
        )
    ).values(
        'numdos',
        'entrepot_echantillon__numrappechauto',
        'code_labo',
        'date_echantillon',
        'num_certificat_qualite',
        'date_reception_labo',
        'conformiteProduit',
        'nom_entrepot',
        'nom_importateur',
        'immatriculation',
        'nom_produit',
    ).order_by('-date_reception_labo')

    date_d = request.session['date_d']
    date_f = request.session['date_f']

    # Apply search filter to the QuerySet
    if date_d and date_f:
        qs = qs.filter(
            entrepot_echantillon__laboreception__datereceptionlabo__date__range=(date_d, date_f)
        )
    else:
        if date_d:
            qs = qs.filter(
                entrepot_echantillon__laboreception__datereceptionlabo__date=(date_d)
            )
        else:
            if date_f:
                qs = qs.filter(
                    entrepot_echantillon__laboreception__datereceptionlabo__date=(date_f)
                )

    table = rapportActiviteCQ(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)

    export_format = 'xlsx'
    serialized_qs = list(qs)

    # Start Celery task to export report asynchronously
    result = app.send_task('labo.tasks.export_report_task_rapport_cq', args=[export_format, serialized_qs])

    # Retrieve the task ID
    task_id = result.id

    message = "Export task started. Task ID: {}".format(task_id)
    return JsonResponse({'task_id': task_id})


@login_required(login_url='login')
@require_POST
def bulkConforme1(request):
    user = request.user
    role = user.role_id

    if role in (1, 6):
        selected_ids = request.POST.getlist('selectedRowIds[]')
        if not selected_ids:
            return JsonResponse({'status': 'failure', 'message': 'No samples selected'}, status=400)

        try:
            with transaction.atomic():
                cargaisons = Cargaison.objects.select_for_update().filter(idcargaison__in=selected_ids)
                count = cargaisons.count()

                cargaisons.update(
                    etat="Validation en cours 2",
                    conformite="Conforme aux exigences",
                    impression="0"
                )

                UserActivityLog.objects.create(
                    user=user,
                    action="Bulk Validation 1: CONFORME",
                    description=f"User validated {count} samples as CONFORME (Step 1). IDs: {', '.join(selected_ids)}",
                )

            return JsonResponse({'status': 'success', 'message': f'{count} samples processed.'})
        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'failure', 'message': 'Unauthorized'}, status=403)


@login_required(login_url='login')
@require_POST
def bulkNonConforme1(request):
    user = request.user
    role = user.role_id

    if role in (1, 6):
        selected_ids = request.POST.getlist('selectedRowIds[]')
        if not selected_ids:
            return JsonResponse({'status': 'failure', 'message': 'No samples selected'}, status=400)

        try:
            with transaction.atomic():
                cargaisons = Cargaison.objects.select_for_update().filter(idcargaison__in=selected_ids)
                count = cargaisons.count()

                cargaisons.update(
                    etat="Validation en cours 2",
                    conformite="Non conforme aux exigences",
                    impression="0"
                )

                UserActivityLog.objects.create(
                    user=user,
                    action="Bulk Validation 1: NON CONFORME",
                    description=f"User validated {count} samples as NON CONFORME (Step 1). IDs: {', '.join(selected_ids)}",
                )

            return JsonResponse({'status': 'success', 'message': f'{count} samples processed.'})
        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'failure', 'message': 'Unauthorized'}, status=403)


@login_required(login_url='login')
@require_POST
def bulkRefaire1(request):
    user = request.user
    role = user.role_id

    if role in (1, 6):
        selected_ids = request.POST.getlist('selectedRowIds[]')
        if not selected_ids:
            return JsonResponse({'status': 'failure', 'message': 'No samples selected'}, status=400)

        try:
            with transaction.atomic():
                cargaisons = Cargaison.objects.select_for_update().filter(idcargaison__in=selected_ids)
                count = cargaisons.count()

                cargaisons.update(etat="Refaire")

                UserActivityLog.objects.create(
                    user=user,
                    action="Bulk Validation: REFAIRE",
                    description=f"User requested re-analysis for {count} samples. IDs: {', '.join(selected_ids)}",
                )

            return JsonResponse({'status': 'success', 'message': f'{count} samples marked as REFAIRE.'})
        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'failure', 'message': 'Unauthorized'}, status=403)


@login_required(login_url='login')
@require_POST
def bulkConforme2(request):
    user = request.user
    role = user.role_id

    if role in (1, 10):
        selected_ids = request.POST.getlist('selectedRowIds[]')
        if not selected_ids:
            return JsonResponse({'status': 'failure', 'message': 'No samples selected'}, status=400)

        try:
            now = timezone.now()
            with transaction.atomic():
                cargaisons = Cargaison.objects.select_for_update().filter(idcargaison__in=selected_ids)
                count = 0
                processed_ids = []

                for c in cargaisons:
                    if not ImpressionResultat.objects.filter(idcargaison=c).exists():
                        ImpressionResultat.objects.create(
                            printDate=now.date(),
                            isConforme=True,
                            isPrinted=False,
                            idcargaison=c
                        )
                        c.etat = "Conforme aux exigences"
                        c.conformite = "Conforme aux exigences"
                        c.impression = "0"
                        c.dateHeureAnalyseLabo = now
                        c.save(update_fields=['etat', 'conformite', 'impression', 'dateHeureAnalyseLabo'])
                        count += 1
                        processed_ids.append(str(c.idcargaison))

                if count > 0:
                    UserActivityLog.objects.create(
                        user=user,
                        action="Bulk Validation 2: CONFORME",
                        description=f"User performed final validation (CONFORME) for {count} samples. IDs: {', '.join(processed_ids)}",
                    )

            return JsonResponse({'status': 'success', 'message': f'{count} samples validated.'})
        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'failure', 'message': 'Unauthorized'}, status=403)


@login_required(login_url='login')
@require_POST
def bulkNonConforme2(request):
    user = request.user
    role = user.role_id

    if role in (1, 10):
        selected_ids = request.POST.getlist('selectedRowIds[]')
        if not selected_ids:
            return JsonResponse({'status': 'failure', 'message': 'No samples selected'}, status=400)

        try:
            now = timezone.now()
            with transaction.atomic():
                cargaisons = Cargaison.objects.select_for_update().filter(idcargaison__in=selected_ids)
                count = 0
                processed_ids = []

                for c in cargaisons:
                    if not ImpressionResultat.objects.filter(idcargaison=c).exists():
                        ImpressionResultat.objects.create(
                            printDate=now.date(),
                            isConforme=False,
                            isPrinted=False,
                            idcargaison=c
                        )
                        c.etat = "Non conforme aux exigences"
                        c.conformite = "Non conforme aux exigences"
                        c.impression = "0"
                        c.dateHeureAnalyseLabo = now
                        c.save(update_fields=['etat', 'conformite', 'impression', 'dateHeureAnalyseLabo'])
                        count += 1
                        processed_ids.append(str(c.idcargaison))

                if count > 0:
                    UserActivityLog.objects.create(
                        user=user,
                        action="Bulk Validation 2: NON CONFORME",
                        description=f"User performed final validation (NON CONFORME) for {count} samples. IDs: {', '.join(processed_ids)}",
                    )

            return JsonResponse({'status': 'success', 'message': f'{count} samples validated.'})
        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'failure', 'message': 'Unauthorized'}, status=403)


@login_required(login_url='login')
@require_POST
def bulkRefaire2(request):
    user = request.user
    role = user.role_id

    if role in (1, 10):
        selected_ids = request.POST.getlist('selectedRowIds[]')
        if not selected_ids:
            return JsonResponse({'status': 'failure', 'message': 'No samples selected'}, status=400)

        try:
            with transaction.atomic():
                cargaisons = Cargaison.objects.select_for_update().filter(idcargaison__in=selected_ids)
                count = cargaisons.count()

                cargaisons.update(etat="Refaire")

                UserActivityLog.objects.create(
                    user=user,
                    action="Bulk Validation 2: REFAIRE",
                    description=f"User requested re-analysis for {count} samples (Step 2). IDs: {', '.join(selected_ids)}",
                )

            return JsonResponse({'status': 'success', 'message': f'{count} samples marked as REFAIRE.'})
        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'failure', 'message': 'Unauthorized'}, status=403)


# Fonction pour impression Certificat
@login_required(login_url='login')
@require_POST
def impressionCertificatBulk(request):
    user = request.user
    role = user.role_id

    # Check authorized roles (Admin or Labo)
    if role not in (1, 5):
        return JsonResponse({'status': 'failure', 'message': 'Unauthorized'}, status=403)

    selected_ids = request.POST.getlist('selectedRowIds[]')
    if not selected_ids:
        return JsonResponse({'status': 'failure', 'message': 'No certificates selected'}, status=400)

    try:
        # Get user's assigned ville and province
        try:
            aff_ville = AffectationVille.objects.get(username_id=user.id)
            ville_id = aff_ville.ville_id
            ville_obj = Ville.objects.get(idville=ville_id)
            province = (ville_obj.province or "").upper()
        except (AffectationVille.DoesNotExist, Ville.DoesNotExist):
            return JsonResponse({'status': 'failure', 'message': 'User not assigned to a city or city not found.'}, status=400)

        # Get signers and lab data
        try:
            affect1 = AffectationLaboratoire.objects.get(ville_id=ville_id, signGauche=False)
            affect2 = AffectationLaboratoire.objects.get(ville_id=ville_id, signGauche=True)
            
            signDroite = affect1.userId
            signGauche = affect2.userId
            
            lab_data = affect1.idLaboratoire
            lab_name = lab_data.denominationLaboratoire
        except AffectationLaboratoire.DoesNotExist:
            return JsonResponse({'status': 'failure', 'message': 'Laboratory signatories not configured for this city.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': f'Config error: {str(e)}'}, status=400)

        sign_gauche_payload = {
            'first_name': signGauche.first_name,
            'last_name': signGauche.last_name,
        }
        sign_droite_payload = {
            'first_name': signDroite.first_name,
            'last_name': signDroite.last_name,
        }

        # Start Celery task to export report asynchronously
        # We use the imported task and .delay() for robustness
        result = generate_certificates_pdf_task.delay(
            selected_ids, 
            province, 
            sign_gauche_payload, 
            sign_droite_payload, 
            lab_name,
            user_id=user.id
        )

        return JsonResponse({'task_id': result.id})

    except Exception as e:
        return JsonResponse({'status': 'failure', 'message': str(e)}, status=500)
