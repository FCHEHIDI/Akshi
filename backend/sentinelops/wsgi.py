"""
WSGI config for sentinelops project.

Exposes the WSGI callable as ``application``.
Used by gunicorn for synchronous HTTP fallback.
For production traffic, prefer the ASGI entry point (daphne).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sentinelops.settings.production")

application = get_wsgi_application()
