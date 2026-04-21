"""Auth URL patterns for /api/v1/auth/."""

from django.urls import path

from apps.accounts.views import LoginView, LogoutView, RefreshView

urlpatterns = [
    path("login", LoginView.as_view(), name="auth-login"),
    path("refresh", RefreshView.as_view(), name="auth-refresh"),
    path("logout", LogoutView.as_view(), name="auth-logout"),
]
