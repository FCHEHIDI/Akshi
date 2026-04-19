"""API URL patterns for accounts resources."""

from django.urls import path

from apps.accounts.views import APIKeyListCreateView, APIKeyRevokeView, MeView

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("api-keys/", APIKeyListCreateView.as_view(), name="api-key-list-create"),
    path("api-keys/<uuid:pk>/", APIKeyRevokeView.as_view(), name="api-key-revoke"),
]
