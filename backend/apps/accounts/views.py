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
    InvitationAcceptSerializer,
    InvitationPeekSerializer,
    InvitationSerializer,
    LoginSerializer,
    LogoutSerializer,
    MemberListSerializer,
    MembershipSerializer,
    OnboardingCreateSerializer,
    RefreshSerializer,
    TokenPairSerializer,
    InviteCreateSerializer,
)
from apps.accounts.services import APIKeyService, AuthService, InvitationService, OnboardingService
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


# ---------------------------------------------------------------------------
# Team views
# ---------------------------------------------------------------------------

class TeamMemberListView(APIView):
    """
    GET /v1/team/members/

    List all members of the requesting organisation.
    Requires ``members:manage`` permission.
    """

    permission_classes = [IsAuthenticated, make_org_permission("members:manage")]

    def get(self, request: Request) -> Response:
        memberships = (
            request.tenant.memberships  # type: ignore[union-attr]
            .select_related("user")
            .order_by("created_at")
        )
        serializer = MemberListSerializer(memberships, many=True)
        return Response({"members": serializer.data})


class TeamMemberRemoveView(APIView):
    """
    DELETE /v1/team/members/<pk>/

    Remove a member from the organisation.  Cannot remove yourself or the owner.
    Requires ``members:manage`` permission.
    """

    permission_classes = [IsAuthenticated, make_org_permission("members:manage")]

    def delete(self, request: Request, pk: str) -> Response:
        from apps.accounts.models import Membership  # noqa: PLC0415

        try:
            membership = (
                request.tenant.memberships  # type: ignore[union-attr]
                .select_related("user")
                .get(user_id=pk)
            )
        except Membership.DoesNotExist:
            return Response(
                {"error": "Member not found.", "code": "not_found", "details": {}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if str(membership.user_id) == str(request.user.id):
            return Response(
                {"error": "You cannot remove yourself.", "code": "forbidden", "details": {}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if membership.role == "owner":
            return Response(
                {"error": "The owner cannot be removed.", "code": "forbidden", "details": {}},
                status=status.HTTP_403_FORBIDDEN,
            )
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamInvitationListView(APIView):
    """
    GET /v1/team/invitations/

    List all invitations for the requesting organisation.
    Requires ``members:manage`` permission.
    """

    permission_classes = [IsAuthenticated, make_org_permission("members:manage")]

    def get(self, request: Request) -> Response:
        invitations = (
            request.tenant.invitations  # type: ignore[union-attr]
            .select_related("invited_by")
            .order_by("-created_at")
        )
        serializer = InvitationSerializer(invitations, many=True)
        return Response({"invitations": serializer.data})


class TeamInviteCreateView(APIView):
    """
    POST /v1/team/invitations/

    Send a new invitation to join the organisation.
    Requires ``members:manage`` permission.
    """

    permission_classes = [IsAuthenticated, make_org_permission("members:manage")]

    def post(self, request: Request) -> Response:
        serializer = InviteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            invitation = InvitationService.send(
                organization=request.tenant,  # type: ignore[arg-type]
                invited_by=request.user,
                email=data["email"],
                role=data["role"],
            )
        except ValueError as exc:
            return Response(
                {"error": str(exc), "code": "conflict", "details": {}},
                status=status.HTTP_409_CONFLICT,
            )

        out = InvitationSerializer(invitation)
        return Response(out.data, status=status.HTTP_201_CREATED)


class TeamInvitationCancelView(APIView):
    """
    DELETE /v1/team/invitations/<pk>/

    Cancel a pending invitation.
    Requires ``members:manage`` permission.
    """

    permission_classes = [IsAuthenticated, make_org_permission("members:manage")]

    def delete(self, request: Request, pk: str) -> Response:
        try:
            InvitationService.cancel(
                invitation_id=pk,
                organization=request.tenant,  # type: ignore[arg-type]
            )
        except ValueError as exc:
            return Response(
                {"error": str(exc), "code": "not_found", "details": {}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Public invitation views (no auth required)
# ---------------------------------------------------------------------------

class InvitationPeekView(APIView):
    """
    GET /v1/invitations/<token>/peek/

    Return public metadata about an invitation without consuming it.
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request: Request, token: str) -> Response:
        try:
            data = InvitationService.peek(token)
        except ValueError as exc:
            return Response(
                {"error": str(exc), "code": "invalid", "details": {}},
                status=status.HTTP_404_NOT_FOUND,
            )
        # Map backend "member" → frontend "operator"
        data["role"] = "operator" if data["role"] == "member" else data["role"]
        serializer = InvitationPeekSerializer(data)
        return Response(serializer.data)


class InvitationAcceptView(APIView):
    """
    POST /v1/invitations/accept/

    Accept an invitation, create an account if needed, and return a JWT pair.
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request: Request) -> Response:
        serializer = InvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            tokens = InvitationService.accept(
                token=data["token"],
                password=data["password"],
                full_name=data["full_name"],
            )
        except ValueError as exc:
            return Response(
                {"error": str(exc), "code": "invalid", "details": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(tokens, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Onboarding view (no auth required)
# ---------------------------------------------------------------------------

class OnboardingCreateView(APIView):
    """
    POST /v1/onboarding/create-org/

    Bootstrap a brand-new organisation and return the owner's JWT pair.
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request: Request) -> Response:
        serializer = OnboardingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = OnboardingService.create_org(
                org_name=data["org_name"],
                slug=data["slug"],
                full_name=data["full_name"],
                email=data["email"],
                password=data["password"],
            )
        except ValueError as exc:
            return Response(
                {"error": str(exc), "code": "conflict", "details": {}},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(result, status=status.HTTP_201_CREATED)
