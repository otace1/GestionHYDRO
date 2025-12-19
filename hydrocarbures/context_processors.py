import os


def sentry(request):
    """Expose Sentry variables to templates for browser SDK initialization."""
    return {
        'SENTRY_DSN_JS': os.environ.get('SENTRY_DSN_JS', ''),
        'SENTRY_ENV': os.environ.get('SENTRY_ENV', 'development'),
        'SENTRY_RELEASE': os.environ.get('SENTRY_RELEASE', ''),
        'SENTRY_TRACES_SAMPLE_RATE': os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '1.0'),
    }
