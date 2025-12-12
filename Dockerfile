# Use Python 3.11 slim base image
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# System deps
# - libpq5 runtime for postgres
# - build deps to compile psycopg2 (if your requirements need it)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libpq-dev \
    gcc \
    curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python deps first (better cache)
COPY ./requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
 && pip install -r /app/requirements.txt

# (Optional) remove build deps after install to slim down
RUN apt-get update && apt-get purge -y --auto-remove gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy app source
COPY . /app

# Copy scripts
COPY ./scripts/entrypoint.sh /scripts/entrypoint.sh
COPY ./scripts/worker-entrypoint.sh /scripts/worker-entrypoint.sh
COPY ./scripts/migration.sh /scripts/migration.sh
COPY ./scripts/collectstatic.sh /scripts/collectstatic.sh
RUN chmod +x /scripts/*

# Non-root user
RUN useradd -m appuser \
 && chown -R appuser:appuser /app /scripts
USER appuser

# DO provides $PORT at runtime; keep a conventional exposed port
EXPOSE 8080

# Entrypoint handles default gunicorn OR executes DO run command
ENTRYPOINT ["/scripts/entrypoint.sh"]

# Leave CMD empty-ish; DO App Platform will set a Run Command per component.
# If no Run Command, entrypoint should start gunicorn by default.
CMD []