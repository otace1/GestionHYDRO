"""
CDN/S3 Storage Configuration.

IMPORTANT: This file should NOT contain any secrets.
All credentials are loaded from environment variables via hydrocarbures.config.

This file is kept for backward compatibility but credentials are now managed
in the environment-specific settings files (development.py, production.py).
"""
import os

# AWS credentials - MUST come from environment, never hardcoded
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# Allow overriding bucket and endpoint by env, with sensible defaults
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "gestionhydro")
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", "https://sfo3.digitaloceanspaces.com")
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}

AWS_LOCATION = os.environ.get(
    "AWS_LOCATION", "https://gestionhydro.sfo3.digitaloceanspaces.com"
)

DEFAULT_FILE_STORAGE = "hydrocarbures.cdn.backend.MediaRootS3BotoStorage"

STATICFILES_STORAGE = "hydrocarbures.cdn.backend.StaticRootS3BotoStorage"
