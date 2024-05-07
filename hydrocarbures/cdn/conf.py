import os

import hydrocarbures.cdn.backend

AWS_ACCESS_KEY_ID=os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME="gestionhydro"
AWS_S3_ENDPOINT_URL="https://sfo3.digitaloceanspaces.com"
AWS_S3_OBJECT_PARAMETERS= {
    "CacheControl": "max-age=86400",
    "ACL": "public-read"
}
AWS_LOCATION="https://gestionhydro.sfo3.digitaloceanspaces.com"
DEFAULT_FILE_STORAGE="hydrocarbures.cdn.backend.MediaRootS3BotoStorage"
STATICFILES_STORAGE="hydrocarbures.cdn.backend.StaticRootS3BotoStorage"
