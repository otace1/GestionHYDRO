# labo/tasks.py

import os
import io
import importlib
import tempfile

from celery import shared_task
from django.db.models import Q
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models.functions import ExtractMonth, ExtractYear
from openpyxl import Workbook
from pypdf import PdfWriter, PdfReader

from enreg.models import (
    Cargaison, ResultatAnalyse, ImpressionResultat, Produit,
    Entrepot_echantillon, LaboReception, AffectationParametre
)
from labo.utils import render_to_pdf_content


@shared_task(bind=True)
def generate_certificates_pdf_task(self, selected_ids, province, sign_gauche_data, sign_droite_data, laboratoire_name, marks_printed=True, user_id=None):
    """
    Celery task to generate one or more certificate PDFs.
    If multiple, they are merged into a single PDF.
    """
    total = len(selected_ids)
    if total == 0:
        return {"error": "No IDs provided"}

    writer = PdfWriter()
    processed_count = 0

    from accounts.models import ListeLaboratoire, UserActivityLog
    laboratoireData = ListeLaboratoire.objects.get(denominationLaboratoire=laboratoire_name)

    for pk in selected_ids:
        try:
            # Re-fetch objects to ensure fresh data in worker
            cargaison = Cargaison.objects.select_related(
                'entrepot_echantillon',
                'entrepot_echantillon__laboreception'
            ).get(idcargaison=pk)
            produit = cargaison.nom_produit

            impressionData = ImpressionResultat.objects.filter(idcargaison_id=pk).first()
            
            labo_rec = cargaison.entrepot_echantillon.laboreception
            mois = labo_rec.datereceptionlabo.month if labo_rec and labo_rec.datereceptionlabo else None
            annee = labo_rec.datereceptionlabo.year if labo_rec and labo_rec.datereceptionlabo else None

            echantillon = cargaison.entrepot_echantillon
            laboratoire = labo_rec

            template = ""
            context = {
                'cargaison': cargaison,
                'echantillon': echantillon,
                'laboratoire': laboratoire,
                'mois': mois,
                'annee': annee,
                'province': province,
                'signGauche': sign_gauche_data,
                'signDroite': sign_droite_data,
                'impressionData': impressionData,
                'laboratoireData': laboratoireData,
            }

            # Optimization: Fetch all analysis results in one query
            results = ResultatAnalyse.objects.filter(idcargaison=pk).values('idParametre_id', 'valeurResultat', 'valeurResultatChar')
            res_dict = {r['idParametre_id']: r for r in results}

            if produit == 'GASOIL':
                template = 'report/Report1/gasoilreport.html'
                context.update({
                    'couleurastm': res_dict.get(8, {}).get('valeurResultatChar', ''),
                    'aciditetotal': res_dict.get(1, {}).get('valeurResultat', ''),
                    'soufre': res_dict.get(34, {}).get('valeurResultat', ''),
                    'massevolumique': res_dict.get(21, {}).get('valeurResultat', ''),
                    'massevolumique15': res_dict.get(20, {}).get('valeurResultat', ''),
                    'distillation': res_dict.get(100, {}).get('valeurResultat', ''),
                    'distillation10': res_dict.get(11, {}).get('valeurResultat', ''),
                    'distillation20': res_dict.get(12, {}).get('valeurResultat', ''),
                    'distillation50': res_dict.get(13, {}).get('valeurResultat', ''),
                    'distillation90': res_dict.get(15, {}).get('valeurResultat', ''),
                    'pointinitial': res_dict.get(30, {}).get('valeurResultat', ''),
                    'pointfinal': res_dict.get(29, {}).get('valeurResultat', ''),
                    'pointeclair': res_dict.get(25, {}).get('valeurResultat', ''),
                    'viscosite': res_dict.get(38, {}).get('valeurResultat', ''),
                    'pointecoulement': res_dict.get(26, {}).get('valeurResultat', ''),
                    'teneureau': res_dict.get(35, {}).get('valeurResultat', ''),
                    'sediment': res_dict.get(32, {}).get('valeurResultat', ''),
                    'indicecetane': res_dict.get(19, {}).get('valeurResultat', ''),
                    'recuperation362': res_dict.get(10, {}).get('valeurResultat', ''),
                    'cendre': res_dict.get(3, {}).get('valeurResultat', ''),
                })
                try:
                    corrosion_str = res_dict.get(6, {}).get('valeurResultat', '')
                    context['corrosion'] = int(corrosion_str) if corrosion_str != '' else ''
                except: context['corrosion'] = ''

            elif produit == 'MOGAS':
                template = 'report/Report1/mogasreport.html'
                context.update({
                    'aspect': res_dict.get(2, {}).get('valeurResultatChar', ''),
                    'odeur': res_dict.get(22, {}).get('valeurResultatChar', ''),
                    'couleursaybolt': res_dict.get(8, {}).get('valeurResultatChar', ''),
                    'soufre': res_dict.get(34, {}).get('valeurResultat', ''),
                    'distillation': res_dict.get(100, {}).get('valeurResultat', ''),
                    'pointfinal': res_dict.get(29, {}).get('valeurResultat', ''),
                    'residu': res_dict.get(31, {}).get('valeurResultat', ''),
                    'pourcent10': res_dict.get(11, {}).get('valeurResultat', ''),
                    'pourcent20': res_dict.get(12, {}).get('valeurResultat', ''),
                    'pourcent50': res_dict.get(13, {}).get('valeurResultat', ''),
                    'pourcent70': res_dict.get(14, {}).get('valeurResultat', ''),
                    'pourcent90': res_dict.get(15, {}).get('valeurResultat', ''),
                    'tensionvapeur': res_dict.get(36, {}).get('valeurResultat', ''),
                    'difftemperature': res_dict.get(9, {}).get('valeurResultat', ''),
                    'plomb': res_dict.get(24, {}).get('valeurResultat', ''),
                    'indiceoctane': res_dict.get(18, {}).get('valeurResultat', ''),
                    'massevolumique15': res_dict.get(20, {}).get('valeurResultat', ''),
                })
                try:
                    corrosion_str = res_dict.get(7, {}).get('valeurResultat', '')
                    context['corrosion'] = int(corrosion_str) if corrosion_str != '' else ''
                except: context['corrosion'] = ''

            elif produit == 'JET A1':
                template = 'report/Report1/jeta1report.html'
                context.update({
                    'aspect': res_dict.get(2, {}).get('valeurResultatChar', ''),
                    'couleursaybolt': res_dict.get(8, {}).get('valeurResultatChar', ''),
                    'aciditetotal': res_dict.get(1, {}).get('valeurResultat', ''),
                    'soufre': res_dict.get(34, {}).get('valeurResultat', ''),
                    'soufremercaptan': res_dict.get(33, {}).get('valeurResultat', ''),
                    'docteurtest': res_dict.get(16, {}).get('valeurResultat', ''),
                    'distillation': res_dict.get(100, {}).get('valeurResultat', ''),
                    'pointinitial': res_dict.get(30, {}).get('valeurResultat', ''),
                    'pointfinal': res_dict.get(29, {}).get('valeurResultat', ''),
                    'pointfumee': res_dict.get(28, {}).get('valeurResultat', ''),
                    'pointeclair': res_dict.get(25, {}).get('valeurResultat', ''),
                    'freezingpoint': res_dict.get(17, {}).get('valeurResultat', ''),
                    'residu': res_dict.get(31, {}).get('valeurResultat', ''),
                    'perte': res_dict.get(23, {}).get('valeurResultat', ''),
                    'massevolumique15': res_dict.get(20, {}).get('valeurResultat', ''),
                    'viscosite': res_dict.get(37, {}).get('valeurResultat', ''),
                    'pointinflammabilite': res_dict.get(27, {}).get('valeurResultat', ''),
                    'teneureau': res_dict.get(35, {}).get('valeurResultat', ''),
                    'conductivite': res_dict.get(4, {}).get('valeurResultat', ''),
                    'vol10': res_dict.get(11, {}).get('valeurResultat', ''),
                    'vol20': res_dict.get(12, {}).get('valeurResultat', ''),
                    'vol30': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol40': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol50': res_dict.get(13, {}).get('valeurResultat', ''),
                    'vol60': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol70': res_dict.get(14, {}).get('valeurResultat', ''),
                    'vol80': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol90': res_dict.get(15, {}).get('valeurResultat', ''),
                })
                try:
                    corrosion_str = res_dict.get(5, {}).get('valeurResultat', '')
                    context['corrosion'] = int(corrosion_str) if corrosion_str != '' else ''
                except: context['corrosion'] = ''

            elif produit == 'PETROLE LAMPANT':
                template = 'report/Report1/petrolereport.html'
                context.update({
                    'aspect': res_dict.get(2, {}).get('valeurResultatChar', ''),
                    'couleursaybolt': res_dict.get(8, {}).get('valeurResultatChar', ''),
                    'aciditetotal': res_dict.get(1, {}).get('valeurResultat', ''),
                    'soufre': res_dict.get(34, {}).get('valeurResultat', ''),
                    'soufremercaptan': res_dict.get(33, {}).get('valeurResultat', ''),
                    'docteurtest': res_dict.get(16, {}).get('valeurResultat', ''),
                    'distillation': res_dict.get(100, {}).get('valeurResultat', ''),
                    'pointinitial': res_dict.get(30, {}).get('valeurResultat', ''),
                    'pointfinal': res_dict.get(29, {}).get('valeurResultat', ''),
                    'pointfumee': res_dict.get(28, {}).get('valeurResultat', ''),
                    'pointeclair': res_dict.get(25, {}).get('valeurResultat', ''),
                    'freezingpoint': res_dict.get(17, {}).get('valeurResultat', ''),
                    'residu': res_dict.get(31, {}).get('valeurResultat', ''),
                    'perte': res_dict.get(23, {}).get('valeurResultat', ''),
                    'massevolumique15': res_dict.get(20, {}).get('valeurResultat', ''),
                    'viscosite': res_dict.get(37, {}).get('valeurResultat', ''),
                    'pointinflammabilite': res_dict.get(27, {}).get('valeurResultat', ''),
                    'teneureau': res_dict.get(35, {}).get('valeurResultat', ''),
                    'conductivite': res_dict.get(4, {}).get('valeurResultat', ''),
                    'vol10': res_dict.get(11, {}).get('valeurResultat', ''),
                    'vol20': res_dict.get(12, {}).get('valeurResultat', ''),
                    'vol30': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol40': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol50': res_dict.get(13, {}).get('valeurResultat', ''),
                    'vol60': res_dict.get(44, {}).get('valeurResultat', ''),
                    'vol70': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol80': res_dict.get(100, {}).get('valeurResultat', ''),
                    'vol90': res_dict.get(15, {}).get('valeurResultat', ''),
                })
                try:
                    corrosion_str = res_dict.get(5, {}).get('valeurResultat', '')
                    context['corrosion'] = int(corrosion_str) if corrosion_str != '' else ''
                except: context['corrosion'] = ''

            if template:
                pdf_content = render_to_pdf_content(template, context)
                if pdf_content:
                    writer.append(io.BytesIO(pdf_content))
                    if marks_printed:
                        ImpressionResultat.objects.filter(idcargaison=pk).update(isPrinted=True)
                        if user_id:
                            UserActivityLog.objects.create(
                                user_id=user_id,
                                action="Certificat Imprimé",
                                object_id=str(pk),
                                description=f"Certificat pour cargaison {pk} (Produit: {produit}) imprimé via tâche groupée."
                            )
            
            processed_count += 1
            percent = round((processed_count / total) * 100, 2)
            self.update_state(state='PROGRESS', meta={'total': total, 'done': processed_count, 'percent': percent})

        except Exception as e:
            print(f"Error processing idcargaison {pk}: {e}")

    if len(writer.pages) == 0:
        return {"error": "No PDF pages generated"}

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)

    now_dt = timezone.now()
    ts = now_dt.strftime("%Y%m%d%H%M%S")
    file_name = f"certificats_{ts}.pdf"
    rel_path = f"pdf/certificats/{now_dt.strftime('%Y')}/{now_dt.strftime('%m')}/{file_name}"
    
    storage_path = default_storage.save(rel_path, ContentFile(output.read()))
    file_url = default_storage.url(storage_path)

    return {
        "storage_key": storage_path,
        "file_url": file_url,
        "file_name": file_name,
        "total": total,
        "done": processed_count,
        "percent": 100.0,
    }


def _parse_date_range(value: str):
    """
    Expects: 'YYYY-MM-DD - YYYY-MM-DD'
    Returns: (date|None, date|None)
    """
    try:
        if not value:
            return None, None
        value = str(value).strip()
        if " - " not in value:
            return None, None

        a, b = value.split(" - ", 1)

        dtmod = importlib.import_module("datetime")  # ✅ real module, never shadowed
        start = dtmod.datetime.strptime(a.strip(), "%Y-%m-%d").date()
        end = dtmod.datetime.strptime(b.strip(), "%Y-%m-%d").date()

        if end < start:
            start, end = end, start
        return start, end
    except Exception:
        return None, None


def _fmt_date(v):
    """
    Robust formatter immune to 'datetime' name shadowing.
    """
    if v is None:
        return None

    dtmod = importlib.import_module("datetime")  # ✅ real module
    dt_cls = dtmod.datetime
    date_cls = dtmod.date

    if isinstance(v, dt_cls):
        try:
            if timezone.is_aware(v):
                v = timezone.localtime(v)
        except Exception:
            pass
        return v.strftime("%Y-%m-%d %H:%M")

    if isinstance(v, date_cls):
        return v.strftime("%Y-%m-%d")

    return str(v)


def _build_reception_queryset(user_id: int, filters: dict):
    qs = Cargaison.objects.filter(
        entrepot__ville__affectationville__username_id=user_id,
        entrepot_echantillon__laboreception__datereceptionlabo__isnull=False,
    )

    date_type = (filters.get("date_type") or "reception").strip()
    date_range = (filters.get("date_range") or "").strip()
    entrepot = (filters.get("entrepot") or "").strip()
    num_re = (filters.get("num_re") or "").strip()
    immat = (filters.get("immatriculation") or "").strip()
    code_labo = (filters.get("code_labo") or "").strip()
    search_value = (filters.get("search") or "").strip()

    start_date, end_date = _parse_date_range(date_range)
    if start_date and end_date:
        if date_type == "echantillon":
            qs = qs.filter(entrepot_echantillon__dateechantillonage__date__range=(start_date, end_date))
        else:
            qs = qs.filter(entrepot_echantillon__laboreception__datereceptionlabo__date__range=(start_date, end_date))

    if entrepot:
        qs = qs.filter(entrepot__nomentrepot__icontains=entrepot)
    if num_re:
        qs = qs.filter(entrepot_echantillon__numrappechauto__icontains=num_re)
    if immat:
        qs = qs.filter(immatriculation__icontains=immat)
    if code_labo:
        qs = qs.filter(entrepot_echantillon__laboreception__codelabo__icontains=code_labo)

    if search_value:
        qs = qs.filter(
            Q(numdos__icontains=search_value)
            | Q(entrepot_echantillon__numrappechauto__icontains=search_value)
            | Q(entrepot_echantillon__laboreception__codelabo__icontains=search_value)
            | Q(entrepot__nomentrepot__icontains=search_value)
            | Q(importateur__nomimportateur__icontains=search_value)
            | Q(immatriculation__icontains=search_value)
            | Q(produit__nomproduit__icontains=search_value)
        )

    return qs


@shared_task(bind=True)
def export_reception_rapports_to_xlsx(self, user_id: int, filters: dict):
    try:
        try:
            self.update_state(state="PROGRESS", meta={"total": 0, "done": 0, "percent": 0})
        except Exception:
            pass

        qs = _build_reception_queryset(user_id, filters).order_by(
            "-entrepot_echantillon__laboreception__datereceptionlabo"
        )

        values_qs = qs.values(
            "numdos",
            "entrepot_echantillon__numrappechauto",
            "entrepot_echantillon__laboreception__codelabo",
            "entrepot_echantillon__dateechantillonage__date",
            "entrepot_echantillon__laboreception__datereceptionlabo__date",
            "entrepot__nomentrepot",
            "importateur__nomimportateur",
            "immatriculation",
            "produit__nomproduit",
        )

        total = values_qs.count()

        EXCEL_MAX_DATA_ROWS = 1048576 - 1
        if total > EXCEL_MAX_DATA_ROWS:
            raise Exception(
                "Le résultat dépasse la limite d’Excel (1 048 576 lignes). "
                "Affinez vos filtres et réessayez."
            )

        wb = Workbook(write_only=True)
        ws = wb.create_sheet("Rapports")
        ws.append([
            "NUM.DOSS", "NUM.RE", "CODE LABO", "DATE ECHANT.",
            "DATE RECEP.", "ENTREPOT", "FOURNISSEUR",
            "IMMATRICULATION", "PRODUIT"
        ])

        done = 0
        chunk_size = 1000

        for r in values_qs.iterator(chunk_size=chunk_size):
            ws.append([
                r.get("numdos"),
                r.get("entrepot_echantillon__numrappechauto"),
                r.get("entrepot_echantillon__laboreception__codelabo"),
                _fmt_date(r.get("entrepot_echantillon__dateechantillonage__date")),
                _fmt_date(r.get("entrepot_echantillon__laboreception__datereceptionlabo__date")),
                r.get("entrepot__nomentrepot"),
                r.get("importateur__nomimportateur"),
                r.get("immatriculation"),
                r.get("produit__nomproduit"),
            ])

            done += 1
            if done % chunk_size == 0 or done == total:
                try:
                    percent = round((done / max(total, 1)) * 100, 2) if total else 100.0
                    self.update_state(state="PROGRESS", meta={"total": total, "done": done, "percent": percent})
                except Exception:
                    pass

        now_dt = timezone.now()
        ts = now_dt.strftime("%Y%m%d%H%M%S")
        file_name = f"rapport_reception_{ts}.xlsx"
        # Since MediaRootS3BotoStorage has location="media", 
        # saving "xlsx/..." results in "media/xlsx/..." in the bucket.
        # We store the path relative to the storage root.
        rel_path = f"xlsx/{now_dt.strftime('%Y')}/{now_dt.strftime('%m')}/{file_name}"
        
        bio = io.BytesIO()
        wb.save(bio)
        bio.seek(0)

        # Save to default storage (S3/Spaces)
        storage_path = default_storage.save(rel_path, ContentFile(bio.read()))
        # default_storage.url(storage_path) should return a usable URL (possibly already signed)
        file_url = default_storage.url(storage_path)

        # We return the actual path returned by save() to be safe
        storage_key = storage_path

        # Legacy fallback: also save to system temp dir for local serving if needed
        try:
            tmp_fname = f"rapport_reception_{user_id}_{self.request.id}.xlsx"
            tmp_path = os.path.join(tempfile.gettempdir(), tmp_fname)
            bio.seek(0)
            with open(tmp_path, "wb") as f:
                f.write(bio.read())
        except Exception:
            pass

        try:
            self.update_state(state="SUCCESS", meta={
                "total": total, "done": done, "percent": 100.0,
                "storage_key": storage_key, "file_url": file_url, "file_name": file_name
            })
        except Exception:
            pass

        return {
            "storage_key": storage_key,
            "file_url": file_url,
            "file_name": file_name,
            "total": total,
            "done": done,
            "percent": 100.0,
        }

    except Exception as e:
        try:
            self.update_state(state="FAILURE", meta={"total": 0, "done": 0, "percent": 0, "error": str(e)})
        except Exception:
            pass
        raise