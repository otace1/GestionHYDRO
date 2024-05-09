import os
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.files.storage import default_storage


def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute paths using Django's default storage system
    """
    # Define the base URLs
    sUrl = settings.STATIC_URL  # Typically /static/
    mUrl = settings.MEDIA_URL   # Typically /media/

    # Convert URIs to absolute paths
    if uri.startswith(mUrl):
        # If URI starts with MEDIA_URL, replace it with relative path
        path = uri.replace(mUrl, "")
    elif uri.startswith(sUrl):
        # If URI starts with STATIC_URL, replace it with relative path
        path = uri.replace(sUrl, "")
    else:
        # If URI is absolute, return it as is
        return uri

    # Ensure that the file exists
    if not default_storage.exists(path):
        raise Exception(f'File does not exist: {path}')

    # Return the absolute path
    return default_storage.path(path)


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback, encoding='UTF-8')

    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None
