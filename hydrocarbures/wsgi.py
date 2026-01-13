"""
WSGI config for hydrocarbures project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.wsgi import get_wsgi_application

# Load .env file
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# Dynamically select settings based on DJANGO_ENV
from hydrocarbures.settings import get_settings_module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', get_settings_module())

application = get_wsgi_application()
