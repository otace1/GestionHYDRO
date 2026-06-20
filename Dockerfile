# syntax=docker/dockerfile:1.5
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# System deps (add only what you need)
# - build-essential/gcc: for compiling some python wheels
# - default-libmysqlclient-dev/pkg-config: if using mysqlclient
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    curl \
    nano \
  && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better caching)
COPY requirements/ /app/requirements/
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copy scripts and make them executable
COPY scripts/ /scripts/
RUN chmod +x /scripts/*.sh

# Copy project code last
COPY . /app

# Create non-root user
RUN useradd -m -u 10001 appuser \
  && chown -R appuser:appuser /app /scripts
USER appuser

ENTRYPOINT ["/scripts/entrypoint.sh"]