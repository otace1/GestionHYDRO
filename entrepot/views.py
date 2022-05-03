from django.shortcuts import render, redirect
from .tables import EchantillonTable, CargaisonDechargement, EchantillonEnregistrer, CargaisonDechargee, \
    CargaisonEnAttenteRequisition, RapportEchantillonage
from enreg.models import *
from accounts.models import *
from .forms import Echantilloner, Decharger
from labo.utils import render_to_pdf
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import math
from django.db.models import Q, Count
from django_tables2.paginators import LazyPaginator
from django_tables2 import RequestConfig
from datetime import date
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
import datetime
from .numrappech import numRappEch


# Gestion des echantillonages
class GestionEchantillonage():
    # Methode permettant l'affichage du tableau d'echantillonage
    @login_required(login_url='login')
    def tableauechantillonnage(request):
        user = request.user
        role = user.role_id
        id = user.id
        today = date.today()
        request.session['url'] = request.get_full_path()
        form = Echantilloner(request.POST or None)

        if role == 3 or role == 1 or role == 9:
            qs = Cargaison.objects.filter(etat="En attente requisition").filter(
                entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
            qs1 = Cargaison.objects.filter(etat="En attente d'echantillonage").filter(
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
            # table = EchantillonTable(Cargaison.objects.filter(Q(etat='En attente requisition')|Q(tampon='0')).filter(entrepot__affectationentrepot__username_id=id,
            #                              dateheurecargaison__lte=today,
            #                              dateheurecargaison__gt=today - datetime.timedelta(days=90)).order_by('-dateheurecargaison'))
            RequestConfig(request, paginate={"per_page": 12}).configure(table)

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
                entrepot__affectationentrepot__username_id=id, dateheurecargaison__date=today).count()

            d = Cargaison.objects.filter(
                Q(etat='En attente de dechargement') | Q(Q(etat='Conforme aux exigences'))).filter(
                entrepot__affectationentrepot__username_id=id).count()
            # d = Cargaison.objects.filter(Q(etat='En attente de dechargement')|Q(Q(etat='Conforme aux exigences'))).filter(entrepot__affectationentrepot__username_id=id,  dateheurecargaison__lte=today, dateheurecargaison__gt=today-datetime.timedelta(days=90)).count()

            r = Cargaison.objects.filter(Q(etat='En attente requisition') | Q(tampon='0')).filter(
                entrepot__affectationentrepot__username_id=id).count()

            o = Cargaison.objects.filter(Q(etat='En attente de dechargement') | Q(etat='Conforme aux exigences'),
                                         entrepot__affectationentrepot__username_id=id).count()

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
        affectation_entrepot = AffectationEntrepot.objects.get(username=id)
        affectation_entrepot = affectation_entrepot.entrepot
        request.session['url'] = request.get_full_path()
        today = date.today()

        if role == 9:
            # qs = Cargaison.objects.filter(Q(etat="Conforme aux exigences") | Q(etat='En attente de dechargement')).filter(entrepot__affectationentrepot__username_id=id,dateheurecargaison__lte=today,dateheurecargaison__gt=today - datetime.timedelta(days=120)).order_by('-dateheurecargaison')
            # g= Resultat.objects.filter(massevolumique15=)

            qs = Resultat.objects.filter(idcargaison__idcargaison__idcargaison__etat='Echantillonner',
                                         idcargaison__idcargaison__idcargaison__entrepot=affectation_entrepot).order_by(
                '-idcargaison__datereceptionlabo')
            table = CargaisonDechargement(qs, prefix='2_')

            qs1 = Dechargement.objects.filter(
                idcargaison__idcargaison__idcargaison__idcargaison__etat='Cargaison dechargee',
                idcargaison__idcargaison__idcargaison__idcargaison__entrepot=affectation_entrepot).order_by(
                '-datedechargement')
            table1 = CargaisonDechargee(qs1, prefix='1_')

            RequestConfig(request, paginate={"per_page": 17}).configure(table)
            RequestConfig(request, paginate={"per_page": 17}).configure(table1)
            return render(request, 'entrepot_dechargement.html', {'cargaison': table,
                                                                  'rapport': table1,
                                                                  })
        else:
            if role == 3 or role == 1:
                qs = Resultat.objects.filter(
                    Q(idcargaison__idcargaison__idcargaison__etat='Conforme aux exigences') | Q(
                        idcargaison__idcargaison__idcargaison__etat='En attente de dechargement'),
                    idcargaison__idcargaison__idcargaison__entrepot=affectation_entrepot).order_by(
                    '-idcargaison__datereceptionlabo')
                table = CargaisonDechargement(qs, prefix='1_')

                qs1 = Dechargement.objects.filter(
                    idcargaison__idcargaison__idcargaison__idcargaison__etat='Cargaison dechargee',
                    idcargaison__idcargaison__idcargaison__idcargaison__entrepot=affectation_entrepot).order_by(
                    '-datedechargement')
                table1 = CargaisonDechargee(qs1, prefix='1_')

                RequestConfig(request, paginate={"per_page": 17}).configure(table)
                RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 17}).configure(table1)
                return render(request, 'entrepot_dechargement.html', {'cargaison': table,
                                                                      'rapport': table1,
                                                                      })
            else:
                return redirect('logout')


# Methode permettant d'effectuer un dechargement
# @login_required(login_url='login')
# def dechargementcargaison(request):
#     user = request.user
#     id = user.id
#     role = user.role_id
#     url = request.session['url']
#
#     if role == 3 or role == 1 or role == 9:
#         if request.is_ajax():
#             pk = request.POST.get('pk', None)
#             densite15 = request.POST.get('densite15', None)
#             gov = request.POST.get('gov', None)
#             temperature = request.POST.get('temperature', None)
#
#             # Test de la conformite des donnees
#             if pk == '' or densite15 == '' or gov == '' or temperature == '':
#                 reponse = 'Erreur de données! Veuillez completer tous les champs obligatoires !'
#                 return JsonResponse(reponse, status=400)
#
#             carg = Cargaison.objects.get(idcargaison=pk)
#             carg.etat = "Cargaison dechargee"
#             immatriculation = carg.immatriculation
#             numerodossier = carg.numdossier
#             codecamion = carg.codecargaison
#
#             densite15 = float(densite15)
#             temperature = float(temperature)
#             gov = float(gov)
#
#             # Calcul des GSV MTV MTA
#             if densite15 >= float(839):
#                 a = 186.9696
#                 b = 0.4862
#                 delta = temperature - 15
#                 alpha = (a / densite15) / densite15 + (b / densite15)
#                 vcf = math.exp((-(alpha)) * delta) - 0.8 * ((alpha) * (alpha)) * ((delta * delta))
#                 gsv = round((vcf * gov), 5)
#                 mtv = gsv * (densite15) / 1000
#                 mta = ((densite15) - 1.1) * (gsv / 1000)
#             else:
#                 if (densite15 >= float(788)) & (densite15 < float(839)):
#                     a = 594.5418
#                     delta = temperature - 15
#                     alpha = (a / densite15) / densite15
#                     vcf = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
#                     gsv = round((vcf * gov), 5)
#                     mtv = gsv * (densite15) / 1000
#                     mta = ((densite15) - 1.1) * (gsv / 1000)
#                 else:
#                     if (densite15 > float(770)) & (densite15 < float(788)):
#                         a = 0.00336312
#                         b = 2680.3206
#                         delta = temperature - 15
#                         alpha = ((-a) + (b)) / densite15 / densite15
#                         vcf = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
#                         gsv = round((vcf * gov), 5)
#                         mtv = gsv * densite15 / 1000
#                         mta = ((densite15) - 1.1) * (gsv / 1000)
#                     else:
#                         a = 346.4228
#                         b = 0.4388
#                         d = densite15
#                         delta = temperature - 15
#                         alpha = (((a) / (d)) / (d)) + (b / d)
#                         vcf = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
#                         gsv = round((vcf * gov), 5)
#                         mtv = gsv * densite15 / 1000
#                         mta = ((densite15) - 1.1) * (gsv / 1000)
#
#             if Resultat.objects.filter(idcargaison_id=pk).exists():
#                 carg.save(update_fields=['etat'])
#                 r = Resultat.objects.get(idcargaison_id=pk)
#
#                 p = Dechargement(idcargaison=r, densite15=densite15, temperature=temperature, gov=gov, gsv=gsv,
#                                  mtv=mtv, mta=mta, vcf=vcf)
#                 p.save()
#                 response = {'valid': True}
#                 return JsonResponse(response, status=200)
#             else:
#                 e = Entrepot_echantillon.objects.get(idcargaison_id=pk)
#                 e = e.idcargaison_id
#                 d = datetime.datetime.today()
#                 d = d.date()
#                 codelabo = 0
#
#                 c = LaboReception(idcargaison_id=e, codelabo=codelabo, datereceptionlabo=d)
#                 c.save()
#                 r = Resultat(idcargaison_id=pk, dateimpression=d)
#                 r.save()
#                 carg.save(update_fields=['etat'])
#                 p = Dechargement(idcargaison=r, densite15=densite15, temperature=temperature, gov=gov, gsv=gsv,
#                                  mtv=mtv, mta=mta,vcf=vcf)
#                 p.save()
#                 response = {'valid': True}
#                 return JsonResponse(response, status=200)
#         else:
#             return redirect('dechargement')
#     else:
#         return redirect('logout')


def ImpressionRapport(request, pk):
    template = 'rapport.html'

    # Request to fecth data into database
    cargaison_data = Cargaison.objects.get(idcargaison=pk)
    echantillon_data = Entrepot_echantillon.objects.get(idcargaison=pk)
    dechargement_data = Dechargement.objects.get(idcargaison=pk)
    if Resultat.objects.filter(idcargaison_id=pk).exists():
        resultat_data = Resultat.objects.get(idcargaison_id=pk)

    immatriculation = cargaison_data.immatriculation
    entrance = cargaison_data.frontiere
    arrivaldate = cargaison_data.dateheurecargaison
    origin = cargaison_data.provenance.name
    provenance = cargaison_data.provenance.name
    product = cargaison_data.produit
    operationdate = dechargement_data.datedechargement
    receiver = cargaison_data.entrepot
    consigner = cargaison_data.importateur
    gov = dechargement_data.gov
    temperature = dechargement_data.temperature
    densite = dechargement_data.densite15
    vcf = dechargement_data.vcf
    gsv = dechargement_data.gsv
    mta = dechargement_data.mta
    dens15 = resultat_data.densite
    frais = gsv * 11

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
    lastthreecargo = Cargaison.objects.filter(immatriculation=immatriculation).order_by('-dateheurecargaison')[:3]
    taille = len(lastthreecargo)
    array = []
    for p in lastthreecargo:
        array.append(p.produit)

    if taille == 3:
        flast = array[0]
        slast = array[1]
        tlast = array[2]
    else:
        if taille == 2:
            flast = array[0]
            slast = array[1]
            tlast = '-'
        else:
            if taille == 1:
                flast = '-'
                slast = '-'
                tlast = '-'
            else:
                flast = '-'
                slast = '-'
                tlast = '-'

    data = {
        'immatriculation': immatriculation,
        'entrance': entrance,
        'arrivaldate': arrivaldate,
        'origin': origin,
        'provenance': provenance,
        'product': product,
        'operationdate': operationdate,
        'receiver': receiver,
        'consigner': consigner,
        'gov': gov,
        'temperature': temperature,
        'densite': densite,
        'dens15': dens15,
        'vcf': vcf,
        'gsv': gsv,
        'mta': mta,
        'flast': flast,
        'slast': slast,
        'tlast': tlast,
        'color': color,
        'aspect': aspect,
        'odor': odor,
        'frais': frais
    }

    # Render PDF Files
    pdf = render_to_pdf(template, data)
    return HttpResponse(pdf, content_type='application/pdf')


def echantillonage(request, pk):
    template = 'form.html'
    form = Echantilloner()
    pk = pk
    if request.method == 'POST':
        qte = request.POST['qte']
        numplombh = request.POST['numplombh']
        numplombb = request.POST['numplombb']
        numplombbr = request.POST['numplombbr']
        numplombaph = request.POST['numplombaph']
        etatphysique = request.POST['etatphysique']

        c = Cargaison.objects.get(idcargaison=pk)
        ville = c.entrepot.ville
        numrappech = numRappEch(pk,
                                ville)  # Generation automatique du numero de rapport d'achentillonnage / ville et annuel
        numrappechauto = numrappech
        c.rapechctrl = 1
        c.etat = "Echantillonner"
        c.save(update_fields=['etat', 'rapechctrl'])

        e = Entrepot_echantillon(idcargaison=c, numplombb=numplombb, numplombbr=numplombbr, numplombaph=numplombaph,
                                 numplombh=numplombh, numrappech=numrappech, numrappechauto=numrappechauto,
                                 etatphysique=etatphysique, qte=qte)
        e.save()
        return redirect('entrepot')
    else:
        return render(request, template, {'form': form})


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


def dechargement(request, pk):
    template = 'formDecharger.html'
    form = Decharger()
    pk = pk
    request.session['url'] = request.get_full_path()  # Getting URL full path

    # Changement d'etat de la cargaison
    carg = Cargaison.objects.get(idcargaison=pk)
    carg.etat = "Cargaison dechargee"

    # Getting current Year & Month
    today = date.today()
    month = today.month
    year = today.year

    if request.method == 'POST':
        formSave = Decharger(request.POST)
        if formSave.is_valid():
            types = formSave.cleaned_data['types']
            indexinit = formSave.cleaned_data['indexinit']
            indexfin = formSave.cleaned_data['indexfin']
            temperature = formSave.cleaned_data['temperature']
            gov = formSave.cleaned_data['gov']

            # temperature = float(temperature)
            # gov = float(gov)
            # indexinit = float(indexinit)
            # indexfin = float(indexfin)

            # Checking if there is value into index to get GOV by calculation of index values
            if indexinit is not None:
                if indexfin is not None:
                    gov = indexfin - indexinit
                    # print(gov)

            if Resultat.objects.filter(idcargaison_id=pk).exists():
                r = Resultat.objects.get(idcargaison_id=pk)
                key = r.idcargaison_id
                # p = Cargaison.objects.get(idcargaison=pk)
                # # # Getting the product type of this record for further test
                # # p = p.produit.id
                # Retrieve densite of the product from the LAB
                densite = float(r.massevolumique15)
                densite = densite * 1000

                if densite >= float(839):
                    a = 186.9696
                    b = 0.4862
                    delta = temperature - 15
                    alpha = (a / densite) / densite + (b / densite)
                    vcf = math.exp((-(alpha)) * delta) - 0.8 * ((alpha) * (alpha)) * ((delta * delta))
                    gsv = round((vcf * gov), 5)
                    mtv = gsv * (densite) / 1000
                    mta = ((densite) - 1.1) * (gsv / 1000)
                else:
                    if (densite >= float(788)) & (densite < float(839)):
                        a = 594.5418
                        delta = temperature - 15
                        alpha = (a / densite) / densite
                        vcf = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
                        gsv = round((vcf * gov), 5)
                        mtv = gsv * (densite) / 1000
                        mta = ((densite) - 1.1) * (gsv / 1000)
                    else:
                        if (densite > float(770)) & (densite < float(788)):
                            a = 0.00336312
                            b = 2680.3206
                            delta = temperature - 15
                            alpha = ((-a) + (b)) / densite / densite
                            vcf = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
                            gsv = round((vcf * gov), 5)
                            mtv = gsv * densite / 1000
                            mta = ((densite) - 1.1) * (gsv / 1000)
                        else:
                            a = 346.4228
                            b = 0.4388
                            d = densite
                            delta = temperature - 15
                            alpha = (((a) / (d)) / (d)) + (b / d)
                            vcf = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
                            gsv = round((vcf * gov), 5)
                            mtv = gsv * densite / 1000
                            mta = ((densite) - 1.1) * (gsv / 1000)

                # Sauvegarde des infos dans la table Dechargement
                e = Dechargement(idcargaison_id=key, typescontainer=types, indexinitial=indexinit, indexfinal=indexfin,
                                 temperature=temperature, gov=gov, gsv=gsv, mtv=mtv, mta=mta, vcf=vcf)

                # Mise a jour du statut de la cargaison
                carg.save(update_fields=['etat'])

                e.save()
            return redirect('dechargement')
        return redirect('dechargement')
    else:
        return render(request, template, {'form': form})


# Impression certificat de qualite au niveau de l'entrepot
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
