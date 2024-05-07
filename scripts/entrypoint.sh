#!/bin/bash

set -e

cd /app/

python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py migrate django_celery_results
gunicorn hydrocarbures.wsgi --bind 0.0.0.0:8000 --workers 4 --threads 4 --worker-tmp-dir /dev/shm

exec "$@"




