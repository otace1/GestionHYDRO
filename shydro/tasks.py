import os
from django_tables2.export.export import TableExport
import datetime

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport

from hydrocarbures.celery import app
from shydro.tables import RapportActivite


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



