"""
Development settings.

This configuration is optimized for local development with:
- DEBUG=True
- Django Debug Toolbar enabled
- Relaxed security settings
- Local file storage (optional)

Usage:
    export DJANGO_ENV=development
    python manage.py runserver
"""
from .base import *  # noqa: F401, F403

# Ensure we're in development mode
DEBUG = True

# Add debug toolbar
INSTALLED_APPS += [  # noqa: F405
    "debug_toolbar",
]

MIDDLEWARE.insert(  # noqa: F405
    MIDDLEWARE.index("django.middleware.clickjacking.XFrameOptionsMiddleware") + 1,  # noqa: F405
    "debug_toolbar.middleware.DebugToolbarMiddleware",
)

# Allow all hosts in development
if not ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = ['*']  # noqa: F405

# Development logging - more verbose
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django.db.backends': {
            'level': 'WARNING',  # Set to DEBUG to see SQL queries
            'handlers': ['console'],
        },
    },
}

# CORS - allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Disable CSRF in development for API testing (optional)
# CSRF_TRUSTED_ORIGINS = ['http://localhost:*', 'http://127.0.0.1:*']

# Email backend - console for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Optional: Use local file storage instead of S3 in development
# Uncomment these lines to use local storage:
# DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
# MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'

# AWS/S3 settings for development - from environment or use defaults
from hydrocarbures.config import get_settings
_env = get_settings()

if _env.AWS_ACCESS_KEY_ID and _env.AWS_SECRET_ACCESS_KEY:
    # Use S3 if credentials are provided
    AWS_ACCESS_KEY_ID = _env.AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = _env.AWS_SECRET_ACCESS_KEY
    AWS_STORAGE_BUCKET_NAME = _env.AWS_STORAGE_BUCKET_NAME
    AWS_S3_ENDPOINT_URL = _env.AWS_S3_ENDPOINT_URL
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    AWS_LOCATION = _env.AWS_LOCATION

    DEFAULT_FILE_STORAGE = "hydrocarbures.cdn.backend.MediaRootS3BotoStorage"
    STATICFILES_STORAGE = "hydrocarbures.cdn.backend.StaticRootS3BotoStorage"
else:
    # Fall back to local storage in development
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'  # noqa: F405

print(f"\n🔧 Running in DEVELOPMENT mode (DEBUG={DEBUG})\n")

