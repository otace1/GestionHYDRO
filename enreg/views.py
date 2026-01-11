import base64
import io
import os
import uuid
from datetime import date, datetime
import pyqrcode
from PIL import Image
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, FileResponse
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django_tables2 import RequestConfig
from django_tables2.paginators import LazyPaginator

from accounts.models import UserActivityLog, MyUser
from .forms import Ajoutcargaison
from .models import *
from .tables import CargaisonTable
from .uploadToStorage import upload_to_space


# Function
@login_required(login_url='login')
def getCargaison(request):
    user = request.user
    today = date.today()
    qs = Cargaison.objects.order_by('-dateheurecargaison').filter(user=user.id, dateheurecargaison__year=today.year)
    data = list(qs.values())
    # return JsonResponse(cargaisonList,safe=False)
    response = {'data': data}
    return JsonResponse(response)


# Affichage du Tableau
@login_required(login_url='login')
def showTableauTemplate(request):
    user = request.user
    today = date.today()
    q = request.GET.get('q')
    f = request.GET.get('f')

    base_qs = Cargaison.objects.filter(user=user.id)

    stats = {
        'today': base_qs.filter(dateheurecargaison__date=today).count(),
        'month': base_qs.filter(dateheurecargaison__year=today.year, dateheurecargaison__month=today.month).count(),
        'pending_req': base_qs.filter(etat="En attente requisition").count(),
    }

    qs = base_qs.filter(dateheurecargaison__year=today.year).order_by('-dateheurecargaison')

    if q:
        qs = qs.filter(qrcode__icontains=q)

    if f:
        qs = qs.filter(Q(immatriculation=f) | Q(numdossier=f) | Q(declaration=f))

    form = Ajoutcargaison()
    table = CargaisonTable(qs)
    template = 'cargaison/cargaison.html'
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 5}).configure(table)
    context = {
        'table': table,
        'form': form,
        'stats': stats,
    }
    return render(request, template, context)


@login_required(login_url='login')
def cargaison_create_form(request):
    form = Ajoutcargaison()
    html = render_to_string('cargaison/partial_create_form.html', {'form': form}, request=request)
    return JsonResponse({'html': html})


@login_required(login_url='login')
@require_POST
def cargaison_create(request):
    user = request.user
    form = Ajoutcargaison(request.POST)
    if form.is_valid():
        instance = Cargaison(
            voie=form.cleaned_data['voie'],
            frontiere=form.cleaned_data['frontiere'],
            typeunitetransport=form.cleaned_data['typeunitetransport'],
            provenance=form.cleaned_data['provenance'],
            importateur=form.cleaned_data['importateur'],
            produit=form.cleaned_data['produit'],
            entrepot=form.cleaned_data['entrepot'],
            immatriculation=form.cleaned_data['immatriculation'],
            transitaire=form.cleaned_data['transitaire'],
            declaration=form.cleaned_data['declaration'],
            volume=form.cleaned_data['volume'],
            volume15=form.cleaned_data['volume15'],
            volume20=form.cleaned_data['volume20'],
            tonnagevide=form.cleaned_data['tonnagevide'],
            tonnageair=form.cleaned_data['tonnageair'],
        )
        instance.qrcode = str(uuid.uuid4())
        instance.user = str(user.id)
        instance.etat = "En attente requisition"
        instance.save()

        # Activity Log
        UserActivityLog.objects.create(
            user=user,
            action="Data creation",
            description="User has created new import record successfully via AJAX",
        )
        return JsonResponse({'success': True, 'qrcode': instance.qrcode})
    else:
        html = render_to_string('cargaison/partial_create_form.html', {'form': form}, request=request)
        return JsonResponse({'success': False, 'html': html}, status=400)


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
        u = user.username
        user = MyUser.objects.get(pk=u)
        template='cargaison/cargaison.html'
        form = Ajoutcargaison()
        today = date.today()
        q = request.GET.get('q')
        f = request.GET.get('f')
        qs = Cargaison.objects.order_by('-dateheurecargaison').filter(user=u, dateheurecargaison__year=today.year)
        
        if q:
            qs = qs.filter(qrcode__icontains=q)
        
        if f:
            qs = qs.filter(Q(immatriculation=f) | Q(numdossier=f) | Q(declaration=f))
            
        table = CargaisonTable(qs)
        RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 5}).configure(table)
        context={
            'cargaison': table,
            'form': form,
        }
        return render(request, template, context)


    @login_required(login_url='login')
    def enregCargaison(request):
        user = request.user
        role = user.role_id
        u = user.id

        if role in [2, 1, 7]:
            if request.method == 'POST':
                # Extract form data
                form = Ajoutcargaison(request.POST, request.FILES)
                if form.is_valid():
                    voie = form.cleaned_data['voie']
                    frontiere = form.cleaned_data['frontiere']
                    typeunitetransport = form.cleaned_data['typeunitetransport']
                    provenance = form.cleaned_data['provenance']
                    importateur = form.cleaned_data['importateur']
                    produit = form.cleaned_data['produit']
                    entrepot = form.cleaned_data['entrepot']
                    immatriculation = form.cleaned_data['immatriculation']
                    transitaire = form.cleaned_data['transitaire']
                    declaration = form.cleaned_data['declaration']
                    volume = form.cleaned_data['volume']
                    volume15 = form.cleaned_data['volume15']
                    volume20 = form.cleaned_data['volume20']
                    tonnagevide = form.cleaned_data['tonnagevide']
                    tonnageair = form.cleaned_data['tonnageair']
                    # files = request.FILES.get('files')


                    qrcode = str(uuid.uuid4())
                    # Save the filepath into the database
                    instance = Cargaison(
                        voie=voie,
                        frontiere=frontiere,
                        typeunitetransport=typeunitetransport,
                        provenance=provenance,
                        importateur=importateur,
                        produit=produit,
                        entrepot=entrepot,
                        immatriculation=immatriculation,
                        transitaire=transitaire,
                        declaration=declaration,
                        volume=volume,
                        volume15=volume15,
                        volume20=volume20,
                        tonnagevide=tonnagevide,
                        tonnageair=tonnageair,
                        # files_path=uploaded_filepath  # Save the file path
                    )
                    instance.save()

                    # Save QR code and other details
                    instance.qrcode = qrcode
                    instance.user = u
                    instance.etat = "En attente requisition"
                    instance.save()

                    # Activity Log
                    UserActivityLog.objects.create(
                        user=user,
                        action="Data creation",
                        description="User has created new import record successfully",
                    )
                    return JsonResponse({'qrcode': qrcode}, status=200)
                else:
                    return JsonResponse({'error': 'Invalid form data'}, status=400)
            else:
                return JsonResponse({'error': 'Method not allowed'}, status=405)
        else:
            form = Ajoutcargaison()
            return render(request, 'cargaison/form.html', {'form': form})



    # Process the uploaded file
    # if files:
    #     print('FILE EXIST')
    #     # Generate a unique filename using QR code value and timestamp
    #     qrcode = str(uuid.uuid4())
    #     timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    #     directory = f'/files/{qrcode}'  # Directory name based on QR code value
    #     os.makedirs(directory, exist_ok=True)  # Create directory if not exists
    #     filename = f'{timestamp}.pdf'  # Filename including QR code value and timestamp
    #
    #     uploaded_filepath = upload_to_space(files.read(), directory, filename)
    #
    #     if uploaded_filepath:
    #         # Save the filepath into the database
    #         instance = Cargaison(
    #             voie=voie,
    #             frontiere=frontiere,
    #             typeunitetransport=typeunitetransport,
    #             provenance=provenance,
    #             importateur=importateur,
    #             produit=produit,
    #             entrepot=entrepot,
    #             immatriculation=immatriculation,
    #             transitaire=transitaire,
    #             declaration=declaration,
    #             volume=volume,
    #             volume15=volume15,
    #             volume20=volume20,
    #             tonnagevide=tonnagevide,
    #             tonnageair=tonnageair,
    #             files_path=uploaded_filepath  # Save the file path
    #         )
    #         instance.save()
    #
    #         # Save QR code and other details
    #         instance.qrcode = qrcode
    #         instance.user = u
    #         instance.etat = "En attente requisition"
    #         instance.save()
    #
    #         # Activity Log
    #         UserActivityLog.objects.create(
    #             user=user,
    #             action="Data creation",
    #             description="User has created new import record successfully",
    #         )
    #
    #         return JsonResponse({'qrcode': qrcode}, status=200)
    #     else:
    #         return JsonResponse({'error': 'Failed to upload file'}, status=500)
    # else:


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


@login_required(login_url='login')
def cargaison_details_partial(request, pk):
    cargaison = get_object_or_404(Cargaison, pk=pk)

    # Generate QR Code as base64 for preview
    qr = pyqrcode.create(cargaison.qrcode, encoding='utf-8')
    buffer = io.BytesIO()
    qr.png(buffer, scale=10)
    qrcode_base64 = base64.b64encode(buffer.getvalue()).decode()

    html = render_to_string('cargaison/partial_details.html', {
        'cargaison': cargaison,
        'qrcode_base64': qrcode_base64
    }, request=request)
    return JsonResponse({'html': html})


@login_required(login_url='login')
def cargaison_qrcode_download(request, pk):
    cargaison = get_object_or_404(Cargaison, pk=pk)
    qr = pyqrcode.create(cargaison.qrcode, encoding='utf-8')
    buffer = io.BytesIO()
    qr.png(buffer, scale=10)
    buffer.seek(0)

    filename = f"qrcode_{cargaison.immatriculation or cargaison.pk}.png"
    return FileResponse(buffer, as_attachment=True, filename=filename)
