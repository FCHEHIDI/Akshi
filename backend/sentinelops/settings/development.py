"""
Development settings for SentinelOps.

Extends base.py with DEBUG=True, relaxed security, and console email backend.
Set DJANGO_SETTINGS_MODULE=sentinelops.settings.development
"""

import os

from .base import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "dev-insecure-secret-key-do-not-use-in-production-ever",
)
DEBUG = True
ALLOWED_HOSTS = ["*"]
APPEND_SLASH = False

# ---------------------------------------------------------------------------
# Database — uses PostgreSQL by default (same as prod) to keep parity.
# Override DATABASE_URL in .env to point to your local PG instance.
# ---------------------------------------------------------------------------
# Inherited from base.py — just ensure your local .env has DATABASE_URL set.

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ---------------------------------------------------------------------------
# CORS (allow all in dev)
# ---------------------------------------------------------------------------
INSTALLED_APPS = INSTALLED_APPS + ["corsheaders"]  # type: ignore[name-defined]  # noqa: F405
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
] + MIDDLEWARE  # type: ignore[name-defined]  # noqa: F405
CORS_ALLOW_ALL_ORIGINS = True
