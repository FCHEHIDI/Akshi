"""
Test settings for SentinelOps.

Uses a faster password hasher and forces Celery tasks to run eagerly (inline).
Set DJANGO_SETTINGS_MODULE=sentinelops.settings.test
"""

import os

from .base import *  # noqa: F401, F403

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "testcorp.sentinelops.io"]

# ---------------------------------------------------------------------------
# Faster password hashing in tests
# ---------------------------------------------------------------------------
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ---------------------------------------------------------------------------
# Run Celery tasks synchronously (no worker needed)
# ---------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ---------------------------------------------------------------------------
# Use in-memory channel layer for WebSocket tests
# ---------------------------------------------------------------------------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

# ---------------------------------------------------------------------------
# Disable plugin encryption key requirement in tests
# ---------------------------------------------------------------------------
PLUGIN_ENCRYPTION_KEY = os.environ.get(
    "PLUGIN_ENCRYPTION_KEY",
    b"",  # type: ignore[assignment]
)
