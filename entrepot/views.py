from __future__ import annotations

import base64
from datetime import date
import datetime as dt
from decimal import Decimal, InvalidOperation
from math import ceil
from re import template
from typing import Any, List, Dict, Optional
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
# Sending email
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Q, Sum, Avg, Case, When, FloatField, F, Value, CharField, Count, Exists, OuterRef
from django.forms import IntegerField
from django.http import HttpResponse, HttpResponseBadRequest, Http404, HttpRequest, HttpResponseNotAllowed
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.timezone import is_naive, make_naive, get_current_timezone, make_aware, localtime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django_tables2 import RequestConfig
from django_tables2.paginators import LazyPaginator
from openpyxl import Workbook
from reportlab.graphics.shapes import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Spacer

from accounts.models import *
from labo.utils import render_to_pdf
from shydro.numact import num_cert_inspection
from enreg.models import *
from .calculs import *
from .forms import *
from .numrappech import numRappEch
from .tables import *


# --- Styles / helpers ---------------------------------------------------------
BASE_FONT = "Helvetica"
BOLD_FONT = "Helvetica-Bold"

def _p(html, size=11, align="LEFT", bold=False):
    return Paragraph(
        html,
        ParagraphStyle(
            name="p",
            fontName=BOLD_FONT if bold else BASE_FONT,
            fontSize=size,
            leading=size + 2,
            alignment={"LEFT": TA_LEFT, "CENTER": TA_CENTER}.get(align, TA_LEFT),
        ),
    )

def _section_title(text):
    return Paragraph(
        f"<b>{text}</b>",
        ParagraphStyle(
            name="section",
            fontName=BOLD_FONT,
            fontSize=12,
            leading=14,
            spaceBefore=4,
            spaceAfter=2,
        ),
    )


def _is_ajax(request) -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


@login_required
def cargaisons_pending(request):
    user = request.user
    uid = user.id

    # Query cargaisons
    qs = (
        Cargaison.objects
        .filter(
            etat="En attente d'echantillonage",
            entrepot__affectationentrepot__username_id=uid
        )
        .order_by("-dateheurecargaison")
    )

    # Handle pagination (default page=1, per_page=10)
    page_num = request.GET.get("page", 1)
    per_page = int(request.GET.get("per_page", 10))

    paginator = Paginator(qs, per_page)
    page = paginator.get_page(page_num)

    data = [
        {
            "id": c.idcargaison,
            "dateheurecargaison": c.dateheurecargaison.isoformat() if c.dateheurecargaison else None,
            "importateur": str(c.importateur) if c.importateur else None,
            "entrepot": str(c.entrepot) if c.entrepot else None,
            "immatriculation": c.immatriculation,
            "produit": str(c.produit) if c.produit else None,
            "volume": c.volume,
            "etat": c.etat,
        }
        for c in page
    ]

    return JsonResponse({
        "pending": data,
        "pagination": {
            "page": page.number,
            "per_page": per_page,
            "total": paginator.count,
            "pages": paginator.num_pages,
            "has_next": page.has_next(),
            "has_prev": page.has_previous(),
        }
    }, safe=False)


@login_required
def cargaisons_status_requisition(request):
    user   = request.user
    uid    = getattr(user, "id", None)
    status = "En attente requisition"

    # Parse & clamp pagination inputs
    try:
        page = max(1, int(request.GET.get("page", 1)))
    except ValueError:
        page = 1
    try:
        per = int(request.GET.get("per_page", 10))
        per = 1 if per < 1 else (100 if per > 100 else per)  # hard cap for safety
    except ValueError:
        per = 10

    q = (request.GET.get("q", "") or "").strip()

    # Base queryset (only this user's assigned entrepôt + status)
    qs = (
        Cargaison.objects
        .filter(
            etat=status,
            entrepot__affectationentrepot__username_id=uid
        )
        .order_by("-dateheurecargaison")
    )

    # Text search (fix field name to 'immatriculation')
    if q:
        qs = qs.filter(
            Q(immatriculation__icontains=q)
            | Q(importateur__icontains=q)
            | Q(produit__icontains=q)
            | Q(entrepot__icontains=q)
        )

    total = qs.count()
    pages = max(1, ceil(total / per)) if per else 1
    if page > pages:
        page = pages  # clamp to last page if out of range

    start = (page - 1) * per
    end   = start + per

    # Normalize field names so the frontend mapper works:
    # - provide 'id' (alias of idcargaison)
    # - keep your simple string fields as-is
    page_qs = (
        qs
        .annotate(id=F("idcargaison"))
        .values(
            "id",
            "dateheurecargaison",
            "importateur",
            "entrepot",
            "immatriculation",
            "produit",
            "volume",
        )[start:end]
    )

    items = list(page_qs)

    return JsonResponse({
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
        },
    })



@require_GET
@login_required
@require_GET
@login_required
def tableauechantillonnage(request):
    user = request.user
    role = getattr(user, "role_id", None)
    if role not in (1, 3, 9):
        return redirect('logout')

    request.session['url'] = request.get_full_path()
    uid = user.id

    base = (
        Cargaison.objects
        .filter(entrepot__affectationentrepot__username_id=uid)
        .only(
            'idcargaison', 'etat', 'etatInspection',
            'toBeConsignated', 'toBeRefouler', 'isConsignated', 'isRefouler'
        )
    )

    # EXISTS: record in ImpressionResultat with isConforme=True for this cargo
    sub_conforme = Exists(
        ImpressionResultat.objects.filter(
            idcargaison_id=OuterRef('pk'),
            isConforme=True
        )
    )

    qs = base.annotate(
        is_waiting=Case(
            When(etat__iexact="En attente requisition", then=1),
            default=0,
            output_field=models.IntegerField(),  # fully qualified
        ),
        is_inspection=Case(
            When(etatInspection=False, then=1),
            default=0,
            output_field=models.IntegerField(),
        ),
        is_conformes=Case(
            When(Q(etat__iexact="Conforme aux exigences") & sub_conforme, then=1),
            default=0,
            output_field=models.IntegerField(),
        ),
        is_reports=Case(
            When(
                (Q(toBeConsignated=True) | Q(toBeRefouler=True)) &
                (Q(isConsignated=False) | Q(isRefouler=False)),
                then=1,
            ),
            default=0,
            output_field=models.IntegerField(),
        ),
    )

    agg = qs.aggregate(
        waiting=Sum('is_waiting'),
        inspection=Sum('is_inspection'),
        conformes=Sum('is_conformes'),
        reports=Sum('is_reports'),
    )

    kpis = {
        "waiting":    int(agg["waiting"] or 0),
        "inspection": int(agg["inspection"] or 0),
        "conformes":  int(agg["conformes"] or 0),
        "reports":    int(agg["reports"] or 0),
    }

    wants_json = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or request.headers.get('accept', '').lower().startswith('application/json')
        or request.GET.get('format') == 'json'
    )
    if wants_json:
        return JsonResponse(kpis, status=200)

    return render(request, "entrepot.html", kpis)


@login_required(login_url="login")
@require_POST
def record_sampling(request):
    # AJAX only
    if not _is_ajax(request):
        return JsonResponse({"error": "Invalid request"}, status=400)

    # Role check
    user = request.user
    if getattr(user, "role_id", None) not in (1, 3, 9):
        return JsonResponse({"error": "Forbidden"}, status=403)

    # Inputs
    pk = request.POST.get("cargaison_id") or request.POST.get("pk")
    matricule = (request.POST.get("matricule") or "").strip()
    methodeutilisee = (request.POST.get("methodeutilisee") or "").strip()
    qte = (request.POST.get("qte") or "").strip()
    notes = (request.POST.get("notes") or "").strip()

    if not (pk and matricule and methodeutilisee and qte):
        return JsonResponse({"error": "Champs requis manquants."}, status=400)

    # Fetch cargaison
    cargaison = get_object_or_404(Cargaison, pk=pk)

    # We assign/compute the auto number inside a transaction to avoid
    # duplicate numbers under normal concurrency.
    with transaction.atomic():
        # Get or create the sampling row
        echantillon, created = Entrepot_echantillon.objects.select_for_update().get_or_create(
            idcargaison=cargaison
        )

        # Compute/assign auto number only if not already set
        if echantillon.numrappechauto is None:
            try:
                ville = cargaison.entrepot.ville  # Ville instance
            except Exception:
                # If Entrepot or Ville missing, fail clearly
                return JsonResponse({"error": "Ville d'entrepôt introuvable pour cette cargaison."}, status=400)

            auto_num = numRappEch(cargaison.idcargaison, ville)
            echantillon.numrappechauto = auto_num

        # Update fields
        echantillon.matricule = matricule
        echantillon.methodeutilisee = methodeutilisee
        echantillon.qte = qte
        echantillon.notes = notes
        echantillon.useredit = str(user) if user.is_authenticated else None
        echantillon.save()

        # Update cargaison state
        # (tampon "1" semble signifier "pris en charge" dans votre logique)
        if cargaison.tampon != "1":
            cargaison.tampon = "1"
        cargaison.etat = "Echantillonner"
        cargaison.save(update_fields=["tampon", "etat"])

    # Build print URL
    print_url = reverse("sampling_report", args=[cargaison.pk])

    return JsonResponse(
        {
            "valid": True,
            "print_url": print_url,
            "idcargaison": cargaison.pk,
            "numrappechauto": echantillon.numrappechauto,
        },
        status=200,
    )



@login_required
def sampling_report_pdf(request, pk: int):
    c = get_object_or_404(
        Cargaison.objects.select_related("importateur", "produit", "entrepot", "voie", "frontiere"),
        pk=pk
    )
    e = Entrepot_echantillon.objects.filter(idcargaison=c).first()

    # Variables
    numrappechauto = e.numrappechauto if e and e.numrappechauto else "—"
    numdos = c.numdos or "—"
    importateur = getattr(c.importateur, "nomimportateur", "") or "—"
    adresseimportateur = getattr(c.importateur, "adresseimportateur", "") or "—"
    dateech = (e.dateechantillonage or c.dateheurecargaison or datetime.now()).strftime("%d/%m/%Y")
    entrepot = getattr(c.entrepot, "nomentrepot", "") or "—"
    matricule = getattr(e, "matricule", "") or "—"
    produit = getattr(c.produit, "nomproduit", "") or "—"
    volume = f"{c.volume:.3f}".rstrip("0").rstrip(".") if c.volume is not None else "—"
    provenance = getattr(c, "provenance", "") or "—"
    voie = getattr(c.voie, "nomvoie", "") or "—"
    immatriculation = c.immatriculation or "—"
    numplombh = ""
    methodeutilisee = getattr(e, "methodeutilisee", "") or "—"
    dateechantillonage = (e.dateechantillonage.strftime("%d/%m/%Y %H:%M") if e and e.dateechantillonage else "—")
    qtelabo = getattr(e, "qte", "") or "—"

    # HTTP response
    filename = f"rapport_echantillonnage_{pk}.pdf"
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'

    # Tighter page margins (less space at top)
    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=8*mm,       # ↓ smaller top margin
        bottomMargin=10*mm
    )
    story = []

    # ---- Compact centered header (logo + multi-line title) ----
    # --- 100% width header: 30% logo (centered) + 70% text (centered) ---
    logo_path = finders.find("Logo_occ_new.png")
    img = Image(logo_path, width=42 * mm, height=42 * mm) if logo_path else Spacer(42 * mm, 42 * mm)

    style_title = ParagraphStyle(
        name="title_main",
        alignment=TA_CENTER,
        fontName=BASE_FONT,
        fontSize=10.6,
        leading=12.6,
        spaceBefore=0,
        spaceAfter=0,
    )

    style_legal = ParagraphStyle(
        name="title_legal",
        alignment=TA_CENTER,
        fontName=BASE_FONT,
        fontSize=8.0,
        leading=10.0,
        spaceBefore=0,
        spaceAfter=0,
    )

    p1 = Paragraph("<b>OFFICE CONGOLAIS DE CONTROLE</b>", style_title)
    p2 = Paragraph(f"<b>RAPPORT D’ECHANTILLONNAGE N° {numrappechauto}</b>", style_title)

    legal_block = Paragraph(
        "Etablissement Public à caractère technique et scientifique créé par Ordonnance-loi n° 74-013 du 10 janvier 1974<br/>"
        "telle que modifiée par le décret n° 09/42 du 03 décembre 2009 fixant ses statuts.<br/>"
        "98, avenue du Port, Kinshasa/Gombe – B.P. 8806 – NIF A0700325M <br/>"
        "E-mail : occ_dg@occ.cd – site Web : www.occ.cd",
        style_legal
    )

    # Right text block (centered), with small gaps
    right_block = Table(
        [
            [p1],
            [Spacer(1, 2)],  # tiny gap between line 1 & 2
            [p2],
            [Spacer(1, 3)],  # tiny gap before legal text
            [legal_block],
        ],
        colWidths=[doc.width * 0.7],
        hAlign="CENTER",
    )
    right_block.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    # Wrap logo in a 1-cell table so we can center it in its 30% column
    logo_cell = Table([[img]], colWidths=[doc.width * 0.3], hAlign="CENTER")
    logo_cell.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    # Two-column header across 100% width: 30% + 70%, both centered
    header_table = Table(
        [[logo_cell, right_block]],
        colWidths=[doc.width * 0.3, doc.width * 0.7],
        hAlign="CENTER",
    )
    header_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "CENTER"),  # logo column centered
        ("ALIGN", (1, 0), (1, 0), "CENTER"),  # text column centered
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    # Minimal top whitespace; subtle gap after header
    story.append(Spacer(1, 2))
    story.append(header_table)
    story.append(Spacer(1, 10))


    # ---- First line (dossier / importateur / date) ----
    line1_tbl = Table(
        [[
            _p(f"<b>N° DOSSIER: {numdos}</b>", size=12),
            _p(f"<b>Imp. Entité: {importateur}</b>", size=12),
            _p(f"<b>Le {dateech}</b>", size=12, align="CENTER"),
        ]],
        colWidths=[45*mm, 85*mm, 45*mm],
        hAlign="CENTER"
    )
    line1_tbl.setStyle(TableStyle([
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
    ]))
    story.append(line1_tbl)
    story.append(Spacer(1, 10))

    # ---- Body ----
    story.append(
        _p(f"Conformément aux dispositions légales, nous avons procédé dans les installations de <b>{entrepot}</b> au prélèvement d’échantillons.", size=12)
    )
    story.append(Spacer(1, 6))

    story.append(_section_title("Agent échantillonneur"))
    story.append(Spacer(1, 2))
    story.append(_p("Noms & post-noms : <b></b>", size=12))
    story.append(_p("N° de Téléphone : <b></b>", size=12))
    story.append(_p(f"Matricule : <b>{matricule}</b>", size=12))
    story.append(Spacer(1, 6))

    story.append(_section_title("Client"))
    story.append(Spacer(1, 2))
    story.append(_p(f"Noms : <b>{importateur}</b>", size=12))
    story.append(_p("Qualité : <b>IMPORTATEUR</b>", size=12))
    story.append(_p(f"Adresse : <b>{adresseimportateur}</b>", size=12))
    story.append(Spacer(1, 6))

    story.append(_section_title("Marchandise"))
    story.append(Spacer(1, 2))
    story.append(_p("Nature de la marchandise : <b>PRODUIT PETROLIER</b>", size=12))
    story.append(_p(f"Marque du produit : <b>{produit}</b>", size=12))
    story.append(_p(f"Quantité de la marchandise : <b>{volume} m<super>3</super></b>", size=12))
    story.append(_p(f"Pays d'origine/de provenance : <b>{provenance}</b>", size=12))
    story.append(_p("Nombre de LT : <b>1</b>", size=12))
    story.append(_p(f"Arrivée par : <b>VOIE {voie}</b>  dans : <b>{immatriculation}</b>", size=12))
    story.append(_p("Type d'emballage : <b>BOITE METALLIQUE</b>", size=12))
    story.append(_p(f"Nombres de plombs : <b></b> N° <b>{numplombh}</b>", size=12))
    story.append(_p(f"Méthodes d'échantillonnage utilisées : <b>{methodeutilisee}</b>", size=12))
    story.append(_p(f"Date et Heure d'échantillonnage : <b>Le {dateechantillonage}</b>", size=12))
    story.append(_p("Date et Heure d'expédition au Laboratoire : <b></b>", size=12))
    story.append(_p(f"Nombre de produit remis au Laboratoire : <b>{qtelabo} L</b>", size=12))

    doc.build(story)
    return response




# Gestion des echantillonages
class GestionEchantillonage():

    @login_required(login_url='login')
    def c1(request):
        user = request.user
        id = user.id
        today = date.today()
        request.session['url'] = request.get_full_path()
        role = user.role_id
        form = Echantilloner(request.POST or None)

        if role == 1 or role == 3 or role == 9:
            qs = Cargaison.objects.filter(
                Q(etat="En attente d'echantillonage") | Q(tampon='0') | Q(etat="En attente requisition")).filter(
                entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
            table = EchantillonTable(qs, prefix="1_")
            RequestConfig(request, paginate={"per_page": 12}).configure(table)

            # #Compteur de la page principale de l'entrepot
            n = Cargaison.objects.filter(
                Q(etat='En attente requisition') | Q(tampon='0') | Q(etat="En attente d'echantillonage")).filter(
                entrepot__affectationentrepot__username_id=id).count()

            d = Cargaison.objects.filter(
                Q(etat='En attente de dechargement') | Q(Q(etat='Conforme aux exigences'))).filter(
                entrepot__affectationentrepot__username_id=id).count()

            r = Cargaison.objects.filter(Q(etat='En attente requisition') | Q(tampon='0')).filter(
                entrepot__affectationentrepot__username_id=id).count()

            o = Cargaison.objects.filter(Q(etat='En attente de dechargement') | Q(etat='Conforme aux exigences'),
                                         entrepot__affectationentrepot__username_id=id).count()

            x = Entrepot_echantillon.objects.filter(
                Q(nonConformiteProduit=True) | Q(idcargaison__controlOrganoleptique=True),
                idcargaison__entrepot__affectationentrepot__username_id=id).count()

            return render(request, 'entrepot.html', {
                'cargaison': table,
                'n': n,
                'd': d,
                'r': r,
                'o': o,
                'x': x,
                'form': form,
            })
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def c2(request):
        user = request.user
        id = user.id
        today = date.today()
        role = user.role_id
        form = Echantilloner(request.POST or None)

        request.session['url'] = request.get_full_path()
        if role == 1 or role == 3 or role == 9:

            table = EchantillonTable(Cargaison.objects.filter(Q(etat='En attente requisition') | Q(tampon='0')).filter(
                entrepot__affectationentrepot__username_id=id,
                dateheurecargaison__date=today).order_by('-dateheurecargaison'))

            RequestConfig(request, paginate={"per_page": 20}).configure(table)

            # #Compteur de la page principale de l'entrepot
            n = Cargaison.objects.filter(
                Q(etat='En attente requisition') | Q(tampon='0') | Q(etat="En attente d'echantillonage")).filter(
                entrepot__affectationentrepot__username_id=id).count()

            d = Cargaison.objects.filter(
                Q(etat='En attente de dechargement') | Q(Q(etat='Conforme aux exigences'))).filter(
                entrepot__affectationentrepot__username_id=id).count()
            # d = Cargaison.objects.filter(Q(etat='En attente de dechargement')|Q(Q(etat='Conforme aux exigences'))).filter(entrepot__affectationentrepot__username_id=id,  dateheurecargaison__lte=today, dateheurecargaison__gt=today-datetime.timedelta(days=90)).count()

            r = Cargaison.objects.filter(Q(etat='En attente requisition') | Q(tampon='0')).filter(
                entrepot__affectationentrepot__username_id=id).count()

            o = Cargaison.objects.filter(Q(etat='En attente de dechargement') | Q(etat='Conforme aux exigences'),
                                         entrepot__affectationentrepot__username_id=id).count()

            x = Entrepot_echantillon.objects.filter(
                Q(nonConformiteProduit=True) | Q(idcargaison__controlOrganoleptique=True),
                idcargaison__entrepot__affectationentrepot__username_id=id).count()

            return render(request, 'entrepot.html', {
                'cargaison': table,
                'n': n,
                'd': d,
                'r': r,
                'o': o,
                'x': x,
                'form': form,
            })
        else:
            return redirect('logout')

    # Methodes permettant d'effectuer l'echantillonage
    @login_required(login_url='login')
    def echantilloner(request):
        # Getting Logged in user detail for filtering
        user = request.user
        id = user.id
        role = user.role_id
        form = Echantilloner(request.POST or None)

        # Getting current Year & Month
        today = date.today()
        month = today.month
        year = today.year

        # Saving current URL Path in session Variable
        url = request.session['url']
        if role == 3 or role == 1 or role == 9:
            if request.is_ajax():
                pk = request.POST.get('pk', None)
                numrappech = request.POST.get('numrappech', None)
                numplombh = request.POST.get('numplombh', None)
                numplombb = request.POST.get('numplombb', None)
                numplombbr = request.POST.get('numplombbr', None)
                numplombaph = request.POST.get('numplombaph', None)
                etatphysique = request.POST.get('etatphysique', None)
                qte = request.POST.get('qte', None)
                conformite = request.POST.get('conformite', None)
                dateechantillonage = request.POST.get('dateechantillonage', None)
                numdossier = request.POST.get('numdossier', None)
                codecargaison = request.POST.get('codecargaison', None)
                c = Cargaison.objects.get(idcargaison=pk)

                if dateechantillonage == '' or numdossier == '' or numrappech == '' or numplombh == '' or qte == '' or conformite == '':
                    return JsonResponse({'error': form.errors}, status=400)

                # Test pour savoir si le laboratoire a deja pris en charge lechantillon
                if c.tampon == "1":
                    c.etat = "Echantillonner"
                    c.numdossier = numdossier
                    c.codecargaison = codecargaison
                    c.save(update_fields=['etat', 'numdossier', 'codecargaison'])
                    p = Entrepot_echantillon(idcargaison=c, numrappech=numrappech, numplombh=numplombh,
                                             numplombb=numplombb, numplombbr=numplombbr, numplombaph=numplombaph,
                                             etatphysique=etatphysique, qte=qte, conformite=conformite,
                                             dateechantillonage=dateechantillonage)
                    p.save()
                    response = {'valid': True}
                    return JsonResponse(response, status=200)
                else:
                    c.tampon = "1"
                    c.numdossier = numdossier
                    c.codecargaison = codecargaison
                    c.save(update_fields=['tampon', 'numdossier', 'codecargaison'])
                    p = Entrepot_echantillon.objects.get(idcargaison=pk)
                    p.numrappech = numrappech
                    p.numplombh = numplombh
                    p.numplombb = numplombb
                    p.numplombbr = numplombbr
                    p.numplombaph = numplombaph
                    p.etatphysique = etatphysique
                    p.qte = qte
                    p.conformite = conformite
                    p.save(update_fields=['numplombh', 'numrappech', 'numplombb', 'numplombbr', 'numplombaph',
                                          'etatphysique', 'qte', 'conformite'])
                    response = {'valid': True}
                    return JsonResponse(response, status=200)

        else:
            return redirect('logout')

    # Recherche par qrcode En attente d'echantillonnage
    @login_required(login_url='login')
    def rechercheqrcode(request):
        # Getting Logged in user detail for filtering
        user = request.user
        id = user.id
        role = user.role_id

        # Getting current Year & Month
        today = date.today()
        month = today.month
        year = today.year

        form = Echantilloner(request.POST or None)

        if role == 3 or role == 1 or role == 9:
            q = request.GET.get('q')
            if q:
                qs = Cargaison.objects.filter(etat="En attente requisition").filter(
                    entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
                qs1 = Cargaison.objects.filter(etat="En attente d'echantillonage", qrcode=q).filter(
                    entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
                qs2 = Cargaison.objects.filter(entrepot__affectationentrepot__username_id=id).filter(
                    Q(rapechctrl=1) | Q(etat="Echantillonner")).order_by('-dateheurecargaison')
                table = EchantillonTable(qs1, prefix="1_")
                table1 = CargaisonEnAttenteRequisition(qs, prefix="2_")
                table2 = RapportEchantillonage(qs2, prefix='3_')
                RequestConfig(request, paginate={"per_page": 7}).configure(table)
                RequestConfig(request, paginate={"per_page": 10}).configure(table1)
                RequestConfig(request, paginate={"per_page": 5}).configure(table2)

                # #Compteur de la page principale de l'entrepot
                n = Cargaison.objects.filter(
                    Q(etat='En attente requisition') | Q(tampon='0') | Q(etat="En attente d'echantillonage")).filter(
                    entrepot__affectationentrepot__username_id=id, dateheurecargaison__date=today).count()
                d = Cargaison.objects.filter(
                    Q(etat='En attente de dechargement') | Q(Q(etat='Conforme aux exigences'))).filter(
                    entrepot__affectationentrepot__username_id=id).count()
                r = Cargaison.objects.filter(Q(etat='En attente requisition') | Q(tampon='0')).filter(
                    entrepot__affectationentrepot__username_id=id).count()
                o = Cargaison.objects.filter(Q(etat='En attente de dechargement') | Q(etat='Conforme aux exigences'),
                                             entrepot__affectationentrepot__username_id=id).count()
                x = Cargaison.objects.filter(etat='Cargaison dechargee',
                                             entrepot__affectationentrepot__username_id=id).count()

                return render(request, 'entrepot.html', {
                    'cargaison': table,
                    'cargaison1': table1,
                    'cargaison2': table2,
                    'form': form,
                    'n': n,
                    'd': d,
                    'r': r,
                    'o': o,
                    'x': x,
                })
        else:
            return redirect('logout')

    # Rechercher RE
    # Recherche par qrcode En attente d'echantillonnage
    @login_required(login_url='login')
    def rechercherre(request):
        # Getting Logged in user detail for filtering
        user = request.user
        id = user.id
        role = user.role_id

        # Getting current Year & Month
        today = date.today()
        month = today.month
        year = today.year

        form = Echantilloner(request.POST or None)

        if role == 3 or role == 1 or role == 9:
            q = request.GET.get('q')
            if q:
                qs = Cargaison.objects.filter(etat="En attente requisition").filter(
                    entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
                qs1 = Cargaison.objects.filter(etat="En attente d'echantillonage").filter(
                    entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
                qs2 = Cargaison.objects.filter(entrepot__affectationentrepot__username_id=id).filter(
                    Q(rapechctrl=1) | Q(etat="Echantillonner"), qrcode=q).order_by('-dateheurecargaison')
                table = EchantillonTable(qs1, prefix="1_")
                table1 = CargaisonEnAttenteRequisition(qs, prefix="2_")
                table2 = RapportEchantillonage(qs2, prefix='3_')
                RequestConfig(request, paginate={"per_page": 7}).configure(table)
                RequestConfig(request, paginate={"per_page": 10}).configure(table1)
                RequestConfig(request, paginate={"per_page": 5}).configure(table2)

                # #Compteur de la page principale de l'entrepot
                n = Cargaison.objects.filter(
                    Q(etat='En attente requisition') | Q(tampon='0') | Q(etat="En attente d'echantillonage")).filter(
                    entrepot__affectationentrepot__username_id=id, dateheurecargaison__date=today).count()
                d = Cargaison.objects.filter(
                    Q(etat='En attente de dechargement') | Q(Q(etat='Conforme aux exigences'))).filter(
                    entrepot__affectationentrepot__username_id=id).count()
                r = Cargaison.objects.filter(Q(etat='En attente requisition') | Q(tampon='0')).filter(
                    entrepot__affectationentrepot__username_id=id).count()
                o = Cargaison.objects.filter(Q(etat='En attente de dechargement') | Q(etat='Conforme aux exigences'),
                                             entrepot__affectationentrepot__username_id=id).count()
                x = Cargaison.objects.filter(etat='Cargaison dechargee',
                                             entrepot__affectationentrepot__username_id=id).count()

                return render(request, 'entrepot.html', {
                    'cargaison': table,
                    'cargaison1': table1,
                    'cargaison2': table2,
                    'form': form,
                    'n': n,
                    'd': d,
                    'r': r,
                    'o': o,
                    'x': x,
                })
        else:
            return redirect('logout')


# Class de gestion de dechargement
class GestionDechargement():
    # Methode d'affichage du tableau de dechargement
    @login_required(login_url='login')
    def tableaudechargement(request):
        # Getting Logged in user detail for filtering
        user = request.user
        role = user.role_id
        form = MeterAfter()
        template = 'entrepot_dechargement.html'

        if role == 3 or role == 1:
            context = {'form': form}
            return render(request, template, context)
        else:
            return redirect('logout')

    @login_required(login_url='login')
    def tableauDechargementResponse(request):
        # Getting Logged in user detail for filtering
        user = request.user
        id = user.id
        role = user.role_id

        if role == 3 or role == 1:
            qs = Cargaison.objects.filter(
                etat='Conforme aux exigences',
                impressionresultat__isConforme=1,
                entrepot__affectationentrepot__username_id=id,
            ).values(
                'idcargaison',
                'dateheurecargaison__date',
                'importateur__nomimportateur',
                'immatriculation',
                'numdos',
                'produit__nomproduit',
            ).order_by(
                '-impressionresultat__printDate'
            )

            # Number of items to show per page
            items_per_page = 8

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

        else:
            return redirect('logout')


@login_required(login_url='login')
def impressionRe(request, pk):
    # Generer le rapport d'echantillonage
    c = Cargaison.objects.get(idcargaison=pk)
    template = 'rapportechantillonage.html'
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


@login_required(login_url='login')
def impressionRapport(request, pk):
    user = request.user.id
    ville = AffectationVille.objects.get(username_id=user)
    ville = ville.ville_id
    province = Ville.objects.get(idville=ville)
    province = province.province
    province = province.upper()

    template = 'rapport.html'
    #
    # pk = request.session['id']

    # Request to fecth data into database
    cargaison = Cargaison.objects.get(idcargaison=pk)

    if cargaison.numCertInspection == None:
        numCertInspection = num_cert_inspection(ville)
        cargaison.numCertInspection = numCertInspection
        cargaison.save(update_fields=['numCertInspection'])
    else:
        numCertInspection = cargaison.numCertInspection

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
    govTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('gov', flat=True)), 3))  # gov Total Tanker
    gsvTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('gsv', flat=True)), 3))  # gsv Total Tanker
    mtaTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('mta', flat=True)), 3))  # mta Total Tanker
    mtvTotal = '{0:.3f}'.format(round(sum(compartiment.values_list('mtv', flat=True)), 3))  # mtv Total Tanker

    densite = densite15(inspection.temp, inspection.dens)  # densite 15c
    govMeter = round((inspection.meterafter - inspection.meterbefore) / 1000, 3)  # govmeter
    vcfMeter = vcf(densite, inspection.temp)  # vcfMeter
    gsvMeter = gsv(vcfMeter, govMeter)  # gsvMeter
    mtaMeter = mta(gsvMeter, densite)  # mta Meter

    govLt = float(cargaison.volume)  # gov LT
    vcfLt = vcf(densite, inspection.temp)  # VCF LT
    gsvLt = (cargaison.volume15)  # GSV LT
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

    govLtTanker = round((govLt - float(govTotal)), 3)  # Difference LT/Tanker
    gsvLtTanker = round((float(gsvLt) - float(gsvTotal)), 3)  # Difference GSV LT/Tanker
    mtvLtTanker = round((float(mtvLt) - float(mtvTotal)), 3)  # Difference mtv LT/Tanker
    mtaLtTanker = round((float(mtaLt) - float(mtaTotal)), 3)  # Difference mtv LT/Tanker
    prLtTanker = round((govLtTanker * 100) / govLt, 3)
    if gsvLt == 0:
        gsvLt = 1
    prGsvLtTanker = round((gsvLtTanker * 100) / float(gsvLt), 3)
    if mtaLt == 0:
        mtaLt = 1
    prMtaLtTanker = round((mtaLtTanker / (float(mtaLt)) * 100), 3)
    if mtvLt == 0:
        mtvLt = 1
    prMtvLtTanker = round((mtvLtTanker / (float(mtvLt)) * 100), 3)

    govTankerMeter = float(govTotal) - float(govMeter)  # Difference Tanker/Meter
    gsvTankerMeter = float(gsvTotal) - float(gsvMeter)  # Difference GSV Tanker/Meter
    mtaTankerMeter = round((float(mtaTotal) - mtaMeter), 3)  # Difference MTA Tanker/Meter
    prTankerMeter = round((govTankerMeter * 100) / float(govTotal), 3)

    govLtMeter = govLt - govMeter  # Diff LT/Meter
    gsvLtMeter = round((float(gsvLt) - gsvMeter), 3)  # Diff GSV LT/Meter
    mtaLtMeter = float(mtaLt) - mtaMeter  # Diff mta LT/Meter
    if govLt == 0:
        govLt = 1
    prLtMeter = round((govLtMeter * 100) / govLt, 3)
    if gsvLt == 0:
        gsvLt = 1
    prGsvLtMeter = round((gsvLtMeter * 100) / float(gsvLt), 3)
    if mtaLt == 0:
        mtaLt = 1
    prMtaLtMeter = round((mtaLtMeter * 100) / float(mtaLt), 3)

    # Certified Quantity
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

    fraisOcc = round((11 * float(gsvMax)), 3)  # Frais occ a Payer

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
        'province': province,
        'numCertInspection': numCertInspection,
        'inspection': inspection,
        'densite': densite,
        'prGsvLtTanker': prGsvLtTanker,
        'prMtaLtTanker': prMtaLtTanker,
        'prMtvLtTanker': prMtvLtTanker,
        'prGsvLtMeter': prGsvLtMeter,
        'prMtaLtMeter': prMtaLtMeter,
        'prLtTanker': prLtTanker,
        'prTankerMeter': prTankerMeter,
        'prLtMeter': prLtMeter,
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

    }
    # Render PDF Files
    pdf = render_to_pdf(template, data)
    return HttpResponse(pdf, content_type='application/pdf')


@login_required(login_url='login')
def echantillonage(request):
    # Getting Logged in user detail for filtering
    user = request.user
    id = user.id
    role = user.role_id

    # Getting current Year & Month
    today = datetime.datetime.now()
    # template = 'form.html'
    # # form = Echantilloner()

    if request.method == 'POST':
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            pk = request.POST.get('pk', None)
            matricule = request.POST.get('matricule', None)
            methodeutilisee = request.POST.get('methodeutilisee', None)
            qte = request.POST.get('qte', None)

            c = Cargaison.objects.get(idcargaison=pk)
            ville = c.entrepot.ville
            print(ville)
            numrappech = numRappEch(pk,
                                    ville)  # Generation automatique du numero de rapport d'achentillonnage / ville et annuel
            numrappechauto = numrappech
            c.rapechctrl = 1
            c.etatInspection = 1
            c.etat = "Echantillonner"
            c.save(update_fields=['etat', 'rapechctrl', 'etatInspection'])

            e = Entrepot_echantillon(idcargaison=c, numrappechauto=numrappechauto, matricule=matricule,
                                     methodeutilisee=methodeutilisee, qte=qte, dateechantillonage=today)
            e.save()

            UserActivityLog.objects.create(
                user=user,
                action="Sample Data creation",
                description=f"User has created a new sampling record for {c.idcargaison} successfully",
            )

            # Generer le rapport d'echantillonage
            template = 'rapportechantillonage.html'
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
            pdf_base64 = base64.b64encode(pdf.getvalue()).decode('utf-8')
            return JsonResponse({'status': 'success', 'pdf_base64': pdf_base64})
        else:
            return redirect('entrepot')
    else:
        return redirect('entrepot')


@login_required(login_url='login')
def view_pdf(request):
    # Get PDF data from cache
    pdf_data = cache.get('pdf_data')

    # Return PDF as response
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    return response


@login_required(login_url='login')
def rapportechantillonage(request, pk: int):
    template = "rapportechantillonage.html"

    # Load Cargaison and true relations (no CountryField in select_related)
    c = get_object_or_404(
        Cargaison.objects.select_related(
            "importateur", "produit", "entrepot", "voie", "frontiere"
        ),
        idcargaison=pk,
    )

    # Sampling record may be missing
    e = Entrepot_echantillon.objects.filter(idcargaison=pk).first()

    # --- datetime helpers (handle naive or aware) ---------------------------
    def _to_local(dt):
        """Return a timezone-aware, localized datetime (or None)."""
        if not dt:
            return None
        if timezone.is_naive(dt):
            # Make it aware in the current timezone; fallback to UTC if anything odd
            try:
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            except Exception:
                dt = timezone.make_aware(dt, timezone.utc)
        return timezone.localtime(dt)

    def _fmt_date(dt, with_time=False):
        d = _to_local(dt)
        if not d:
            return "—"
        return d.strftime("%d/%m/%Y %H:%M" if with_time else "%d/%m/%Y")

    # CountryField -> human name
    try:
        provenance_name = (c.provenance.name or "—") if c.provenance else "—"
    except Exception:
        provenance_name = getattr(c, "get_provenance_display", lambda: "—")() or "—"

    adresse_import = (
        getattr(c.importateur, "adresseimportateur", None)
        or Importateur.objects.filter(idimportateur=c.importateur_id)
           .values_list("adresseimportateur", flat=True)
           .first()
        or "—"
    )

    data = {
        "dateechantillonage": e.dateechantillonage if e else None,
        "dateech": _fmt_date(e.dateechantillonage if e else c.dateheurecargaison),
        "entrepot": getattr(c.entrepot, "nomentrepot", "—") or "—",
        "numdos": c.numdos or "—",
        "importateur": getattr(c.importateur, "nomimportateur", "—") or "—",
        "adresseimportateur": adresse_import,
        "declarant": getattr(c, "declarant", "—") or "—",
        "produit": getattr(c.produit, "nomproduit", "—") or "—",
        "volume": c.volume if c.volume is not None else "—",
        "provenance": provenance_name,
        "voie": getattr(getattr(c, "voie", None), "nomvoie", "—") or "—",
        "immatriculation": c.immatriculation or "—",
        "qtelabo": getattr(e, "qte", "—") if e else "—",
        "numplombh": getattr(e, "numplombh", "—") if e else "—",
        "numrappechauto": getattr(e, "numrappechauto", "—") if e else "—",
        "dateechantillonage_h": _fmt_date(e.dateechantillonage, with_time=True) if e else "—",
    }

    pdf = render_to_pdf(template, data)
    if not pdf:
        raise Http404("Impossible de générer le rapport.")
    return HttpResponse(pdf, content_type="application/pdf")



@login_required(login_url='login')
def impressionCert(request, pk):
    user = request.user
    id = user.id
    ville = AffectationVille.objects.get(username_id=id)
    ville = ville.ville_id
    province = Ville.objects.get(idville=ville)
    province = province.province
    province = province.upper()
    role = user.role_id
    url = request.session['url']
    if role == 3 or role == 9 or role == 1:

        # td = datetime.today()
        # today = td.date()

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
        provenance = a.provenance.name
        qte = b.qte
        datereceptionlabo = c.datereceptionlabo
        codelabo = c.codelabo
        numdossier = a.numdos
        immatriculation = a.immatriculation
        numrappech = b.numrappech

        # Putting printing counter to 1
        # a.impression = "1"
        # a.save(update_fields=['impression'])

        # Saving print date into DBS  a ameliorer
        # d.dateimpression = today
        # d.save(update_fields=['dateimpression'])
        # dateimpression = d.dateimpression

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
                # 'dateimpression': dateimpression,
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
                'annee': annee,
                'province': province,
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
                    # 'dateimpression': dateimpression,
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
                    'annee': annee,
                    'province': province,
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
                        # 'dateimpression': dateimpression,
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
                        'annee': annee,
                        'province': province,
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
                            # 'dateimpression': dateimpression,
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
                            'annee': annee,
                            'province': province,
                        }

                        # Rendered PDF report
                        pdf = render_to_pdf(template, data)
                        return HttpResponse(pdf, content_type='application/pdf')
                    else:
                        return redirect('logout')
    else:
        return redirect('logout')


# Seals Inspections
@login_required(login_url='login')
def choiceoftype(request, pk):
    template = 'choicetype.html'
    form = PreInspectionForm1(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            meter = form.cleaned_data['meter']
            tanker = form.cleaned_data['tanker']
            shore = form.cleaned_data['shore']

            # Test pour affichage des formulaires correspondant
            if meter is False:
                if tanker is False:
                    if shore is False:
                        template = 'error.html'
                        context = {}
                        return render(request, template, context)  # Meter=0,Tanker=0,Shore=0
                    else:
                        return redirect('shore', pk=pk)  # Meter=0,Tanker=0,Shore=1
                else:
                    if shore is False:
                        return redirect('seals', pk=pk)  # Meter=0,Tanker=1,Shore=0
                    else:
                        return HttpResponseBadRequest  # Meter=0,Tanker=1,Shore=1
            else:
                if tanker is False:
                    if shore is False:
                        return redirect('seals', pk=pk)  # Meter=1,Tanker=0,Shore=0
                    else:
                        return redirect('shore', pk=pk)  # Meter=1,Tanker=0,Shore=1
                else:
                    if shore is False:
                        return redirect('seals', pk=pk)  # Meter=1,Tanker=1,Shore=0
                    else:
                        return HttpResponseBadRequest  # Meter=1,Tanker=1,Shore=1
    else:
        context = {'form': form}
        return render(request, template, context)


@login_required(login_url='login')
def seals(request, pk):
    template = 'formPreInspection1.html'
    cargaison = Cargaison.objects.get(idcargaison=pk)
    form = SealInspection(request.POST or None)
    request.session['id'] = pk

    if request.method == 'POST':
        if form.is_valid():
            form = form.save(commit=False)
            form.idcargaison = cargaison
            form.save()
            return redirect('seal-details', pk=form.id)
        else:
            template = "partials/sealinspection.html"
            return render(request, template, {'form': form})

    context = {
        "form": form,
        "cargaison": cargaison,
        # "seals":seals,
    }
    return render(request, template, context)


@login_required(login_url='login')
def sealinspection(request):
    template = 'partials/sealinspection.html'
    form = SealInspection()
    context = {
        "form": form
    }
    return render(request, template, context)


@login_required(login_url='login')
def detailseals(request, pk):
    template = 'partials/sealdetails.html'
    seals = InspectionSeal.objects.get(id=pk)
    context = {"seals": seals}
    return render(request, template, context)


@login_required(login_url='login')
def sealsdelete(request, pk):
    seal = InspectionSeal.objects.get(pk=pk)
    seal.delete()
    return HttpResponse()


@login_required(login_url='login')
def updateseals(request, pk):
    template = 'partials/sealinspection.html'
    seal = InspectionSeal.objects.get(pk=pk)
    form = SealInspection(request.POST or None, instance=seal)

    if request.method == "POST":
        if request.method == 'POST':
            if form.is_valid():
                form = form.save()
                return redirect('seal-details', pk=form.id)

    context = {
        "form": form,
        "seal": seal,
    }
    return render(request, template, context)


@login_required(login_url='login')
def tankerinspection(request):
    pk = request.session['id']
    template = 'tankerInspection.html'
    cargaison = Cargaison.objects.get(idcargaison=pk)
    form = TankerInspection(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            # produit = request.POST['produit']
            # produit = Produit.objects.get(idproduit=produit)
            dens = request.POST['dens']
            temp = request.POST['temp']
            innagein = request.POST['innagein']
            if innagein == '':
                innagein == 'N/A'
            volumein = request.POST['volumein']
            tempin = request.POST['tempin']
            weightin = request.POST['weightin']
            # # meterbefore = request.POST['meterbefore']
            # if meterbefore == '':
            #     meterbefore = 0
            try:
                data = Inspection(idcargaison=cargaison, dens=dens, temp=temp, innagein=innagein, volumein=volumein,
                                  tempin=tempin, weightin=weightin)
                data.save()
            except:
                data = Inspection.objects.get(idcargaison=cargaison)
                data.dens = dens
                data.temp = temp
                data.innagein = innagein
                data.volumein = volumein
                data.tempin = tempin
                data.weightin = weightin
                data.save(update_fields=['dens', 'temp', 'innagein', 'volumein', 'tempin', 'weightin'])
            return redirect('compartiment', pk=pk)
    else:
        context = {'form': form}
        return render(request, template, context)


@login_required(login_url='login')
def compartiment(request, pk):
    template = 'formCompartiment1.html'
    inspection = Inspection.objects.get(idcargaison=pk)
    form = CompartimentInspection(request.POST or None)
    request.session['id'] = pk

    if request.method == 'POST':
        if form.is_valid():
            form = form.save(commit=False)

            t = request.POST['tempcomp']  # Temperature du compartiment
            govCompart = request.POST['gov']  # Gov du compartiment

            # calcul des valeurs d'inspection
            # Recuperation des valeurs pour calcul de la densite a 15
            densite = inspection.dens
            temperature = inspection.temp
            d = densite15(temperature, densite)  # Calcul Dens a 15

            v = vcf(d, t)  # VCF
            g = gsv(v, govCompart)  # GSV
            m = mtv(g, d)  # MTV
            a = mta(g, d)  # MTA

            # Recuperation des donnees des calculs
            form.gsv = g
            form.mtv = m
            form.mta = a
            form.vcf = v
            form.idinspection = inspection

            form.save()
            return redirect('compartiment-details', pk=form.id)
        else:
            template = "partials/compartimentinspection.html"
            return render(request, template, {'form': form})

    context = {
        "form": form,
        "cargaison": inspection,
        # "seals":seals,
    }
    return render(request, template, context)


@login_required(login_url='login')
def compartimentinspection(request):
    template = 'partials/compartimentinspection.html'
    form = CompartimentInspection()
    context = {
        "form": form
    }
    return render(request, template, context)


@login_required(login_url='login')
def detailscompartiment(request, pk):
    template = 'partials/compartimentdetails.html'
    compartiment = Compartiment.objects.get(id=pk)
    context = {"compartiment": compartiment}
    return render(request, template, context)


@login_required(login_url='login')
def compartimentdelete(request, pk):
    compartement = Compartiment.objects.get(pk=pk)
    compartement.delete()
    return HttpResponse()


@login_required(login_url='login')
def updatecompartiment(request, pk):
    template = 'partials/compartimentinspection.html'
    compartiment = Compartiment.objects.get(pk=pk)
    form = CompartimentInspection(request.POST or None, instance=compartiment)

    if request.method == "POST":
        if request.method == 'POST':
            if form.is_valid():
                form = form.save()
                return redirect('compartiment-details', pk=form.id)

    context = {
        "form": form,
        "compartiment": compartiment,
    }
    return render(request, template, context)


@login_required(login_url='login')
def meterafter(request):
    if request.method == 'POST':
        idcargaison = request.POST['idcargaison']
        meterafter = request.POST['meterafter']
        meterbefore = request.POST['meterbefore']
        # print('TEST')
        # print(idcargaison)
        # print(meterbefore)

        try:
            cargaison = Cargaison.objects.get(idcargaison=idcargaison)
            inspection = Inspection.objects.get(idcargaison=cargaison)

            if meterbefore == '':
                meterbefore = 0
            if meterafter == '':
                meterafter = 0

            inspection.meterafter = meterafter
            inspection.save(update_fields=['meterafter', 'meterbefore'])
            cargaison.etat = 'Cargaison dechargee'
            cargaison.dateDechargement = datetime.datetime.today()

            UserActivityLog.objects.create(
                user=request.user,
                action="Offload of the Truck",
                description=f"User has confirmed the offload of the Truck for the record  {cargaison.idcargaison}",
            )

            cargaison.save(update_fields=['etat', 'dateDechargement'])
            return JsonResponse({'status': 'success'})

        except ObjectDoesNotExist:
            return JsonResponse({'status': 'error',
                                 'message': "Erreur! La cargaison sélectionnée n'a encore fait l'objet d'aucune inspection"})

    return redirect('dechargement')


@login_required(login_url='login')
def shoreinspection(request, pk):
    # pk = request.session['id']
    template = 'shoreInspectionForm.html'
    cargaison = Cargaison.objects.get(idcargaison=pk)
    try:
        Inspection.objects.get(idcargaison_id=cargaison)
        print("OK")
        return redirect('shore-inspection-after', pk=pk)
    except:
        form = ShoreInspection(request.POST or None)
        if request.method == 'POST':
            if form.is_valid():
                produit = request.POST['produit']
                produit = Produit.objects.get(idproduit=produit)
                innagein = request.POST['innagein']
                volumein = request.POST['volumein']
                tempin = request.POST['tempin']
                weightin = request.POST['weightin']
                data = Inspection(idcargaison=cargaison, produit=produit, innagein=innagein,
                                  volumein=volumein, tempin=tempin, weightin=weightin)
                data.save()
                return redirect('shore-inspection', pk=pk)
        else:
            context = {'form': form}
            return render(request, template, context)


@login_required(login_url='login')
def shoretankbefore(request, pk):
    template = 'ShoreInspection.html'
    inspection = Inspection.objects.get(idcargaison=pk)
    cargaison = Cargaison.objects.get(idcargaison=pk)
    form = ShoreInspectionBefore(request.POST or None)
    request.session['id'] = pk

    if request.method == 'POST':
        if form.is_valid():
            form = form.save(commit=False)
            form.idinspection = inspection
            form.save()
            # Update fields to show that this shore has passed the before inspection
            cargaison.before = 1
            cargaison.save(update_fields=['before'])

            return redirect('shore-details', pk=form.id)
        else:
            template = "partials/shoreinspection.html"
            return render(request, template, {'form': form})

    context = {
        "form": form,
        "cargaison": cargaison,
    }
    return render(request, template, context)


@login_required(login_url='login')
def shoretankafter(request, pk):
    template = 'ShoreInspectionAfter.html'
    cargaison = Cargaison.objects.get(idcargaison=pk)
    inspection = Inspection.objects.get(idcargaison=cargaison)
    form = ShoreInspectionAfter(request.POST or None)
    request.session['id'] = pk

    if request.method == 'POST':
        if form.is_valid():
            tankdenomafter = request.POST['tankdenomafter']
            prodinnageafter = request.POST['prodinnageafter']
            fwdeepafter = request.POST['fwdeepafter']
            govafter = request.POST['govafter']
            tempafter = request.POST['tempafter']
            densityafter = request.POST['densityafter']

            a = ShoreTank.objects.get(idinspection=inspection)
            a.tankdenomafter = tankdenomafter
            a.prodinnageafter = prodinnageafter
            a.fwdeepafter = fwdeepafter
            a.govafter = govafter
            a.tempafter = tempafter
            a.densityafter = densityafter

            a.save(update_fields=['tankdenomafter', 'prodinnageafter', 'prodinnageafter', 'fwdeepafter', 'govafter',
                                  'tempafter', 'densityafter'])
            # Update fields to show that this shore has passed the before inspection
            cargaison.after = 1
            cargaison.save(update_fields=['after'])

            return redirect('shore-details-after', pk=form.id)
        else:
            template = "partials/shoreinspection.html"
            return render(request, template, {'form': form})

    context = {
        "form": form,
        "cargaison": cargaison,
    }
    return render(request, template, context)


@login_required(login_url='login')
def shore(request):
    template = 'partials/shoreinspection.html'
    form = ShoreInspectionBefore()
    context = {
        "form": form
    }
    return render(request, template, context)


@login_required(login_url='login')
def shoreafter(request):
    template = 'partials/shoreinspectionafter.html'
    form = ShoreInspectionAfter()
    context = {
        "form": form
    }
    return render(request, template, context)


@login_required(login_url='login')
def shoredetails(request, pk):
    # print(pk)
    template = 'partials/shoredetails.html'
    shore = ShoreTank.objects.get(id=pk)
    context = {"shore": shore}
    return render(request, template, context)


@login_required(login_url='login')
def shoredetailsafter(request, pk):
    # print(pk)
    template = 'partials/shoredetailsafter.html'
    shore = ShoreTank.objects.get(id=pk)
    context = {"shore": shore}
    return render(request, template, context)


@login_required(login_url='login')
def shoredelete(request, pk):
    shore = Shore.objects.get(pk=pk)
    shore.delete()
    return HttpResponse()


@login_required(login_url='login')
def shoredeleteafter(request, pk):
    shore = Shore.objects.get(pk=pk)
    shore.delete()
    return HttpResponse()


@login_required(login_url='login')
def shoreupdate(request, pk):
    template = 'partials/shoreinspection.html'
    shore = Shore.objects.get(pk=pk)
    form = ShoreInspectionBefore(request.POST or None, instance=shore)

    if request.method == "POST":
        if request.method == 'POST':
            if form.is_valid():
                form = form.save()
                return redirect('shore-details', pk=form.id)

    context = {
        "form": form,
        "shore": shore,
    }
    return render(request, template, context)


@login_required(login_url='login')
def shoreupdateafter(request, pk):
    template = 'partials/shoreinspectionafter.html'
    shore = Shore.objects.get(pk=pk)
    form = ShoreInspectionAfter(request.POST or None, instance=shore)

    if request.method == "POST":
        if request.method == 'POST':
            if form.is_valid():
                tankdenomafter = request.POST['tankdenomafter']
                prodinnageafter = request.POST['prodinnageafter']
                fwdeepafter = request.POST['fwdeepafter']
                govafter = request.POST['govafter']
                tempafter = request.POST['tempafter']
                densityafter = request.POST['densityafter']

                shore.tankdenomafter = tankdenomafter
                shore.prodinnageafter = prodinnageafter
                shore.fwdeepafter = fwdeepafter
                shore.govafter = govafter
                shore.tempafter = tempafter
                shore.densityafter = densityafter

                shore.save(
                    update_fields=['tankdenomafter', 'prodinnageafter', 'prodinnageafter', 'fwdeepafter', 'govafter',
                                   'tempafter', 'densityafter'])

                return redirect('shore-details-after', pk=form.id)

    context = {
        "form": form,
        "shore": shore,
    }
    return render(request, template, context)


@login_required(login_url='login')
def tableaurapports(request):
    user = request.user.id
    template = 'tableauRapport.html'
    context = {}
    return render(request, template, context)


@login_required(login_url='login')
def responseTableauRapports(request):
    user = request.user.id
    qs = Cargaison.objects.filter(
        entrepot__affectationentrepot__username_id=user,
        etatInspection=0,
    ).annotate(
        volConst=Sum('inspection__compartiment__gov'),
        gsvT=Sum('inspection__compartiment__gsv')
    ).values(
        'idcargaison',
        'numdos',
        'declaration',
        'inspection__idinspection',
        'entrepot__ville__nomville',
        'inspection__dateinspection',
        'importateur__nomimportateur',
        'entrepot__nomentrepot',
        'immatriculation',
        'produit__nomproduit',
        'dateheurecargaison__date',
        'requisitiondackdate',
        'dateDechargement',
        'entrepot_echantillon__dateechantillonage',
        'entrepot_echantillon__laboreception__datereceptionlabo',
        'impressionresultat__printDate',
        'inspection__dateinspection',
        'volume',
        'volConst',
        gsvT=Case(
            When(inspection__compartiment__gsv__isnull=False, then=F('gsvT')),
            default=0,
            output_field=FloatField()
        )
    ).order_by('-inspection__dateinspection')
    # Number of items to show per page
    items_per_page = 8

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

    # Check if it's an AJAX request and if the export flag is set
    # Check if it's an AJAX request and if the export flag is set
    export = request.GET.get('export', None)
    if export == 'excel':
        # Retrieve all data (no lazy pagination) and store it in a list
        data = list(qs)

        # Create a new Excel workbook
        workbook = Workbook()
        sheet = workbook.active

        # Write headers to the Excel file
        header_row = ['DATE ENTREE', 'FOURNISSEUR', 'ENTREPOT', 'PRODUIT', 'VOL.DECL.', 'IMMATR.',
                      '#.T1D',
                      '#.REQ.']

        # Combine header and data rows using zip
        all_rows = [header_row] + [
            [
                row['dateheurecargaison__date'],
                row['frontiere__nomville'],
                row['importateur__nomimportateur'],
                row['entrepot__nomentrepot'],
                row['produit__nomproduit'],
                row['immatriculation'],
                row['declaration'],
                row['numdos'],
                row['requisitiondackdate__date'],
                row['entrepot_echantillon__dateechantillonage__date'],
                row['entrepot_echantillon__laboreception__datereceptionlabo__date'],
                row['impressionresultat__printDate'],
                row['inspection__dateinspection'],
                row['volume'],
                row['volConst'],
                row['gsvT'],
            ] for row in data
        ]

        # Write data rows to the Excel file
        for row in all_rows:
            sheet.append(row)

        # Create an in-memory stream to hold the Excel file data
        excel_stream = io.BytesIO()
        workbook.save(excel_stream)
        excel_stream.seek(0)

        # Prepare the response to return the Excel file
        response = HttpResponse(excel_stream,
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="rapport_brut_journalier.xlsx"'
        return response

    # Return JSON response with the data
    return JsonResponse({
        'data': data,
        'draw': draw,
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
    })


@login_required(login_url='login')
def natureProduit(request, pk):
    user = request.user.id
    template = 'natureProduit.html'
    cargaison = Cargaison.objects.get(idcargaison=pk)
    form = NatureProduit(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            produit = request.POST['produit']
            if int(produit) == int(cargaison.produit.idproduit):
                c = ControlNatureProduit(idcargaison=cargaison, natureProduitEntrepot=produit.nomproduit,
                                         userEntrepot=user, conformiteProduit=True)
                return redirect('echantillonage', pk=pk)
            else:
                produit = Produit.objects.get(idproduit=produit)
                c = ControlNatureProduit(idcargaison=cargaison, natureProduitEntrepot=produit.nomproduit,
                                         userEntrepot=user, conformiteProduit=False)
                c.save()
                return redirect('entrepot')
    else:
        context = {'form': form}
        return render(request, template, context)


@login_required(login_url='login')
def affichageProduitNonConforme(request):
    user = request.user
    role = user.role_id
    id = user.id
    template = 'affichageProduitNonConforme.html'

    # qs = ControlNatureProduit.objects.filter(idcargaison__entrepot__affectationentrepot__username_id=id,conformiteProduit=False)
    qs = Entrepot_echantillon.objects.filter(idcargaison__toBeRefouler=1, idcargaison__isRefouler=0,
                                             idcargaison__entrepot__affectationentrepot__username_id=id)
    qs1 = Entrepot_echantillon.objects.filter(idcargaison__toBeConsignated=1, idcargaison__isConsignated=0,
                                              idcargaison__entrepot__affectationentrepot__username_id=id)

    table = NonConformeOrganoleptique(qs, prefix='1')
    table1 = NonConformeLaboratoire(qs1, prefix='2')
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 5}).configure(table)
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 5}).configure(table1)
    context = {
        'table': table,
        'table1': table1,
    }
    return render(request, template, context)


@login_required(login_url='login')
def affichageEnAttenteRequisition(request):
    user = request.user
    role = user.role_id
    id = user.id
    template = 'enAttenteRequisition.html'
    qs = Cargaison.objects.filter(etat="En attente requisition",
                                  entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
    table = CargaisonEnAttenteRequisition(qs)
    RequestConfig(request, paginate={"per_page": 15}).configure(table)
    context = {'table': table}
    return render(request, template, context)


@login_required(login_url='login')
def correctionNonConformite(request, pk):
    user = request.user.id
    # Update Product Name Correction
    x = ControlNatureProduit.objects.get(idcontrol=pk)
    x.correctionNature = x.natureProduitEntrepot
    x.userEntrepot = user
    x.conformiteProduit = True
    x.save(update_fields=['correctionNature', 'userEntrepot', 'conformiteProduit'])
    return redirect('entrepot')


@login_required(login_url='login')
def inspection(request, pk):
    user = request.user.id
    role = user.role_id

    if role == 3 or role == 1:
        qs = Cargaison.objects.filter(etatInspection=True, etat="Echantillonner", before=False,
                                      entrepot__affectationentrepot__username_id=id).order_by('-dateheurecargaison')
        table = CargaisonDechargement(qs, prefix='1_')

        # affichage des tanker cabotteurs
        qs1 = Cargaison.objects.filter(before=True, entrepot__affectationentrepot__username_id=id).order_by(
            '-dateheurecargaison')
        table1 = TankerCabotteur(qs1, prefix='2_')
        RequestConfig(request, paginate={"per_page": 10}).configure(table)
        RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 10}).configure(table1)
        return render(request, 'entrepot_dechargement.html', {'cargaison': table,
                                                              'rapport': table1,
                                                              })
    else:
        return redirect('logout')


@login_required(login_url='login')
def affichageInspection(request):
    user = request.user.id
    try:
        # Fetch the user's ville
        affectation_ville = AffectationVille.objects.get(username_id=user)
        ville = affectation_ville.ville.nomville  # Access the related ville's name
    except AffectationVille.DoesNotExist:
        ville = None  # Handle cases where no Ville is assigned to the user

    template = 'entrepot_enAttenteInspection.html'
    form = Special_inspection_form()

    # Determine the status condition outside the query
    if ville == "KALEMIE":
        status_appurement = Value("Appurement")
        status_other = Value("Pending")  # Default for non-KALEMIE
    elif ville is None:
        status_appurement = Value("No Ville")
        status_other = Value("Pending")
    else:
        status_appurement = Value("Pending")
        status_other = Value("Pending")

    # Fetch and annotate the queryset
    qs = (Cargaison.objects.filter(etatInspection=True, entrepot__affectationentrepot__username_id=user)
          .annotate(
        status=Case(
            When(entrepot__ville__nomville="KALEMIE", then=status_appurement),  # Ville is KALEMIE
            When(~Q(entrepot__ville__nomville="KALEMIE") & Q(entrepot__ville__isnull=False), then=status_other),   # Ville is not KALEMIE
            When(entrepot__ville__isnull=True, then=Value("No Ville")),  # Ville is None
            default=Value("Unknown"),
            output_field=CharField()
        )
    )
          .order_by('-dateheurecargaison'))


    # Configure the table with the queryset
    table = EnAttenteInspection(qs, prefix='1_')
    RequestConfig(request, paginate={"per_page": 10}).configure(table)

    context = {
        'form': form,
        'table': table
    }
    return render(request, template, context)


@login_required(login_url='login')
def marquageInspectionWeb(request):
    user = request.user.id
    ville = AffectationVille.objects.get(username_id=user)
    pk = request.session['id']
    c = Cargaison.objects.get(idcargaison=pk)
    c.etatInspection = 0
    c.numact = num_cert_inspection(ville)
    c.save(update_fields=['etatInspection', 'numact'])

    UserActivityLog.objects.create(
        user=request.user,
        action="Inspection completed",
        description=f"User has completed the inspection of the record  {c.idcargaison}",
    )

    # Create a dictionary with the data you want to return
    response_data = {
        'message': 'Inspection marked successfully',
        'status': 'success',
        'pk': pk,
    }

    # Return a JSON response
    return JsonResponse(response_data)


@login_required(login_url='login')
def consignatedOk(request, pk):
    c = Cargaison.objects.get(idcargaison=pk)
    c.isConsignated = 1
    c.toBeConsignated = 0
    c.save(update_fields=['isConsignated', 'toBeConsignated'])
    return redirect('affichageProduitNonConforme')


@login_required(login_url='login')
def refouleOk(request, pk):
    c = Cargaison.objects.get(idcargaison=pk)
    c.isRefouler = 1
    c.toBeRefouler = 0
    c.save(update_fields=['isRefouler', 'toBeRefouler'])
    return redirect('affichageProduitNonConforme')


#Fonction pour les appurement des volumes a Kalemie seulement
@login_required(login_url='login')
def appurement_vol(request):
    user = request.user.id
    ville = AffectationVille.objects.get(username_id=user)

    # Check if the request is a POST request (AJAX submission)
    if request.method == 'POST':
        # Get the form data from the request
        form_data = request.POST

        recordId = form_data.get('recordId')  # Get recordId from POST data

        # Create an instance of the form with the data
        form = Special_inspection_form(form_data)

        if form.is_valid():
            # Extract form data
            dens = form.cleaned_data.get('dens')
            index_deb = form.cleaned_data.get('index_deb')
            index_fin = form.cleaned_data.get('index_fin')
            temp = form.cleaned_data.get('temp')

            if index_deb:
                if index_fin:
                    gov = index_fin - index_deb
                else:
                    gov = form.cleaned_data.get('gov')
            else:
                gov = form.cleaned_data.get('gov')

            #Calcul des valeurs GSV, MTV, MTA
            densite = dens
            temperature = temp
            d = densite15(temperature, densite)  # Calcul Dens a 15

            v = vcf(d, temperature)  # VCF
            g = gsv(v, gov)  # GSV
            m = mtv(g, d)  # MTV
            a = mta(g, d)  # MTA

            insp = Inspection(
                dens=densite,
                temp=temperature,
                innagein="cm",
                volumein="Cu.Mtrs",
                tempin="C°",
                weightin="m/t",
                idcargaison_id=recordId
            )
            insp.save()

            insp = Inspection.objects.get(idcargaison_id=recordId)

            seals = SealState.objects.get(idsealstate=1)

            # Process the valid form data (e.g., save it to the database)
            c = Compartiment(
                compart='TANKER',
                sealNumber='N/A',
                gov=g,
                tempcomp=temperature,
                vcf=v,
                mta=a,
                mtv=m,
                gsv=g,
                idinspection=insp,
                sealstate=seals
            )
            c.save()

            #Mise a jour des informations afin de conclure l'inspection
            c = Cargaison.objects.get(idcargaison=recordId)
            c.etatInspection = 0
            c.numact = num_cert_inspection(ville.ville_id)
            c.save(update_fields=['etatInspection', 'numact'])

            # Example: form.save() or any other data processing logic
            print("Form is valid. Data saved.")

            # Return a JSON response indicating success
            return JsonResponse({"status": "success", "message": "Données enregistrées"})

        else:
            # If the form is not valid, return an error message
            print("Form is invalid.")
            return JsonResponse({"status": "error", "message": "Erreur de validation de formulaire"}, status=400)

    # If the request is GET or other methods, render the page or handle accordingly
    else:
        return JsonResponse({"status": "error", "message": "Erreur de validation de formulaire"}, status=400)



def _safe_iso(dt):
    """Return an ISO string for a datetime, handling naive values safely."""
    if not dt:
        return None
    try:
        if timezone.is_naive(dt):
            # Attach current timezone if value is naive (legacy rows / old imports)
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        else:
            dt = timezone.localtime(dt)
        return dt.isoformat()
    except Exception:
        # Fallback without TZ if anything odd happens
        try:
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            return None


def _serialize_cargaison(c: Cargaison) -> dict:
    return {
        "id": c.idcargaison,
        "dateheurecargaison": _safe_iso(c.dateheurecargaison),
        "importateur_name": getattr(c.importateur, "nomimportateur", None),
        "entrepot_name": getattr(c.entrepot, "nomentrepot", None),
        "immatriculation": c.immatriculation,
        "produit_name": getattr(c.produit, "nomproduit", None),
        "volume": c.volume,
        "qrcode": c.qrcode,
    }


@login_required(login_url="login")
def workbench_list(request):
    """
    JSON endpoint for the Workbench modal table.

    GET:
      - status   : 'requisition' to list 'En attente requisition' or 'reports' for Rapports / Historique
      - page     : int (default 1)
      - per_page : int (default 10, max 100)
      - q        : optional free-text search
    """
    user = request.user
    if getattr(user, "role_id", None) not in (1, 3, 9):
        return JsonResponse({"error": "Forbidden"}, status=403)

    status_key = (request.GET.get("status") or "requisition").lower()
    try:
        page = max(1, int(request.GET.get("page") or 1))
    except ValueError:
        page = 1
    try:
        per_page = max(1, min(100, int(request.GET.get("per_page") or 10)))
    except ValueError:
        per_page = 10

    q = (request.GET.get("q") or "").strip()

    if status_key == "requisition":
        # En attente de réquisition
        qs = (
            Cargaison.objects
            .select_related("importateur", "entrepot", "produit")
            .filter(
                etat="En attente requisition",
                entrepot__affectationentrepot__username_id=user.id
            )
            .order_by("-dateheurecargaison")
        )
    elif status_key == "reports":
        # Rapports / Historique — afficher tous les enregistrements dans les entrepôts affectés à l'utilisateur
        qs = (
            Cargaison.objects
            .select_related("importateur", "entrepot", "produit")
            .filter(
                entrepot__affectationentrepot__username_id=user.id,
            )
            .order_by("-dateheurecargaison")
        )
    else:
        qs = Cargaison.objects.none()

    if q:
        qs = qs.filter(
            Q(immatriculation__icontains=q)
            | Q(importateur__nomimportateur__icontains=q)
            | Q(entrepot__nomentrepot__icontains=q)
            | Q(produit__nomproduit__icontains=q)
        )

    # Manual lazy pagination: fetch per_page + 1 to detect has_next without COUNT(*).
    start = (page - 1) * per_page
    if start < 0:
        start = 0
    batch = list(qs[start:start + per_page + 1])
    has_next = len(batch) > per_page
    rows = batch[:per_page]
    has_prev = page > 1

    items = [_serialize_cargaison(c) for c in rows]

    return JsonResponse(
        {
            "items": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                # In lazy mode we do not compute total/pages to avoid expensive COUNT(*).
                "total": None,
                "pages": None,
                "has_next": has_next,
                "has_prev": has_prev,
            },
        },
        status=200,
        json_dumps_params={"ensure_ascii": False},
    )



# ----------------------------
# Small helpers (DRY)
# ----------------------------
def _as_int(v, default):
    try:
        n = int(v)
        return n if n > 0 else default
    except Exception:
        return default


def _user_entrepot_ids(user):
    """
    IDs of entrepôts assigned to this user through the affectation table.
    Adjust the relation name if needed (affectationentrepot__username_id).
    """
    return set(
        Entrepot.objects.filter(affectationentrepot__username_id=user.id)
        .values_list("identrepot", flat=True)
    )


def _visible_cargos_for(user, entrepot_id=None):
    """
    Base queryset: cargos in entrepôts assigned to this user.
    Optionally restrict to a specific entrepôt_id (validated by caller).
    """
    qs = Cargaison.objects.filter(
        entrepot__affectationentrepot__username_id=user.id
    )
    if entrepot_id:
        qs = qs.filter(entrepot_id=entrepot_id)
    return qs


def _serialize_row(c: Cargaison):
    return {
        "id": c.idcargaison,
        "dateheurecargaison": c.dateheurecargaison,
        "importateur": getattr(c.importateur, "nomimportateur", None),
        "importateur_name": getattr(c.importateur, "nomimportateur", None),
        "entrepot": getattr(c.entrepot, "nomentrepot", None),
        "entrepot_name": getattr(c.entrepot, "nomentrepot", None),
        "immatriculation": c.immatriculation,
        "produit": getattr(c.produit, "nomproduit", None),
        "produit_name": getattr(c.produit, "nomproduit", None),
        "volume": c.volume,
        "qrcode": c.qrcode,
        "etat": c.etat,
        "etatInspection": bool(c.etatInspection),
        "toBeRefouler": bool(c.toBeRefouler),
        "toBeConsignated": bool(c.toBeConsignated),
        "isRefouler": bool(c.isRefouler),
        "isConsignated": bool(c.isConsignated),
    }


def _paginate_qs(qs, page, per_page):
    total = qs.count()
    start = (page - 1) * per_page
    end   = start + per_page
    pages = max(1, (total + per_page - 1) // per_page)
    data  = {
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_prev": page > 1,
            "has_next": page < pages,
        }
    }
    return data, qs[start:end]


def _search_filter(q: str):
    """
    Build a Q() that searches across common fields.
    """
    if not q:
        return Q()
    return (
        Q(immatriculation__icontains=q)
        | Q(importateur__nomimportateur__icontains=q)
        | Q(produit__nomproduit__icontains=q)
        | Q(entrepot__nomentrepot__icontains=q)
    )


def _list_payload(request, base_q: Q, tag: str):
    """
    Shared engine:
      - scope to user’s assigned entrepôts
      - optional entrepôt filter (?entrepot=<id>) validated against user’s list
      - optional text search (?q=…)
      - select_related to avoid N+1
      - pagination
    """
    page       = _as_int(request.GET.get("page"), 1)
    per_page   = _as_int(request.GET.get("per_page"), 10)
    q_text     = (request.GET.get("q") or "").strip()
    ent_param  = request.GET.get("entrepot")
    entrepot_id = _as_int(ent_param, None) if ent_param else None

    # Validate entrepôt scope — only allow IDs the user actually has
    if entrepot_id:
        allowed_ids = _user_entrepot_ids(request.user)
        if entrepot_id not in allowed_ids:
            # If not allowed, return empty payload (or 403 if you prefer)
            payload = {
                "status": tag,
                "q": q_text,
                "pagination": {
                    "page": 1, "per_page": per_page, "total": 0, "pages": 1,
                    "has_prev": False, "has_next": False
                },
                "items": [],
                "entrepot": entrepot_id,
            }
            return JsonResponse(payload)

    qs = (
        _visible_cargos_for(request.user, entrepot_id=entrepot_id)
        .select_related("importateur", "entrepot", "produit")
        .filter(base_q)
        .filter(_search_filter(q_text))
        .distinct()
        .order_by("-dateheurecargaison", "-idcargaison")
    )

    meta, slice_qs = _paginate_qs(qs, page, per_page)
    payload = {
        "status": tag,
        "q": q_text,
        "entrepot": entrepot_id,
        **meta,
        "items": [_serialize_row(c) for c in slice_qs],
    }
    return JsonResponse(payload)


# ----------------------------
# Separate KPI endpoints
# ----------------------------
def _guard(request):
    return getattr(request.user, "role_id", None) in (1, 3, 9)

@login_required
def workbench_requisition(request):
    if not _guard(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    # En attente de réquisition
    base_q = Q(etat__iexact="En attente requisition")
    return _list_payload(request, base_q, tag="requisition")

@login_required
def workbench_inspection(request):
    if not _guard(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    # En inspection (non encore inspectées)
    base_q = Q(etatInspection=False)
    return _list_payload(request, base_q, tag="inspection")

@login_required
def workbench_conformes(request):
    if not _guard(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    # Conformes: etat = "Conforme aux exigences" AND an ImpressionResultat exists with isConforme=True
    base_q = Q(etat__iexact="Conforme aux exigences") & Exists(
        ImpressionResultat.objects.filter(
            idcargaison=OuterRef("idcargaison"),
            isConforme=True,
        )
    )
    return _list_payload(request, base_q, tag="conformes")


@login_required
def workbench_reports(request):
    if not _guard(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    # Rapports / Historique — montrer tous les enregistrements visibles (sans filtre de statut spécifique)
    base_q = Q()
    return _list_payload(request, base_q, tag="reports")



# ----------------------------
# Views
# ----------------------------
def _json_error(message: str, *, status: int = 400):
    return JsonResponse({"ok": False, "error": message}, status=status)

def _to_float(val: Any, ndigits: Optional[int] = None) -> Optional[float]:
    """Convert to float (or None). Optionally round to 'ndigits'."""
    if val in (None, "", "null"):
        return None
    try:
        f = float(val)
        return round(f, ndigits) if (ndigits is not None) else f
    except (TypeError, ValueError):
        return None

def _reverse_inspection_start(pk: int) -> str:
    """
    Try to reverse a named URL, fallback to the hardcoded template used by your frontend.
    Adjust the name below if your URL is named differently.
    """
    candidates = ("inspection_start", "entrepot_inspection_start")
    for name in candidates:
        try:
            return reverse(name, kwargs={"pk": pk})
        except Exception:
            continue
    return f"/entrepot/inspection/start/{pk}/"


def _to_decimal(val, places=3):
    """
    Convert incoming numbers to Decimal or return None.
    Accepts str|int|float|None. Rounds to 'places' if provided.
    """
    if val in ("", None):
        return None
    try:
        d = Decimal(str(val))
        if places is not None:
            q = Decimal("1").scaleb(-places)  # e.g. places=3 -> Decimal("0.001")
            d = d.quantize(q)
        return d
    except (InvalidOperation, ValueError, TypeError):
        return None


def _sealstate_from_frontend(value) -> Optional[SealState]:
    """
    Resolve a SealState instance from a frontend-provided value/label.
    - Matches on `sealstate` case-insensitively.
    - Creates a new SealState if not found.
    Returns None only if the input is empty/invalid.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return SealState.objects.get(sealstate__iexact=text)
    except SealState.DoesNotExist:
        try:
            return SealState.objects.create(sealstate=text)
        except Exception:
            # Last resort: try again in case of race condition
            try:
                return SealState.objects.get(sealstate__iexact=text)
            except Exception:
                return None


@login_required
def inspection_start(request, pk: int):
    """
    Landing route after the wizard.
    Ensures an Inspection exists for the cargo `pk` then redirects to the
    existing compartiment form to continue/edit compartments.
    """
    cargo = get_object_or_404(Cargaison, pk=pk)
    # Make sure an Inspection row exists so compartiment view can resolve it
    Inspection.objects.get_or_create(idcargaison=cargo, defaults={})
    return redirect('compartiment', pk=pk)


@login_required
@require_POST
def inspection_wizard_post(request, pk: int):
    """
    Upserts Inspection for the given Cargaison, replaces related
    InspectionSeal (FK -> Cargaison) and Compartiment (FK -> Inspection).
    SealState is taken from FRONTEND label and created if missing.
    """
    # ---- Parse JSON
    try:
        payload: Dict[str, Any] = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return _json_error("Invalid JSON body.")

    cargo = get_object_or_404(Cargaison, pk=pk)

    body_id = str(payload.get("idcargaison", "")).strip()
    if body_id and body_id != str(pk):
        return _json_error("Payload cargo id does not match URL.")

    seals_in = payload.get("seals") or []
    comps_in = payload.get("compartiments") or []

    ti = payload.get("tankerInspection") or {}
    dens = _to_float(ti.get("dens"))
    temp = _to_float(ti.get("temp"))
    innagein = (ti.get("innagein") or "").strip() or None
    volumein = (ti.get("volumein") or "").strip() or None
    tempin = (ti.get("tempin") or "").strip() or None
    weightin = (ti.get("weightin") or "").strip() or None

    meterbefore = _to_float(payload.get("meterbefore"))
    meterafter = _to_float(payload.get("meterafter"))

    # ---- Minimal validation (FKs must not be NULL)
    if not seals_in:
        return _json_error("Au moins un manifold/seal est requis.")
    for s in seals_in:
        if not str(s.get("manifoldnumber", "")).strip():
            return _json_error("Chaque manifold doit avoir un numéro.")
        if not str(s.get("sealstate", "")).strip():
            return _json_error("Chaque manifold doit avoir un état du sceau.")

    if not comps_in:
        return _json_error("Au moins un compartiment est requis.")
    for c in comps_in:
        if not str(c.get("compart", "")).strip():
            return _json_error("Chaque compartiment doit avoir une dénomination.")
        if not str(c.get("sealstate", "")).strip():
            return _json_error("Chaque compartiment doit avoir un état du sceau.")

    # ---- Persist
    try:
        with transaction.atomic():
            # Upsert Inspection (OneToOne)
            inspection, _created = Inspection.objects.select_for_update().get_or_create(
                idcargaison=cargo,
                defaults={}
            )

            # Mirror produit from cargo if present
            if isinstance(getattr(cargo, "produit", None), Produit):
                inspection.produit = cargo.produit

            inspection.dens = dens
            inspection.temp = temp
            inspection.innagein = innagein
            inspection.volumein = volumein
            inspection.tempin = tempin
            inspection.weightin = weightin
            inspection.meterbefore = meterbefore
            inspection.meterafter = meterafter
            inspection.save()

            # Replace Compartiments
            Compartiment.objects.filter(idinspection=inspection).delete()
            comp_objs = []
            for c in comps_in:
                # Base fields
                inn = _to_float(c.get("innage"))
                gv  = _to_float(c.get("gov"))
                tp  = _to_float(c.get("tempcomp"))

                # Default computed values
                v_val = None
                g_val = None
                m_val = None
                a_val = None

                # Compute derived metrics when inputs are sufficient
                # Uses the same logic as the legacy 'compartiment' view:
                # d = densite15(inspection.temp, inspection.dens)
                # v = vcf(d, tp); g = gsv(v, gv); m = mtv(g, d); a = mta(g, d)
                if inspection.dens is not None and inspection.temp is not None and tp is not None and gv is not None:
                    try:
                        d15 = densite15(inspection.temp, inspection.dens)
                        v_val = vcf(d15, tp)
                        g_val = gsv(v_val, gv)
                        m_val = mtv(g_val, d15)
                        a_val = mta(g_val, d15)
                    except Exception:
                        # Keep computed fields as None if any calc fails
                        v_val = g_val = m_val = a_val = None

                comp_objs.append(
                    Compartiment(
                        idinspection=inspection,
                        compart=str(c.get("compart", "")).strip(),
                        sealNumber=str(c.get("sealNumber", "")).strip() or None,
                        sealstate=_sealstate_from_frontend(c.get("sealstate")),  # <- frontend label
                        innage=inn,
                        gov=gv,
                        tempcomp=tp,
                        vcf=v_val,
                        gsv=g_val,
                        mtv=m_val,
                        mta=a_val,
                    )
                )
            if comp_objs:
                # Ensure no None sealstate slipped in
                if any(o.sealstate is None for o in comp_objs):
                    return _json_error("État du sceau manquant pour un compartiment.")
                Compartiment.objects.bulk_create(comp_objs)

            # Replace Seals (FK to Cargaison)
            InspectionSeal.objects.filter(idcargaison=cargo).delete()
            seal_objs = []
            for s in seals_in:
                seal_objs.append(
                    InspectionSeal(
                        idcargaison=cargo,
                        manifoldnumber=str(s.get("manifoldnumber", "")).strip(),
                        sealstate=_sealstate_from_frontend(s.get("sealstate")),  # <- frontend label
                    )
                )
            if seal_objs:
                if any(o.sealstate is None for o in seal_objs):
                    return _json_error("État du sceau manquant pour un manifold.")
                InspectionSeal.objects.bulk_create(seal_objs)

            # Mark cargo as “in inspection”
            if hasattr(cargo, "etatInspection") and not cargo.etatInspection:
                cargo.etatInspection = True
                cargo.save(update_fields=["etatInspection"])

    except Exception as e:
        return _json_error(str(e))

    return JsonResponse(
        {
            "ok": True,
            "id": cargo.pk,
            "inspection_id": inspection.idinspection,
            "redirect": _reverse_inspection_start(cargo.pk),
        }
    )








@login_required
@require_POST
def inspection_wizard_finalize(request, pk: int):
    """
    New endpoint for the modal: saves Inspection, InspectionSeal and Compartiment
    (with calculations for compartments) and returns JSON only. No redirects.

    Response: { ok: true, id: <cargaison id>, inspection_id: <inspection pk> }
    """
    try:
        payload: Dict[str, Any] = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return _json_error("Invalid JSON body.")

    cargo = get_object_or_404(Cargaison, pk=pk)

    body_id = str(payload.get("idcargaison", "")).strip()
    if body_id and body_id != str(pk):
        return _json_error("Payload cargo id does not match URL.")

    seals_in = payload.get("seals") or []
    comps_in = payload.get("compartiments") or []

    ti = payload.get("tankerInspection") or {}
    dens = _to_float(ti.get("dens"))
    temp = _to_float(ti.get("temp"))
    innagein = (ti.get("innagein") or "").strip() or None
    volumein = (ti.get("volumein") or "").strip() or None
    tempin = (ti.get("tempin") or "").strip() or None
    weightin = (ti.get("weightin") or "").strip() or None

    meterbefore = _to_float(payload.get("meterbefore"))
    meterafter = _to_float(payload.get("meterafter"))

    # Minimal validation
    if not seals_in:
        return _json_error("Au moins un manifold/seal est requis.")
    for s in seals_in:
        if not str(s.get("manifoldnumber", "")).strip():
            return _json_error("Chaque manifold doit avoir un numéro.")
        if not str(s.get("sealstate", "")).strip():
            return _json_error("Chaque manifold doit avoir un état du sceau.")

    if not comps_in:
        return _json_error("Au moins un compartiment est requis.")
    for c in comps_in:
        if not str(c.get("compart", "")).strip():
            return _json_error("Chaque compartiment doit avoir une dénomination.")
        if not str(c.get("sealstate", "")).strip():
            return _json_error("Chaque compartiment doit avoir un état du sceau.")

    try:
        with transaction.atomic():
            inspection, _created = Inspection.objects.select_for_update().get_or_create(
                idcargaison=cargo,
                defaults={}
            )

            if isinstance(getattr(cargo, "produit", None), Produit):
                inspection.produit = cargo.produit

            inspection.dens = dens
            inspection.temp = temp
            inspection.innagein = innagein
            inspection.volumein = volumein
            inspection.tempin = tempin
            inspection.weightin = weightin
            inspection.meterbefore = meterbefore
            inspection.meterafter = meterafter
            inspection.save()

            # Compartiments: replace and compute derived values
            Compartiment.objects.filter(idinspection=inspection).delete()
            comp_objs = []
            for c in comps_in:
                inn = _to_float(c.get("innage"))
                gv  = _to_float(c.get("gov"))
                tp  = _to_float(c.get("tempcomp"))

                v_val = g_val = m_val = a_val = None
                if inspection.dens is not None and inspection.temp is not None and tp is not None and gv is not None:
                    try:
                        d15 = densite15(inspection.temp, inspection.dens)
                        v_val = vcf(d15, tp)
                        g_val = gsv(v_val, gv)
                        m_val = mtv(g_val, d15)
                        a_val = mta(g_val, d15)
                    except Exception:
                        v_val = g_val = m_val = a_val = None

                comp_objs.append(
                    Compartiment(
                        idinspection=inspection,
                        compart=str(c.get("compart", "")).strip(),
                        sealNumber=str(c.get("sealNumber", "")).strip() or None,
                        sealstate=_sealstate_from_frontend(c.get("sealstate")),
                        innage=inn,
                        gov=gv,
                        tempcomp=tp,
                        vcf=v_val,
                        gsv=g_val,
                        mtv=m_val,
                        mta=a_val,
                    )
                )
            if comp_objs:
                if any(o.sealstate is None for o in comp_objs):
                    return _json_error("État du sceau manquant pour un compartiment.")
                Compartiment.objects.bulk_create(comp_objs)

            # Seals: replace
            InspectionSeal.objects.filter(idcargaison=cargo).delete()
            seal_objs = []
            for s in seals_in:
                seal_objs.append(
                    InspectionSeal(
                        idcargaison=cargo,
                        manifoldnumber=str(s.get("manifoldnumber", "")).strip(),
                        sealstate=_sealstate_from_frontend(s.get("sealstate")),
                    )
                )
            if seal_objs:
                if any(o.sealstate is None for o in seal_objs):
                    return _json_error("État du sceau manquant pour un manifold.")
                InspectionSeal.objects.bulk_create(seal_objs)

            # Flag cargo as in-inspection when applicable
            if hasattr(cargo, "etatInspection") and not cargo.etatInspection:
                cargo.etatInspection = True
                cargo.save(update_fields=["etatInspection"])

    except Exception as e:
        return _json_error(str(e))

    return JsonResponse({
        "ok": True,
        "id": cargo.pk,
        "inspection_id": inspection.idinspection,
    })
