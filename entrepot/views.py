from django.shortcuts import render, redirect
from .tables import EchantillonTable, CargaisonDechargement, EchantillonEnregistrer, CargaisonDechargee
from enreg.models import Cargaison, Entrepot_echantillon, Dechargement, Resultat, LaboReception
from accounts.models import *
from .forms import Echantilloner, Decharger
from django.contrib.auth.decorators import login_required
import math
from django.db.models import Q, Count
from django_tables2.paginators import LazyPaginator
from django_tables2 import RequestConfig
from datetime import date
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
import datetime



#Gestion des echantillonages
class GestionEchantillonage():

#Methode permettant l'affichage du tableau d'echantillonage
    @login_required(login_url='login')
    def tableauechantillonnage(request):
        user = request.user
        role = user.role_id
        id = user.id
        today = date.today()
        request.session['url'] = request.get_full_path()
        form = Echantilloner(request.POST or None)

        if role == 3 or role == 1 or role == 9:
           # table = EchantillonTable(Cargaison.objects.filter(Q(etat="En attente d'echantillonage")|Q(tampon='0')|Q(etat="En attente requisition")).filter(entrepot__affectationentrepot__username_id=id, dateheurecargaison__year=today.year).order_by('-dateheurecargaison'), prefix="1_")
           # RequestConfig(request, paginate={"per_page":15}).configure(table)
           #
           # table1 = EchantillonEnregistrer(Cargaison.objects.filter(Q(etat="En attente requisition")|Q(tampon='0')).filter(entrepot__affectationentrepot__username_id=id, dateheurecargaison__year=today.year).order_by('-dateheurecargaison'), prefix="2_")
           # RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page":15}).configure(table1)

           table = EchantillonTable(Cargaison.objects.filter(
               Q(etat="En attente d'echantillonage") | Q(tampon='0') | Q(etat="En attente requisition")).filter(
               entrepot__affectationentrepot__username_id=id).order_by(
               '-dateheurecargaison'), prefix="1_")
           RequestConfig(request, paginate={"per_page": 15}).configure(table)

           table1 = EchantillonEnregistrer(
               Cargaison.objects.filter(Q(etat="En attente requisition") | Q(tampon='0')).filter(
                   entrepot__affectationentrepot__username_id=id).order_by(
                   '-dateheurecargaison'), prefix="2_")
           RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table1)

                # #Compteur de la page principale de l'entrepot
           n = Cargaison.objects.filter(Q(etat='En attente requisition')|Q(tampon='0')).filter(entrepot__affectationentrepot__username_id=id ,dateheurecargaison__date=today).count()

           d = Cargaison.objects.filter(etat='En attente de dechargement', entrepot__affectationentrepot__username_id=id,  dateheurecargaison__lte=today, dateheurecargaison__gt=today-datetime.timedelta(days=90)).count()

           r = Cargaison.objects.filter(Q(etat='En attente requisition')|Q(tampon='0')).filter(entrepot__affectationentrepot__username_id=id, dateheurecargaison__lte=today, dateheurecargaison__gt=today-datetime.timedelta(days=90)).count()

           o = Cargaison.objects.filter(etat='En attente de dechargement', entrepot__affectationentrepot__username_id=id, dateheurecargaison__lte=today, dateheurecargaison__gt=today-datetime.timedelta(days=90)).count()

           x = Cargaison.objects.filter(etat='Cargaison dechargee', entrepot__affectationentrepot__username_id=id).count()

           return render(request, 'entrepot.html', {
                    'cargaison': table,
                    'cargaison1':table1,
                    'form':form,
                    'n':n,
                    'd':d,
                    'r':r,
                    'o':o,
                    'x':x,
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

            table = EchantillonTable(Cargaison.objects.filter(Q(etat='En attente requisition')|Q(tampon='0')).filter(entrepot__affectationentrepot__username_id=id,
                                         dateheurecargaison__lte=today,
                                         dateheurecargaison__gt=today - datetime.timedelta(days=90)).order_by('-dateheurecargaison'))
            RequestConfig(request, paginate={"per_page": 15}).configure(table)

            # #Compteur de la page principale de l'entrepot
            n = Cargaison.objects.filter(Q(etat='En attente requisition')|Q(tampon='0')).filter(entrepot__affectationentrepot__username_id=id,
                                         dateheurecargaison__date=today).count()

            d = Cargaison.objects.filter(etat='En attente de dechargement',
                                         entrepot__affectationentrepot__username_id=id).count()

            r = Cargaison.objects.filter(Q(etat='En attente requisition')|Q(tampon='0')).filter(entrepot__affectationentrepot__username_id=id,
                                         dateheurecargaison__lte=today,
                                         dateheurecargaison__gt=today - datetime.timedelta(days=90)).count()

            o = Cargaison.objects.filter(etat='En attente de dechargement',
                                         entrepot__affectationentrepot__username_id=id, dateheurecargaison__lte=today,
                                         dateheurecargaison__gt=today - datetime.timedelta(days=90)).count()

            x = Cargaison.objects.filter(etat='Cargaison dechargee',
                                         entrepot__affectationentrepot__username_id=id).count()

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

            table = EchantillonTable(Cargaison.objects.filter(Q(etat='En attente requisition')|Q(tampon='0')).filter(entrepot__affectationentrepot__username_id=id,
                                         dateheurecargaison__date=today).order_by('-dateheurecargaison'))

            RequestConfig(request, paginate={"per_page": 20}).configure(table)

            # #Compteur de la page principale de l'entrepot
            n = Cargaison.objects.filter(Q(etat='En attente requisition')|Q(tampon='0')).filter(entrepot__affectationentrepot__username_id=id,
                                         dateheurecargaison__date=today).count()

            d = Cargaison.objects.filter(etat='En attente de dechargement',
                                         entrepot__affectationentrepot__username_id=id).count()

            r = Cargaison.objects.filter(Q(etat='En attente requisition')|Q(tampon='0')).filter(entrepot__affectationentrepot__username_id=id,
                                         dateheurecargaison__lte=today,
                                         dateheurecargaison__gt=today - datetime.timedelta(days=90)).count()

            o = Cargaison.objects.filter(etat='En attente de dechargement',
                                         entrepot__affectationentrepot__username_id=id, dateheurecargaison__lte=today,
                                         dateheurecargaison__gt=today - datetime.timedelta(days=90)).count()

            x = Cargaison.objects.filter(etat='Cargaison dechargee',
                                         entrepot__affectationentrepot__username_id=id).count()

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

#Recherche par qrcode
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
                table1 = EchantillonEnregistrer(Cargaison.objects.filter(Q(etat="En attente requisition")|Q(etat="En attente d'echantillonage")|Q(tampon='0')).filter(entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison'), prefix="2_")
                RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 5}).configure(table1)

                table = EchantillonTable(Cargaison.objects.filter(qrcode=q).filter(Q(etat="En attente d'echantillonage")|Q(etat="En attente requisition")|Q(tampon='0')), prefix="1_")
                RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 5}).configure(table)

                # #Compteur de la page principale de l'entrepot
                n = Cargaison.objects.filter(Q(etat='En attente requisition')|Q(tampon='0')).filter(
                                             entrepot__affectationentrepot__username_id=id,
                                             dateheurecargaison__date=today).count()

                d = Cargaison.objects.filter(etat='En attente de dechargement',
                                             entrepot__affectationentrepot__username_id=id).count()

                r = Cargaison.objects.filter(Q(etat='En attente requisition')|Q(tampon='0')).filter(
                                             entrepot__affectationentrepot__username_id=id,
                                             dateheurecargaison__lte=today,
                                             dateheurecargaison__gt=today - datetime.timedelta(days=90)).count()

                o = Cargaison.objects.filter(etat='En attente de dechargement',
                                             entrepot__affectationentrepot__username_id=id,
                                             dateheurecargaison__lte=today,
                                             dateheurecargaison__gt=today - datetime.timedelta(days=90)).count()

                x = Cargaison.objects.filter(etat='Cargaison dechargee',
                                             entrepot__affectationentrepot__username_id=id).count()

                return render(request,'entrepot.html',{
                    'cargaison': table,
                    'cargaison1':table1,
                    'n': n,
                    'd': d,
                    'r': r,
                    'o': o,
                    'x': x,
                    'form':form,
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
        form = Decharger(request.POST or None)
        today = date.today()

        if role == 9 or role == 1:
            table = CargaisonDechargement(
                Cargaison.objects.filter(etat="Echantillonner").filter(entrepot__affectationentrepot__username_id=id,
                                                                       dateheurecargaison__lte=today,
                                                                       dateheurecargaison__gt=today - datetime.timedelta(
                                                                           days=120)).order_by('-dateheurecargaison'),
                prefix='2_')
            table1 = CargaisonDechargee(Dechargement.objects.raw('SELECT DISTINCT(d.idcargaison_id) , d.datedechargement, c.numdossier, c.codecargaison, c.immatriculation, d.gov, d.gsv, d.mta, d.mtv \
                                             FROM hydro_occ.enreg_dechargement d, hydro_occ.enreg_resultat r,hydro_occ.enreg_laboreception l, hydro_occ.enreg_entrepot_echantillon e, hydro_occ.enreg_cargaison c, hydro_occ.accounts_affectationentrepot a, hydro_occ.accounts_myuser u \
                                             WHERE d.idcargaison_id = r.idcargaison_id \
                                             AND r.idcargaison_id = l.idcargaison_id  \
                                             AND l.idcargaison_id = e.idcargaison_id \
                                             AND e.idcargaison_id = c.idcargaison \
                                             AND c.entrepot_id = a.entrepot_id \
                                             AND a.username_id = %s \
                                             GROUP BY d.idcargaison_id \
                                             ORDER BY d.datedechargement DESC', [id, ]), prefix="1_")

            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            RequestConfig(request, paginate={"per_page": 15}).configure(table1)
            return render(request, 'entrepot_dechargement.html', {'cargaison': table,
                                                                  'rapport':table1,
                                                                  'form':form,
                                                                 })
        else:
            if role == 3 or role == 1:
                table = CargaisonDechargement(Cargaison.objects.filter(etat="En attente de dechargement").filter(entrepot__affectationentrepot__username_id=id, dateheurecargaison__lte=today, dateheurecargaison__gt=today-datetime.timedelta(days=120)).order_by('-dateheurecargaison'), prefix='2_')

                table1 = CargaisonDechargee(Dechargement.objects.raw('SELECT DISTINCT(d.idcargaison_id) , d.datedechargement, c.numdossier, c.codecargaison, c.immatriculation, d.gov, d.gsv, d.mta, d.mtv \
                                                 FROM hydro_occ.enreg_dechargement d, hydro_occ.enreg_resultat r,hydro_occ.enreg_laboreception l, hydro_occ.enreg_entrepot_echantillon e, hydro_occ.enreg_cargaison c, hydro_occ.accounts_affectationentrepot a, hydro_occ.accounts_myuser u \
                                                 WHERE d.idcargaison_id = r.idcargaison_id \
                                                 AND r.idcargaison_id = l.idcargaison_id  \
                                                 AND l.idcargaison_id = e.idcargaison_id \
                                                 AND e.idcargaison_id = c.idcargaison \
                                                 AND c.entrepot_id = a.entrepot_id \
                                                 AND a.username_id = %s \
                                                 GROUP BY d.idcargaison_id \
                                                 ORDER BY d.datedechargement DESC', [id,]), prefix="1_")


                RequestConfig(request, paginate={"per_page": 15}).configure(table)
                RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table1)
                return render(request, 'entrepot_dechargement.html', {'cargaison': table,
                                                                      'rapport': table1,
                                                                      'form':form,
                                                                      })
            else:
                return redirect('logout')

#Methode permettant d'effectuer un dechargement
    @login_required(login_url='login')
    def dechargementcargaison(request):
        user = request.user
        id = user.id
        role = user.role_id
        url = request.session['url']

        if role == 3 or role == 1 or role == 9:
            if request.is_ajax():
                pk = request.POST.get('pk', None)
                densite15 = request.POST.get('densite15', None)
                gov = request.POST.get('gov', None)
                temperature = request.POST.get('temperature', None)

                # Test de la conformite des donnees
                if pk == '' or densite15 == '' or gov == '' or temperature == '':
                    reponse = 'Erreur de données! Veuillez completer tous les champs obligatoires !'
                    return JsonResponse(reponse, status=400)

                carg = Cargaison.objects.get(idcargaison=pk)
                carg.etat = "Cargaison dechargee"
                immatriculation = carg.immatriculation
                numerodossier = carg.numdossier
                codecamion = carg.codecargaison

                densite15 = float(densite15)
                temperature = float(temperature)
                gov = float(gov)

                # Calcul des GSV MTV MTA
                if densite15 >= float(839):
                    a = 186.9696
                    b = 0.4862
                    delta = temperature - 15
                    alpha = (a / densite15) / densite15 + (b / densite15)
                    vcf = math.exp((-(alpha)) * delta) - 0.8 * ((alpha) * (alpha)) * ((delta * delta))
                    gsv = round((vcf * gov), 5)
                    mtv = gsv * (densite15) / 1000
                    mta = ((densite15) - 1.1) * (gsv / 1000)
                else:
                    if (densite15 >= float(788)) & (densite15 < float(839)):
                        a = 594.5418
                        delta = temperature - 15
                        alpha = (a / densite15) / densite15
                        vcf = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
                        gsv = round((vcf * gov), 5)
                        mtv = gsv * (densite15) / 1000
                        mta = ((densite15) - 1.1) * (gsv / 1000)
                    else:
                        if (densite15 > float(770)) & (densite15 < float(788)):
                            a = 0.00336312
                            b = 2680.3206
                            delta = temperature - 15
                            alpha = ((-a) + (b)) / densite15 / densite15
                            vcf = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
                            gsv = round((vcf * gov), 5)
                            mtv = gsv * densite15 / 1000
                            mta = ((densite15) - 1.1) * (gsv / 1000)
                        else:
                            a = 346.4228
                            b = 0.4388
                            d = densite15
                            delta = temperature - 15
                            alpha = (((a) / (d)) / (d)) + (b / d)
                            vcf = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
                            gsv = round((vcf * gov), 5)
                            mtv = gsv * densite15 / 1000
                            mta = ((densite15) - 1.1) * (gsv / 1000)

                if Resultat.objects.filter(idcargaison_id=pk).exists():
                    carg.save(update_fields=['etat'])
                    p = Dechargement(idcargaison=r, densite15=densite15, temperature=temperature, gov=gov, gsv=gsv,
                                     mtv=mtv, mta=mta)
                    p.save()
                    response = {'valid': True}
                    return JsonResponse(response, status=200)
                else:
                    e = Entrepot_echantillon.objects.get(idcargaison_id=pk)
                    e = e.idcargaison_id
                    d = datetime.datetime.today()
                    d = d.date()
                    codelabo = 0

                    c = LaboReception(idcargaison_id=e, codelabo=codelabo, datereceptionlabo=d)
                    c.save()
                    r = Resultat(idcargaison_id=pk, dateimpression=d)
                    r.save()
                    carg.save(update_fields=['etat'])
                    p = Dechargement(idcargaison=r, densite15=densite15, temperature=temperature, gov=gov, gsv=gsv,
                                     mtv=mtv, mta=mta)
                    p.save()
                    response = {'valid': True}
                    return JsonResponse(response, status=200)

                # try:
                #     r = Resultat.objects.get(idcargaison=pk)
                #
                #     carg.save(update_fields=['etat'])
                #
                #     p = Dechargement(idcargaison=r, densite15=densite15, temperature=temperature, gov=gov, gsv=gsv,
                #                      mtv=mtv, mta=mta)
                #     p.save()
                #
                # except ObjectDoesNotExist:
                #
                #     d = datetime.datetime.today()
                #     d = d.date()
                #     codelabo = 0
                #
                #     c = LaboReception(idcargaison_id=pk, codelabo=codelabo, datereceptionlabo=d)
                #     c.save()
                #
                #     r = Resultat(idcargaison_id=pk, dateimpression=d)
                #     r.save()
                #
                #     carg.save(update_fields=['etat'])
                #
                #     p = Dechargement(idcargaison=r, densite15=densite15, temperature=temperature, gov=gov, gsv=gsv,
                #                      mtv=mtv, mta=mta)
                #     p.save()
                #     response = {'valid': True}
                #     return JsonResponse(response, status=200)
            else:
                return redirect('dechargement')
        else:
            return redirect('logout')
