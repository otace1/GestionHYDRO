"""
Base settings shared across all environments.

DO NOT use this file directly. Use development.py, production.py, or test.py.
This file contains settings that are common to all environments.
"""
import os
import sys
from pathlib import Path
import logging

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from django.contrib.messages import constants as messages

# Import validated settings
from hydrocarbures.config import get_settings, SettingsValidationError

# Load and validate environment configuration
try:
    env_settings = get_settings()
except SettingsValidationError as e:
    print(f"\n{'='*60}")
    print("CONFIGURATION ERROR - Application cannot start")
    print('='*60)
    print(str(e))
    print('='*60 + "\n")
    sys.exit(1)

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Core settings from validated config
SECRET_KEY = env_settings.DJANGO_SECRET_KEY
DEBUG = env_settings.DEBUG
ALLOWED_HOSTS = env_settings.ALLOWED_HOSTS

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
    "formtools",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "rest_framework_simplejwt.token_blacklist",
    "rest_framework_api_key",
    "fontawesomefree",
    "push_notifications",
    "django.contrib.humanize",
    "ajax_datatable",
    "jsignature",
    # My Apps
    "enreg",
    "shydro",
    "entrepot",
    "labo",
    "accounts",
    "ads",
    "facturations",
    "api",
    "app_settings",
]

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

PUSH_NOTIFICATIONS_SETTINGS = {
    "FCM_API_KEY": os.environ.get("FCM_API_KEY", ""),
    "GCM_API_KEY": os.environ.get("GCM_API_KEY", ""),
    "APNS_CERTIFICATE": os.environ.get("APNS_CERTIFICATE", ""),
    "APNS_TOPIC": os.environ.get("APNS_TOPIC", "com.example.push_test"),
    "WNS_PACKAGE_SECURITY_ID": os.environ.get("WNS_PACKAGE_SECURITY_ID", ""),
    "WNS_SECRET_KEY": os.environ.get("WNS_SECRET_KEY", ""),
    "WP_PRIVATE_KEY": os.environ.get("WP_PRIVATE_KEY", ""),
    "WP_CLAIMS": {"sub": os.environ.get("WP_CLAIMS_SUB", "mailto:dev@example.com")},
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
}

# API KEY Secret
API_KEY_SECRET = env_settings.API_SECRET

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
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django_session_timeout.middleware.SessionTimeoutMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.middleware.RequestStoreMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

SESSION_EXPIRE_SECONDS = 1200
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_EXPIRE_AFTER_LAST_ACTIVITY_GRACE_PERIOD = 20

ROOT_URLCONF = "hydrocarbures.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.csrf",
                "hydrocarbures.context_processors.sentry",
            ],
        },
    },
]

WSGI_APPLICATION = "hydrocarbures.wsgi.application"

# Database configuration from validated settings
DATABASES = {
    "default": env_settings.get_database_config()
}

CRISPY_TEMPLATE_PACK = "bootstrap4"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-FR"
TIME_ZONE = "Africa/Lubumbashi"
USE_L10N = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles-cdn"
STATICFILES_DIRS = [BASE_DIR / "staticfiles"]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Sentry configuration
SENTRY_DSN = env_settings.SENTRY_DSN
SENTRY_ENV = env_settings.SENTRY_ENV
SENTRY_RELEASE = env_settings.SENTRY_RELEASE
SENTRY_TRACES = env_settings.SENTRY_TRACES_SAMPLE_RATE
SENTRY_PROFILES = env_settings.SENTRY_PROFILES_SAMPLE_RATE

if SENTRY_DSN:
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
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

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = env_settings.CSRF_TRUSTED_ORIGINS or [
    host if host.startswith(("http://", "https://")) else f"https://{host}"
    for host in ALLOWED_HOSTS
]

# Celery settings
CELERY_BROKER_URL = env_settings.CELERY_BROKER
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_RESULT_BACKEND = "django-db"

# App-specific settings
DELETE_CONFIRMATION_CODE = env_settings.DELETE_CONFIRMATION_CODE

# Audit Log Settings
AUDIT_LOG_ENABLED = True
AUDIT_LOG_EXCLUDE_MODELS = [
    'accounts.auditlog',
    'accounts.useractivitylog',
    'sessions.session',
    'admin.logentry',
    'contenttypes.contenttype',
    'auth.permission',
    'django_celery_results.taskresult',
    'django_celery_beat.periodictask',
    'django_celery_beat.periodictasks',
    'django_celery_beat.crontabschedule',
    'django_celery_beat.intervalschedule',
    'django_celery_beat.solarschedule',
    'django_celery_beat.clockedschedule',
]
AUDIT_LOG_RETENTION_DAYS = 90

