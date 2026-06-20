"""
TDD Tests for Django Split Settings Configuration.

These tests validate that:
1. Environment configuration is properly validated
2. Settings are correctly loaded based on DJANGO_ENV
3. Required variables cause fail-fast behavior when missing
4. Sensitive defaults are never used in production
"""
import os
import unittest
from unittest.mock import patch, MagicMock


class TestEnvironmentConfig(unittest.TestCase):
    """Test the Pydantic-based environment configuration."""

    def test_config_raises_error_when_secret_key_missing_in_production(self):
        """Production must fail-fast if DJANGO_SECRET_KEY is not set."""
        from hydrocarbures.config import get_settings, SettingsValidationError

        env = {
            'DJANGO_ENV': 'production',
            'DJANGO_SECRET_KEY': '',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SettingsValidationError) as context:
                get_settings(force_reload=True)
            self.assertIn('DJANGO_SECRET_KEY', str(context.exception))

    def test_config_allows_missing_secret_key_in_development(self):
        """Development mode should auto-generate a secret key if missing."""
        from hydrocarbures.config import get_settings

        env = {
            'DJANGO_ENV': 'development',
            'DJANGO_SECRET_KEY': '',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
        }

        with patch.dict(os.environ, env, clear=True):
            settings = get_settings(force_reload=True)
            self.assertTrue(len(settings.DJANGO_SECRET_KEY) >= 50)

    def test_debug_is_always_false_in_production(self):
        """DEBUG must be False in production, regardless of env var."""
        from hydrocarbures.config import get_settings

        env = {
            'DJANGO_ENV': 'production',
            'DEBUG': '1',  # Attempt to force DEBUG=True
            'DJANGO_SECRET_KEY': 'a-very-long-secret-key-for-testing-purposes-1234567890',
            'ALLOWED_HOSTS': 'example.com',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
            'AWS_ACCESS_KEY_ID': 'test-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret',
        }

        with patch.dict(os.environ, env, clear=True):
            settings = get_settings(force_reload=True)
            self.assertFalse(settings.DEBUG)

    def test_debug_defaults_to_true_in_development(self):
        """DEBUG should default to True in development."""
        from hydrocarbures.config import get_settings

        env = {
            'DJANGO_ENV': 'development',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
        }

        with patch.dict(os.environ, env, clear=True):
            settings = get_settings(force_reload=True)
            self.assertTrue(settings.DEBUG)

    def test_database_config_is_required(self):
        """Database configuration must be provided."""
        from hydrocarbures.config import get_settings, SettingsValidationError

        env = {
            'DJANGO_ENV': 'production',
            'DJANGO_SECRET_KEY': 'a-very-long-secret-key-for-testing-purposes-1234567890',
            # Missing DATABASE_* vars
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SettingsValidationError):
                get_settings(force_reload=True)

    def test_allowed_hosts_parsed_correctly(self):
        """ALLOWED_HOSTS should be parsed from comma-separated string."""
        from hydrocarbures.config import get_settings

        env = {
            'DJANGO_ENV': 'development',
            'ALLOWED_HOSTS': 'localhost, 127.0.0.1, example.com',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
        }

        with patch.dict(os.environ, env, clear=True):
            settings = get_settings(force_reload=True)
            self.assertEqual(
                settings.allowed_hosts_list,
                ['localhost', '127.0.0.1', 'example.com']
            )

    def test_allowed_hosts_not_empty_in_production(self):
        """Production must have at least one allowed host."""
        from hydrocarbures.config import get_settings, SettingsValidationError

        env = {
            'DJANGO_ENV': 'production',
            'DJANGO_SECRET_KEY': 'a-very-long-secret-key-for-testing-purposes-1234567890',
            'ALLOWED_HOSTS': '',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SettingsValidationError) as context:
                get_settings(force_reload=True)
            self.assertIn('ALLOWED_HOSTS', str(context.exception))


class TestSettingsModuleSelection(unittest.TestCase):
    """Test that the correct settings module is loaded."""

    def test_development_env_loads_development_settings(self):
        """DJANGO_ENV=development should load development settings."""
        env = {'DJANGO_ENV': 'development'}

        with patch.dict(os.environ, env):
            from hydrocarbures.settings import get_settings_module
            self.assertEqual(get_settings_module(), 'hydrocarbures.settings.development')

    def test_production_env_loads_production_settings(self):
        """DJANGO_ENV=production should load production settings."""
        env = {'DJANGO_ENV': 'production'}

        with patch.dict(os.environ, env):
            from hydrocarbures.settings import get_settings_module
            self.assertEqual(get_settings_module(), 'hydrocarbures.settings.production')

    def test_test_env_loads_test_settings(self):
        """DJANGO_ENV=test should load test settings."""
        env = {'DJANGO_ENV': 'test'}

        with patch.dict(os.environ, env):
            from hydrocarbures.settings import get_settings_module
            self.assertEqual(get_settings_module(), 'hydrocarbures.settings.test')

    def test_default_env_is_development(self):
        """When DJANGO_ENV is not set, default to development (safe default)."""
        with patch.dict(os.environ, {}, clear=True):
            from hydrocarbures.settings import get_settings_module
            self.assertEqual(get_settings_module(), 'hydrocarbures.settings.development')


class TestAWSSecretsNotHardcoded(unittest.TestCase):
    """Ensure AWS/S3 secrets are loaded from environment, never hardcoded."""

    def test_aws_access_key_from_environment(self):
        """AWS_ACCESS_KEY_ID must come from environment."""
        from hydrocarbures.config import get_settings

        env = {
            'DJANGO_ENV': 'development',
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
        }

        with patch.dict(os.environ, env, clear=True):
            settings = get_settings(force_reload=True)
            self.assertEqual(settings.AWS_ACCESS_KEY_ID, 'test-access-key')

    def test_aws_secrets_required_in_production(self):
        """Production must have AWS credentials configured."""
        from hydrocarbures.config import get_settings, SettingsValidationError

        env = {
            'DJANGO_ENV': 'production',
            'DJANGO_SECRET_KEY': 'a-very-long-secret-key-for-testing-purposes-1234567890',
            'ALLOWED_HOSTS': 'example.com',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
            # Missing AWS_* vars
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SettingsValidationError) as context:
                get_settings(force_reload=True)
            self.assertIn('AWS', str(context.exception))


class TestEnvironmentIsolation(unittest.TestCase):
    """
    Test that dev and prod environments are properly isolated.

    These tests ensure that development configurations cannot
    accidentally leak into production.
    """

    def test_development_uses_different_defaults_than_production(self):
        """Dev and prod should have different security defaults."""
        dev_env = {
            'DJANGO_ENV': 'development',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
        }

        prod_env = {
            'DJANGO_ENV': 'production',
            'DJANGO_SECRET_KEY': 'a-very-long-secret-key-for-testing-purposes-1234567890',
            'ALLOWED_HOSTS': 'example.com',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
            'AWS_ACCESS_KEY_ID': 'test-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret',
        }

        from hydrocarbures.config import get_settings

        with patch.dict(os.environ, dev_env, clear=True):
            dev_settings = get_settings(force_reload=True)

        with patch.dict(os.environ, prod_env, clear=True):
            prod_settings = get_settings(force_reload=True)

        # DEBUG must differ
        self.assertTrue(dev_settings.DEBUG)
        self.assertFalse(prod_settings.DEBUG)

    def test_production_secret_key_cannot_be_dev_key(self):
        """Production should reject weak or known development keys."""
        from hydrocarbures.config import get_settings, SettingsValidationError

        # Simulate using a short/weak key in production
        env = {
            'DJANGO_ENV': 'production',
            'DJANGO_SECRET_KEY': 'short-key',  # Too short for production
            'ALLOWED_HOSTS': 'example.com',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
            'AWS_ACCESS_KEY_ID': 'test-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret',
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SettingsValidationError):
                get_settings(force_reload=True)

    def test_csrf_trusted_origins_parsed_correctly(self):
        """CSRF_TRUSTED_ORIGINS should be parsed from comma-separated string."""
        from hydrocarbures.config import get_settings

        env = {
            'DJANGO_ENV': 'development',
            'CSRF_TRUSTED_ORIGINS': 'http://localhost:8000, https://example.com',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
        }

        with patch.dict(os.environ, env, clear=True):
            settings = get_settings(force_reload=True)
            self.assertEqual(
                settings.csrf_origins_list,
                ['http://localhost:8000', 'https://example.com']
            )

    def test_celery_broker_from_environment(self):
        """CELERY_BROKER must come from environment."""
        from hydrocarbures.config import get_settings

        env = {
            'DJANGO_ENV': 'development',
            'CELERY_BROKER': 'redis://custom-redis:6379/1',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
        }

        with patch.dict(os.environ, env, clear=True):
            settings = get_settings(force_reload=True)
            self.assertEqual(settings.CELERY_BROKER, 'redis://custom-redis:6379/1')


class TestSettingsModuleImport(unittest.TestCase):
    """Test that Django settings modules can be imported without errors."""

    def test_development_settings_importable(self):
        """Development settings should import without errors in dev env."""
        env = {
            'DJANGO_ENV': 'development',
            'DATABASE_HOST': 'localhost',
            'DATABASE_NAME': 'test',
            'DATABASE_USER': 'user',
            'DATABASE_PASSWORD': 'pass',
        }

        with patch.dict(os.environ, env, clear=True):
            # Clear cached settings
            from hydrocarbures.config import get_settings
            get_settings(force_reload=True)

            # This should not raise
            try:
                from importlib import import_module, reload
                module = import_module('hydrocarbures.settings.development')
                self.assertTrue(hasattr(module, 'DEBUG'))
            except Exception as e:
                self.fail(f"Failed to import development settings: {e}")


if __name__ == '__main__':
    unittest.main()

