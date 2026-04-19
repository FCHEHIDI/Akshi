"""
DRF serializers for the monitoring app.

Hierarchy:
    ServiceSerializer           — CRUD on Service
    CheckSerializer             — CRUD on Check (nested under Service)
    CheckResultSerializer       — read-only, nested under Check
    IncidentSerializer          — read + acknowledge/resolve actions
"""

from __future__ import annotations

import logging

from rest_framework import serializers

from apps.monitoring.models import (
    Check,
    CheckResult,
    Incident,
    IncidentState,
    Service,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ServiceSerializer(serializers.ModelSerializer):
    """
    Full CRUD serializer for Service.

    Read-only computed fields:
        checks_count: Total number of checks attached to this service.
        open_incidents_count: Number of currently open or acknowledged incidents.
    """

    checks_count = serializers.SerializerMethodField()
    open_incidents_count = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "tags",
            "status",
            "sla_target",
            "checks_count",
            "open_incidents_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "checks_count", "open_incidents_count", "created_at", "updated_at"]

    def get_checks_count(self, obj: Service) -> int:
        """
        Return the total number of checks for this service.

        Args:
            obj: The Service instance.

        Returns:
            Integer count of associated checks.
        """
        return obj.checks.count()

    def get_open_incidents_count(self, obj: Service) -> int:
        """
        Return the number of open or acknowledged incidents for this service.

        Args:
            obj: The Service instance.

        Returns:
            Integer count of active incidents.
        """
        return obj.incidents.filter(
            state__in=[IncidentState.OPEN, IncidentState.ACKNOWLEDGED]
        ).count()


# ---------------------------------------------------------------------------
# Check
# ---------------------------------------------------------------------------


class CheckSerializer(serializers.ModelSerializer):
    """
    Full CRUD serializer for Check.

    The ``service`` field is injected from the URL kwarg in the view,
    so it is read-only here (not writable by the client).
    """

    service_id = serializers.UUIDField(source="service.id", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = Check
        fields = [
            "id",
            "service_id",
            "service_name",
            "name",
            "check_type",
            "config",
            "interval_seconds",
            "retry_count",
            "is_enabled",
            "next_run_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "service_id",
            "service_name",
            "next_run_at",
            "created_at",
            "updated_at",
        ]

    def validate_interval_seconds(self, value: int) -> int:
        """
        Enforce minimum polling interval of 30 seconds.

        Args:
            value: The interval in seconds provided by the client.

        Returns:
            The validated value.

        Raises:
            serializers.ValidationError: If value is below 30.
        """
        if value < 30:
            raise serializers.ValidationError("interval_seconds must be at least 30.")
        return value

    def validate_config(self, value: dict) -> dict:
        """
        Validate that config is a non-empty dict.

        Args:
            value: The config JSON provided by the client.

        Returns:
            The validated value.

        Raises:
            serializers.ValidationError: If value is not a non-empty dict.
        """
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("config must be a non-empty JSON object.")
        return value


# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------


class CheckResultSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for CheckResult.

    Used for the check history endpoint.
    """

    class Meta:
        model = CheckResult
        fields = [
            "id",
            "status",
            "duration_ms",
            "response_code",
            "error_message",
            "checked_via",
            "created_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Incident
# ---------------------------------------------------------------------------


class IncidentSerializer(serializers.ModelSerializer):
    """
    Read serializer for Incident.

    Includes denormalised service and check names for convenience.
    Write operations (acknowledge / resolve) use dedicated action serializers.
    """

    service_name = serializers.CharField(source="service.name", read_only=True)
    check_name = serializers.CharField(source="health_check.name", read_only=True)
    check_type = serializers.CharField(source="health_check.check_type", read_only=True)

    class Meta:
        model = Incident
        fields = [
            "id",
            "service_id",
            "service_name",
            "check_name",
            "check_type",
            "state",
            "severity",
            "opened_at",
            "acknowledged_at",
            "resolved_at",
            "ack_note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AcknowledgeIncidentSerializer(serializers.Serializer):
    """
    Input serializer for the acknowledge action.

    Args:
        ack_note: Optional human note explaining the acknowledgement.
    """

    ack_note = serializers.CharField(required=False, allow_blank=True, default="")
