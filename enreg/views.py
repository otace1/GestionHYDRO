import math
import uuid
from datetime import date

import pyqrcode
from PIL import Image
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core import serializers
from django.shortcuts import render, HttpResponse, redirect
from django_tables2 import RequestConfig
from django_tables2.paginators import LazyPaginator

from .forms import Ajoutcargaison
from .models import Cargaison
from .models import Ville, Voie, Entrepot, Importateur, Produit, Nationalites
from accounts.models import *
from .tables import CargaisonTable



# Create your views here.
class GestionCargaison():

    # Affichage du Tableaux des caragisons enregistrer
    @login_required(login_url='login')
    def qrcodeprint(request):
        user = request.user
        role = user.role_id

        if role == 1 or role == 2:
            code = request.session['qrcode']
            if code == '':
                pass
            else:
                # # Code pour generer le QRCode
                qrobj = pyqrcode.create(code, encoding='utf-8')
                with open('test.png', 'wb') as f:
                    qrobj.png(f, scale=10)
                image_data = open('test.png', 'rb').read()
                response = HttpResponse(image_data, content_type='image/png')
                response['Content-Disposition'] = 'attachment; filename=%s.png'

                return response
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def affichageTableau(request):
        user = request.user
        role = user.role_id
        id = user.id
        u = user.username
        frontiere = AffectationVille.objects.get(username=id)
        user = frontiere.username_id
        form = Ajoutcargaison()
        today = date.today()

        if role == 2:
            table = CargaisonTable(Cargaison.objects.order_by('-dateheurecargaison').filter(user=u,
                                                                                            dateheurecargaison__year=today.year))
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            return render(request, 'cargaison/cargaison.html', {'cargaison': table,
                                                                'form': form})
        else:
            if role == 1:
                form = Ajoutcargaison()
                table = CargaisonTable(
                    Cargaison.objects.filter(dateheurecargaison__year=today.year).order_by('-dateheurecargaison'))
                RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
                return render(request, 'cargaison/cargaison.html', {'cargaison': table,
                                                                    'form': form})
            else:
                return redirect('logout')

    @login_required(login_url='login')
    def enregistrementCargaison(request):
        user = request.user
        role = user.role_id
        id = user.id
        u = user.username
        username = user.username
        frontiere = AffectationVille.objects.get(username=id)
        user = frontiere.ville_id
        d = date.today()

        if role == 2 or role == 1 or role == 7:
            template = 'cargaison/cargaison_form.html'

            # if request.is_ajax and request.method == "POST":
            if request.method == "POST":
                # Get Form DATA
                form = Ajoutcargaison(request.POST)

                #     if form.is_valid():
                #         instance=form.save()
                #         ser_instance = serializers.serialize('json',[instance,])
                #         return JsonResponse({'instance':ser_instance},status=200)
                #     else:
                #         return JsonResponse({'error':form.errors}, status=400)
                #         # some error occured
                # return JsonResponse({"error": ""}, status=400)
                voie = request.POST['voie']
                fournisseur = request.POST['fournisseur']
                manifestdgda = request.POST['manifestdgda']
                numbtfh = request.POST['numbtfh']
                numdeclaration = request.POST['numdeclaration']
                valeurfacture = request.POST['valeurfacture']
                importateur = request.POST['importateur']
                produit = request.POST['produit']
                frontiere = request.POST['frontiere']
                provenance = request.POST['provenance']
                entrepot = request.POST['entrepot']
                transporteur = request.POST['transporteur']
                declarant = request.POST['declarant']
                poids = request.POST['poids']
                volume = request.POST['volume']
                densite = request.POST['densitecargaison']
                t1d = request.POST['t1d']
                t1e = request.POST['t1e']
                idchauffeur = request.POST['idchauffeur']
                nationalite = request.POST['nationalite']
                nomchauffeur = request.POST['nomchauffeur']
                immatriculation = request.POST['immatriculation']
                tempcargaison = 20.00

                if voie == '' or frontiere == '' or importateur == '' or provenance == '' or entrepot == '' or transporteur == '' or declarant == '' or produit == '' or poids == '' or volume == '' or nationalite == '' or nomchauffeur == '' or immatriculation == '':
                    return JsonResponse({'error': form.errors}, status=400)

                # verification de la quantite saisie
                if voie == 1:
                    if volume > 50:
                        msg = 'Vous avez introduit un volume eronee pour la voie routiere'
                        return JsonResponse(msg, safe=False, status=400)
                else:
                    if densite == '':
                        densite = 1

                    if valeurfacture == '':
                        valeurfacture = 0

                    # caste des variables
                    densite = float(densite)
                    tempcargaison = float(tempcargaison)
                    volume = float(volume)

                    # Calcul du volume declare a 15 degre
                    if densite >= float(839):
                        a = 186.9696
                        b = 0.4862
                        delta = tempcargaison - 15
                        alpha = (a / densite) / densite + (b / densite)
                        vcf = math.exp((-(alpha)) * delta) - 0.8 * ((alpha) * (alpha)) * ((delta * delta))
                        gsv = round((vcf * volume), 5)
                        mtv = gsv * (densite) / 1000
                        mta = ((densite) - 1.1) * (gsv / 1000)
                    else:
                        if (densite >= float(788)) & (densite < float(839)):
                            a = 594.5418
                            delta = tempcargaison - 15
                            alpha = (a / densite) / densite
                            vcf = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
                            gsv = round((vcf * volume), 5)
                            mtv = gsv * (densite) / 1000
                            mta = ((densite) - 1.1) * (gsv / 1000)
                        else:
                            if (densite > float(770)) & (densite < float(788)):
                                a = 0.00336312
                                b = 2680.3206
                                delta = tempcargaison - 15
                                alpha = ((-a) + (b)) / densite / densite
                                vcf = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
                                gsv = round((vcf * volume), 5)
                                mtv = gsv * densite / 1000
                                mta = ((densite) - 1.1) * (gsv / 1000)
                            else:
                                a = 346.4228
                                b = 0.4388
                                d = densite
                                delta = tempcargaison - 15
                                alpha = (((a) / (d)) / (d)) + (b / d)
                                vcf = math.exp((-(alpha) * delta) - 0.8 * ((alpha) * (alpha)) * (delta * delta))
                                gsv = round((vcf * volume), 5)
                                mtv = gsv * densite / 1000
                                mta = ((densite) - 1.1) * (gsv / 1000)

                    volume_decl15 = gsv

                    # Gestion des cles etrangeres
                    v = Voie.objects.get(pk=voie)
                    i = Importateur.objects.get(pk=importateur)
                    p = Produit.objects.get(pk=produit)
                    f = Ville.objects.get(pk=frontiere)
                    e = Entrepot.objects.get(pk=entrepot)
                    n = Nationalites.objects.get(pk=nationalite)

                    # Get the name for populating Table with Ajax
                    i1 = i.nomimportateur
                    p1 = p.nomproduit
                    e1 = e.nomentrepot

                    # Assignation de l'etat de l'enregistrenment
                    etat = ("En attente requisition")

                    # Utilisation de l'UUID comme id unique dans la base de donnee
                    code = str(uuid.uuid4())

                    p = Cargaison(voie=v, importateur=i, produit=p, frontiere=f, provenance=provenance, entrepot=e,
                                  fournisseur=fournisseur, manifestdgda=manifestdgda, numbtfh=numbtfh,
                                  numdeclaration=numdeclaration, valeurfacture=valeurfacture, transporteur=transporteur,
                                  declarant=declarant, poids=poids, volume=volume,
                                  tempcargaison=tempcargaison, densitecargaison=densite, volume_decl15=volume_decl15,
                                  t1d=t1d, t1e=t1e, idchauffeur=idchauffeur,
                                  nationalite=n, nomchauffeur=nomchauffeur, immatriculation=immatriculation,
                                  qrcode=code, etat=etat, user=u)
                    p.save()
                    data = {'code': code,
                            # 'date':d,
                            # 'manifestdgda':manifestdgda,
                            # 'numbtfh':numbtfh,
                            # 'numdeclaration':numdeclaration,
                            # 'valeurfacture':valeurfacture,
                            # 'importateur':i1,
                            # 'produit': p1,
                            # 'entrepot':entrepot,
                            # 'volume':volume,
                            # 'entrepot':e1,
                            # 'immatriculation':immatriculation,
                            # 't1d':t1d,
                            # 't1e':t1e
                            }
                    return JsonResponse(data, safe=False, status=200)
            else:
                form = Ajoutcargaison()
            return render(request, template, {'form': form})
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def effacer(request, pk):
        user = request.user
        role = user.role_id
        if role == 2 or role == 1:
            cargaison = Cargaison.objects.get(pk=pk)
            cargaison.delete()
            return redirect('cargaison')
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def showqrcode(request, pk):
        user = request.user
        role = user.role_id
        if role == 2 or role == 1:
            a = Cargaison.objects.get(pk=pk)
            b = a.qrcode
            qrobj = pyqrcode.create(b, encoding='utf-8')
            with open('test.png', 'wb') as f:
                qrobj.png(f, scale=10)
            img = Image.open('test.png')
            image_data = open('test.png', 'rb').read()

            return HttpResponse(image_data, content_type='image/png')

        else:
            return redirect('logout')
