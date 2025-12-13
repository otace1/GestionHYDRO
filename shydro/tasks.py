import os
import io
from django_tables2.export.export import TableExport
import datetime

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport

from hydrocarbures.celery import app
from shydro.tables import RapportActivite
from django.db.models import Q, Sum
from django.utils import timezone
from openpyxl import Workbook
from enreg.models import Cargaison
from entrepot.calculs import densite15, vcf


# app = Celery('tasks', broker='redis://127.0.0.1:6379/0', backend='redis://127.0.0.1:6379/1')


@app.task
def add(x, y):
    return x + y


@app.task
def export_report_task(export_format, queryset_data, request=None):
    try:
        # Initialize the table with the queryset data
        table = RapportActivite(queryset_data)

        # If request is provided, configure pagination
        if request:
            RequestConfig(request, paginate={"per_page": 15}).configure(table)

        # Export the table
        exporter = TableExport(export_format, table, exclude_columns=("actions"))
        file_content = exporter.export()

        # Generate a unique file name using datetime
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"table_{current_datetime}.{export_format}"

        # Save the exported file to the default storage (DigitalOcean Spaces)
        file_path = f"xlsx/{file_name}"
        file_content_file = ContentFile(file_content)
        file_url = default_storage.save(file_path, file_content_file)

        # Get the full URL of the exported file
        full_file_url = default_storage.url(file_path)

        # Return the full URL of the exported file along with the file name
        return {
            'file_url': full_file_url,
            'file_name': file_name,
        }

    except Exception as e:
        return {'error': str(e)}



@app.task
def export_rapport_activites_task(params: dict, user_id: int):
    """
    Build the Rapport d'activités Excel asynchronously using server-side filters/order.
    Saves the file to the default storage and returns a public URL and filename.

    params: Dict containing possible keys:
        - search[value]
        - date_from, date_to, frontiere, importateur, entrepot, produit,
          immatriculation, declaration, numdos
        - order: list of {column, dir} like DataTables
    """
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage

    # Rebuild queryset similar to responseRapportActivite
    qs = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user_id
    ).annotate(
        volConst=Sum('inspection__compartiment__gov'),
        gsvT=Sum('inspection__compartiment__gsv'),
        mtaT=Sum('inspection__compartiment__mta'),
        mtvT=Sum('inspection__compartiment__mtv'),
    ).values(
        'idcargaison',
        'numdos',
        'declaration',
        'frontiere__nomville',
        'entrepot__nomentrepot',
        'inspection__dateinspection',
        'inspection__dens',
        'inspection__temp',
        'importateur__nomimportateur',
        'immatriculation',
        'produit__nomproduit',
        'dateheurecargaison__date',
        'requisitiondackdate__date',
        'entrepot_echantillon__dateechantillonage__date',
        'entrepot_echantillon__laboreception__datereceptionlabo__date',
        'impressionresultat__printDate',
        'dateDechargement',
        'volume',
        'volConst',
        'gsvT',
        'mtaT',
        'mtvT',
    )

    # Advanced filters
    def g(k):
        v = params.get(k)
        return (v or '').strip() if isinstance(v, str) else (v or '')

    date_from = g('date_from')
    date_to = g('date_to')
    ft_name = g('frontiere')
    imp_name = g('importateur')
    ent_name = g('entrepot')
    prod_name = g('produit')
    immat = g('immatriculation')
    decl = g('declaration')
    numd = g('numdos')

    adv = Q()
    if date_from and date_to:
        adv &= Q(dateheurecargaison__date__range=[date_from, date_to])
    elif date_from:
        adv &= Q(dateheurecargaison__date__gte=date_from)
    elif date_to:
        adv &= Q(dateheurecargaison__date__lte=date_to)
    if ft_name:
        adv &= Q(frontiere__nomville__icontains=ft_name)
    if imp_name:
        adv &= Q(importateur__nomimportateur__icontains=imp_name)
    if ent_name:
        adv &= Q(entrepot__nomentrepot__icontains=ent_name)
    if prod_name:
        adv &= Q(produit__nomproduit__icontains=prod_name)
    if immat:
        adv &= Q(immatriculation__icontains=immat)
    if decl:
        adv &= Q(declaration__icontains=decl)
    if numd:
        adv &= Q(numdos__icontains=numd)
    if adv:
        qs = qs.filter(adv)

    # Global search
    search_value = g('search[value]')
    if search_value:
        qs = qs.filter(
            Q(frontiere__nomville__icontains=search_value) |
            Q(importateur__nomimportateur__icontains=search_value) |
            Q(entrepot__nomentrepot__icontains=search_value) |
            Q(produit__nomproduit__icontains=search_value) |
            Q(immatriculation__icontains=search_value) |
            Q(declaration__icontains=search_value) |
            Q(numdos__icontains=search_value)
        )

    # Ordering map aligned with DataTables columns
    dt_columns_to_fields = [
        'dateheurecargaison__date',            # 0
        'frontiere__nomville',                 # 1
        'importateur__nomimportateur',         # 2
        'entrepot__nomentrepot',               # 3
        'produit__nomproduit',                 # 4
        'volume',                               # 5
        'immatriculation',                      # 6
        'declaration',                          # 7
        'numdos',                               # 8
        'requisitiondackdate__date',           # 9
        'entrepot_echantillon__dateechantillonage__date', # 10
        'entrepot_echantillon__laboreception__datereceptionlabo__date', # 11
        'impressionresultat__printDate',       # 12
        'inspection__dateinspection',          # 13
        'dateDechargement',                    # 14
        'volConst',                             # 15
        None,                                   # 16
        'inspection__temp',                     # 17
        None,                                   # 18
        'mtaT',                                 # 19
        'mtvT',                                 # 20
        'gsvT',                                 # 21
        None,                                   # 22
    ]

    order = params.get('order') or []
    order_by = []
    try:
        for o in order:
            col = int(o.get('column'))
            dirv = o.get('dir') or 'asc'
            field = dt_columns_to_fields[col] if 0 <= col < len(dt_columns_to_fields) else None
            if field:
                order_by.append(('-' if dirv == 'desc' else '') + field)
    except Exception:
        order_by = []
    if order_by:
        qs = qs.order_by(*order_by)
    else:
        qs = qs.order_by('-dateheurecargaison__date')

    # Build workbook
    wb = Workbook(write_only=True)
    ws = wb.create_sheet('Rapport')
    try:
        if len(wb.worksheets) > 1:
            wb.remove(wb.worksheets[0])
    except Exception:
        pass

    headers = [
        'DATE ENTREE','FRONTIERE','FOURNISSEUR','ENTREPOT','PRODUIT','VOL.DECL.',
        'IMMATR.','#.DECLARATION','#.DOSSIER','DATE REQUISITION','DATE ECHANTILLONNAGE',
        'DATE RECEPTION LABO','DATE D\'ANALYSE','DATE D\'INSPECTION','DATE DE DECHARGEMENT',
        'VOL JAUGE (GOV)','DENSITE @15','TEMPERATURE','VCF','MTA','MTV','GSV'
    ]
    ws.append(headers)

    def _to_float(s):
        try:
            if s is None:
                return None
            if isinstance(s, (int, float)):
                return float(s)
            s = str(s).strip().replace(',', '.')
            return float(s) if s else None
        except Exception:
            return None

    for row in qs.iterator(chunk_size=1000):
        dens = _to_float(row.get('inspection__dens'))
        temp = _to_float(row.get('inspection__temp'))
        d15 = None
        vcf_val = None
        try:
            if dens is not None and temp is not None:
                d15 = densite15(temp, dens)
                vcf_val = vcf(d15 if d15 is not None else dens, temp)
        except Exception:
            d15 = None
            vcf_val = None
        # Round for readability
        if isinstance(d15, (int, float)):
            try: d15 = round(float(d15), 5)
            except Exception: pass
        if isinstance(vcf_val, (int, float)):
            try: vcf_val = round(float(vcf_val), 6)
            except Exception: pass

        def r3(v):
            try:
                return round(float(v), 3) if v is not None else None
            except Exception:
                return v

        ws.append([
            row.get('dateheurecargaison__date'),
            row.get('frontiere__nomville'),
            row.get('importateur__nomimportateur'),
            row.get('entrepot__nomentrepot'),
            row.get('produit__nomproduit'),
            row.get('volume'),
            row.get('immatriculation'),
            row.get('declaration'),
            row.get('numdos'),
            row.get('requisitiondackdate__date'),
            row.get('entrepot_echantillon__dateechantillonage__date'),
            row.get('entrepot_echantillon__laboreception__datereceptionlabo__date'),
            row.get('impressionresultat__printDate'),
            row.get('inspection__dateinspection'),
            row.get('dateDechargement'),
            row.get('volConst'),
            d15,
            temp,
            vcf_val,
            r3(row.get('mtaT')),
            r3(row.get('mtvT')),
            r3(row.get('gsvT')),
        ])

    # Save to storage
    now = timezone.now().strftime('%Y%m%d%H%M%S')
    file_name = f"rapport_activites_{now}.xlsx"
    file_path = f"xlsx/{user_id}/{file_name}"
    # Ensure folder prefix exists (default_storage handles folders implicitly)
    content = io.BytesIO()
    wb.save(content)
    content.seek(0)
    default_storage.save(file_path, ContentFile(content.read()))
    file_url = default_storage.url(file_path)

    return {
        'file_url': file_url,
        'file_name': file_name,
    }



