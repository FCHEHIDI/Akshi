"""Views for the accounts app — auth endpoints."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import (
    APIKeyCreateSerializer,
    APIKeyCreatedSerializer,
    APIKeySerializer,
    LoginSerializer,
    LogoutSerializer,
    MembershipSerializer,
    RefreshSerializer,
    TokenPairSerializer,
)
from apps.accounts.services import APIKeyService, AuthService
from common.permissions import make_org_permission


class LoginView(APIView):
    """
    POST /api/v1/auth/login/

    Authenticate with email + password and receive a JWT token pair.

    Request body::

        {"email": "user@example.com", "password": "secret"}

    Response (200)::

        {"access_token": "...", "refresh_token": "..."}
    """

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tokens = AuthService.login(**serializer.validated_data)
        except ValueError as exc:
            return Response(
                {"error": str(exc), "code": "invalid_credentials", "details": {}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(TokenPairSerializer(tokens).data)


class RefreshView(APIView):
    """
    POST /api/v1/auth/refresh/

    Exchange a refresh token for a new token pair (rotation applied).

    Request body::

        {"refresh_token": "..."}

    Response (200)::

        {"access_token": "...", "refresh_token": "..."}
    """

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tokens = AuthService.refresh(serializer.validated_data["refresh_token"])
        except ValueError as exc:
            return Response(
                {"error": str(exc), "code": "invalid_token", "details": {}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(TokenPairSerializer(tokens).data)


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/

    Revoke the supplied refresh token (or all sessions when ``all_devices=true``).

    Request body::

        {"refresh_token": "...", "all_devices": false}

    Response (204): No content.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            AuthService.logout(
                serializer.validated_data["refresh_token"],
                all_devices=serializer.validated_data["all_devices"],
            )
        except ValueError as exc:
            return Response(
                {"error": str(exc), "code": "invalid_token", "details": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """
    GET /api/v1/me/

    Return the authenticated user's membership in the current tenant.

    Response (200)::

        {"id": "...", "user": {...}, "role": "owner", ...}
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        membership = getattr(request, "membership", None)
        if membership is None:
            return Response(
                {"error": "Not a member of this organisation.", "code": "forbidden", "details": {}},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(MembershipSerializer(membership).data)


class APIKeyListCreateView(APIView):
    """
    GET  /api/v1/api-keys/  — list API keys for the current tenant.
    POST /api/v1/api-keys/  — create a new API key (raw key returned once).
    """

    permission_classes = [IsAuthenticated, make_org_permission("members:manage")]

    def get(self, request: Request) -> Response:
        keys = request.tenant.api_keys.filter(is_active=True).order_by("-created_at")  # type: ignore[union-attr]
        return Response(APIKeySerializer(keys, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = APIKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_key, api_key = APIKeyService.create_key(
            organization=request.tenant,  # type: ignore[union-attr]
            actor=request.user,
            **serializer.validated_data,
        )

        data = APIKeyCreatedSerializer(api_key).data
        data["raw_key"] = raw_key
        return Response(data, status=status.HTTP_201_CREATED)


class APIKeyRevokeView(APIView):
    """
    DELETE /api/v1/api-keys/<pk>/

    Revoke an API key by its UUID.  Only members with ``members:manage`` may revoke.
    """

    permission_classes = [IsAuthenticated, make_org_permission("members:manage")]

    def delete(self, request: Request, pk: str) -> Response:
        from apps.accounts.models import APIKey  # noqa: PLC0415

        try:
            api_key = request.tenant.api_keys.get(pk=pk)  # type: ignore[union-attr]
        except APIKey.DoesNotExist:
            return Response(
                {"error": "API key not found.", "code": "not_found", "details": {}},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            APIKeyService.revoke_key(api_key, actor=request.user)
        except ValueError as exc:
            return Response(
                {"error": str(exc), "code": "conflict", "details": {}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
