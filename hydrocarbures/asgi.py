"""
ASGI config for hydrocarbures project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.asgi import get_asgi_application

# Load .env file
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# Dynamically select settings based on DJANGO_ENV
from hydrocarbures.settings import get_settings_module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', get_settings_module())

application = get_asgi_application()
