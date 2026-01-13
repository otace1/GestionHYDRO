"""
Environment Configuration with Pydantic Validation.

This module provides fail-fast validation for all environment variables.
If a required variable is missing or invalid, the application will fail
to start with a clear error message.

Usage:
    from hydrocarbures.config import get_settings
    settings = get_settings()
    print(settings.DATABASE_HOST)
"""
import os
from functools import lru_cache
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from django.core.management.utils import get_random_secret_key


class SettingsValidationError(Exception):
    """Raised when environment configuration is invalid."""
    pass


class DatabaseSettings(BaseModel):
    """Database connection settings."""
    HOST: str = Field(..., min_length=1)
    PORT: int = Field(default=3306, ge=1, le=65535)
    NAME: str = Field(..., min_length=1)
    USER: str = Field(..., min_length=1)
    PASSWORD: str = Field(..., min_length=1)


class AWSSettings(BaseModel):
    """AWS/S3 storage settings."""
    ACCESS_KEY_ID: Optional[str] = None
    SECRET_ACCESS_KEY: Optional[str] = None
    STORAGE_BUCKET_NAME: str = "gestionhydro"
    S3_ENDPOINT_URL: str = "https://sfo3.digitaloceanspaces.com"
    LOCATION: str = "https://gestionhydro.sfo3.digitaloceanspaces.com"


class SentrySettings(BaseModel):
    """Sentry error tracking settings."""
    DSN: str = ""
    ENV: str = "development"
    RELEASE: str = ""
    TRACES_SAMPLE_RATE: float = Field(default=1.0, ge=0.0, le=1.0)
    PROFILES_SAMPLE_RATE: float = Field(default=1.0, ge=0.0, le=1.0)


class EnvironmentSettings(BaseSettings):
    """
    Main settings class with full validation.

    All settings are loaded from environment variables.
    The prefix is stripped from variable names (e.g., DATABASE_HOST -> HOST in DatabaseSettings).
    """
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=True,
    )

    # Core Django settings
    DJANGO_ENV: str = Field(default="development", pattern="^(development|production|test)$")
    DJANGO_SECRET_KEY: str = Field(default="")
    DEBUG: bool = Field(default=False)
    ALLOWED_HOSTS: str = Field(default="")  # Comma-separated string

    # Database settings (flat for env var compatibility)
    DATABASE_HOST: str = Field(default="")
    DATABASE_PORT: int = Field(default=3306)
    DATABASE_NAME: str = Field(default="")
    DATABASE_USER: str = Field(default="")
    DATABASE_PASSWORD: str = Field(default="")

    # AWS/S3 settings
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None)
    AWS_STORAGE_BUCKET_NAME: str = Field(default="gestionhydro")
    AWS_S3_ENDPOINT_URL: str = Field(default="https://sfo3.digitaloceanspaces.com")
    AWS_LOCATION: str = Field(default="https://gestionhydro.sfo3.digitaloceanspaces.com")

    # Celery settings
    CELERY_BROKER: str = Field(default="redis://redis:6379/0")

    # Sentry settings
    SENTRY_DSN: str = Field(default="")
    SENTRY_ENV: str = Field(default="development")
    SENTRY_RELEASE: str = Field(default="")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=1.0)
    SENTRY_PROFILES_SAMPLE_RATE: float = Field(default=1.0)

    # CSRF settings
    CSRF_TRUSTED_ORIGINS: str = Field(default="")  # Comma-separated string

    # App-specific settings
    DELETE_CONFIRMATION_CODE: str = Field(default="")
    API_SECRET: str = Field(default="")

    # Database connection pool
    DB_CONN_MAX_AGE: int = Field(default=60, ge=0)

    # Internal parsed lists (not from env)
    _allowed_hosts_list: List[str] = []
    _csrf_origins_list: List[str] = []

    def _parse_comma_list(self, value: str) -> List[str]:
        """Parse comma-separated string into list."""
        if not value:
            return []
        return [item.strip() for item in value.split(',') if item.strip()]

    @model_validator(mode='after')
    def validate_production_requirements(self):
        """Ensure production environment has all required settings."""
        errors = []

        # Parse comma-separated lists
        self._allowed_hosts_list = self._parse_comma_list(self.ALLOWED_HOSTS)
        self._csrf_origins_list = self._parse_comma_list(self.CSRF_TRUSTED_ORIGINS)

        if self.DJANGO_ENV == 'production':
            # Force DEBUG=False in production
            self.DEBUG = False

            # Validate required secrets
            if not self.DJANGO_SECRET_KEY or len(self.DJANGO_SECRET_KEY) < 50:
                errors.append("DJANGO_SECRET_KEY must be set and at least 50 characters in production")

            if not self._allowed_hosts_list:
                errors.append("ALLOWED_HOSTS must not be empty in production")

            # Validate AWS credentials
            if not self.AWS_ACCESS_KEY_ID or not self.AWS_SECRET_ACCESS_KEY:
                errors.append("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are required in production")

            # Validate database
            if not all([self.DATABASE_HOST, self.DATABASE_NAME, self.DATABASE_USER, self.DATABASE_PASSWORD]):
                errors.append("Complete database configuration required in production")

        elif self.DJANGO_ENV == 'development':
            # Auto-generate secret key in development if not provided
            if not self.DJANGO_SECRET_KEY:
                self.DJANGO_SECRET_KEY = get_random_secret_key()

            # Default DEBUG to True in development
            if 'DEBUG' not in os.environ:
                self.DEBUG = True

            # Default allowed hosts for local development
            if not self._allowed_hosts_list:
                self._allowed_hosts_list = ['localhost', '127.0.0.1', '[::1]']

        elif self.DJANGO_ENV == 'test':
            # Auto-generate secret key for tests
            if not self.DJANGO_SECRET_KEY:
                self.DJANGO_SECRET_KEY = 'test-secret-key-not-for-production-use-1234567890'

            self.DEBUG = False
            if not self._allowed_hosts_list:
                self._allowed_hosts_list = ['localhost', '127.0.0.1', 'testserver']

        if errors:
            raise SettingsValidationError(
                f"Configuration errors for {self.DJANGO_ENV} environment:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

        return self

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Get parsed ALLOWED_HOSTS as list."""
        return self._allowed_hosts_list

    @property
    def csrf_origins_list(self) -> List[str]:
        """Get parsed CSRF_TRUSTED_ORIGINS as list."""
        return self._csrf_origins_list

    def get_database_config(self) -> dict:
        """Get Django-compatible database configuration."""
        config = {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': self.DATABASE_NAME,
            'USER': self.DATABASE_USER,
            'PASSWORD': self.DATABASE_PASSWORD,
            'HOST': self.DATABASE_HOST,
            'PORT': self.DATABASE_PORT,
            'OPTIONS': {
                'autocommit': True,
            },
        }

        if self.DJANGO_ENV == 'production':
            config['OPTIONS']['init_command'] = "SET sql_mode='STRICT_TRANS_TABLES'"
            config['OPTIONS']['ssl'] = {'ca': '/app/hydrocarbures/ca.crt'}
            config['CONN_MAX_AGE'] = self.DB_CONN_MAX_AGE

        return config


# Singleton pattern with cache
_settings_instance: Optional[EnvironmentSettings] = None


def get_settings(force_reload: bool = False) -> EnvironmentSettings:
    """
    Get validated settings singleton.

    Args:
        force_reload: If True, reload settings from environment (useful for testing)

    Returns:
        Validated EnvironmentSettings instance

    Raises:
        SettingsValidationError: If configuration is invalid
    """
    global _settings_instance

    if _settings_instance is None or force_reload:
        try:
            _settings_instance = EnvironmentSettings()
        except Exception as e:
            if 'validation error' in str(e).lower():
                raise SettingsValidationError(f"Configuration validation failed: {e}")
            raise

    return _settings_instance


def get_env() -> str:
    """Get current environment name."""
    return os.environ.get('DJANGO_ENV', 'development')

