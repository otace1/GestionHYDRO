#!/bin/bash

set -e

celery -A hydrocarbures worker --loglevel=info --concurrency 4 -E

exec "$@"




