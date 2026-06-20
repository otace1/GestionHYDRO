import os
from pathlib import Path
from dotenv import load_dotenv
from celery import Celery

# Load .env file
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# Dynamically select settings based on DJANGO_ENV
from hydrocarbures.settings import get_settings_module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', get_settings_module())

app = Celery('hydrocarbures')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespacpue='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')