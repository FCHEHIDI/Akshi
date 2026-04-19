"""
DRF views for the monitoring app — Phase 1, Bloc 4.

URL structure:
    /api/v1/services/                          ServiceListCreateView
    /api/v1/services/<pk>/                     ServiceDetailView
    /api/v1/services/<service_pk>/checks/      CheckListCreateView
    /api/v1/services/<service_pk>/checks/<pk>/ CheckDetailView
    /api/v1/checks/<check_pk>/results/         CheckResultListView
    /api/v1/incidents/                         IncidentListView
    /api/v1/incidents/<pk>/acknowledge/        AcknowledgeIncidentView
    /api/v1/incidents/<pk>/resolve/            ResolveIncidentView
"""

from __future__ import annotations

import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.monitoring.models import (
    Check,
    CheckResult,
    Incident,
    IncidentState,
    Service,
)
from apps.monitoring.serializers import (
    AcknowledgeIncidentSerializer,
    CheckResultSerializer,
    CheckSerializer,
    IncidentSerializer,
    ServiceSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Service views
# ---------------------------------------------------------------------------


class ServiceListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/services/  — list all services for the current tenant.
    POST /api/v1/services/  — create a new service.

    Supports filtering by status via ?status=active|paused|archived.
    """

    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return non-deleted services for the current tenant, ordered by name.

        Returns:
            QuerySet of Service instances.
        """
        qs = Service.objects.all().order_by("name")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/services/<pk>/  — retrieve a service.
    PUT    /api/v1/services/<pk>/  — full update.
    PATCH  /api/v1/services/<pk>/  — partial update.
    DELETE /api/v1/services/<pk>/  — soft-delete (sets deleted_at).
    """

    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return non-deleted services for the current tenant.

        Returns:
            QuerySet of Service instances.
        """
        return Service.objects.all()


# ---------------------------------------------------------------------------
# Check views
# ---------------------------------------------------------------------------


class CheckListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/services/<service_pk>/checks/  — list checks for a service.
    POST /api/v1/services/<service_pk>/checks/  — create a check.

    Supports filtering by is_enabled via ?enabled=true|false.
    """

    serializer_class = CheckSerializer
    permission_classes = [IsAuthenticated]

    def _get_service(self) -> Service:
        """
        Resolve the parent service from the URL kwarg, scoped to this tenant.

        Returns:
            The parent Service instance.

        Raises:
            Http404: If the service does not exist or belongs to another tenant.
        """
        return get_object_or_404(Service, pk=self.kwargs["service_pk"])

    def get_queryset(self):
        """
        Return checks for the parent service.

        Returns:
            QuerySet of Check instances.
        """
        service = self._get_service()
        qs = service.checks.all().order_by("name")
        enabled = self.request.query_params.get("enabled")
        if enabled is not None:
            qs = qs.filter(is_enabled=enabled.lower() == "true")
        return qs

    def perform_create(self, serializer: CheckSerializer) -> None:
        """
        Inject the parent service before saving.

        Args:
            serializer: The validated CheckSerializer instance.
        """
        service = self._get_service()
        serializer.save(service=service)
        logger.info(
            "monitoring: check created service=%s check=%s",
            service.name,
            serializer.instance.name,
        )


class CheckDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/services/<service_pk>/checks/<pk>/  — retrieve a check.
    PUT    /api/v1/services/<service_pk>/checks/<pk>/  — full update.
    PATCH  /api/v1/services/<service_pk>/checks/<pk>/  — partial update.
    DELETE /api/v1/services/<service_pk>/checks/<pk>/  — soft-delete.
    """

    serializer_class = CheckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return checks scoped to the parent service.

        Returns:
            QuerySet of Check instances.
        """
        return Check.objects.filter(service_id=self.kwargs["service_pk"])


# ---------------------------------------------------------------------------
# CheckResult views
# ---------------------------------------------------------------------------


class CheckResultListView(generics.ListAPIView):
    """
    GET /api/v1/checks/<check_pk>/results/

    Returns the most recent 100 results for a check (append-only history).
    Supports ?limit=N to override (max 500).
    """

    serializer_class = CheckResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return recent CheckResult records for the given check.

        Returns:
            QuerySet of CheckResult instances, newest first.
        """
        check = get_object_or_404(Check, pk=self.kwargs["check_pk"])
        try:
            limit = min(int(self.request.query_params.get("limit", 100)), 500)
        except (TypeError, ValueError):
            limit = 100
        return CheckResult.objects.filter(health_check=check).order_by("-created_at")[:limit]


# ---------------------------------------------------------------------------
# Incident views
# ---------------------------------------------------------------------------


class IncidentListView(generics.ListAPIView):
    """
    GET /api/v1/incidents/

    Lists incidents for the current tenant.
    Supports filtering:
        ?state=open|acknowledged|resolved
        ?severity=low|medium|high|critical
        ?service_id=<uuid>
    """

    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return incidents with optional filters.

        Returns:
            QuerySet of Incident instances, newest first.
        """
        qs = Incident.objects.select_related("service", "health_check").order_by("-opened_at")

        state = self.request.query_params.get("state")
        if state:
            qs = qs.filter(state=state)

        severity = self.request.query_params.get("severity")
        if severity:
            qs = qs.filter(severity=severity)

        service_id = self.request.query_params.get("service_id")
        if service_id:
            qs = qs.filter(service_id=service_id)

        return qs


class AcknowledgeIncidentView(APIView):
    """
    POST /api/v1/incidents/<pk>/acknowledge/

    Transitions an OPEN incident to ACKNOWLEDGED.
    Body (optional): {"ack_note": "Looking into it"}

    Returns 400 if the incident is not in OPEN state.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: str) -> Response:
        """
        Acknowledge an open incident.

        Args:
            request: The DRF request object.
            pk: The incident UUID from the URL.

        Returns:
            200 with the updated incident, or 400 if transition is invalid.
        """
        incident = get_object_or_404(Incident, pk=pk)

        if incident.state != IncidentState.OPEN:
            return Response(
                {"detail": f"Cannot acknowledge an incident in state '{incident.state}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AcknowledgeIncidentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        incident.state = IncidentState.ACKNOWLEDGED
        incident.acknowledged_at = timezone.now()
        incident.ack_note = serializer.validated_data["ack_note"]
        incident.save(update_fields=["state", "acknowledged_at", "ack_note", "updated_at"])

        logger.info(
            "monitoring: incident acknowledged incident=%s by user=%s",
            incident.id,
            request.user,
        )

        return Response(IncidentSerializer(incident).data, status=status.HTTP_200_OK)


class ResolveIncidentView(APIView):
    """
    POST /api/v1/incidents/<pk>/resolve/

    Manually resolves an OPEN or ACKNOWLEDGED incident.
    Returns 400 if already resolved.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: str) -> Response:
        """
        Manually resolve an incident.

        Args:
            request: The DRF request object.
            pk: The incident UUID from the URL.

        Returns:
            200 with the updated incident, or 400 if already resolved.
        """
        incident = get_object_or_404(Incident, pk=pk)

        if incident.state == IncidentState.RESOLVED:
            return Response(
                {"detail": "Incident is already resolved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        incident.state = IncidentState.RESOLVED
        incident.resolved_at = timezone.now()
        incident.save(update_fields=["state", "resolved_at", "updated_at"])

        logger.info(
            "monitoring: incident manually resolved incident=%s by user=%s",
            incident.id,
            request.user,
        )

        return Response(IncidentSerializer(incident).data, status=status.HTTP_200_OK)
