import os
import io
import datetime

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

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
        # Lazy import to avoid hard dependency at worker startup
        try:
            from django_tables2 import RequestConfig  # type: ignore
            from django_tables2.export.export import TableExport  # type: ignore
        except Exception as imp_err:
            return {'error': f"django-tables2 is required for export_report_task: {imp_err}"}

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



@app.task(bind=True)
def export_rapport_activites_task(self, params: dict, user_id: int):
    """
    Build the Rapport d'activités Excel asynchronously using server-side filters/order.
    Saves the file to the default storage and returns a public URL and filename.

    IMPORTANT CHANGE:
      - We DO NOT filter by "frontiere" anymore.
      - The UI field "frontiere" is now treated as "entrepot_ville_id" (filters by entrepot__ville_id) for compatibility.
      - The primary param is now "entite" (also treated as entrepot_ville_id).
    """
    import io
    import datetime
    from django.db.models import Q, Sum
    from django.utils import timezone
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    from openpyxl import Workbook

    # Rebuild queryset similar to responseRapportActivite
    qs = Cargaison.objects.filter(
        # entrepot__ville__affectationville__username_id=user_id,

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

    # ---------- Helpers ----------
    def g(k):
        v = params.get(k)
        return (v or '').strip() if isinstance(v, str) else (v or '')

    # ---------- Filters ----------
    date_from = g('date_from')
    date_to = g('date_to')

    # ⛔️ DO NOT USE "frontiere" as a direct frontiere filter anymore
    # ✅ Instead, treat "entite" (primary) and optionally "frontiere" (compatibility)
    #    as entrepot_ville_id (ville PK) if entrepot_ville_id is not explicitly provided
    frontiere_value = g('frontiere')  # compatibility: treat as ville id
    entite_value = g('entite')        # primary: treat as ville id

    imp_name = g('importateur')
    ent_name = g('entrepot')
    ent_ids = params.get('entrepot_ids') or []

    # New: allow filtering by entrepot.ville_id directly
    ent_ville_id = params.get('entrepot_ville_id')
    ent_ville_ids = params.get('entrepot_ville_ids') or []

    # Fallback precedence for ville selection: explicit param > entite > frontiere (compat)
    if ent_ville_id is None or str(ent_ville_id).strip() == '':
        if entite_value:
            ent_ville_id = entite_value
        elif frontiere_value:
            ent_ville_id = frontiere_value

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

    # ✅ Apply entrepot__ville__idville filter (list > single)
    try:
        if ent_ville_ids:
            _ids = [int(x) for x in ent_ville_ids if str(x).isdigit()]
            if _ids:
                adv &= Q(entrepot__ville__idville__in=_ids)

        elif ent_ville_id is not None and str(ent_ville_id).strip() != '':
            if str(ent_ville_id).isdigit():
                adv &= Q(entrepot__ville__idville=int(ent_ville_id))
    except Exception:
        pass

    # If a list of entrepôt IDs is explicitly provided, apply it (takes precedence over name filter)
    if ent_ids:
        try:
            ids = [int(x) for x in ent_ids if str(x).isdigit()]
            if ids:
                adv &= Q(entrepot_id__in=ids)
        except Exception:
            pass

    if imp_name:
        adv &= Q(importateur__nomimportateur__istartswith=imp_name)
    if ent_name and not ent_ids:
        adv &= Q(entrepot__nomentrepot__istartswith=ent_name)
    if prod_name:
        adv &= Q(produit__nomproduit__istartswith=prod_name)
    if immat:
        adv &= Q(immatriculation__istartswith=immat)
    if decl:
        adv &= Q(declaration__istartswith=decl)
    if numd:
        adv &= Q(numdos__istartswith=numd)

    if adv:
        qs = qs.filter(adv)

    # ---------- Global search ----------
    search_value = g('search[value]')
    if search_value:
        # Optimization: use istartswith for indexed fields and group them.
        # Prefix search on indexed fields (immatriculation, declaration, numdos) is much faster.
        qs = qs.filter(
            Q(immatriculation__istartswith=search_value) |
            Q(declaration__istartswith=search_value) |
            Q(numdos__istartswith=search_value) |
            Q(frontiere__nomville__icontains=search_value) |
            Q(importateur__nomimportateur__icontains=search_value) |
            Q(entrepot__nomentrepot__icontains=search_value) |
            Q(produit__nomproduit__icontains=search_value)
        )

    # ---------- Ordering ----------
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

    qs = qs.order_by(*order_by) if order_by else qs.order_by('-dateheurecargaison__date')

    # ---------- Workbook ----------
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

    EXCEL_MAX_DATA_ROWS = 1048576 - 1
    total = qs.count()
    if total > EXCEL_MAX_DATA_ROWS:
        raise Exception("Le résultat dépasse la limite d’Excel (1 048 576 lignes). Affinez vos filtres et réessayez.")

    done = 0

    def _fmt_dt(val):
        try:
            if val is None:
                return None
            if isinstance(val, datetime.datetime):
                if timezone.is_aware(val):
                    val = timezone.localtime(val)
                return val.strftime('%d/%m/%Y %H:%M')
            if isinstance(val, datetime.date):
                return val.strftime('%d/%m/%Y')
        except Exception:
            return None
        return str(val)

    # Optimized Loop for large datasets
    # Caching function lookups
    f_densite15 = densite15
    f_vcf = vcf
    
    def r3(v):
        try:
            return round(float(v), 3) if v is not None else None
        except Exception:
            return v

    for row in qs.iterator(chunk_size=2000):
        dens = _to_float(row.get('inspection__dens'))
        temp = _to_float(row.get('inspection__temp'))
        d15 = None
        vcf_val = None
        
        if dens is not None and temp is not None:
            try:
                # Direct calculation only if values are present
                d15 = f_densite15(temp, dens)
                if d15 is not None:
                    vcf_val = f_vcf(d15, temp)
                    # Rounding optimized
                    d15 = round(float(d15), 5)
                if vcf_val is not None:
                    vcf_val = round(float(vcf_val), 6)
            except Exception:
                d15 = None
                vcf_val = None

        ws.append([
            _fmt_dt(row.get('dateheurecargaison__date')),
            row.get('frontiere__nomville'),
            row.get('importateur__nomimportateur'),
            row.get('entrepot__nomentrepot'),
            row.get('produit__nomproduit'),
            row.get('volume'),
            row.get('immatriculation'),
            row.get('declaration'),
            row.get('numdos'),
            _fmt_dt(row.get('requisitiondackdate__date')),
            _fmt_dt(row.get('entrepot_echantillon__dateechantillonage__date')),
            _fmt_dt(row.get('entrepot_echantillon__laboreception__datereceptionlabo__date')),
            _fmt_dt(row.get('impressionresultat__printDate')),
            _fmt_dt(row.get('inspection__dateinspection')),
            _fmt_dt(row.get('dateDechargement')),
            row.get('volConst'),
            d15,
            temp,
            vcf_val,
            r3(row.get('mtaT')),
            r3(row.get('mtvT')),
            r3(row.get('gsvT')),
        ])

        done += 1
        # Update progress less frequently to reduce Redis/database I/O
        if done % 2000 == 0 or done == total:
            percent = round((done / max(total, 1)) * 100, 2)
            try:
                self.update_state(state='PROGRESS', meta={'total': total, 'done': done, 'percent': percent})
            except Exception:
                pass

    # ---------- Save to storage ----------
    now_dt = timezone.now()
    now = now_dt.strftime('%Y%m%d%H%M%S')
    file_name = f"rapport_activites_{now}.xlsx"
    file_path = f"xlsx/{now_dt.strftime('%Y')}/{now_dt.strftime('%m')}/{file_name}"

    content = io.BytesIO()
    wb.save(content)
    content.seek(0)
    default_storage.save(file_path, ContentFile(content.read()))
    file_url = default_storage.url(file_path)

    return {'file_url': file_url, 'file_name': file_name, 'expires_in_hours': 24}



# --- Cleanup task: delete exported files older than 24 hours ---
@app.task(bind=True)
def cleanup_old_exports(self):
    """
    Delete files under xlsx/ older than 24 hours using storage's modified_time.
    Works with FileSystemStorage and S3Boto3Storage.
    """
    cutoff = timezone.now() - datetime.timedelta(hours=24)

    from django.core.files.storage import default_storage

    def list_recursive(prefix):
        try:
            dirs, files = default_storage.listdir(prefix)
        except Exception:
            return []
        paths = [f"{prefix.rstrip('/')}/{f}" for f in files]
        for d in dirs:
            sub_prefix = f"{prefix.rstrip('/')}/{d}"
            paths.extend(list_recursive(sub_prefix))
        return paths

    base_prefix = 'xlsx'
    to_check = list_recursive(base_prefix)
    deleted = 0
    checked = 0
    for name in to_check:
        checked += 1
        try:
            mtime = default_storage.modified_time(name)
            # Some backends return naive datetimes
            if timezone.is_naive(mtime):
                mtime = timezone.make_aware(mtime, timezone.get_current_timezone())
            if mtime < cutoff:
                default_storage.delete(name)
                deleted += 1
        except Exception:
            # ignore errors per file
            continue

    return {'checked': checked, 'deleted': deleted}




@app.task(bind=True)
def export_kpi_details_to_excel(self, user_id: int, kpi: str, year: int):
    """
    Build an Excel file for KPI details (full dataset for the current user + year).
    Columns: DATE/HEURE, FRONTIÈRE, IMPORTATEUR, ENTREPÔT, PRODUIT, VOLUME, and
    one KPI-specific date column label as requested by the product owner.

    Returns { file_url, file_name, expires_in_hours } on success.
    """
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage

    # Base queryset within user scope and year
    base = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user_id,
        dateheurecargaison__year=year
    ).values(
        'dateheurecargaison',
        'frontiere__nomville',
        'importateur__nomimportateur',
        'entrepot__nomentrepot',
        'produit__nomproduit',
        'volume',
        'requisitiondackdate__date',
        'entrepot_echantillon__dateechantillonage__date',
        'entrepot_echantillon__laboreception__datereceptionlabo__date',
    ).order_by('-dateheurecargaison')

    # Map KPI to filter and label+date field
    kpi = (kpi or '').strip()
    date_label = 'Date'
    date_key = 'dateheurecargaison'

    if kpi == 'attente_echantillonnage':
        qs = base.filter(etat="En attente d'echantillonage")
        date_label = 'Date Réquisition'
        date_key = 'requisitiondackdate__date'
    elif kpi == 'attente_reception_labo':
        qs = base.filter(etat="Echantillonner")
        date_label = "Date Échantillonnage"
        date_key = 'entrepot_echantillon__dateechantillonage__date'
    elif kpi == 'attente_resultats':
        qs = base.filter(etat="Analyse Labo en cours")
        date_label = 'Date Réception Labo'
        date_key = 'entrepot_echantillon__laboreception__datereceptionlabo__date'
    elif kpi == 'attente_inspection':
        qs = base.filter(etatInspection=True)
        date_label = "Date Échantillonnage"
        date_key = 'entrepot_echantillon__dateechantillonage__date'
    else:
        # total or any other -> no extra filter, use cargaison date
        qs = base
        date_label = 'Date Cargaison'
        date_key = 'dateheurecargaison'

    # Build workbook
    wb = Workbook()
    ws = wb.active
    ws.title = 'KPI'

    headers = [
        'DATE/HEURE', 'FRONTIÈRE', 'IMPORTATEUR', 'ENTREPÔT', 'PRODUIT', 'VOLUME', date_label
    ]
    ws.append(headers)

    def _fmt_dt(v):
        if not v:
            return ''
        try:
            # Support datetime/date/str
            if hasattr(v, 'strftime'):
                return v.strftime('%Y-%m-%d %H:%M')
            return str(v)
        except Exception:
            return str(v)

    total = qs.count()
    done = 0

    # Iterate in chunks to avoid memory spikes
    chunk_size = 2000
    for start in range(0, total, chunk_size):
        for row in qs[start:start+chunk_size]:
            ws.append([
                _fmt_dt(row.get('dateheurecargaison')),
                row.get('frontiere__nomville') or '',
                row.get('importateur__nomimportateur') or '',
                row.get('entrepot__nomentrepot') or '',
                row.get('produit__nomproduit') or '',
                row.get('volume') if row.get('volume') is not None else '',
                _fmt_dt(row.get(date_key)),
            ])

            done += 1
            if done % 1000 == 0:
                try:
                    self.update_state(state='PROGRESS', meta={'total': total, 'done': done, 'percent': round(done/max(total,1)*100,2)})
                except Exception:
                    pass

    # Save to storage
    now_dt = timezone.now()
    now = now_dt.strftime('%Y%m%d%H%M%S')
    safe_kpi = (kpi or 'total').replace(' ', '_')
    file_name = f"kpi_{safe_kpi}_{now}.xlsx"
    file_path = f"xlsx/kpi/{now_dt.strftime('%Y')}/{now_dt.strftime('%m')}/{file_name}"

    content = io.BytesIO()
    wb.save(content)
    content.seek(0)
    default_storage.save(file_path, ContentFile(content.read()))
    file_url = default_storage.url(file_path)

    return {
        'file_url': file_url,
        'file_name': file_name,
        'expires_in_hours': 24,
    }



