from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Sum, F, Q, Max
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django_tables2 import RequestConfig
from django_tables2.paginators import LazyPaginator

from enreg.models import *
from .forms import SaisieBL
from .tables import Facturations, Appuration, Detailsappuration, Facturations1, AffichageDetailLiquidation


# Create your views here.
@login_required(login_url='login')
def facturations(request):
    # request.session['url'] = request.get_full_path()
    template = 'facturations.html'
    form = SaisieBL()
    context = {
        'form':form,
    }
    return render(request,template,context)


# Create your views here.
@login_required(login_url='login')
def partial(request):
    # request.session['url'] = request.get_full_path()
    template = 'partial.html'
    form = SaisieBL()
    context = {
        'form':form,
    }
    return render(request,template,context)


    # qs2 = Liquidation.objects.filter(idcargaison_id=F('cargaison__idcargaison')) \
    #     .filter(cargaison__frontiere_id=F('cargaison__accounts_affectationville__ville_id')) \
    #     .filter(cargaison__accounts_affectationville__username_id=id) \
    #     .filter(type_appurement=3) \
    #     .order_by('-datebl') \
    #     .values('idliquidation', 'cargaison__idcargaison', 'datebl', 'numerobl', 'codebureau_id', 'vol_liq',
    #             'cargaison__importateur_id', 'cargaison__declarant', 'cargaison__immatriculation',
    #             'cargaison__entrepot_id')
    # table1 = Facturations1(qs2)


# # Traitement tableau 2
#     i=1
#     data = table1.data
#     list = []
#     while i<= (len(data)-1):
#         t=data[i-1]
#         pk = t.idcargaison
#         vol_liq_som = Liquidation.objects.filter(idcargaison_id=pk).aggregate(Sum('vol_liq'))
#         vol_liq_som = vol_liq_som.get('vol_liq__sum')
#         vol = t.volume
#
#         if (vol - vol_liq_som) >= 0.5:
#             list.append(t)
#         i = i + 1
#
#     table2 = Facturations1(list)



@login_required(login_url='login')
def facturationsResponse(request):
    user = request.user
    qs = Cargaison.objects.filter(entrepot__ville__affectationville__username_id=user,
                                  controlLiquidation=False,
                                  partialLiquidattion=False
                                  ).order_by('-dateheurecargaison') \
        .annotate(gsvTotal=Sum('inspection__compartiment__gsv')) \
        .values('idcargaison', 'dateheurecargaison', 'transitaire',
                'immatriculation', 'declaration', 'produit__nomproduit',
                'entrepot__nomentrepot', 'importateur__nomimportateur',
                'volume', 'dateDechargement', 'gsvTotal', 'frontiere__nomville')

    # Get the search value from the request's GET parameters
    search_value = request.GET.get('search[value]', '')

    # Apply search filter to the QuerySet
    if search_value:
        qs = qs.filter(
            Q(declaration__icontains=search_value) |
            Q(transitaire__icontains=search_value) |
            Q(entrepot__nomentrepot__icontains=search_value) |
            Q(importateur__nomimportateur__icontains=search_value)
        )

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
def partialResponse(request):
    user = request.user
    qs = Cargaison.objects.filter(entrepot__ville__affectationville__username_id=user,
                                  controlLiquidation=False,
                                  partialLiquidattion=True
                                  ).order_by('-dateheurecargaison') \
        .annotate(gsvTotal=Sum('inspection__compartiment__gsv')) \
        .values('idcargaison', 'dateheurecargaison', 'transitaire',
                'immatriculation', 'declaration', 'produit__nomproduit',
                'entrepot__nomentrepot', 'importateur__nomimportateur',
                'volume', 'dateDechargement', 'gsvTotal', 'frontiere__nomville')

    # Get the search value from the request's GET parameters
    search_value = request.GET.get('search[value]', '')

    # Apply search filter to the QuerySet
    if search_value:
        qs = qs.filter(
            Q(declaration__icontains=search_value) |
            Q(transitaire__icontains=search_value) |
            Q(entrepot__nomentrepot__icontains=search_value) |
            Q(importateur__nomimportateur__icontains=search_value)
        )

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
def partialResponseData(request):
    template = 'detailsPartials.html'
    pk = request.GET.get('pk','')
    qs = Liquidation.objects.filter(
        idcargaison=pk
    )
    table = AffichageDetailLiquidation(qs)
    RequestConfig(request, paginate={"per_page": 50}).configure(table)
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def rapports(request):
    template = 'rapports.html'
    context = {}
    return render(request,template,context)


@login_required(login_url='login')
def rapportsResponse(request):
    user = request.user
    qs = Liquidation.objects.filter(
        idcargaison__entrepot__ville__affectationville__username_id=user
    ).values('idcargaison').annotate(
        dateheurecargaison__date=Max('idcargaison__dateheurecargaison__date'),
        nomville=Max('idcargaison__frontiere__nomville'),
        declaration=Max('idcargaison__declaration'),
        nomimportateur=Max('idcargaison__importateur__nomimportateur'),
        nomentrepot=Max('idcargaison__entrepot__nomentrepot'),
        nomproduit=Max('idcargaison__produit__nomproduit'),
        volume=Max('idcargaison__volume'),
        gsvT=Sum('idcargaison__inspection__compartiment__gsv'),
        volLiqTotal=Sum('vol_liq')
    ).order_by('idcargaison')


    # Get the search value from the request's GET parameters
    search_value = request.GET.get('search[value]', '')

    # Apply search filter to the QuerySet
    if search_value:
        qs = qs.filter(
            Q(idcargaison__declaration__icontains=search_value) |
            Q(idcargaison__importateur__nomimportateur__icontains=search_value) |
            Q(numerobl__icontains=search_value)
        )

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
def saisiebl(request):
    user = request.user
    if request.method == 'POST':
        pk = request.POST['pk']
        c = Cargaison.objects.get(idcargaison=pk)

        datebl = request.POST['datebl']
        datepay = request.POST['datepay']
        numerobl = request.POST['numerobl']
        modele = request.POST['modele']
        bankName = request.POST['bankName']
        codebureau = request.POST['codebureau']
        vol_liq = request.POST['vol_liq']
        paiement = request.POST['paiement']

        codebureau = BureauDGDA.objects.get(idbureau=codebureau)
        modele = LiquidationModel.objects.get(idLiquidationMod=modele)
        bankName = Banques.objects.get(idbanque=bankName)

        if paiement == 'total':
            try:
                Liquidation(
                    datebl=datebl,
                    datepay=datepay,
                    numerobl=numerobl,
                    modele=modele,
                    bankName=bankName,
                    codebureau=codebureau,
                    vol_liq=vol_liq,
                    type_appurement=paiement,
                    user=user,
                    idcargaison=c
                ).save()
                Cargaison.objects.filter(pk=pk).update(controlLiquidation=True,partialLiquidattion=False)
                context = {}
                return JsonResponse(context, status=200)
            except:
                context = {}
                return JsonResponse(context, status=400)
        else:
            try:
                Liquidation(
                    datebl=datebl,
                    datepay=datepay,
                    numerobl=numerobl,
                    modele=modele,
                    bankName=bankName,
                    codebureau=codebureau,
                    vol_liq=vol_liq,
                    type_appurement=paiement,
                    user=user,
                    idcargaison=c
                ).save()
                Cargaison.objects.filter(pk=pk).update(partialLiquidattion=True)
                context = {}
                return JsonResponse(context, status=200)
            except:
                context = {}
                return JsonResponse(context, status=400)
    else:
        context = {}
        return JsonResponse(context,status=400)




@login_required(login_url='login')
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



@login_required(login_url='login')
def detailsappuration(request, pk):
    template = 'detailsappuration.html'
    c = Liquidation.objects.get(idliquidation=pk)
    code_bur = c.codebureau
    date_liq = c.datebl
    n_liq = c.numerobl
    table = Detailsappuration(Paiement.objects.filter(code_bur=code_bur, date_liq=date_liq, n_liq=n_liq))
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    return render(request, template, {'detailsappuration': table})


@login_required(login_url='login')
def filtret1(request):
    user = request.user
    id = user.id
    q = request.GET.get('q')
    form = SaisieBL()
    table = Facturations(Cargaison.objects.raw('SELECT c.idcargaison, c.dateheurecargaison, c.frontiere_id, c.importateur_id, c.declarant, c.immatriculation, c.t1e, c.t1d, c.numdeclaration, c.valeurfacture, c.produit_id, c.entrepot_id, c.fournisseur, c.volume, d.datedechargement, d.gsv \
                                                    FROM hydro_occ.enreg_cargaison c, hydro_occ.enreg_entrepot_echantillon e, hydro_occ.enreg_dechargement d,hydro_occ.accounts_affectationville a \
                                                    WHERE c.idcargaison = e.idcargaison_id \
                                                    AND e.idcargaison_id = d.idcargaison_id \
                                                    AND c.frontiere_id = a.ville_id \
                                                    AND a.username_id = %s \
                                                    AND c.l_control is NULL \
                                                    AND c.t1e = %s \
                                                    ORDER BY c.dateheurecargaison DESC', [id, q, ]), prefix='1_')

    table1 = Facturations1(Cargaison.objects.raw('SELECT l.idliquidation,c.idcargaison,l.datebl, l.numerobl ,l.codebureau_id , l.vol_liq , c.importateur_id , c.declarant ,c.immatriculation , c.entrepot_id \
                                                      FROM hydro_occ.enreg_liquidation l, hydro_occ.enreg_cargaison c, hydro_occ.accounts_affectationville a \
                                                      WHERE l.idcargaison_id = c.idcargaison \
                                                      AND c.frontiere_id = a.ville_id \
                                                      AND a.username_id = %s \
                                                      AND l.type_appurement = 3 \
                                                      ORDER BY l.datebl DESC', [id, ]), prefix='2_')

    # Traitement tableau 2
    i = 1
    data = table1.data
    list = []
    while i <= (len(data) - 1):
        t = data[i - 1]
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
    return render(request, 'facturations1.html', {'facturations': table,
                                                  'facturations1': table2,
                                                  'form': form,
                                                  })
