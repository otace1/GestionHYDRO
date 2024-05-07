import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import sentry_sdk
import json
from sentry_sdk.integrations.django import DjangoIntegration
from django.core.management.utils import get_random_secret_key
# import mysql.connector.django as mysql
from django.contrib.messages import constants as messages
from datetime import timedelta

import api.authentication

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#Env File loading here
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

DEBUG = bool(int(os.environ.get("DEBUG")))

ALLOWED_HOSTS = []
ALLOWED_HOSTS.extend(
    filter(
        None,
        os.environ.get("ALLOWED_HOSTS",'').split(','),
    )
)



DEVELOPMENT_MODE = bool(int(os.environ.get("DEVELOPMENT_MODE")))


INTERNAL_IPS = [
    '127.0.0.1',
]

AUTH_USER_MODEL = 'accounts.MyUser'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',

    'debug_toolbar',
    'django_countries',
    'crispy_forms',
    'crispy_bootstrap4',
    'qr_code',
    'django_tables2',
    'bootstrap4',
    'bootstrap_datepicker_plus',
    'django_htmx',
    #Celery
    'django_celery_beat',
    'django_celery_results',
    'celery_progress',
    # 'dotenv',

    'formtools',
    # 'tailwind',
    'django_browser_reload',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'rest_framework_simplejwt.token_blacklist',
    "rest_framework_api_key",

    'push_notifications', #Push Notification

    #Ajax#
    'ajax_datatable',

    # My Apps
    'enreg',
    'shydro',
    'entrepot',
    'labo',
    'accounts',
    'ads',
    'facturations',
    # 'theme',
    'api',
    # 'verification',
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # other finders..
    # 'compressor.finders.CompressorFinder',
)

PUSH_NOTIFICATIONS_SETTINGS = {
        "FCM_API_KEY": "[your api key]",
        "GCM_API_KEY": "[your api key]",
        "APNS_CERTIFICATE": "/path/to/your/certificate.pem",
        "APNS_TOPIC": "com.example.push_test",
        "WNS_PACKAGE_SECURITY_ID": "[your package security id, e.g: 'ms-app://e-3-4-6234...']",
        "WNS_SECRET_KEY": "[your app secret key, e.g.: 'KDiejnLKDUWodsjmewuSZkk']",
        "WP_PRIVATE_KEY": "/path/to/your/private.pem",
        "WP_CLAIMS": {'sub': "mailto: development@example.com"}
}

#
# #Email Host
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = os.getenv("EMAIL_HOST")
# EMAIL_USE_TLS = True
# EMAIL_PORT = 587
# EMAIL_HOST_USER = os.getenv("API_USER")
# EMAIL_HOST_PASSWORD = os.getenv("API_KEY")


REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        # "rest_framework_api_key.permissions.HasAPIKey",
        # 'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
        # 'rest_framework.permissions.IsAuthenticated',
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'rest_framework.authentication.BasicAuthentication',
        # 'api.authentication.SafeJWTAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 'rest_framework.authentication.BasicAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ]
}

# API KEY Secret
API_KEY_SECRET = os.environ.get("API_SECRET")


IMPORT_EXPORT_USE_TRANSACTIONS = True

MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}


BOOTSTRAP3 = {
    'include_jquery': True,
}

DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap4-responsive.html"


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_session_timeout.middleware.SessionTimeoutMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'django_browser_reload.middleware.BrowserReloadMiddleware',
    ]


SESSION_EXPIRE_SECONDS = 1200
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_EXPIRE_AFTER_LAST_ACTIVITY_GRACE_PERIOD = 20

# SECURE_SSL_REDIRECT = True

ROOT_URLCONF = 'hydrocarbures.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hydrocarbures.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
if DEVELOPMENT_MODE is True:
    DATABASES = {
        'default': {
            'NAME':str(os.environ.get("DATABASE_NAME")),
            'ENGINE': 'django.db.backends.mysql',
            'USER': str(os.environ.get("DATABASE_USER")),
            'HOST': str(os.environ.get("DATABASE_HOST")),
            'PORT': os.environ.get("DATABASE_PORT"),
            'PASSWORD': str(os.environ.get("DATABASE_PASSWORD")),
            'OPTIONS': {
                'autocommit': True,
            },
        }
    }
else:
    if os.environ.get("DATABASE_HOST") is None:
        raise Exception("DATABASE_HOST environment variable not defined")
    DATABASES = {
        'default': {
            'NAME':str(os.environ.get("DATABASE_NAME")),
            'ENGINE': 'django.db.backends.mysql',
            'USER': str(os.environ.get("DATABASE_USER")),
            'HOST': str(os.environ.get("DATABASE_HOST")),
            'PORT': os.environ.get("DATABASE_PORT"),
            'PASSWORD': str(os.environ.get("DATABASE_PASSWORD")),
            'OPTIONS': {
                'autocommit': True,
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'ssl': {'ca': '/app/hydrocarbures/ca.crt'},
            },
        }
    }


CRISPY_TEMPLATE_PACK = 'bootstrap4'
DJANGO_TABLES2_TEMPLATE = 'django_tables2/bootstrap-responsive.html'
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
# TAILWIND_APP_NAME = 'theme'

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'fr-FR'

TIME_ZONE = 'Africa/Lubumbashi'
USE_L10N = True
#
# USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = "/static/"
MEDIA_URL = "/media/"

STATIC_ROOT = "/vol/web/static"
MEDIA_ROOT = "/vol/web/media"

STATICFILES_DIRS = [
    Path(BASE_DIR).joinpath("assets"),
    # Add other directories if needed
]


# DB Primary key
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# # Sentry
#
sentry_sdk.init(
    dsn="https://0b479a1d226644afad74678a3d3779a9@o554823.ingest.sentry.io/4505436514746368",
    integrations=[
        DjangoIntegration(),
    ],

    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    send_default_pii=True

)

CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = 'suivicargo.com'


# CELERY SETTINGS
#
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER","redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'
# CELERY_TIMEZONE = 'Africa/Lubumbashi'


# if DEVELOPMENT_MODE is not True:
#     #Static and Media Files Storage
#     AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
#     AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
#     AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
#     AWS_DEFAULT_ACL = os.environ.get("AWS_DEFAULT_ACL")
#     AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL") # Make sure nyc3 is correct
#     AWS_S3_OBJECT_PARAMETERS = {
#         'CacheControl': 'max-age=86400'
#     }
#
#     AWS_STATIC_LOCATION = 'static'
#     STATIC_URL = '%s/%s' % (AWS_S3_ENDPOINT_URL, AWS_STATIC_LOCATION)
#     STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
#


