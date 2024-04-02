import uuid
from datetime import date

import pyqrcode
from PIL import Image
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect
from django_tables2 import RequestConfig, LazyPaginator

from .forms import Ajoutcargaison, AjoutCargaison
from .models import *
from .tables import CargaisonTable


#Function
@login_required(login_url='login')
def getCargaison(request):
    user = request.user
    today = date.today()
    qs = Cargaison.objects.order_by('-dateheurecargaison').filter(user=user.id, dateheurecargaison__year=today.year)
    data = list(qs.values())
    # return JsonResponse(cargaisonList,safe=False)
    response = {'data':data}
    return JsonResponse(response)


#Affichage du Tableau
@login_required(login_url='login')
def showTableauTemplate(request):
    user = request.user
    today = date.today()
    qs = Cargaison.objects.order_by('-dateheurecargaison').filter(user=user.id, dateheurecargaison__year=today.year)
    form = Ajoutcargaison()
    table = CargaisonTable(qs)
    template = 'cargaison/cargaison.html'
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
    context = {
        'table':table,
        'form':form,
    }
    return render(request,template,context)


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
        form = Ajoutcargaison()
        today = date.today()
        if role == 2:
            if request.method == 'GET':
                qs = Cargaison.objects.order_by('-dateheurecargaison').filter(user=u,dateheurecargaison__year=today.year)
                table = CargaisonTable(qs)
                data = list(qs.values())
                RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 10}).configure(table)
                return render(request, 'cargaison/cargaison.html', {
                    'cargaison': table,
                    'form': form,
                    'data': data,
                })
        else:
            if role == 1:
                if request.method == 'GET':
                    form = Ajoutcargaison()
                    qs = Cargaison.objects.filter(dateheurecargaison__year=today.year).order_by('-dateheurecargaison')
                    table = CargaisonTable(qs)
                    data = list(qs.values())
                    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 10}).configure(table)
                    return render(request, 'cargaison/cargaison.html', {
                        'cargaison': table,
                        'form': form,
                        'data': data,
                    })
            else:
                return redirect('logout')

    @login_required(login_url='login')
    def enregCargaison(request):
        user = request.user
        role = user.role_id
        u = user.id

        if role == 2 or role == 1 or role == 7:
            template = 'cargaison/form.html'
            form = AjoutCargaison(request.POST or None)
            if form.is_valid():
                instance = form.save(commit=False)
                qrcode = str(uuid.uuid4())
                instance.qrcode = qrcode
                instance.user = u
                instance.etat = "En attente requisition"
                instance.save()
                return JsonResponse(qrcode, status=200, safe=False)
            context = {'form': form}
            return render(request, template, context)


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



