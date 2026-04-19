"""WebSocket URL patterns for the monitoring app."""

from django.urls import path

from apps.monitoring.consumers import DashboardConsumer, IncidentFeedConsumer

websocket_urlpatterns = [
    path("ws/dashboard/", DashboardConsumer.as_asgi()),
    path("ws/incidents/", IncidentFeedConsumer.as_asgi()),
]
