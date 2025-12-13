FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# System deps:
# - bash: ensure /usr/bin/env bash works
# - dos2unix: fix CRLF if repo was edited on Windows
# - build deps: compile msgpack/grpcio + rust for pydantic_core
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    dos2unix \
    build-essential \
    gcc \
    g++ \
    make \
    python3-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    rustc \
    cargo \
    libpq5 \
    curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (better cache)
COPY ./requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel \
 && pip install --prefer-binary -r /app/requirements.txt

# Copy app
COPY . /app

# Copy scripts and ensure:
# - executable
# - LF line endings
# - bash shebang
COPY ./scripts/entrypoint.sh /scripts/entrypoint.sh
COPY ./scripts/worker-entrypoint.sh /scripts/worker-entrypoint.sh
RUN chmod +x /scripts/*.sh \
 && dos2unix /scripts/*.sh \
 && sed -i '1s|^.*$|#!/usr/bin/env bash|' /scripts/entrypoint.sh /scripts/worker-entrypoint.sh

# Non-root user
RUN useradd -m appuser \
 && chown -R appuser:appuser /app /scripts
USER appuser

# DO provides PORT at runtime (commonly 8080)
EXPOSE 8080

# Force bash to run the entrypoint, regardless of platform shell behavior
ENTRYPOINT ["/bin/bash", "/scripts/entrypoint.sh"]