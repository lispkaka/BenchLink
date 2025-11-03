"""
Celery configuration for BenchLink project.
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BenchLink.settings')

app = Celery('BenchLink')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()



