"""
Notification dispatch — Phase 1, Bloc 6.

notify() is called from the incident state machine after every state change.
It enqueues a send_notification_task Celery task for each active
NotificationChannel that matches the event and severity filters.

Supported channel types
-----------------------
* **slack**   — HTTP POST to a Slack Incoming Webhook URL.
* **email**   — Django ``send_mail`` via the configured SMTP backend.
* **webhook** — Generic HTTP POST with a JSON payload.

Channel config schemas
----------------------
* slack / webhook: ``{"url": "https://..."}``
  Webhook may optionally include ``{"headers": {"Authorization": "Bearer ..."}}``
* email: ``{"to": ["alice@example.com"]}``

Events
------
* ``"opened"``    — new incident created
* ``"escalated"`` — existing incident severity increased
* ``"resolved"``  — incident transitioned to RESOLVED
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    pass  # avoid circular imports at type-check time

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Severity ordering for min_severity filtering
# ---------------------------------------------------------------------------

_SEVERITY_RANK: dict[str, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


# ---------------------------------------------------------------------------
# Public entry point  (sync — just enqueues tasks)
# ---------------------------------------------------------------------------


def notify(incident: object, event: str) -> None:
    """
    Enqueue a ``send_notification_task`` for every applicable active channel.

    Filtering rules applied per channel:
    - ``is_active`` must be ``True``
    - For ``"opened"`` / ``"escalated"``: ``notify_on_open`` must be ``True``
    - For ``"resolved"``: ``notify_on_resolve`` must be ``True``
    - ``incident.severity`` rank must be >= ``channel.min_severity`` rank

    Args:
        incident: The ``Incident`` model instance that changed state.
        event: One of ``"opened"``, ``"escalated"``, ``"resolved"``.
    """
    from apps.monitoring.models import NotificationChannel  # noqa: PLC0415

    channels = NotificationChannel.objects.filter(is_active=True)

    incident_rank = _SEVERITY_RANK.get(incident.severity, 0)

    dispatched = 0
    for channel in channels:
        # Severity gate
        channel_min_rank = _SEVERITY_RANK.get(channel.min_severity, 0)
        if incident_rank < channel_min_rank:
            continue

        # Event gate
        if event in ("opened", "escalated") and not channel.notify_on_open:
            continue
        if event == "resolved" and not channel.notify_on_resolve:
            continue

        send_notification_task.delay(str(channel.id), str(incident.id), event)
        dispatched += 1

    logger.debug(
        "notifications: dispatched event=%s incident=%s channels=%d",
        event,
        incident.id,
        dispatched,
    )


# ---------------------------------------------------------------------------
# Celery task  (async delivery)
# ---------------------------------------------------------------------------


def _get_celery_app():
    """Lazy import of the Celery app to avoid circular imports."""
    from sentinelops.celery import app  # noqa: PLC0415

    return app


# We define the task function first, then register it with Celery lazily
# to avoid the circular import chain:
#   notifications → sentinelops.celery → django.setup → models → notifications
import functools  # noqa: E402

import celery  # noqa: E402


@celery.shared_task(
    name="monitoring.send_notification",
    queue="checks",
    ignore_result=True,
    max_retries=2,
    default_retry_delay=30,
    bind=True,
)
def send_notification_task(self, channel_id: str, incident_id: str, event: str) -> None:
    """
    Deliver one notification to one channel.

    Retries up to 2 times with a 30-second delay on transient failures
    (network errors, SMTP timeouts).

    Args:
        channel_id: UUID string of the ``NotificationChannel``.
        incident_id: UUID string of the ``Incident``.
        event: One of ``"opened"``, ``"escalated"``, ``"resolved"``.
    """
    import requests  # noqa: PLC0415

    from apps.monitoring.models import Incident, NotificationChannel  # noqa: PLC0415

    try:
        channel = NotificationChannel.objects.get(id=channel_id)
        incident = Incident.objects.get(id=incident_id)
    except Exception:  # noqa: BLE001
        # Channel or incident deleted in the meantime — silently drop.
        logger.warning(
            "notifications: channel or incident not found channel=%s incident=%s",
            channel_id,
            incident_id,
        )
        return

    payload = _build_payload(incident, event)

    try:
        if channel.channel_type == "slack":
            _send_slack(channel.config, payload)
        elif channel.channel_type == "email":
            _send_email(channel.config, payload)
        elif channel.channel_type == "webhook":
            _send_webhook(channel.config, payload, requests)
        else:
            logger.error(
                "notifications: unknown channel_type=%s channel=%s",
                channel.channel_type,
                channel.id,
            )
            return
    except Exception as exc:
        logger.warning(
            "notifications: delivery failed channel=%s event=%s error=%s — retrying",
            channel.id,
            event,
            exc,
        )
        raise self.retry(exc=exc)

    logger.info(
        "notifications: delivered channel=%s type=%s event=%s incident=%s",
        channel.id,
        channel.channel_type,
        event,
        incident.id,
    )


# ---------------------------------------------------------------------------
# Payload builder
# ---------------------------------------------------------------------------

_EVENT_EMOJI: dict[str, str] = {
    "opened": ":red_circle:",
    "escalated": ":large_orange_circle:",
    "resolved": ":large_green_circle:",
}

_EVENT_LABEL: dict[str, str] = {
    "opened": "OPENED",
    "escalated": "ESCALATED",
    "resolved": "RESOLVED",
}


def _build_payload(incident: object, event: str) -> dict:
    """
    Build a canonical notification payload from an incident + event.

    Args:
        incident: The ``Incident`` model instance.
        event: ``"opened"``, ``"escalated"``, or ``"resolved"``.

    Returns:
        A dict with keys ``text`` (plain), ``subject`` (email subject),
        ``body`` (multi-line), and ``meta`` (structured data for webhooks).
    """
    emoji = _EVENT_EMOJI.get(event, ":white_circle:")
    label = _EVENT_LABEL.get(event, event.upper())

    subject = f"[SentinelOps] {label}: {incident.service.name} — {incident.health_check.name}"

    body_lines = [
        f"Event    : {label}",
        f"Service  : {incident.service.name}",
        f"Check    : {incident.health_check.name} ({incident.health_check.check_type})",
        f"Severity : {incident.severity.upper()}",
        f"State    : {incident.state}",
        f"Opened at: {incident.opened_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
    ]
    if incident.resolved_at:
        body_lines.append(
            f"Resolved : {incident.resolved_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )

    body = "\n".join(body_lines)
    slack_text = f"{emoji} *{subject}*\n```{body}```"

    return {
        "text": slack_text,
        "subject": subject,
        "body": body,
        "meta": {
            "event": event,
            "incident_id": str(incident.id),
            "service": incident.service.name,
            "check": incident.health_check.name,
            "severity": incident.severity,
            "state": incident.state,
        },
    }


# ---------------------------------------------------------------------------
# Channel-specific senders
# ---------------------------------------------------------------------------


def _send_slack(config: dict, payload: dict) -> None:
    """
    POST a message to a Slack Incoming Webhook.

    Args:
        config: Channel config. Must contain ``url`` key.
        payload: The canonical payload dict from :func:`_build_payload`.

    Raises:
        requests.HTTPError: If Slack returns a non-2xx status.
        KeyError: If ``config`` is missing the ``url`` key.
    """
    import requests  # noqa: PLC0415

    url = config["url"]
    response = requests.post(
        url,
        json={"text": payload["text"]},
        timeout=10,
    )
    response.raise_for_status()


def _send_email(config: dict, payload: dict) -> None:
    """
    Send an email using Django's configured email backend.

    Args:
        config: Channel config. Must contain ``to`` key (list of addresses).
        payload: The canonical payload dict from :func:`_build_payload`.

    Raises:
        django.core.mail.BadHeaderError: If subject contains forbidden chars.
        KeyError: If ``config`` is missing the ``to`` key.
    """
    from django.core.mail import send_mail  # noqa: PLC0415

    send_mail(
        subject=payload["subject"],
        message=payload["body"],
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@sentinelops.io"),
        recipient_list=config["to"],
        fail_silently=False,
    )


def _send_webhook(config: dict, payload: dict, requests_module) -> None:
    """
    POST the full ``meta`` dict to a generic HTTP endpoint.

    Args:
        config: Channel config. Must contain ``url`` key. Optionally
            ``headers`` dict for auth tokens etc.
        payload: The canonical payload dict from :func:`_build_payload`.
        requests_module: The ``requests`` module (injected to avoid re-import).

    Raises:
        requests.HTTPError: If the endpoint returns a non-2xx status.
        KeyError: If ``config`` is missing the ``url`` key.
    """
    url = config["url"]
    headers = config.get("headers", {})
    response = requests_module.post(
        url,
        json=payload["meta"],
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
