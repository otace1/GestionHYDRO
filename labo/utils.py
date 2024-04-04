import os
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa


def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    # Define the base URLs and roots
    sUrl = settings.STATIC_URL  # Typically /static/
    sRoot = settings.STATIC_ROOT  # Typically /home/userX/project_static/
    mUrl = settings.MEDIA_URL  # Typically /media/
    mRoot = settings.MEDIA_ROOT  # Typically /home/userX/project_media/

    # Convert URIs to absolute system paths
    if uri.startswith(mUrl):
        # If URI starts with MEDIA_URL, replace it with MEDIA_ROOT
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        # If URI starts with STATIC_URL, replace it with STATIC_ROOT
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        # If URI is absolute, return it as is
        return uri

    # Ensure that the file exists
    if not os.path.isfile(path):
        raise Exception(f'File does not exist: {path}')

    return path


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback, encoding='UTF-8')

    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None
