"""
Django Split Settings Package.

This package provides environment-specific settings:
- development.py: Local development with DEBUG=True
- production.py: Production-ready with security hardening
- test.py: CI/CD testing configuration

The appropriate settings module is selected based on DJANGO_ENV environment variable.
Default is 'development' for safety.
"""
import os


def get_settings_module() -> str:
    """
    Determine which settings module to use based on DJANGO_ENV.

    Returns:
        Full module path for Django settings.
    """
    env = os.environ.get('DJANGO_ENV', 'development').lower()

    valid_environments = {
        'development': 'hydrocarbures.settings.development',
        'production': 'hydrocarbures.settings.production',
        'test': 'hydrocarbures.settings.test',
    }

    return valid_environments.get(env, 'hydrocarbures.settings.development')

