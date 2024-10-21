import base64
import io
import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, F, Case, When, Value, CharField
from django.db.models.functions import ExtractMonth, ExtractYear
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport
from django_tables2.paginators import LazyPaginator
from openpyxl import Workbook

from accounts.models import AffectationVille, AffectationLaboratoire, ListeLaboratoire, MyUser, UserActivityLog
from enreg.models import *
from hydrocarbures.celery import app
from labo.utils import render_to_pdf
from .codeLabo import generate_labo_code
from .forms import *
from .numCq import numCq
from .tables import *


#Sending email

# from django.core.mail import send_mail #Sending Email
#

# Class de gestion pouir le laboratoire
class GestionLaboratoire():
    # Methode d'affichage des echantillons a la reception
    @login_required(login_url='login')
    def affichageenchantillon(request):
        template = 'labo.html'
        context={}
        return render(request,template,context)


    @login_required(login_url='login')
    def affichageenchantillonResponse(request):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 4 or role == 1:
            qs = Cargaison.objects.filter(
                etat="Echantillonner",
                entrepot__ville__affectationville__username_id=id
                ).values(
                'idcargaison',
                'dateheurecargaison__date',
                'entrepot_echantillon__dateechantillonage__date',
                'entrepot__nomentrepot',
                'produit__nomproduit',
                'immatriculation',
                'numdos',
                'entrepot_echantillon__numrappechauto',
                ).order_by('-entrepot_echantillon__dateechantillonage__date')

            # Get the search value from the request's GET parameters
            search_value = request.GET.get('search[value]', '')

            # Apply search filter to the QuerySet
            if search_value:
                qs = qs.filter(
                    Q(entrepot__nomentrepot__icontains=search_value) |
                    Q(immatriculation__icontains=search_value) |
                    Q(numdos__icontains=search_value) |
                    Q(entrepot_echantillon__numrappechauto__icontains=search_value) |
                    Q(qrcode__icontains=search_value)
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
            count = Cargaison.objects.filter(
                        etat='Refaire',
                        entrepot__ville__affectationville__username_id=user.id
                    ).count()
            # print(count)
            context={
                'count':count,
                'form':form
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

                    #Getting Parameters ID
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
        id = user.id
        role = user.role_id
        request.session['url'] = request.get_full_path()
        d = datetime.today()
        da = d.day
        mo = d.month
        yr = d.year
        form = RapportLabo()
        if role == 5 or role == 1 or role == 6:
            # Compteur Chef Laboratoire
            laboreception = Entrepot_echantillon.objects.filter(idcargaison__etat='Echantillonner',idcargaison__entrepot__ville__affectationville__username_id=id).count()
            enanalyse = LaboReception.objects.filter(idcargaison__idcargaison__entrepot__ville__affectationville__username_id=id,
                                                     idcargaison__idcargaison__etat='Analyse Labo en cours').count()
            enattente = LaboReception.objects.filter(idcargaison__idcargaison__entrepot__ville__affectationville__username_id=id,
                                                     idcargaison__idcargaison__etat='Validation en cours 2').count()
            certImprimer = ImpressionResultat.objects.filter(idcargaison__entrepot__ville__affectationville__username_id=id,isPrinted=1).count()

            return render(request, 'labo_validation1.html', {
                                                             'form': form,
                                                             'laboreception': laboreception,
                                                             'enanalyse': enanalyse,
                                                             'enattente': enattente,
                                                            'certImprimer':certImprimer,
                                                             })
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
            d = LaboReception.objects.raw('SELECT idcargaison_id, MONTH(datereceptionlabo) as mois, YEAR(datereceptionlabo) as annee \
                                        FROM hydro_occ.enreg_laboreception \
                                        WHERE idcargaison_id = %s', [pk, ])
            for obj in d:
                mois = obj.mois
                annee = obj.annee

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
        id = user.id
        role = user.role_id

        if role == 6 or role == 1:
            c = Cargaison.objects.get(idcargaison=pk)
            c.etat = "En attente validation 2"
            c.save(update_fields=['etat'])
            return redirect('validation1')
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def refaire(request):
        user = request.user
        id = user.id
        role = user.role_id
        url = request.session['url']
        pk = request.session['pk']
        if role == 6 or role == 1:
            c = Cargaison.objects.get(idcargaison=pk)
            c.etat = "Refaire"
            c.save(update_fields=['etat'])
            return redirect(url)
        else:
            return redirect('logout')

    # Validation du responsable Division LABO OCC
    @login_required(login_url='login')
    def conforme(request):
        user = request.user
        id = user.id
        role = user.role_id
        url = request.session['url']
        pk = request.session['pk']

        if role == "v2" or role == 1 or role == 6:
            c = Cargaison.objects.get(idcargaison=pk)
            c.etat = "Validation en cours 2"
            c.conformite = "Conforme aux exigences"
            c.impression = "0"
            c.save(update_fields=['etat', 'conformite', 'impression'])

            # i = ImpressionResultat.objects.get(idcargaison_id=c.idcargaison)
            # i.isConforme = True
            # i.isPrinted = False
            # i.save(update_fields=['isConforme','isPrinted'])

            return redirect(url)
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def nonconforme(request):
        user = request.user
        id = user.id
        role = user.role_id
        url = request.session['url']
        pk = request.session['pk']
        if role == "v2" or role == 1 or role == 6:
            c = Cargaison.objects.get(idcargaison=pk)
            c.etat = "Validation en cours 2"
            c.conformite = "Non conforme aux exigences"
            c.impression = "0"
            c.save(update_fields=['etat', 'conformite', 'impression'])
            return redirect(url)
        else:
            return redirect('logout')


    @login_required(login_url='login')
    def conforme2(request):
        user = request.user
        id = user.id
        role = user.role_id
        pk = request.session['pk']

        if role == 1 or role == 10:
            c = Cargaison.objects.get(idcargaison=pk)

            # Check if ImpressionResultat exists for the Cargaison
            if not ImpressionResultat.objects.filter(idcargaison=c).exists():
                # Create and save ImpressionResultat
                i = ImpressionResultat(printDate=datetime.now(), isConforme=1, isPrinted=0, idcargaison=c)
                i.save()

                # Update Cargaison fields
                c.etat = "Conforme aux exigences"
                c.conformite = "Conforme aux exigences"
                c.impression = "0"
                c.dateHeureAnalyseLabo = datetime.now()
                c.save(update_fields=['etat', 'impression', 'conformite', 'dateHeureAnalyseLabo'])
                return redirect('validation2')
            return redirect('validation2')
        else:
            return redirect('logout')


    @login_required(login_url='login')
    def nonconforme2(request):
        user = request.user
        pk = request.session['pk']
        id = user.id
        role = user.role_id
        if role == 1 or role == 10:
            c = Cargaison.objects.get(idcargaison=pk)
            a = LaboReception.objects.get(idcargaison=pk)

            #Updated Method
            i=ImpressionResultat(printDate=datetime.now,isConforme=0,isPrinted=0,idcargaison=c)
            i.save()

            c.etat = "Non conforme aux exigences"
            c.impression = "0"
            c.dateHeureAnalyseLabo = datetime.now()
            c.save(update_fields=['etat', 'impression','dateHeureAnalyseLabo'])
            return redirect('validation2')
        else:
            return redirect('logout')



    # Fonction affichage des resultats sur Validation 1
    @login_required(login_url='login')
    def affichagetableauvalidation2(request):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 5 or role == 1 or role == 6 or role == 10:
            template = 'labo_validation2.html'
            laboreception = Entrepot_echantillon.objects.filter(idcargaison__etat='Echantillonner',idcargaison__entrepot__ville__affectationville__username_id=id).count()
            enanalyse = LaboReception.objects.filter(idcargaison__idcargaison__entrepot__ville__affectationville__username_id=id,
                                                     idcargaison__idcargaison__etat='Analyse Labo en cours').count()
            enattente = LaboReception.objects.filter(idcargaison__idcargaison__entrepot__ville__affectationville__username_id=id,
                                                     idcargaison__idcargaison__etat='Validation en cours 2').count()
            certImprimer = ImpressionResultat.objects.filter(idcargaison__entrepot__ville__affectationville__username_id=id,isPrinted=1).count()

            context = {
                'laboreception':laboreception,
                'enanalyse':enanalyse,
                'enattente':enattente,
                'certImprimer':certImprimer,
            }
            return render(request,template,context)
        else:
            return redirect('logout')


# Gestion des impression des CQ
class GestionImpressionLabo():

    # Fonction pour affichage tableu impression des certificats
    @login_required(login_url='login')
    def affichagetableauimpression(request):
        user = request.user
        role = user.role_id
        ville = AffectationVille.objects.get(username_id=user.id)
        ville = ville.ville_id
        request.session['url'] = request.get_full_path()
        template = 'labo_impression.html'
        if role == 5 or role == 1:
            # calcul pr affichages des pastilles
            cqNotPrinted = ImpressionResultat.objects.filter(isPrinted=False,idcargaison__entrepot__ville=ville).count()
            cqPrinted = ImpressionResultat.objects.filter(isPrinted=True, idcargaison__entrepot__ville=ville).count()
            context = {
                        'cqNotPrinted': cqNotPrinted,
                        'cqPrinted': cqPrinted,
                        }
            return render(request,template,context)
        else:
            return redirect('logout')

    # Fonction de recherche des certificat à imprimer
    @login_required(login_url='login')
    def recherchecq(request):
        user = request.user
        role = user.role_id
        ville = AffectationVille.objects.get(username_id=user.id)
        ville = ville.ville_id
        request.session['url'] = request.get_full_path()
        template='labo_impression.html'
        if role == 5 or role == 1 or role == 6 or role == "v2":
            numcode = request.GET.get('codelabo')
            if numcode != "":
                qs = Cargaison.objects.raw('SELECT ec.idcargaison, ei.idImpression, el.numcertificatqualite, el.codelabo, ep.nomproduit, i.nomimportateur, ee.nomentrepot \
                        FROM enreg_impressionresultat ei, enreg_cargaison ec, enreg_laboreception el, enreg_produit ep, enreg_importateur i, enreg_entrepot ee, enreg_ville ev \
                        WHERE ei.idcargaison_id = ec.idcargaison \
                        AND ec.idcargaison = el.idcargaison_id \
                        AND ec.produit_id = ep.idproduit \
                        AND ec.importateur_id = i.idimportateur \
                        AND ec.entrepot_id = ee.identrepot \
                        AND ee.ville_id = ev.idville \
                        AND ev.idville = %s \
                        AND el.codelabo = %s \
                        AND ei.isPrinted = 0', [ville,numcode, ])

                table = AffichageTableauImpression(qs, prefix='2_')
                RequestConfig(request, paginate={"per_page": 10}).configure(table)
                context = {'labo':table}
                return render(request,template,context)
            else:
                return redirect('impression')
        else:
            return redirect('logout')

    # Fonction de recherche des certificat à Re-imprimer
    @login_required(login_url='login')
    def recherchecqr(request):
        user = request.user
        id = user.id
        role = user.role_id
        ville = AffectationVille.objects.get(username_id=user.id)
        ville = ville.ville_id
        request.session['url'] = request.get_full_path()
        if role == 5 or role == 1 or role == "v1" or role == "v2":
            numcode = request.GET.get('codelabo')
            if numcode != "":
                qs = Cargaison.objects.raw('SELECT ec.idcargaison, ei.idImpression, el.numcertificatqualite, el.codelabo, ep.nomproduit, i.nomimportateur, ee.nomentrepot \
                        FROM enreg_impressionresultat ei, enreg_cargaison ec, enreg_laboreception el, enreg_produit ep, enreg_importateur i, enreg_entrepot ee, enreg_ville ev \
                        WHERE ei.idcargaison_id = ec.idcargaison \
                        AND ec.idcargaison = el.idcargaison_id \
                        AND ec.produit_id = ep.idproduit \
                        AND ec.importateur_id = i.idimportateur \
                        AND ec.entrepot_id = ee.identrepot \
                        AND ee.ville_id = ev.idville \
                        AND ev.idville = %s \
                        AND el.codelabo = %s \
                        AND ei.isPrinted = 1', [ville,numcode, ])

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

    # # Fonction pour impression Certificat
    # @login_required(login_url='login')
    # def impressioncertificat(request, pk):
    #     user = request.user
    #     id = user.id
    #     name = user.last_name + ' ' + user.first_name
    #     poste = user.poste
    #     ville = AffectationVille.objects.get(username_id=id)
    #     ville = ville.ville_id
    #     province = Ville.objects.get(idville=ville)
    #     province = province.province
    #     province = province.upper()
    #     role = user.role_id
    #     url = request.session['url']
    #
    #     #Recuperation des donnees liees aux signataires
    #     affect1 = AffectationLaboratoire.objects.get(ville=ville, signGauche=False)
    #     affect2 = AffectationLaboratoire.objects.get(ville=ville, signGauche=True)
    #     signDroite = MyUser.objects.get(username=affect1.userId)
    #     signGauche = MyUser.objects.get(username=affect2.userId)
    #
    #     #Recuperation du Laboratoire asssocie a la ville
    #     laboratoireData = ListeLaboratoire.objects.get(denominationLaboratoire=affect1.idLaboratoire)
    #
    #     #Recuperation des donnees liees a l'Impression
    #     print(pk)
    #     impressionData = ImpressionResultat.objects.get(idcargaison_id=pk)
    #
    #     print(signGauche)
    #     print(signDroite)
    #
    #     d = LaboReception.objects.filter(idcargaison_id=pk).annotate(
    #         mois=ExtractMonth('datereceptionlabo'),
    #         annee=ExtractYear('datereceptionlabo')
    #     ).values('idcargaison_id', 'mois', 'annee')
    #
    #
    #     for entry in d:
    #         mois = entry['mois']
    #         annee = entry['annee']
    #
    #     print(mois)
    #     print(annee)
    #
    #
    #     if role == 5 or role == 1 :
    #         td = datetime.today()
    #         # today = td.date()
    #
    #         # Récuperation des dates
    #         # d = LaboReception.objects.raw('SELECT idcargaison_id, MONTH(datereceptionlabo) as mois, YEAR(datereceptionlabo) as annee \
    #         #                                        FROM hydro_occ.enreg_laboreception \
    #         #                                        WHERE idcargaison_id = %s', [pk, ])
    #         # for obj in d:
    #         #     mois = obj.mois
    #         #     annee = obj.annee
    #
    #         # Recuperation du produit de la cargaison
    #         p = Produit.objects.get(cargaison=pk)
    #         produit = p.nomproduit
    #
    #         # Fecthing object with pk corresponding into database
    #         cargaison = Cargaison.objects.get(idcargaison=pk)
    #         echantillon = Entrepot_echantillon.objects.get(idcargaison=pk)
    #         laboratoire = LaboReception.objects.get(idcargaison=pk)
    #
    #         printed = ImpressionResultat.objects.get(idcargaison=pk)
    #         printed.isPrinted = 1
    #         printed.save(update_fields=['isPrinted'])
    #
    #
    #
    #         # Test pour afficher les differents rapports
    #         if produit == 'GASOIL':
    #             template = 'report/Report1/gasoilreport.html'
    #
    #             # Resultat Gasoil Fetching data into Database
    #             try:
    #                 couleurastm = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=8)[0].valeurResultatChar
    #             except:
    #                 couleurastm = ''
    #             try:
    #                 aciditetotal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=1)[0].valeurResultat
    #             except:
    #                 aciditetotal= ''
    #             try:
    #                 soufre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[0].valeurResultat
    #             except:
    #                 soufre = ''
    #             try:
    #                 massevolumique = ResultatAnalyse.objects.filter(idcargaison=pk,idParametre=21)[0].valeurResultat
    #             except:
    #                 massevolumique = ''
    #             try:
    #                 massevolumique15 = ResultatAnalyse.objects.filter(idcargaison=pk,idParametre=20)[0].valeurResultat
    #             except:
    #                 massevolumique15 = ''
    #             try:
    #                 distillation = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[0].valeurResultat
    #             except:
    #                 distillation = ''
    #             try:
    #                 distillation10 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=11)[0].valeurResultat
    #             except:
    #                 distillation10 = ''
    #             try:
    #                 distillation20 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=12)[0].valeurResultat
    #             except:
    #                 distillation20 = ''
    #             try:
    #                 distillation50 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=13)[0].valeurResultat
    #             except:
    #                 distillation50 = ''
    #             try:
    #                 distillation90 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=15)[0].valeurResultat
    #             except:
    #                 distillation90 = ''
    #             try:
    #                 pointinitial = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=30)[0].valeurResultat
    #             except:
    #                 pointinitial = ''
    #             try:
    #                 pointfinal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=29)[0].valeurResultat
    #             except:
    #                 pointfinal = ''
    #             try:
    #                 pointeclair = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=25)[0].valeurResultat
    #             except:
    #                 pointeclair = ''
    #             try:
    #                 viscosite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=38)[0].valeurResultat
    #             except:
    #                 viscosite = ''
    #             try:
    #                 pointecoulement = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=26)[0].valeurResultat
    #             except:
    #                 pointecoulement = ''
    #             try:
    #                 teneureau = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=35)[0].valeurResultat
    #             except:
    #                 teneureau = ''
    #             try:
    #                 sediment = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=32)[0].valeurResultat
    #             except:
    #                 sediment = ''
    #             try:
    #                 corrosion_str = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=6)[0].valeurResultat
    #                 corrosion = int(corrosion_str)
    #             except:
    #                 corrosion = ''
    #             try:
    #                 indicecetane = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=19)[0].valeurResultat
    #             except:
    #                 indicecetane = ''
    #             # try:
    #             #     densite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=49)[0].valeurResultat
    #             # except:
    #             #     densite = ''
    #             try:
    #                 recuperation362 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=10)[0].valeurResultat
    #             except:
    #                 recuperation362 = ''
    #             try:
    #                 cendre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=3)[0].valeurResultat
    #             except:
    #                 cendre = ''
    #
    #             data = {
    #                 'laboratoire': laboratoire,
    #                 'cargaison': cargaison,
    #                 'echantillon': echantillon,
    #                 'annee': annee,
    #                 'mois': mois,
    #                 'province': province,
    #                 'couleurastm': couleurastm,
    #                 'aciditetotal': aciditetotal,
    #                 'soufre': soufre,
    #                 'massevolumique': massevolumique,
    #                 'distillation': distillation,
    #                 'distillation10': distillation10,
    #                 'distillation20': distillation20,
    #                 'distillation50': distillation50,
    #                 'distillation90': distillation90,
    #                 'pointfinal': pointfinal,
    #                 'pointeclair': pointeclair,
    #                 'pointinitial': pointinitial,
    #                 'viscosite': viscosite,
    #                 'pointecoulement': pointecoulement,
    #                 'teneureau': teneureau,
    #                 'sediment': sediment,
    #                 'corrosion': corrosion,
    #                 'indicecetane': indicecetane,
    #                 # 'densite': densite,
    #                 'recuperation362': recuperation362,
    #                 'cendre': cendre,
    #                 'massevolumique15': massevolumique15,
    #                 'signGauche': signGauche,
    #                 'signDroite': signDroite,
    #                 'impressionData': impressionData,
    #                 'laboratoireData':laboratoireData,
    #             }
    #
    #             # Rendered PDF report
    #             pdf = render_to_pdf(template, data)
    #             return HttpResponse(pdf, content_type='application/pdf')
    #
    #         else:
    #             if produit == 'MOGAS':
    #                 template = 'report/Report1/mogasreport.html'
    #                 # Resultat Gasoil Fetching data into Database
    #                 try:
    #                     aspect = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=2)[0].valeurResultatChar
    #                 except:
    #                     aspect=''
    #                 try:
    #                     odeur = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=22)[0].valeurResultatChar
    #                 except:
    #                     odeur=''
    #                 try:
    #                     couleursaybolt = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=8)[0].valeurResultatChar
    #                 except:
    #                     couleursaybolt=''
    #                 try:
    #                     soufre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[0].valeurResultat
    #                 except:
    #                     soufre=''
    #                 try:
    #                     distillation = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[0].valeurResultat
    #                 except:
    #                     distillation=''
    #                 try:
    #                     pointfinal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=29)[0].valeurResultat
    #                 except:
    #                     pointfinal=''
    #                 try:
    #                     residu = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=31)[0].valeurResultat
    #                 except:
    #                     residu=''
    #                 try:
    #                     corrosion_str = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=7)[0].valeurResultat
    #                     corrosion = int(corrosion_str)
    #                 except:
    #                     corrosion=''
    #                 try:
    #                     pourcent10 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=11)[0].valeurResultat
    #                 except:
    #                     pourcent10=''
    #                 try:
    #                     pourcent20 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=12)[0].valeurResultat
    #                 except:
    #                     pourcent20=''
    #                 try:
    #                     pourcent50 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=13)[0].valeurResultat
    #                 except:
    #                     pourcent50=''
    #                 try:
    #                     pourcent70 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=14)[0].valeurResultat
    #                 except:
    #                     pourcent70=''
    #                 try:
    #                     pourcent90 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=15)[0].valeurResultat
    #                 except:
    #                     pourcent90=''
    #                 try:
    #                     tensionvapeur = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=36)[0].valeurResultat
    #                 except:
    #                     tensionvapeur=''
    #                 try:
    #                     difftemperature = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=9)[0].valeurResultat
    #                 except:
    #                     difftemperature=''
    #                 try:
    #                     plomb = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=24)[0].valeurResultat
    #                 except:
    #                     plomb=''
    #                 try:
    #                     indiceoctane = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=18)[0].valeurResultat
    #                 except:
    #                     indiceoctane=''
    #                 try:
    #                     massevolumique15 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[0].valeurResultat
    #                 except:
    #                     massevolumique15=''
    #
    #                 data = {
    #                     'laboratoire': laboratoire,
    #                     'cargaison': cargaison,
    #                     'echantillon': echantillon,
    #                     'annee': annee,
    #                     'mois': mois,
    #                     'province': province,
    #                     'aspect': aspect,
    #                     'odeur': odeur,
    #                     'couleursaybolt': couleursaybolt,
    #                     'soufre': soufre,
    #                     'distillation': distillation,
    #                     'pointfinal': pointfinal,
    #                     'residu': residu,
    #                     'corrosion': corrosion,
    #                     'pourcent10': pourcent10,
    #                     'pourcent20': pourcent20,
    #                     'pourcent50': pourcent50,
    #                     'pourcent70': pourcent70,
    #                     'pourcent90': pourcent90,
    #                     'tensionvapeur': tensionvapeur,
    #                     'difftemperature': difftemperature,
    #                     'plomb': plomb,
    #                     'indiceoctane': indiceoctane,
    #                     'massevolumique15': massevolumique15,
    #                     'signGauche': signGauche,
    #                 'signDroite': signDroite,
    #                 'impressionData': impressionData,
    #                 'laboratoireData':laboratoireData,
    #                 }
    #
    #                 # Rendered PDF report
    #                 pdf = render_to_pdf(template, data)
    #                 return HttpResponse(pdf, content_type='application/pdf')
    #             else:
    #                 if produit == 'JET A1':
    #                     template = 'report/Report1/jeta1report.html'
    #
    #                     # Resultat Gasoil Fetching data into Database
    #                     try:
    #                         aspect = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=2)[
    #                             0].valeurResultatChar
    #                     except:
    #                         aspect=''
    #                     try:
    #                         couleursaybolt = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=8)[
    #                             0].valeurResultatChar
    #                     except:
    #                         couleursaybolt=''
    #                     try:
    #                         aciditetotal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=1)[
    #                             0].valeurResultat
    #                     except:
    #                         aciditetotal=''
    #                     try:
    #                         soufre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[
    #                             0].valeurResultat
    #                     except:
    #                         soufre=''
    #                     try:
    #                         soufremercaptan = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=33)[
    #                             0].valeurResultat
    #                     except:
    #                         soufremercaptan=''
    #                     try:
    #                         docteurtest = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=16)[
    #                             0].valeurResultat
    #                     except:
    #                         docteurtest=''
    #                     try:
    #                         distillation = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
    #                             0].valeurResultat
    #                     except:
    #                         distillation=''
    #                     try:
    #                         pointinitial = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=30)[
    #                             0].valeurResultat
    #                     except:
    #                         pointinitial=''
    #                     try:
    #                         pointfinal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=29)[
    #                             0].valeurResultat
    #                     except:
    #                         pointfinal=''
    #
    #                     try:
    #                         pointfumee = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=28)[
    #                             0].valeurResultat
    #                     except:
    #                         pointfumee=''
    #
    #                     try:
    #                         pointeclair = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=25)[
    #                             0].valeurResultat
    #                     except:
    #                         pointeclair=''
    #
    #                     try:
    #                         freezingpoint = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=17)[
    #                             0].valeurResultat
    #                     except:
    #                         freezingpoint=''
    #
    #                     try:
    #                         residu = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=31)[
    #                             0].valeurResultat
    #                     except:
    #                         residu=''
    #
    #                     try:
    #                         perte = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=23)[
    #                             0].valeurResultat
    #                     except:
    #                         perte=''
    #
    #                     try:
    #                         massevolumique15 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[
    #                             0].valeurResultat
    #                     except:
    #                         massevolumique15=''
    #
    #                     try:
    #                         viscosite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=37)[
    #                             0].valeurResultat
    #                     except:
    #                         viscosite=''
    #
    #                     try:
    #                         pointinflammabilite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=27)[
    #                             0].valeurResultat
    #                     except:
    #                         pointinflammabilite=''
    #
    #                     try:
    #                         teneureau = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=35)[
    #                             0].valeurResultat
    #                     except:
    #                         teneureau=''
    #
    #                     try:
    #                         corrosion_str = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=5)[
    #                             0].valeurResultat
    #                         corrosion = int(corrosion_str)
    #                     except:
    #                         corrosion=''
    #
    #                     try:
    #                         conductivite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=4)[
    #                             0].valeurResultat
    #                     except:
    #                         conductivite=''
    #
    #                     try:
    #                         vol10 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=11)[
    #                             0].valeurResultat
    #                     except:
    #                         vol10=''
    #
    #                     try:
    #                         vol20 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=12)[
    #                             0].valeurResultat
    #                     except:
    #                         vol20=''
    #                     try:
    #                         vol30 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
    #                             0].valeurResultat
    #                     except:
    #                         vol30=''
    #                     try:
    #                         vol40 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
    #                             0].valeurResultat
    #                     except:
    #                         vol40=''
    #                     try:
    #                         vol50 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=13)[
    #                             0].valeurResultat
    #                     except:
    #                         vol50=''
    #                     try:
    #                         vol60 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
    #                             0].valeurResultat
    #                     except:
    #                         vol60=''
    #                     try:
    #                         vol70 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=14)[
    #                             0].valeurResultat
    #                     except:
    #                         vol70=''
    #                     try:
    #                         vol80 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
    #                             0].valeurResultat
    #                     except:
    #                         vol80=''
    #                     try:
    #                         vol90 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=15)[
    #                             0].valeurResultat
    #                     except:
    #                         vol90=''
    #
    #                     data = {
    #                         'laboratoire': laboratoire,
    #                         'cargaison': cargaison,
    #                         'echantillon': echantillon,
    #                         'annee': annee,
    #                         'mois': mois,
    #                         'province': province,
    #                         'aspect': aspect,
    #                         'couleursaybolt': couleursaybolt,
    #                         'aciditetotal': aciditetotal,
    #                         'soufre': soufre,
    #                         'soufremercaptan': soufremercaptan,
    #                         'docteurtest': docteurtest,
    #                         'distillation': distillation,
    #                         'pointinitial': pointinitial,
    #                         'pointfinal': pointfinal,
    #                         'pointfumee': pointfumee,
    #                         'freezingpoint': freezingpoint,
    #                         'residu': residu,
    #                         'perte': perte,
    #                         'pointeclair': pointeclair,
    #                         'massevolumique15': massevolumique15,
    #                         'viscosite': viscosite,
    #                         'pointinflammabilite': pointinflammabilite,
    #                         'teneureau': teneureau,
    #                         'corrosion': corrosion,
    #                         'conductivite': conductivite,
    #                         'vol10': vol10,
    #                         'vol20': vol20,
    #                         'vol30': vol30,
    #                         'vol40': vol40,
    #                         'vol50': vol50,
    #                         'vol60': vol60,
    #                         'vol70': vol70,
    #                         'vol80': vol80,
    #                         'vol90': vol90,
    #                         'signGauche': signGauche,
    #                         'signDroite': signDroite,
    #                         'impressionData': impressionData,
    #                         'laboratoireData':laboratoireData,
    #                     }
    #                     # Rendered PDF report
    #                     pdf = render_to_pdf(template, data)
    #                     return HttpResponse(pdf, content_type='application/pdf')
    #
    #                 else:
    #                     if produit == 'PETROLE LAMPANT':
    #                         template = 'report/Report1/petrolereport.html'
    #
    #                         # Resultat Gasoil Fetching data into Database
    #                         try:
    #                             aspect = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=1)[
    #                                 0].valeurResultatChar
    #                         except:
    #                             aspect = ''
    #                         try:
    #                             couleursaybolt = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=3)[
    #                                 0].valeurResultatChar
    #                         except:
    #                             couleursaybolt = ''
    #                         try:
    #                             aciditetotal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=5)[
    #                                 0].valeurResultat
    #                         except:
    #                             aciditetotal = ''
    #                         try:
    #                             soufre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=6)[
    #                                 0].valeurResultat
    #                         except:
    #                             soufre = ''
    #                         try:
    #                             soufremercaptan = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=7)[
    #                                 0].valeurResultat
    #                         except:
    #                             soufremercaptan = ''
    #                         try:
    #                             docteurtest = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=8)[
    #                                 0].valeurResultat
    #                         except:
    #                             docteurtest = ''
    #                         try:
    #                             distillation = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=11)[
    #                                 0].valeurResultat
    #                         except:
    #                             distillation = ''
    #                         try:
    #                             pointinitial = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=16)[
    #                                 0].valeurResultat
    #                         except:
    #                             pointinitial = ''
    #                         try:
    #                             pointfinal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=17)[
    #                                 0].valeurResultat
    #                         except:
    #                             pointfinal = ''
    #
    #                         try:
    #                             pointfumee = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=19)[
    #                                 0].valeurResultat
    #                         except:
    #                             pointfumee = ''
    #
    #                         try:
    #                             pointeclair = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=18)[
    #                                 0].valeurResultat
    #                         except:
    #                             pointeclair = ''
    #
    #                         try:
    #                             freezingpoint = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[
    #                                 0].valeurResultat
    #                         except:
    #                             freezingpoint = ''
    #
    #                         try:
    #                             residu = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=21)[
    #                                 0].valeurResultat
    #                         except:
    #                             residu = ''
    #
    #                         try:
    #                             perte = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=22)[
    #                                 0].valeurResultat
    #                         except:
    #                             perte = ''
    #
    #                         try:
    #                             massevolumique15 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=52)[
    #                                 0].valeurResultat
    #                         except:
    #                             massevolumique15 = ''
    #
    #                         try:
    #                             viscosite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=23)[
    #                                 0].valeurResultat
    #                         except:
    #                             viscosite = ''
    #
    #                         try:
    #                             pointinflammabilite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=24)[
    #                                 0].valeurResultat
    #                         except:
    #                             pointinflammabilite = ''
    #
    #                         try:
    #                             teneureau = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=26)[
    #                                 0].valeurResultat
    #                         except:
    #                             teneureau = ''
    #
    #                         try:
    #                             corrosion_str = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=28)[
    #                                 0].valeurResultat
    #                             corrosion = int(corrosion_str)
    #
    #                         except:
    #                             corrosion = ''
    #
    #                         try:
    #                             conductivite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=29)[
    #                                 0].valeurResultat
    #                         except:
    #                             conductivite = ''
    #
    #                         try:
    #                             vol10 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=39)[
    #                                 0].valeurResultat
    #                         except:
    #                             vol10 = ''
    #
    #                         try:
    #                             vol20 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=40)[
    #                                 0].valeurResultat
    #                         except:
    #                             vol20 = ''
    #                         try:
    #                             vol30 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=41)[
    #                                 0].valeurResultat
    #                         except:
    #                             vol30 = ''
    #                         try:
    #                             vol40 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=42)[
    #                                 0].valeurResultat
    #                         except:
    #                             vol40 = ''
    #                         try:
    #                             vol50 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=43)[
    #                                 0].valeurResultat
    #                         except:
    #                             vol50 = ''
    #                         try:
    #                             vol60 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=44)[
    #                                 0].valeurResultat
    #                         except:
    #                             vol60 = ''
    #                         try:
    #                             vol70 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=45)[
    #                                 0].valeurResultat
    #                         except:
    #                             vol70 = ''
    #                         try:
    #                             vol80 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=46)[
    #                                 0].valeurResultat
    #                         except:
    #                             vol80 = ''
    #                         try:
    #                             vol90 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=47)[
    #                                 0].valeurResultat
    #                         except:
    #                             vol90 = ''
    #
    #                         data = {
    #                             'laboratoire': laboratoire,
    #                             'cargaison': cargaison,
    #                             'echantillon': echantillon,
    #                             'annee': annee,
    #                             'mois': mois,
    #                             'province': province,
    #                             'aspect': aspect,
    #                             'couleursaybolt': couleursaybolt,
    #                             'aciditetotal': aciditetotal,
    #                             'soufre': soufre,
    #                             'soufremercaptan': soufremercaptan,
    #                             'docteurtest': docteurtest,
    #                             'distillation': distillation,
    #                             'pointinitial': pointinitial,
    #                             'pointfinal': pointfinal,
    #                             'pointfumee': pointfumee,
    #                             'freezingpoint': freezingpoint,
    #                             'residu': residu,
    #                             'perte': perte,
    #                             'pointeclair': pointeclair,
    #                             'massevolumique15': massevolumique15,
    #                             'viscosite': viscosite,
    #                             'pointinflammabilite': pointinflammabilite,
    #                             'teneureau': teneureau,
    #                             'corrosion': corrosion,
    #                             'conductivite': conductivite,
    #                             'vol10': vol10,
    #                             'vol20': vol20,
    #                             'vol30': vol30,
    #                             'vol40': vol40,
    #                             'vol50': vol50,
    #                             'vol60': vol60,
    #                             'vol70': vol70,
    #                             'vol80': vol80,
    #                             'vol90': vol90,
    #                             'signGauche': signGauche,
    #                 'signDroite': signDroite,
    #                 'impressionData': impressionData,
    #                 'laboratoireData':laboratoireData,
    #                         }
    #
    #                         # Rendered PDF report
    #                         pdf = render_to_pdf(template, data)
    #                         return HttpResponse(pdf, content_type='application/pdf')
    #                 return redirect('logout')
    #     else:
    #         return redirect('logout')

    # Fonction pour impression Certificat
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
            d = LaboReception.objects.raw('SELECT idcargaison_id, MONTH(datereceptionlabo) as mois, YEAR(datereceptionlabo) as annee \
                                                   FROM hydro_occ.enreg_laboreception \
                                                   WHERE idcargaison_id = %s', [pk, ])

            for obj in d:
                mois = obj.mois
                annee = obj.annee

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
            d = LaboReception.objects.raw('SELECT idcargaison_id, MONTH(datereceptionlabo) as mois, YEAR(datereceptionlabo) as annee \
                                                              FROM hydro_occ.enreg_laboreception \
                                                              WHERE idcargaison_id = %s', [pk, ])

            for obj in d:
                mois = obj.mois
                annee = obj.annee
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
    role = user.role_id
    id = user.id
    u = user.username
    username = user.username
    ville = AffectationVille.objects.get(username=id)
    ville = ville.ville_id
    template = 'labodashboardrapport.html'
    if request.method == 'POST':
        datedebut = request.POST['datedebut']
        datefin = request.POST['datefin']
        request.session['datedebut'] = datedebut
        request.session['datefin'] = datefin
        table1 = RapportLaboTable(LaboReception.objects.raw('SELECT DISTINCT(l.idcargaison_id), e.dateechantillonage, l.datereceptionlabo, i.nomimportateur , ee.nomentrepot , c.immatriculation, c.numdossier, c.codecargaison, e.numrappech, l.codelabo, r.dateanalyse, r.dateimpression, l.numcertificatqualite \
                                                                        FROM hydro_occ.enreg_laboreception l, hydro_occ.enreg_entrepot_echantillon e, hydro_occ.enreg_cargaison c, hydro_occ.enreg_resultat r, hydro_occ.enreg_importateur i, hydro_occ.enreg_entrepot ee \
                                                                        WHERE l.idcargaison_id = e.idcargaison_id \
                                                                        AND e.idcargaison_id = c.idcargaison \
                                                                        AND l.idcargaison_id = r.idcargaison_id \
                                                                        AND i.idimportateur = c.importateur_id \
                                                                        AND ee.identrepot = c.entrepot_id \
                                                                        AND c.frontiere_id = %s \
                                                                        AND l.datereceptionlabo BETWEEN %s AND %s \
                                                                        ORDER BY DATE(l.datereceptionlabo) DESC',
                                                            [ville, datedebut, datefin, ]), prefix='1_')
        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                         "per_page": 20}).configure(table1)
        return render(request, template, {'table': table1})
    else:
        datedebut = request.session['datedebut']
        datefin = request.session['datefin']
        table1 = RapportLaboTable(LaboReception.objects.raw('SELECT DISTINCT(l.idcargaison_id), e.dateechantillonage, l.datereceptionlabo, i.nomimportateur , ee.nomentrepot , c.immatriculation, c.numdossier, c.codecargaison, e.numrappech, l.codelabo, r.dateanalyse, r.dateimpression, l.numcertificatqualite \
                                                                                FROM hydro_occ.enreg_laboreception l, hydro_occ.enreg_entrepot_echantillon e, hydro_occ.enreg_cargaison c, hydro_occ.enreg_resultat r, hydro_occ.enreg_importateur i, hydro_occ.enreg_entrepot ee \
                                                                                WHERE l.idcargaison_id = e.idcargaison_id \
                                                                                AND e.idcargaison_id = c.idcargaison \
                                                                                AND l.idcargaison_id = r.idcargaison_id \
                                                                                AND i.idimportateur = c.importateur_id \
                                                                                AND ee.identrepot = c.entrepot_id \
                                                                                AND c.frontiere_id = %s \
                                                                                AND l.datereceptionlabo BETWEEN %s AND %s \
                                                                                ORDER BY DATE(l.datereceptionlabo) DESC',
                                                            [ville, datedebut, datefin, ]), prefix='1_')
        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                         "per_page": 20}).configure(table1)
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
                    c.save(update_fields=['natureProduitLabo','userLabo'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Product denomination update",
                        description=f"User has changed the nature of the product for the record {cargaison.idcargaison}"
                    )

                    return redirect('reception', pk=pk)
                except:
                    c = ControlNatureProduit(idcargaison=cargaison,natureProduitLabo=produit.nomproduit,userLabo=user)
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


#Saisie saisieResultat
@login_required(login_url='login')
def saisieResultat(request,pk):
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
            ORDER BY a.id ASC' ,[pk,])

    table = SaisieResultat(qs)
    # RequestConfig(request, paginate={"per_page": 10}).configure(table)
    context = {
        'table': table,
        'codeLabo':a,
    }
    return render(request,template,context)


@login_required(login_url='login')
def saisieResultatParametre(request,pk):
    user = request.user
    id = request.session['pk']
    cargaison = Cargaison.objects.get(idcargaison=id)
    parametre = ParametresProduits.objects.get(idParametre=pk)
    if request.method == 'POST':
        valeurResultat = request.POST['valeurResultat']
        if parametre.idParametre == 2 or parametre.idParametre == 8 or parametre.idParametre == 22:
            try:
                r = ResultatAnalyse.objects.get(idParametre=parametre,idcargaison=cargaison)
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
                return redirect('saisieResultat',id)
        else:
            try:
                r = ResultatAnalyse.objects.get(idParametre=parametre,idcargaison=cargaison)
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
                return redirect('saisieResultat',id)
    else:
        return redirect('saisieResultat',id)


@login_required(login_url='login')
def validationResulat(request):
    user = request.user
    if request.method == 'POST':
        id = request.POST['idcargaison']
        cargaison = Cargaison.objects.get(idcargaison=id)
        cargaison.etat = 'Validation en cours 1'
        cargaison.save(update_fields=['etat'])

        UserActivityLog.objects.create(
            user=user,
            action="Test result form confirmation",
            description=f"User has confirm the results for the record {cargaison.idcargaison}",
        )

        context = {
            'status':'success'
        }
        return JsonResponse(context)
    else:
        return redirect('analyse')


@login_required(login_url='login')
def affichageDetailsResultats(request,pk):
    user = request.user.id
    cargaison = Cargaison.objects.get(idcargaison=pk)
    request.session['pk'] = pk

    template = 'laboDetailsResultat.html'

    qs = Cargaison.objects.raw("SELECT c.idcargaison, ee.nomentrepot, i.nomimportateur, ep.nomproduit, l.codelabo, l.numcertificatqualite, p.nomParametre, a.valeurMin, a.valeurMax ,r.valeurResultatChar ,r.valeurResultat, \
    	                IF (r.valeurResultat  > a.valeurMax , 'Non Conforme', IF (r.valeurResultat < a.valeurMin, 'Non Conforme','Conforme')) as etatValeur \
                        FROM enreg_cargaison c, enreg_resultatanalyse r, enreg_parametresproduits p,  enreg_affectationparametre a, enreg_produit ep, enreg_importateur i, enreg_entrepot_echantillon e, enreg_laboreception l, enreg_entrepot ee, accounts_affectationville aa, enreg_ville ev \
                        WHERE c.idcargaison = r.idcargaison_id \
    	                AND r.idParametre_id = p.idParametre \
                        AND p.idParametre = a.idParametre_id \
                        AND a.idproduit_id = ep.idproduit \
                        AND ep.idproduit = c.produit_id \
                        AND c.importateur_id = i.idimportateur \
                        AND c.idcargaison = e.idcargaison_id \
                        AND e.idcargaison_id = l.idcargaison_id \
                        AND c.entrepot_id = ee.identrepot \
                        AND ee.ville_id = ev.idville \
                        AND ev.idville = aa.ville_id \
                        AND aa.username_id = %s \
                        AND c.idcargaison = %s \
                        AND c.etat = 'Validation en cours 1'", [user,pk, ])

    table = AffichageDetailResultat(qs,prefix='_1')
    RequestConfig(request, paginate={"per_page": 50}).configure(table)
    context = {'table': table}
    return render(request,template,context)



@login_required(login_url='login')
def affichageDetailsResultatsDroite(request,pk):
    user = request.user.id
    cargaison = Cargaison.objects.get(idcargaison=pk)
    request.session['pk'] = pk

    template = 'laboDetailsResultatDroite.html'

    qs = Cargaison.objects.raw("SELECT c.idcargaison, ee.nomentrepot, i.nomimportateur, ep.nomproduit, l.codelabo, l.numcertificatqualite, p.nomParametre ,r.valeurResultat, \
    	                IF (r.valeurResultat  > a.valeurMax , 'Non Conforme', \
    		            IF (r.valeurResultat < a.valeurMin, 'Non Conforme','Conforme')) as etatValeur \
                        FROM enreg_cargaison c, enreg_resultatanalyse r, enreg_parametresproduits p,  enreg_affectationparametre a, enreg_produit ep, enreg_importateur i, enreg_entrepot_echantillon e, enreg_laboreception l, enreg_entrepot ee, accounts_affectationville aa, enreg_ville ev \
                        WHERE c.idcargaison = r.idcargaison_id \
    	                AND r.idParametre_id = p.idParametre \
                        AND p.idParametre = a.idParametre_id \
                        AND a.idproduit_id = ep.idproduit \
                        AND ep.idproduit = c.produit_id \
                        AND c.importateur_id = i.idimportateur \
                        AND c.idcargaison = e.idcargaison_id \
                        AND e.idcargaison_id = l.idcargaison_id \
                        AND c.entrepot_id = ee.identrepot \
                        AND ee.ville_id = ev.idville \
                        AND ev.idville = aa.ville_id \
                        AND aa.username_id = %s \
                        AND c.idcargaison = %s \
                        AND c.etat = 'Validation en cours 2'", [user,pk, ])

    table = AffichageDetailResultat(qs,prefix='_1')
    RequestConfig(request, paginate={"per_page": 50}).configure(table)
    context = {'table': table}
    return render(request,template,context)


@login_required(login_url='login')
def receptionRapports(request):
    template ='laboReceptionRapports.html'
    form = FiltresDate()
    context = {'form':form}
    return render(request,template,context)


@login_required(login_url='login')
def receptionRapportsResponse(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user,
        entrepot_echantillon__laboreception__datereceptionlabo__isnull=False
    ).values(
        'numdos',
        'entrepot_echantillon__numrappechauto',
        'entrepot_echantillon__laboreception__codelabo',
        'entrepot_echantillon__dateechantillonage__date',
        'entrepot_echantillon__laboreception__datereceptionlabo__date',
        'entrepot__nomentrepot',
        'importateur__nomimportateur',
        'immatriculation',
        'produit__nomproduit',
    ).order_by('-entrepot_echantillon__laboreception__datereceptionlabo')

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

    # # Convert the page object to a list of dictionaries
    # data = list(page)
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
                      'IMMATRICULATION','PRODUIT']

        # Combine header and data rows using zip
        all_rows = [header_row] + [
            [
                row['numdos'],
                row['entrepot_echantillon__numrappechauto'],
                row['entrepot_echantillon__laboreception__codelabo'],
                row['entrepot_echantillon__dateechantillonage__date'],
                row['entrepot_echantillon__laboreception__datereceptionlabo__date'],
                row['entrepot__nomentrepot'],
                row['importateur__nomimportateur'],
                row['immatriculation'],
                row['produit__nomproduit'],
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
def receptionRapportsGenerate(request):
    template ='laboReceptionRapportsFiltres.html'
    # Get the search value from the request's GET parameters
    if request.method == 'POST':
        date_d = request.POST['date_d']
        date_f = request.POST['date_f']

        request.session['date_d'] = date_d
        request.session['date_f'] = date_f

        form = FiltresDate()
        context = {'form':form}
        return render(request,template,context)
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
        'entrepot_echantillon__laboreception__codelabo',
        'entrepot_echantillon__dateechantillonage__date',
        'entrepot_echantillon__laboreception__datereceptionlabo__date',
        'entrepot__nomentrepot',
        'importateur__nomimportateur',
        'immatriculation',
        'produit__nomproduit',
    ).order_by('-dateheurecargaison')

    date_d = request.session['date_d']
    date_f = request.session['date_f']

    # Apply search filter to the QuerySet
    if date_d and date_f:
        qs = qs.filter(
            entrepot_echantillon__laboreception__datereceptionlabo__date__range=(date_d,date_f)
        )

    if date_d:
        qs = qs.filter(
            entrepot_echantillon__laboreception__datereceptionlabo__date=(date_d)
        )
        print(date_d)

    if date_f:
        qs = qs.filter(
            entrepot_echantillon__laboreception__datereceptionlabo__date=(date_f)
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
                row['entrepot_echantillon__laboreception__codelabo'],
                row['entrepot_echantillon__dateechantillonage__date'],
                row['entrepot_echantillon__laboreception__datereceptionlabo__date'],
                row['entrepot__nomentrepot'],
                row['importateur__nomimportateur'],
                row['immatriculation'],
                row['produit__nomproduit'],
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
def refaireAjx(request):
    user = request.user
    role = user.role_id
    if role == 6 or role == 1 or role == 10:
        if request.method == 'POST':
            idcargaison = request.POST.get('idcargaison')

            try:
                c = Cargaison.objects.get(idcargaison=idcargaison)
                c.etat = "Refaire"
                c.save(update_fields=['etat'])

                UserActivityLog.objects.create(
                    user=user,
                    action="Request to re-do the Test",
                    description=f"User has requested that the record  {c.idcargaison} test need to be done again",
                )

                response_data = {'status': 'success', 'message': 'Cargaison marked as REFAIRE'}
                return JsonResponse(response_data)
            except Cargaison.DoesNotExist:
                response_data = {'status': 'failure', 'message': 'Cargaison not found'}
                return JsonResponse(response_data, status=404)  # 404 Not Found status code
        else:
            # Return a JSON response indicating unauthorized access
            response_data = {'status': 'failure', 'message': 'Unauthorized'}
            return JsonResponse(response_data, status=401)  # 401 Unauthorized status code
    else:
        # Return a JSON response indicating bad request method (not POST)
        response_data = {'status': 'failure', 'message': 'Invalid request method'}
        return JsonResponse(response_data, status=400)  # 400 Bad Request status code




# Validation du responsable Division LABO OCC
@login_required(login_url='login')
def conformeAjx(request):
    user = request.user
    role = user.role_id

    if role == 1 or role == 6:
        if request.method == 'POST':
            idcargaison = request.POST.get('idcargaison')

            try:
                c = Cargaison.objects.get(idcargaison=idcargaison)

                c.etat = "Validation en cours 2"
                c.conformite = "Conforme aux exigences"
                c.impression = "0"
                c.save(update_fields=['etat', 'conformite', 'impression'])

                UserActivityLog.objects.create(
                    user=user,
                    action="Test result first validation CONFORME",
                    description=f"User has done the first validation for the results for the record {idcargaison}",
                )

                response_data = {'status': 'success', 'message': 'Cargaison marked as CONFORME'}
                return JsonResponse(response_data)
            except Cargaison.DoesNotExist:
                response_data = {'status': 'failure', 'message': 'Cargaison not found'}
                return JsonResponse(response_data, status=404)  # 404 Not Found status code
        else:
            # Return a JSON response indicating unauthorized access
            response_data = {'status': 'failure', 'message': 'Unauthorized'}
            return JsonResponse(response_data, status=401)  # 401 Unauthorized status code
    else:
        # Return a JSON response indicating bad request method (not POST)
        response_data = {'status': 'failure', 'message': 'Invalid request method'}
        return JsonResponse(response_data, status=400)  # 400 Bad Request status code


@login_required(login_url='login')
def nonconformeAjx(request):
    user = request.user
    role = user.role_id
    if role == "v2" or role == 1 or role == 6:
        if request.method == 'POST':
            idcargaison = request.POST.get('idcargaison')
            # print(idcargaison)
            try:
                c = Cargaison.objects.get(idcargaison=idcargaison)
                # print(c.idcargaison)
                c.etat = "Validation en cours 2"
                # print(c.etat)
                c.conformite = "Non conforme aux exigences"
                c.impression = "0"
                c.save(update_fields=['etat', 'conformite', 'impression'])

                UserActivityLog.objects.create(
                    user=user,
                    action="Test result first validation NON CONFORME",
                    description=f"User has done the first validation for the results for the record {c.idcargaison}",
                )

                response_data = {'status': 'success', 'message': 'Cargaison marked as NON CONFORME'}
                return JsonResponse(response_data)
            except Cargaison.DoesNotExist:
                response_data = {'status': 'failure', 'message': 'Cargaison not found'}
                return JsonResponse(response_data, status=404)  # 404 Not Found status code
        else:
            # Return a JSON response indicating unauthorized access
            response_data = {'status': 'failure', 'message': 'Unauthorized'}
            return JsonResponse(response_data, status=401)  # 401 Unauthorized status code
    else:
        # Return a JSON response indicating bad request method (not POST)
        response_data = {'status': 'failure', 'message': 'Invalid request method'}
        return JsonResponse(response_data, status=400)  # 400 Bad Request status code



@login_required(login_url='login')
def affichagetableauvalidation1Response(request):
    user = request.user
    id = user.id
    role = user.role_id
    if role == 5 or role == 1 or role == 6:
        qs = Cargaison.objects.filter(
            etat="Validation en cours 1",
            entrepot__ville__affectationville__username_id=id,
        ).values(
            'idcargaison',
            'entrepot_echantillon__laboreception__datereceptionlabo__date',
            'importateur__nomimportateur',
            'entrepot__nomentrepot',
            'entrepot_echantillon__laboreception__codelabo',
            'entrepot_echantillon__laboreception__numcertificatqualite',
            'produit__nomproduit'
        ).order_by(
            '-entrepot_echantillon__laboreception__datereceptionlabo'
        )

        # Get the search value from the request's GET parameters
        search_value = request.GET.get('search[value]', '')

        # Apply search filter to the QuerySet
        if search_value:
            qs = qs.filter(
                Q(entrepot_echantillon__laboreception__datereceptionlabo__icontains=search_value) |
                Q(importateur__nomimportateur__icontains=search_value) |
                Q(entrepot__nomentrepot__icontains=search_value) |
                Q(entrepot_echantillon__laboreception__codelabo__icontains=search_value) |
                Q(entrepot_echantillon__laboreception__numcertificatqualite__icontains=search_value) |
                Q(produit__nomproduit__icontains=search_value)
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
def affichagetableauvalidation2Response(request):
    user = request.user
    id = user.id
    role = user.role_id
    if role == 5 or role == 1 or role == 6 or role == 10:
        qs = Cargaison.objects.filter(
            etat="Validation en cours 2",
            entrepot__ville__affectationville__username_id=id,
        ).values(
            'idcargaison',
            'entrepot_echantillon__laboreception__datereceptionlabo__date',
            'importateur__nomimportateur',
            'entrepot__nomentrepot',
            'entrepot_echantillon__laboreception__codelabo',
            'entrepot_echantillon__laboreception__numcertificatqualite',
            'produit__nomproduit'
        ).order_by(
            '-entrepot_echantillon__laboreception__datereceptionlabo'
        )

        # Get the search value from the request's GET parameters
        search_value = request.GET.get('search[value]', '')

        # Apply search filter to the QuerySet
        if search_value:
            qs = qs.filter(
                Q(entrepot_echantillon__laboreception__datereceptionlabo__icontains=search_value) |
                Q(importateur__nomimportateur__icontains=search_value) |
                Q(entrepot__nomentrepot__icontains=search_value) |
                Q(entrepot_echantillon__laboreception__codelabo__icontains=search_value) |
                Q(entrepot_echantillon__laboreception__numcertificatqualite__icontains=search_value) |
                Q(produit__nomproduit__icontains=search_value)
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
def conformeAjx2(request):
    user = request.user
    role = user.role_id

    if role == 1 or role == 10:
        if request.method == 'POST':
            idcargaison = request.POST.get('idcargaison')
            # print(idcargaison)
            try:
                c = Cargaison.objects.get(idcargaison=idcargaison)
                # print(c.idcargaison)
                # Updated Method
                # Check if ImpressionResultat exists for the Cargaison
                if not ImpressionResultat.objects.filter(idcargaison=c).exists():
                    i = ImpressionResultat(printDate=datetime.now, isConforme=1, isPrinted=0, idcargaison=c)
                    i.save()

                    # A supprimer
                    c.etat = "Conforme aux exigences"
                    c.conformite = "Conforme aux exigences"
                    c.impression = "0"
                    c.dateHeureAnalyseLabo = datetime.now()
                    c.save(update_fields=['etat', 'impression', 'conformite', 'dateHeureAnalyseLabo'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Test result second validation CONFORME",
                        description=f"User has done the second validation for the results for the record {c.idcargaison}",
                    )

                    response_data = {'status': 'success', 'message': 'Cargaison marked as CONFORME'}
                    return JsonResponse(response_data)
                response_data = {}
                return JsonResponse(response_data,status=400)
            except Cargaison.DoesNotExist:
                response_data = {'status': 'failure', 'message': 'Cargaison not found'}
                return JsonResponse(response_data, status=404)  # 404 Not Found status code
        else:
            # Return a JSON response indicating unauthorized access
            response_data = {'status': 'failure', 'message': 'Unauthorized'}
            return JsonResponse(response_data, status=401)  # 401 Unauthorized status code
    else:
        # Return a JSON response indicating bad request method (not POST)
        response_data = {'status': 'failure', 'message': 'Invalid request method'}
        return JsonResponse(response_data, status=400)  # 400 Bad Request status code


@login_required(login_url='login')
def nonconformeAjx2(request):
    user = request.user
    role = user.role_id
    if role == 1 or role == 10:
        if request.method == 'POST':
            idcargaison = request.POST.get('idcargaison')
            # print(idcargaison)
            try:
                c = Cargaison.objects.get(idcargaison=idcargaison)
                # print(c.idcargaison)
                if not ImpressionResultat.objects.filter(idcargaison=c).exists():
                    # Updated Method
                    i = ImpressionResultat(printDate=datetime.now, isConforme=0, isPrinted=0, idcargaison=c)
                    i.save()

                    c.etat = "Non conforme aux exigences"
                    c.impression = "0"
                    c.dateHeureAnalyseLabo = datetime.now()
                    c.save(update_fields=['etat', 'impression', 'dateHeureAnalyseLabo'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Test result second validation NON CONFORME",
                        description=f"User has done the second validation for the results for the record {c.idcargaison}",
                    )

                    response_data = {'status': 'success', 'message': 'Cargaison marked as NON CONFORME'}
                    return JsonResponse(response_data)
                response_data = {}
                return JsonResponse(response_data, status=400)
            except Cargaison.DoesNotExist:
                response_data = {'status': 'failure', 'message': 'Cargaison not found'}
                return JsonResponse(response_data, status=404)  # 404 Not Found status code
        else:
            # Return a JSON response indicating unauthorized access
            response_data = {'status': 'failure', 'message': 'Unauthorized'}
            return JsonResponse(response_data, status=401)  # 401 Unauthorized status code
    else:
        # Return a JSON response indicating bad request method (not POST)
        response_data = {'status': 'failure', 'message': 'Invalid request method'}
        return JsonResponse(response_data, status=400)  # 400 Bad Request status code



# Fonction pour affichage tableu impression des certificats
@login_required(login_url='login')
def responseAffichagetableauimpression(request):
    user = request.user
    role = user.role_id
    ville = AffectationVille.objects.get(username_id=user.id)
    ville = ville.ville_id
    if role == 5 or role == 1:

        qs = Cargaison.objects.filter(
            impressionresultat__isPrinted=0,
            entrepot__ville__idville=ville
        ).annotate(
            dateReceptionLabo=F('entrepot_echantillon__laboreception__datereceptionlabo__date'),
            idImpression=F('impressionresultat__idImpression'),
            numcertificatqualite=F('entrepot_echantillon__laboreception__numcertificatqualite'),
            codelabo=F('entrepot_echantillon__laboreception__codelabo'),
            nomproduit=F('produit__nomproduit'),
            nomimportateur=F('importateur__nomimportateur'),
            nomentrepot=F('entrepot__nomentrepot')
        ).values(
            'idcargaison',
            'dateReceptionLabo',
            'impressionresultat__printDate',
            'idImpression',
            'numcertificatqualite',
            'codelabo',
            'nomproduit',
            'nomimportateur',
            'nomentrepot'
        )

        # Get the search value from the request's GET parameters
        search_value = request.GET.get('search[value]', '')

        # Apply search filter to the QuerySet
        if search_value:
            qs_search = Cargaison.objects.filter(
            entrepot__ville__idville=ville,
            ).annotate(
                dateReceptionLabo=F('entrepot_echantillon__laboreception__datereceptionlabo__date'),
                idImpression=F('impressionresultat__idImpression'),
                numcertificatqualite=F('entrepot_echantillon__laboreception__numcertificatqualite'),
                codelabo=F('entrepot_echantillon__laboreception__codelabo'),
                nomproduit=F('produit__nomproduit'),
                nomimportateur=F('importateur__nomimportateur'),
                nomentrepot=F('entrepot__nomentrepot')
            ).values(
                'idcargaison',
                'dateReceptionLabo',
                'idImpression',
                'impressionresultat__printDate',
                'numcertificatqualite',
                'codelabo',
                'nomproduit',
                'nomimportateur',
                'nomentrepot'
            )
            qs = qs_search.filter(
                Q(codelabo=search_value) |
                Q(nomimportateur=search_value) |
                Q(nomentrepot=search_value)
            )

        # Number of items to show per page
        items_per_page = 10

        print(items_per_page)

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


# Fonction pour impression Certificat
@login_required(login_url='login')
def impressioncertificat(request):
    user = request.user
    id = user.id
    name = user.last_name + ' ' + user.first_name
    poste = user.poste
    ville = AffectationVille.objects.get(username_id=id)
    ville = ville.ville_id
    province = Ville.objects.get(idville=ville)
    province = province.province
    province = province.upper()
    role = user.role_id

    #Recuperation des donnees liees aux signataires
    affect1 = AffectationLaboratoire.objects.get(ville=ville, signGauche=False)
    affect2 = AffectationLaboratoire.objects.get(ville=ville, signGauche=True)
    signDroite = MyUser.objects.get(username=affect1.userId)
    signGauche = MyUser.objects.get(username=affect2.userId)

    #Recuperation du Laboratoire asssocie a la ville
    laboratoireData = ListeLaboratoire.objects.get(denominationLaboratoire=affect1.idLaboratoire)

    #Recuperation des donnees liees a l'Impression
    if request.method == 'POST':
        dataJson = json.loads(request.body)
        pk = dataJson.get('idcargaison')
        print(pk)
        impressionData = ImpressionResultat.objects.get(idcargaison_id=pk)

        print(signGauche)
        print(signDroite)

        d = LaboReception.objects.filter(idcargaison_id=pk).annotate(
            mois=ExtractMonth('datereceptionlabo'),
            annee=ExtractYear('datereceptionlabo')
        ).values('idcargaison_id', 'mois', 'annee')


        for entry in d:
            mois = entry['mois']
            annee = entry['annee']

        if role == 5 or role == 1 :
            td = datetime.today()
            # Recuperation du produit de la cargaison
            p = Produit.objects.get(cargaison=pk)
            produit = p.nomproduit

            # Fecthing object with pk corresponding into database
            cargaison = Cargaison.objects.get(idcargaison=pk)
            echantillon = Entrepot_echantillon.objects.get(idcargaison=pk)
            laboratoire = LaboReception.objects.get(idcargaison=pk)

            printed = ImpressionResultat.objects.get(idcargaison=pk)
            printed.isPrinted = 1
            printed.save(update_fields=['isPrinted'])

            # Test pour afficher les differents rapports

            if produit == 'GASOIL':
                template = 'report/Report1/gasoilreport.html'

                # Resultat Gasoil Fetching data into Database
                try:
                    couleurastm = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=8)[0].valeurResultatChar
                except:
                    couleurastm = ''
                try:
                    aciditetotal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=1)[0].valeurResultat
                except:
                    aciditetotal= ''
                try:
                    soufre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[0].valeurResultat
                except:
                    soufre = ''
                try:
                    massevolumique = ResultatAnalyse.objects.filter(idcargaison=pk,idParametre=21)[0].valeurResultat
                except:
                    massevolumique = ''
                try:
                    massevolumique15 = ResultatAnalyse.objects.filter(idcargaison=pk,idParametre=20)[0].valeurResultat
                except:
                    massevolumique15 = ''
                try:
                    distillation = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[0].valeurResultat
                except:
                    distillation = ''
                try:
                    distillation10 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=11)[0].valeurResultat
                except:
                    distillation10 = ''
                try:
                    distillation20 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=12)[0].valeurResultat
                except:
                    distillation20 = ''
                try:
                    distillation50 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=13)[0].valeurResultat
                except:
                    distillation50 = ''
                try:
                    distillation90 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=15)[0].valeurResultat
                except:
                    distillation90 = ''
                try:
                    pointinitial = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=30)[0].valeurResultat
                except:
                    pointinitial = ''
                try:
                    pointfinal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=29)[0].valeurResultat
                except:
                    pointfinal = ''
                try:
                    pointeclair = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=25)[0].valeurResultat
                except:
                    pointeclair = ''
                try:
                    viscosite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=38)[0].valeurResultat
                except:
                    viscosite = ''
                try:
                    pointecoulement = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=26)[0].valeurResultat
                except:
                    pointecoulement = ''
                try:
                    teneureau = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=35)[0].valeurResultat
                except:
                    teneureau = ''
                try:
                    sediment = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=32)[0].valeurResultat
                except:
                    sediment = ''
                try:
                    corrosion_str = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=6)[0].valeurResultat
                    corrosion = int(corrosion_str)
                except:
                    corrosion = ''
                try:
                    indicecetane = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=19)[0].valeurResultat
                except:
                    indicecetane = ''
                # try:
                #     densite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=49)[0].valeurResultat
                # except:
                #     densite = ''
                try:
                    recuperation362 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=10)[0].valeurResultat
                except:
                    recuperation362 = ''
                try:
                    cendre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=3)[0].valeurResultat
                except:
                    cendre = ''

                data = {
                    'laboratoire': laboratoire,
                    'cargaison': cargaison,
                    'echantillon': echantillon,
                    'annee': annee,
                    'mois': mois,
                    'province': province,
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
                    # 'densite': densite,
                    'recuperation362': recuperation362,
                    'cendre': cendre,
                    'massevolumique15': massevolumique15,
                    'signGauche': signGauche,
                    'signDroite': signDroite,
                    'impressionData': impressionData,
                    'laboratoireData':laboratoireData,
                }

                # Rendered PDF report
                pdf = render_to_pdf(template, data)
                pdf_base64 = base64.b64encode(pdf.getvalue()).decode('utf-8')
                return JsonResponse({'status': 'success', 'pdf_base64': pdf_base64})
                # return HttpResponse(pdf, content_type='application/pdf')

            if produit == 'MOGAS':
                template = 'report/Report1/mogasreport.html'
                # Resultat Gasoil Fetching data into Database
                try:
                    aspect = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=2)[0].valeurResultatChar
                except:
                    aspect=''
                try:
                    odeur = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=22)[0].valeurResultatChar
                except:
                    odeur=''
                try:
                    couleursaybolt = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=8)[0].valeurResultatChar
                except:
                    couleursaybolt=''
                try:
                    soufre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[0].valeurResultat
                except:
                    soufre=''
                try:
                    distillation = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[0].valeurResultat
                except:
                    distillation=''
                try:
                    pointfinal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=29)[0].valeurResultat
                except:
                    pointfinal=''
                try:
                    residu = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=31)[0].valeurResultat
                except:
                    residu=''
                try:
                    corrosion_str = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=7)[0].valeurResultat
                    corrosion = int(corrosion_str)
                except:
                    corrosion=''
                try:
                    pourcent10 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=11)[0].valeurResultat
                except:
                    pourcent10=''
                try:
                    pourcent20 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=12)[0].valeurResultat
                except:
                    pourcent20=''
                try:
                    pourcent50 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=13)[0].valeurResultat
                except:
                    pourcent50=''
                try:
                    pourcent70 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=14)[0].valeurResultat
                except:
                    pourcent70=''
                try:
                    pourcent90 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=15)[0].valeurResultat
                except:
                    pourcent90=''
                try:
                    tensionvapeur = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=36)[0].valeurResultat
                except:
                    tensionvapeur=''
                try:
                    difftemperature = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=9)[0].valeurResultat
                except:
                    difftemperature=''
                try:
                    plomb = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=24)[0].valeurResultat
                except:
                    plomb=''
                try:
                    indiceoctane = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=18)[0].valeurResultat
                except:
                    indiceoctane=''
                try:
                    massevolumique15 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[0].valeurResultat
                except:
                    massevolumique15=''

                data = {
                    'laboratoire': laboratoire,
                    'cargaison': cargaison,
                    'echantillon': echantillon,
                    'annee': annee,
                    'mois': mois,
                    'province': province,
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
                    'signGauche': signGauche,
                    'signDroite': signDroite,
                    'impressionData': impressionData,
                    'laboratoireData':laboratoireData,
                }

                # Rendered PDF report
                pdf = render_to_pdf(template, data)
                pdf_base64 = base64.b64encode(pdf.getvalue()).decode('utf-8')
                return JsonResponse({'status': 'success', 'pdf_base64': pdf_base64})
                # return HttpResponse(pdf, content_type='application/pdf')

            if produit == 'JET A1':
                template = 'report/Report1/jeta1report.html'

                # Resultat Gasoil Fetching data into Database
                try:
                    aspect = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=2)[
                        0].valeurResultatChar
                except:
                    aspect=''
                try:
                    couleursaybolt = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=8)[
                        0].valeurResultatChar
                except:
                    couleursaybolt=''
                try:
                    aciditetotal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=1)[
                        0].valeurResultat
                except:
                    aciditetotal=''
                try:
                    soufre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[
                        0].valeurResultat
                except:
                    soufre=''
                try:
                    soufremercaptan = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=33)[
                        0].valeurResultat
                except:
                    soufremercaptan=''
                try:
                    docteurtest = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=16)[
                        0].valeurResultat
                except:
                    docteurtest=''
                try:
                    distillation = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                        0].valeurResultat
                except:
                    distillation=''
                try:
                    pointinitial = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=30)[
                        0].valeurResultat
                except:
                    pointinitial=''
                try:
                    pointfinal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=29)[
                        0].valeurResultat
                except:
                    pointfinal=''

                try:
                    pointfumee = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=28)[
                        0].valeurResultat
                except:
                    pointfumee=''

                try:
                    pointeclair = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=25)[
                        0].valeurResultat
                except:
                    pointeclair=''

                try:
                    freezingpoint = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=17)[
                        0].valeurResultat
                except:
                    freezingpoint=''

                try:
                    residu = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=31)[
                        0].valeurResultat
                except:
                    residu=''

                try:
                    perte = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=23)[
                        0].valeurResultat
                except:
                    perte=''

                try:
                    massevolumique15 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[
                        0].valeurResultat
                except:
                    massevolumique15=''

                try:
                    viscosite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=37)[
                        0].valeurResultat
                except:
                    viscosite=''

                try:
                    pointinflammabilite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=27)[
                        0].valeurResultat
                except:
                    pointinflammabilite=''

                try:
                    teneureau = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=35)[
                        0].valeurResultat
                except:
                    teneureau=''

                try:
                    corrosion_str = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=5)[
                        0].valeurResultat
                    corrosion = int(corrosion_str)
                except:
                    corrosion=''

                try:
                    conductivite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=4)[
                        0].valeurResultat
                except:
                    conductivite=''

                try:
                    vol10 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=11)[
                        0].valeurResultat
                except:
                    vol10=''

                try:
                    vol20 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=12)[
                        0].valeurResultat
                except:
                    vol20=''
                try:
                    vol30 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                        0].valeurResultat
                except:
                    vol30=''
                try:
                    vol40 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                        0].valeurResultat
                except:
                    vol40=''
                try:
                    vol50 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=13)[
                        0].valeurResultat
                except:
                    vol50=''
                try:
                    vol60 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                        0].valeurResultat
                except:
                    vol60=''
                try:
                    vol70 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=14)[
                        0].valeurResultat
                except:
                    vol70=''
                try:
                    vol80 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                        0].valeurResultat
                except:
                    vol80=''
                try:
                    vol90 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=15)[
                        0].valeurResultat
                except:
                    vol90=''

                data = {
                    'laboratoire': laboratoire,
                    'cargaison': cargaison,
                    'echantillon': echantillon,
                    'annee': annee,
                    'mois': mois,
                    'province': province,
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
                    'signGauche': signGauche,
                    'signDroite': signDroite,
                    'impressionData': impressionData,
                    'laboratoireData':laboratoireData,
                }
                # Rendered PDF report
                pdf = render_to_pdf(template, data)
                pdf_base64 = base64.b64encode(pdf.getvalue()).decode('utf-8')
                return JsonResponse({'status': 'success', 'pdf_base64': pdf_base64})
                # return HttpResponse(pdf, content_type='application/pdf')

            if produit == 'PETROLE LAMPANT':
                template = 'report/Report1/petrolereport.html'

                # Resultat Gasoil Fetching data into Database
                try:
                    aspect = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=2)[
                        0].valeurResultatChar
                except:
                    aspect = ''
                try:
                    couleursaybolt = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=8)[
                        0].valeurResultatChar
                except:
                    couleursaybolt = ''
                try:
                    aciditetotal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=1)[
                        0].valeurResultat
                except:
                    aciditetotal = ''
                try:
                    soufre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[
                        0].valeurResultat
                except:
                    soufre = ''
                try:
                    soufremercaptan = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=33)[
                        0].valeurResultat
                except:
                    soufremercaptan = ''
                try:
                    docteurtest = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=16)[
                        0].valeurResultat
                except:
                    docteurtest = ''
                try:
                    distillation = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                        0].valeurResultat
                except:
                    distillation = ''
                try:
                    pointinitial = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=30)[
                        0].valeurResultat
                except:
                    pointinitial = ''
                try:
                    pointfinal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=29)[
                        0].valeurResultat
                except:
                    pointfinal = ''

                try:
                    pointfumee = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=28)[
                        0].valeurResultat
                except:
                    pointfumee = ''

                try:
                    pointeclair = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=25)[
                        0].valeurResultat
                except:
                    pointeclair = ''

                try:
                    freezingpoint = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=17)[
                        0].valeurResultat
                except:
                    freezingpoint = ''

                try:
                    residu = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=31)[
                        0].valeurResultat
                except:
                    residu = ''

                try:
                    perte = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=23)[
                        0].valeurResultat
                except:
                    perte = ''

                try:
                    massevolumique15 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[
                        0].valeurResultat
                except:
                    massevolumique15 = ''

                try:
                    viscosite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=37)[
                        0].valeurResultat
                except:
                    viscosite = ''

                try:
                    pointinflammabilite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=27)[
                        0].valeurResultat
                except:
                    pointinflammabilite = ''

                try:
                    teneureau = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=35)[
                        0].valeurResultat
                except:
                    teneureau = ''

                try:
                    corrosion_str = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=5)[
                        0].valeurResultat
                    corrosion = int(corrosion_str)

                except:
                    corrosion = ''

                try:
                    conductivite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=4)[
                        0].valeurResultat
                except:
                    conductivite = ''

                try:
                    vol10 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=11)[
                        0].valeurResultat
                except:
                    vol10 = ''

                try:
                    vol20 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=12)[
                        0].valeurResultat
                except:
                    vol20 = ''
                try:
                    vol30 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                        0].valeurResultat
                except:
                    vol30 = ''
                try:
                    vol40 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                        0].valeurResultat
                except:
                    vol40 = ''
                try:
                    vol50 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=13)[
                        0].valeurResultat
                except:
                    vol50 = ''
                try:
                    vol60 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=44)[
                        0].valeurResultat
                except:
                    vol60 = ''
                try:
                    vol70 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                        0].valeurResultat
                except:
                    vol70 = ''
                try:
                    vol80 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                        0].valeurResultat
                except:
                    vol80 = ''
                try:
                    vol90 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=15)[
                        0].valeurResultat
                except:
                    vol90 = ''

                data = {
                    'laboratoire': laboratoire,
                    'cargaison': cargaison,
                    'echantillon': echantillon,
                    'annee': annee,
                    'mois': mois,
                    'province': province,
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
                    'signGauche': signGauche,
                    'signDroite': signDroite,
                    'impressionData': impressionData,
                    'laboratoireData':laboratoireData,
                }

                # Rendered PDF report
                pdf = render_to_pdf(template, data)
                pdf_base64 = base64.b64encode(pdf.getvalue()).decode('utf-8')
                return JsonResponse({'status': 'success', 'pdf_base64': pdf_base64})
                # return HttpResponse(pdf, content_type='application/pdf')

        else:
            return ('logout')
    else:
        return redirect('logout')




#Ajax response
@login_required(login_url='login')
def responseAffichageanalyse(request):
    user = request.user
    id = user.id
    role = user.role_id
    if role == 5 or role == 1:
        qs = Cargaison.objects.filter(etat='Analyse Labo en cours',
                                      entrepot__ville__affectationville__username_id=id,
                                     ).values(
                                    'idcargaison',
                                    'entrepot_echantillon__laboreception__datereceptionlabo__date',
                                    'entrepot_echantillon__laboreception__codelabo',
                                    'entrepot_echantillon__numrappechauto',
                                    'numdos',
                                    'immatriculation',
                                    'produit__nomproduit'
                                    ).order_by('-entrepot_echantillon__laboreception__datereceptionlabo')

        qs2 = Cargaison.objects.filter(etat='Refaire',
                                      entrepot__ville__affectationville__username_id=id,
                                      ).values(
                                    'idcargaison',
                                    'entrepot_echantillon__laboreception__datereceptionlabo__date',
                                    'entrepot_echantillon__laboreception__codelabo',
                                    'entrepot_echantillon__numrappechauto',
                                    'produit__nomproduit'
                                    ).order_by('-entrepot_echantillon__laboreception__datereceptionlabo')

        # Get the search value from the request's GET parameters
        search_value = request.GET.get('search[value]', '')

        # Apply search filter to the QuerySet
        if search_value:
            qs = qs.filter(
                Q(entrepot_echantillon__laboreception__codelabo=search_value)
            )

        # Number of items to show per page
        items_per_page = 13

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



#Saisie saisieResultat Ajax
@login_required(login_url='login')
def saisieResultatAjax(request):
    pk = request.GET.get('idcargaison','')
    print(pk)
    e = Entrepot_echantillon.objects.get(idcargaison=pk)
    a = LaboReception.objects.get(idcargaison=e)
    a = a.codelabo

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

    # Serialize the raw SQL queryset results manually into a list of dictionaries
    data = [
        {
            'idParametre': item.idParametre,
            'idcargaison': item.idcargaison,
            'nomproduit': item.nomproduit,
            'nomParametre': item.nomParametre,
            'valeurResultat': item.valeurResultat,
            'valeurResultatChar': item.valeurResultatChar
        }
        for item in qs
    ]

    # Return JSON response with the data
    return JsonResponse({
        'data': data,
        'codeLabo': a,
    })


@login_required(login_url='login')
def saisieResultatParametreAjax(request):
    user = request.user
    if request.method == 'POST':
        parametreId = request.POST['idParametre']
        idcargaison = request.POST['idcargaison']
        inputValue = request.POST['inputValue']
        cargaison = Cargaison.objects.get(idcargaison=idcargaison)
        parametre = ParametresProduits.objects.get(idParametre=parametreId)

        if parametre.idParametre == 2 or parametre.idParametre == 8 or parametre.idParametre == 22:
            try:
                r = ResultatAnalyse.objects.get(idParametre=parametre,idcargaison=cargaison)
                r.valeurResultatChar = inputValue
                r.save(update_fields=['valeurResultatChar'])

                UserActivityLog.objects.create(
                    user=user,
                    action="Test result input",
                    description=f"User has input the test result for the record {cargaison.idcargaison}",
                )
                return JsonResponse({'status': 'success'})
            except:
                r = ResultatAnalyse(valeurResultatChar=inputValue, idParametre=parametre, idcargaison=cargaison)
                r.save()
                UserActivityLog.objects.create(
                    user=user,
                    action="Test result input",
                    description=f"User has input the test result for the record {cargaison.idcargaison}",
                )
                return JsonResponse({'status': 'success'})
        else:
            try:
                r = ResultatAnalyse.objects.get(idParametre=parametre,idcargaison=cargaison)
                r.valeurResultat = inputValue
                r.save(update_fields=['valeurResultat'])
                UserActivityLog.objects.create(
                    user=user,
                    action="Test result input",
                    description=f"User has input the test result for the record {cargaison.idcargaison}",
                )
                return JsonResponse({'status': 'success'})
            except:
                r = ResultatAnalyse(valeurResultat=inputValue, idParametre=parametre, idcargaison=cargaison)
                r.save()
                UserActivityLog.objects.create(
                    user=user,
                    action="Test result input",
                    description=f"User has input the test result for the record {cargaison.idcargaison}",
                )
                return JsonResponse({'status': 'success'})
    else:
        redirect('logout')


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
        context={
            'count':count
        }
        return render(request,template, context)
    else:
        return redirect('logout')


@login_required(login_url='login')
def affichageAnalyseRefaireResponse(request):
    user = request.user
    id = user.id
    role = user.role_id
    if role == 5 or role == 1:
        qs = Cargaison.objects.filter(
            etat="Refaire",
            entrepot__ville__affectationville__username_id=id
            ).values(
            'idcargaison',
            'dateheurecargaison__date',
            'entrepot_echantillon__laboreception__datereceptionlabo__date',
            'entrepot_echantillon__laboreception__codelabo',
            'entrepot_echantillon__numrappechauto',
            'produit__nomproduit',
            'immatriculation',
            'numdos',
            'entrepot_echantillon__numrappechauto',
            ).order_by('-entrepot_echantillon__dateechantillonage__date')

        # Get the search value from the request's GET parameters
        search_value = request.GET.get('search[value]', '')

        # Apply search filter to the QuerySet
        if search_value:
            qs = qs.filter(
                Q(entrepot_echantillon__laboreception__codelabo__icontains=search_value)
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


@login_required(login_url='login')
def echantillonRecus(request):
    user = request.user
    role = user.role_id
    if role == 5 or role == 1 or role == 6:
        template = 'labo_rapport.html'
        context={}
        return render(request,template,context)
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
            'entrepot_echantillon__dateechantillonage__date',
            'entrepot_echantillon__laboreception__datereceptionlabo__date',
            'entrepot_echantillon__laboreception__codelabo',
            'entrepot_echantillon__numrappechauto',
            'entrepot_echantillon__laboreception__numcertificatqualite',
            'produit__nomproduit',
            'numdos',
            ).order_by('-entrepot_echantillon__laboreception__datereceptionlabo__date')

        # Get the search value from the request's GET parameters
        search_value = request.GET.get('search[value]', '')

        # Apply search filter to the QuerySet
        if search_value:
            qs = qs.filter(
                Q(entrepot_echantillon__laboreception__codelabo__icontains=search_value)
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
        produit = request.POST['produit']
        idcargaison = request.POST['idcargaison']
        c=Cargaison.objects.get(idcargaison=idcargaison)
        p=Produit.objects.get(idproduit=produit)
        c.produit = p
        c.save(update_fields=['produit'])
        # print(produit)
        # print(idcargaison)
        response_data = {"message": "Form submitted successfully"}
        return JsonResponse(response_data, status=200)
    else:
        # Handle other HTTP methods or errors if needed
        response_data = {"message": "Invalid request method"}
        return JsonResponse(response_data, status=400)



@login_required(login_url='login')
def clearSaisie(request):
    if request.method == 'POST':
        parametreId = request.POST.get('rowId')  # Get the rowId from POST data
        idcargaison = request.POST.get('idcargaison')  # Get the idcargaison from POST data
        inputValue = ""  # Define inputValue (you need to get this from your POST data)
        print(parametreId)
        print(idcargaison)
        # Check if the user is allowed to clear values based on parametre.idParametre
        try:
            parametre = ParametresProduits.objects.get(idParametre=parametreId)
            cargaison = Cargaison.objects.get(idcargaison=idcargaison)
            print(parametre.nomParametre)

            if parametre.idParametre in [2, 8, 22]:
                r, created = ResultatAnalyse.objects.get_or_create(idParametre=parametre, idcargaison=cargaison)
                r.valeurResultatChar = inputValue
                r.save(update_fields=['valeurResultatChar'])
            else:
                r, created = ResultatAnalyse.objects.get_or_create(idParametre=parametre, idcargaison=cargaison)
                r.valeurResultat = None
                r.save(update_fields=['valeurResultat'])

            return JsonResponse({'status': 'success'})
        except ParametresProduits.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Parametre not found'}, status=400)
        except Cargaison.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Cargaison not found'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
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
        'numdos','entrepot_echantillon__numrappechauto','entrepot_echantillon__dateechantillonage',
        'entrepot__nomentrepot','importateur__nomimportateur',
        'produit__nomproduit','entrepot_echantillon__qte'
    )
    table = RapportLaboratoireEnAttenteReception(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)

    context = {'table': table}
    return render(request,template,context)

@login_required(login_url='login')
def enchAttenteReception2(request):
    user = request.user.id
    template = 'laboRapport2.html'
    qs = Cargaison.objects.filter(
        etat='Echantillonner',
        entrepot__ville__affectationville__username_id=user
    ).values(
        'numdos','entrepot_echantillon__numrappechauto','entrepot_echantillon__dateechantillonage',
        'entrepot__nomentrepot','importateur__nomimportateur',
        'produit__nomproduit','entrepot_echantillon__qte'
    )
    table = RapportLaboratoireEnAttenteReception(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)

    context = {'table': table}
    return render(request,template,context)


@login_required(login_url='login')
def enchAttenteReceptionExport(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        etat='Echantillonner',
        entrepot__ville__affectationville__username_id=user
    ).values(
        'numdos','entrepot_echantillon__numrappechauto','entrepot_echantillon__dateechantillonage',
        'entrepot__nomentrepot','importateur__nomimportateur',
        'produit__nomproduit','entrepot_echantillon__qte'
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
        'numdos','entrepot_echantillon__numrappechauto','entrepot_echantillon__dateechantillonage',
        'entrepot__nomentrepot','importateur__nomimportateur',
        'produit__nomproduit','entrepot_echantillon__qte'
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
        'entrepot_echantillon__dateechantillonage','entrepot_echantillon__laboreception__datereceptionlabo','numdos',
        'entrepot_echantillon__numrappechauto','entrepot_echantillon__laboreception__codelabo','entrepot__nomentrepot',
        'importateur__nomimportateur','produit__nomproduit',
        'entrepot_echantillon__qte'
    )
    table = RapportLaboratoireEnAttenteResultat(qs)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    context = {'table': table}
    return (render(request, template, context)



@login_required(login_url='login'))
def enchAttenteResultat2(request):
    user = request.user.id
    template = 'laboRapportEnAttenteAnalyse2.html'
    qs = Cargaison.objects.filter(
        etat='Analyse Labo en cours',
        entrepot__ville__affectationville__username_id=user,
    ).values(
        'entrepot_echantillon__dateechantillonage','entrepot_echantillon__laboreception__datereceptionlabo','numdos',
        'entrepot_echantillon__numrappechauto','entrepot_echantillon__laboreception__codelabo','entrepot__nomentrepot',
        'importateur__nomimportateur','produit__nomproduit',
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
        'entrepot_echantillon__dateechantillonage','entrepot_echantillon__laboreception__datereceptionlabo','numdos',
        'entrepot_echantillon__numrappechauto','entrepot_echantillon__laboreception__codelabo','entrepot__nomentrepot',
        'importateur__nomimportateur','produit__nomproduit',
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
        'entrepot_echantillon__dateechantillonage','entrepot_echantillon__laboreception__datereceptionlabo','numdos',
        'entrepot_echantillon__numrappechauto','entrepot_echantillon__laboreception__codelabo','entrepot__nomentrepot',
        'importateur__nomimportateur','produit__nomproduit',
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
        'entrepot_echantillon__dateechantillonage','entrepot_echantillon__laboreception__datereceptionlabo','numdos',
        'entrepot_echantillon__numrappechauto','entrepot_echantillon__laboreception__codelabo','entrepot_echantillon__laboreception__numcertificatqualite',
        'entrepot__nomentrepot','importateur__nomimportateur',
        'produit__nomproduit'
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
        'entrepot_echantillon__dateechantillonage','entrepot_echantillon__laboreception__datereceptionlabo','numdos',
        'entrepot_echantillon__numrappechauto','entrepot_echantillon__laboreception__codelabo','entrepot_echantillon__laboreception__numcertificatqualite',
        'entrepot__nomentrepot','importateur__nomimportateur',
        'produit__nomproduit'
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
        'entrepot_echantillon__dateechantillonage','entrepot_echantillon__laboreception__datereceptionlabo','numdos',
        'entrepot_echantillon__numrappechauto','entrepot_echantillon__laboreception__codelabo','entrepot_echantillon__laboreception__numcertificatqualite',
        'entrepot__nomentrepot','importateur__nomimportateur','impressionresultat__printDate',
        'produit__nomproduit'
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
        'entrepot_echantillon__dateechantillonage','entrepot_echantillon__laboreception__datereceptionlabo','numdos',
        'entrepot_echantillon__numrappechauto','entrepot_echantillon__laboreception__codelabo','entrepot_echantillon__laboreception__numcertificatqualite',
        'entrepot__nomentrepot','importateur__nomimportateur','impressionresultat__printDate',
        'produit__nomproduit'
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
        'entrepot_echantillon__dateechantillonage','entrepot_echantillon__laboreception__datereceptionlabo','numdos',
        'entrepot_echantillon__numrappechauto','entrepot_echantillon__laboreception__codelabo','entrepot_echantillon__laboreception__numcertificatqualite',
        'entrepot__nomentrepot','importateur__nomimportateur','impressionresultat__printDate',
        'produit__nomproduit'
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
        'entrepot_echantillon__dateechantillonage','entrepot_echantillon__laboreception__datereceptionlabo','numdos',
        'entrepot_echantillon__numrappechauto','entrepot_echantillon__laboreception__codelabo','entrepot_echantillon__laboreception__numcertificatqualite',
        'entrepot__nomentrepot','importateur__nomimportateur','impressionresultat__printDate',
        'produit__nomproduit'
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
    template ='laboRapportsCq.html'
    form = FiltresDate()
    context = {'form':form}
    return render(request,template,context)


@login_required(login_url='login')
def rapportCq2(request):
    template ='laboRapportsCq2.html'
    form = FiltresDate()
    context = {'form':form}
    return render(request,template,context)


@login_required(login_url='login')
def rapportCqResponse(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user,
        entrepot_echantillon__laboreception__isnull=False
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
        'entrepot_echantillon__laboreception__codelabo',
        'entrepot_echantillon__dateechantillonage__date',
        'entrepot_echantillon__laboreception__numcertificatqualite',
        'entrepot_echantillon__laboreception__datereceptionlabo__date',
        'conformiteProduit',
        'entrepot__nomentrepot',
        'importateur__nomimportateur',
        'immatriculation',
        'produit__nomproduit','immatriculation','produit__nomproduit'
    ).order_by('-entrepot_echantillon__laboreception__datereceptionlabo')

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
        entrepot_echantillon__laboreception__isnull=False
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
        'entrepot_echantillon__laboreception__codelabo',
        'entrepot_echantillon__dateechantillonage',
        'entrepot_echantillon__laboreception__numcertificatqualite',
        'entrepot_echantillon__laboreception__datereceptionlabo',
        'conformiteProduit',
        'entrepot__nomentrepot',
        'importateur__nomimportateur',
        'immatriculation',
        'produit__nomproduit',
    ).order_by('-entrepot_echantillon__laboreception__datereceptionlabo')

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
    template ='laboRapportsCQFiltres.html'
    # Get the search value from the request's GET parameters
    if request.method == 'POST':
        date_d = request.POST['date_d']
        date_f = request.POST['date_f']

        request.session['date_d'] = date_d
        request.session['date_f'] = date_f

        form = FiltresDate()
        context = {'form':form}
        return render(request,template,context)
    else:
        return redirect('receptionRapports')


@login_required(login_url='login')
def rapportCqfiltres2(request):
    template ='laboRapportsCQFiltres2.html'
    # Get the search value from the request's GET parameters
    if request.method == 'POST':
        date_d = request.POST['date_d']
        date_f = request.POST['date_f']

        request.session['date_d'] = date_d
        request.session['date_f'] = date_f

        form = FiltresDate()
        context = {'form':form}
        return render(request,template,context)
    else:
        return redirect('receptionRapports')


@login_required(login_url='login')
def rapportCqfiltresResponse(request):
    user = request.user.id
    ville = AffectationVille.objects.filter(username_id=user).values_list('ville_id', flat=True)
    qs = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user,
        entrepot_echantillon__laboreception__isnull=False
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
        'entrepot_echantillon__laboreception__codelabo',
        'entrepot_echantillon__dateechantillonage',
        'entrepot_echantillon__laboreception__numcertificatqualite',
        'entrepot_echantillon__laboreception__datereceptionlabo',
        'conformiteProduit',
        'entrepot__nomentrepot',
        'importateur__nomimportateur',
        'immatriculation',
        'produit__nomproduit',
    ).order_by('-entrepot_echantillon__laboreception__datereceptionlabo')

    date_d = request.session['date_d']
    date_f = request.session['date_f']

    # Apply search filter to the QuerySet
    if date_d and date_f:
        qs = qs.filter(
            entrepot_echantillon__laboreception__datereceptionlabo__date__range=(date_d,date_f)
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
        entrepot_echantillon__laboreception__isnull=False
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
        'entrepot_echantillon__laboreception__codelabo',
        'entrepot_echantillon__dateechantillonage',
        'entrepot_echantillon__laboreception__numcertificatqualite',
        'entrepot_echantillon__laboreception__datereceptionlabo',
        'conformiteProduit',
        'entrepot__nomentrepot',
        'importateur__nomimportateur',
        'immatriculation',
        'produit__nomproduit',
    ).order_by('-entrepot_echantillon__laboreception__datereceptionlabo')

    date_d = request.session['date_d']
    date_f = request.session['date_f']

    # Apply search filter to the QuerySet
    if date_d and date_f:
        qs = qs.filter(
            entrepot_echantillon__laboreception__datereceptionlabo__date__range=(date_d,date_f)
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
def bulkConforme1(request):
    user = request.user
    role = user.role_id

    if role == 1 or role == 6:
        if request.method == 'POST':
            selectedRows = request.POST.getlist('selectedRowIds[]')
            for data in selectedRows:
                try:
                    c = Cargaison.objects.get(idcargaison=data)
                    c.etat = "Validation en cours 2"
                    c.conformite = "Conforme aux exigences"
                    c.impression = "0"
                    c.save(update_fields=['etat', 'conformite', 'impression'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Test result first validation CONFORME",
                        description=f"User has done the first validation for the results for the record {c.idcargaison}",
                    )

                except Cargaison.DoesNotExist:
                    return JsonResponse({'message': 'An error occured'}, status=400)

            return JsonResponse({'message': 'Request processed successfully.'}, status=200)
        else:
            # If the request method is not POST or it's not an AJAX request, return an error
            return JsonResponse({'error': 'Invalid request.'}, status=400)
    # If the request method is not POST or it's not an AJAX request, return an error
    return JsonResponse({'error': 'Invalid request.'}, status=400)



@login_required(login_url='login')
def bulkNonConforme1(request):
    user = request.user
    role = user.role_id

    if role == 1 or role == 6:
        if request.method == 'POST':
            selectedRows = request.POST.getlist('selectedRowIds[]')
            for data in selectedRows:
                try:
                    c = Cargaison.objects.get(idcargaison=data)
                    print(c.idcargaison)
                    c.etat = "Validation en cours 2"
                    c.conformite = "Non conforme aux exigences"
                    c.impression = "0"
                    c.save(update_fields=['etat', 'conformite', 'impression'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Test result first validation NON CONFORME",
                        description=f"User has done the first validation for the results for the record {c.idcargaison}",
                    )

                except Cargaison.DoesNotExist:
                    return JsonResponse({'message': 'An error occured'}, status=400)

            return JsonResponse({'message': 'Request processed successfully.'}, status=200)
        else:
            # If the request method is not POST or it's not an AJAX request, return an error
            return JsonResponse({'error': 'Invalid request.'}, status=400)
    # If the request method is not POST or it's not an AJAX request, return an error
    return JsonResponse({'error': 'Invalid request.'}, status=400)



@login_required(login_url='login')
def bulkRefaire1(request):
    user = request.user
    role = user.role_id

    if role == 1 or role == 6:
        if request.method == 'POST':
            selectedRows = request.POST.getlist('selectedRowIds[]')
            for data in selectedRows:
                try:
                    c = Cargaison.objects.get(idcargaison=data)

                    c.etat = "Refaire"

                    c.save(update_fields=['etat'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Request to re-do the Test",
                        description=f"User has requested that the record  {c.idcargaison} test need to be done again",
                    )

                except Cargaison.DoesNotExist:
                    return JsonResponse({'message': 'An error occured'}, status=400)

            return JsonResponse({'message': 'Request processed successfully.'}, status=200)
        else:
            # If the request method is not POST or it's not an AJAX request, return an error
            return JsonResponse({'error': 'Invalid request.'}, status=400)
    # If the request method is not POST or it's not an AJAX request, return an error
    return JsonResponse({'error': 'Invalid request.'}, status=400)





@login_required(login_url='login')
def bulkConforme2(request):
    user = request.user
    role = user.role_id

    if role == 1 or role == 6:
        if request.method == 'POST':
            selectedRows = request.POST.getlist('selectedRowIds[]')
            for data in selectedRows:
                try:
                    c = Cargaison.objects.get(idcargaison=data)

                    # Updated Method
                    i = ImpressionResultat(printDate=datetime.now, isConforme=1, isPrinted=0, idcargaison=c)
                    i.save()

                    # A supprimer
                    c.etat = "Conforme aux exigences"
                    c.conformite = "Conforme aux exigences"
                    c.impression = "0"
                    c.dateHeureAnalyseLabo = datetime.now()

                    #Activity Log
                    UserActivityLog.objects.create(
                        user=user,
                        action="Test result second validation CONFORME",
                        description=f"User has done the second validation for the results for the record {c.idcargaison}",
                    )

                    c.save(update_fields=['etat', 'impression', 'conformite', 'dateHeureAnalyseLabo'])
                except Cargaison.DoesNotExist:
                    return JsonResponse({'message': 'An error occured'}, status=400)

            return JsonResponse({'message': 'Request processed successfully.'}, status=200)
        else:
            # If the request method is not POST or it's not an AJAX request, return an error
            return JsonResponse({'error': 'Invalid request.'}, status=400)
    # If the request method is not POST or it's not an AJAX request, return an error
    return JsonResponse({'error': 'Invalid request.'}, status=400)



@login_required(login_url='login')
def bulkNonConforme2(request):
    user = request.user
    role = user.role_id

    if role == 1 or role == 6:
        if request.method == 'POST':
            selectedRows = request.POST.getlist('selectedRowIds[]')
            for data in selectedRows:
                try:
                    c = Cargaison.objects.get(idcargaison=data)

                    # Updated Method
                    i = ImpressionResultat(printDate=datetime.now, isConforme=0, isPrinted=0, idcargaison=c)
                    i.save()

                    c.etat = "Non conforme aux exigences"
                    c.impression = "0"
                    c.dateHeureAnalyseLabo = datetime.now()
                    c.save(update_fields=['etat', 'impression', 'dateHeureAnalyseLabo'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Test result second validation NON CONFORME",
                        description=f"User has done the second validation for the results for the record {c.idcargaison}",
                    )

                except Cargaison.DoesNotExist:
                    return JsonResponse({'message': 'An error occured'}, status=400)

            return JsonResponse({'message': 'Request processed successfully.'}, status=200)
        else:
            # If the request method is not POST or it's not an AJAX request, return an error
            return JsonResponse({'error': 'Invalid request.'}, status=400)
    # If the request method is not POST or it's not an AJAX request, return an error
    return JsonResponse({'error': 'Invalid request.'}, status=400)



@login_required(login_url='login')
def bulkRefaire2(request):
    user = request.user
    role = user.role_id

    if role == 1 or role == 6:
        if request.method == 'POST':
            selectedRows = request.POST.getlist('selectedRowIds[]')
            for data in selectedRows:
                try:
                    c = Cargaison.objects.get(idcargaison=data)

                    c.etat = "Refaire"

                    c.save(update_fields=['etat'])

                    UserActivityLog.objects.create(
                        user=user,
                        action="Request to re-do the Test",
                        description=f"User has requested that the record  {c.idcargaison} test need to be done again",
                    )


                except Cargaison.DoesNotExist:
                    return JsonResponse({'message': 'An error occured'}, status=400)

            return JsonResponse({'message': 'Request processed successfully.'}, status=200)
        else:
            # If the request method is not POST or it's not an AJAX request, return an error
            return JsonResponse({'error': 'Invalid request.'}, status=400)
    # If the request method is not POST or it's not an AJAX request, return an error
    return JsonResponse({'error': 'Invalid request.'}, status=400)



# Fonction pour impression Certificat
@login_required(login_url='login')
def impressionCertificatBulk(request):
    user = request.user
    id = user.id
    name = user.last_name + ' ' + user.first_name
    poste = user.poste
    ville = AffectationVille.objects.get(username_id=id)
    ville = ville.ville_id
    province = Ville.objects.get(idville=ville)
    province = province.province
    province = province.upper()
    role = user.role_id

    selectedRows = request.POST.getlist('selectedRowIds[]')


    # Recuperation des donnees liees aux signataires
    affect1 = AffectationLaboratoire.objects.get(ville=ville, signGauche=False)
    affect2 = AffectationLaboratoire.objects.get(ville=ville, signGauche=True)
    signDroite = MyUser.objects.get(username=affect1.userId)
    signGauche = MyUser.objects.get(username=affect2.userId)

    signGauche_data = {
        'first_name': signGauche.first_name,
        'last_name': signGauche.last_name,
        # Add any other required fields
    }

    signDroite_data = {
        'first_name': signDroite.first_name,
        'last_name': signDroite.last_name,
        # Add any other required fields
    }

    # Recuperation du Laboratoire asssocie a la ville
    laboratoireData = ListeLaboratoire.objects.get(denominationLaboratoire=affect1.idLaboratoire)

    laboratoireName = laboratoireData.denominationLaboratoire
    #
    #     {
    #     'laboratoireName': laboratoireData.denominationLaboratoire,
    #     'laboratoireType': laboratoireData.typeLaboratoire,
    # }
    #
    # print("Print BULK")
    # print(laboratoireData['laboratoireName'])
    # print(laboratoireData['laboratoireType'])


    # Start Celery task to export report asynchronously
    result = app.send_task('labo.tasks.generate_bulk_pdf', args=[selectedRows,province,signGauche_data,signDroite_data,laboratoireName])

    # Retrieve the task ID
    task_id = result.id

    message = "Export task started. Task ID: {}".format(task_id)
    return JsonResponse({'task_id': task_id})



