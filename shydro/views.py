from django.http import JsonResponse
from django.shortcuts import render, redirect, HttpResponse

from ads.forms import ImportateurForm, EntrepotForm
from enreg.forms import Ajoutcargaison
from enreg.models import *
from accounts.models import *
from entrepot.calculs import densite15, vcf, gsv, mta
from .tables import *
from .forms import *
from django.contrib.auth.decorators import login_required
from shydro.utils import render_to_pdf
from django_tables2.paginators import LazyPaginator
from django_tables2.export.export import TableExport
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

        if role == 7 or role == 1:
            if 'search' in request.GET:
                qs = request.GET['search']
                if qs == "":
                    request.session['url'] = request.get_full_path()

                    e = Cargaison.objects.filter(etat="En attente d'echantillonage",
                                                 entrepot__ville__affectationville__username_id=id).count()
                    d = ImpressionResultat.objects.filter(isConforme=1, idcargaison__etat="Conforme aux exigences",
                                                          idcargaison__entrepot__ville__affectationville__username_id=id).count()
                    l = Cargaison.objects.filter(etat="Analyse Labo en cours",
                                                 entrepot__ville__affectationville__username_id=id).count()
                    n = ImpressionResultat.objects.filter(idcargaison__entrepot__ville__affectationville__username_id=id,
                                                            isConforme=0, control=1).count()

                    table = CodificationTable(
                        Cargaison.objects.filter(etat="En attente requisition").filter(entrepot__ville__affectationville__username_id=id) \
                            .order_by('-dateheurecargaison'), prefix="1_")
                    data = Entrepot.objects.filter(ville__affectationville__username_id=id)
                    RequestConfig(request, paginate={"per_page": 7}).configure(table)
                    return render(request, 'shydro.html', {
                        'cargaison': table,
                        'filter': data,
                        'e':e,
                        'd':d,
                        'l':l,
                        'n':n

                    })
                else:
                    request.session['url'] = request.get_full_path()

                    e = Cargaison.objects.filter(etat="En attente d'echantillonage",
                                                 entrepot__ville__affectationville__username_id=id).count()
                    d = ImpressionResultat.objects.filter(isConforme=1, idcargaison__etat="Conforme aux exigences",
                                                          idcargaison__entrepot__ville__affectationville__username_id=id).count()
                    l = Cargaison.objects.filter(etat="Analyse Labo en cours",
                                                 entrepot__ville__affectationville__username_id=id).count()
                    n = ImpressionResultat.objects.filter(idcargaison__entrepot__ville__affectationville__username_id=id,
                                                            isConforme=0, control=1).count()

                    qs_temp = Entrepot.objects.get(nomentrepot=qs)
                    id_ent = qs_temp.identrepot
                    table = CodificationTable(
                        Cargaison.objects.filter(etat="En attente requisition", entrepot=id_ent, entrepot__ville__affectationville__username_id=id) \
                            .order_by('-dateheurecargaison'), prefix="3_")
                    data = Entrepot.objects.filter(ville__affectationville__username_id=id)
                    RequestConfig(request, paginate={"per_page": 7}).configure(table)
                    return render(request, 'shydro.html', {
                        'cargaison': table,
                        'filter': data,
                        'e':e,
                        'd':d,
                        'l':l,
                        'n':n

                    })
            else:
                request.session['url'] = request.get_full_path()

                e = Cargaison.objects.filter(etat="En attente d'echantillonage",
                                             entrepot__ville__affectationville__username_id=id).count()
                d = ImpressionResultat.objects.filter(isConforme=1, idcargaison__etat="Conforme aux exigences",
                                                      idcargaison__entrepot__ville__affectationville__username_id=id).count()
                l = Cargaison.objects.filter(etat="Analyse Labo en cours",
                                             entrepot__ville__affectationville__username_id=id).count()
                n = ImpressionResultat.objects.filter(idcargaison__entrepot__ville__affectationville__username_id=id,
                                                      isConforme=0, control=0).count()

                table = CodificationTable(Cargaison.objects.filter(etat="En attente requisition", entrepot__ville__affectationville__username_id=id) \
                                          .order_by('-dateheurecargaison'), prefix="5_")
                data = Entrepot.objects.filter(ville__affectationville__username_id=id)
                RequestConfig(request, paginate={"per_page": 7}).configure(table)
                context = {
                    'cargaison': table,
                    'filter': data,
                    'e':e,
                    'd':d,
                    'l':l,
                    'n':n
                }
                return render(request, 'shydro.html', context)
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

    #Get Town du point de dechargement pour l'attribution automatique des numeros
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

#Methode pour l'affichage des details d'un ligne
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
    def affichageNonConforme(request):
        user = request.user
        id = user.id
        role = user.role_id
        if role == 7 or role == 1:
            qs1 = Entrepot_echantillon.objects.filter(idcargaison__etat="Non conforme aux exigences",
                                                      idcargaison__entrepot__ville__affectationville__username=id,
                                                      idcargaison__impressionresultat__isConforme=0, idcargaison__impressionresultat__control=0)


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

@login_required(login_url='login')
def enAttenteEchantillonnage(request):
    user = request.user.id
    template = 'enAttenteEchantillonnage.html'
    qs = Cargaison.objects.filter(etat="En attente d'echantillonage",entrepot__ville__affectationville__username_id=user)
    table = EnAttenteEchantillonage(qs)
    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    context = {'table':table}
    return render(request,template,context)


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
            AND aa.username_id = %s",[user,])

    table = EnAttenteDechargement(qs)
    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    context = {'table':table}
    return render(request,template,context)


@login_required(login_url='login')
def enAttenteResultatLabo(request):
    user = request.user.id
    template = 'enAttenteResultatLabo.html'
    qs = LaboReception.objects.filter(idcargaison__idcargaison__etat="Analyse Labo en cours", idcargaison__idcargaison_id__entrepot__ville__affectationville__username_id=user)
    table = EnAttenteResultatLabo(qs)
    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    context = {'table':table}
    return render(request,template,context)


@login_required(login_url='login')
def rapportActivite(request):
    user = request.user.id
    template = 'rapportActivite.html'
    form = Filters(user=user)

    # qs = Cargaison.objects.select_related('entrepot_echantillon').filter(entrepot__ville__affectationville__username_id=user)
    qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                                FROM enreg_cargaison c \
                                                    LEFT JOIN enreg_entrepot_echantillon e \
                                                    ON c.idcargaison = e.idcargaison_id \
                                                    LEFT JOIN enreg_laboreception l \
                                                    ON e.idcargaison_id = l.idcargaison_id \
                                                    LEFT JOIN enreg_impressionresultat r \
                                                    ON l.idcargaison_id = r.idcargaison_id \
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
                                                    ORDER BY i.dateinspection DESC', [user, ])

    table = RapportActivite(qs)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response("table.{}".format(export_format))

    context = {
        'table':table,
        'form':form
        }
    return render(request,template,context)


@login_required(login_url='login')
def regularisation(request):
    user = request.user.id
    template ='regularisation.html'
    form = ChangementDestination()
    form1 = Transbordement()
    form2 = ChangementNatureProduit()
    form3 = ImportateurForm()
    form4 = EntrepotForm()
    form5 = Ajoutcargaison()
    qs = Cargaison.objects.filter(entrepot__ville__affectationville__username_id=user).filter(Q(etat='En attente requisition')| Q(etat="En attente d'echantillonage") | Q(etat='Echantillonner') | Q(etat='Analyse Labo en cours')).order_by('-dateheurecargaison')
    table = Regularisation(qs)
    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    context = {
        'table':table,
        'form':form,
        'form1':form1,
        'form2':form2,
        'form3':form3,
        'form4':form4,
        'form5':form5,
    }
    return render(request,template,context)


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
            pk = request.POST.get('pk',None)
            nouvelleDestination = request.POST.get('nouvelleDestination',None)
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
            pk = request.POST.get('pk',None)
            nouvelleImmatriculation = request.POST.get('nouvelleImmatriculation',None)
            nouveauVolume = request.POST.get('nouveauVolume',None)
            cargaison = Cargaison.objects.get(idcargaison=pk)
            cargaison.immatriculation = nouvelleImmatriculation
            cargaison.volume = nouveauVolume
            cargaison.save(update_fields=['immatriculation','volume'])
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
            pk = request.POST.get('pk',None)
            nouvelleNatureProduit = request.POST.get('nouvelleNatureProduit',None)
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
def pertes(request,pk):
    Cargaison.objects.get(idcargaison=pk).delete()
    return redirect('regularisation')


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

        if fournisseur and entrepot and dateDebut and dateFin:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND c.importateur_id = %s \
                                                AND c.entrepot_id = %s \
                                                AND DATE(c.dateheurecargaison) BETWEEN %s AND %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,fournisseur,entrepot,dateDebut,dateFin, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if fournisseur and entrepot and dateDebut:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND c.importateur_id = %s \
                                                AND c.entrepot_id = %s \
                                                AND DATE(c.dateheurecargaison) = %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,fournisseur,entrepot,dateDebut, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if fournisseur and entrepot and dateFin:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND c.importateur_id = %s \
                                                AND c.entrepot_id = %s \
                                                AND DATE(c.dateheurecargaison) = %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,fournisseur,entrepot,dateFin, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if fournisseur and entrepot:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND c.importateur_id = %s \
                                                AND c.entrepot_id = %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,fournisseur,entrepot, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if fournisseur and dateDebut and dateFin:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND c.importateur_id = %s \
                                                AND DATE(c.dateheurecargaison) BETWEEN %s AND %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,fournisseur,dateDebut,dateFin, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if fournisseur and dateDebut :
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND c.importateur_id = %s \
                                                AND DATE(c.dateheurecargaison) = %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,fournisseur,dateDebut, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if fournisseur and dateFin:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND c.importateur_id = %s \
                                                AND DATE(c.dateheurecargaison) = %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,fournisseur,dateFin, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if fournisseur:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND c.importateur_id = %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,fournisseur, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if entrepot and dateDebut and dateFin:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND c.entrepot_id = %s \
                                                AND DATE(c.dateheurecargaison) BETWEEN %s AND %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,entrepot,dateDebut,dateFin, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if entrepot and dateDebut:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND c.entrepot_id = %s \
                                                AND DATE(c.dateheurecargaison) = %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,entrepot,dateDebut, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if entrepot and dateFin:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND c.entrepot_id = %s \
                                                AND DATE(c.dateheurecargaison) = %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,entrepot,dateFin, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if entrepot:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND c.entrepot_id = %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,entrepot, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if dateDebut and dateFin:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND DATE(c.dateheurecargaison) BETWEEN %s AND %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,dateDebut,dateFin, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if dateDebut:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND DATE(c.dateheurecargaison) = %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,dateDebut, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        if dateFin:
            qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                AND DATE(c.dateheurecargaison) = %s \
                                                GROUP BY c.idcargaison \
                                                ORDER BY i.dateinspection DESC', [user,dateFin, ])

            table = RapportActivite(qs)
            RequestConfig(request, paginate={"per_page": 15}).configure(table)
            export_format = request.GET.get("_export", None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response("table.{}".format(export_format))

            context = {
                'table':table,
                'form':form
                }
            return render(request,template,context)

        qs = Cargaison.objects.raw('SELECT c.idcargaison, i.idinspection, ev.nomville, i.dateinspection, a.nomimportateur, ee.nomentrepot ,c.immatriculation, p.nomproduit, c.dateheurecargaison, c.requisitiondackdate, e.dateechantillonage, l.datereceptionlabo, r.printDate, i.dateinspection , c.volume , SUM(co.gov) as volConst, ROUND(SUM(co.gsv),4) as gsvT \
                                            FROM enreg_cargaison c \
                                                LEFT JOIN enreg_entrepot_echantillon e \
                                                ON c.idcargaison = e.idcargaison_id \
                                                LEFT JOIN enreg_laboreception l \
                                                ON e.idcargaison_id = l.idcargaison_id \
                                                LEFT JOIN enreg_impressionresultat r \
                                                ON l.idcargaison_id = r.idcargaison_id \
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
                                                ORDER BY i.dateinspection DESC', [user, ])

        table = RapportActivite(qs)
        RequestConfig(request, paginate={"per_page": 15}).configure(table)
        export_format = request.GET.get("_export", None)
        if TableExport.is_valid_format(export_format):
            exporter = TableExport(export_format, table)
            return exporter.response("table.{}".format(export_format))

        context = {
            'table':table,
            'form':form
            }
        return render(request,template,context)
    else:
        return redirect('rapportActivite')


@login_required(login_url='login')
def rapportRe(request,pk):
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
            'province':province,

        }
        # Render PDF Files
        pdf = render_to_pdf(template, data)
        return HttpResponse(pdf, content_type='application/pdf')
    except:
        return redirect('rapportActivite')


def consignation(request,pk):
    c = Cargaison.objects.get(idcargaison=pk)
    i = ImpressionResultat.objects.get(idcargaison=c)
    i.control = 1
    c.toBeConsignated = 1
    i.save(update_fields=['control'])
    c.save(update_fields=['toBeConsignated'])
    return redirect('affichageNonConforme')







