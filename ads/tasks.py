import os
import base64
import datetime

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport
from xlsxwriter import Workbook

from ads.tables import RapportBrut
from enreg.models import ResultatAnalyse, ImpressionResultat, Produit, Cargaison
from hydrocarbures import settings
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

        # Save the exported file to the default storage
        file_path = f"xlsx/{file_name}"
        file_content_file = ContentFile(file_content)
        file_url = default_storage.save(file_path, file_content_file)

        # Return the URL of the exported file
        return {
            'file_url': file_url,
            'file_name': file_name,
        }

    except Exception as e:
        return {'error': str(e)}


    #     # # Define the media directory
    #     # media_dir = os.path.join("/vol/web/media", 'xlsx')
    #     # os.makedirs(media_dir, exist_ok=True)  # Ensure the directory exists\
    #
    #     media_dir = os.path.join(settings.MEDIA_ROOT, 'xlsx')
    #     os.makedirs(media_dir, exist_ok=True)
    #
    #
    #     # Save the exported file to the mounted volume
    #     file_path = os.path.join(media_dir, file_name)  # Path to the mounted volume
    #     with default_storage.open(file_path, "wb") as file_content_file:
    #         file_content_file.write(file_content)
    #
    #     # Return the URL of the exported file
    #     file_url = os.path.join(settings.MEDIA_URL,'xlsx', file_name)  # Assuming MEDIA_URL is /media/
    #     return {
    #         'file_url': file_url,
    #         'file_name': file_name,
    #     }
    #
    # except Exception as e:
    #     return {'error': str(e)}

