from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.db import connection
from enreg.models import Entrepot, Produit, Ville, Importateur, Cargaison, Paiement, Dechargement, Liquidation
from django.db.models import Q
from .tables import EntrepotTable, ImportateurTable, VilleTable, ProduitTable, StatistiquesTable, DerniersEnregistrements, ProductionTable, EncaissementTable
from .forms import EntrepotForm, EntrepotEditForm, ImportateurForm, ImportateurEditForm, VilleForm, ProduitForm, \
    ProduitEditForm, RechercheStat, RechercheEncaissement
import json
from django.db.models import Sum
import simplejson
from datetime import datetime
import datetime
import csv, io
from django_tables2 import RequestConfig
from django_tables2.paginators import LazyPaginator
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django_tables2.export.export import TableExport
import math



@login_required(login_url='login')
# Fonction pour affichage page dashboard
class Dashboard():
    def chartjs(request):
        user = request.user
        role = user.role_id
        if role == 1 or role == 'st' or role == 7 or role == 8:
            today = datetime.datetime.now()
            year = today.year
            month = today.month
            day = today.day

            template = 'admin.html'
            # Gasoil
            cursor1 = connection.cursor()
            cursor1.execute(
                'SELECT SUM(volume) \
                 FROM hydro_occ.enreg_cargaison \
                 where produit_id =2 \
                 and MONTH (dateheurecargaison) = MONTH (CURRENT_DATE) \
                 and YEAR (dateheurecargaison) = YEAR (CURRENT_DATE)')
            g1data = cursor1.fetchone()

            # Mogas
            cursor2 = connection.cursor()
            cursor2.execute(
                'SELECT SUM(volume) FROM hydro_occ.enreg_cargaison WHERE MONTH(dateheurecargaison)=MONTH(CURRENT_DATE) AND YEAR(dateheurecargaison)=YEAR(CURRENT_DATE) AND produit_id=1')
            g2data = cursor2.fetchone()

            # JETA1
            cursor3 = connection.cursor()
            cursor3.execute(
                'SELECT SUM(volume) FROM hydro_occ.enreg_cargaison WHERE MONTH(dateheurecargaison)=MONTH(CURRENT_DATE) AND YEAR(dateheurecargaison)=YEAR(CURRENT_DATE) AND produit_id=3')
            g3data = cursor2.fetchone()

            # Petrole Lampant
            cursor4 = connection.cursor()
            cursor4.execute(
                'SELECT SUM(volume) FROM hydro_occ.enreg_cargaison WHERE MONTH(dateheurecargaison)=MONTH(CURRENT_DATE) AND YEAR(dateheurecargaison)=YEAR(CURRENT_DATE) AND produit_id=4')
            g4data = cursor2.fetchone()

            dataset = Cargaison.objects \
                .extra(select={'month': 'EXTRACT(month from dateheurecargaison)'}) \
                .values('month') \
                .filter(dateheurecargaison__year=year) \
                .annotate(gasoil=Sum('volume', filter=Q(produit=2)),
                          mogas=Sum('volume', filter=Q(produit=1)),
                          jeta1=Sum('volume', filter=Q(produit=3)),
                          petrole=Sum('volume', filter=Q(produit=4))) \
                .order_by('month')

            categories_list = list()
            gasoil_list = list()
            mogas_list = list()
            jeta1_list = list()
            petrole_list = list()

            # Valeur du Dictionnaires dataset
            for data in dataset:
                categories_list.append(data['month'])
                gasoil_list.append(data['gasoil'])
                mogas_list.append(data['mogas'])
                jeta1_list.append(data['jeta1'])
                petrole_list.append(data['petrole'])

            categories = json.dumps(categories_list)
            gasoil_list = simplejson.dumps(gasoil_list)
            mogas_list = simplejson.dumps(mogas_list)
            jeta1_list = simplejson.dumps(jeta1_list)
            petrole_list = simplejson.dumps(petrole_list)

            form = RechercheStat()
            form1 = RechercheEncaissement()

            # Statistiques des TOP 10 importateurs
            cursor5 = connection.cursor()
            cursor5.execute('SELECT DISTINCT c.importateur_id as importateur_id, i.nomimportateur as nomimportateur, CONVERT(SUM(c.volume),CHAR) AS vol \
                             FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_importateur i \
                             WHERE YEAR(c.dateheurecargaison)=YEAR(CURRENT_DATE) \
                             AND c.importateur_id = i.idimportateur \
                             GROUP BY importateur_id \
                             ORDER BY SUM(c.volume) DESC \
                             LIMIT 10')

            importateur = cursor5.fetchall()

            #récupération des classements par volume
            vol = list()
            imp = list()

            # A activer en debut d'annee
            # if not vol:
            #     vol = [1,1,1,1,1,1,1,1,1,1]
            #
            # if not imp:
            #     imp = [1,1,1,1,1,1,1,1,1,1]


            for volume in importateur:
                vol.append(volume[2])
                imp.append(volume[1])

            v1=vol[0]
            v2=vol[1]
            v3=vol[2]
            v4=vol[3]
            v5=vol[4]
            v6=vol[5]
            v7=vol[6]
            v8=vol[7]
            v9=vol[8]
            v10=vol[9]

            i1=imp[0]
            i2=imp[1]
            i3=imp[2]
            i4=imp[3]
            i5=imp[4]
            i6=imp[5]
            i7=imp[6]
            i8=imp[7]
            i9=imp[8]
            i10=imp[9]

            #Total year Stats
            cursor6=connection.cursor()
            cursor6.execute('SELECT DISTINCT CONVERT(SUM(c.volume),CHAR) AS vol \
                             FROM hydro_occ.enreg_cargaison c \
                             WHERE YEAR(c.dateheurecargaison)=YEAR(CURRENT_DATE)')

            total=cursor6.fetchone()

            if total == 0:
                total == 1

            pourcentage = list()

            if not pourcentage :
                pourcentage = [1,1,1,1,1,1,1,1,1,1]
                volume = [1,1,1,1,1,1,1,1,1,1]

            for data in importateur:
                volume = float(data[2])
                pourcent = (volume * 100)/float(total[0])
                pourcentage.append(pourcent)

            #Récupération des pourcentage
            p1=math.ceil(pourcentage[0])
            p2=math.ceil(pourcentage[1])
            p3=math.ceil(pourcentage[2])
            p4=math.ceil(pourcentage[3])
            p5=math.ceil(pourcentage[4])
            p6=math.ceil(pourcentage[5])
            p7=math.ceil(pourcentage[6])
            p8=math.ceil(pourcentage[7])
            p9=math.ceil(pourcentage[8])
            p10=math.ceil(pourcentage[9])

            #Tableau des derniers enregistrements
            table = DerniersEnregistrements(Cargaison.objects.all().order_by('-idcargaison')[:8])
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)


            # Activité journalier donut chart
            cursor7 = connection.cursor()
            cursor7.execute('SELECT COUNT(idcargaison) \
                                FROM hydro_occ.enreg_cargaison \
                            WHERE DATE(dateheurecargaison)=CURRENT_DATE AND etat="En attente requisition"')

            n = cursor7.fetchone()

            cursor7 = connection.cursor()
            cursor7.execute('SELECT COUNT(idcargaison_id) \
                        FROM hydro_occ.enreg_entrepot_echantillon \
                        WHERE DATE(dateechantillonage)=CURRENT_DATE')

            e = cursor7.fetchone()

            cursor7 = connection.cursor()
            cursor7.execute('SELECT COUNT(idcargaison_id) \
                                FROM hydro_occ.enreg_dechargement \
                                WHERE DATE(datedechargement)=CURRENT_DATE')

            d = cursor7.fetchone()

            cursor7 = connection.cursor()
            cursor7.execute('SELECT COUNT(idcargaison_id) \
                            FROM hydro_occ.enreg_laboreception \
                                WHERE DATE(datereceptionlabo)=CURRENT_DATE')

            l = cursor7.fetchone()

            return render(request, template,
                          {
                              'categories': categories,
                              'gasoil_list': gasoil_list,
                              'mogas_list': mogas_list,
                              'jeta1_list': jeta1_list,
                              'petrole_list': petrole_list,
                              'g1data': g1data,
                              'g2data': g2data,
                              'g3data': g3data,
                              'g4data': g4data,
                              'form': form,
                              'form1':form1,
                              'importateur':importateur,
                              'total':total,
                              'volume':volume,
                              'pourcentage':pourcentage,
                              'p1':p1,
                              'p2':p2,
                              'p3':p3,
                              'p4':p4,
                              'p5':p5,
                              'p6':p6,
                              'p7':p7,
                              'p8':p8,
                              'p9':p9,
                              'p10':p10,
                              'v1':v1,
                              'v2':v2,
                              'v3':v3,
                              'v4':v4,
                              'v5':v5,
                              'v6':v6,
                              'v7':v7,
                              'v8':v8,
                              'v9':v9,
                              'v10':v10,
                              'i1':i1,
                              'i2':i2,
                              'i3':i3,
                              'i4':i4,
                              'i5':i5,
                              'i6':i6,
                              'i7':i7,
                              'i8':i8,
                              'i9':i9,
                              'i10':i10,
                              'n': n,
                              'e': e,
                              'd': d,
                              'l': l,
                              'table':table,
                          })

        else:
            return redirect('logout')

    # Fonction Recherche Statistique Detaillé
    def statistiquesimportations(request):
        template = 'stats.html'
        user = request.user
        role = user.role_id
        if role == 1 or role == 'st' or role == 7 or role == 8:

            if request.method == 'POST':

                template = 'stats.html'
                frontiere = request.POST['frontiere']
                produit = request.POST['produit']
                importateur = request.POST['importateur']
                entrepot = request.POST['entrepot']
                date_d = request.POST['date_d']
                date_f = request.POST['date_f']

                frontiereqs = frontiere
                produitqs = produit
                importateurqs = importateur
                entrepotqs = entrepot
                date_dqs = date_d
                date_fqs = date_f

                request.session['frontiere'] = frontiereqs
                request.session['produit'] = produitqs
                request.session['importateur'] = importateurqs
                request.session['entrepot'] = entrepotqs
                request.session['date_d'] = date_d
                request.session['date_f'] = date_f

                # R1
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.order_by('-dateheurecargaison'),prefix="1_")
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)

                                        return render(request, 'stats.html', {
                                            'cargaison': table
                                        })

                # R2
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(dateheurecargaison__startswith=date_f),prefix='2_')
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R3
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(dateheurecargaison__startswith=date_d), prefix='3_')
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R4
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R5
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R6
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(entrepot=entrepot, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R7
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(entrepot=entrepot, dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R8
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(entrepot=entrepot, dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R9
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(importateur=importateur))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R10
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(importateur=importateur, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R11
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(importateur=importateur, dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R12
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(importateur=importateur, dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R13
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(importateur=importateur, entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R14
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(importateur=importateur, entrepot=entrepot, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R15
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(importateur=importateur, entrepot=entrepot, dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R16
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(importateur=importateur, entrepot=entrepot, dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,"per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R17
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R18
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R19
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":

                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R20
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R21
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R22
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit,entrepot=entrepot, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R23
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":

                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, entrepot=entrepot, dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R24
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, entrepot=entrepot, dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R25
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, importateur=importateur))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R26
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, importateur=importateur, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R26
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":

                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, importateur=importateur, dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 20}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R27
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, importateur=importateur, dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R28
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, importateur=importateur, entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R29
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, importateur=importateur, entrepot=entrepot, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R30
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, importateur=importateur, entrepot=entrepot, dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R31
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit, importateur=importateur, entrepot=entrepot, dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R32
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R32
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R33
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R34
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R35
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R35
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, entrepot=entrepot, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R36
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, entrepot=entrepot, dateheurecargaison__startwith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R37
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, entrepot=entrepot, dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, importateur=importateur))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R40
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, importateur=importateur, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R41
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, importateur=importateur, dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R42
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere,importateur=importateur,dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R43
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, importateur=importateur, entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R44
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, importateur=importateur, entrepot=entrepot, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R45
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, importateur=importateur, entrepot=entrepot, dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R46
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, importateur=importateur, entrepot=entrepot, dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R47
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, produit=produit))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R48
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, produit=produit, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R49
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere,produit=produit, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R50
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, produit=produit, dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R51
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, produit=produit, dateheurecargaison__startswith=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R52
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, produit=produit, entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R53
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, produit=produit, entrepot=entrepot, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R54
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, produit=produit, entrepot=entrepot, dateheurecargaison__startswith=date_d))

                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R55
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, produit=produit, entrepot=entrepot, dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R56
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, produit=produit, importateur=importateur))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R57
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere, produit=produit, importateur=importateur, dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R58
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere,produit=produit,importateur=importateur, dateheurecargaison__startswith=date_d))

                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R58
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere,produit=produit,importateur=importateur, dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))

                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R59
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere,produit=produit,importateur=importateur,entrepot=entrepot))

                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R60
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere,produit=produit,importateur=importateur,entrepot=entrepot,dateheurecargaison__startswith=date_f))

                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})

                # R61
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere,produit=produit,importateur=importateur,entrepot=entrepot, dateheurecargaison__startswith=date_d))

                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        return render(request, 'stats.html', {'cargaison': table})
                # R62
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":

                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere,produit=produit,importateur=importateur,entrepot=entrepot,dateheurecargaison__gte=date_d, dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)

                                        return render(request, 'stats.html', {'cargaison': table})

            if request.method == 'GET':

                frontiere = request.session['frontiere']
                produit = request.session['produit']
                importateur = request.session['importateur']
                entrepot = request.session['entrepot']
                date_d = request.session['date_d']
                date_f = request.session['date_f']

                # R1
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.order_by('-dateheurecargaison'),
                                                                  prefix="1_")
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))

                                        return render(request, 'stats.html', {
                                            'cargaison': table
                                        })

                # R2
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(dateheurecargaison__startswith=date_f),
                                            prefix='2_')
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R3
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(dateheurecargaison__startswith=date_d),
                                            prefix='3_')
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R4
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(dateheurecargaison__gte=date_d,
                                                                     dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R5
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R6
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(entrepot=entrepot,
                                                                                           dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R7
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(entrepot=entrepot,
                                                                                           dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R8
                if frontiere == "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(entrepot=entrepot, dateheurecargaison__gte=date_d,
                                                                     dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R9
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(importateur=importateur))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R10
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(importateur=importateur,
                                                                                           dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R11
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(importateur=importateur,
                                                                                           dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R12
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(importateur=importateur,
                                                                                           dateheurecargaison__gte=date_d,
                                                                                           dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R13
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(importateur=importateur, entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R14
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(importateur=importateur, entrepot=entrepot,
                                                                     dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R15
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(importateur=importateur, entrepot=entrepot,
                                                                     dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R16
                if frontiere == "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(importateur=importateur, entrepot=entrepot,
                                                                     dateheurecargaison__gte=date_d,
                                                                     dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R17
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R18
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit,
                                                                                           dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R19
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(produit=produit,
                                                                                           dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R20
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(produit=produit, dateheurecargaison__gte=date_d,
                                                                     dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R21
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(produit=produit, entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R22
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(produit=produit, entrepot=entrepot,
                                                                     dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R23
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(produit=produit, entrepot=entrepot,
                                                                     dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R24
                if frontiere == "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(produit=produit, entrepot=entrepot,
                                                                     dateheurecargaison__gte=date_d,
                                                                     dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R25
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(produit=produit, importateur=importateur))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R26
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(produit=produit, importateur=importateur,
                                                                     dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R26
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(produit=produit, importateur=importateur,
                                                                     dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 20}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R27
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(produit=produit, importateur=importateur,
                                                                     dateheurecargaison__gte=date_d,
                                                                     dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R28
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(produit=produit, importateur=importateur,
                                                                     entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R29
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(produit=produit, importateur=importateur,
                                                                     entrepot=entrepot,
                                                                     dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R30
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(produit=produit, importateur=importateur,
                                                                     entrepot=entrepot,
                                                                     dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R31
                if frontiere == "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(produit=produit, importateur=importateur,
                                                                     entrepot=entrepot, dateheurecargaison__gte=date_d,
                                                                     dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R32
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R32
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere,
                                                                                           dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R33
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere,
                                                                                           dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R34
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(Cargaison.objects.filter(frontiere=frontiere,
                                                                                           dateheurecargaison__gte=date_d,
                                                                                           dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R35
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R35
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, entrepot=entrepot,
                                                                     dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R36
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, entrepot=entrepot,
                                                                     dateheurecargaison__startwith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R37
                if frontiere != "":
                    if produit == "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, entrepot=entrepot,
                                                                     dateheurecargaison__gte=date_d,
                                                                     dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, importateur=importateur))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R40
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, importateur=importateur,
                                                                     dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R41
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, importateur=importateur,
                                                                     dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R42
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, importateur=importateur,
                                                                     dateheurecargaison__gte=date_d,
                                                                     dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R43
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, importateur=importateur,
                                                                     entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R44
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, importateur=importateur,
                                                                     entrepot=entrepot,
                                                                     dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R45
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, importateur=importateur,
                                                                     entrepot=entrepot,
                                                                     dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R46
                if frontiere != "":
                    if produit == "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, importateur=importateur,
                                                                     entrepot=entrepot, dateheurecargaison__gte=date_d,
                                                                     dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R47
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R48
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R49
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R50
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     dateheurecargaison__startswith=date_d))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R51
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     dateheurecargaison__startswith=date_d,
                                                                     dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R52
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     entrepot=entrepot))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R53
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     entrepot=entrepot,
                                                                     dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R54
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     entrepot=entrepot,
                                                                     dateheurecargaison__startswith=date_d))

                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R55
                if frontiere != "":
                    if produit != "":
                        if importateur == "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     entrepot=entrepot, dateheurecargaison__gte=date_d,
                                                                     dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R56
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     importateur=importateur))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R57
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     importateur=importateur,
                                                                     dateheurecargaison__startswith=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R58
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     importateur=importateur,
                                                                     dateheurecargaison__startswith=date_d))

                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R58
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot == "":
                                if date_d != "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     importateur=importateur,
                                                                     dateheurecargaison__gte=date_d,
                                                                     dateheurecargaison__lte=date_f))

                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R59
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     importateur=importateur, entrepot=entrepot))

                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R60
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d == "":
                                    if date_f != "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     importateur=importateur, entrepot=entrepot,
                                                                     dateheurecargaison__startswith=date_f))

                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})

                # R61
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f == "":
                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     importateur=importateur, entrepot=entrepot,
                                                                     dateheurecargaison__startswith=date_d))

                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)
                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {'cargaison': table})
                # R62
                if frontiere != "":
                    if produit != "":
                        if importateur != "":
                            if entrepot != "":
                                if date_d != "":
                                    if date_f != "":

                                        table = StatistiquesTable(
                                            Cargaison.objects.filter(frontiere=frontiere, produit=produit,
                                                                     importateur=importateur, entrepot=entrepot,
                                                                     dateheurecargaison__gte=date_d,
                                                                     dateheurecargaison__lte=date_f))
                                        RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                         "per_page": 15}).configure(table)

                                        export_format = request.GET.get('_export', None)
                                        if TableExport.is_valid_format(export_format):
                                            exporter = TableExport(export_format, table)
                                            return exporter.response('table.{}'.format(export_format))
                                        return render(request, 'stats.html', {
                                            'cargaison': table
                                        })

        else:
            return redirect('logout')

@login_required(login_url='login')
# Fonction gestion des entrepots
def gestionentrepot(request):
    user = request.user
    role = user.role_id

    if role == 1:
        template = 'entrepot/entrepotlist.html'
        table = EntrepotTable(Entrepot.objects.order_by('identrepot'))
        table.paginate(page=request.GET.get('page', 1), per_page=15)
        return render(request, template, {'entrepot': table})

    else:
        return redirect('logout')


@login_required(login_url='login')
# Fonction ajout entrepot
def addentrepot(request):
    user = request.user
    role = user.role_id

    if role == 1:
        template = 'entrepot/entrepot_form.html'
        if request.method == 'POST':
            form = EntrepotForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('gest_entrepot')
        else:
            form = EntrepotForm()
        return render(request, template, {'form': form})
    else:
        return redirect('logout')


@login_required(login_url='login')
# Fonction delete entrepot
def deleteentrepot(request, pk):
    user = request.user
    role = user.role_id

    if role == 1:
        obj = Entrepot.objects.get(identrepot=pk)
        obj.delete()
        return redirect('gest_entrepot')

    else:
        return redirect('logout')


@login_required(login_url='login')
# Fonction d'edition des entrepots
def editentrepot(request, pk):
    user = request.user
    role = user.role_id

    if role == 1:
        template = 'entrepot/editentrepot.html'
        instance = get_object_or_404(Entrepot, identrepot=pk)
        form = EntrepotEditForm(request.POST or None, instance=instance)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            return redirect('gest_entrepot')

        args = {'form': form}
        return render(request, template, args)
    else:
        return redirect('logout')


@login_required(login_url='login')
# Fonction pour la gestion des importateurs
def gestionimportateur(request):
    user = request.user
    role = user.role_id

    if role == 1:
        template = 'importateur/importateurlist.html'
        table = ImportateurTable(Importateur.objects.order_by('idimportateur'))
        RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 20}).configure(table)
        return render(request, template, {'importateur': table})

    else:
        return redirect('logout')


@login_required(login_url='login')
# Formulaire d'ajout d'importateur
def addimportateur(request):
    user = request.user
    role = user.role_id
    if role == 1:
        template = 'importateur/importateur_form.html'
        if request.method == 'POST':
            form = ImportateurForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('gest_importateur')
        else:
            form = ImportateurForm()
        return render(request, template, {'form': form})
    else:
        return redirect('logout')

@login_required(login_url='login')
# Formulaire pour effacer des importateurs
def deleteimportateur(request, pk):
    user = request.user
    role = user.role_id
    if role == 1:
        obj = Importateur.objects.get(idimportateur=pk)
        obj.delete()
        return redirect('gest_importateur')
    else:
        return redirect('logout')

@login_required(login_url='login')
# Formulaire d'edition Importateurs
def editimportateur(request, pk):
    user = request.user
    role = user.role_id

    if role == 1:
        template = 'importateur/importateuredit.html'
        instance = get_object_or_404(Importateur, idimportateur=pk)
        form = ImportateurEditForm(request.POST or None, instance=instance)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            return redirect('gest_importateur')

        args = {'form': form}
        return render(request, template, args)
    else:
        return redirect('logout')

@login_required(login_url='login')
# Formulaire de gestion de frontiere
def gestionfrontiere(request):
    user = request.user
    role = user.role_id

    if role == 1:
        template = 'frontiere/frontierelist.html'
        table = VilleTable(Ville.objects.order_by('idville'))
        table.paginate(page=request.GET.get('page', 1), per_page=15)
        return render(request, template, {'ville': table})
    else:
        return redirect('logout')


@login_required(login_url='login')
# Fonction ajout des frontieres
def addfrontiere(request):
    user = request.user
    role = user.role_id

    if role == 1:
        template = 'frontiere/frontiere_form.html'
        if request.method == 'POST':
            form = VilleForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('gest_frontiere')
        else:
            form = VilleForm()
        return render(request, template, {'form': form})
    else:
        return redirect('logout')

@login_required(login_url='login')
# Fonction delete frontiere
def delfrontiere(request, pk):
    user = request.user
    role = user.role_id

    if role == 1:
        obj = Ville.objects.get(idville=pk)
        obj.delete()
        return redirect('gest_frontiere')
    else:
        return redirect('logout')

@login_required(login_url='login')
# Fonction edit frontiere
def editfrontiere(request, pk):
    user = request.user
    role = user.role_id

    if role == 1:
        template = 'frontiere/frontiereedit.html'
        instance = get_object_or_404(Ville, idville=pk)
        form = ImportateurEditForm(request.POST or None, instance=instance)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            return redirect('gest_frontiere')
        args = {'form': form}
        return render(request, template, args)
    else:
        return redirect('logout')


@login_required(login_url='login')
# Fonction gestion produit
def gestionproduit(request):
    user = request.user
    role = user.role_id

    if role == 1:
        template = 'produit/produitlist.html'
        table = ProduitTable(Produit.objects.order_by('idproduit'))
        table.paginate(page=request.GET.get('page', 1), per_page=15)
        return render(request, template, {'produit': table})
    else:
        return redirect('logout')


@login_required(login_url='login')
# Fonction ajout produit
def addproduit(request):
    user = request.user
    role = user.role_id

    if role == 1:
        template = 'produit/produit_form.html'
        if request.method == 'POST':
            form = ProduitForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('gest_produit')
        else:
            form = ProduitForm()
        return render(request, template, {'form': form})
    else:
        return redirect('logout')


@login_required(login_url='login')
# Fonction edit produit
def editproduit(request, pk):
    user = request.user
    role = user.role_id

    if role == 1:
        template = 'produit/produitedit.html'
        instance = get_object_or_404(Produit, idproduit=pk)
        form = ProduitEditForm(request.POST or None, instance=instance)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            return redirect('gest_produit')
        args = {'form': form}
        return render(request, template, args)
    else:
        return redirect('logout')

@login_required(login_url='login')
# Fonction delete produit
def delproduit(request, pk):
    user = request.user
    role = user.role_id

    if role == 1:
        obj = Produit.objects.get(idproduit=pk)
        obj.delete()
        return redirect('gest_produit')
    else:
        return redirect('logout')


@login_required(login_url='login')
# Upload des données
def uploadcargaison(request):
    user = request.user
    role = user.role_id

    if role == 1:
        template = 'cargaisonupload.html'

        if request.method == 'POST':
            csv_file = request.FILES['file']
            data_set = csv_file.read().decode('UTF-8')
            lines = data_set.split("\n")

            for line in lines:
                fields = line.split(",")

                data_dict = {}

                data_dict["idcargaison"] = fields[0],
                data_dict["provenance"] = fields[1],
                data_dict["transporteur"] = fields[2],
                data_dict["declarant"] = fields[3],
                data_dict["poids"] = fields[4],
                data_dict["volume"] = fields[5],
                data_dict["tempcargaison"] = fields[6],
                data_dict["densitecargaison"] = fields[7],
                data_dict["t1d"] = fields[8],
                data_dict["t1e"] = fields[9],
                data_dict["idchauffeur"] = fields[10],
                data_dict["nationalite_id"] = fields[11],
                data_dict["nomchauffeur"] = fields[12],
                data_dict["immatriculation"] = fields[13],
                data_dict["dateheurecargaison"] = fields[14],
                data_dict["qrcode"] = fields[15],
                data_dict["etat"] = fields[16],
                data_dict["volume_decl15"] = fields[17],
                data_dict["numdossier"] = fields[18],
                data_dict["codecargaison"] = fields[19],
                data_dict["numact"] = fields[20],
                data_dict["conformite"] = fields[21],
                data_dict["impression"] = fields[22],
                data_dict["entrepot_id"] = fields[23],
                data_dict["frontiere_id"] = fields[24],
                data_dict["importateur_id"] = fields[25],
                data_dict["produit_id"] = fields[26],
                data_dict["voie_id"] = fields[27]

                p = Cargaison(idcargaison=fields[0], )

        return render(request, template)
    else:
        return redirect('logout')


@login_required(login_url='login')
def uploadimportateur(request):
    user = request.user
    role = user.role_id

    if role == 1:
        data = {}
        template = 'importateurlist.html'
        if request.method == 'get':
            return render(request, template, data)

        try:
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, "Le fichier n'est pas au format CSV")
                return HttpResponseRedirect(reverse("ads:gest_importateur"))

            file_data = csv_file.read().decode("UTF-8")

            lines = file_data.split("\n")

            for line in lines:
                fields = line.split(",")
                data_dict = {}
                data_dict["idimportateur"] = fields[0]
                data_dict["nomimportateur"] = fields[1]
                data_dict["adresseimportateur"] = fields[2]
                p = Importateur(idimportateur=fields[0], nomimportateur=fields[1], adresseimportateur=fields[2])
                p.save()
        except Exception as e:
            messages.error(request, "Impossible d'uploader ce fichier." + repr(e))

        return HttpResponseRedirect(reverse(("ads:gest_importateur")))
    else:
        return redirect('logout')


@login_required(login_url='login')
def uploadentrepot(request):
    user = request.user
    role = user.role_id

    if role == 1:
        template = 'entrepotupload.html'
        if request.method == 'get':
            csv_file = request.FILES['file']
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            next(io_string)

            for column in csv.reader(io_string, delimiter=',', quotechar='|'):
                _, created = Entrepot.objects.update_or_create(
                    identrepot=column[0],
                    nomentrepot=column[1],
                    adresseentrepot=column[2],
                    ville_id=[3]
                )
            return render(request, template)
        return render(request, template)
    else:
        return redirect('logout')


@login_required(login_url='login')
def uploadville(request):
    user = request.user
    role = user.role_id

    if role == 1:
        data = {}
        template = 'frontierelist.html'
        if request.method == 'get':
            return render(request, template, data)

        else:
            csv_file = request.FILES['csv_file']
            file_data = csv_file.read().decode("UTF-8")
            lines = file_data.split("\n")
            for line in lines:
                data_dict = {}
                data_dict["idville"] = fields[0]
                data_dict["nomville"] = fields[1]
                data_dict["province"] = fields[2]

                txt = line[0]
                integer = int(txt)

                p = Ville(idville=integer, nomville=line[2], province=line[2])
                p.save()
            return redirect('gest_frontiere')

        return redirect('gest_frontiere')
    else:
        return redirect('logout')


@login_required(login_url='login')
def uploadsydonia(request):
    user = request.user
    role = user.role_id

    if role == 1:
        template ='sydoniaupload.html'
        prompt = {'order': 'Attention a la disposition des colonnes'}

        if request.method == 'GET':
            return render(request, template, prompt)

        csv_file = request.FILES['file']

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Ceci n'est pas un fichier CSV")

        data_set = csv_file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        next(io_string)
        for column in csv.reader(io_string, delimiter=','):
            _, created = Paiement.objects.update_or_create(
                code_bur=column[0],
                bureau = column[1],
                modele = column[2],
                nif_importateur = column[3],
                importateur = column[4],
                nom_decl = column[5],
                n_liq = column[6],
                date_liq = column[7],
                ide_ser = column[8],
                ide_nbr = column[9],
                date_pay = column[10],
                tax_cod = column[11],
                mont_enc = column[12],
                bnk_nam = column[13],
                libelle = column[14],
                ref_pay = column[15],
                taux = column[16],
                qte_stat = column[17],
            )
        context = {}
        return render(request, template, context)
    else:
        return redirect('logout')


# Recherche des statistiques de production

def statproduction(request):
    template = 'statsprod.html'
    user = request.user
    role = user.role_id
    if role == 1 or role == 'st' or role == 7 or role == 8:
        if request.method == 'POST':
            frontiere = request.POST['frontiere']
            produit = request.POST['produit']
            importateur = request.POST['importateur']
            entrepot = request.POST['entrepot']
            date_d = request.POST['date_d']
            date_f = request.POST['date_f']

            frontiereqs = frontiere
            produitqs = produit
            importateurqs = importateur
            entrepotqs = entrepot
            date_dqs = date_d
            date_fqs = date_f

            request.session['frontiere'] = frontiereqs
            request.session['produit'] = produitqs
            request.session['importateur'] = importateurqs
            request.session['entrepot'] = entrepotqs
            request.session['date_d'] = date_d
            request.session['date_f'] = date_f

            # R1
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                        ORDER BY c.dateheurecargaison DESC'), prefix="1_")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)

                                    return render(request, 'stats.html', {
                                        'cargaison': table
                                    })

            # R2
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                            WHERE c.idcargaison = d.idcargaison_id \
                                                                                            AND c.dateheurecargaison = %s \
                                                                                            ORDER BY c.dateheurecargaison DESC',[date_f,]), prefix="1_")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)

                                    return render(request, 'stats.html', {
                                        'cargaison': table
                                    })

            # R3
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                               FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                               WHERE c.idcargaison = d.idcargaison_id \
                                                                                               AND c.dateheurecargaison = %s \
                                                                                               ORDER BY c.dateheurecargaison DESC',
                                                                                     [date_d, ]), prefix="1_")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)

                                    return render(request, 'stats.html', {
                                        'cargaison': table
                                    })

            # R4
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                               FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                               WHERE c.idcargaison = d.idcargaison_id \
                                                                                               AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                               ORDER BY c.dateheurecargaison DESC',
                                                                                     [date_d,date_f, ]), prefix="1_")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)

                                    return render(request, 'stats.html', {
                                        'cargaison': table
                                    })

            # R5
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                  FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                  WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                  AND c.entrepot_id = %s \
                                                                                                                                  ORDER BY c.dateheurecargaison DESC',[entrepot, ]), prefix="1_")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'statsprod.html', {'cargaison': table})

            # R6
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                  FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                  WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                  AND c.entrepot_id = %s \
                                                                                                                                  AND c.dateheurecargaison = %s \
                                                                                                                                  ORDER BY c.dateheurecargaison DESC',
                                                                                     [entrepot,date_f, ]), prefix="1_")


                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R7
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                      AND c.entrepot_id = %s \
                                                                                                                                                                      AND c.dateheurecargaison = %s \
                                                                                                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [entrepot, date_d, ]), prefix="1_")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R8
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                         FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                         WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                         AND c.entrepot_id = %s \
                                                                                                                                                                                                         AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                                                                                                                                         ORDER BY c.dateheurecargaison DESC',
                                                                                     [entrepot, date_d,date_f, ]), prefix="1_1")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R9
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                                                             FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                                                             WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                                                             AND c.importateur_id = %s \
                                                                                                                                                                                                                                             ORDER BY c.dateheurecargaison DESC',
                                                                                     [importateur, ]),
                                                            prefix="1_1")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R10
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                                                                                                FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                                                                                                WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                                                                                                AND c.importateur_id = %s \
                                                                                                                                                                                                                                                                                AND c.dateheurecargaison = %s \
                                                                                                                                                                                                                                                                                ORDER BY c.dateheurecargaison DESC',
                                                                                     [importateur, date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R11
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                                                                                                                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                                                                                                                                    WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                                                                                                                                    AND c.importateur_id = %s \
                                                                                                                                                                                                                                                                                                                    AND c.dateheurecargaison = %s \
                                                                                                                                                                                                                                                                                                                    ORDER BY c.dateheurecargaison DESC',
                                                                                     [importateur, date_d, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R12
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                                                                                                                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                                                                                                                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                                                                                                                                                                        AND c.importateur_id = %s \
                                                                                                                                                                                                                                                                                                                                                        AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                                                                                                                                                                                                                                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [importateur, date_d, date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R13
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                                                                                                                                                                                                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                                                                                                                                                                                                            WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                                                                                                                                                                                                            AND c.importateur_id = %s \
                                                                                                                                                                                                                                                                                                                                                                                            AND c.entrepot_id = %s \
                                                                                                                                                                                                                                                                                                                                                                                            ORDER BY c.dateheurecargaison DESC',
                                                                                     [importateur, entrepot, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R14
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
WHERE c.idcargaison = d.idcargaison_id \
AND c.importateur_id = %s \
AND c.entrepot_id = %s \
AND c.dateheurecargaison = %s \
ORDER BY c.dateheurecargaison DESC',[importateur, entrepot, date_f, ]), prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R15
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.importateur_id = %s \
                                    AND c.entrepot_id = %s \
                                    AND c.dateheurecargaison = %s \
                                    ORDER BY c.dateheurecargaison DESC', [importateur, entrepot, date_d, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R16
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.importateur_id = %s \
                                                                        AND c.entrepot_id = %s \
                                                                        AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [importateur, entrepot, date_d, date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R17
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                            WHERE c.idcargaison = d.idcargaison_id \
                                                                                                            AND c.produit_id = %s \
                                                                                                            ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R18
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                AND c.produit_id = %s \
                                                                                                                                                AND c.dateheurcargaison = %s \
                                                                                                                                                ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R19
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                    WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                    AND c.produit_id = %s \
                                                                                                                                                                                    AND c.dateheurcargaison = %s \
                                                                                                                                                                                    ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, date_d, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R20
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                            WHERE c.idcargaison = d.idcargaison_id \
                                                                                                            AND c.produit_id = %s \
                                                                                                            AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                                            ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, date_d, date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R21
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                AND c.produit_id = %s \
                                                                                                                                                AND c.entrepot_id = %s \
                                                                                                                                                ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, entrepot, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R22
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
WHERE c.idcargaison = d.idcargaison_id \
AND c.produit_id = %s \
AND c.entrepot_id = %s \
AND c.dateheurecargaison = %s \
ORDER BY c.dateheurecargaison DESC',
[produit, entrepot, date_f ]),
prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R23
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.produit_id = %s \
                                    AND c.entrepot_id = %s \
                                    AND c.dateheurecargaison = %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, entrepot, date_d]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R24
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.produit_id = %s \
                                    AND c.entrepot_id = %s \
                                    AND c.dateheurecargaison BETWEEN %s AND %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, entrepot, date_d, date_f]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R25
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.produit_id = %s \
                                    AND c.importateur_id = %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, importateur,]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R26
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.produit_id = %s \
                                                                        AND c.importateur_id = %s \
                                                                        AND c.dateheurecargaison = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, importateur, date_f ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R26
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.produit_id = %s \
                                    AND c.importateur_id = %s \
                                    AND c.dateheurecargaison = %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [produit, importateur, date_d]),
                                    prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 20}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R27
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.produit_id = %s \
                                    AND c.importateur_id = %s \
                                    AND c.dateheurecargaison BETWEEN %s AND %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [produit, importateur, date_d, date_f,]),
                                    prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R28
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.produit_id = %s \
                                    AND c.importateur_id = %s \
                                    AND c.entrepot_id = %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [produit, importateur, entrepot,]),
                                    prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R29
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.produit_id = %s \
                                                                        AND c.importateur_id = %s \
                                                                        AND c.entrepot_id = %s \
                                                                        AND c.dateheurcargaison = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, importateur,entrepot, date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R30
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.produit_id = %s \
                                    AND c.importateur_id = %s \
                                    AND c.entrepot_id = %s \
                                    AND c.dateheurcargaison BETWEEN %s AND %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [produit, importateur,entrepot, date_d, date_f, ]),
                                    prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R31
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.produit_id = %s \
                                    AND c.importateur_id = %s \
                                    AND c.entrepot_id = %s \
                                    AND c.dateheurcargaison BETWEEN %s AND %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [produit, importateur, entrepot, date_d, date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R32
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.frontiere_id = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R32
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.frontiere_id = %s \
                                    AND c.dateheurecargaison = %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [frontiere, date_f, ]),
                                    prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R33
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.frontiere_id = %s \
                                    AND c.dateheurecargaison = %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [frontiere, date_d, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R34
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.frontiere_id = %s \
                                    AND c.dateheurecargaison BETWEEN %s AND %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [frontiere, date_d, date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R35
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.frontiere_id = %s \
                                                                        AND c.entrepot_id = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, entrepot, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R35
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.frontiere_id = %s \
                                    AND c.entrepot_id = %s \
                                    AND c.dateheurecargaison_id = %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [frontiere, entrepot, date_f ]),
                                    prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R36
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.frontiere_id = %s \
                                                                        AND c.entrepot_id = %s \
                                                                        AND c.dateheurecargaison_id = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, entrepot, date_d]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R37
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.frontiere_id = %s \
                                    AND c.entrepot_id = %s \
                                    AND c.dateheurecargaison BETWEEN %s AND %S \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [frontiere, entrepot, date_d, date_f]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.frontiere_id = %s \
                                                                        AND c.importateur_id = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, importateur, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R40
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.frontiere_id = %s \
                                    AND c.importateur_id = %s \
                                    AND c.dateheurecargaison = %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [frontiere, importateur, date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R41
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.frontiere_id = %s \
                                                                        AND c.importateur_id = %s \
                                                                        AND c.dateheurecargaison = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, importateur,
                                                                                      date_d, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R42
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                     FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                     WHERE c.idcargaison = d.idcargaison_id \
                                                                                     AND c.frontiere_id = %s \
                                                                                     AND c.importateur_id = %s \
                                                                                     AND c.dateheurecargaison BETWEEN %s AND %s\
                                                                                     ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, importateur,
                                                                                      date_d, date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R43
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                          WHERE c.idcargaison = d.idcargaison_id \
                                          AND c.frontiere_id = %s \
                                          AND c.importateur_id = %s \
                                          AND c.entrepot_id = %s\
                                          ORDER BY c.dateheurecargaison DESC',
                                          [frontiere, importateur, entrepot, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R44
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                              FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                              WHERE c.idcargaison = d.idcargaison_id \
                                                                              AND c.frontiere_id = %s \
                                                                              AND c.importateur_id = %s \
                                                                              AND c.entrepot_id = %s\
                                                                              AND c.dateheurecargaison = %s \
                                                                              ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, importateur, entrepot, date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R45
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                          WHERE c.idcargaison = d.idcargaison_id \
                                          AND c.frontiere_id = %s \
                                          AND c.importateur_id = %s \
                                          AND c.entrepot_id = %s\
                                          AND c.dateheurecargaison = %s \
                                          ORDER BY c.dateheurecargaison DESC',
                                          [frontiere, importateur, entrepot, date_d, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R46
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                              FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                              WHERE c.idcargaison = d.idcargaison_id \
                                                                              AND c.frontiere_id = %s \
                                                                              AND c.importateur_id = %s \
                                                                              AND c.entrepot_id = %s\
                                                                              AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                              ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, importateur, entrepot,
                                                                                      date_d, date_f ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R47
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                  FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                  WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                  AND c.frontiere_id = %s \
                                                                                                                  AND c.produit_id = %s \
                                                                                                                  ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R48
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.dateheurecargaison = %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, date_f]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})


            # R49
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.dateheurecargaison = %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, date_d]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R51
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, date_d, date_f,]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R52
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.entrepot_id = %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, entrepot,]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R53
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                          WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                          AND c.frontiere_id = %s \
                                                                                                                          AND c.produit_id = %s \
                                                                                                                          AND c.entrepot_id = %s \
                                                                                                                          AND c.dateheurecargaison = %s \
                                                                                                                          ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, entrepot, date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R54
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                          WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                          AND c.frontiere_id = %s \
                                                                                                                          AND c.produit_id = %s \
                                                                                                                          AND c.entrepot_id = %s \
                                                                                                                          AND c.dateheurecargaison = %s \
                                                                                                                          ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, entrepot, date_d, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R55
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                          WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                          AND c.frontiere_id = %s \
                                                                                                                          AND c.produit_id = %s \
                                                                                                                          AND c.entrepot_id = %s \
                                                                                                                          AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                                                          ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, entrepot, date_d, date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R56
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.importateur_id = %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, importateur, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R57
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.importateur_id = %s \
                                                                                      AND c.dateheurecargaison = %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, date_f ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R58
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.importateur_id = %s \
                                                                                      AND c.dateheurecargaison = %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, date_d]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R58
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.importateur_id = %s \
                                                                                      AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, date_d, date_f,]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R59
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.importateur_id = %s \
                                                                                      AND c.entrepot_id = %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, entrepot, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R60
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.importateur_id = %s \
                                                                                      AND c.entrepot_id = %s \
                                                                                      AND c.dateheurecargaison = %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, entrepot, date_f ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})

            # R61
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                          WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                          AND c.frontiere_id = %s \
                                                                                                                          AND c.produit_id = %s \
                                                                                                                          AND c.importateur_id = %s \
                                                                                                                          AND c.entrepot_id = %s \
                                                                                                                          AND c.dateheurecargaison = %s \
                                                                                                                          ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, entrepot, date_d]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    return render(request, 'stats.html', {'cargaison': table})
            # R62
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                          WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                          AND c.frontiere_id = %s \
                                                                                                                          AND c.produit_id = %s \
                                                                                                                          AND c.importateur_id = %s \
                                                                                                                          AND c.entrepot_id = %s \
                                                                                                                          AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                                                          ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, entrepot, date_d, date_f]),
                                                            prefix="1_2")


                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)

                                    return render(request, 'stats.html', {'cargaison': table})

        if request.method == 'GET':

            frontiere = request.session['frontiere']
            produit = request.session['produit']
            importateur = request.session['importateur']
            entrepot = request.session['entrepot']
            date_d = request.session['date_d']
            date_f = request.session['date_f']

            # R1
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                            WHERE c.idcargaison = d.idcargaison_id \
                                                                                            ORDER BY c.dateheurecargaison DESC'),
                                                             prefix="1_")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))

                                    return render(request, 'stats.html', {
                                        'cargaison': table
                                    })

            # R2
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                AND c.dateheurecargaison = %s \
                                                                                                                                ORDER BY c.dateheurecargaison DESC',
                                                                                     [date_f, ]), prefix="1_")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R3
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                   FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                   WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                   AND c.dateheurecargaison = %s \
                                                                                                                                   ORDER BY c.dateheurecargaison DESC',
                                                                                     [date_d, ]), prefix="1_")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R4
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                   FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                   WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                   AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                                                                   ORDER BY c.dateheurecargaison DESC',
                                                                                     [date_d, date_f, ]), prefix="1_")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R5
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                      AND c.entrepot_id = %s \
                                                                                                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [entrepot, ]), prefix="1_")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R6
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                      AND c.entrepot_id = %s \
                                                                                                                                                                      AND c.dateheurecargaison = %s \
                                                                                                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [entrepot, date_f, ]), prefix="1_")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R7
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                         FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                         WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                         AND c.entrepot_id = %s \
                                                                                                                                                                                                         AND c.dateheurecargaison = %s \
                                                                                                                                                                                                         ORDER BY c.dateheurecargaison DESC',
                                                                                     [entrepot, date_d, ]), prefix="1_")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R8
            if frontiere == "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                                                             FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                                                             WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                                                             AND c.entrepot_id = %s \
                                                                                                                                                                                                                                             AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                                                                                                                                                                             ORDER BY c.dateheurecargaison DESC',
                                                                                     [entrepot, date_d, date_f, ]),
                                                            prefix="1_1")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R9
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                                                                                                 FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                                                                                                 WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                                                                                                 AND c.importateur_id = %s \
                                                                                                                                                                                                                                                                                 ORDER BY c.dateheurecargaison DESC',
                                                                                     [importateur, ]),
                                                            prefix="1_1")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R10
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                                                                                                                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                                                                                                                                    WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                                                                                                                                    AND c.importateur_id = %s \
                                                                                                                                                                                                                                                                                                                    AND c.dateheurecargaison = %s \
                                                                                                                                                                                                                                                                                                                    ORDER BY c.dateheurecargaison DESC',
                                                                                     [importateur, date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R11
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                                                                                                                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                                                                                                                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                                                                                                                                                                        AND c.importateur_id = %s \
                                                                                                                                                                                                                                                                                                                                                        AND c.dateheurecargaison = %s \
                                                                                                                                                                                                                                                                                                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [importateur, date_d, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R12
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                                                                                                                                                                                                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                                                                                                                                                                                                            WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                                                                                                                                                                                                            AND c.importateur_id = %s \
                                                                                                                                                                                                                                                                                                                                                                                            AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                                                                                                                                                                                                                                                                                                                            ORDER BY c.dateheurecargaison DESC',
                                                                                     [importateur, date_d, date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R13
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                                                                                                                                                                                                                                                FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                                                                                                                                                                                                                                                WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                                                                                                                                                                                                                                                AND c.importateur_id = %s \
                                                                                                                                                                                                                                                                                                                                                                                                                                AND c.entrepot_id = %s \
                                                                                                                                                                                                                                                                                                                                                                                                                                ORDER BY c.dateheurecargaison DESC',
                                                                                     [importateur, entrepot, ]),
                                                            prefix="1_2")
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R14
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.importateur_id = %s \
                                    AND c.entrepot_id = %s \
                                    AND c.dateheurecargaison = %s \
                                    ORDER BY c.dateheurecargaison DESC', [importateur, entrepot, date_f, ]), prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R15
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.importateur_id = %s \
                                                                        AND c.entrepot_id = %s \
                                                                        AND c.dateheurecargaison = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [importateur, entrepot, date_d, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R16
            if frontiere == "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                            WHERE c.idcargaison = d.idcargaison_id \
                                                                                                            AND c.importateur_id = %s \
                                                                                                            AND c.entrepot_id = %s \
                                                                                                            AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                                            ORDER BY c.dateheurecargaison DESC',
                                                                                     [importateur, entrepot, date_d,
                                                                                      date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R17
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                AND c.produit_id = %s \
                                                                                                                                                ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R18
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                    WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                    AND c.produit_id = %s \
                                                                                                                                                                                    AND c.dateheurcargaison = %s \
                                                                                                                                                                                    ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R19
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                                                        AND c.produit_id = %s \
                                                                                                                                                                                                                        AND c.dateheurcargaison = %s \
                                                                                                                                                                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, date_d, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R20
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                AND c.produit_id = %s \
                                                                                                                                                AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                                                                                ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, date_d, date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R21
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                                                    WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                                                    AND c.produit_id = %s \
                                                                                                                                                                                    AND c.entrepot_id = %s \
                                                                                                                                                                                    ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, entrepot, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R22
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.produit_id = %s \
                                    AND c.entrepot_id = %s \
                                    AND c.dateheurecargaison = %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, entrepot, date_f]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R23
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.produit_id = %s \
                                    AND c.entrepot_id = %s \
                                    AND c.dateheurecargaison = %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, entrepot, date_d]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R24
            if frontiere == "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.produit_id = %s \
                                    AND c.entrepot_id = %s \
                                    AND c.dateheurecargaison BETWEEN %s AND %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, entrepot, date_d, date_f]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R25
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.produit_id = %s \
                                                                        AND c.importateur_id = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, importateur, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R26
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                            WHERE c.idcargaison = d.idcargaison_id \
                                                                                                            AND c.produit_id = %s \
                                                                                                            AND c.importateur_id = %s \
                                                                                                            AND c.dateheurecargaison = %s \
                                                                                                            ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, importateur, date_f]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R26
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.produit_id = %s \
                                    AND c.importateur_id = %s \
                                    AND c.dateheurecargaison = %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [produit, importateur, date_d]),
                                    prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 20}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R27
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.produit_id = %s \
                                    AND c.importateur_id = %s \
                                    AND c.dateheurecargaison BETWEEN %s AND %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [produit, importateur, date_d, date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R28
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.produit_id = %s \
                                                                        AND c.importateur_id = %s \
                                                                        AND c.entrepot_id = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, importateur,
                                                                                      entrepot, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R29
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.produit_id = %s \
                                                                        AND c.importateur_id = %s \
                                                                        AND c.entrepot_id = %s \
                                                                        AND c.dateheurcargaison = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, importateur,entrepot, date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R30
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.produit_id = %s \
                                                                        AND c.importateur_id = %s \
                                                                        AND c.entrepot_id = %s \
                                                                        AND c.dateheurcargaison BETWEEN %s AND %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, importateur, entrepot,
                                                                                      date_d, date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R31
            if frontiere == "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.produit_id = %s \
                                                                        AND c.importateur_id = %s \
                                                                        AND c.entrepot_id = %s \
                                                                        AND c.dateheurcargaison BETWEEN %s AND %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [produit, importateur, entrepot,
                                                                                      date_d, date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R32
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                            WHERE c.idcargaison = d.idcargaison_id \
                                                                                                            AND c.frontiere_id = %s \
                                                                                                            ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R32
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.frontiere_id = %s \
                                                                        AND c.dateheurecargaison = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R33
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.frontiere_id = %s \
                                                                        AND c.dateheurecargaison = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, date_d, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R34
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.frontiere_id = %s \
                                                                        AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, date_d, date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R35
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                            WHERE c.idcargaison = d.idcargaison_id \
                                                                                                            AND c.frontiere_id = %s \
                                                                                                            AND c.entrepot_id = %s \
                                                                                                            ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, entrepot, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R35
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.frontiere_id = %s \
                                                                        AND c.entrepot_id = %s \
                                                                        AND c.dateheurecargaison_id = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, entrepot, date_f]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R36
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                            WHERE c.idcargaison = d.idcargaison_id \
                                                                                                            AND c.frontiere_id = %s \
                                                                                                            AND c.entrepot_id = %s \
                                                                                                            AND c.dateheurecargaison_id = %s \
                                                                                                            ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, entrepot, date_d]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R37
            if frontiere != "":
                if produit == "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.frontiere_id = %s \
                                                                        AND c.entrepot_id = %s \
                                                                        AND c.dateheurecargaison BETWEEN %s AND %S \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, entrepot, date_d,
                                                                                      date_f]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                            WHERE c.idcargaison = d.idcargaison_id \
                                                                                                            AND c.frontiere_id = %s \
                                                                                                            AND c.importateur_id = %s \
                                                                                                            ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, importateur, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R40
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                        WHERE c.idcargaison = d.idcargaison_id \
                                                                        AND c.frontiere_id = %s \
                                                                        AND c.importateur_id = %s \
                                                                        AND c.dateheurecargaison = %s \
                                                                        ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, importateur,
                                                                                      date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R41
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                            WHERE c.idcargaison = d.idcargaison_id \
                                                                                                            AND c.frontiere_id = %s \
                                                                                                            AND c.importateur_id = %s \
                                                                                                            AND c.dateheurecargaison = %s \
                                                                                                            ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, importateur,
                                                                                      date_d, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R42
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.frontiere_id = %s \
                                    AND c.importateur_id = %s \
                                    AND c.dateheurecargaison BETWEEN %s AND %s\
                                    ORDER BY c.dateheurecargaison DESC',
                                    [frontiere, importateur, date_d, date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R43
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                              FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                              WHERE c.idcargaison = d.idcargaison_id \
                                                                              AND c.frontiere_id = %s \
                                                                              AND c.importateur_id = %s \
                                                                              AND c.entrepot_id = %s\
                                                                              ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, importateur,
                                                                                      entrepot, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R44
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                  FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                  WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                  AND c.frontiere_id = %s \
                                                                                                                  AND c.importateur_id = %s \
                                                                                                                  AND c.entrepot_id = %s\
                                                                                                                  AND c.dateheurecargaison = %s \
                                                                                                                  ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, importateur, entrepot,
                                                                                      date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R45
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                              FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                              WHERE c.idcargaison = d.idcargaison_id \
                                                                              AND c.frontiere_id = %s \
                                                                              AND c.importateur_id = %s \
                                                                              AND c.entrepot_id = %s\
                                                                              AND c.dateheurecargaison = %s \
                                                                              ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, importateur, entrepot,
                                                                                      date_d, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R46
            if frontiere != "":
                if produit == "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                  FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                  WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                  AND c.frontiere_id = %s \
                                                                                                                  AND c.importateur_id = %s \
                                                                                                                  AND c.entrepot_id = %s\
                                                                                                                  AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                                                  ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, importateur, entrepot,
                                                                                      date_d, date_f]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R47
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                                                      AND c.frontiere_id = %s \
                                                                                                                                                      AND c.produit_id = %s \
                                                                                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R48
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.frontiere_id = %s \
                                    AND c.produit_id = %s \
                                    AND c.dateheurecargaison = %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [frontiere, produit, date_f]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R49
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.dateheurecargaison = %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, date_d]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R51
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, date_d, date_f,]),
                                                            prefix="1_2")


                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R52
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                          WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                          AND c.frontiere_id = %s \
                                                                                                                          AND c.produit_id = %s \
                                                                                                                          AND c.entrepot_id = %s \
                                                                                                                          ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, entrepot, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R53
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                          WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                          AND c.frontiere_id = %s \
                                                                                                                          AND c.produit_id = %s \
                                                                                                                          AND c.entrepot_id = %s \
                                                                                                                          AND c.dateheurecargaison = %s \
                                                                                                                          ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, entrepot, date_f, ]),
                                                            prefix="1_2")
                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R54
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                          WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                          AND c.frontiere_id = %s \
                                                                                                                          AND c.produit_id = %s \
                                                                                                                          AND c.entrepot_id = %s \
                                                                                                                          AND c.dateheurecargaison = %s \
                                                                                                                          ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit, entrepot, date_d, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R55
            if frontiere != "":
                if produit != "":
                    if importateur == "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.frontiere_id = %s \
                                    AND c.produit_id = %s \
                                    AND c.entrepot_id = %s \
                                    AND c.dateheurecargaison BETWEEN %s AND %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                    [frontiere, produit, entrepot, date_d, date_f, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R56
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                          WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                          AND c.frontiere_id = %s \
                                                                                                                          AND c.produit_id = %s \
                                                                                                                          AND c.importateur_id = %s \
                                                                                                                          ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R57
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.importateur_id = %s \
                                                                                      AND c.dateheurecargaison = %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, date_f ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R58
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.importateur_id = %s \
                                                                                      AND c.dateheurecargaison = %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, date_d]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R58
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot == "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                          WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                          AND c.frontiere_id = %s \
                                                                                                                          AND c.produit_id = %s \
                                                                                                                          AND c.importateur_id = %s \
                                                                                                                          AND c.dateheurecargaison BETWEEN %s AND %s \
                                                                                                                          ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, date_d, date_f, ]),
                                                            prefix="1_2")


                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R59
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                      FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                      WHERE c.idcargaison = d.idcargaison_id \
                                                                                      AND c.frontiere_id = %s \
                                                                                      AND c.produit_id = %s \
                                                                                      AND c.importateur_id = %s \
                                                                                      AND c.entrepot_id = %s \
                                                                                      ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, entrepot, ]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R60
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d == "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                          WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                          AND c.frontiere_id = %s \
                                                                                                                          AND c.produit_id = %s \
                                                                                                                          AND c.importateur_id = %s \
                                                                                                                          AND c.entrepot_id = %s \
                                                                                                                          AND c.dateheurecargaison = %s \
                                                                                                                          ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, entrepot, date_f]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})

            # R61
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f == "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                                                                                                          FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                                                                                                          WHERE c.idcargaison = d.idcargaison_id \
                                                                                                                          AND c.frontiere_id = %s \
                                                                                                                          AND c.produit_id = %s \
                                                                                                                          AND c.importateur_id = %s \
                                                                                                                          AND c.entrepot_id = %s \
                                                                                                                          AND c.dateheurecargaison = %s \
                                                                                                                          ORDER BY c.dateheurecargaison DESC',
                                                                                     [frontiere, produit,
                                                                                      importateur, entrepot, date_f]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)
                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {'cargaison': table})
            # R62
            if frontiere != "":
                if produit != "":
                    if importateur != "":
                        if entrepot != "":
                            if date_d != "":
                                if date_f != "":
                                    table = ProductionTable(Dechargement.objects.raw('SELECT d.idcargaison_id, c.importateur_id, c.declarant, c.immatriculation, c.produit_id, c.volume, d.gov, d.gsv, \
                                    IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*6, d.gsv*5) AS cgwprod, \
		                            IF(DATE(c.dateheurecargaison) < "2020-05-16", d.gsv*5, d.gsv*6) AS occprod \
                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d \
                                    WHERE c.idcargaison = d.idcargaison_id \
                                    AND c.frontiere_id = %s \
                                    AND c.produit_id = %s \
                                    AND c.importateur_id = %s \
                                    AND c.entrepot_id = %s \
                                    AND c.dateheurecargaison BETWEEN %s AND %s \
                                    ORDER BY c.dateheurecargaison DESC',
                                       [frontiere, produit,importateur, entrepot, date_d, date_f]),
                                                            prefix="1_2")

                                    RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                     "per_page": 15}).configure(table)

                                    export_format = request.GET.get('_export', None)
                                    if TableExport.is_valid_format(export_format):
                                        exporter = TableExport(export_format, table)
                                        return exporter.response('table.{}'.format(export_format))
                                    return render(request, 'stats.html', {
                                        'cargaison': table
                                    })

        else:
            return redirect('logout')


#Stats encaissement
def statencaissement(request):
    template = 'statsprod.html'
    user = request.user
    role = user.role_id
    if role == 1 or role == 'st' or role == 7 or role == 8:
        if request.method == 'POST':
            frontiere = request.POST['frontiere']
            importateur = request.POST['importateur']
            banque = request.POST['banque']
            date_d = request.POST['date_d']
            date_f = request.POST['date_f']

            request.session['frontiere'] = frontiere
            request.session['importateur'] = importateur
            request.session['banque'] = banque
            request.session['date_d'] = date_d
            request.session['date_f'] = date_f

#R1
            if frontiere == '':
                if importateur == '':
                    if banque == '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
WHERE c.idcargaison = l.idcargaison_id \
AND p.code_bur = b.codebureau \
AND b.idbureau = l.codebureau_id \
AND l.numerobl = p.n_liq \
AND l.datebl = p.date_liq \
AND c.importateur_id = i.idimportateur'), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

#R2
            if frontiere == '':
                if importateur == '':
                    if banque == '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
            WHERE c.idcargaison = l.idcargaison_id \
            AND p.code_bur = b.codebureau \
            AND b.idbureau = l.codebureau_id \
            AND l.numerobl = p.n_liq \
            AND l.datebl = p.date_liq \
            AND c.importateur_id = i.idimportateur \
            AND l.datebl = %s',[date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

# R3
            if frontiere == '':
                if importateur == '':
                    if banque == '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND l.datebl = %s', [date_d, ]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

# R4
            if frontiere == '':
                if importateur == '':
                    if banque == '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND l.datebl BETWEEN %s AND %s', [date_d,date_f, ]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

# R5
            if frontiere == '':
                if importateur == '':
                    if banque != '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND p.bank_nam = %s ', [banque, ]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

# R6
            if frontiere == '':
                if importateur == '':
                    if banque != '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND p.bank_nam = %s \
                        AND l.datebl = %s', [banque,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

# R7
            if frontiere == '':
                if importateur == '':
                    if banque != '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND p.bank_nam = %s \
                        AND l.datebl = %s', [banque,date_d,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})


    # R8
            if frontiere == '':
                if importateur == '':
                    if banque != '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND p.bank_nam = %s \
                        AND l.datebl BETWEEN %s AND %s', [banque,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})


    # R9
            if frontiere == '':
                if importateur != '':
                    if banque == '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s', [importateur,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R10
            if frontiere == '':
                if importateur != '':
                    if banque == '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND l.datebl = %s', [importateur,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})


    # R11
            if frontiere == '':
                if importateur != '':
                    if banque == '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND l.datebl = %s', [importateur,date_d,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})


    # R12
            if frontiere == '':
                if importateur != '':
                    if banque == '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND l.datebl BETWEEN %s AND %s', [importateur,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R13
            if frontiere == '':
                if importateur != '':
                    if banque != '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s', [importateur,banque,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})


    # R14
            if frontiere == '':
                if importateur != '':
                    if banque != '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl = %s', [importateur,banque,date_f]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R15
            if frontiere == '':
                if importateur != '':
                    if banque != '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl = %s', [importateur,banque,date_d]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R16
            if frontiere == '':
                if importateur != '':
                    if banque != '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl BETWEEN %s and %s', [importateur,banque,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R17
            if frontiere != '':
                if importateur == '':
                    if banque == '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s', [frontiere,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})


    # R18
            if frontiere != '':
                if importateur == '':
                    if banque == '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND l.datebl = %s', [frontiere,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R19
            if frontiere != '':
                if importateur == '':
                    if banque == '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND l.datebl = %s', [frontiere,date_d,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R20
            if frontiere != '':
                if importateur == '':
                    if banque == '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND l.datebl BETWEEN %s and %s', [frontiere,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})


    # R21
            if frontiere != '':
                if importateur == '':
                    if banque != '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND p.bnk_nam = %s', [frontiere,banque,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R22
            if frontiere != '':
                if importateur == '':
                    if banque != '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl = %s', [frontiere,banque,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R23
            if frontiere != '':
                if importateur == '':
                    if banque != '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl = %s', [frontiere,banque,date_d,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R24
            if frontiere != '':
                if importateur == '':
                    if banque != '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl BETWEEN %s AND %s', [frontiere,banque,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R25
            if frontiere != '':
                if importateur != '':
                    if banque == '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s', [frontiere,importateur,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R26
            if frontiere != '':
                if importateur != '':
                    if banque == '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s \
                        AND l.datebl=%s', [frontiere,importateur,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R27
            if frontiere != '':
                if importateur != '':
                    if banque == '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s \
                        AND l.datebl=%s', [frontiere,importateur,date_d,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})


    # R28
            if frontiere != '':
                if importateur != '':
                    if banque == '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s \
                        AND l.datebl BETWEEN %s AND %s', [frontiere,importateur,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R29
            if frontiere != '':
                if importateur != '':
                    if banque != '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s', [frontiere,importateur,banque,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})


    # R30
            if frontiere != '':
                if importateur != '':
                    if banque != '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl = %s', [frontiere,importateur,banque,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R31
            if frontiere != '':
                if importateur != '':
                    if banque != '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl = %s', [frontiere,importateur,banque,date_d,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

    # R32
            if frontiere != '':
                if importateur != '':
                    if banque != '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl BETWEEN %s AND %s', [frontiere,importateur,banque,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)
                                return render(request, 'stats.html', {'cargaison': table})

        if request.method == 'GET':

            frontiere =  request.session['frontiere']
            importateur =  request.session['importateur']
            banque = request.session['banque']
            date_d = request.session['date_d']
            date_f = request.session['date_f']
            if frontiere == '':
                if importateur == '':
                    if banque == '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
            WHERE c.idcargaison = l.idcargaison_id \
            AND p.code_bur = b.codebureau \
            AND b.idbureau = l.codebureau_id \
            AND l.numerobl = p.n_liq \
            AND l.datebl = p.date_liq \
            AND c.importateur_id = i.idimportateur'), prefix="1_2")
                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

                    # R2
            if frontiere == '':
                if importateur == '':
                    if banque == '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                    WHERE c.idcargaison = l.idcargaison_id \
                    AND p.code_bur = b.codebureau \
                    AND b.idbureau = l.codebureau_id \
                    AND l.numerobl = p.n_liq \
                    AND l.datebl = p.date_liq \
                    AND c.importateur_id = i.idimportateur \
                    AND l.datebl = %s', [date_f, ]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

                # R3
            if frontiere == '':
                if importateur == '':
                    if banque == '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                            WHERE c.idcargaison = l.idcargaison_id \
                            AND p.code_bur = b.codebureau \
                            AND b.idbureau = l.codebureau_id \
                            AND l.numerobl = p.n_liq \
                            AND l.datebl = p.date_liq \
                            AND c.importateur_id = i.idimportateur \
                            AND l.datebl = %s', [date_d, ]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

                # R4
            if frontiere == '':
                if importateur == '':
                    if banque == '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                            FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                            WHERE c.idcargaison = l.idcargaison_id \
                            AND p.code_bur = b.codebureau \
                            AND b.idbureau = l.codebureau_id \
                            AND l.numerobl = p.n_liq \
                            AND l.datebl = p.date_liq \
                            AND c.importateur_id = i.idimportateur \
                            AND l.datebl BETWEEN %s AND %s', [date_d, date_f, ]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

                    # R5
            if frontiere == '':
                if importateur == '':
                    if banque != '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                                FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                                WHERE c.idcargaison = l.idcargaison_id \
                                AND p.code_bur = b.codebureau \
                                AND b.idbureau = l.codebureau_id \
                                AND l.numerobl = p.n_liq \
                                AND l.datebl = p.date_liq \
                                AND c.importateur_id = i.idimportateur \
                                AND p.bank_nam = %s ', [banque, ]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

    # R6
            if frontiere == '':
                if importateur == '':
                    if banque != '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                                                    WHERE c.idcargaison = l.idcargaison_id \
                                                    AND p.code_bur = b.codebureau \
                                                    AND b.idbureau = l.codebureau_id \
                                                    AND l.numerobl = p.n_liq \
                                                    AND l.datebl = p.date_liq \
                                                    AND c.importateur_id = i.idimportateur \
                                                    AND p.bank_nam = %s \
                                                    AND l.datebl = %s', [banque, date_f, ]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

    # R7
            if frontiere == '':
                if importateur == '':
                    if banque != '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND p.bank_nam = %s \
                        AND l.datebl = %s', [banque,date_d,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })



    # R8
            if frontiere == '':
                if importateur == '':
                    if banque != '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND p.bank_nam = %s \
                        AND l.datebl BETWEEN %s AND %s', [banque,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })


    # R9
            if frontiere == '':
                if importateur != '':
                    if banque == '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s', [importateur,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })



    # R10
            if frontiere == '':
                if importateur != '':
                    if banque == '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND l.datebl = %s', [importateur,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })



    # R11
            if frontiere == '':
                if importateur != '':
                    if banque == '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND l.datebl = %s', [importateur,date_d,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })


    # R12
            if frontiere == '':
                if importateur != '':
                    if banque == '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND l.datebl BETWEEN %s AND %s', [importateur,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

    # R13
            if frontiere == '':
                if importateur != '':
                    if banque != '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s', [importateur,banque,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

    # R14
            if frontiere == '':
                if importateur != '':
                    if banque != '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl = %s', [importateur,banque,date_f]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })



    # R15
            if frontiere == '':
                if importateur != '':
                    if banque != '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl = %s', [importateur,banque,date_d]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })



    # R16
            if frontiere == '':
                if importateur != '':
                    if banque != '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl BETWEEN %s and %s', [importateur,banque,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

    # R17
            if frontiere != '':
                if importateur == '':
                    if banque == '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s', [frontiere,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })


    # R18
            if frontiere != '':
                if importateur == '':
                    if banque == '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND l.datebl = %s', [frontiere,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })


    # R19
            if frontiere != '':
                if importateur == '':
                    if banque == '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND l.datebl = %s', [frontiere,date_d,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })


    # R20
            if frontiere != '':
                if importateur == '':
                    if banque == '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND l.datebl BETWEEN %s and %s', [frontiere,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })


    # R21
            if frontiere != '':
                if importateur == '':
                    if banque != '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND p.bnk_nam = %s', [frontiere,banque,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })


    # R22
            if frontiere != '':
                if importateur == '':
                    if banque != '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl = %s', [frontiere,banque,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })


    # R23
            if frontiere != '':
                if importateur == '':
                    if banque != '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl = %s', [frontiere,banque,date_d,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })


    # R24
            if frontiere != '':
                if importateur == '':
                    if banque != '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl BETWEEN %s AND %s', [frontiere,banque,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })


    # R25
            if frontiere != '':
                if importateur != '':
                    if banque == '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s', [frontiere,importateur,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })


    # R26
            if frontiere != '':
                if importateur != '':
                    if banque == '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s \
                        AND l.datebl=%s', [frontiere,importateur,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

    # R27
            if frontiere != '':
                if importateur != '':
                    if banque == '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s \
                        AND l.datebl=%s', [frontiere,importateur,date_d,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

    # R28
            if frontiere != '':
                if importateur != '':
                    if banque == '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s \
                        AND l.datebl BETWEEN %s AND %s', [frontiere,importateur,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

                                return render(request, 'stats.html', {'cargaison': table})


    # R29
            if frontiere != '':
                if importateur != '':
                    if banque != '':
                        if date_d == '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                                                    WHERE c.idcargaison = l.idcargaison_id \
                                                    AND p.code_bur = b.codebureau \
                                                    AND b.idbureau = l.codebureau_id \
                                                    AND l.numerobl = p.n_liq \
                                                    AND l.datebl = p.date_liq \
                                                    AND c.importateur_id = i.idimportateur \
                                                    AND c.frontiere_id = %s \
                                                    AND c.importateur_id = %s \
                                                    AND p.bnk_nam = %s', [frontiere, importateur, banque, ]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

                                return render(request, 'stats.html', {'cargaison': table})

    # R30
            if frontiere != '':
                if importateur != '':
                    if banque != '':
                        if date_d == '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl = %s', [frontiere,importateur,banque,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

                                return render(request, 'stats.html', {'cargaison': table})


    # R31
            if frontiere != '':
                if importateur != '':
                    if banque != '':
                        if date_d != '':
                            if date_f == '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl = %s', [frontiere,importateur,banque,date_d,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

                                return render(request, 'stats.html', {'cargaison': table})


    # R32
            if frontiere != '':
                if importateur != '':
                    if banque != '':
                        if date_d != '':
                            if date_f != '':
                                table = EncaissementTable(Liquidation.objects.raw('SELECT DISTINCT (l.idliquidation), l.idcargaison_id , b.idbureau , p.code_bur, i.nomimportateur, p.nom_decl, l.numerobl, l.datebl, p.date_pay, p.mont_enc, p.qte_stat, p.bnk_nam \
                        FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_liquidation l, hydro_occ.enreg_bureaudgda b, hydro_occ.enreg_paiement p, hydro_occ.enreg_importateur i \
                        WHERE c.idcargaison = l.idcargaison_id \
                        AND p.code_bur = b.codebureau \
                        AND b.idbureau = l.codebureau_id \
                        AND l.numerobl = p.n_liq \
                        AND l.datebl = p.date_liq \
                        AND c.importateur_id = i.idimportateur \
                        AND c.frontiere_id = %s \
                        AND c.importateur_id = %s \
                        AND p.bnk_nam = %s \
                        AND l.datebl BETWEEN %s AND %s', [frontiere,importateur,banque,date_d,date_f,]), prefix="1_2")

                                RequestConfig(request, paginate={"paginator_class": LazyPaginator,
                                                                 "per_page": 15}).configure(table)

                                export_format = request.GET.get('_export', None)
                                if TableExport.is_valid_format(export_format):
                                    exporter = TableExport(export_format, table)
                                    return exporter.response('table.{}'.format(export_format))
                                return render(request, 'stats.html', {
                                    'cargaison': table
                                })

                                return render(request, 'stats.html', {'cargaison': table})
    else:
        return redirect('logout')



