import base64
import datetime

from PyPDF3 import PdfFileMerger
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models.functions import ExtractYear, ExtractMonth
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport

from enreg.models import ResultatAnalyse, ImpressionResultat, Produit, Cargaison
from hydrocarbures.celery import app
from labo.tables import *
from labo.utils import render_to_pdf
#
# @app.task
# def queryProcessing(queryset_data,):
#
#     pass
#



#
# # Convert the page object to a list of dictionaries
# data = list(page)
#
# # Check if it's an AJAX request and if the export flag is set
# export = request.GET.get('export', None)
# if export == 'excel':
#     # Retrieve all data (no lazy pagination) and store it in a list
#     data = list(qs)
#
#     # Create a new Excel workbook
#     workbook = Workbook()
#     sheet = workbook.active
#
#     # Write headers to the Excel file
#     header_row = ['DATE ENTREE', 'FRONTIERE', 'DECL.#T1D', 'FOURNISSEUR', 'ENTREPOT', 'IMMATRICULATION',
#                   'DATE REQ.', 'DATE ECH.', 'DATE REC.LABO', 'DATE ANALYSE', 'DATE INSPEC.', 'DATE DECH.',
#                   'PRODUIT', 'DENS.ATA',
#                   'TEMP.', 'VOL. DECL.', 'VOL. JAUGE', 'MTA', 'GSV JAUGE', 'GSV COMPTEUR', 'FRAIS A PAYER']
#     sheet.append(header_row)
#
#     # Write data rows to the Excel file
#     for row in data:
#         sheet.append([
#             row['dateheurecargaison__date'],
#             row['frontiere__nomville'],
#             row['declaration'],
#             row['importateur__nomimportateur'],
#             row['entrepot__nomentrepot'],
#             row['immatriculation'],
#             row['requisitiondackdate__date'],
#             row['entrepot_echantillon__dateechantillonage__date'],
#             row['entrepot_echantillon__laboreception__datereceptionlabo__date'],
#             row['impressionresultat__printDate'],
#             row['inspection__dateinspection__date'],
#             row['dateDechargement__date'],
#             row['produit__nomproduit'],
#             row['inspection__dens'],
#             row['inspection__temp'],
#             row['volJauge'],
#             row['mta'],
#             row['gsvJauge'],
#             row['gsvMeter'],
#             row['fraisOcc_rounded'],
#         ])
#
#     # Create an in-memory stream to hold the Excel file data
#     excel_stream = BytesIO()
#     workbook.save(excel_stream)
#     excel_stream.seek(0)
#
#     # Prepare the response to return the Excel file
#     response = HttpResponse(excel_stream,
#                             content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#     response['Content-Disposition'] = 'attachment; filename="rapport_brut_journalier.xlsx"'
#     return response