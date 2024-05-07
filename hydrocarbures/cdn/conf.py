import os

import hydrocarbures.cdn.backend

SPACE_SECRET=os.environ.get("SPACE_SECRET")
SPACE_ACCESS_KEY=os.environ.get("SPACE_ACCESS_KEY")
SPACE_NAME="gestionhydro"
SPACE_ENDPOINT="https://sfo3.digitaloceanspaces.com"
S3_OBJECT_PARAMETERS= {
    "CacheControl": "max-age=86400",
    "ACL": "public-read"
}
SPACE_LOCATION="https://gestionhydro.sfo3.digitaloceanspaces.com"
DEFAULT_FILE_STORAGE="hydrocarbures.cdn.backend.MediaRootS3BotoStorage"
STATICFILES_STORAGE="hydrocarbures.cdn.backend.StaticRootS3BotoStorage"
