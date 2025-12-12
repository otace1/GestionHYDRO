import base64
import os
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from tempfile import template

import pyqrcode
from PIL import Image
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.db.models import Q, F
from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django_tables2 import RequestConfig, LazyPaginator

from accounts.models import UserActivityLog, MyUser
from .forms import Ajoutcargaison
from .models import *
from .tables import CargaisonTable
from .uploadToStorage import upload_to_space


def _num(val, allow_empty=True):
    """Parse optional numbers safely."""
    if val in (None, '',):
        return None if allow_empty else 0
    try:
        return float(Decimal(str(val)))
    except (InvalidOperation, ValueError, TypeError):
        return None if allow_empty else 0




# Function
@login_required(login_url='login')
def getCargaison(request):
    # Time window: last 30 days up to now
    now = timezone.now()
    start = now - timedelta(days=30)

    # Your model stores `user` as CharField; match username or id-as-string
    username = request.user.get_username()  # same as request.user.username
    user_id_str = str(request.user.id) if request.user.id is not None else ""

    qs = (
        Cargaison.objects
        .select_related('importateur', 'entrepot', 'produit')
        .filter(
            dateheurecargaison__gte=start,
            dateheurecargaison__lte=now,
        )
        .filter(
            Q(user=username) | Q(user=user_id_str)
        )
        .annotate(
            importateur_name=F('importateur__nomimportateur'),
            entrepot_name=F('entrepot__nomentrepot'),
            produit_name=F('produit__nomproduit'),
        )
        .order_by('-dateheurecargaison')
        .values(
            'idcargaison',
            'dateheurecargaison',
            'immatriculation',
            'volume',
            'importateur_name',
            'entrepot_name',
            'produit_name',
        )
    )

    data = list(qs)

    # Normalize fields for the frontend (ISO date + "id")
    for r in data:
        dt = r.get('dateheurecargaison')
        r['dateheurecargaison'] = dt.isoformat() if dt else None
        r['id'] = r.pop('idcargaison', None)

    return JsonResponse({'data': data})



def cargaisons_page(request):
    """
    Renders the page shell (no server-rendered table).
    The table is rendered client-side via JS.
    """
    template = 'cargaison_page.html'
    return render(request, template, {
        "form": Ajoutcargaison(),
    })


# Affichage du Tableau
@login_required(login_url='login')
def showTableauTemplate(request):
    user = request.user
    today = date.today()

    # Base queryset (same logic as before)
    qs = (
        Cargaison.objects
        .filter(user=user.id, dateheurecargaison__year=today.year)
        .order_by('-dateheurecargaison')
    )

    # Optional quick search (?q=...)
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(importateur__nomimportateur__icontains=q) |
            Q(immatriculation__icontains=q) |
            Q(produit__nomproduit__icontains=q) |
            Q(entrepot__nomentrepot__icontains=q)
        )

    # Pagination (default 15 per page)
    per_page = int(request.GET.get('per_page', 15) or 15)
    paginator = Paginator(qs, per_page)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        "form": Ajoutcargaison(),
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": paginator.num_pages > 1,
        "q": q,
        "per_page": per_page,
    }

    # AJAX: return only the table fragment (table + pagination)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render(request, "cargaison/_table.html", context)

    # Full page
    return render(request, "cargaison/cargaison.html", context)




@login_required
@require_POST
@transaction.atomic
def nouvelle(request):
    """
    Create a new Cargaison from modal form POST.
    Returns a text/plain QR payload on success (201),
    or a JSON error (400) on validation problems.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée."}, status=405)

    data = request.POST

    # ---- Resolve FKs (will 404 -> 400 if invalid) ----
    try:
        voie = Voie.objects.get(pk=int(data["voie"]))
        frontiere = Ville.objects.get(pk=int(data["frontiere"]))
        type_unite = TypeUniteTransport.objects.get(pk=int(data["typeunitetransport"]))
        importateur = Importateur.objects.get(pk=int(data["importateur"]))
        entrepot = Entrepot.objects.get(pk=int(data["entrepot"]))
        produit = Produit.objects.get(pk=int(data["produit"]))
    except (ValueError, Voie.DoesNotExist, Ville.DoesNotExist,
            TypeUniteTransport.DoesNotExist, Importateur.DoesNotExist,
            Entrepot.DoesNotExist, Produit.DoesNotExist):
        return JsonResponse(
            {"error": "Références invalides pour les champs liés."},
            status=400
        )

    # ---- Numbers & specific validation ----
    def _num(v, allow_empty=True):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None if allow_empty else None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    volume = _num(data.get("volume"), allow_empty=False)
    if volume is None or volume <= 0:
        return JsonResponse(
            {"error": "Volume ambiant invalide (doit être > 0).", "fields": ["volume"]},
            status=400
        )

    volume15 = _num(data.get("volume15"))
    volume20 = _num(data.get("volume20"))
    tonnagevide = _num(data.get("tonnagevide"))
    tonnageair = _num(data.get("tonnageair"))

    provenance = data.get("provenance")  # ISO country code (e.g., "CD", "FR")

    # ---- Create object (no qrcode yet) ----
    obj = Cargaison.objects.create(
        voie=voie,
        frontiere=frontiere,
        typeunitetransport=type_unite,
        importateur=importateur,
        entrepot=entrepot,
        produit=produit,
        immatriculation=(data.get("immatriculation") or "").strip(),
        transitaire=(data.get("transitaire") or "").strip(),
        provenance=provenance,
        declaration=((data.get("declaration") or "").strip() or None),
        volume=volume,
        volume15=volume15,
        volume20=volume20,
        tonnagevide=tonnagevide,
        tonnageair=tonnageair,
        # store username (your model's "user" is a CharField in your example)
        user=(getattr(request.user, "username", None) or str(getattr(request.user, "pk", ""))),
    )

    # ---- Generate QR code SAME WAY (uuid4 string) & set etat ----
    qrcode_value = str(uuid.uuid4())
    obj.qrcode = qrcode_value
    obj.etat = "En attente requisition"
    obj.save(update_fields=["qrcode", "etat"])

    # ---- Activity Log (if you use it) ----
    try:
        UserActivityLog.objects.create(
            user=request.user,
            action="Data creation",
            description="User has created new import record successfully",
        )
    except Exception:
        # Don't crash the creation if logging fails
        pass

    # ---- Return plain text so the front-end can feed it to QRCode() ----
    return HttpResponse(qrcode_value, content_type="text/plain", status=200)


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
        qs = Cargaison.objects.order_by('-dateheurecargaison').filter(user=u, dateheurecargaison__year=today.year).select_related('user')
        table = CargaisonTable(qs)
        RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 15}).configure(table)
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
