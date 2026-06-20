"""
Test settings for CI/CD.

This configuration is optimized for automated testing with:
- Fast password hashing
- In-memory caching
- Minimal logging
- Local file storage

Usage:
    export DJANGO_ENV=test
    python manage.py test
"""
from .base import *  # noqa: F401, F403

# Force DEBUG=False for realistic testing
DEBUG = False

# Use faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use local memory cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Celery - run tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use local file storage for tests
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'test_media'  # noqa: F405

# Minimal logging for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'CRITICAL',
    },
}

# Disable Sentry in tests
SENTRY_DSN = ''

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Allowed hosts for test server
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']  # noqa: F405

print(f"\n🧪 Running in TEST mode (DEBUG={DEBUG})\n")

