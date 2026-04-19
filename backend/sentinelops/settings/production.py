"""
Production settings for SentinelOps.

All secrets MUST come from environment variables — never hard-code values here.
Set DJANGO_SETTINGS_MODULE=sentinelops.settings.production
"""

from .base import *  # noqa: F401, F403

if not SECRET_KEY:  # noqa: F405
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        "SECRET_KEY environment variable must be set in production. "
        "Generate one with: python -c 'import secrets; print(secrets.token_hex(50))'"
    )

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------
DEBUG = False
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------------
# Storage — use MinIO/S3 for static + media files in production
# ---------------------------------------------------------------------------
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
}
