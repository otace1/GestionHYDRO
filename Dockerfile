FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# System deps needed to compile msgpack/grpcio and rust deps for pydantic_core
RUN apt-get update && apt-get install -y --no-install-recommends \
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

COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade pip setuptools wheel \
 && pip install --prefer-binary -r /app/requirements.txt

COPY . /app

COPY ./scripts/entrypoint.sh /scripts/entrypoint.sh
COPY ./scripts/worker-entrypoint.sh /scripts/worker-entrypoint.sh
RUN chmod +x /scripts/*

RUN useradd -m appuser && chown -R appuser:appuser /app /scripts
USER appuser

EXPOSE 8080

ENTRYPOINT ["/scripts/entrypoint.sh"]