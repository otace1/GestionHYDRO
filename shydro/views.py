from django.shortcuts import render, redirect, HttpResponse
from enreg.models import Cargaison, Ville, Voie, Entrepot, Importateur, Produit, Dechargement, Entrepot_echantillon, \
    Resultat, LaboReception
from accounts.models import *
from .tables import CodificationTable, ResultatGoLabo, Avarie, Act, Act2, ModificationCodification
from .forms import CodificationHydro
from django.contrib.auth.decorators import login_required
from shydro.utils import render_to_pdf
from django_tables2.paginators import LazyPaginator
from django_tables2 import RequestConfig
from django.db.models import Q
from datetime import date
import datetime
from .numact import numeroactcurrent
from .numdossier import numDossier


#Class de gestion des codifacations des cargaisons
class GestionCodification():
#Methode d'affichage du tableau pour la codification (Cargaison en attente de requisition)
    @login_required(login_url='login')
    def affichageTableau(request):
        user = request.user
        id = user.id
        role = user.role_id
        ville = AffectationVille.objects.get(username_id=id)
        ville = ville.ville_id

        if role == 7 or role == 1:
            if 'search' in request.GET:
                qs = request.GET['search']
                if qs == "":
                    request.session['url'] = request.get_full_path()
                    table = CodificationTable(
                        Cargaison.objects.filter(etat="En attente requisition").filter(entrepot__ville=ville) \
                            .order_by('-dateheurecargaison'), prefix="1_")
                    data = Entrepot.objects.filter(ville__idville=ville)
                    RequestConfig(request, paginate={"per_page": 20}).configure(table)
                    return render(request, 'shydro.html', {
                        'cargaison': table,
                        'filter': data,
                    })
                else:
                    request.session['url'] = request.get_full_path()
                    qs_temp = Entrepot.objects.get(nomentrepot=qs)
                    id_ent = qs_temp.identrepot
                    table = CodificationTable(
                        Cargaison.objects.filter(etat="En attente requisition", entrepot=id_ent, entrepot__ville=ville) \
                            .order_by('-dateheurecargaison'), prefix="3_")
                    data = Entrepot.objects.filter(ville__idville=ville)
                    RequestConfig(request, paginate={"per_page": 20}).configure(table)
                    return render(request, 'shydro.html', {
                        'cargaison': table,
                        'filter': data,
                    })
            else:
                request.session['url'] = request.get_full_path()
                table = CodificationTable(Cargaison.objects.filter(etat="En attente requisition", entrepot__ville=ville) \
                                          .order_by('-dateheurecargaison'), prefix="5_")
                data = Entrepot.objects.filter(ville__idville=ville)
                RequestConfig(request, paginate={"per_page": 20}).configure(table)
                return render(request, 'shydro.html', {
                    'cargaison': table,
                    'filter': data,
                })
        else:
            return redirect('logout')

# Fonction numrequisition
@login_required(login_url='login')
def numreq(request, pk):
    url = request.session['url']
    user = request.user
    id = user.id
    role = user.role_id
    if role == 7 or role == 1:
        if request.method == 'POST':
            numreq = request.POST['numreq']
            c = Cargaison.objects.get(pk=pk)
            numreq = numreq.upper()
            c.numreq = numreq
            c.save(update_fields=['numreq'])
            return redirect(url)
        else:
            return redirect(url)
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
        ville = AffectationVille.objects.get(username_id=id)
        ville = ville.ville_id
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

#Methode pour l'affichage des details d'un ligne
    @login_required(login_url='login')
    def linedetails(request,pk):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 7 or role == 1:
            a=Cargaison.objects.get(pk=pk)
            return render(request, 'shydroview.html')
        else:
            return redirect('logout')

#Gestion des Go apres avoir obtenu le statut de la cargaison
class GestionResultatLabo():

#Methode pour l'affichage des resultats venant Labo conforme
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
                                                          ORDER BY r.dateanalyse DESC', [id,]))

            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            return render(request, 'shydro_result.html', {'cargaison': table})
        else:
            return redirect('logout')

#Methode pour l'affichage des resultats venant du Labo Avarie
    @login_required(login_url='login')
    def affichagetableauavarie(request):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 7 or role == 1:
            table = Avarie(Cargaison.objects.filter(etat="Non conforme aux exigences", frontiere__affectationville__username_id=id).order_by('-dateheurecargaison'))
            RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
            return render(request, 'shydro_avarie.html', {'cargaison': table})
        else:
            return redirect('logout')

#Class pour la gestion des dechargements
class GestionDecharger():

#Methode pour l'envoi du Go de dechargement aux entrepots
    @login_required(login_url='login')
    def godechargement(request,pk):
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

#Methode pour l'affichage des elements dont les ACT sont prets a etre imprimer
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
                                                   ORDER BY d.datedechargement DESC', [id,]),prefix="100_")

            table1 = Act2(Cargaison.objects.raw('SELECT c.idcargaison, c.printactdate, c.numdossier, c.codecargaison, c.importateur_id , c.entrepot_id, c.immatriculation, l.numcertificatqualite, d.gsv\
                                                   FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_dechargement d, hydro_occ.enreg_laboreception l,hydro_occ.accounts_affectationville a\
                                                   WHERE c.idcargaison = d.idcargaison_id \
                                                   AND l.idcargaison_id = d.idcargaison_id \
                                                   AND c.frontiere_id = a.ville_id \
                                                   AND a.username_id = %s \
                                                   AND c.numact IS NOT NULL \
                                                   ORDER BY c.printactdate DESC',[id,]),prefix="200_")

            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            RequestConfig(request, paginate={"per_page": 15}).configure(table1)

            return render(request, 'shydro_act.html', {
                'act': table,
                'act1':table1,
            })
        else:
            return redirect('logout')


#Impression des ACT
    @login_required(login_url='login')
    def printact (request,pk):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 7 or role == 1:
            template = 'report/act.html'

            #Recuperation Cargaison
            c = Cargaison.objects.get(idcargaison=pk)
            d = Dechargement.objects.get(idcargaison=pk)
            e = Entrepot.objects.get(cargaison=pk)
            r = Resultat.objects.get(idcargaison=pk)
            p = Produit.objects.get(cargaison=pk)
            i = Importateur.objects.get(cargaison=pk)
            en = Entrepot_echantillon.objects.get(idcargaison=pk)
            re = LaboReception.objects.get(idcargaison=pk)

            #Elements de l'ACT
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
            diffvolume = round(((gov - gsv)/(gov))*100,2)
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
            c.save(update_fields=['impression','printactdate','numact'])

            data = {
                'year':year,
                'numact':numact,
                't1d':t1d,
                'codecargaison':codecargaison,
                'numdossier':numdossier,
                'importateur':importateur,
                'addressimport':addressimport,
                'provenance':provenance,
                'produit':produit,
                'immatriculation':immatriculation,
                'voldecl':voldecl,
                'voldecl15':voldecl15,
                'entrepot':entrepot,
                'chauffeur':chauffeur,
                'nationalite':nationalite,
                'numrappech':numrappech,
                'dateech':dateech,
                'datedech':datedech,
                'nature':nature,
                'gov':gov,
                'gsv':gsv,
                'numerore':numerore,
                'datecert':datecert,
                # 'diffvolume':diffvolume,
                'printactdate':printactdate
                    }

            #Render PDF report
            pdf = render_to_pdf(template,data)
            return HttpResponse(pdf,content_type='application/pdf')
        else:
            return redirect('logout')


#Impression des ACT
    @login_required(login_url='login')
    def reprintact (request,pk):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 7 or role == 1:
            template = 'report/act.html'

            #Recuperation Cargaison
            c = Cargaison.objects.get(idcargaison=pk)
            d = Dechargement.objects.get(idcargaison=pk)
            e = Entrepot.objects.get(cargaison=pk)
            r = Resultat.objects.get(idcargaison=pk)
            p = Produit.objects.get(cargaison=pk)
            i = Importateur.objects.get(cargaison=pk)
            en = Entrepot_echantillon.objects.get(idcargaison=pk)
            re = LaboReception.objects.get(idcargaison=pk)

            #Elements de l'ACT
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
            diffvolume = round(((gov - gsv)/(gov))*100,2)
            numerore = re.numcertificatqualite
            datecert = r.dateanalyse
            numact = c.numact
            printactdate = c.printactdate

            #Year Num
            year = c.dateheurecargaison
            year = datetime.datetime.date(year)
            year = year.year

            data = {
                'year':year,
                'numact':numact,
                't1d':t1d,
                'codecargaison':codecargaison,
                'numdossier':numdossier,
                'importateur':importateur,
                'addressimport':addressimport,
                'provenance':provenance,
                'produit':produit,
                'immatriculation':immatriculation,
                'voldecl':voldecl,
                'voldecl15':voldecl15,
                'entrepot':entrepot,
                'chauffeur':chauffeur,
                'nationalite':nationalite,
                'numrappech':numrappech,
                'dateech':dateech,
                'datedech':datedech,
                'nature':nature,
                'gov':gov,
                'gsv':gsv,
                'numerore':numerore,
                'datecert':datecert,
                'diffvolume':diffvolume,
                'printactdate':printactdate
                    }

            #Render PDF report
            pdf = render_to_pdf(template,data)
            return HttpResponse(pdf,content_type='application/pdf')
        else:
            return redirect('logout')


# Recherche ACT par numéro dossier, Codecargaison, Numéro ACT
    def rechercheact(request):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 7 or role == 1:
            if request.method == 'GET' :
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
                                                                       ORDER BY d.datedechargement ASC',[id,]), prefix="1_")

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
                                                                       ORDER BY c.printactdate DESC ',[q,q,q]), prefix="2_")

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






















