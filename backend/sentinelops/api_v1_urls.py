"""
API v1 root URL router.

Aggregates routers from all Django apps into a single URL namespace.
"""

from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.accounts.urls.auth")),
    path("", include("apps.accounts.urls.api")),
    path("team/", include("apps.accounts.urls.team")),
    path("invitations/", include("apps.accounts.urls.invitations")),
    path("onboarding/", include("apps.accounts.urls.onboarding")),
    path("", include("apps.monitoring.urls")),
]
