import base64

from django.shortcuts import render, redirect
from .tables import *
from enreg.models import *
from django.core.exceptions import BadRequest
from accounts.models import *
from .forms import *
from labo.utils import render_to_pdf
from xhtml2pdf import pisa
from io import BytesIO, StringIO
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
import math
from django.db.models import Q, Count
from django_tables2.paginators import LazyPaginator
from django_tables2.export.export import TableExport
from django_tables2 import RequestConfig
from datetime import date
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from .numrappech import numRappEch
from .calculs import *


#Sending email
from django.core.mail import send_mail, EmailMessage
from django.core.cache import cache


# Gestion des echantillonages
class GestionEchantillonage():
    # Methode permettant l'affichage du tableau d'echantillonage
    @login_required(login_url='login')
    def tableauechantillonnage(request):
        user = request.user
        role = user.role_id
        id = user.id
        template = 'entrepot.html'
        today = date.today()
        request.session['url'] = request.get_full_path()
        form = Echantilloner(request.POST or None)

        if role == 3 or role == 1 or role == 9:
            qs1 = Cargaison.objects.filter(etat="En attente d'echantillonage", entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
            qs2 = Cargaison.objects.filter(entrepot__affectationentrepot__username_id=id).filter(
                Q(rapechctrl=1) | Q(etat="Echantillonner")).order_by('-dateheurecargaison')
            table = EchantillonTable(qs1, prefix="1_")
            # table1 = CargaisonEnAttenteRequisition(qs, prefix="2_")
            table2 = RapportEchantillonage(qs2, prefix='3_')
            RequestConfig(request, paginate={"per_page": 5}).configure(table)
            # RequestConfig(request, paginate={"per_page": 5}).configure(table1)
            RequestConfig(request, paginate={"per_page": 5}).configure(table2)

            # #Compteur de la page principale de l'entrepot
            n = Cargaison.objects.filter(etat='En attente requisition',entrepot__affectationentrepot__username_id=id).count()
            d = Cargaison.objects.filter(impressionresultat__isConforme=1,entrepot__affectationentrepot__username_id=id).count()
            i = Cargaison.objects.filter(etatInspection=1,entrepot__affectationentrepot__username_id=id).count()
            x= ImpressionResultat.objects.filter(idcargaison__entrepot__affectationentrepot__username_id=id).filter(Q(idcargaison__toBeConsignated=1)|Q(idcargaison__toBeRefouler=1)).filter(Q(idcargaison__isRefouler=0)|Q(idcargaison__isConsignated=0)).count()

            return render(request, template, {
                'cargaison': table,
                'cargaison2': table2,
                'form': form,
                'n': n,
                'd': d,
                'i': i,
                'x': x,
            })
        else:
            return redirect('logout')

#Fonction d'affichage des resultats des compteurs
    @login_required(login_url='login')
    def c1(request):
        user = request.user
        id = user.id
        today = date.today()
        request.session['url'] = request.get_full_path()
        role = user.role_id
        form = Echantilloner(request.POST or None)

        if role == 1 or role == 3 or role == 9:
            qs = Cargaison.objects.filter(
                Q(etat="En attente d'echantillonage") | Q(tampon='0') | Q(etat="En attente requisition")).filter(
                entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
            table = EchantillonTable(qs, prefix="1_")
            RequestConfig(request, paginate={"per_page": 12}).configure(table)

            # #Compteur de la page principale de l'entrepot
            n = Cargaison.objects.filter(
                Q(etat='En attente requisition') | Q(tampon='0') | Q(etat="En attente d'echantillonage")).filter(
                entrepot__affectationentrepot__username_id=id).count()

            d = Cargaison.objects.filter(
                Q(etat='En attente de dechargement') | Q(Q(etat='Conforme aux exigences'))).filter(
                entrepot__affectationentrepot__username_id=id).count()

            r = Cargaison.objects.filter(Q(etat='En attente requisition') | Q(tampon='0')).filter(
                entrepot__affectationentrepot__username_id=id).count()

            o = Cargaison.objects.filter(Q(etat='En attente de dechargement') | Q(etat='Conforme aux exigences'),
                                         entrepot__affectationentrepot__username_id=id).count()

            x = Entrepot_echantillon.objects.filter(
                Q(nonConformiteProduit=True) | Q(idcargaison__controlOrganoleptique=True),
                idcargaison__entrepot__affectationentrepot__username_id=id).count()

            return render(request, 'entrepot.html', {
                'cargaison': table,
                'n': n,
                'd': d,
                'r': r,
                'o': o,
                'x': x,
                'form':form,
            })
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def c2(request):
        user = request.user
        id = user.id
        today = date.today()
        role = user.role_id
        form = Echantilloner(request.POST or None)

        request.session['url'] = request.get_full_path()
        if role == 1 or role == 3 or role == 9:

            table = EchantillonTable(Cargaison.objects.filter(Q(etat='En attente requisition') | Q(tampon='0')).filter(
                entrepot__affectationentrepot__username_id=id,
                dateheurecargaison__date=today).order_by('-dateheurecargaison'))

            RequestConfig(request, paginate={"per_page": 20}).configure(table)

            # #Compteur de la page principale de l'entrepot
            n = Cargaison.objects.filter(
                Q(etat='En attente requisition') | Q(tampon='0') | Q(etat="En attente d'echantillonage")).filter(
                entrepot__affectationentrepot__username_id=id).count()

            d = Cargaison.objects.filter(
                Q(etat='En attente de dechargement') | Q(Q(etat='Conforme aux exigences'))).filter(
                entrepot__affectationentrepot__username_id=id).count()
            # d = Cargaison.objects.filter(Q(etat='En attente de dechargement')|Q(Q(etat='Conforme aux exigences'))).filter(entrepot__affectationentrepot__username_id=id,  dateheurecargaison__lte=today, dateheurecargaison__gt=today-datetime.timedelta(days=90)).count()

            r = Cargaison.objects.filter(Q(etat='En attente requisition') | Q(tampon='0')).filter(
                entrepot__affectationentrepot__username_id=id).count()

            o = Cargaison.objects.filter(Q(etat='En attente de dechargement') | Q(etat='Conforme aux exigences'),
                                         entrepot__affectationentrepot__username_id=id).count()

            x = Entrepot_echantillon.objects.filter(
                Q(nonConformiteProduit=True) | Q(idcargaison__controlOrganoleptique=True),
                idcargaison__entrepot__affectationentrepot__username_id=id).count()

            return render(request, 'entrepot.html', {
                'cargaison': table,
                'n': n,
                'd': d,
                'r': r,
                'o': o,
                'x': x,
                'form':form,
            })
        else:
            return redirect('logout')

    #Methodes permettant d'effectuer l'echantillonage
    @login_required(login_url='login')
    def echantilloner(request):
        #Getting Logged in user detail for filtering
        user = request.user
        id = user.id
        role = user.role_id
        form = Echantilloner(request.POST or None)

        # Getting current Year & Month
        today = date.today()
        month = today.month
        year = today.year

        # Saving current URL Path in session Variable
        url = request.session['url']
        if role == 3 or role == 1 or role == 9:
            if request.is_ajax():
                pk = request.POST.get('pk', None)
                numrappech = request.POST.get('numrappech', None)
                numplombh = request.POST.get('numplombh', None)
                numplombb = request.POST.get('numplombb', None)
                numplombbr = request.POST.get('numplombbr', None)
                numplombaph = request.POST.get('numplombaph', None)
                etatphysique = request.POST.get('etatphysique', None)
                qte = request.POST.get('qte', None)
                conformite = request.POST.get('conformite', None)
                dateechantillonage = request.POST.get('dateechantillonage', None)
                numdossier = request.POST.get('numdossier', None)
                codecargaison = request.POST.get('codecargaison', None)
                c = Cargaison.objects.get(idcargaison=pk)

                if dateechantillonage == '' or numdossier == '' or numrappech == '' or numplombh == '' or qte == '' or conformite == '':
                    return JsonResponse({'error': form.errors}, status=400)

                # Test pour savoir si le laboratoire a deja pris en charge lechantillon
                if c.tampon == "1":
                    c.etat = "Echantillonner"
                    c.numdossier = numdossier
                    c.codecargaison = codecargaison
                    c.save(update_fields=['etat', 'numdossier', 'codecargaison'])
                    p = Entrepot_echantillon(idcargaison=c, numrappech=numrappech, numplombh=numplombh,
                                             numplombb=numplombb, numplombbr=numplombbr, numplombaph=numplombaph,
                                             etatphysique=etatphysique, qte=qte, conformite=conformite,
                                             dateechantillonage=dateechantillonage)
                    p.save()
                    response = {'valid': True}
                    return JsonResponse(response, status=200)
                else:
                   c.tampon = "1"
                   c.numdossier = numdossier
                   c.codecargaison = codecargaison
                   c.save(update_fields=['tampon','numdossier','codecargaison'])
                   p = Entrepot_echantillon.objects.get(idcargaison=pk)
                   p.numrappech=numrappech
                   p.numplombh=numplombh
                   p.numplombb=numplombb
                   p.numplombbr=numplombbr
                   p.numplombaph=numplombaph
                   p.etatphysique=etatphysique
                   p.qte=qte
                   p.conformite=conformite
                   p.save(update_fields=['numplombh','numrappech','numplombb','numplombbr','numplombaph','etatphysique','qte','conformite'])
                   response = {'valid':True}
                   return JsonResponse(response, status=200)

        else:
            return redirect('logout')

    # Recherche par qrcode En attente d'echantillonnage
    @login_required(login_url='login')
    def rechercheqrcode(request):
        # Getting Logged in user detail for filtering
        user = request.user
        id = user.id
        role = user.role_id

        # Getting current Year & Month
        today = date.today()
        month = today.month
        year = today.year

        form = Echantilloner(request.POST or None)

        if role == 3 or role == 1 or role == 9:
            q = request.GET.get('q')
            if q:
                qs = Cargaison.objects.filter(etat="En attente requisition").filter(
                    entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
                qs1 = Cargaison.objects.filter(etat="En attente d'echantillonage", qrcode=q).filter(
                    entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
                qs2 = Cargaison.objects.filter(entrepot__affectationentrepot__username_id=id).filter(
                    Q(rapechctrl=1) | Q(etat="Echantillonner")).order_by('-dateheurecargaison')
                table = EchantillonTable(qs1, prefix="1_")
                table1 = CargaisonEnAttenteRequisition(qs, prefix="2_")
                table2 = RapportEchantillonage(qs2, prefix='3_')
                RequestConfig(request, paginate={"per_page": 7}).configure(table)
                RequestConfig(request, paginate={"per_page": 10}).configure(table1)
                RequestConfig(request, paginate={"per_page": 5}).configure(table2)

                # #Compteur de la page principale de l'entrepot
                n = Cargaison.objects.filter(
                    Q(etat='En attente requisition') | Q(tampon='0') | Q(etat="En attente d'echantillonage")).filter(
                    entrepot__affectationentrepot__username_id=id, dateheurecargaison__date=today).count()
                d = Cargaison.objects.filter(
                    Q(etat='En attente de dechargement') | Q(Q(etat='Conforme aux exigences'))).filter(
                    entrepot__affectationentrepot__username_id=id).count()
                r = Cargaison.objects.filter(Q(etat='En attente requisition') | Q(tampon='0')).filter(
                    entrepot__affectationentrepot__username_id=id).count()
                o = Cargaison.objects.filter(Q(etat='En attente de dechargement') | Q(etat='Conforme aux exigences'),
                                             entrepot__affectationentrepot__username_id=id).count()
                x = Cargaison.objects.filter(etat='Cargaison dechargee',
                                             entrepot__affectationentrepot__username_id=id).count()

                return render(request, 'entrepot.html', {
                    'cargaison': table,
                    'cargaison1': table1,
                    'cargaison2': table2,
                    'form': form,
                    'n': n,
                    'd': d,
                    'r': r,
                    'o': o,
                    'x': x,
                })
        else:
            return redirect('logout')

    # Rechercher RE
    # Recherche par qrcode En attente d'echantillonnage
    @login_required(login_url='login')
    def rechercherre(request):
        # Getting Logged in user detail for filtering
        user = request.user
        id = user.id
        role = user.role_id

        # Getting current Year & Month
        today = date.today()
        month = today.month
        year = today.year

        form = Echantilloner(request.POST or None)

        if role == 3 or role == 1 or role == 9:
            q = request.GET.get('q')
            if q:
                qs = Cargaison.objects.filter(etat="En attente requisition").filter(
                    entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
                qs1 = Cargaison.objects.filter(etat="En attente d'echantillonage").filter(
                    entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
                qs2 = Cargaison.objects.filter(entrepot__affectationentrepot__username_id=id).filter(
                    Q(rapechctrl=1) | Q(etat="Echantillonner"), qrcode=q).order_by('-dateheurecargaison')
                table = EchantillonTable(qs1, prefix="1_")
                table1 = CargaisonEnAttenteRequisition(qs, prefix="2_")
                table2 = RapportEchantillonage(qs2, prefix='3_')
                RequestConfig(request, paginate={"per_page": 7}).configure(table)
                RequestConfig(request, paginate={"per_page": 10}).configure(table1)
                RequestConfig(request, paginate={"per_page": 5}).configure(table2)

                # #Compteur de la page principale de l'entrepot
                n = Cargaison.objects.filter(
                    Q(etat='En attente requisition') | Q(tampon='0') | Q(etat="En attente d'echantillonage")).filter(
                    entrepot__affectationentrepot__username_id=id, dateheurecargaison__date=today).count()
                d = Cargaison.objects.filter(
                    Q(etat='En attente de dechargement') | Q(Q(etat='Conforme aux exigences'))).filter(
                    entrepot__affectationentrepot__username_id=id).count()
                r = Cargaison.objects.filter(Q(etat='En attente requisition') | Q(tampon='0')).filter(
                    entrepot__affectationentrepot__username_id=id).count()
                o = Cargaison.objects.filter(Q(etat='En attente de dechargement') | Q(etat='Conforme aux exigences'),
                                             entrepot__affectationentrepot__username_id=id).count()
                x = Cargaison.objects.filter(etat='Cargaison dechargee',
                                             entrepot__affectationentrepot__username_id=id).count()

                return render(request, 'entrepot.html', {
                    'cargaison': table,
                    'cargaison1': table1,
                    'cargaison2': table2,
                    'form': form,
                    'n': n,
                    'd': d,
                    'r': r,
                    'o': o,
                    'x': x,
                })
        else:
            return redirect('logout')


#Class de gestion de dechargement
class GestionDechargement():
#Methode d'affichage du tableau de dechargement
    @login_required(login_url='login')
    def tableaudechargement(request):
        # Getting Logged in user detail for filtering
        user = request.user
        id = user.id
        role = user.role_id
        request.session['url'] = request.get_full_path()
        # today = date.today()
        form = MeterAfter()

        if role == 3 or role == 1:
            qs = ImpressionResultat.objects.raw('SELECT ei.idImpression, ei.isConforme, ei.idcargaison_id, ec.numdos, i.nomimportateur, ee.nomentrepot, ec.immatriculation,ep.nomproduit, ec.requisitiondackdate, eee.dateechantillonage, el.datereceptionlabo, ei.printDate \
                    FROM enreg_impressionresultat ei, enreg_cargaison ec, enreg_importateur i, enreg_entrepot ee, enreg_produit ep, enreg_entrepot_echantillon eee, enreg_laboreception el, accounts_affectationville aa \
                    WHERE ei.idcargaison_id = ec.idcargaison \
                    AND ec.importateur_id = i.idimportateur \
                    AND ec.entrepot_id = ee.identrepot \
                    AND ec.produit_id = ep.idproduit \
                    AND ec.idcargaison = eee.idcargaison_id \
                    AND eee.idcargaison_id = el.idcargaison_id \
                    AND ei.isConforme = 1 \
                    AND aa.username_id = %s',[id,])
            table = CargaisonDechargement(qs)
            RequestConfig(request, paginate={"per_page": 10}).configure(table)
            return render(request, 'entrepot_dechargement.html', {
                'cargaison': table,
                'form':form,
                                                                  })
        else:
            return redirect('logout')


@login_required(login_url='login')
def impressionRe(request,pk):
    # Generer le rapport d'echantillonage
    c = Cargaison.objects.get(idcargaison=pk)
    template = 'rapportechantillonage.html'
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


@login_required(login_url='login')
def impressionRapport(request, pk):
    template = 'rapport.html'

    # Request to fecth data into database
    cargaison = Cargaison.objects.get(idcargaison=pk)
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
    govTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('gov', flat=True)),3))  # gov Total Tanker
    gsvTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('gsv', flat=True)),3))  # gsv Total Tanker
    mtaTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('mta', flat=True)),3))  # mta Total Tanker
    mtvTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('mtv', flat=True)),3))  # mtv Total Tanker

    densite = densite15(inspection.temp, inspection.dens)  # densite 15c
    govMeter = round((inspection.meterafter - inspection.meterbefore)/1000,3)  # govmeter
    vcfMeter = vcf(densite, inspection.temp)  # vcfMeter
    gsvMeter = gsv(vcfMeter, govMeter)  # gsvMeter
    mtaMeter = mta(gsvMeter, densite)  # mta Meter

    govLt = float(cargaison.volume)  # gov LT
    vcfLt = vcf(densite, inspection.temp)  # VCF LT
    gsvLt = (cargaison.volume15)# GSV LT
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

    govLtTanker = round((govLt - float(govTotal)),3)  # Difference LT/Tanker
    gsvLtTanker = round((float(gsvLt) - float(gsvTotal)),3)  # Difference GSV LT/Tanker
    mtvLtTanker = round((float(mtvLt) - float(mtvTotal)),3)  # Difference mtv LT/Tanker
    mtaLtTanker = round((float(mtaLt) - float(mtaTotal)),3)  # Difference mtv LT/Tanker
    prLtTanker = round((govLtTanker * 100) / govLt,3)
    if gsvLt==0:
        gsvLt=1
    prGsvLtTanker = round((gsvLtTanker * 100)/ float(gsvLt),3)
    if mtaLt==0:
        mtaLt=1
    prMtaLtTanker = round((mtaLtTanker / (float(mtaLt)) * 100),3)
    if mtvLt==0:
        mtvLt=1
    prMtvLtTanker = round((mtvLtTanker / (float(mtvLt)) * 100),3)

    govTankerMeter = float(govTotal) - float(govMeter)  # Difference Tanker/Meter
    gsvTankerMeter = float(gsvTotal) - float(gsvMeter)  # Difference GSV Tanker/Meter
    mtaTankerMeter = round((float(mtaTotal) - mtaMeter),3)  # Difference MTA Tanker/Meter
    prTankerMeter = round((govTankerMeter * 100) / float(govTotal),3)

    govLtMeter = govLt - govMeter  # Diff LT/Meter
    gsvLtMeter = round((float(gsvLt) - gsvMeter),3)  # Diff GSV LT/Meter
    mtaLtMeter = float(mtaLt) - mtaMeter  # Diff mta LT/Meter
    if govLt==0:
        govLt=1
    prLtMeter = round((govLtMeter * 100) / govLt,3)
    if gsvLt==0:
        gsvLt=1
    prGsvLtMeter = round((gsvLtMeter * 100) / float(gsvLt),3)
    if mtaLt==0:
        mtaLt=1
    prMtaLtMeter = round((mtaLtMeter * 100) / float(mtaLt),3)

    #Certified Quantity
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

    fraisOcc = round((11 * float(gsvMax)),3)  # Frais occ a Payer

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
        'inspection': inspection,
        'densite': densite,
        'prGsvLtTanker':prGsvLtTanker,
        'prMtaLtTanker':prMtaLtTanker,
        'prMtvLtTanker':prMtvLtTanker,
        'prGsvLtMeter':prGsvLtMeter,
        'prMtaLtMeter':prMtaLtMeter,
        'prLtTanker':prLtTanker,
        'prTankerMeter':prTankerMeter,
        'prLtMeter':prLtMeter,
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
    return HttpResponse(pdf, content_type='application/pdf')


@login_required(login_url='login')
def echantillonage(request):
    # Getting Logged in user detail for filtering
    user = request.user
    id = user.id
    role = user.role_id

    # Getting current Year & Month
    today = datetime.datetime.now()
    # template = 'form.html'
    # # form = Echantilloner()

    if request.method == 'POST':
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            pk = request.POST.get('pk', None)
            matricule = request.POST.get('matricule', None)
            methodeutilisee = request.POST.get('methodeutilisee', None)
            qte = request.POST.get('qte', None)

            c = Cargaison.objects.get(idcargaison=pk)
            ville = c.entrepot.ville
            print(ville)
            numrappech = numRappEch(pk,ville)  # Generation automatique du numero de rapport d'achentillonnage / ville et annuel
            numrappechauto = numrappech
            c.rapechctrl = 1
            c.etatInspection = True
            c.etat = "Echantillonner"
            c.save(update_fields=['etat', 'rapechctrl','etatInspection'])

            e = Entrepot_echantillon(idcargaison=c, numrappechauto=numrappechauto, matricule=matricule,methodeutilisee=methodeutilisee, qte=qte, dateechantillonage=today)
            e.save()

            # Generer le rapport d'echantillonage
            template = 'rapportechantillonage.html'
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
                'matricule':matricule,
                'qtelabo': qtelabo,
                'numrappechauto': numrappechauto,
            }

            # Render PDF Files
            pdf = render_to_pdf(template, data)

            # # Create an email message
            # subject = 'OCC Sampling Report ' + str(numrappech) + str(today.year)
            # message = 'Please find attached the Sampling Report'
            # email_from = 'otace1@gmail.com'  # Replace with your email address
            # recipient_list = ['cedric@malabar-group.com']  # Replace with recipient email address(es)
            # email = EmailMessage(subject, message, email_from, recipient_list)
            #
            # # Add the PDF report as an attachment
            # filename = 'SamplingReport.pdf'
            # email.attach(filename, pdf.getvalue(), 'application/pdf')
            #
            # # Send the email
            # email.send()
            # Convert PDF content to Base64-encoded string
            pdf_base64 = base64.b64encode(pdf.getvalue()).decode('utf-8')
            return JsonResponse({'status': 'success', 'pdf_base64': pdf_base64})
        else:
            return redirect('entrepot')
    else:
        return redirect('entrepot')


@login_required(login_url='login')
def view_pdf(request):
    # Get PDF data from cache
    pdf_data = cache.get('pdf_data')

    # Return PDF as response
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    return response



@login_required(login_url='login')
def rapportechantillonage(request, pk):
    template = 'rapportechantillonage.html'
    c = Cargaison.objects.get(idcargaison=pk)
    e = Entrepot_echantillon.objects.get(idcargaison=pk)

    entrepot = c.entrepot
    dateechantillonage = e.dateechantillonage
    dateech = dateechantillonage
    numdos = c.numdos
    importateur = c.importateur
    adresseimportateur = c.importateur_id
    adresseimportateur = Importateur.objects.get(idimportateur=adresseimportateur).adresseimportateur
    declarant = c.declarant
    produit = c.produit
    volume = c.volume
    provenance = c.provenance.name
    voie = c.voie.nomvoie
    immatriculation = c.immatriculation
    qtelabo = e.qte
    numplombh = e.numplombh
    numrappechauto = e.numrappechauto

    data = {
        'dateechantillonage': dateechantillonage,
        'dateech': dateech,
        'entrepot': entrepot,
        'numdos': numdos,
        'importateur': importateur,
        'adresseimportateur': adresseimportateur,
        'declarant': declarant,
        'produit': produit,
        'volume': volume,
        'provenance': provenance,
        'voie': voie,
        'immatriculation': immatriculation,
        'qtelabo': qtelabo,
        'numplombh': numplombh,
        'numrappechauto': numrappechauto,
    }

    # Render PDF Files
    pdf = render_to_pdf(template, data)
    return HttpResponse(pdf, content_type='application/pdf')

@login_required(login_url='login')
def impressionCert(request, pk):
    user = request.user
    id = user.id
    ville = AffectationVille.objects.get(username_id=id)
    ville = ville.ville_id
    province = Ville.objects.get(idville=ville)
    province = province.province
    province = province.upper()
    role = user.role_id
    url = request.session['url']
    if role == 3 or role == 9 or role == 1:

        # td = datetime.today()
        # today = td.date()

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
        numdossier = a.numdos
        immatriculation = a.immatriculation
        numrappech = b.numrappech

        # Putting printing counter to 1
        # a.impression = "1"
        # a.save(update_fields=['impression'])

        # Saving print date into DBS  a ameliorer
        # d.dateimpression = today
        # d.save(update_fields=['dateimpression'])
        # dateimpression = d.dateimpression

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
                # 'dateimpression': dateimpression,
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
                'annee': annee,
                'province': province,
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
                    # 'dateimpression': dateimpression,
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
                    'annee': annee,
                    'province': province,
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
                        # 'dateimpression': dateimpression,
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
                        'annee': annee,
                        'province': province,
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
                            # 'dateimpression': dateimpression,
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
                            'annee': annee,
                            'province': province,
                        }

                        # Rendered PDF report
                        pdf = render_to_pdf(template, data)
                        return HttpResponse(pdf, content_type='application/pdf')
                    else:
                        return redirect('logout')
    else:
        return redirect('logout')


# Seals Inspections
@login_required(login_url='login')
def choiceoftype(request, pk):
    template = 'choicetype.html'
    form = PreInspectionForm1(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            meter = form.cleaned_data['meter']
            tanker = form.cleaned_data['tanker']
            shore = form.cleaned_data['shore']

            # Test pour affichage des formulaires correspondant
            if meter is False:
                if tanker is False:
                    if shore is False:
                        template = 'error.html'
                        context={}
                        return render(request,template,context) #Meter=0,Tanker=0,Shore=0
                    else:
                        return redirect('shore', pk=pk) #Meter=0,Tanker=0,Shore=1
                else:
                    if shore is False:
                        return redirect('seals', pk=pk) #Meter=0,Tanker=1,Shore=0
                    else:
                        return HttpResponseBadRequest #Meter=0,Tanker=1,Shore=1
            else:
                if tanker is False:
                    if shore is False:
                        return redirect('seals', pk=pk) #Meter=1,Tanker=0,Shore=0
                    else:
                        return redirect('shore', pk=pk) #Meter=1,Tanker=0,Shore=1
                else:
                    if shore is False:
                        return redirect('seals', pk=pk) #Meter=1,Tanker=1,Shore=0
                    else:
                        return HttpResponseBadRequest #Meter=1,Tanker=1,Shore=1
    else:
        context = {'form': form}
        return render(request, template, context)


@login_required(login_url='login')
def seals(request, pk):
    template = 'formPreInspection1.html'
    cargaison = Cargaison.objects.get(idcargaison=pk)
    form = SealInspection(request.POST or None)
    request.session['id'] = pk

    if request.method == 'POST':
        if form.is_valid():
            form = form.save(commit=False)
            form.idcargaison = cargaison
            form.save()
            return redirect('seal-details', pk=form.id)
        else:
            template = "partials/sealinspection.html"
            return render(request, template, {'form': form})

    context = {
        "form": form,
        "cargaison": cargaison,
        # "seals":seals,
    }
    return render(request, template, context)


@login_required(login_url='login')
def sealinspection(request):
    template = 'partials/sealinspection.html'
    form = SealInspection()
    context = {
        "form": form
    }
    return render(request, template, context)


@login_required(login_url='login')
def detailseals(request, pk):
    template = 'partials/sealdetails.html'
    seals = InspectionSeal.objects.get(id=pk)
    context = {"seals": seals}
    return render(request, template, context)


@login_required(login_url='login')
def sealsdelete(request, pk):
    seal = InspectionSeal.objects.get(pk=pk)
    seal.delete()
    return HttpResponse()


@login_required(login_url='login')
def updateseals(request, pk):
    template = 'partials/sealinspection.html'
    seal = InspectionSeal.objects.get(pk=pk)
    form = SealInspection(request.POST or None, instance=seal)

    if request.method == "POST":
        if request.method == 'POST':
            if form.is_valid():
                form = form.save()
                return redirect('seal-details', pk=form.id)

    context = {
        "form": form,
        "seal": seal,
    }
    return render(request, template, context)


@login_required(login_url='login')
def tankerinspection(request):
    pk = request.session['id']
    template = 'tankerInspection.html'
    cargaison = Cargaison.objects.get(idcargaison=pk)
    form = TankerInspection(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            # produit = request.POST['produit']
            # produit = Produit.objects.get(idproduit=produit)
            dens = request.POST['dens']
            temp = request.POST['temp']
            innagein = request.POST['innagein']
            if innagein == '':
                innagein == 'N/A'
            volumein = request.POST['volumein']
            tempin = request.POST['tempin']
            weightin = request.POST['weightin']
            # # meterbefore = request.POST['meterbefore']
            # if meterbefore == '':
            #     meterbefore = 0
            data = Inspection(idcargaison=cargaison, dens=dens, temp=temp, innagein=innagein,
                              volumein=volumein, tempin=tempin, weightin=weightin)
            data.save()
            return redirect('compartiment', pk=pk)
    else:
        context = {'form': form}
        return render(request, template, context)


@login_required(login_url='login')
def compartiment(request, pk):
    template = 'formCompartiment1.html'
    inspection = Inspection.objects.get(idcargaison=pk)
    form = CompartimentInspection(request.POST or None)
    request.session['id'] = pk

    if request.method == 'POST':
        if form.is_valid():
            form = form.save(commit=False)

            t = request.POST['tempcomp']  # Temperature du compartiment
            govCompart = request.POST['gov']  # Gov du compartiment

            # calcul des valeurs d'inspection
            # Recuperation des valeurs pour calcul de la densite a 15
            densite = inspection.dens
            temperature = inspection.temp
            d = densite15(temperature, densite)  # Calcul Dens a 15

            v = vcf(d, t)  # VCF
            g = gsv(v, govCompart)  # GSV
            m = mtv(g, d)  # MTV
            a = mta(g, d)  # MTA

            # Recuperation des donnees des calculs
            form.gsv = g
            form.mtv = m
            form.mta = a
            form.vcf = v
            form.idinspection = inspection

            form.save()
            return redirect('compartiment-details', pk=form.id)
        else:
            template = "partials/compartimentinspection.html"
            return render(request, template, {'form': form})

    context = {
        "form": form,
        "cargaison": inspection,
        # "seals":seals,
    }
    return render(request, template, context)


@login_required(login_url='login')
def compartimentinspection(request):
    template = 'partials/compartimentinspection.html'
    form = CompartimentInspection()
    context = {
        "form": form
    }
    return render(request, template, context)


@login_required(login_url='login')
def detailscompartiment(request, pk):
    template = 'partials/compartimentdetails.html'
    compartiment = Compartiment.objects.get(id=pk)
    context = {"compartiment": compartiment}
    return render(request, template, context)


@login_required(login_url='login')
def compartimentdelete(request, pk):
    compartement = Compartiment.objects.get(pk=pk)
    compartement.delete()
    return HttpResponse()


@login_required(login_url='login')
def updatecompartiment(request, pk):
    template = 'partials/compartimentinspection.html'
    compartiment = Compartiment.objects.get(pk=pk)
    form = CompartimentInspection(request.POST or None, instance=compartiment)

    if request.method == "POST":
        if request.method == 'POST':
            if form.is_valid():
                form = form.save()
                return redirect('compartiment-details', pk=form.id)

    context = {
        "form": form,
        "compartiment": compartiment,
    }
    return render(request, template, context)


@login_required(login_url='login')
def meterafter(request):
    if request.method == 'POST':
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            pk = request.POST.get('pk', None)
            meterafter = request.POST.get('meterafter', None)
            meterbefore = request.POST.get('meterbefore', None)
            impression = ImpressionResultat.objects.get(idImpression=pk)
            cargaison = Cargaison.objects.get(idcargaison=impression.idcargaison_id)
            try:
                if meterbefore == '':
                    meterbefore = 0
                if meterafter == '':
                    meterafter = 0
                inspection = Inspection.objects.get(idcargaison=cargaison)
                inspection.meterafter = meterafter
                inspection.save(update_fields=['meterafter', 'meterbefore'])
                cargaison.etat = 'Cargaison dechargee'
                cargaison.dateDechargement = datetime.datetime.today()
                cargaison.save(update_fields=['etat', 'dateDechargement'])
                return JsonResponse({'status': 'success'})
            except (Inspection.DoesNotExist):
                return JsonResponse({'status': 'error', 'message': 'ImpressionResultat or Cargaison object does not exist.'})
        return redirect('dechargement')
    return redirect('dechargement')


@login_required(login_url='login')
def shoreinspection(request, pk):
    # pk = request.session['id']
    template = 'shoreInspectionForm.html'
    cargaison = Cargaison.objects.get(idcargaison=pk)
    try:
        Inspection.objects.get(idcargaison_id=cargaison)
        print("OK")
        return redirect('shore-inspection-after', pk=pk)
    except:
        form = ShoreInspection(request.POST or None)
        if request.method == 'POST':
            if form.is_valid():
                produit = request.POST['produit']
                produit = Produit.objects.get(idproduit=produit)
                innagein = request.POST['innagein']
                volumein = request.POST['volumein']
                tempin = request.POST['tempin']
                weightin = request.POST['weightin']
                data = Inspection(idcargaison=cargaison, produit=produit, innagein=innagein,
                                  volumein=volumein, tempin=tempin, weightin=weightin)
                data.save()
                return redirect('shore-inspection', pk=pk)
        else:
            context = {'form': form}
            return render(request, template, context)


@login_required(login_url='login')
def shoretankbefore(request, pk):
    template = 'ShoreInspection.html'
    inspection = Inspection.objects.get(idcargaison=pk)
    cargaison = Cargaison.objects.get(idcargaison=pk)
    form = ShoreInspectionBefore(request.POST or None)
    request.session['id'] = pk

    if request.method == 'POST':
        if form.is_valid():
            form = form.save(commit=False)
            form.idinspection = inspection
            form.save()
            # Update fields to show that this shore has passed the before inspection
            cargaison.before = 1
            cargaison.save(update_fields=['before'])

            return redirect('shore-details', pk=form.id)
        else:
            template = "partials/shoreinspection.html"
            return render(request, template, {'form': form})

    context = {
        "form": form,
        "cargaison": cargaison,
    }
    return render(request, template, context)


@login_required(login_url='login')
def shoretankafter(request, pk):
    template = 'ShoreInspectionAfter.html'
    cargaison = Cargaison.objects.get(idcargaison=pk)
    inspection = Inspection.objects.get(idcargaison=cargaison)
    form = ShoreInspectionAfter(request.POST or None)
    request.session['id'] = pk

    if request.method == 'POST':
        if form.is_valid():
            tankdenomafter = request.POST['tankdenomafter']
            prodinnageafter = request.POST['prodinnageafter']
            fwdeepafter = request.POST['fwdeepafter']
            govafter = request.POST['govafter']
            tempafter = request.POST['tempafter']
            densityafter = request.POST['densityafter']

            a = ShoreTank.objects.get(idinspection=inspection)
            a.tankdenomafter = tankdenomafter
            a.prodinnageafter = prodinnageafter
            a.fwdeepafter = fwdeepafter
            a.govafter = govafter
            a.tempafter = tempafter
            a.densityafter = densityafter

            a.save(update_fields=['tankdenomafter', 'prodinnageafter', 'prodinnageafter', 'fwdeepafter', 'govafter',
                                  'tempafter', 'densityafter'])
            # Update fields to show that this shore has passed the before inspection
            cargaison.after = 1
            cargaison.save(update_fields=['after'])

            return redirect('shore-details-after', pk=form.id)
        else:
            template = "partials/shoreinspection.html"
            return render(request, template, {'form': form})

    context = {
        "form": form,
        "cargaison": cargaison,
    }
    return render(request, template, context)


@login_required(login_url='login')
def shore(request):
    template = 'partials/shoreinspection.html'
    form = ShoreInspectionBefore()
    context = {
        "form": form
    }
    return render(request, template, context)


@login_required(login_url='login')
def shoreafter(request):
    template = 'partials/shoreinspectionafter.html'
    form = ShoreInspectionAfter()
    context = {
        "form": form
    }
    return render(request, template, context)


@login_required(login_url='login')
def shoredetails(request, pk):
    # print(pk)
    template = 'partials/shoredetails.html'
    shore = ShoreTank.objects.get(id=pk)
    context = {"shore": shore}
    return render(request, template, context)


@login_required(login_url='login')
def shoredetailsafter(request, pk):
    # print(pk)
    template = 'partials/shoredetailsafter.html'
    shore = ShoreTank.objects.get(id=pk)
    context = {"shore": shore}
    return render(request, template, context)


@login_required(login_url='login')
def shoredelete(request, pk):
    shore = Shore.objects.get(pk=pk)
    shore.delete()
    return HttpResponse()


@login_required(login_url='login')
def shoredeleteafter(request, pk):
    shore = Shore.objects.get(pk=pk)
    shore.delete()
    return HttpResponse()


@login_required(login_url='login')
def shoreupdate(request, pk):
    template = 'partials/shoreinspection.html'
    shore = Shore.objects.get(pk=pk)
    form = ShoreInspectionBefore(request.POST or None, instance=shore)

    if request.method == "POST":
        if request.method == 'POST':
            if form.is_valid():
                form = form.save()
                return redirect('shore-details', pk=form.id)

    context = {
        "form": form,
        "shore": shore,
    }
    return render(request, template, context)


@login_required(login_url='login')
def shoreupdateafter(request, pk):
    template = 'partials/shoreinspectionafter.html'
    shore = Shore.objects.get(pk=pk)
    form = ShoreInspectionAfter(request.POST or None, instance=shore)

    if request.method == "POST":
        if request.method == 'POST':
            if form.is_valid():
                tankdenomafter = request.POST['tankdenomafter']
                prodinnageafter = request.POST['prodinnageafter']
                fwdeepafter = request.POST['fwdeepafter']
                govafter = request.POST['govafter']
                tempafter = request.POST['tempafter']
                densityafter = request.POST['densityafter']

                shore.tankdenomafter = tankdenomafter
                shore.prodinnageafter = prodinnageafter
                shore.fwdeepafter = fwdeepafter
                shore.govafter = govafter
                shore.tempafter = tempafter
                shore.densityafter = densityafter

                shore.save(
                    update_fields=['tankdenomafter', 'prodinnageafter', 'prodinnageafter', 'fwdeepafter', 'govafter',
                                   'tempafter', 'densityafter'])

                return redirect('shore-details-after', pk=form.id)

    context = {
        "form": form,
        "shore": shore,
    }
    return render(request, template, context)


@login_required(login_url='login')
def tableaurapports(request):
    user = request.user.id
    template = 'tableauRapport.html'
    qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, c.dateDechargement ,e.dateechantillonage, l.datereceptionlabo , ei.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                FROM enreg_cargaison c \
                                    LEFT JOIN enreg_entrepot_echantillon e \
                                    ON c.idcargaison = e.idcargaison_id \
                                    LEFT JOIN enreg_laboreception l \
                                    ON e.idcargaison_id = l.idcargaison_id \
                                    LEFT JOIN enreg_impressionresultat ei \
                                    ON l.idcargaison_id = ei.idcargaison_id \
                                    LEFT JOIN enreg_inspection i \
                                    ON i.idcargaison_id = c.idcargaison \
                                    LEFT JOIN enreg_compartiment co \
                                    ON co.idinspection_id = i.idinspection \
                                    LEFT JOIN enreg_produit p \
                                    ON p.idproduit = c.produit_id \
                                    LEFT JOIN enreg_importateur a \
                                    ON a.idimportateur = c.importateur_id \
                                    LEFT JOIN enreg_entrepot ee \
                                    ON ee.identrepot = c.entrepot_id \
                                    LEFT JOIN enreg_ville ev \
                                    ON ev.idville = ee.ville_id \
                                    LEFT JOIN accounts_affectationville v \
                                    ON v.ville_id = ev.idville \
                                WHERE v.username_id= %s \
                                GROUP BY c.idcargaison \
                                ORDER BY i.dateinspection DESC',[user,])
    # qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.dateanalyse, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
    qs1 = Cargaison.objects.filter(voie__idvoie=3)
    table = RapportInspectionCamion(qs, prefix='1_')
    table1 = RapportInspectionTanker(qs1, prefix='2_')
    # RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page":5}).configure(table)
    # RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page":5}).configure(table1)

    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    context = {
        'table': table,
        'table1': table1
    }
    return render(request, template, context)


# def reportCheck(request,data):
#     template


@login_required(login_url='login')
def natureProduit(request, pk):
    user = request.user.id
    template = 'natureProduit.html'
    cargaison = Cargaison.objects.get(idcargaison=pk)
    form = NatureProduit(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            produit = request.POST['produit']
            if int(produit) == int(cargaison.produit.idproduit):
                c = ControlNatureProduit(idcargaison=cargaison,natureProduitEntrepot=produit.nomproduit,userEntrepot=user, conformiteProduit=True)
                return redirect('echantillonage', pk=pk)
            else:
                produit = Produit.objects.get(idproduit=produit)
                c = ControlNatureProduit(idcargaison=cargaison,natureProduitEntrepot=produit.nomproduit,userEntrepot=user, conformiteProduit=False)
                c.save()
                return redirect('entrepot')
    else:
        context = {'form': form}
        return render(request, template, context)


@login_required(login_url='login')
def affichageProduitNonConforme(request):
    user = request.user
    role = user.role_id
    id = user.id
    template = 'affichageProduitNonConforme.html'

    # qs = ControlNatureProduit.objects.filter(idcargaison__entrepot__affectationentrepot__username_id=id,conformiteProduit=False)
    qs = Entrepot_echantillon.objects.filter(idcargaison__toBeRefouler=1, idcargaison__isRefouler=0,
                                              idcargaison__entrepot__affectationentrepot__username_id=id)
    qs1 = Entrepot_echantillon.objects.filter(idcargaison__toBeConsignated=1, idcargaison__isConsignated=0,
                                              idcargaison__entrepot__affectationentrepot__username_id=id)

    table = NonConformeOrganoleptique(qs,prefix='1')
    table1 = NonConformeLaboratoire(qs1,prefix='2')
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page":5}).configure(table)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page":5}).configure(table1)
    context = {
        'table': table,
        'table1': table1,
    }
    return render(request,template,context)


@login_required(login_url='login')
def affichageEnAttenteRequisition(request):
    user = request.user
    role = user.role_id
    id = user.id
    template = 'enAttenteRequisition.html'
    qs = Cargaison.objects.filter(etat="En attente requisition").filter(entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
    table = CargaisonEnAttenteRequisition(qs)
    RequestConfig(request, paginate={"per_page": 5}).configure(table)
    context = {'table':table}
    return render(request,template,context)


@login_required(login_url='login')
def correctionNonConformite(request,pk):
    user = request.user.id
    # Update Product Name Correction
    x = ControlNatureProduit.objects.get(idcontrol=pk)
    x.correctionNature = x.natureProduitEntrepot
    x.userEntrepot = user
    x.conformiteProduit = True
    x.save(update_fields=['correctionNature', 'userEntrepot','conformiteProduit'])
    return redirect('entrepot')


@login_required(login_url='login')
def inspection(request,pk):
    user = request.user.id
    role = user.role_id

    if role == 3 or role == 1:
        qs = Cargaison.objects.filter(etatInspection=True, etat="Echantillonner",before=False,entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
        table = CargaisonDechargement(qs, prefix='1_')

        # affichage des tanker cabotteurs
        qs1 = Cargaison.objects.filter(before=True, entrepot__affectationentrepot__username_id=id).order_by(
            '-dateheurecargaison')
        table1 = TankerCabotteur(qs1, prefix='2_')
        RequestConfig(request, paginate={"per_page": 10}).configure(table)
        RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 10}).configure(table1)
        return render(request, 'entrepot_dechargement.html', {'cargaison': table,
                                                              'rapport': table1,
                                                              })
    else:
        return redirect('logout')

@login_required(login_url='login')
def affichageInspection(request):
    user = request.user.id
    template = 'enAttenteInspection.html'
    qs = Cargaison.objects.filter(etatInspection=True, entrepot__affectationentrepot__username_id=user).order_by('-dateheurecargaison')
    table = EnAttenteInspection(qs,prefix='1_')
    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    context = {'table':table}
    return render(request,template,context)


@login_required(login_url='login')
def marquageInspection(request):
    pk = request.session['id']
    c = Cargaison.objects.get(idcargaison=pk)
    c.etatInspection = 0
    c.save(update_fields=['etatInspection'])
    return redirect('entrepot')


@login_required(login_url='login')
def consignatedOk(request,pk):
    c = Cargaison.objects.get(idcargaison=pk)
    c.isConsignated = 1
    c.toBeConsignated = 0
    c.save(update_fields=['isConsignated','toBeConsignated'])
    return redirect('affichageProduitNonConforme')


@login_required(login_url='login')
def refouleOk(request,pk):
    c = Cargaison.objects.get(idcargaison=pk)
    c.isRefouler = 1
    c.toBeRefouler = 0
    c.save(update_fields=['isRefouler','toBeRefouler'])
    return redirect('affichageProduitNonConforme')



