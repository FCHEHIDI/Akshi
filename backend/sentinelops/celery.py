"""
Celery application instance for SentinelOps.

This module initialises the Celery app and ensures Django settings are loaded
before any task is imported.  It also auto-discovers tasks in all INSTALLED_APPS.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sentinelops.settings.development")

app = Celery("sentinelops")

# Read config from Django settings, using the CELERY_ prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in each installed app.
app.autodiscover_tasks()
