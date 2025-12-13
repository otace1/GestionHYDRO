#!/usr/bin/env bash
set -euo pipefail

cd /app

# DigitalOcean sets PORT; fallback to 8000 for local/dev
: "${PORT:=8000}"

# Set PROCESS_TYPE=web for Web Service, PROCESS_TYPE=worker for Worker
: "${PROCESS_TYPE:=web}"

# ---------------------------
# WEB: migrations + static
# ---------------------------
run_migrations() {
  # If you want to enable later, uncomment below.
  # echo "==> collectstatic"
  # python manage.py collectstatic --noinput
  #
  # echo "==> migrate"
  # python manage.py migrate --noinput
  #
  # echo "==> migrate django_celery_results"
  # python manage.py migrate django_celery_results --noinput || true

  : # <-- IMPORTANT: non-empty function body (prevents bash parse error)
}

# ---------------------------
# Defaults tuned per DO sizing
# Web: 4 GB RAM / 1 Dedicated vCPU
# Worker: 1 GB RAM / 1 Shared vCPU
# ---------------------------

# Gunicorn tuning for 1 vCPU / 4GB RAM
: "${GUNICORN_WORKERS:=2}"
: "${GUNICORN_THREADS:=4}"
: "${GUNICORN_TIMEOUT:=120}"
: "${GUNICORN_MAX_REQUESTS:=1000}"
: "${GUNICORN_MAX_REQUESTS_JITTER:=100}"
: "${GUNICORN_KEEPALIVE:=5}"

# Celery tuning for 1GB / shared vCPU
: "${CELERY_CONCURRENCY:=1}"
: "${CELERY_PREFETCH_MULTIPLIER:=1}"
: "${CELERY_MAX_TASKS_PER_CHILD:=100}"
: "${CELERY_LOGLEVEL:=info}"

if [[ "${PROCESS_TYPE}" == "web" ]]; then
  run_migrations
fi

# Optional: allow migrations on worker ONLY if explicitly enabled
if [[ "${PROCESS_TYPE}" == "worker" && "${RUN_MIGRATIONS_ON_WORKER:-0}" == "1" ]]; then
  echo "Worker migrations enabled (RUN_MIGRATIONS_ON_WORKER=1)"
  python manage.py migrate --noinput
  python manage.py migrate django_celery_results --noinput || true
fi

# If DO provides a Run Command, execute it
if [[ $# -gt 0 ]]; then
  exec "$@"
fi

# Otherwise choose default by PROCESS_TYPE
if [[ "${PROCESS_TYPE}" == "worker" ]]; then
  echo "==> Starting Celery Worker (1GB tuning): concurrency=${CELERY_CONCURRENCY}"
  exec celery -A hydrocarbures worker \
    -l "${CELERY_LOGLEVEL}" \
    --concurrency="${CELERY_CONCURRENCY}" \
    --prefetch-multiplier="${CELERY_PREFETCH_MULTIPLIER}" \
    --max-tasks-per-child="${CELERY_MAX_TASKS_PER_CHILD}" \
    --without-gossip \
    --without-mingle \
    --heartbeat-interval=30
else
  echo "==> Starting Gunicorn (4GB/1vCPU tuning): workers=${GUNICORN_WORKERS} threads=${GUNICORN_THREADS}"
  exec gunicorn hydrocarbures.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers "${GUNICORN_WORKERS}" \
    --threads "${GUNICORN_THREADS}" \
    --timeout "${GUNICORN_TIMEOUT}" \
    --keep-alive "${GUNICORN_KEEPALIVE}" \
    --max-requests "${GUNICORN_MAX_REQUESTS}" \
    --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER}" \
    --worker-tmp-dir /dev/shm
fi