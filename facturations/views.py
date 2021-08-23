from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Avg, Sum
from decimal import Decimal
from .tables import Facturations, Appuration, Detailsappuration, Facturations1, Liquidat
from django_tables2 import RequestConfig
from django_tables2.paginators import LazyPaginator
from enreg.models import *
from .forms import SaisieBL


# Create your views here.
def facturations(request):
    request.session['url'] = request.get_full_path()
    user = request.user
    id = user.id
    form = SaisieBL()
    table = Facturations(Cargaison.objects.raw('SELECT c.idcargaison, c.dateheurecargaison, c.frontiere_id, c.importateur_id, c.declarant, c.immatriculation, c.t1e, c.t1d, c.numdeclaration, c.valeurfacture, c.produit_id, c.entrepot_id, c.fournisseur, c.volume, d.datedechargement, d.gsv \
                                                FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_entrepot_echantillon e, hydro_occ.enreg_dechargement d,hydro_occ.accounts_affectationville a \
                                                WHERE c.idcargaison = e.idcargaison_id \
                                                AND e.idcargaison_id = d.idcargaison_id \
                                                AND c.frontiere_id = a.ville_id \
                                                AND a.username_id = %s \
                                                AND c.l_control is NULL \
                                                ORDER BY c.dateheurecargaison DESC',[id,]), prefix='1_')

    table1 = Facturations1(Cargaison.objects.raw('SELECT l.idliquidation,c.idcargaison,l.datebl, l.numerobl ,l.codebureau_id , l.vol_liq , c.importateur_id , c.declarant ,c.immatriculation , c.entrepot_id \
                                                  FROM hydro_occ.enreg_liquidation l, hydro_occ.enreg_cargaison c, hydro_occ.accounts_affectationville a \
                                                  WHERE l.idcargaison_id = c.idcargaison \
                                                  AND c.frontiere_id = a.ville_id \
                                                  AND a.username_id = %s \
                                                  AND l.type_appurement = 3 \
                                                  ORDER BY l.datebl DESC', [id,]), prefix='2_')


# Traitement tableau 2
    i=1
    data = table1.data
    list = []
    while i<= (len(data)-1):
        t=data[i-1]
        pk = t.idcargaison
        vol_liq_som = Liquidation.objects.filter(idcargaison_id=pk).aggregate(Sum('vol_liq'))
        vol_liq_som = vol_liq_som.get('vol_liq__sum')
        vol = t.volume

        if (vol - vol_liq_som) >= 0.5:
            list.append(t)
        i = i + 1

    table2 = Facturations1(list)

    RequestConfig(request, paginate={"per_page": 8}).configure(table)
    RequestConfig(request, paginate={"per_page": 8}).configure(table2)
    return render(request, 'facturations.html', {'facturations': table,
                                                 'facturations1': table2,
                                                 'form': form,
                                                 })

def saisiebl(request):
    user = request.user
    url = request.session['url']
    template = 'formsbl.html'
    form = SaisieBL()

    if request.is_ajax():
        pk = request.POST['pk']
        c = Cargaison.objects.get(idcargaison=pk)
        idcargaison = c.idcargaison

        datebl = request.POST['datebl']
        numerobl = request.POST['numerobl']
        codebureau = request.POST['codebureau']
        vol_liq = request.POST['vol_liq']
        paiement = request.POST['paiement']

        codebureau = BureauDGDA.objects.get(idbureau=codebureau)

        c.l_control = 1
        c.save(update_fields=['l_control'])

        if paiement == 'total':
            paiement = 1
        else:
            paiement = 3

        # comparaison des volumes
        vol_liq_dec = Decimal(vol_liq)
        vol_cargaison = c.volume

        if Liquidation.objects.filter(idcargaison_id=pk).exists():
            vol_liq_som = Liquidation.objects.filter(idcargaison_id=pk).aggregate(Sum('vol_liq'))
            vol_liq_som = vol_liq_som.get('vol_liq__sum')
        else:
            vol_liq_som = 0

        if vol_cargaison >= vol_liq_som + vol_liq_dec:
            p = Liquidation(idcargaison_id=idcargaison, numerobl=numerobl, codebureau=codebureau, datebl=datebl,
                            vol_liq=vol_liq, type_appurement=paiement)
            p.save()
            return redirect(url)
        else:
            context = 'La somme des volumes est supérieure au volume declarée'
            return render(request, template, {'form': form,
                                              'context': context})
    return render(request, template, {'form': form})

def appureration(request):
    user = request.user
    id = user.id
    request.session['url'] = request.get_full_path()
    table=Appuration(Liquidation.objects.raw('SELECT l.idliquidation,l.datebl, l.numerobl , l.codebureau_id , l.vol_liq , c.importateur_id , c.declarant ,c.immatriculation , c.entrepot_id, c.manifestdgda, c.t1e, c.t1d \
                                                  FROM hydro_occ.enreg_liquidation l, hydro_occ.enreg_cargaison c, hydro_occ.accounts_affectationville a \
                                                  WHERE l.idcargaison_id = c.idcargaison \
                                                  AND c.frontiere_id = a.ville_id \
                                                  AND a.username_id = %s \
                                                  ORDER BY l.datebl DESC', [id,]), prefix='2_')
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
    return render(request, 'appuration.html', {'appuration': table})

def detailsappuration(request,pk):
    template='detailsappuration.html'
    c = Liquidation.objects.get(idliquidation=pk)   
    code_bur = c.codebureau
    date_liq = c.datebl
    n_liq = c.numerobl
    table = Detailsappuration(Paiement.objects.filter(code_bur=code_bur,date_liq=date_liq,n_liq=n_liq))
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    return render(request, template, {'detailsappuration': table})
