"""
Base abstract models shared across all SentinelOps apps.

All models in the project should inherit from one of these mixins to ensure
consistent primary keys, timestamps, and soft-delete behaviour.
"""

import uuid

from django.db import models
from django.utils import timezone


class UUIDModel(models.Model):
    """
    Replaces the default auto-increment integer PK with a UUID v4.

    UUIDs are stable, non-guessable, and safe to expose in URLs/API responses.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(UUIDModel):
    """
    Adds ``created_at`` and ``updated_at`` timestamps to a model.

    ``created_at`` is set once on INSERT; ``updated_at`` is refreshed on every UPDATE.
    Both are indexed for efficient time-range queries.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet that excludes soft-deleted records by default."""

    def alive(self) -> "SoftDeleteQuerySet":
        """Return only non-deleted records."""
        return self.filter(deleted_at__isnull=True)

    def deleted(self) -> "SoftDeleteQuerySet":
        """Return only deleted records."""
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """
    Default manager for SoftDeleteModel.

    The queryset excludes records where ``deleted_at`` is set, making soft-deleted
    rows invisible to normal ORM queries.  Use ``Model.all_objects`` to bypass this.
    """

    def get_queryset(self) -> SoftDeleteQuerySet:
        """Return a queryset that excludes soft-deleted records."""
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class SoftDeleteModel(TimestampedModel):
    """
    Soft-delete mixin.

    Instead of issuing a SQL DELETE, sets ``deleted_at`` to the current timestamp.
    The default manager hides deleted records from all queries.

    Use ``hard_delete()`` only when data must be physically removed (e.g. GDPR erasure).

    Attributes:
        deleted_at: Timestamp of soft-deletion; ``None`` while the record is active.
        objects: Manager that excludes soft-deleted rows (default).
        all_objects: Unfiltered manager that includes all rows.
    """

    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects: SoftDeleteManager = SoftDeleteManager()
    all_objects: models.Manager = models.Manager()

    def delete(self, using: str | None = None, keep_parents: bool = False) -> tuple[int, dict]:  # type: ignore[override]
        """
        Soft-delete the record by setting ``deleted_at`` to now.

        Args:
            using: Database alias to use (forwarded to save).
            keep_parents: Ignored (kept for API compatibility).

        Returns:
            Tuple of (1, {model_label: 1}) to mimic Django's hard-delete return value.
        """
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])
        return 1, {self._meta.label: 1}

    def hard_delete(self, using: str | None = None, keep_parents: bool = False) -> None:
        """
        Permanently delete the record from the database.

        Use only when physical removal is required (e.g. GDPR right-to-erasure).

        Args:
            using: Database alias to use.
            keep_parents: Forwarded to Django's super().delete().
        """
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self) -> None:
        """Un-delete a soft-deleted record by clearing ``deleted_at``."""
        self.deleted_at = None
        self.save(update_fields=["deleted_at", "updated_at"])

    class Meta:
        abstract = True


class TenantScopedModel(TimestampedModel):
    """
    Marker mixin for models that live inside a tenant's PostgreSQL schema.

    No FK to Organization is needed — schema isolation provided by django-tenants
    guarantees that rows in one tenant's schema are never visible to another tenant.
    All tenant-specific apps (monitoring, automations, compliance, plugins) should
    use this as their base class instead of TimestampedModel.
    """

    class Meta:
        abstract = True
