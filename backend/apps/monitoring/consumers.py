"""
WebSocket consumers for the monitoring app.

DashboardConsumer  — real-time service status feed for an organisation.
IncidentFeedConsumer — real-time incident events feed.
"""

from __future__ import annotations

import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class DashboardConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for the live monitoring dashboard.

    Clients connect to ``ws://host/ws/dashboard/`` and are added to the
    ``dashboard:{org_slug}`` channel group.  Any Celery task that broadcasts
    to this group will be forwarded to all connected clients.

    Message types handled:
        - ``service.status`` — a check result was recorded.
        - ``incident.opened`` — a new incident was created.
        - ``incident.resolved`` — an incident was resolved.
    """

    async def connect(self) -> None:
        """Accept the connection and join the organisation's channel group."""
        # TODO: validate JWT token from query string before accepting
        tenant = getattr(self.scope.get("tenant"), "slug", "unknown")
        self.group_name = f"dashboard:{tenant}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug("WS connected: group=%s channel=%s", self.group_name, self.channel_name)

    async def disconnect(self, close_code: int) -> None:
        """Leave the channel group on disconnect."""
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.debug("WS disconnected: group=%s code=%s", self.group_name, close_code)

    # ------------------------------------------------------------------
    # Handlers for messages sent via channel_layer.group_send()
    # ------------------------------------------------------------------

    async def service_status(self, event: dict) -> None:
        """Forward a service.status event to the WebSocket client."""
        await self.send_json(event)

    async def incident_opened(self, event: dict) -> None:
        """Forward an incident.opened event to the WebSocket client."""
        await self.send_json(event)

    async def incident_resolved(self, event: dict) -> None:
        """Forward an incident.resolved event to the WebSocket client."""
        await self.send_json(event)


class IncidentFeedConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for the incident-only feed.

    Useful for alert dashboards that only care about incident state changes.
    """

    async def connect(self) -> None:
        tenant = getattr(self.scope.get("tenant"), "slug", "unknown")
        self.group_name = f"incidents:{tenant}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def incident_opened(self, event: dict) -> None:
        await self.send_json(event)

    async def incident_resolved(self, event: dict) -> None:
        await self.send_json(event)

    async def incident_acknowledged(self, event: dict) -> None:
        await self.send_json(event)
