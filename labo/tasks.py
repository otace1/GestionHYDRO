import base64

from PyPDF3 import PdfFileMerger
from celery import Celery
from django.db.models.functions import ExtractYear, ExtractMonth
from django_tables2.export.export import TableExport
from django_tables2 import RequestConfig
from django.http import JsonResponse

from enreg.models import ResultatAnalyse, ImpressionResultat, Produit
from hydrocarbures.celery import app
from labo.tables import *
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import time
import datetime

from labo.utils import render_to_pdf


# app = Celery('tasks', broker='redis://127.0.0.1:6379/0', backend='redis://127.0.0.1:6379/1')


@app.task
def add(x, y):
    return x + y


@app.task
def export_report_task(export_format, queryset_data, request=None):
    try:
        # Initialize the table with the queryset data
        table = RapportLaboratoireEnAttenteReception(queryset_data)

        # If request is provided, configure pagination
        if request:
            RequestConfig(request, paginate={"per_page": 20}).configure(table)

        # Export the table
        exporter = TableExport(export_format, table)
        file_content = exporter.export()

        # Generate a unique file name using datetime
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"table_{current_datetime}.{export_format}"

        # Save the exported file
        file_path = default_storage.save(file_name, ContentFile(file_content))
        file_url = default_storage.url(file_path)

        # Return the URL of the exported file
        return {
            'file_url': file_url,
            'file_name': file_name,
        }
    except Exception as e:
        return {'error': str(e)}


@app.task
def export_report_task_Attente_Res(export_format, queryset_data, request=None):
    try:
        # Initialize the table with the queryset data
        table = RapportLaboratoireEnAttenteResultat(queryset_data)

        # If request is provided, configure pagination
        if request:
            RequestConfig(request, paginate={"per_page": 20}).configure(table)

        # Export the table
        exporter = TableExport(export_format, table)
        file_content = exporter.export()

        # Generate a unique file name using datetime
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"table_{current_datetime}.{export_format}"

        # Save the exported file
        file_path = default_storage.save(file_name, ContentFile(file_content))
        file_url = default_storage.url(file_path)

        # Return the URL of the exported file
        return {
            'file_url': file_url,
            'file_name': file_name,
        }
    except Exception as e:
        return {'error': str(e)}


@app.task
def export_report_task_Attente_Res(export_format, queryset_data, request=None):
    try:
        # Initialize the table with the queryset data
        table = RapportLaboratoireEnAttenteResultat(queryset_data)

        # If request is provided, configure pagination
        if request:
            RequestConfig(request, paginate={"per_page": 20}).configure(table)

        # Export the table
        exporter = TableExport(export_format, table)
        file_content = exporter.export()

        # Generate a unique file name using datetime
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"table_{current_datetime}.{export_format}"

        # Save the exported file
        file_path = default_storage.save(file_name, ContentFile(file_content))
        file_url = default_storage.url(file_path)

        # Return the URL of the exported file
        return {
            'file_url': file_url,
            'file_name': file_name,
        }
    except Exception as e:
        return {'error': str(e)}



@app.task
def export_report_task_cert_imprimer(export_format, queryset_data, request=None):
    try:
        # Initialize the table with the queryset data
        table = RapportLaboratoireEnchPrintedCert(queryset_data)

        # If request is provided, configure pagination
        if request:
            RequestConfig(request, paginate={"per_page": 20}).configure(table)

        # Export the table
        exporter = TableExport(export_format, table)
        file_content = exporter.export()

        # Generate a unique file name using datetime
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"table_{current_datetime}.{export_format}"

        # Save the exported file
        file_path = default_storage.save(file_name, ContentFile(file_content))
        file_url = default_storage.url(file_path)

        # Return the URL of the exported file
        return {
            'file_url': file_url,
            'file_name': file_name,
        }
    except Exception as e:
        return {'error': str(e)}



@app.task
def export_report_task_rapport_cq(export_format, queryset_data, request=None):
    try:
        # Initialize the table with the queryset data
        table = rapportActiviteCQ(queryset_data)

        # If request is provided, configure pagination
        if request:
            RequestConfig(request, paginate={"per_page": 20}).configure(table)

        # Export the table
        exporter = TableExport(export_format, table)
        file_content = exporter.export()

        # Generate a unique file name using datetime
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"table_{current_datetime}.{export_format}"

        # Save the exported file
        file_path = default_storage.save(file_name, ContentFile(file_content))
        file_url = default_storage.url(file_path)

        # Return the URL of the exported file
        return {
            'file_url': file_url,
            'file_name': file_name,
        }
    except Exception as e:
        return {'error': str(e)}


@app.task
def generate_bulk_pdf(selectedRow,province,signGauche,signDroite,laboratoireData):
    bulk_pdf_data = []

    for pk in selectedRow:
        impressionData = ImpressionResultat.objects.get(idcargaison_id=pk)
        d = LaboReception.objects.filter(idcargaison_id=pk).annotate(
            mois=ExtractMonth('datereceptionlabo'),
            annee=ExtractYear('datereceptionlabo')
        ).values('idcargaison_id', 'mois', 'annee')

        for entry in d:
            mois = entry['mois']
            annee = entry['annee']
        #
        # Recuperation du produit de la cargaison
        p = Produit.objects.get(cargaison=pk)
        produit = p.nomproduit

        # Fecthing object with pk corresponding into database
        cargaison = Cargaison.objects.get(idcargaison=pk)
        echantillon = Entrepot_echantillon.objects.get(idcargaison=pk)
        laboratoire = LaboReception.objects.get(idcargaison=pk)

        printed = ImpressionResultat.objects.get(idcargaison=pk)
        printed.isPrinted = 1
        printed.save(update_fields=['isPrinted'])

        # Test pour afficher les differents rapports
        if produit == 'GASOIL':
            template = 'report/Report1/gasoilreport.html'

            # Resultat Gasoil Fetching data into Database
            try:
                couleurastm = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=8)[0].valeurResultatChar
            except:
                couleurastm = ''
            try:
                aciditetotal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=1)[0].valeurResultat
            except:
                aciditetotal = ''
            try:
                soufre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[0].valeurResultat
            except:
                soufre = ''
            try:
                massevolumique = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=21)[0].valeurResultat
            except:
                massevolumique = ''
            try:
                massevolumique15 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[0].valeurResultat
            except:
                massevolumique15 = ''
            try:
                distillation = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[0].valeurResultat
            except:
                distillation = ''
            try:
                distillation10 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=11)[0].valeurResultat
            except:
                distillation10 = ''
            try:
                distillation20 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=12)[0].valeurResultat
            except:
                distillation20 = ''
            try:
                distillation50 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=13)[0].valeurResultat
            except:
                distillation50 = ''
            try:
                distillation90 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=15)[0].valeurResultat
            except:
                distillation90 = ''
            try:
                pointinitial = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=30)[0].valeurResultat
            except:
                pointinitial = ''
            try:
                pointfinal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=29)[0].valeurResultat
            except:
                pointfinal = ''
            try:
                pointeclair = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=25)[0].valeurResultat
            except:
                pointeclair = ''
            try:
                viscosite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=38)[0].valeurResultat
            except:
                viscosite = ''
            try:
                pointecoulement = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=26)[0].valeurResultat
            except:
                pointecoulement = ''
            try:
                teneureau = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=35)[0].valeurResultat
            except:
                teneureau = ''
            try:
                sediment = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=32)[0].valeurResultat
            except:
                sediment = ''
            try:
                corrosion_str = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=6)[0].valeurResultat
                corrosion = int(corrosion_str)
            except:
                corrosion = ''
            try:
                indicecetane = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=19)[0].valeurResultat
            except:
                indicecetane = ''
            # try:
            #     densite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=49)[0].valeurResultat
            # except:
            #     densite = ''
            try:
                recuperation362 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=10)[0].valeurResultat
            except:
                recuperation362 = ''
            try:
                cendre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=3)[0].valeurResultat
            except:
                cendre = ''

            data = {
                'laboratoire': laboratoire,
                'cargaison': cargaison,
                'echantillon': echantillon,
                'annee': annee,
                'mois': mois,
                'province': province,
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
                # 'densite': densite,
                'recuperation362': recuperation362,
                'cendre': cendre,
                'massevolumique15': massevolumique15,
                'signGauche': signGauche,
                'signDroite': signDroite,
                'impressionData': impressionData,
                'laboratoireData': laboratoireData,
            }

            # Rendered PDF report
            pdf = render_to_pdf(template, data)
            pdf_base64 = base64.b64encode(pdf.getvalue()).decode('utf-8')
            bulk_pdf_data.append(pdf_base64)

        if produit == 'MOGAS':
            template = 'report/Report1/mogasreport.html'
            # Resultat Gasoil Fetching data into Database
            try:
                aspect = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=2)[0].valeurResultatChar
            except:
                aspect = ''
            try:
                odeur = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=22)[0].valeurResultatChar
            except:
                odeur = ''
            try:
                couleursaybolt = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=8)[0].valeurResultatChar
            except:
                couleursaybolt = ''
            try:
                soufre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[0].valeurResultat
            except:
                soufre = ''
            try:
                distillation = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[0].valeurResultat
            except:
                distillation = ''
            try:
                pointfinal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=29)[0].valeurResultat
            except:
                pointfinal = ''
            try:
                residu = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=31)[0].valeurResultat
            except:
                residu = ''
            try:
                corrosion_str = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=7)[0].valeurResultat
                corrosion = int(corrosion_str)
            except:
                corrosion = ''
            try:
                pourcent10 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=11)[0].valeurResultat
            except:
                pourcent10 = ''
            try:
                pourcent20 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=12)[0].valeurResultat
            except:
                pourcent20 = ''
            try:
                pourcent50 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=13)[0].valeurResultat
            except:
                pourcent50 = ''
            try:
                pourcent70 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=14)[0].valeurResultat
            except:
                pourcent70 = ''
            try:
                pourcent90 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=15)[0].valeurResultat
            except:
                pourcent90 = ''
            try:
                tensionvapeur = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=36)[0].valeurResultat
            except:
                tensionvapeur = ''
            try:
                difftemperature = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=9)[0].valeurResultat
            except:
                difftemperature = ''
            try:
                plomb = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=24)[0].valeurResultat
            except:
                plomb = ''
            try:
                indiceoctane = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=18)[0].valeurResultat
            except:
                indiceoctane = ''
            try:
                massevolumique15 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[0].valeurResultat
            except:
                massevolumique15 = ''

            data = {
                'laboratoire': laboratoire,
                'cargaison': cargaison,
                'echantillon': echantillon,
                'annee': annee,
                'mois': mois,
                'province': province,
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
                'signGauche': signGauche,
                'signDroite': signDroite,
                'impressionData': impressionData,
                'laboratoireData': laboratoireData,
            }

            # Rendered PDF report
            pdf = render_to_pdf(template, data)
            pdf_base64 = base64.b64encode(pdf.getvalue()).decode('utf-8')
            bulk_pdf_data.append(pdf_base64)

        if produit == 'JET A1':
            template = 'report/Report1/jeta1report.html'

            # Resultat Gasoil Fetching data into Database
            try:
                aspect = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=2)[
                    0].valeurResultatChar
            except:
                aspect = ''
            try:
                couleursaybolt = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=8)[
                    0].valeurResultatChar
            except:
                couleursaybolt = ''
            try:
                aciditetotal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=1)[
                    0].valeurResultat
            except:
                aciditetotal = ''
            try:
                soufre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=34)[
                    0].valeurResultat
            except:
                soufre = ''
            try:
                soufremercaptan = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=33)[
                    0].valeurResultat
            except:
                soufremercaptan = ''
            try:
                docteurtest = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=16)[
                    0].valeurResultat
            except:
                docteurtest = ''
            try:
                distillation = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                    0].valeurResultat
            except:
                distillation = ''
            try:
                pointinitial = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=30)[
                    0].valeurResultat
            except:
                pointinitial = ''
            try:
                pointfinal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=29)[
                    0].valeurResultat
            except:
                pointfinal = ''

            try:
                pointfumee = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=28)[
                    0].valeurResultat
            except:
                pointfumee = ''

            try:
                pointeclair = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=25)[
                    0].valeurResultat
            except:
                pointeclair = ''

            try:
                freezingpoint = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=17)[
                    0].valeurResultat
            except:
                freezingpoint = ''

            try:
                residu = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=31)[
                    0].valeurResultat
            except:
                residu = ''

            try:
                perte = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=23)[
                    0].valeurResultat
            except:
                perte = ''

            try:
                massevolumique15 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[
                    0].valeurResultat
            except:
                massevolumique15 = ''

            try:
                viscosite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=37)[
                    0].valeurResultat
            except:
                viscosite = ''

            try:
                pointinflammabilite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=27)[
                    0].valeurResultat
            except:
                pointinflammabilite = ''

            try:
                teneureau = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=35)[
                    0].valeurResultat
            except:
                teneureau = ''

            try:
                corrosion_str = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=5)[
                    0].valeurResultat
                corrosion = int(corrosion_str)
            except:
                corrosion = ''

            try:
                conductivite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=4)[
                    0].valeurResultat
            except:
                conductivite = ''

            try:
                vol10 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=11)[
                    0].valeurResultat
            except:
                vol10 = ''

            try:
                vol20 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=12)[
                    0].valeurResultat
            except:
                vol20 = ''
            try:
                vol30 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                    0].valeurResultat
            except:
                vol30 = ''
            try:
                vol40 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                    0].valeurResultat
            except:
                vol40 = ''
            try:
                vol50 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=13)[
                    0].valeurResultat
            except:
                vol50 = ''
            try:
                vol60 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                    0].valeurResultat
            except:
                vol60 = ''
            try:
                vol70 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=14)[
                    0].valeurResultat
            except:
                vol70 = ''
            try:
                vol80 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=100)[
                    0].valeurResultat
            except:
                vol80 = ''
            try:
                vol90 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=15)[
                    0].valeurResultat
            except:
                vol90 = ''

            data = {
                'laboratoire': laboratoire,
                'cargaison': cargaison,
                'echantillon': echantillon,
                'annee': annee,
                'mois': mois,
                'province': province,
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
                'signGauche': signGauche,
                'signDroite': signDroite,
                'impressionData': impressionData,
                'laboratoireData': laboratoireData,
            }
            # Rendered PDF report
            pdf = render_to_pdf(template, data)
            pdf_base64 = base64.b64encode(pdf.getvalue()).decode('utf-8')
            bulk_pdf_data.append(pdf_base64)

        if produit == 'PETROLE LAMPANT':
            template = 'report/Report1/petrolereport.html'

            # Resultat Gasoil Fetching data into Database
            try:
                aspect = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=1)[
                    0].valeurResultatChar
            except:
                aspect = ''
            try:
                couleursaybolt = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=3)[
                    0].valeurResultatChar
            except:
                couleursaybolt = ''
            try:
                aciditetotal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=5)[
                    0].valeurResultat
            except:
                aciditetotal = ''
            try:
                soufre = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=6)[
                    0].valeurResultat
            except:
                soufre = ''
            try:
                soufremercaptan = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=7)[
                    0].valeurResultat
            except:
                soufremercaptan = ''
            try:
                docteurtest = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=8)[
                    0].valeurResultat
            except:
                docteurtest = ''
            try:
                distillation = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=11)[
                    0].valeurResultat
            except:
                distillation = ''
            try:
                pointinitial = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=16)[
                    0].valeurResultat
            except:
                pointinitial = ''
            try:
                pointfinal = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=17)[
                    0].valeurResultat
            except:
                pointfinal = ''

            try:
                pointfumee = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=19)[
                    0].valeurResultat
            except:
                pointfumee = ''

            try:
                pointeclair = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=18)[
                    0].valeurResultat
            except:
                pointeclair = ''

            try:
                freezingpoint = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=20)[
                    0].valeurResultat
            except:
                freezingpoint = ''

            try:
                residu = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=21)[
                    0].valeurResultat
            except:
                residu = ''

            try:
                perte = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=22)[
                    0].valeurResultat
            except:
                perte = ''

            try:
                massevolumique15 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=52)[
                    0].valeurResultat
            except:
                massevolumique15 = ''

            try:
                viscosite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=23)[
                    0].valeurResultat
            except:
                viscosite = ''

            try:
                pointinflammabilite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=24)[
                    0].valeurResultat
            except:
                pointinflammabilite = ''

            try:
                teneureau = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=26)[
                    0].valeurResultat
            except:
                teneureau = ''

            try:
                corrosion_str = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=28)[
                    0].valeurResultat
                corrosion = int(corrosion_str)

            except:
                corrosion = ''

            try:
                conductivite = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=29)[
                    0].valeurResultat
            except:
                conductivite = ''

            try:
                vol10 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=39)[
                    0].valeurResultat
            except:
                vol10 = ''

            try:
                vol20 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=40)[
                    0].valeurResultat
            except:
                vol20 = ''
            try:
                vol30 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=41)[
                    0].valeurResultat
            except:
                vol30 = ''
            try:
                vol40 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=42)[
                    0].valeurResultat
            except:
                vol40 = ''
            try:
                vol50 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=43)[
                    0].valeurResultat
            except:
                vol50 = ''
            try:
                vol60 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=44)[
                    0].valeurResultat
            except:
                vol60 = ''
            try:
                vol70 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=45)[
                    0].valeurResultat
            except:
                vol70 = ''
            try:
                vol80 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=46)[
                    0].valeurResultat
            except:
                vol80 = ''
            try:
                vol90 = ResultatAnalyse.objects.filter(idcargaison=pk, idParametre=47)[
                    0].valeurResultat
            except:
                vol90 = ''

            data = {
                'laboratoire': laboratoire,
                'cargaison': cargaison,
                'echantillon': echantillon,
                'annee': annee,
                'mois': mois,
                'province': province,
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
                'signGauche': signGauche,
                'signDroite': signDroite,
                'impressionData': impressionData,
                'laboratoireData': laboratoireData,
            }

            # Rendered PDF report
            pdf = render_to_pdf(template, data)
            pdf_base64 = base64.b64encode(pdf.getvalue()).decode('utf-8')
            bulk_pdf_data.append(pdf_base64)

    # Merging all PDF content into one file
    merged_pdf = PdfFileMerger()
    for pdf_base64 in bulk_pdf_data:
        pdf_content = base64.b64decode(pdf_base64)
        merged_pdf.append(ContentFile(pdf_content))

    # Generate a unique file name using datetime
    current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"merged_pdf_{current_datetime}.pdf"

    # Save the merged PDF content to a file
    with default_storage.open(file_name, 'wb') as merged_pdf_file:
        merged_pdf.write(merged_pdf_file)

    file_url = default_storage.url(file_name)

    # print('INSIDE CELERY')
    # print(file_url)
    # print(file_name)

    return {
        'file_url': file_url,
        'file_name': file_name,
    }














