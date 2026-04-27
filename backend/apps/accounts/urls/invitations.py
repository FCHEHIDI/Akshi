"""URL patterns for /v1/invitations/ endpoints (public — no auth required)."""

from django.urls import path

from apps.accounts.views import InvitationAcceptView, InvitationPeekView

urlpatterns = [
    path("<str:token>/peek", InvitationPeekView.as_view(), name="invitation-peek"),
    path("accept", InvitationAcceptView.as_view(), name="invitation-accept"),
]
