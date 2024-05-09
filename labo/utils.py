import os
from io import BytesIO

from django.conf import settings
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa


def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute URLs to access resources from DigitalOcean Spaces
    """
    if rel == 'stylesheet' and uri.startswith(settings.STATIC_URL):
        # Handle static files
        return uri
    elif uri.startswith(settings.MEDIA_URL):
        # Handle media files
        file_url = default_storage.url(uri)
        # Ensure that the file exists
        if not default_storage.exists(uri):
            raise Exception(f'File does not exist: {uri}')
        return file_url
    else:
        # Handle other URIs
        return uri


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback, encoding='UTF-8')

    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None
