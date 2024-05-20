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
from django.db.models import Q, Sum, Prefetch
from django.db.models.functions import Round
from django.http import JsonResponse
from django.shortcuts import render, redirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport
from django_tables2.paginators import LazyPaginator
from openpyxl import Workbook

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


# Class de gestion des codifacations des cargaisons
class GestionCodification():
    # Methode d'affichage du tableau pour la codification (Cargaison en attente de requisition)
    @login_required(login_url='login')
    def affichageTableau(request):
        user = request.user
        id = user.id
        role = user.role_id

        if role == 7 or role == 1 or role == 11:
            if 'search' in request.GET:
                qs = request.GET['search']
                if qs == "":
                    e = Cargaison.objects.filter(etat="En attente d'echantillonage",
                                                 entrepot__ville__affectationville__username_id=id).count()
                    d = ImpressionResultat.objects.filter(isConforme=1, idcargaison__etat="Conforme aux exigences",
                                                          idcargaison__entrepot__ville__affectationville__username_id=id).count()
                    l = Cargaison.objects.filter(etat="Analyse Labo en cours",
                                                 entrepot__ville__affectationville__username_id=id).count()
                    n = ImpressionResultat.objects.filter(
                        idcargaison__entrepot__ville__affectationville__username_id=id,
                        isConforme=0, control=1).count()
                    p = Entrepot_echantillon.objects.filter(
                        idcargaison__etat='Echantillonner',
                        idcargaison__entrepot__ville__affectationville__username_id=id
                    ).count()

                    c = Cargaison.objects.filter(
                        entrepot__ville__affectationville__username_id=id
                    ).count()

                    i = Cargaison.objects.filter(inspection__dateinspection__isnull=True,
                                                 entrepot__ville__affectationville__username_id=id).count()

                    return render(request, 'shydro.html', {
                        'e': e,
                        'd': d,
                        'l': l,
                        'n': n,
                        'p': p,
                        'c': c,
                        'i': i

                    })
                else:
                    request.session['url'] = request.get_full_path()

                    e = Cargaison.objects.filter(etat="En attente d'echantillonage",
                                                 entrepot__ville__affectationville__username_id=id).count()
                    d = ImpressionResultat.objects.filter(isConforme=1, idcargaison__etat="Conforme aux exigences",
                                                          idcargaison__entrepot__ville__affectationville__username_id=id).count()
                    l = Cargaison.objects.filter(etat="Analyse Labo en cours",
                                                 entrepot__ville__affectationville__username_id=id).count()
                    n = ImpressionResultat.objects.filter(
                        idcargaison__entrepot__ville__affectationville__username_id=id,
                        isConforme=0, control=1).count()
                    p = Entrepot_echantillon.objects.filter(
                        idcargaison__etat='Echantillonner',
                        idcargaison__entrepot__ville__affectationville__username_id=id
                    ).count()

                    c = Cargaison.objects.filter(
                        entrepot__ville__affectationville__username_id=id
                    ).count()

                    i = Cargaison.objects.filter(inspection__dateinspection__isnull=True,
                                                 entrepot__ville__affectationville__username_id=id).count()

                    return render(request, 'shydro.html', {
                        'e': e,
                        'd': d,
                        'l': l,
                        'n': n,
                        'p': p,
                        'c': c,
                        'i': i

                    })
            else:
                e = Cargaison.objects.filter(etat="En attente d'echantillonage",
                                             entrepot__ville__affectationville__username_id=id).count()
                d = ImpressionResultat.objects.filter(isConforme=1, idcargaison__etat="Conforme aux exigences",
                                                      idcargaison__entrepot__ville__affectationville__username_id=id).count()
                l = Cargaison.objects.filter(etat="Analyse Labo en cours",
                                             entrepot__ville__affectationville__username_id=id).count()
                n = ImpressionResultat.objects.filter(idcargaison__entrepot__ville__affectationville__username_id=id,
                                                      isConforme=0, control=0).count()
                p = Entrepot_echantillon.objects.filter(
                    idcargaison__etat='Echantillonner',
                    idcargaison__entrepot__ville__affectationville__username_id=id
                ).count()

                c = Cargaison.objects.filter(
                    entrepot__ville__affectationville__username_id=id
                ).count()

                i = Cargaison.objects.filter(inspection__dateinspection__isnull=True,
                                             entrepot__ville__affectationville__username_id=id).count()

                return render(request, 'shydro.html', {
                    'e': e,
                    'd': d,
                    'l': l,
                    'n': n,
                    'p': p,
                    'c': c,
                    'i': i

                })
                return render(request, 'shydro.html', context)
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def responseAffichageTableau(request):
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
        idcargaison__inspection__dateinspection__isnull=True,
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
        idcargaison__inspection__dateinspection__isnull=True,
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
    user = request.user.id
    template = 'rapportActiviteFirst.html'
    form = Filters(user=user)

    qs = Cargaison.objects.filter(entrepot__ville__affectationville__username_id=user).annotate(
        volConst=Sum('inspection__compartiment__gov'),
        gsvT=Sum('inspection__compartiment__gsv'),
        mtaTotal=Sum('inspection__compartiment__mta'),
        mtvTotal=Round(Sum('inspection__compartiment__mtv'), 3)
    ).values('idcargaison',
             'numdos', 'declaration', 'frontiere__nomville', 'inspection__dens', 'inspection__temp', 'mtaTotal',
             'entrepot__nomentrepot', 'inspection__dateinspection', 'importateur__nomimportateur', 'immatriculation',
             'produit__nomproduit', 'dateheurecargaison',
             'requisitiondackdate', 'entrepot_echantillon__dateechantillonage__date',
             'entrepot_echantillon__laboreception__datereceptionlabo__date', 'impressionresultat__printDate',
             'inspection__dateinspection', 'volume', 'volConst', 'gsvT', 'mtvTotal').order_by('-dateheurecargaison')

    # qs = list(qs)
    table = RapportActivite(qs)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    context = {
        'table': table,
        'form': form
    }
    return render(request, template, context)



@login_required(login_url='login')
def responseRapportActivite(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user
    ).annotate(
        volConst=Sum('inspection__compartiment__gov'),
        gsvT=Sum('inspection__compartiment__gsv')
    ).values_list(
        'numdos', 'declaration', 'frontiere__nomville',
        'entrepot__nomentrepot', 'inspection__dateinspection', 'importateur__nomimportateur', 'immatriculation',
        'produit__nomproduit', 'dateheurecargaison__date',
        'requisitiondackdate__date', 'entrepot_echantillon__dateechantillonage__date',
        'entrepot_echantillon__laboreception__datereceptionlabo__date', 'impressionresultat__printDate',
        'inspection__dateinspection', 'volume', 'volConst', 'gsvT'
    ).order_by('-dateheurecargaison')

    # Get the search value from the request's GET parameters
    search_value = request.GET.get('search[value]', '')

    # Apply search filter to the QuerySet
    if search_value:
        qs = qs.filter(
            Q(frontiere__nomville__icontains=search_value) |
            Q(importateur__nomimportateur__icontains=search_value) |
            Q(entrepot__nomentrepot__icontains=search_value) |
            Q(produit__nomproduit__icontains=search_value) |
            Q(immatriculation__icontains=search_value) |
            Q(declaration__icontains=search_value) |
            Q(numreq__icontains=search_value)
        )

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

    # Check if it's an AJAX request and if the export flag is set
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

        # Combine header and data rows using zip
        all_rows = [header_row] + [
            [
                row['dateheurecargaison__date'],
                row['frontiere__nomville'],
                row['importateur__nomimportateur'],
                row['entrepot__nomentrepot'],
                row['produit__nomproduit'],
                row['immatriculation'],
                row['declaration'],
                row['numdos'],
                row['requisitiondackdate__date'],
                row['entrepot_echantillon__dateechantillonage__date'],
                row['entrepot_echantillon__laboreception__datereceptionlabo__date'],
                row['impressionresultat__printDate'],
                row['inspection__dateinspection'],
                row['volume'],
                row['volConst'],
                row['gsvT'],
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
def regularisationDestination(request):
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
            nouvelleDestination = request.POST.get('nouvelleDestination', None)
            print(pk)
            print(nouvelleDestination)
            cargaison = Cargaison.objects.get(idcargaison=pk)
            entrepot = Entrepot.objects.get(identrepot=nouvelleDestination)
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
def pertes(request, pk):
    Cargaison.objects.get(idcargaison=pk).delete()
    return redirect('regularisation')


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
            ).annotate(
                volConst=Sum('inspection__compartiment__gov'),
                gsvT=Sum('inspection__compartiment__gsv'),
                mtaTotal=Sum('inspection__compartiment__mta'),
                mtvTotal=Sum('inspection__compartiment__mtv')
            ).values(
                'inspection__compartiment__vcf',
                'idcargaison', 'numdos', 'declaration', 'frontiere__nomville',
                'inspection__idinspection', 'entrepot__ville__nomville',
                'inspection__dateinspection', 'importateur__nomimportateur',
                'entrepot__nomentrepot', 'immatriculation', 'produit__nomproduit',
                'dateheurecargaison__date', 'requisitiondackdate__date',
                'entrepot_echantillon__dateechantillonage__date',
                'inspection__dens', 'inspection__temp',
                'entrepot_echantillon__laboreception__datereceptionlabo__date',
                'mtaTotal', 'mtvTotal', 'impressionresultat__printDate',
                'inspection__dateinspection', 'volume', 'volConst', 'gsvT'
            ).order_by('-inspection__dateinspection')

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
    print('TEST IMPRESSION')
    print(pk)

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

        if cargaison.numCertInspection is None:
            numCertInspection = num_cert_inspection(ville)

            # print("DEBUG")
            # print(numCertInspection)

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
    user = request.user
    id = user.id
    role = user.role_id

    current_year = date.today().year

    template = 'dashboardHydro.html'

    e = Cargaison.objects.filter(etat="En attente d'echantillonage",
                                 entrepot__ville__affectationville__username_id=id).count()
    d = ImpressionResultat.objects.filter(isConforme=1, idcargaison__etat="Conforme aux exigences",
                                          idcargaison__entrepot__ville__affectationville__username_id=id).count()
    l = Cargaison.objects.filter(etat="Analyse Labo en cours",
                                 entrepot__ville__affectationville__username_id=id).count()
    n = ImpressionResultat.objects.filter(idcargaison__entrepot__ville__affectationville__username_id=id,
                                          isConforme=0, control=0).count()
    p = Entrepot_echantillon.objects.filter(
        idcargaison__etat='Echantillonner',
        idcargaison__entrepot__ville__affectationville__username_id=id
    ).count()

    c = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=id
    ).count()

    i = Cargaison.objects.filter(etatInspection=1,
                                 entrepot__ville__affectationville__username_id=id).count()

    # Nouveau Produtc list
    totalVolume = Cargaison.objects.aggregate(totalVolume=Sum('volume'))['totalVolume']
    totalVolume = round(totalVolume) if totalVolume is not None else 0

    gasoilVolume = Cargaison.objects.filter(produit=2).aggregate(gasoilVolume=Sum('volume'))['gasoilVolume']
    gasoilVolume = round(gasoilVolume) if gasoilVolume is not None else 0

    mogasVolume = Cargaison.objects.filter(produit=1).aggregate(mogasVolume=Sum('volume'))['mogasVolume']
    mogasVolume = round(mogasVolume) if mogasVolume is not None else 0

    jetVolume = Cargaison.objects.filter(produit=3).aggregate(jetVolume=Sum('volume'))['jetVolume']
    jetVolume = round(jetVolume) if jetVolume is not None else 0

    petroleVolume = Cargaison.objects.filter(produit=4).aggregate(petroleVolume=Sum('volume'))['petroleVolume']
    petroleVolume = round(petroleVolume) if petroleVolume is not None else 0

    # Pourcentage
    gasoilPercentage = round(((gasoilVolume / totalVolume) * 100 if totalVolume else 0))
    mogasPercentage = round(((mogasVolume / totalVolume) * 100 if totalVolume else 0))
    jetPercentage = round(((jetVolume / totalVolume) * 100 if totalVolume else 0))
    petrolePercentage = round(((petroleVolume / totalVolume) * 100 if totalVolume else 0))

    context = {
        'e': e,
        'd': d,
        'l': l,
        'n': n,
        'p': p,
        'c': c,
        'i': i,
        'gasoilVolume': gasoilVolume,
        'mogasVolume': mogasVolume,
        'jetVolume': jetVolume,
        'petroleVolume': petroleVolume,
        'totalVolume': totalVolume,
        'gasoilPercentage': gasoilPercentage,
        'mogasPercentage': mogasPercentage,
        'jetPercentage': jetPercentage,
        'petrolePercentage': petrolePercentage,
        'current_year': current_year,
    }
    return render(request, template, context)


@login_required(login_url='login')
def lastrecordShydro(request):
    user = request.user
    id = user.id
    latest_cargaisons = Cargaison.objects.filter(etat="En attente requisition",
                                                 entrepot__ville__affectationville__username_id=id
                                                 ).values(
        'dateheurecargaison', 'frontiere__nomville', 'importateur__nomimportateur', 'entrepot__nomentrepot',
        'produit__nomproduit', 'volume'
    ).order_by('-dateheurecargaison')[:5]

    # Convert the page object to a list of dictionaries
    data = list(latest_cargaisons)

    # Return JSON response with the data
    return JsonResponse({
        'data': data
    })


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
