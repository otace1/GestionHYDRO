import base64
import datetime
from io import BytesIO

from PyPDF3 import PdfFileMerger
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models.functions import ExtractYear, ExtractMonth
from django.http import HttpResponse
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport
from xlsxwriter import Workbook

from ads.tables import RapportBrut
from enreg.models import ResultatAnalyse, ImpressionResultat, Produit, Cargaison
from hydrocarbures.celery import app
from labo.tables import *
from labo.utils import render_to_pdf


@app.task
def exportLargeDataSet(export_format, queryset_data, request=None):
    try:
        # Initialize the table with the queryset data
        table = RapportBrut(queryset_data)

        # If request is provided, configure pagination
        if request:
            RequestConfig(request, paginate={"per_page": 15}).configure(table)

        # Export the table
        exporter = TableExport(export_format, table, exclude_columns=("actions"))
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

