"""URL patterns for /v1/team/ endpoints."""

from django.urls import path

from apps.accounts.views import (
    TeamInvitationCancelView,
    TeamInvitationListView,
    TeamInviteCreateView,
    TeamMemberListView,
    TeamMemberRemoveView,
)

urlpatterns = [
    path("members", TeamMemberListView.as_view(), name="team-member-list"),
    path("members/<uuid:pk>", TeamMemberRemoveView.as_view(), name="team-member-remove"),
    path("invitations", TeamInvitationListView.as_view(), name="team-invitation-list"),
    path("invitations/", TeamInviteCreateView.as_view(), name="team-invite-create"),
    path("invitations/<uuid:pk>", TeamInvitationCancelView.as_view(), name="team-invitation-cancel"),
]
