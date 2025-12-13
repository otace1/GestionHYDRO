from django.conf import settings


def flags(request):
    """Expose selected feature flags and common values to all templates."""
    return {
        "ENABLE_ANALYTICS": getattr(settings, "ENABLE_ANALYTICS", False),
    }
