import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import sentry_sdk
import logging
import json
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from django.core.management.utils import get_random_secret_key
# import mysql.connector.django as mysql
from django.contrib.messages import constants as messages
from datetime import timedelta

import api.authentication

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Env File loading here (no-op in Kubernetes if .env doesn't exist)
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)


def env_list(name: str, default: str = ""):
    """
    Read a comma-separated env var into a clean Python list.
    Example: "a,b, c" -> ["a", "b", "c"]
    """
    return [
        item.strip()
        for item in os.environ.get(name, default).split(",")
        if item.strip()
    ]


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

DEBUG = bool(int(os.environ.get("DEBUG", "0")))
DEVELOPMENT_MODE = bool(int(os.environ.get("DEVELOPMENT_MODE", "0")))

ALLOWED_HOSTS = []
ALLOWED_HOSTS.extend(
    filter(
        None,
        os.environ.get("ALLOWED_HOSTS", "").split(","),
    )
)

INTERNAL_IPS = [
    "127.0.0.1",
]

AUTH_USER_MODEL = "accounts.MyUser"

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    "debug_toolbar",
    "django_countries",
    "crispy_forms",
    "crispy_bootstrap4",
    "qr_code",
    "django_tables2",
    "bootstrap4",
    "django_bootstrap5",
    "bootstrap_datepicker_plus",
    "django_htmx",
    # Celery
    "django_celery_beat",
    "django_celery_results",
    "celery_progress",
    # "dotenv",
    "formtools",
    # "tailwind",
    # "django_browser_reload",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "rest_framework_simplejwt.token_blacklist",
    "rest_framework_api_key",
    "fontawesomefree",
    "push_notifications",  # Push Notification
    "django.contrib.humanize",
    # Ajax
    "ajax_datatable",
    # My Apps
    "enreg",
    "shydro",
    "entrepot",
    "labo",
    "accounts",
    "ads",
    "facturations",
    # "theme",
    "api",
    # "verification",
]


STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

PUSH_NOTIFICATIONS_SETTINGS = {
    "FCM_API_KEY": "[your api key]",
    "GCM_API_KEY": "[your api key]",
    "APNS_CERTIFICATE": "/path/to/your/certificate.pem",
    "APNS_TOPIC": "com.example.push_test",
    "WNS_PACKAGE_SECURITY_ID": "[your package security id, e.g: 'ms-app://e-3-4-6234...']",
    "WNS_SECRET_KEY": "[your app secret key, e.g.: 'KDiejnLKDUWodsjmewuSZkk']",
    "WP_PRIVATE_KEY": "/path/to/your/private.pem",
    "WP_CLAIMS": {"sub": "mailto: development@example.com"},
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        # "rest_framework_api_key.permissions.HasAPIKey",
        # "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly",
        # "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
}

# API KEY Secret
API_KEY_SECRET = os.environ.get("API_SECRET")

IMPORT_EXPORT_USE_TRANSACTIONS = True

MESSAGE_TAGS = {
    messages.ERROR: "danger",
}

BOOTSTRAP3 = {
    "include_jquery": True,
}

DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap4-responsive.html"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Enable gzip compression for faster JSON/HTML transfer
    "django.middleware.gzip.GZipMiddleware",
    # "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django_session_timeout.middleware.SessionTimeoutMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    # "django_browser_reload.middleware.BrowserReloadMiddleware",
]

SESSION_EXPIRE_SECONDS = 1200
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_EXPIRE_AFTER_LAST_ACTIVITY_GRACE_PERIOD = 20

ROOT_URLCONF = "hydrocarbures.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Expose Sentry vars to templates for browser SDK
                "hydrocarbures.context_processors.sentry",
            ],
        },
    },
]

WSGI_APPLICATION = "hydrocarbures.wsgi.application"

# Database
if DEVELOPMENT_MODE is True:
    DATABASES = {
        "default": {
            "NAME": str(os.environ.get("DATABASE_NAME")),
            "ENGINE": "django.db.backends.mysql",
            "USER": str(os.environ.get("DATABASE_USER")),
            "HOST": str(os.environ.get("DATABASE_HOST")),
            "PORT": os.environ.get("DATABASE_PORT"),
            "PASSWORD": str(os.environ.get("DATABASE_PASSWORD")),
            "OPTIONS": {
                "autocommit": True,
            },
        }
    }
else:
    if os.environ.get("DATABASE_HOST") is None:
        raise Exception("DATABASE_HOST environment variable not defined")
    DATABASES = {
        "default": {
            "NAME": str(os.environ.get("DATABASE_NAME")),
            "ENGINE": "django.db.backends.mysql",
            "USER": str(os.environ.get("DATABASE_USER")),
            "HOST": str(os.environ.get("DATABASE_HOST")),
            "PORT": os.environ.get("DATABASE_PORT"),
            "PASSWORD": str(os.environ.get("DATABASE_PASSWORD")),
            "OPTIONS": {
                "autocommit": True,
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                "ssl": {"ca": "/app/hydrocarbures/ca.crt"},
            },
            # Keep DB connections open briefly to avoid handshake overhead
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
        }
    }

CRISPY_TEMPLATE_PACK = "bootstrap4"
DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap-responsive.html"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "fr-FR"

TIME_ZONE = "Africa/Lubumbashi"
USE_L10N = True

STATIC_URL = "/static/"

STATIC_ROOT = Path(BASE_DIR) / "staticfiles-cdn"

STATICFILES_DIRS = [
    Path(BASE_DIR).joinpath("staticfiles"),
]

from .cdn.conf import *  # noqa

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Sentry
# Read config from environment to support all environments (dev/staging/prod)
SENTRY_DSN = os.environ.get("SENTRY_DSN", "https://0b479a1d226644afad74678a3d3779a9@o554823.ingest.sentry.io/4505436514746368")
SENTRY_ENV = os.environ.get("SENTRY_ENV", "development")
SENTRY_RELEASE = os.environ.get("SENTRY_RELEASE", "")
try:
    SENTRY_TRACES = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "1.0"))
except Exception:
    SENTRY_TRACES = 1.0
try:
    SENTRY_PROFILES = float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "1.0"))
except Exception:
    SENTRY_PROFILES = 1.0

sentry_logging = LoggingIntegration(
    level=logging.INFO,        # capture breadcrumbs from INFO and up
    event_level=logging.ERROR  # send events for ERROR and up
)

sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=SENTRY_ENV,
    release=SENTRY_RELEASE,
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
        sentry_logging,
    ],
    traces_sample_rate=SENTRY_TRACES,
    profiles_sample_rate=SENTRY_PROFILES,
    send_default_pii=True,
)

# Minimal logging to ensure errors still go to console and Sentry picks up breadcrumbs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

CORS_ALLOW_ALL_ORIGINS = True

# CSRF_TRUSTED_ORIGINS from env, with fallback to ALLOWED_HOSTS
_csrf_from_env = env_list("CSRF_TRUSTED_ORIGINS")

if _csrf_from_env:
    CSRF_TRUSTED_ORIGINS = _csrf_from_env
else:
    # Fallback: assume HTTPS for all hosts that don’t already have a scheme
    CSRF_TRUSTED_ORIGINS = [
        host if host.startswith(("http://", "https://")) else f"https://{host}"
        for host in ALLOWED_HOSTS
    ]

# CELERY SETTINGS
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER", "redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_RESULT_BACKEND = "django-db"
# CELERY_TIMEZONE = 'Africa/Lubumbashi'


# SECRET DELETION CODE
DELETE_CONFIRMATION_CODE = os.environ.get("DELETE_CONFIRMATION_CODE")