#!/bin/bash
set -euo pipefail

cd /app/

echo "[entrypoint] collectstatic..."
python manage.py collectstatic --noinput

echo "[entrypoint] migrate..."
python manage.py migrate --noinput
python manage.py migrate django_celery_results --noinput || true

# ---- Gunicorn tuning for TIMEOUT / OOM-ish behavior ----
# Increase timeout so long DB queries don't get killed mid-read.
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-180}"          # 180s
GUNICORN_GRACEFUL_TIMEOUT="${GUNICORN_GRACEFUL_TIMEOUT:-30}"
GUNICORN_KEEPALIVE="${GUNICORN_KEEPALIVE:-5}"

# Reduce memory pressure:
# - fewer workers by default (4 workers can OOM on small pods)
# - recycle workers to prevent gradual memory growth
GUNICORN_WORKERS="${GUNICORN_WORKERS:-2}"
GUNICORN_THREADS="${GUNICORN_THREADS:-2}"
GUNICORN_MAX_REQUESTS="${GUNICORN_MAX_REQUESTS:-800}"
GUNICORN_MAX_REQUESTS_JITTER="${GUNICORN_MAX_REQUESTS_JITTER:-100}"

# Use /dev/shm if available (fast), otherwise fallback
WORKER_TMP_DIR="/dev/shm"
if [ ! -d "/dev/shm" ]; then
  WORKER_TMP_DIR="/tmp"
fi

echo "[entrypoint] starting gunicorn..."
exec gunicorn hydrocarbures.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "$GUNICORN_WORKERS" \
  --threads "$GUNICORN_THREADS" \
  --timeout "$GUNICORN_TIMEOUT" \
  --graceful-timeout "$GUNICORN_GRACEFUL_TIMEOUT" \
  --keep-alive "$GUNICORN_KEEPALIVE" \
  --max-requests "$GUNICORN_MAX_REQUESTS" \
  --max-requests-jitter "$GUNICORN_MAX_REQUESTS_JITTER" \
  --worker-tmp-dir "$WORKER_TMP_DIR" \
  --access-logfile "-" \
  --error-logfile "-" \
  --log-level info