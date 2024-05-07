#!/bin/bash

set -e

cd /app/

python manage.py collectstatic --noinput

exec "$@"