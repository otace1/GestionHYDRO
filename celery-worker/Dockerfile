# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Run Celery worker when the container launches
CMD celery -A hydrocarbures worker --loglevel=info --concurrency 4 -E -b rediss://default:AVNS_BYb1N7gemjfX_bH3Zc5@db-redis-sfo3-68436-do-user-4618658-0.c.db.ondigitalocean.com:25061
