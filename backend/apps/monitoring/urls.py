"""HTTP URL patterns for the monitoring app — Phase 1, Bloc 4 + Bloc 6."""

from django.urls import path

from apps.monitoring.views import (
    AcknowledgeIncidentView,
    AllChecksListView,
    CheckDetailView,
    CheckListCreateView,
    CheckResultListView,
    IncidentListView,
    NotificationChannelDetailView,
    NotificationChannelListCreateView,
    RecentResultsListView,
    ResolveIncidentView,
    ServiceDetailView,
    ServiceListCreateView,
)

urlpatterns = [
    # Services
    path("services", ServiceListCreateView.as_view(), name="service-list"),
    path("services/<uuid:pk>", ServiceDetailView.as_view(), name="service-detail"),
    # Checks (nested under service)
    path("services/<uuid:service_pk>/checks", CheckListCreateView.as_view(), name="check-list"),
    path("services/<uuid:service_pk>/checks/<uuid:pk>", CheckDetailView.as_view(), name="check-detail"),
    # Flat checks list (all services)
    path("checks", AllChecksListView.as_view(), name="check-flat-list"),
    # Check results (history)
    path("checks/<uuid:check_pk>/results", CheckResultListView.as_view(), name="checkresult-list"),
    # Flat recent results (all checks)
    path("results/recent", RecentResultsListView.as_view(), name="results-recent"),
    # Incidents
    path("incidents", IncidentListView.as_view(), name="incident-list"),
    path("incidents/<uuid:pk>/acknowledge", AcknowledgeIncidentView.as_view(), name="incident-acknowledge"),
    path("incidents/<uuid:pk>/resolve", ResolveIncidentView.as_view(), name="incident-resolve"),
    # Notification channels
    path("notification-channels", NotificationChannelListCreateView.as_view(), name="notificationchannel-list"),
    path("notification-channels/<uuid:pk>", NotificationChannelDetailView.as_view(), name="notificationchannel-detail"),
]
