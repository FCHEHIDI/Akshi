"""
Monitoring models — Service, Check, CheckResult, Incident, NotificationChannel.

All models inherit from TenantScopedModel and live in the tenant's PostgreSQL schema.
"""

from __future__ import annotations

from django.db import models

from common.models import SoftDeleteModel, TenantScopedModel, TimestampedModel


class ServiceStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    ARCHIVED = "archived", "Archived"


class CheckType(models.TextChoices):
    HTTP = "http", "HTTP"
    TCP = "tcp", "TCP"
    PING = "ping", "Ping"
    CRON = "cron", "Cron Heartbeat"


class CheckStatus(models.TextChoices):
    OK = "ok", "OK"
    FAIL = "fail", "Fail"
    TIMEOUT = "timeout", "Timeout"
    UNKNOWN = "unknown", "Unknown"


class IncidentState(models.TextChoices):
    OPEN = "open", "Open"
    ACKNOWLEDGED = "acknowledged", "Acknowledged"
    RESOLVED = "resolved", "Resolved"


class Severity(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class Service(SoftDeleteModel, TenantScopedModel):
    """
    A monitored service (e.g. "API Gateway", "PostgreSQL primary").

    Attributes:
        name: Human-readable service name.
        description: Optional longer description.
        tags: JSON list of strings for filtering (e.g. ``["api", "production"]``).
        status: Lifecycle status (active / paused / archived).
        sla_target: Target uptime percentage (e.g. ``99.900``).
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list)
    status = models.CharField(
        max_length=20, choices=ServiceStatus.choices, default=ServiceStatus.ACTIVE
    )
    sla_target = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)

    class Meta(SoftDeleteModel.Meta):
        app_label = "monitoring"

    def __str__(self) -> str:
        return self.name


class Check(SoftDeleteModel, TenantScopedModel):
    """
    A single health-check configuration attached to a Service.

    Attributes:
        service: The parent Service.
        name: Human-readable check name.
        check_type: http | tcp | ping | cron.
        config: Type-specific JSON config (see architecture doc §7.4).
        interval_seconds: How often the check runs (minimum 30).
        retry_count: Number of consecutive failures before opening an incident.
        is_enabled: Pause without deleting.
        next_run_at: Used by Celery Beat for dispatch scheduling.
    """

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="checks")
    name = models.CharField(max_length=255)
    check_type = models.CharField(max_length=10, choices=CheckType.choices)
    config = models.JSONField()
    interval_seconds = models.PositiveIntegerField(default=60)
    retry_count = models.PositiveIntegerField(default=3)
    is_enabled = models.BooleanField(default=True)
    next_run_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta(SoftDeleteModel.Meta):
        app_label = "monitoring"

    def __str__(self) -> str:
        return f"{self.name} [{self.check_type}]"


class CheckResult(TenantScopedModel):
    """
    Append-only record of a single check execution.

    Never updated after creation.  Used for SLA calculations and uptime history.

    Attributes:
        health_check: The Check that produced this result.
        status: ok | fail | timeout | unknown.
        duration_ms: End-to-end check duration in milliseconds.
        response_code: HTTP status code (HTTP checks only).
        error_message: Human-readable error description on failure.
        checked_via: ``"cloud"`` or the ID of the on-prem agent.
    """

    health_check = models.ForeignKey(Check, on_delete=models.CASCADE, related_name="results")
    status = models.CharField(max_length=10, choices=CheckStatus.choices)
    duration_ms = models.PositiveIntegerField()
    response_code = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    checked_via = models.CharField(max_length=255, default="cloud")

    class Meta:
        app_label = "monitoring"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.health_check.name} → {self.status} ({self.duration_ms}ms)"


class Incident(TenantScopedModel):
    """
    An incident triggered when a Check fails beyond its retry threshold.

    State machine: open → acknowledged → resolved (can re-open from resolved).

    Attributes:
        service: Denormalised reference to the service for quick queries.
        health_check: The Check that triggered this incident.
        state: open | acknowledged | resolved.
        severity: low | medium | high | critical.
        opened_at: When the incident was first detected.
        acknowledged_at: When a team member acknowledged it.
        resolved_at: When the check recovered.
        ack_note: Optional note left during acknowledgement.
    """

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="incidents")
    health_check = models.ForeignKey(Check, on_delete=models.CASCADE, related_name="incidents")
    state = models.CharField(
        max_length=20, choices=IncidentState.choices, default=IncidentState.OPEN, db_index=True
    )
    severity = models.CharField(
        max_length=20, choices=Severity.choices, default=Severity.MEDIUM
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    ack_note = models.TextField(blank=True)

    class Meta:
        app_label = "monitoring"
        ordering = ["-opened_at"]

    def __str__(self) -> str:
        return f"Incident [{self.state}] on {self.service.name}"


# ---------------------------------------------------------------------------
# Notification channels
# ---------------------------------------------------------------------------


class ChannelType(models.TextChoices):
    SLACK = "slack", "Slack Webhook"
    EMAIL = "email", "Email"
    WEBHOOK = "webhook", "Generic Webhook"


class NotificationChannel(TenantScopedModel):
    """
    A delivery channel for incident notifications (Slack, email, or HTTP webhook).

    Channels are tenant-scoped. Every active channel is evaluated each time an
    incident is opened, escalated, or resolved.

    Attributes:
        name: Human-readable label (e.g. ``"#ops-alerts Slack"``).
        channel_type: ``slack`` | ``email`` | ``webhook``.
        config: Channel-specific JSON config.

            * **slack** / **webhook**: ``{"url": "https://..."}``.
              Webhook may also include ``{"headers": {"Authorization": "Bearer ..."}}``.'
            * **email**: ``{"to": ["alice@example.com", "bob@example.com"]}``.

        is_active: Master on/off switch.
        notify_on_open: Send when a new incident is opened.
        notify_on_resolve: Send when an incident is resolved.
        min_severity: Only notify if incident severity >= this value.
    """

    name = models.CharField(max_length=255)
    channel_type = models.CharField(max_length=20, choices=ChannelType.choices)
    config = models.JSONField()
    is_active = models.BooleanField(default=True, db_index=True)
    notify_on_open = models.BooleanField(default=True)
    notify_on_resolve = models.BooleanField(default=True)
    min_severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.LOW,
    )

    class Meta:
        app_label = "monitoring"

    def __str__(self) -> str:
        return f"{self.name} [{self.channel_type}]"
