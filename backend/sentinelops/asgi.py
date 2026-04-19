"""
ASGI entry point for SentinelOps.

Serves both HTTP (via Django ASGI app) and WebSocket (via Django Channels).
Daphne uses this module as its target: `daphne sentinelops.asgi:application`.
"""

import os

import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sentinelops.settings.development")
django.setup()

# Import consumers AFTER django.setup() so models are ready.
from apps.monitoring.routing import websocket_urlpatterns  # noqa: E402

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)
