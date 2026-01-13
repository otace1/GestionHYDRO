"""
Production settings.

This configuration is hardened for production with:
- DEBUG=False (enforced)
- Security headers enabled
- S3 storage required
- SSL enforcement
- Proper logging

Usage:
    export DJANGO_ENV=production
    gunicorn hydrocarbures.wsgi:application
"""
from .base import *  # noqa: F401, F403
from hydrocarbures.config import get_settings

# Get validated settings
_env = get_settings()

# Force DEBUG=False in production (defense in depth)
DEBUG = False

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS settings - enable in production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# AWS/S3 settings - required in production
AWS_ACCESS_KEY_ID = _env.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = _env.AWS_SECRET_ACCESS_KEY
AWS_STORAGE_BUCKET_NAME = _env.AWS_STORAGE_BUCKET_NAME
AWS_S3_ENDPOINT_URL = _env.AWS_S3_ENDPOINT_URL
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
AWS_LOCATION = _env.AWS_LOCATION

DEFAULT_FILE_STORAGE = "hydrocarbures.cdn.backend.MediaRootS3BotoStorage"
STATICFILES_STORAGE = "hydrocarbures.cdn.backend.StaticRootS3BotoStorage"

# Production logging - structured for log aggregation
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
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
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# CORS - restrict in production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    f"https://{host}" for host in ALLOWED_HOSTS  # noqa: F405
    if not host.startswith('.')
]

# Sentry environment override
SENTRY_ENV = 'production'

print(f"\n🚀 Running in PRODUCTION mode (DEBUG={DEBUG})\n")

