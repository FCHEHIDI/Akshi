"""URL patterns for /v1/onboarding/ endpoints (public — no auth required)."""

from django.urls import path

from apps.accounts.views import OnboardingCreateView

urlpatterns = [
    path("create-org", OnboardingCreateView.as_view(), name="onboarding-create-org"),
]
