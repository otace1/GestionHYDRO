from django.shortcuts import render, redirect
from enreg.models import Entrepot_echantillon, LaboReception, Cargaison, Resultat, Produit
from accounts.models import AffectationVille, AffectationEntrepot
from .tables import LaboratoireReception, AffichageAnalyse, AffichageValidation1, AffichageValidation2, \
    AffichageTableauImpression, TableEnvoiGo, AffichageValidation2Go, TableauEchantillonRecu, \
    AffichageTableauReImpression, AffichageAnalyseRefaire, RapportLaboTable
from .forms import ReceptionEchantillon, Mogas, Gasoil, JetA1, PetroleLampant, ModificationEchantillon, RapportLabo
from django.contrib.auth.decorators import login_required
from labo.utils import render_to_pdf
from django.http import HttpResponse
from django.db.models import Q
from django_tables2.paginators import LazyPaginator
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport
from datetime import datetime
from django.http import JsonResponse


# Class de gestion pouir le laboratoire
class GestionLaboratoire():
    # Methode d'affichage des echantillons a la reception
    @login_required(login_url='login')
    def affichageenchantillon(request):
        user = request.user
        id = user.id
        role = user.role_id
        form = ReceptionEchantillon()
        form1 = ModificationEchantillon()
        if role == 4 or role == 1:
            table = LaboratoireReception(Cargaison.objects.raw('SELECT c.idcargaison, DATE(c.dateheurecargaison), e.dateechantillonage,e.numrappech,c.numdossier, c.codecargaison , c.immatriculation \
                                                                          FROM hydro_occ.enreg_cargaison c  \
                                                                          LEFT JOIN hydro_occ.enreg_entrepot_echantillon e ON e.idcargaison_id = c.idcargaison \
                                                                          WHERE c.etat = "Echantillonner" \
                                                                          OR c.etat ="En attente d\'echantillonage" \
                                                                          ORDER BY dateechantillonage DESC'),
                                         prefix="1_")

            table1 = TableauEchantillonRecu(Entrepot_echantillon.objects.raw('SELECT e.idcargaison_id, l.datereceptionlabo, l.codelabo ,e.numrappech,c.numdossier, c.codecargaison , c.immatriculation \
                                                                          FROM hydro_occ.enreg_entrepot_echantillon e \
                                                                          LEFT JOIN hydro_occ.enreg_cargaison c ON e.idcargaison_id = c.idcargaison \
                                                                          LEFT JOIN  hydro_occ.enreg_laboreception l ON l.idcargaison_id = e.idcargaison_id \
                                                                          WHERE c.etat = "Analyse Labo en cours" \
                                                                          ORDER BY l.datereceptionlabo DESC'),
                                            prefix="2_")

            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table1)
            return render(request, 'labo.html', {
                'labo': table,
                'labo1': table1,
                'form': form,
                'form1': form1,
            })
        else:
            return redirect('logout')

    # Methode pour receptionner l'echantillon
    @login_required(login_url='login')
    def receptionechantillon(request):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 4 or role == 1:
            # Getting current Year & Month
            now = datetime.today()
            month = now.month
            year = now.year

            if request.is_ajax():
                pk = request.POST.get('pk', None)
                codelabo = request.POST.get('codelabo', None)
                datereception = request.POST.get('datereception', None)
                dateechantillon = request.POST.get('dateprelevement', None)
                # numrappech = request.POST.get('numerore',None)

                # Test de conformite des donnees saisies
                if pk == '' or codelabo == '' or datereception == '' or dateechantillon == '':
                    return JsonResponse(status=400)

                # Test pour voir si il y'a déjà eu enregistrement
                if Entrepot_echantillon.objects.filter(idcargaison_id=pk).exists():
                    t = Entrepot_echantillon.objects.get(idcargaison_id=pk)
                    pk1 = t.idcargaison_id

                    # t.numrappech = numrappech
                    t.dateechantillonage = dateechantillon
                    t.save(update_fields=['numrappech', 'dateechantillonage'])

                    # Changement de l'etat de la cargaison
                    d = Cargaison.objects.get(idcargaison=pk)
                    d.etat = "Analyse Labo en cours"
                    d.save(update_fields=['etat'])

                    # Sauvegarde de l'instruction dans la Table LaboReception
                    p = LaboReception(idcargaison_id=pk1, datereceptionlabo=datereception, codelabo=codelabo)
                    p.save()
                    response = {'valid': True}
                    return JsonResponse(response, status=200)

                else:

                    e = Entrepot_echantillon(idcargaison_id=pk, dateechantillonage=dateechantillon)
                    e.save()

                    e = Entrepot_echantillon.objects.get(idcargaison_id=pk)
                    pk1 = e.idcargaison_id

                    # Changement de l'etat de la cargaison
                    d = Cargaison.objects.get(idcargaison=pk)
                    d.etat = "Analyse Labo en cours"
                    d.tampon = "0"
                    d.save(update_fields=['etat', 'tampon'])

                    # Sauvegarde de l'instruction dans la Table LaboReception
                    p = LaboReception(idcargaison_id=pk1, datereceptionlabo=datereception, codelabo=codelabo)
                    p.save()
                    response = {'valid': True}
                    return JsonResponse(response, status=200)
            else:
                return redirect('labo')
        else:
            return redirect('logout')

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
        role = user.role_id
        form = ReceptionEchantillon()
        form1 = ModificationEchantillon()
        if role == 4 or role == 1:
            q = request.GET.get('q')
            if q == "":
                return redirect('labo')
            else:
                a = '%' + q + '%'
                table = LaboratoireReception(Cargaison.objects.raw('SELECT c.idcargaison,DATE(c.dateheurecargaison), e.dateechantillonage,e.numrappech,c.numdossier, c.codecargaison , c.immatriculation, c.produit_id \
                                                                    FROM hydro_occ.enreg_cargaison c  \
                                                                    LEFT JOIN hydro_occ.enreg_entrepot_echantillon e ON e.idcargaison_id = c.idcargaison \
                                                                    WHERE c.qrcode LIKE %s \
                                                                    OR e.numrappech LIKE %s \
                                                                    OR c.immatriculation LIKE %s \
                                                                    OR c.codecargaison LIKE %s \
                                                                    ORDER BY dateechantillonage DESC', [q, a, a, q, ]),
                                             prefix="1_")

                table1 = TableauEchantillonRecu(Entrepot_echantillon.objects.raw('SELECT e.idcargaison_id, l.datereceptionlabo, l.codelabo ,e.numrappech,c.numdossier, c.codecargaison , c.immatriculation, c.produit_id \
                                                                          FROM hydro_occ.enreg_entrepot_echantillon e \
                                                                          LEFT JOIN hydro_occ.enreg_cargaison c ON e.idcargaison_id = c.idcargaison \
                                                                          LEFT JOIN  hydro_occ.enreg_laboreception l ON l.idcargaison_id = e.idcargaison_id \
                                                                          WHERE c.etat = "Analyse Labo en cours" \
                                                                          ORDER BY l.datereceptionlabo DESC'),
                                                prefix="2_")

                RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 10}).configure(table)
                RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 10}).configure(table1)

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
        role = user.role_id
        form1 = ModificationEchantillon()
        form = ReceptionEchantillon()
        if role == 4 or role == 1:
            q = request.GET.get('q')
            if q == "":
                return redirect('labo')
            else:

                table = LaboratoireReception(Cargaison.objects.raw('SELECT c.idcargaison,DATE(c.dateheurecargaison), e.dateechantillonage,e.numrappech,c.numdossier, c.codecargaison , c.immatriculation \
                                                                          FROM hydro_occ.enreg_cargaison c  \
                                                                          LEFT JOIN hydro_occ.enreg_entrepot_echantillon e ON e.idcargaison_id = c.idcargaison \
                                                                          WHERE c.etat = "Echantillonner" \
                                                                          OR c.etat ="En attente d\'echantillonage" \
                                                                          ORDER BY dateechantillonage DESC'),
                                             prefix="1_")

                table1 = TableauEchantillonRecu(Entrepot_echantillon.objects.raw('SELECT e.idcargaison_id, l.datereceptionlabo, l.codelabo ,e.numrappech,c.numdossier, c.codecargaison , c.immatriculation, c.produit_id \
                                                                                        FROM hydro_occ.enreg_entrepot_echantillon e \
                                                                                        LEFT JOIN hydro_occ.enreg_cargaison c ON e.idcargaison_id = c.idcargaison \
                                                                                        LEFT JOIN  hydro_occ.enreg_laboreception l ON l.idcargaison_id = e.idcargaison_id \
                                                                                        WHERE c.etat = "Analyse Labo en cours" \
                                                                                        AND l.codelabo = %s \
                                                                                        ORDER BY l.datereceptionlabo DESC',
                                                                                 [q, ]), prefix="2_")
                RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 10}).configure(table)
                RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 10}).configure(table1)
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
        id = user.id
        role = user.role_id
        request.session['url'] = request.get_full_path()
        if role == 5 or role == 1:
            table1 = AffichageAnalyse(LaboReception.objects.raw('SELECT l.idcargaison_id, l.datereceptionlabo, e.numrappech, l.numcertificatqualite, l.codelabo \
                                                                    FROM hydro_occ.enreg_laboreception l, hydro_occ.enreg_cargaison c, hydro_occ.enreg_entrepot_echantillon e \
                                                                    WHERE l.idcargaison_id = c.idcargaison \
                                                                    AND c.idcargaison = e.idcargaison_id \
                                                                    AND c.etat = "Analyse Labo en cours" \
                                                                    ORDER BY l.datereceptionlabo DESC'), prefix="1_")

            table2 = AffichageAnalyseRefaire(LaboReception.objects.raw('SELECT l.idcargaison_id, l.datereceptionlabo, e.numrappech, l.numcertificatqualite, l.codelabo \
                                                                    FROM hydro_occ.enreg_laboreception l, hydro_occ.enreg_cargaison c, hydro_occ.enreg_entrepot_echantillon e \
                                                                    WHERE l.idcargaison_id = c.idcargaison \
                                                                    AND c.idcargaison = e.idcargaison_id \
                                                                    AND c.etat = "Refaire" \
                                                                    ORDER BY l.datereceptionlabo DESC'), prefix="2_")

            RequestConfig(request, paginate={"per_page": 17}).configure(table1)
            RequestConfig(request, paginate={"per_page": 17}).configure(table2)
            return render(request, 'labo_analyse.html', {
                'analyse': table1,
                'refaire': table2,
            })
        else:
            return redirect('logout')

    # Fonction de recherche pour encodage résultat
    @login_required(login_url='login')
    def rechercheencodage1(request):
        user = request.user
        id = user.id
        role = user.role_id

        if role == 5 or role == 1:
            q = request.GET.get('codelabo')

            if q == "":
                return redirect('analyse')
            else:
                table1 = AffichageAnalyse(LaboReception.objects.raw('SELECT l.idcargaison_id, l.datereceptionlabo, e.numrappech, l.numcertificatqualite, l.codelabo \
                                                                                                            FROM hydro_occ.enreg_laboreception l, hydro_occ.enreg_cargaison c, hydro_occ.enreg_entrepot_echantillon e \
                                                                                                            WHERE l.idcargaison_id = c.idcargaison \
                                                                                                            AND c.idcargaison = e.idcargaison_id \
                                                                                                            AND c.etat = "Analyse Labo en cours" \
                                                                                                            AND l.codelabo = %s',
                                                                    [q, ]), prefix="1_")

                table2 = AffichageAnalyseRefaire(LaboReception.objects.raw('SELECT l.idcargaison_id, l.datereceptionlabo, e.numrappech, l.numcertificatqualite, l.codelabo \
                                                                                                        FROM hydro_occ.enreg_laboreception l, hydro_occ.enreg_cargaison c, hydro_occ.enreg_entrepot_echantillon e \
                                                                                                        WHERE l.idcargaison_id = c.idcargaison \
                                                                                                        AND c.idcargaison = e.idcargaison_id \
                                                                                                        AND c.etat = "Refaire" \
                                                                                                        ORDER BY l.datereceptionlabo DESC'),
                                                 prefix="2_")

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

        if role == 5 or role == 1:
            q = request.GET.get('codelabo1')

            if q == "":
                return redirect('analyse')
            else:
                table1 = AffichageAnalyse(LaboReception.objects.raw('SELECT l.idcargaison_id, l.datereceptionlabo, e.numrappech, l.numcertificatqualite, l.codelabo \
                                                                                                            FROM hydro_occ.enreg_laboreception l, hydro_occ.enreg_cargaison c, hydro_occ.enreg_entrepot_echantillon e \
                                                                                                            WHERE l.idcargaison_id = c.idcargaison \
                                                                                                            AND c.idcargaison = e.idcargaison_id \
                                                                                                            AND c.etat = "Analyse Labo en cours" \
                                                                                                            ORDER BY l.datereceptionlabo DESC'),
                                          prefix="1_")

                table2 = AffichageAnalyseRefaire(LaboReception.objects.raw('SELECT l.idcargaison_id, l.datereceptionlabo, e.numrappech, l.numcertificatqualite, l.codelabo \
                                                                                                        FROM hydro_occ.enreg_laboreception l, hydro_occ.enreg_cargaison c, hydro_occ.enreg_entrepot_echantillon e \
                                                                                                        WHERE l.idcargaison_id = c.idcargaison \
                                                                                                        AND c.idcargaison = e.idcargaison_id \
                                                                                                        AND l.codelabo = %s',
                                                                           [q, ]), prefix="2_")

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

    # Fontion pour encodage type produit MOGAS
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

                p = Resultat(idcargaison=a, aspect=aspect, odeur=odeur, couleursaybolt=couleursaybolt, soufre=soufre,
                             distillation=distillation, pointfinal=pointfinal,
                             residu=residu, corrosion=corrosion, pourcent10=pourcent10, pourcent20=pourcent20,
                             pourcent50=pourcent50, pourcent70=pourcent70, pourcent90=pourcent90,
                             tensionvapeur=tensionvapeur, difftemperature=difftemperature, plomb=plomb,
                             indiceoctane=indiceoctane, massevolumique15=massevolumique15,
                             dateimpression=dateimpression)
                p.save()
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
        form = RapportLabo()
        if role == 5 or role == 1 or role == 6:
            table = AffichageValidation1(Resultat.objects.raw('SELECT r.idcargaison_id, r.dateanalyse, c.importateur_id, c.produit_id, e.numrappech, l.codelabo, l.numcertificatqualite \
                                                                FROM hydro_occ.enreg_resultat r, hydro_occ.enreg_laboreception l, hydro_occ.enreg_cargaison c, hydro_occ.enreg_entrepot_echantillon e \
                                                                WHERE  r.idcargaison_id = l.idcargaison_id \
                                                                AND c.idcargaison = l.idcargaison_id \
                                                                AND e.idcargaison_id = c.idcargaison \
                                                                AND c.etat = "Validation en cours 1" \
                                                                ORDER BY r.dateanalyse DESC'))

            RequestConfig(request, paginate={"per_page": 14}).configure(table)
            return render(request, 'labo_validation1.html', {'labo': table,
                                                             'form': form, })
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
            provenance = a.provenance
            qte = b.qte
            datereceptionlabo = c.datereceptionlabo
            codelabo = c.codelabo
            numdossier = a.numdossier
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
    def refaire(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        url = request.session['url']
        if role == 6 or role == 1:
            c = Cargaison.objects.get(idcargaison=pk)
            c.etat = "Refaire"
            c.save(update_fields=['etat'])
            return redirect(url)
        else:
            return redirect('logout')

    # Validation du responsable Division LABO OCC
    @login_required(login_url='login')
    def conforme(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        url = request.session['url']
        if role == "v2" or role == 1 or role == 6:
            c = Cargaison.objects.get(idcargaison=pk)
            e = Entrepot_echantillon.objects.get(idcargaison_id=c.idcargaison)
            r = LaboReception.objects.get(idcargaison_id=e.idcargaison_id)
            cq = r.numcertificatqualite
            if cq == "":
                return redirect('validation1')
            else:
                c.etat = "Conforme aux exigences"
                c.conformite = "Conforme aux exigences"
                c.impression = "0"
                c.save(update_fields=['etat', 'conformite', 'impression'])
                return redirect(url)
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def nonconforme(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        url = request.session['url']

        if role == "v2" or role == 1 or role == 6:
            c = Cargaison.objects.get(idcargaison=pk)
            e = Entrepot_echantillon.objects.get(idcargaison_id=c.idcargaison)
            r = LaboReception.objects.get(idcargaison_id=e.idcargaison_id)
            cq = r.numcertificatqualite
            if cq == "":
                return redirect('validation1')
            else:
                c.etat = "Non conforme aux exigences"
                c.conformite = "Non conforme aux exigences"
                c.impression = "0"
                c.save(update_fields=['etat', 'conformite', 'impression'])
                return redirect(url)
        return redirect('logout')

    @login_required(login_url='login')
    def conforme2(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 1 or role == "ad":
            c = Cargaison.objects.get(idcargaison=pk)
            a = LaboReception.objects.get(idcargaison=pk)
            aspect = 0
            odeur = 0
            couleursaybolt = 0
            couleurastm = 0
            c.etat = "Conforme aux exigences"
            c.conformite = "Conforme aux exigences"
            c.impression = "0"
            c.save(update_fields=['etat', 'impression', 'conformite'])

            p = Resultat(idcargaison=a, aspect=aspect, odeur=odeur, couleursaybolt=couleursaybolt,
                         couleurastm=couleurastm
                         )
            p.save()

            return redirect('validation2')
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def nonconforme2(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 1 or role == "ad":
            c = Cargaison.objects.get(idcargaison=pk)
            a = LaboReception.objects.get(idcargaison=pk)

            aspect = 0
            odeur = 0
            couleursaybolt = 0
            couleurastm = 0

            c.etat = "Non conforme aux exigences"
            c.impression = "0"
            c.save(update_fields=['etat', 'impression'])

            p = Resultat(idcargaison=a, aspect=aspect, odeur=odeur, couleursaybolt=couleursaybolt,
                         couleurastm=couleurastm
                         )
            p.save()

            return redirect('validation2')
        else:
            return redirect('logout')

    # Fonction affichage des resultats sur Validation 1
    @login_required(login_url='login')
    def affichagetableauvalidation2(request):
        user = request.user
        id = user.id
        role = user.role_idole
        if role == "v2" or role == 1:

            table1 = AffichageValidation2(Resultat.objects.raw('SELECT r.idcargaison_id, r.dateanalyse, c.importateur_id, c.produit_id, e.numrappech, l.codelabo, l.numcertificatqualite \
                                                                FROM hydro_occ.enreg_resultat r, hydro_occ.enreg_laboreception l, hydro_occ.enreg_cargaison c, hydro_occ.enreg_entrepot_echantillon e \
                                                                WHERE  r.idcargaison_id = l.idcargaison_id \
                                                                AND c.idcargaison = l.idcargaison_id \
                                                                AND e.idcargaison_id = c.idcargaison \
                                                                ORDER BY r.dateanalyse DESC'))

            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 10}).configure(table1)

            table2 = AffichageValidation2Go(LaboReception.objects.order_by('-datereceptionlabo').filter(Q(
                idcargaison__idcargaison__etat="En attente validation 2") | Q(
                idcargaison__idcargaison__etat="Analyse Labo en cours"),
                                                                                                        idcargaison__idcargaison__entrepot_id__ville_id=user.ville))
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 10}).configure(table2)

            return render(request, 'labo_validation2.html', {
                'labo': table1,
                'labo1': table2
            })
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
        request.session['url'] = request.get_full_path()
        if role == 5 or role == 1 or role == "v1" or role == "v2":
            table = AffichageTableauImpression(Resultat.objects.raw('SELECT r.idcargaison_id, r.dateanalyse, l.numcertificatqualite, c.produit_id, l.codelabo, e.numrappech, c.importateur_id \
                                                FROM hydro_occ.enreg_resultat r, hydro_occ.enreg_cargaison c, hydro_occ.enreg_laboreception l, hydro_occ.enreg_entrepot_echantillon e \
                                                WHERE r.idcargaison_id = c.idcargaison \
                                                AND c.idcargaison = l.idcargaison_id \
                                                AND l.idcargaison_id = e.idcargaison_id \
                                                AND c.conformite = "Conforme aux exigences" \
                                                AND c.impression = 0 \
                                                ORDER BY r.dateanalyse DESC'), prefix='2_')

            table1 = AffichageTableauReImpression(Resultat.objects.raw('SELECT r.idcargaison_id, r.dateanalyse, l.numcertificatqualite, c.produit_id, l.codelabo, e.numrappech, c.importateur_id \
                                                FROM hydro_occ.enreg_resultat r, hydro_occ.enreg_cargaison c, hydro_occ.enreg_laboreception l, hydro_occ.enreg_entrepot_echantillon e \
                                                WHERE r.idcargaison_id = c.idcargaison \
                                                AND c.idcargaison = l.idcargaison_id \
                                                AND l.idcargaison_id = e.idcargaison_id \
                                                AND c.impression = 1 \
                                                ORDER BY r.dateanalyse DESC'), prefix='3_')

            RequestConfig(request, paginate={"per_page": 14}).configure(table)
            RequestConfig(request, paginate={"per_page": 14}).configure(table1)

            return render(request, 'labo_impression.html',
                          {
                              'labo': table,
                              'labo1': table1
                          })
        else:
            return redirect('logout')

    # Fonction de recherche des certificat à imprimer
    @login_required(login_url='login')
    def recherchecq(request):
        user = request.user
        id = user.id
        role = user.role_id
        request.session['url'] = request.get_full_path()
        if role == 5 or role == 1 or role == 6 or role == "v2":
            numcode = request.GET.get('codelabo')
            if numcode != "":
                table = AffichageTableauImpression(Resultat.objects.raw('SELECT r.idcargaison_id, r.dateanalyse, l.numcertificatqualite, c.produit_id, l.codelabo, e.numrappech, c.importateur_id \
                                                                FROM hydro_occ.enreg_resultat r, hydro_occ.enreg_cargaison c, hydro_occ.enreg_laboreception l, hydro_occ.enreg_entrepot_echantillon e \
                                                                WHERE r.idcargaison_id = c.idcargaison \
                                                                AND c.idcargaison = l.idcargaison_id \
                                                                AND l.idcargaison_id = e.idcargaison_id \
                                                                AND c.conformite = "Conforme aux exigences" \
                                                                AND c.impression = 0 \
                                                                AND l.codelabo = %s \
                                                                ORDER BY r.dateanalyse DESC', [numcode, ]), prefix='2_')

                # table1 = AffichageTableauReImpression(Resultat.objects.raw('SELECT r.idcargaison_id, r.dateanalyse, l.numcertificatqualite, c.produit_id, l.codelabo, e.numrappech, c.importateur_id \
                #                                                 FROM hydro_occ.enreg_resultat r, hydro_occ.enreg_cargaison c, hydro_occ.enreg_laboreception l, hydro_occ.enreg_entrepot_echantillon e \
                #                                                 WHERE r.idcargaison_id = c.idcargaison \
                #                                                 AND c.idcargaison = l.idcargaison_id \
                #                                                 AND l.idcargaison_id = e.idcargaison_id \
                #                                                 AND c.impression = 1 \
                #                                                 ORDER BY r.dateanalyse DESC'), prefix='3_')

                RequestConfig(request, paginate={"per_page": 10}).configure(table)
                # RequestConfig(request, paginate={"per_page": 10}).configure(table1)

                return render(request, 'labo_impression.html',
                              {
                                  'labo': table,
                                  # 'labo1': table1
                              })
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
        request.session['url'] = request.get_full_path()
        if role == 5 or role == 1 or role == "v1" or role == "v2":
            numcode = request.GET.get('codelabo')
            if numcode != "":
                table = AffichageTableauImpression(Resultat.objects.raw('SELECT r.idcargaison_id, r.dateanalyse, l.numcertificatqualite, c.produit_id, l.codelabo, e.numrappech, c.importateur_id \
                                                                                FROM hydro_occ.enreg_resultat r, hydro_occ.enreg_cargaison c, hydro_occ.enreg_laboreception l, hydro_occ.enreg_entrepot_echantillon e \
                                                                                WHERE r.idcargaison_id = c.idcargaison \
                                                                                AND c.idcargaison = l.idcargaison_id \
                                                                                AND l.idcargaison_id = e.idcargaison_id \
                                                                                AND c.conformite = "Conforme aux exigences" \
                                                                                AND c.impression = 1 \
                                                                                AND l.codelabo = %s \
                                                                                ORDER BY r.dateanalyse DESC',
                                                                        [numcode, ]), prefix='2_')

                # table1 = AffichageTableauReImpression(Resultat.objects.raw('SELECT r.idcargaison_id, r.dateanalyse, l.numcertificatqualite, c.produit_id, l.codelabo, e.numrappech, c.importateur_id \
                #                                                 FROM hydro_occ.enreg_resultat r, hydro_occ.enreg_cargaison c, hydro_occ.enreg_laboreception l, hydro_occ.enreg_entrepot_echantillon e \
                #                                                 WHERE r.idcargaison_id = c.idcargaison \
                #                                                 AND c.idcargaison = l.idcargaison_id \
                #                                                 AND l.idcargaison_id = e.idcargaison_id \
                #                                                 AND c.impression = 1 \
                #                                                 AND l.codelabo=%s \
                #                                                 ORDER BY r.dateanalyse DESC', [numcode, ]), prefix='3_')

                RequestConfig(request, paginate={"per_page": 10}).configure(table)
                # RequestConfig(request, paginate={"per_page": 10}).configure(table1)

                return render(request, 'labo_impression.html',
                              {
                                  'labo': table,
                                  # 'labo1': table1
                              })
            else:
                return redirect('impression')
        else:
            return redirect('logout')

    # Fonction pour impression Certificat
    @login_required(login_url='login')
    def impressioncertificat(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        url = request.session['url']
        if role == 5 or role == 1 or role == "v1" or role == "v2":

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
            provenance = a.provenance
            qte = b.qte
            datereceptionlabo = c.datereceptionlabo
            codelabo = c.codelabo
            numdossier = a.numdossier
            immatriculation = a.immatriculation
            numrappech = b.numrappech

            # Putting printing counter to 1
            a.impression = "1"
            a.save(update_fields=['impression'])

            # Saving print date into DBS
            d.dateimpression = today
            d.save(update_fields=['dateimpression'])
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

    # Fonction pour impression Certificat
    @login_required(login_url='login')
    def reimpressioncertificat(request, pk):
        user = request.user
        id = user.id
        role = user.role_id
        url = request.session['url']
        if role == 5 or role == 1 or role == "v1" or role == "v2":
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
            provenance = a.provenance
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
            provenance = a.provenance
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
