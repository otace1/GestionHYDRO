# labo/tasks.py

import os
import io
import importlib

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
def generate_certificates_pdf_task(self, selected_ids, province, sign_gauche_data, sign_droite_data, laboratoire_name, marks_printed=True):
    """
    Celery task to generate one or more certificate PDFs.
    If multiple, they are merged into a single PDF.
    """
    total = len(selected_ids)
    if total == 0:
        return {"error": "No IDs provided"}

    writer = PdfWriter()
    processed_count = 0

    from accounts.models import ListeLaboratoire
    laboratoireData = ListeLaboratoire.objects.get(denominationLaboratoire=laboratoire_name)

    for pk in selected_ids:
        try:
            # Re-fetch objects to ensure fresh data in worker
            cargaison = Cargaison.objects.select_related('produit').get(idcargaison=pk)
            produit = cargaison.produit.nomproduit

            impressionData = ImpressionResultat.objects.get(idcargaison_id=pk)
            
            reception_qs = LaboReception.objects.filter(idcargaison_id=pk).annotate(
                mois_extracted=ExtractMonth('datereceptionlabo'),
                annee_extracted=ExtractYear('datereceptionlabo')
            ).first()

            mois = reception_qs.mois_extracted if reception_qs else None
            annee = reception_qs.annee_extracted if reception_qs else None

            echantillon = Entrepot_echantillon.objects.get(idcargaison=pk)
            laboratoire = LaboReception.objects.get(idcargaison=pk)

            if marks_printed:
                printed = ImpressionResultat.objects.get(idcargaison=pk)
                printed.isPrinted = True
                printed.save(update_fields=['isPrinted'])

            template = ""
            context = {
                'cargaison': cargaison,
                'echantillon': echantillon,
                'laboratoire': laboratoire,
                'mois': mois,
                'annee': annee,
                'signGauche': sign_gauche_data,
                'signDroite': sign_droite_data,
                'impressionData': impressionData,
                'laboratoireData': laboratoireData,
            }

            if produit == 'GASOIL':
                template = 'report/Report1/gasoilreport.html'
                try:
                    context['couleurastm'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=8)[0].valeurResultatChar
                except: context['couleurastm'] = ''
                try:
                    context['aciditetotal'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=1)[0].valeurResultat
                except: context['aciditetotal'] = ''
                try:
                    context['soufre'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[0].valeurResultat
                except: context['soufre'] = ''
                try:
                    context['massevolumique'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=21)[0].valeurResultat
                except: context['massevolumique'] = ''
                try:
                    context['massevolumique15'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[0].valeurResultat
                except: context['massevolumique15'] = ''
                try:
                    context['distillation'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[0].valeurResultat
                except: context['distillation'] = ''
                try:
                    context['cetane'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=3)[0].valeurResultat
                except: context['cetane'] = ''
                try:
                    context['pointéclair'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=23)[0].valeurResultat
                except: context['pointéclair'] = ''
                try:
                    context['viscosité'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=37)[0].valeurResultat
                except: context['viscosité'] = ''
                try:
                    context['pointécoulement'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=24)[0].valeurResultat
                except: context['pointécoulement'] = ''
                try:
                    context['teneur'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=33)[0].valeurResultat
                except: context['teneur'] = ''
                try:
                    context['sediment'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=32)[0].valeurResultat
                except: context['sediment'] = ''
                try:
                    context['carbonne'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=27)[0].valeurResultat
                except: context['carbonne'] = ''
                try:
                    context['cendres'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=2)[0].valeurResultat
                except: context['cendres'] = ''
                try:
                    context['corrosion'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=7)[0].valeurResultat
                except: context['corrosion'] = ''

            elif produit == 'MOGAS':
                template = 'report/Report1/mogasreport.html'
                try:
                    context['couleur'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=9)[0].valeurResultatChar
                except: context['couleur'] = ''
                try:
                    context['ron'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=16)[0].valeurResultat
                except: context['ron'] = ''
                try:
                    context['plomb'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=22)[0].valeurResultat
                except: context['plomb'] = ''
                try:
                    context['distillation'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[0].valeurResultat
                except: context['distillation'] = ''
                try:
                    context['pvr'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=25)[0].valeurResultat
                except: context['pvr'] = ''
                try:
                    context['gommes'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=14)[0].valeurResultat
                except: context['gommes'] = ''
                try:
                    context['soufre'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[0].valeurResultat
                except: context['soufre'] = ''
                try:
                    context['corrosion'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=7)[0].valeurResultat
                except: context['corrosion'] = ''
                try:
                    context['massevolumique'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=21)[0].valeurResultat
                except: context['massevolumique'] = ''
                try:
                    context['massevolumique15'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[0].valeurResultat
                except: context['massevolumique15'] = ''
                try:
                    context['stabilite'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=26)[0].valeurResultat
                except: context['stabilite'] = ''
                try:
                    context['benzen'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=39)[0].valeurResultat
                except: context['benzen'] = ''

            elif produit == 'JET A1':
                template = 'report/Report1/jeta1report.html'
                try:
                    context['pointéclair'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=23)[0].valeurResultat
                except: context['pointéclair'] = ''
                try:
                    context['massevolumique'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=21)[0].valeurResultat
                except: context['massevolumique'] = ''
                try:
                    context['massevolumique15'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[0].valeurResultat
                except: context['massevolumique15'] = ''
                try:
                    context['distillation'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[0].valeurResultat
                except: context['distillation'] = ''
                try:
                    context['pointcongelation'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=28)[0].valeurResultat
                except: context['pointcongelation'] = ''
                try:
                    context['viscosité'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=37)[0].valeurResultat
                except: context['viscosité'] = ''
                try:
                    context['soufre'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[0].valeurResultat
                except: context['soufre'] = ''
                try:
                    context['mercaptan'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=35)[0].valeurResultat
                except: context['mercaptan'] = ''
                try:
                    context['corrosion'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=7)[0].valeurResultat
                except: context['corrosion'] = ''
                try:
                    context['acidite'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=1)[0].valeurResultat
                except: context['acidite'] = ''
                try:
                    context['gommes'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=14)[0].valeurResultat
                except: context['gommes'] = ''
                try:
                    context['aromatique'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=40)[0].valeurResultat
                except: context['aromatique'] = ''
                try:
                    context['cendres'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=2)[0].valeurResultat
                except: context['cendres'] = ''
                try:
                    context['wsim'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=38)[0].valeurResultat
                except: context['wsim'] = ''
                try:
                    context['conductivite'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=41)[0].valeurResultat
                except: context['conductivite'] = ''

            elif produit == 'PETROLE LAMPANT':
                template = 'report/Report1/petrolereport.html'
                try:
                    context['pointéclair'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=23)[0].valeurResultat
                except: context['pointéclair'] = ''
                try:
                    context['massevolumique'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=21)[0].valeurResultat
                except: context['massevolumique'] = ''
                try:
                    context['massevolumique15'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[0].valeurResultat
                except: context['massevolumique15'] = ''
                try:
                    context['distillation'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[0].valeurResultat
                except: context['distillation'] = ''
                try:
                    context['soufre'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[0].valeurResultat
                except: context['soufre'] = ''
                try:
                    context['corrosion'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=7)[0].valeurResultat
                except: context['corrosion'] = ''
                try:
                    context['couleur'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=10)[0].valeurResultat
                except: context['couleur'] = ''
                try:
                    context['pointfumee'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=30)[0].valeurResultat
                except: context['pointfumee'] = ''
                try:
                    context['vol210'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=101)[0].valeurResultat
                except: context['vol210'] = ''

            # Resultat Distillation (Shared logic)
            try:
                context['pi'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=10)[0].valeurResultat
                context['vol10'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=11)[0].valeurResultat
                context['vol20'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=102)[0].valeurResultat
                context['vol30'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=103)[0].valeurResultat
                context['vol40'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=104)[0].valeurResultat
                context['vol50'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=12)[0].valeurResultat
                context['vol60'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=105)[0].valeurResultat
                context['vol70'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=106)[0].valeurResultat
                context['vol80'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=107)[0].valeurResultat
                context['vol90'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=13)[0].valeurResultat
                context['pf'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=15)[0].valeurResultat
                context['recu'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=17)[0].valeurResultat
                context['perte'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=18)[0].valeurResultat
                context['residue'] = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=19)[0].valeurResultat
            except:
                pass

            if template:
                pdf_content = render_to_pdf_content(template, context)
                if pdf_content:
                    writer.append(io.BytesIO(pdf_content))
            
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

        # Legacy fallback: also save to /tmp for local serving if needed
        try:
            tmp_fname = f"rapport_reception_{user_id}_{self.request.id}.xlsx"
            tmp_path = os.path.join("/tmp", tmp_fname)
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