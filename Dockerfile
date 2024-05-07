# Use Python 3.11-slim-buster base image
FROM python:3.11-slim-buster

ENV PYTHONUNBUFFERED=1

# Create Directory
RUN mkdir /app

# Set working directory
WORKDIR /app

# Copy the application files
COPY . /app

# Copy entrypoint script and set permissions
COPY ./scripts/entrypoint.sh /scripts/entrypoint.sh
COPY ./scripts/worker-entrypoint.sh /scripts/worker-entrypoint.sh
COPY ./scripts/migration.sh /scripts/migration.sh
COPY ./scripts/collectstatic.sh /scripts/collectstatic.sh
RUN chmod +x /scripts/*


## Create directories for static and media files with appropriate permissions
RUN mkdir -p /app/vol/web/static
RUN mkdir -p /app/vol/web/media

# Copy contents of assets/img to MEDIA_ROOT
COPY ./assets/img /vol/web/media

COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Set the entrypoint
ENTRYPOINT ["/scripts/entrypoint.sh"]
