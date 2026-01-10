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
from django.db import transaction
from django.db.models import Q, Sum, Prefetch, Value, Max, OuterRef, Subquery, Count, F
from django.db.models.fields import CharField
from django.db.models.functions import Round, Coalesce, Cast
from django.forms import FloatField
from django.http import JsonResponse
from django.shortcuts import render, redirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
try:
    from django_tables2 import RequestConfig  # type: ignore
    from django_tables2.export.export import TableExport  # type: ignore
    from django_tables2.paginators import LazyPaginator  # type: ignore
except Exception:  # django_tables2 may be unavailable on some workers
    RequestConfig = None  # type: ignore
    TableExport = None  # type: ignore
    LazyPaginator = None  # type: ignore
from openpyxl import Workbook
from django.utils import timezone

from accounts.models import *
from enreg.models import Entrepot   # for per-user entrepôt scoping
from enreg.uploadToStorage import download_file_from_space
from entrepot.calculs import densite15, vcf, gsv, mta
from hydrocarbures.celery import app
from shydro.utils import render_to_pdf, render_to_pdf_content
from .forms import *
from .numact import num_cert_inspection
# from .numact import numeroactcurrent
from .numdossier import numDossier
from .tables import *

from django.core.cache import cache
import hashlib


# Class de gestion des codifacations des cargaisons
@login_required(login_url='login')
def affichageTableau(request):
    user = request.user
    uid = user.id
    role = user.role_id

    # Roles 7, 1, 11 are allowed. 
    if role not in (7, 1, 11):
        return render(request, 'shydro.html', {})

    template = 'shydro.html'
    
    # 1. Dashboard Metrics Caching
    cache_key_metrics = f"shydro:metrics:{uid}"
    metrics = cache.get(cache_key_metrics)
    
    if metrics is None:
        try:
            # Optimize counting using aggregates where possible
            # base_qs filtered by user's assigned cities
            base_qs = Cargaison.objects.filter(
                entrepot__ville__affectationville__username_id=uid
            )
            
            # Aggregated counts for Cargaison
            agg_cargaison = base_qs.aggregate(
                c=Count('idcargaison'),
                e=Count('idcargaison', filter=Q(etat="En attente d'echantillonage")),
                l=Count('idcargaison', filter=Q(etat="Analyse Labo en cours")),
                i=Count('idcargaison', filter=Q(etatInspection=1))
            )
            
            # Counts for ImpressionResultat (related to user's assigned cargo)
            agg_impression = ImpressionResultat.objects.filter(
                idcargaison__entrepot__ville__affectationville__username_id=uid
            ).aggregate(
                d=Count('idImpression', filter=Q(idcargaison__etat="Conforme aux exigences")),
                n=Count('idImpression', filter=Q(isConforme=0, control=0))
            )
            
            # Count for Entrepot_echantillon
            p = Entrepot_echantillon.objects.filter(
                idcargaison__etat='Echantillonner',
                idcargaison__entrepot__ville__affectationville__username_id=uid
            ).count()
            
            metrics = {
                'e': agg_cargaison['e'],
                'l': agg_cargaison['l'],
                'i': agg_cargaison['i'],
                'c': agg_cargaison['c'],
                'd': agg_impression['d'],
                'n': agg_impression['n'],
                'p': p
            }
            cache.set(cache_key_metrics, metrics, 300) # 5 minutes
        except Exception:
            metrics = {'e':0,'l':0,'i':0,'c':0,'d':0,'n':0,'p':0}

    # 2. Dropdown Options Caching
    # Global lists (Ville, Importateur, Produit) - cache for 15 mins
    frontieres = cache.get("shydro:options:frontieres")
    if frontieres is None:
        frontieres = list(Ville.objects.all().order_by('nomville').values('pk', 'nomville'))
        cache.set("shydro:options:frontieres", frontieres, 900)
        
    fournisseurs = cache.get("shydro:options:fournisseurs")
    if fournisseurs is None:
        fournisseurs = list(Importateur.objects.all().order_by('nomimportateur').values('pk', 'nomimportateur'))
        cache.set("shydro:options:fournisseurs", fournisseurs, 900)
        
    produits = cache.get("shydro:options:produits")
    if produits is None:
        produits = list(Produit.objects.all().order_by('nomproduit').values('pk', 'nomproduit'))
        cache.set("shydro:options:produits", produits, 900)

    # User-specific list (Entrepot) - cache for 15 mins
    cache_key_entrepots = f"shydro:options:entrepots:{uid}"
    entrepots = cache.get(cache_key_entrepots)
    if entrepots is None:
        entrepots = list(Entrepot.objects.filter(
            ville__affectationville__username_id=uid
        ).order_by('nomentrepot').values('pk', 'nomentrepot'))
        cache.set(cache_key_entrepots, entrepots, 900)

    context = {
        **metrics,
        'frontieres': frontieres,
        'fournisseurs': fournisseurs,
        'entrepots': entrepots,
        'produits': produits,
    }
    return render(request, template, context)



@login_required(login_url='login')
def responseAffichageTableau(request):
    params = request.POST
    uid = request.user.id

    def _s(k): return (params.get(k) or '').strip()
    def _has_min(v, n=2): return bool(v) and len(v) >= n

    # DataTables params
    try:
        draw = int(params.get('draw', 1))
        start = max(0, int(params.get('start', 0)))
        length = min(100, max(1, int(params.get('length', 20))))
    except Exception:
        draw, start, length = 1, 0, 20

    # Read filters
    df = _s('flt_date_from')
    dt = _s('flt_date_to')
    fr = _s('flt_frontiere')
    imp = _s('flt_importateur')
    ent = _s('flt_entrepot')
    prd = _s('flt_produit')
    imm = _s('flt_immat')
    dec = _s('flt_declaration')
    dos = _s('flt_numdos')
    search = _s('search[value]')

    has_any_filter = any([df, dt, fr, imp, ent, prd, imm, dec, dos])
    if not has_any_filter and not _has_min(search):
        return JsonResponse({'draw': draw, 'recordsTotal': 0, 'recordsFiltered': 0, 'data': []})

    # Allowed entrepots (cached)
    cache_key_ent = f"u:{uid}:allowed_entrepots"
    allowed_entrepots = cache.get(cache_key_ent)
    if allowed_entrepots is None:
        allowed_entrepots = list(
            Entrepot.objects.filter(ville__affectationville__username_id=uid)
            .values_list('identrepot', flat=True)
        )
        cache.set(cache_key_ent, allowed_entrepots, 900)

    if not allowed_entrepots:
        return JsonResponse({'draw': draw, 'recordsTotal': 0, 'recordsFiltered': 0, 'data': []})

    qs = (
        Cargaison.objects
        .filter(etat="En attente requisition", entrepot_id__in=allowed_entrepots)
    )

    # Date filters (INDEX-FRIENDLY)
    if df:
        try:
            dfrom = datetime.datetime.strptime(df, "%Y-%m-%d").date()
            qs = qs.filter(dateheurecargaison__gte=datetime.datetime.combine(dfrom, datetime.time.min))
        except Exception: pass

    if dt:
        try:
            dto = datetime.datetime.strptime(dt, "%Y-%m-%d").date()
            qs = qs.filter(dateheurecargaison__lte=datetime.datetime.combine(dto, datetime.time.max))
        except Exception: pass

    # Use denormalized fields
    if fr:  qs = qs.filter(nom_frontiere__iexact=fr)
    if imp: qs = qs.filter(nom_importateur__iexact=imp)
    if ent: qs = qs.filter(nom_entrepot__iexact=ent)
    if prd: qs = qs.filter(nom_produit__iexact=prd)

    if _has_min(imm): qs = qs.filter(immatriculation__istartswith=imm)
    if _has_min(dec): qs = qs.filter(declaration__istartswith=dec)
    
    if _has_min(dos):
        s_num = str(dos).strip()
        d_q = Q(numdossier__istartswith=s_num) | Q(numreq__istartswith=s_num)
        if s_num.isdigit():
            d_q |= Q(numdos=int(s_num))
        qs = qs.filter(d_q)

    if _has_min(search):
        s = search
        search_q = Q(declaration__istartswith=s) | \
                   Q(immatriculation__istartswith=s) | \
                   Q(nom_importateur__istartswith=s) | \
                   Q(nom_entrepot__istartswith=s) | \
                   Q(nom_produit__istartswith=s) | \
                   Q(nom_frontiere__istartswith=s) | \
                   Q(numreq__istartswith=s)
        
        if s.isdigit():
            search_q |= Q(numdos=int(s))
            
        qs = qs.filter(search_q)

    # Count (briefly cached)
    count_key = f"shydro:cnt:{uid}:{hash((df,dt,fr,imp,ent,prd,imm,dec,dos,search))}"
    records_filtered = cache.get(count_key)
    if records_filtered is None:
        records_filtered = qs.count()
        cache.set(count_key, records_filtered, 60)

    # recordsTotal (cached)
    records_total_key = f"shydro:total_count_active:{uid}"
    records_total = cache.get(records_total_key)
    if records_total is None:
        records_total = Cargaison.objects.filter(etat="En attente requisition", entrepot_id__in=allowed_entrepots).count()
        cache.set(records_total_key, records_total, 300)

    # Page fetch
    rows = (
        qs.order_by('-dateheurecargaison')
          .values(
              'idcargaison', 'dateheurecargaison',
              'nom_importateur', 'nom_entrepot',
              'nom_produit', 'volume',
              'immatriculation', 'declaration', 'numreq'
          )[start:start+length]
    )

    data = []
    for r in rows:
        dtv = r.get('dateheurecargaison')
        data.append({
            'date_entree_display': dtv.strftime('%d/%m/%Y') if dtv else '',
            'importateur__nomimportateur': r.get('nom_importateur') or '',
            'entrepot__nomentrepot': r.get('nom_entrepot') or '',
            'produit__nomproduit': r.get('nom_produit') or '',
            'volume': r.get('volume') if r.get('volume') is not None else '',
            'immatriculation': r.get('immatriculation') or '',
            'declaration': r.get('declaration') or '',
            'numreq': r.get('numreq') or '',
            'idcargaison': r.get('idcargaison'),
        })

    return JsonResponse({
        'draw': draw,
        'recordsTotal': records_total,
        'recordsFiltered': records_filtered,
        'data': data
    })



# Fonction numrequisition
@login_required(login_url='login')
def numreq(request):
    """
    Optimized function to assign a requisition number and generate a dossier number.
    Uses select_related to minimize DB hits and avoids redundant user fetches.
    """
    user = request.user
    role = user.role_id

    # Authorized roles: 1 (Admin), 7 (Chef Cellule), 11 (Agent Cellule)
    if role not in (1, 7, 11):
        return redirect('logout')

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    try:
        data = json.loads(request.body)
        numreq_val = (data.get('jsonData') or '').strip().upper()
        pk = data.get('idcargaison')

        if not pk:
            return JsonResponse({'error': 'Missing idcargaison'}, status=400)

        # 1. Fetch cargo and related warehouse in a single hit
        # We need the warehouse's ville_id for numDossier
        c = Cargaison.objects.select_related('entrepot').get(idcargaison=pk)
        
        ville_id = c.entrepot.ville_id
        td = timezone.now()
        username = user.username # Already available on request.user

        # 2. Generate Dossier Number (Auto-increment logic usually inside numDossier)
        num_dos = numDossier(ville_id, int(pk))

        # 3. Efficient Update
        c.numdos = num_dos
        c.numreq = numreq_val
        c.requisitiondackdate = td
        c.requisitionack = username
        c.etat = "En attente d'echantillonage"
        
        c.save(update_fields=['numreq', 'requisitiondackdate', 'requisitionack', 'numdos', 'etat'])

        # 4. Activity Logging
        UserActivityLog.objects.create(
            user=user,
            action="Control order data creation",
            description=f"User has authorized a control on record {pk} (Dossier: {num_dos})",
        )

        return JsonResponse({'num': num_dos})

    except Cargaison.DoesNotExist:
        return JsonResponse({'error': 'Cargaison not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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

    # 1. Dropdown Options Caching (reusing keys from affichageTableau for consistency)
    # Global lists (Ville, Importateur, Produit) - cache for 15 mins
    frontieres = cache.get("shydro:options:frontieres")
    if frontieres is None:
        try:
            from enreg.models import Ville
            frontieres = list(Ville.objects.all().order_by('nomville').values('pk', 'nomville'))
            cache.set("shydro:options:frontieres", frontieres, 900)
        except Exception:
            frontieres = []

    fournisseurs = cache.get("shydro:options:fournisseurs")
    if fournisseurs is None:
        try:
            from enreg.models import Importateur
            fournisseurs = list(Importateur.objects.all().order_by('nomimportateur').values('pk', 'nomimportateur'))
            cache.set("shydro:options:fournisseurs", fournisseurs, 900)
        except Exception:
            fournisseurs = []

    produits = cache.get("shydro:options:produits")
    if produits is None:
        try:
            from enreg.models import Produit
            produits = list(Produit.objects.all().order_by('nomproduit').values('pk', 'nomproduit'))
            cache.set("shydro:options:produits", produits, 900)
        except Exception:
            produits = []

    # User-specific list (Entrepot) - cache for 15 mins
    cache_key_entrepots = f"shydro:options:entrepots:{user_id}"
    entrepots = cache.get(cache_key_entrepots)
    if entrepots is None:
        try:
            from enreg.models import Entrepot
            entrepots = list(Entrepot.objects.filter(
                ville__affectationville__username_id=user_id
            ).order_by('nomentrepot').values('pk', 'nomentrepot'))
            cache.set(cache_key_entrepots, entrepots, 900)
        except Exception:
            entrepots = []

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
    uid = request.user.id
    P = request.POST.get

    # DataTables
    draw = int(P('draw', 1) or 1)
    start = max(int(P('start', 0) or 0), 0)
    length = min(max(int(P('length', 20) or 20), 1), 100)  # capped at 100 for performance

    def _s(k): return (P(k, '') or '').strip()
    def _has_min(v, n=2): return bool(v) and len(v) >= n

    # ✅ Prefer IDs from dropdowns
    frontiere_id = _s('frontiere_id')
    importateur_id = _s('importateur_id')
    entrepot_id = _s('entrepot_id')
    produit_id = _s('produit_id')

    # Also handle names if IDs are not sent
    f_name = _s('frontiere')
    i_name = _s('importateur')
    e_name = _s('entrepot')
    p_name = _s('produit')

    immat = _s('immatriculation')
    decl = _s('declaration')
    numd = _s('numdos')

    date_from = _s('date_from')
    date_to = _s('date_to')

    search_value = _s('search[value]')

    # Guard: require filters or long search (VERY IMPORTANT at 1M+)
    has_any_filter = any([
        frontiere_id, importateur_id, entrepot_id, produit_id,
        f_name, i_name, e_name, p_name,
        immat, decl, numd, date_from, date_to
    ])
    if not has_any_filter and not _has_min(search_value, 3):
        return JsonResponse({'draw': draw, 'recordsTotal': 0, 'recordsFiltered': 0, 'data': []})

    # Allowed entrepots (cached)
    ent_key = f"u:{uid}:allowed_entrepots"
    allowed_entrepots = cache.get(ent_key)
    if allowed_entrepots is None:
        allowed_entrepots = list(
            Entrepot.objects.filter(ville__affectationville__username_id=uid)
            .values_list('identrepot', flat=True)
        )
        cache.set(ent_key, allowed_entrepots, 900)

    if not allowed_entrepots:
        return JsonResponse({'draw': draw, 'recordsTotal': 0, 'recordsFiltered': 0, 'data': []})

    # recordsTotal = count of items restricted only by user scope (cached)
    records_total_key = f"shydro:total_count:{uid}"
    records_total = cache.get(records_total_key)
    if records_total is None:
        records_total = Cargaison.objects.filter(entrepot_id__in=allowed_entrepots).count()
        cache.set(records_total_key, records_total, 300)

    qs = Cargaison.objects.filter(entrepot_id__in=allowed_entrepots)

    # ✅ Date range without __date (index-friendly)
    def _parse_iso(d):
        try:
            return datetime.date.fromisoformat(d)
        except Exception:
            return None

    df = _parse_iso(date_from) if date_from else None
    dt = _parse_iso(date_to) if date_to else None

    # Enforce a default window if none provided (recommended)
    # if not df and not dt:
    #     df = timezone.localdate() - datetime.timedelta(days=30)

    if df:
        qs = qs.filter(dateheurecargaison__gte=datetime.datetime.combine(df, datetime.time.min))
    if dt:
        qs = qs.filter(dateheurecargaison__lte=datetime.datetime.combine(dt, datetime.time.max))

    # ✅ Exact match using denormalized names if IDs are missing (faster than joins)
    # However, if we have IDs, we should use them. 
    try:
        if frontiere_id and frontiere_id.isdigit():   qs = qs.filter(frontiere_id=int(frontiere_id))
        elif f_name:       qs = qs.filter(nom_frontiere__iexact=f_name)

        if importateur_id and importateur_id.isdigit(): qs = qs.filter(importateur_id=int(importateur_id))
        elif i_name:       qs = qs.filter(nom_importateur__iexact=i_name)

        if entrepot_id and entrepot_id.isdigit():    qs = qs.filter(entrepot_id=int(entrepot_id))
        elif e_name:       qs = qs.filter(nom_entrepot__iexact=e_name)

        if produit_id and produit_id.isdigit():     qs = qs.filter(produit_id=int(produit_id))
        elif p_name:       qs = qs.filter(nom_produit__iexact=p_name)
    except Exception:
        pass

    if immat: qs = qs.filter(immatriculation__istartswith=immat)
    if decl:  qs = qs.filter(declaration__istartswith=decl)
    if numd:
        s_num = str(numd).strip()
        if s_num:
            d_q = Q(numdossier__icontains=s_num) | Q(numreq__icontains=s_num)
            if s_num.isdigit():
                d_q |= Q(numdos=int(s_num))
            qs = qs.filter(d_q)

    # Search in denormalized fields
    if _has_min(search_value, 3):
        s = search_value
        search_q = Q(declaration__istartswith=s) | \
                   Q(immatriculation__istartswith=s) | \
                   Q(nom_importateur__istartswith=s) | \
                   Q(nom_entrepot__istartswith=s) | \
                   Q(nom_produit__istartswith=s) | \
                   Q(nom_frontiere__istartswith=s) | \
                   Q(numreq__istartswith=s)
        
        # Add numdos to search only if it's a digit to avoid crashes on integer fields
        if s.isdigit():
            search_q |= Q(numdos=int(s))
            
        qs = qs.filter(search_q)

    # ✅ Ordering: only by indexed local columns (avoid joins in ORDER BY)
    qs = qs.order_by('-dateheurecargaison', '-idcargaison')

    # ✅ Count (cache it briefly)
    cnt_key_payload = (
        df, dt, frontiere_id, importateur_id, entrepot_id, produit_id,
        f_name, i_name, e_name, p_name,
        immat, decl, numd, search_value
    )
    cnt_key = f"rep:cnt:{uid}:{hash(cnt_key_payload)}"
    records_filtered = cache.get(cnt_key)
    if records_filtered is None:
        records_filtered = qs.count()
        cache.set(cnt_key, records_filtered, 60)

    # Page IDs
    page_ids = list(qs.values_list('idcargaison', flat=True)[start:start+length])
    if not page_ids:
        return JsonResponse({'draw': draw, 'recordsTotal': records_total, 'recordsFiltered': records_filtered, 'data': []})

    # Heavy aggregates only on the page (OK)
    page_rows = (
        Cargaison.objects
        .filter(idcargaison__in=page_ids)
        .values(
            'idcargaison','numdos','declaration',
            'nom_frontiere', 'nom_entrepot', 'nom_importateur',
            'immatriculation', 'nom_produit',
            'dateheurecargaison','volume',
            'densite_inspection', 'temperature_inspection',
            'gov_total', 'gsv_total', 'mta_total', 'mtv_total',
            'date_echantillon', 'date_reception_labo', 'date_analyse', 'date_inspection',
            'requisitiondackdate', 'dateDechargement'
        )
    )

    # Keep same order as page_ids
    idx = {cid: i for i, cid in enumerate(page_ids)}
    rows_raw = list(page_rows)
    
    # Map denormalized fields to expected output keys for DataTables
    data = []
    for r in rows_raw:
        def _d(dt): return dt.strftime('%d/%m/%Y') if dt else ''
        
        gov = r.get('gov_total') or 0
        gsv = r.get('gsv_total') or 0
        vcf = round(gsv / gov, 4) if gov > 0 else ''

        data.append({
            'idcargaison': r['idcargaison'],
            'numdos': r['numdos'] or '',
            'declaration': r['declaration'] or '',
            'frontiere__nomville': r['nom_frontiere'] or '',
            'entrepot__nomentrepot': r['nom_entrepot'] or '',
            'importateur__nomimportateur': r['nom_importateur'] or '',
            'immatriculation': r['immatriculation'] or '',
            'produit__nomproduit': r['nom_produit'] or '',
            'dateheurecargaison': r['dateheurecargaison'],
            'date_entree_display': _d(r['dateheurecargaison']),
            'volume': r['volume'] or '',
            'inspection__dens': r['densite_inspection'] or '',
            'densite15': r['densite_inspection'] or '',
            'inspection__temp': r['temperature_inspection'] or '',
            'volConst': gov,
            'vol_jauge': gov,
            'gsvT': gsv,
            'gsv': gsv,
            'mtaT': r['mta_total'] or 0,
            'mta': r['mta_total'] or 0,
            'mtvT': r['mtv_total'] or 0,
            'mtv': r['mtv_total'] or 0,
            'vcf': vcf,
            'date_echantillon': r['date_echantillon'],
            'date_echant_display': _d(r['date_echantillon']),
            'date_reception_labo': r['date_reception_labo'],
            'date_recep_labo_display': _d(r['date_reception_labo']),
            'date_analyse': r['date_analyse'],
            'date_analyse_display': _d(r['date_analyse']),
            'date_inspection': r['date_inspection'],
            'date_inspection_display': _d(r['date_inspection']),
            'date_requisition_display': _d(r['requisitiondackdate']),
            'date_dechargement_display': _d(r['dateDechargement']),
        })

    rows = sorted(data, key=lambda r: idx.get(r['idcargaison'], 10**9))

    return JsonResponse({
        'draw': draw,
        'recordsTotal': records_total,
        'recordsFiltered': records_filtered,
        'data': rows,
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

        # Scope options strictly to the current user's perimeter using Cargaison
        from enreg.models import Cargaison
        base = Cargaison.objects.filter(
            entrepot__ville__affectationville__username_id=user_id
        )

        # FRONTIÈRES visibles
        frontieres = []
        for v in (base
                  .exclude(nom_frontiere__isnull=True)
                  .values('frontiere_id', 'nom_frontiere')
                  .order_by('nom_frontiere')
                  .distinct()):
            frontieres.append({
                'id': v['frontiere_id'],
                'label': v['nom_frontiere'],
                'value': v['nom_frontiere'],
            })

        # IMPORTATEURS visibles
        fournisseurs = []
        for i in (base
                  .exclude(nom_importateur__isnull=True)
                  .values('importateur_id', 'nom_importateur')
                  .order_by('nom_importateur')
                  .distinct()):
            fournisseurs.append({
                'id': i['importateur_id'],
                'label': i['nom_importateur'],
                'value': i['nom_importateur'],
            })

        # ENTREPÔTS visibles
        entrepots = []
        for e in (base
                  .exclude(nom_entrepot__isnull=True)
                  .values('entrepot_id', 'nom_entrepot')
                  .order_by('nom_entrepot')
                  .distinct()):
            entrepots.append({
                'id': e['entrepot_id'],
                'label': e['nom_entrepot'],
                'value': e['nom_entrepot'],
            })

        # PRODUITS visibles
        produits = []
        for p in (base
                  .exclude(nom_produit__isnull=True)
                  .values('produit_id', 'nom_produit')
                  .order_by('nom_produit')
                  .distinct()):
            produits.append({
                'id': p['produit_id'],
                'label': p['nom_produit'],
                'value': p['nom_produit'],
            })

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


from django.views.decorators.http import require_POST, require_GET


@login_required(login_url='login')
@require_POST
def filterOptionsRapportActiviteAll(request):
    """
    JSON endpoint to populate Filters modal dropdowns for Rapport d'activités (GLOBAL scope).
    Returns ALL available values in the database (not restricted to user's city/perimeter),
    but still derived from existing Cargaison relations to keep only meaningful options.
    Response schema matches the scoped endpoint: { frontieres, fournisseurs, entrepots, produits }
    where each item is { id, label, value } and lists are sorted A–Z.
    """
    try:
        from django.core.cache import cache
        from enreg.models import Cargaison

        cache_key = "rapport_activ:filters:all"
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse(cached)

        base = Cargaison.objects.all()

        # FRONTIÈRES (global)
        frontieres = []
        for v in (base
                  .exclude(nom_frontiere__isnull=True)
                  .values('frontiere_id', 'nom_frontiere')
                  .order_by('nom_frontiere')
                  .distinct()):
            frontieres.append({
                'id': v['frontiere_id'],
                'label': v['nom_frontiere'],
                'value': v['nom_frontiere'],
            })

        # IMPORTATEURS (global)
        fournisseurs = []
        for i in (base
                  .exclude(nom_importateur__isnull=True)
                  .values('importateur_id', 'nom_importateur')
                  .order_by('nom_importateur')
                  .distinct()):
            fournisseurs.append({
                'id': i['importateur_id'],
                'label': i['nom_importateur'],
                'value': i['nom_importateur'],
            })

        # ENTREPÔTS (global)
        entrepots = []
        for e in (base
                  .exclude(nom_entrepot__isnull=True)
                  .values('entrepot_id', 'nom_entrepot')
                  .order_by('nom_entrepot')
                  .distinct()):
            entrepots.append({
                'id': e['entrepot_id'],
                'label': e['nom_entrepot'],
                'value': e['nom_entrepot'],
            })

        # PRODUITS (global)
        produits = []
        for p in (base
                  .exclude(nom_produit__isnull=True)
                  .values('produit_id', 'nom_produit')
                  .order_by('nom_produit')
                  .distinct()):
            produits.append({
                'id': p['produit_id'],
                'label': p['nom_produit'],
                'value': p['nom_produit'],
            })

        payload = {
            'frontieres': frontieres,
            'fournisseurs': fournisseurs,
            'entrepots': entrepots,
            'produits': produits,
        }
        # Cache globally for 1 hour
        cache.set(cache_key, payload, timeout=3600)
        return JsonResponse(payload)
    except Exception as exc:
        return JsonResponse({'error': 'Failed to load global filter options', 'detail': str(exc)}, status=500)



@login_required(login_url='login')
def startRapportActiviteExport(request):
    """
    Start async export of Rapport d'activités using current filters/search/order.
    Optimized to handle multiple formats and consolidate extraction logic.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    return _handle_rapport_export(request, version=1)


@login_required(login_url='login')
def startRapportActiviteExportV2(request):
    """
    Variante qui applique automatiquement le filtre « Entrepôt dans la ville (Entité) » côté serveur.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    return _handle_rapport_export(request, version=2)


def _handle_rapport_export(request, version=1):
    user_id = request.user.id
    try:
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except Exception:
            payload = {}

        # Use common helper for parameter normalization
        def P(key, default=''):
            return (payload.get(key) or request.POST.get(key) or request.GET.get(key) or default)

        search_val = (payload.get('search', {}) or {}).get('value') or payload.get('search_value') or request.POST.get('search[value]') or ''
        
        frontiere_val = P('frontiere')
        entite_val = P('entite')
        
        if version == 2 and not frontiere_val and entite_val:
            frontiere_val = entite_val

        params = {
            'search[value]': str(search_val).strip(),
            'date_from': P('date_from'),
            'date_to': P('date_to'),
            'frontiere_id': P('frontiere_id') or P('frontiere'),
            'entite': entite_val,
            'importateur_id': P('importateur_id') or P('importateur'),
            'entrepot_id': P('entrepot_id') or P('entrepot'),
            'produit_id': P('produit_id') or P('produit'),
            'immatriculation': P('immatriculation'),
            'declaration': P('declaration'),
            'numdos': P('numdos'),
            'order': payload.get('order') or [],
        }

        if version == 2 and params.get('frontiere') and not params.get('entrepot'):
            try:
                from enreg.models import Entrepot
                ville_id = int(params['frontiere'])
                params['entrepot_ids'] = list(Entrepot.objects.filter(ville__idville=ville_id).values_list('identrepot', flat=True))
            except Exception:
                pass

        from shydro.tasks import export_rapport_activites_task
        res = export_rapport_activites_task.delay(params, user_id)
        return JsonResponse({'task_id': res.id})
    except Exception as exc:
        return JsonResponse({'error': f'Failed to start export (v{version})', 'detail': str(exc)}, status=500)



@login_required(login_url='login')
def regularisation(request):
    """
    Optimized regularisation view with efficient QuerySet and pre-signed scoping.
    Uses select_related to avoid N+1 queries during table rendering and form initialization.
    """
    user_id = request.user.id
    template = 'regularisation.html'

    # 1. Resolve allowed entrepôts for this user once (avoids heavy joins in each request)
    # Reusing the same caching pattern as in regularisation_response for consistency
    cache_key_ent = f"u:{user_id}:allowed_entrepots"
    allowed_entrepots = cache.get(cache_key_ent)
    if allowed_entrepots is None:
        try:
            allowed_entrepots = list(
                Entrepot.objects.filter(
                    ville__affectationville__username_id=user_id
                ).values_list('identrepot', flat=True)
            )
        except Exception:
            allowed_entrepots = []
        cache.set(cache_key_ent, allowed_entrepots, 15 * 60)

    # 2. Optimized QuerySet with select_related
    # We prefetch all foreign keys used in the Regularisation table and potentially in forms
    qs = Cargaison.objects.filter(
        entrepot_id__in=allowed_entrepots if allowed_entrepots else []
    ).filter(
        Q(etat='En attente requisition') | Q(etat="En attente d'echantillonage")
    ).select_related(
        'importateur', 'entrepot', 'produit', 'frontiere'
    ).order_by('-dateheurecargaison')

    # 3. Forms Initialization
    # We only initialize forms that are actually rendered via Django templates/crispy.
    # Others (re-orientation, transbordement, etc.) are handled via manual HTML/JS in partials.
    form3 = ImportateurRegularisationForm()
    form4 = EntrepotRegularisationForm()
    form5 = RegularisationNouvelleEntree()

    table = Regularisation(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)

    context = {
        'table': table,
        'form3': form3,
        'form4': form4,
        'form5': form5,
    }
    return render(request, template, context)




@login_required(login_url='login')
@require_POST
def regularisation_response(request):
    """
    Optimized POST-only JSON response for Regularisation DataTable.
    Leverages indexed fields and caching for scalability.
    """
    user_id = request.user.id

    # 1. Resolve allowed entrepôts for this user once and cache (avoids heavy joins)
    cache_key_ent = f"u:{user_id}:allowed_entrepots"
    allowed_entrepots = cache.get(cache_key_ent)
    if allowed_entrepots is None:
        try:
            allowed_entrepots = list(
                Entrepot.objects.filter(
                    ville__affectationville__username_id=user_id
                ).values_list('identrepot', flat=True)
            )
        except Exception:
            allowed_entrepots = []
        cache.set(cache_key_ent, allowed_entrepots, 15 * 60)

    # 2. Base queryset (restricted to user + specific etat values)
    # Using entrepot_id__in is efficient once allowed_entrepots is resolved.
    base_qs = Cargaison.objects.filter(
        entrepot_id__in=allowed_entrepots if allowed_entrepots else []
    ).filter(
        Q(etat='En attente requisition') | Q(etat="En attente d'echantillonage")
    )

    # 3. Read and normalize filters
    params = request.POST
    flt_date_from = (params.get('flt_date_from') or '').strip()
    flt_date_to = (params.get('flt_date_to') or '').strip()
    flt_frontiere = (params.get('flt_frontiere') or '').strip()
    flt_importateur = (params.get('flt_importateur') or '').strip()
    flt_entrepot = (params.get('flt_entrepot') or '').strip()
    flt_produit = (params.get('flt_produit') or '').strip()
    flt_immat = (params.get('flt_immat') or '').strip()
    flt_declaration = (params.get('flt_declaration') or '').strip()
    flt_numdos = (params.get('flt_numdos') or '').strip()
    search_value = (params.get('search[value]') or '').strip()

    # Function to check for meaningful search/filter input
    def _has_min(s: str, n: int = 2) -> bool:
        return bool(s) and len(s) >= n

    # Guard: Return empty if no filters and no valid global search (Original UX requirement)
    has_any_filter = any([
        flt_date_from, flt_date_to, flt_frontiere, flt_importateur,
        flt_entrepot, flt_produit, flt_immat, flt_declaration, flt_numdos
    ])
    if not has_any_filter and not _has_min(search_value):
        try:
            draw_val = int(params.get('draw', 1) or 1)
        except Exception:
            draw_val = 1
        return JsonResponse({
            'data': [],
            'draw': draw_val,
            'recordsTotal': 0,
            'recordsFiltered': 0,
        })

    # 4. Apply domain-specific filters (Optimized for index usage)
    if flt_date_from:
        try:
            dt_from = datetime.datetime.strptime(flt_date_from, '%Y-%m-%d').date()
            base_qs = base_qs.filter(dateheurecargaison__gte=datetime.datetime.combine(dt_from, datetime.time.min))
        except Exception: pass
    if flt_date_to:
        try:
            dt_to = datetime.datetime.strptime(flt_date_to, '%Y-%m-%d').date()
            base_qs = base_qs.filter(dateheurecargaison__lte=datetime.datetime.combine(dt_to, datetime.time.max))
        except Exception: pass

    # Use istartswith for indexed/high-cardinality fields where possible
    if _has_min(flt_frontiere):
        base_qs = base_qs.filter(nom_frontiere__istartswith=flt_frontiere)
    if _has_min(flt_importateur):
        base_qs = base_qs.filter(nom_importateur__istartswith=flt_importateur)
    if _has_min(flt_entrepot):
        base_qs = base_qs.filter(nom_entrepot__istartswith=flt_entrepot)
    if _has_min(flt_produit):
        base_qs = base_qs.filter(nom_produit__istartswith=flt_produit)
    if _has_min(flt_immat):
        base_qs = base_qs.filter(immatriculation__istartswith=flt_immat)
    if _has_min(flt_declaration):
        base_qs = base_qs.filter(declaration__istartswith=flt_declaration)
    if _has_min(flt_numdos):
        # numdos is an indexed integer field in our optimized models, but often filtered as string
        base_qs = base_qs.filter(numdos__istartswith=flt_numdos)

    # 5. recordsTotal (Count after domain filters, cached)
    try:
        total_cache_payload = {
            'u': user_id, 'df': flt_date_from, 'dt': flt_date_to, 'fr': flt_frontiere,
            'impt': flt_importateur, 'ent': flt_entrepot, 'prd': flt_produit,
            'imm': flt_immat, 'dec': flt_declaration, 'dos': flt_numdos,
        }
        total_key = 'reg:tot:' + hashlib.md5(json.dumps(total_cache_payload, sort_keys=True).encode()).hexdigest()
        records_total = cache.get(total_key)
        if records_total is None:
            records_total = base_qs.count()
            cache.set(total_key, records_total, 120)
    except Exception:
        records_total = base_qs.count()

    # 6. Global Search (Optimized to use denormalized indexed fields and avoid JOINs)
    if _has_min(search_value):
        base_qs = base_qs.filter(
            Q(immatriculation__istartswith=search_value) |
            Q(declaration__istartswith=search_value) |
            Q(nom_importateur__istartswith=search_value) |
            Q(nom_entrepot__istartswith=search_value) |
            Q(nom_produit__istartswith=search_value) |
            Q(nom_frontiere__istartswith=search_value) |
            Q(numdos__istartswith=search_value)
        )

    # 7. recordsFiltered (Count after global search, cached)
    try:
        filtered_cache_payload = {**total_cache_payload, 'q': search_value}
        filtered_key = 'reg:fil:' + hashlib.md5(json.dumps(filtered_cache_payload, sort_keys=True).encode()).hexdigest()
        records_filtered = cache.get(filtered_key)
        if records_filtered is None:
            records_filtered = base_qs.count()
            cache.set(filtered_key, records_filtered, 120)
    except Exception:
        records_filtered = base_qs.count()

    # 8. Paging and Ordering
    try:
        draw = int(params.get('draw', 1) or 1)
        start = int(params.get('start', 0) or 0)
        length = int(params.get('length', 15) or 15)
    except Exception:
        draw, start, length = 1, 0, 15

    # Always order by dateheurecargaison for consistency in regularisation
    qs_final = base_qs.order_by('-dateheurecargaison')

    # 9. Efficient Data Fetching with .values()
    # Minimizes memory usage and prevents object instantiation overhead.
    rows_qs = qs_final.values(
        'dateheurecargaison',
        'nom_frontiere',
        'nom_importateur',
        'nom_entrepot',
        'nom_produit',
        'volume',
        'immatriculation',
        'declaration',
        'idcargaison'
    )[start:start + max(length, 1)]

    data = []
    for r in rows_qs:
        dt = r.get('dateheurecargaison')
        # Format date for display matching expected front-end key 'dateheurecargaison__date'
        date_display = dt.strftime('%d/%m/%Y') if dt else ''
        
        # Build response with keys matching DataTables 'columns' in regularisation.html
        data.append({
            'dateheurecargaison__date': date_display,
            'frontiere__nomville': r['nom_frontiere'] or '',
            'importateur__nomimportateur': r['nom_importateur'] or '',
            'entrepot__nomentrepot': r['nom_entrepot'] or '',
            'produit__nomproduit': r['nom_produit'] or '',
            'volume': r['volume'] if r['volume'] is not None else '',
            'immatriculation': r['immatriculation'] or '',
            'declaration': r['declaration'] or '',
            'idcargaison': r['idcargaison']
        })

    return JsonResponse({
        'data': data,
        'draw': draw,
        'recordsTotal': records_total,
        'recordsFiltered': records_filtered,
    })



@login_required(login_url='login')
@require_GET
def regularisation_filter_options(request):
    """
    Returns dropdown options for Regularisation page.
    Optimized for large datasets using scoping and caching.
    """
    user_id = request.user.id
    cache_key = f"reg:opts:{user_id}"
    
    # 1. Try to return from cache first
    cached_payload = cache.get(cache_key)
    if cached_payload:
        t = (request.GET.get('type') or '').strip().lower()
        if t in {"frontiere", "importateur", "entrepot", "produit"}:
            mapping = {
                "frontiere": "frontieres",
                "importateur": "fournisseurs",
                "entrepot": "entrepots",
                "produit": "produits"
            }
            return JsonResponse({"items": cached_payload.get(mapping[t], [])})
        return JsonResponse(cached_payload)

    try:
        from enreg.models import Cargaison, Entrepot

        try:
            _limit = int(request.GET.get('limit') or 300)
        except Exception:
            _limit = 300

        # Optimization: Resolve allowed entrepôts once (avoids heavy joins in each subquery)
        allowed_entrepots = list(
            Entrepot.objects.filter(
                # ville__affectationville__username_id=user_id
            ).values_list('identrepot', flat=True)
        )
        
        if not allowed_entrepots:
            return JsonResponse({
                "frontieres": [], "fournisseurs": [], "entrepots": [], "produits": []
            })

        base = Cargaison.objects.filter(entrepot_id__in=allowed_entrepots)

        # Build all lists using efficient .values() and distinct()
        frontieres = list(
            base.exclude(frontiere__nomville__isnull=True)
                .exclude(frontiere__nomville='')
                .values('frontiere__idville', 'frontiere__nomville')
                .annotate(id=F('frontiere__idville'), label=F('frontiere__nomville'))
                .values('id', 'label')
                .order_by('label')
                .distinct()[:_limit]
        )

        fournisseurs = list(
            base.exclude(importateur__nomimportateur__isnull=True)
                .exclude(importateur__nomimportateur='')
                .values('importateur__idimportateur', 'importateur__nomimportateur')
                .annotate(id=F('importateur__idimportateur'), label=F('importateur__nomimportateur'))
                .values('id', 'label')
                .order_by('label')
                .distinct()[:_limit]
        )

        entrepots = list(
            base.exclude(entrepot__nomentrepot__isnull=True)
                .exclude(entrepot__nomentrepot='')
                .values('entrepot__identrepot', 'entrepot__nomentrepot', 'entrepot__ville_id')
                .annotate(id=F('entrepot__identrepot'), label=F('entrepot__nomentrepot'), ville_id=F('entrepot__ville_id'))
                .values('id', 'label', 'ville_id')
                .order_by('label')
                .distinct()[:_limit]
        )

        produits = list(
            base.exclude(produit__nomproduit__isnull=True)
                .exclude(produit__nomproduit='')
                .values('produit__idproduit', 'produit__nomproduit')
                .annotate(id=F('produit__idproduit'), label=F('produit__nomproduit'))
                .values('id', 'label')
                .order_by('label')
                .distinct()[:_limit]
        )

        payload = {
            "frontieres": frontieres,
            "fournisseurs": fournisseurs,
            "entrepots": entrepots,
            "produits": produits,
        }

        # Cache the full payload for 15 minutes
        cache.set(cache_key, payload, 15 * 60)

        t = (request.GET.get('type') or '').strip().lower()
        if t in {"frontiere", "importateur", "entrepot", "produit"}:
            mapping = {
                "frontiere": "frontieres",
                "importateur": "fournisseurs",
                "entrepot": "entrepots",
                "produit": "produits"
            }
            return JsonResponse({"items": payload.get(mapping[t], [])})

        return JsonResponse(payload)

    except Exception as exc:
        return JsonResponse(
            {"error": "Failed to load filter options", "detail": str(exc)},
            status=500
        )




@login_required(login_url='login')
@require_GET
def importateur_options_all(request):
    """
    Return an unfiltered list of all importateurs for the CORRECTION FOURNISSEUR modal.
    Response: { "items": [ {"id": idimportateur, "label": nomimportateur}, ... ] }
    Uses caching for performance on large datasets.
    """
    cache_key = "shydro:importateurs_all_list"
    items = cache.get(cache_key)

    if items is None:
        try:
            from enreg.models import Importateur
            try:
                _limit = int(request.GET.get('limit') or 2000)
            except Exception:
                _limit = 2000

            # Fetch only needed fields and map them in one pass
            items = list(
                Importateur.objects
                .exclude(nomimportateur__isnull=True)
                .exclude(nomimportateur__exact='')
                .order_by('nomimportateur')
                .values('idimportateur', 'nomimportateur')[:_limit]
            )
            # Rename keys to match expected format: id, label
            items = [{"id": r['idimportateur'], "label": r['nomimportateur']} for r in items]
            
            # Cache for 15 minutes
            cache.set(cache_key, items, 15 * 60)
        except Exception as exc:
            return JsonResponse({"error": "Failed to load importateurs", "detail": str(exc)}, status=500)

    return JsonResponse({"items": items})


@login_required(login_url='login')
@require_GET
def produit_options_all(request):
    """
    Return an unfiltered list of all produits for the CORRECTION NATURE PRODUIT modal.
    Response: { "items": [ {"id": idproduit, "label": nomproduit}, ... ] }
    Uses caching for performance on large datasets.
    """
    cache_key = "shydro:produits_all_list"
    items = cache.get(cache_key)

    if items is None:
        try:
            # Try known locations for Produit model
            try:
                from enreg.models import Produit  # type: ignore
            except Exception:
                try:
                    from hydrocarbures.models import Produit  # type: ignore
                except Exception:
                    Produit = None  # type: ignore

            if Produit is None:
                return JsonResponse({"error": "Produit model not found"}, status=500)

            try:
                _limit = int(request.GET.get('limit') or 1000)
            except Exception:
                _limit = 1000

            items = list(
                Produit.objects
                .exclude(nomproduit__isnull=True)
                .exclude(nomproduit__exact='')
                .order_by('nomproduit')
                .values('idproduit', 'nomproduit')[:_limit]
            )
            # Rename keys to match expected format: id, label
            items = [{"id": r['idproduit'], "label": r['nomproduit']} for r in items]
            
            # Cache for 15 minutes
            cache.set(cache_key, items, 15 * 60)
        except Exception as exc:
            return JsonResponse({"error": "Failed to load produits", "detail": str(exc)}, status=500)

    return JsonResponse({"items": items})



@login_required(login_url='login')
def regularisationDestination(request):
    """
    Update cargo destination (entrepot).
    Ensures data consistency and handles city mismatch with confirmation.
    """
    user = request.user
    if request.method != 'POST' or request.META.get('HTTP_X_REQUESTED_WITH') != 'XMLHttpRequest':
        return redirect('regularisation')

    pk = request.POST.get('pk')
    nouvelle_destination_id = request.POST.get('nouvelleDestination')
    confirm = request.POST.get('confirm')

    if not pk or not nouvelle_destination_id:
        return JsonResponse({'status': 'error', 'message': 'Paramètres manquants.'}, status=400)

    try:
        with transaction.atomic():
            # Lock the record for update to handle concurrent changes
            cargaison = Cargaison.objects.select_for_update().select_related('entrepot').get(idcargaison=pk)
            entrepot = Entrepot.objects.select_related('ville').get(identrepot=nouvelle_destination_id)

            # Check user's assigned city
            try:
                affectation = AffectationVille.objects.select_related('ville').get(username=user)
                user_ville_id = affectation.ville_id
            except AffectationVille.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Utilisateur non affecté à une ville.'}, status=403)

            if user_ville_id != entrepot.ville_id:
                if not confirm:
                    return JsonResponse({
                        'status': 'warning',
                        'message': "La ville de la nouvelle destination ne correspond pas à votre ville assignée. Confirmez-vous ?"
                    })

            cargaison.entrepot = entrepot
            cargaison.save(update_fields=['entrepot', 'nom_entrepot'])

            UserActivityLog.objects.create(
                user=user,
                action="Regularisation: Change Destination",
                description=f"Cargaison {pk} moved to Entrepot {entrepot.nomentrepot} ({entrepot.ville.nomville})"
            )

        return JsonResponse({'status': 'success'})

    except Cargaison.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Cargaison introuvable.'}, status=404)
    except Entrepot.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Nouvel entrepôt introuvable.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Erreur: {str(e)}'}, status=500)


@login_required(login_url='login')
def transbordement(request):
    """
    Update cargo immatriculation and volume.
    Atomic and multi-user safe.
    """
    user = request.user
    if request.method != 'POST' or request.META.get('HTTP_X_REQUESTED_WITH') != 'XMLHttpRequest':
        return redirect('regularisation')

    pk = request.POST.get('pk')
    nouvelle_immatriculation = (request.POST.get('nouvelleImmatriculation') or '').strip()
    nouveau_volume = request.POST.get('nouveauVolume')

    if not pk:
        return JsonResponse({'status': 'error', 'message': 'ID cargaison manquant.'}, status=400)

    try:
        with transaction.atomic():
            cargaison = Cargaison.objects.select_for_update().get(idcargaison=pk)
            
            old_immat = cargaison.immatriculation
            old_vol = cargaison.volume

            if nouvelle_immatriculation:
                cargaison.immatriculation = nouvelle_immatriculation
            
            if nouveau_volume is not None:
                try:
                    cargaison.volume = float(nouveau_volume)
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Volume invalide.'}, status=400)

            cargaison.save(update_fields=['immatriculation', 'volume'])

            UserActivityLog.objects.create(
                user=user,
                action="Regularisation: Transbordement",
                description=f"Cargaison {pk}: Immat {old_immat}->{cargaison.immatriculation}, Vol {old_vol}->{cargaison.volume}"
            )

        return JsonResponse({'status': 'success'})

    except Cargaison.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Cargaison introuvable.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Erreur: {str(e)}'}, status=500)



@login_required(login_url='login')
@require_POST
def changementNature(request):
    """
    Update cargo product type.
    Atomic, multi-user safe, and includes activity logging.
    """
    user = request.user
    # Optional: align with your other endpoints (only allow some roles)
    # role = getattr(user, "role_id", None)
    # if role not in (1, 4, 5, 7, ): # Added role 7 (Hydro admin/op) if applicable
    #     return JsonResponse(
    #         {"status": "error", "message": "Accès refusé."},
    #         status=403
    #     )

    # Must be AJAX for this flow
    if request.META.get('HTTP_X_REQUESTED_WITH') != 'XMLHttpRequest':
        return redirect('regularisation')

    pk = (request.POST.get('pk') or '').strip()
    produit_id = (request.POST.get('produit_id') or '').strip()
    # remarks = (request.POST.get('remarks') or '').strip() # Unused for now

    if not pk or not produit_id:
        return JsonResponse({"status": "error", "message": "Paramètres manquants (pk ou produit_id)."}, status=400)

    try:
        with transaction.atomic():
            # select_for_update handles concurrency
            cargaison = Cargaison.objects.select_for_update().select_related('produit').get(idcargaison=pk)
            nouveau_produit = Produit.objects.get(idproduit=produit_id)

            old_produit_name = cargaison.produit.nomproduit if cargaison.produit else "N/A"
            
            if cargaison.produit_id != int(produit_id):
                cargaison.produit = nouveau_produit
                cargaison.save(update_fields=['produit', 'nom_produit'])

                UserActivityLog.objects.create(
                    user=user,
                    action="Regularisation: Change Product",
                    description=f"Cargaison {pk}: Product changed from {old_produit_name} to {nouveau_produit.nomproduit}"
                )

        return JsonResponse({
            "status": "success",
            "message": "Nature du produit mise à jour avec succès."
        })

    except Cargaison.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Cargaison introuvable."}, status=404)
    except Produit.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Produit introuvable."}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Erreur serveur: {str(e)}"}, status=500)



@login_required(login_url='login')
def del_record(request):
    """
    Delete a cargo record.
    Requires AJAX, confirmation code, and is multi-user safe.
    """
    user = request.user
    if request.method != 'POST' or request.META.get('HTTP_X_REQUESTED_WITH') != 'XMLHttpRequest':
        return redirect('regularisation')

    pk = request.POST.get('pk')
    confirm_code = (request.POST.get('confirm_code') or '').strip()

    # ✅ Server-side expected code
    expected_code = str(getattr(settings, 'DELETE_CONFIRMATION_CODE', '1234')).strip()

    if not pk:
        return JsonResponse({'status': 'error', 'message': 'PK manquant.'}, status=400)

    if confirm_code != expected_code:
        return JsonResponse({'status': 'error', 'message': 'Code de confirmation incorrect.'}, status=400)

    try:
        with transaction.atomic():
            # Use select_for_update to ensure we have an exclusive lock before deletion
            cargaison = Cargaison.objects.select_for_update().get(idcargaison=pk)
            
            # Log before deletion
            UserActivityLog.objects.create(
                user=user,
                action="Regularisation: Delete Record",
                description=f"Cargaison {pk} (Immat: {cargaison.immatriculation}, Dossier: {cargaison.numdos}) deleted by {user.username}"
            )
            
            cargaison.delete()

        return JsonResponse({'status': 'success'})

    except Cargaison.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Enregistrement introuvable.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Erreur: {str(e)}'}, status=500)



def checkExportTaskStatus(request, task_id):
    """
    Poll a Celery task and return a compact JSON status.

    Returns:
      { state: PENDING|PROGRESS|SUCCESS|FAILURE,
        progress: number|null,    # 0..100 when available
        meta: {...}|null,         # raw task meta when in PROGRESS
        result: {...}|null,       # task result on SUCCESS
        error: string|null }      # error on FAILURE
    """
    task = AsyncResult(task_id, app=app)

    state = task.state or 'PENDING'

    # Default payload
    payload = {
        'state': state,
        'progress': None,
        'meta': None,
        'result': None,
        'error': None,
    }

    if state == 'PENDING':
        # Task is waiting to be picked or no progress provided yet
        payload['progress'] = 0
    elif state == 'PROGRESS':
        meta = task.info or {}
        percent = None
        try:
            percent = float(meta.get('percent')) if meta and 'percent' in meta else None
        except Exception:
            percent = None
        payload['meta'] = meta
        payload['progress'] = percent
    elif state == 'SUCCESS':
        try:
            result_value = task.get()
        except Exception as exc:
            result_value = None
            payload['error'] = str(exc)
            payload['state'] = 'FAILURE'
        else:
            payload['result'] = result_value
            payload['progress'] = 100
    elif state == 'FAILURE':
        # Include error details when possible
        payload['error'] = str(task.result)

    return JsonResponse(payload)



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

        # Filter-first policy: if no valid filter branch matched above,
        # render page with filters only (no table data).
        return render(request, template, { 'form': form })


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
@require_POST
def changementImportateur(request):
    # Only accept AJAX calls (your frontend uses $.ajax)
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return redirect('regularisation')

    pk = (request.POST.get('pk') or '').strip()
    nouvel_importateur = (request.POST.get('importateur_id') or '').strip()
    remarks = (request.POST.get('remarks') or '').strip()  # optional, stored only if you have a field

    if not pk:
        return JsonResponse({'status': 'error', 'message': 'Aucune cargaison sélectionnée.'}, status=400)

    if not nouvel_importateur:
        return JsonResponse({'status': 'error', 'message': 'Veuillez sélectionner un fournisseur.'}, status=400)

    try:
        cargaison = Cargaison.objects.get(idcargaison=pk)
    except Cargaison.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Cargaison introuvable.'}, status=404)

    try:
        imp = Importateur.objects.get(idimportateur=nouvel_importateur)
    except Importateur.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Fournisseur introuvable.'}, status=404)

    # update
    cargaison.importateur = imp

    # If you actually have a "remarks" field in Cargaison, you can save it:
    # if hasattr(cargaison, 'remarks'):
    #     cargaison.remarks = remarks

    cargaison.save(update_fields=['importateur', 'nom_importateur'])

    return JsonResponse({
        'status': 'success',
        'message': 'Fournisseur (importateur) mis à jour avec succès.'
    })



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
        pdf_content = render_to_pdf_content(template, data)
        if pdf_content:
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            return JsonResponse({'status': 'success', 'pdf_base64': pdf_base64})
        else:
            return JsonResponse({'status': 'error', 'message': 'Erreur de génération PDF'})
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
        pdf_content = render_to_pdf_content(template, data)
        if pdf_content:
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            return JsonResponse({'status': 'success', 'pdf_base64': pdf_base64})
        else:
            return JsonResponse({'status': 'error', 'message': 'Erreur de génération PDF'})
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

    # Cache dashboard metrics for 5 minutes per user
    cache_key = f"hydro_dashboard_metrics_{user_id}_{current_year}"
    context = cache.get(cache_key)

    if context is None:
        base = Cargaison.objects.filter(
            entrepot__ville__affectationville__username_id=user_id
        )
        year_qs = base.filter(dateheurecargaison__year=current_year)

        # 1. Main Aggregates
        agg = year_qs.aggregate(
            e=Count('idcargaison', filter=Q(etat="En attente d'echantillonage")),
            l=Count('idcargaison', filter=Q(etat="Analyse Labo en cours")),
            p=Count('idcargaison', filter=Q(etat="Echantillonner")),
            i=Count('idcargaison', filter=Q(etatInspection=True)),
            c=Count('idcargaison'),

            gasoilVolume=Coalesce(Sum('volume', filter=Q(produit_id=2)), Value(0.0)),
            mogasVolume=Coalesce(Sum('volume', filter=Q(produit_id=1)), Value(0.0)),
            jetVolume=Coalesce(Sum('volume', filter=Q(produit_id=3)), Value(0.0)),
            petroleVolume=Coalesce(Sum('volume', filter=Q(produit_id=4)), Value(0.0)),
            totalVolume=Coalesce(Sum('volume'), Value(0.0)),
        )

        # 2. Impression Aggregates (use ID list from year_qs to avoid heavy subquery joins)
        # However, for large datasets, year_qs.values('idcargaison') might still be large.
        # Let's use it as a subquery, which Django handles reasonably well.
        imp_agg = ImpressionResultat.objects.filter(
            idcargaison__in=year_qs.values('idcargaison')
        ).aggregate(
            d=Count('idImpression', filter=Q(idcargaison__etat="Conforme aux exigences")),
            n=Count('idImpression', filter=Q(isConforme=False, control=False)),
        )

        tv = float(agg['totalVolume'] or 0.0)
        def pct(x):
            x = float(x or 0.0)
            return round((x/tv)*100) if tv else 0

        gasoil_v = float(agg['gasoilVolume'] or 0.0)
        mogas_v = float(agg['mogasVolume'] or 0.0)
        jet_v = float(agg['jetVolume'] or 0.0)
        petrole_v = float(agg['petroleVolume'] or 0.0)
        total_v = float(agg['totalVolume'] or 0.0)

        context = {
            'e': agg['e'], 'l': agg['l'], 'p': agg['p'], 'i': agg['i'], 'c': agg['c'],
            'd': imp_agg['d'], 'n': imp_agg['n'],
            'gasoilVolume': f"{gasoil_v}",
            'mogasVolume':  f"{mogas_v}",
            'jetVolume':    f"{jet_v}",
            'petroleVolume':f"{petrole_v}",
            'totalVolume':  f"{total_v}",
            'gasoilPercentage':  pct(gasoil_v),
            'mogasPercentage':   pct(mogas_v),
            'jetPercentage':     pct(jet_v),
            'petrolePercentage': pct(petrole_v),
            'current_year': current_year,
        }
        cache.set(cache_key, context, 300)

    return render(request, 'dashboardHydro.html', context)


@login_required(login_url='login')
@require_POST
def kpi_details_hydro(request):
    """
    POST-only endpoint returning paginated rows for KPI details on the Hydro dashboard.
    Request body (form or JSON):
      - kpi: one of [attente_echantillonnage, attente_reception_labo, attente_resultats, attente_inspection, total]
      - page: optional, 1-based page number (default 1)
    Response JSON:
      {
        rows: [ { dateheurecargaison, frontiere, importateur, entrepot, produit, volume } ],
        page: int,
        has_next: bool,
        has_prev: bool
      }
    """

    # Read data from POST supporting JSON or form-encoded
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}') if request.body else {}
    except Exception:
        payload = {}

    kpi = (payload.get('kpi') or request.POST.get('kpi') or '').strip()
    try:
        page = int(payload.get('page') or request.POST.get('page') or 1)
    except Exception:
        page = 1
    if page < 1:
        page = 1

    user_id = request.user.id
    current_year = date.today().year

    base = (
        Cargaison.objects
        .select_related("frontiere", "importateur", "entrepot", "produit")
        .filter(entrepot__ville__affectationville__username_id=user_id,
                dateheurecargaison__year=current_year)
        .order_by('-dateheurecargaison')
    )

    # Map KPI to filters (aligned with aggregates in tableaudeBordHydro)
    if kpi == 'attente_echantillonnage':
        qs = base.filter(etat="En attente d'echantillonage")
    elif kpi == 'attente_reception_labo':
        qs = base.filter(etat="Echantillonner")
    elif kpi == 'attente_resultats':
        qs = base.filter(etat="Analyse Labo en cours")
    elif kpi == 'attente_inspection':
        qs = base.filter(etatInspection=True)
    elif kpi == 'total':
        qs = base
    else:
        return JsonResponse({
            'rows': [], 'page': 1, 'has_next': False, 'has_prev': False,
            'error': 'invalid_kpi'
        }, status=400)

    paginator = LazyPaginator(qs, per_page=15)
    try:
        page_obj = paginator.page(page)
    except Exception:
        page_obj = paginator.page(1)
        page = 1

    rows = list(qs.values(
        "dateheurecargaison",
        "frontiere__nomville",
        "importateur__nomimportateur",
        "entrepot__nomentrepot",
        "produit__nomproduit",
        "volume"
    )[(page - 1) * 15:page * 15])

    # Format for response
    formatted_rows = []
    for c in rows:
        formatted_rows.append({
            "dateheurecargaison": (c["dateheurecargaison"].isoformat() if c["dateheurecargaison"] else None),
            "frontiere": c["frontiere__nomville"] or "",
            "importateur": c["importateur__nomimportateur"] or "",
            "entrepot": c["entrepot__nomentrepot"] or "",
            "produit": c["produit__nomproduit"] or "",
            "volume": float(c["volume"]) if c["volume"] is not None else None,
        })

    return JsonResponse({
        'rows': formatted_rows,
        'page': page,
        'has_next': page_obj.has_next(),
        'has_prev': page_obj.has_previous(),
    })



@login_required(login_url='login')
@require_POST
def lastrecordShydro(request):
    user = request.user
    user_id = getattr(user, "id", None)
    if not user_id:
        # Not authenticated or no id — return empty dataset
        return JsonResponse({"data": []})

    qs = (
        Cargaison.objects
        .filter(
            etat="En attente requisition",
            entrepot__ville__affectationville__username_id=user_id,
        )
        .order_by("-dateheurecargaison")[:5]
        .values(
            "dateheurecargaison",
            "frontiere__nomville",
            "importateur__nomimportateur",
            "entrepot__nomentrepot",
            "produit__nomproduit",
            "volume"
        )
    )

    data = [
        {
            "dateheurecargaison": (
                c["dateheurecargaison"].isoformat() if c["dateheurecargaison"] else None
            ),
            "frontiere__nomville": c["frontiere__nomville"] or "",
            "importateur__nomimportateur": c["importateur__nomimportateur"] or "",
            "entrepot__nomentrepot": c["entrepot__nomentrepot"] or "",
            "produit__nomproduit": c["produit__nomproduit"] or "",
            "volume": float(c["volume"]) if c["volume"] is not None else None,
        }
        for c in qs
    ]

    return JsonResponse({"data": data})


@login_required(login_url='login')
@require_POST
def topImportersShydro(request):
    user_id = request.user.id
    current_year = date.today().year
    
    cache_key = f"hydro_top_importers_{user_id}_{current_year}"
    data = cache.get(cache_key)

    if data is None:
        # Get the sum of volume for each importer for the current year
        top_importers = Cargaison.objects.filter(
            entrepot__ville__affectationville__username_id=user_id,
            dateheurecargaison__year=current_year
        ).values('importateur__nomimportateur').annotate(
            total_volume=Round(Sum('volume'), 2)
        ).order_by('-total_volume')[:10]

        data = list(top_importers)
        cache.set(cache_key, data, 1800)  # Cache for 30 minutes

    return JsonResponse({'data': data})


@login_required(login_url='login')
@require_POST
def productCountShydro(request):
    user_id = request.user.id
    current_year = date.today().year

    cache_key = f"hydro_product_counts_{user_id}_{current_year}"
    data = cache.get(cache_key)

    if data is None:
        counts = Cargaison.objects.filter(
            entrepot__ville__affectationville__username_id=user_id,
            dateheurecargaison__year=current_year
        ).aggregate(
            gasoilCount=Count('idcargaison', filter=Q(produit_id=2)),
            mogasCount=Count('idcargaison', filter=Q(produit_id=1)),
            jetCount=Count('idcargaison', filter=Q(produit_id=3)),
            petroleCount=Count('idcargaison', filter=Q(produit_id=4)),
        )
        data = counts
        cache.set(cache_key, data, 1800)  # Cache for 30 minutes

    return JsonResponse({'data': data})


@login_required(login_url='login')
@require_POST
def startKpiExportHydro(request):
    """
    Start a Celery task that exports the full dataset for a given KPI to Excel.
    Optimized to handle JSON/Form-data consistently and ensure efficient task dispatch.
    """
    try:
        if request.body:
            try:
                payload = json.loads(request.body.decode('utf-8'))
            except Exception:
                payload = {}
        else:
            payload = {}

        kpi = (payload.get('kpi') or request.POST.get('kpi') or '').strip()
        if not kpi:
            return JsonResponse({'error': 'KPI identifier is required'}, status=400)

        valid_kpis = {
            'attente_echantillonnage', 'attente_reception_labo', 
            'attente_resultats', 'attente_inspection', 'attente_dechargement', 'total'
        }
        if kpi not in valid_kpis:
            return JsonResponse({'error': f'Invalid KPI: {kpi}'}, status=400)

        # Dispatch Celery task
        from shydro.tasks import export_kpi_details_to_excel
        user_id = request.user.id
        year = date.today().year
        
        # We don't need to pass the whole user object, just the ID
        res = export_kpi_details_to_excel.delay(user_id, kpi, year)
        
        return JsonResponse({
            'status': 'success',
            'task_id': res.id
        })
    except Exception as exc:
        return JsonResponse({'error': 'Failed to start export', 'detail': str(exc)}, status=500)


@login_required(login_url='login')
def afficherDossImport(request):
    if request.method != 'POST':
        return JsonResponse({'error': "Invalid request method."}, status=400)

    try:
        data = json.loads(request.body)
        pk = data.get('rowId')
        if not pk:
             return JsonResponse({'error': "Missing rowId."}, status=400)

        cargaison = Cargaison.objects.only('files_path').get(idcargaison=pk)
        file_path = cargaison.files_path
        if not file_path:
            return JsonResponse({'error': "File path not found for this record."}, status=404)

        # Optimization: Fetch file content from DigitalOcean Space
        # Note: In a production environment with large files, we should ideally 
        # return a pre-signed temporary URL instead of downloading and base64-encoding.
        file_content = download_file_from_space(file_path)

        if file_content:
            # Safely encode the file content as Base64
            encoded_content = base64.b64encode(file_content).decode('utf-8')
            return JsonResponse({'file_content': encoded_content}, status=200)
        else:
            return JsonResponse({'error': "File not found or unable to download from storage."}, status=404)

    except Cargaison.DoesNotExist:
        return JsonResponse({'error': "Cargaison not found."}, status=404)
    except Exception as exc:
        return JsonResponse({'error': "Server error during file retrieval.", "detail": str(exc)}, status=500)


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