#!/bin/bash

set -e

cd /app/

python manage.py migrate --noinput
python manage.py migrate django_celery_results

exec "$@"