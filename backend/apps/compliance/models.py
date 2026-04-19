"""
Compliance models — AuditEvent (append-only).
"""

from __future__ import annotations

import uuid

from django.db import models

from common.models import UUIDModel


class AuditEvent(UUIDModel):
    """
    Immutable audit log record.

    ``save()`` and ``delete()`` are overridden to enforce append-only semantics.
    A ``PermissionError`` is raised on any attempt to update or delete a record.

    Attributes:
        timestamp: When the event occurred (auto-set on creation).
        actor_id: UUID of the user who performed the action; None for system actions.
        actor_email: Email snapshot (denormalised so it survives user deletion).
        action: Dot-notation event name, e.g. ``"check.created"``.
        resource_type: Model name of the affected resource, e.g. ``"check"``.
        resource_id: UUID of the affected resource.
        diff: Before/after JSON snapshot for change events.
        ip_address: Client IP address (from request).
        user_agent: Client User-Agent string.
        metadata: Arbitrary contextual data.
    """

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    actor_id = models.UUIDField(null=True, blank=True)
    actor_email = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.UUIDField(null=True, blank=True)
    diff = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        app_label = "compliance"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.action} by {self.actor_email or 'system'}"

    def save(self, *args, **kwargs) -> None:  # type: ignore[override]
        """
        Override to prevent updates.

        Raises:
            PermissionError: If called on an existing record (pk already set).
        """
        if self.pk:
            raise PermissionError(
                "AuditEvent is immutable. Create a new record instead of updating."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> None:  # type: ignore[override]
        """
        Override to prevent deletion.

        Raises:
            PermissionError: Always — AuditEvent records cannot be deleted.
        """
        raise PermissionError("AuditEvent records cannot be deleted.")
