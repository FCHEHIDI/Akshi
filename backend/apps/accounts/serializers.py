"""Serializers for the accounts app."""

from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import APIKey, Membership, Organization, User, Invitation, InvitationStatus


class LoginSerializer(serializers.Serializer):
    """Request body for POST /api/v1/auth/login/."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)


class RefreshSerializer(serializers.Serializer):
    """Request body for POST /api/v1/auth/refresh/."""

    refresh_token = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    """Request body for POST /api/v1/auth/logout/."""

    refresh_token = serializers.CharField()
    all_devices = serializers.BooleanField(default=False)


class TokenPairSerializer(serializers.Serializer):
    """Response body for login / refresh endpoints."""

    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)


class UserSerializer(serializers.ModelSerializer):
    """Read-only representation of a User."""

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "created_at"]
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer):
    """Membership with nested user info."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "user", "role", "is_active", "created_at"]
        read_only_fields = fields


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organisation read endpoints."""

    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "plan", "is_active", "created_at"]
        read_only_fields = fields


class APIKeyCreateSerializer(serializers.Serializer):
    """Request body for creating a new API key."""

    name = serializers.CharField(max_length=255)
    permissions = serializers.ListField(
        child=serializers.CharField(), default=list, required=False
    )
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class APIKeySerializer(serializers.ModelSerializer):
    """Safe representation of an APIKey (never exposes key_hash)."""

    class Meta:
        model = APIKey
        fields = [
            "id",
            "name",
            "prefix",
            "permissions",
            "last_used_at",
            "expires_at",
            "is_active",
            "created_at",
        ]
        read_only_fields = fields


class APIKeyCreatedSerializer(APIKeySerializer):
    """Extended representation returned ONCE at creation — includes the raw key."""

    raw_key = serializers.CharField(read_only=True)

    class Meta(APIKeySerializer.Meta):
        fields = APIKeySerializer.Meta.fields + ["raw_key"]


# ---------------------------------------------------------------------------
# Team serializers
# ---------------------------------------------------------------------------

class MemberListSerializer(serializers.ModelSerializer):
    """Flat representation of a Membership for the team members list."""

    id = serializers.UUIDField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    # Map backend role "member" → frontend role "operator"
    role = serializers.SerializerMethodField()
    joined_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "email", "full_name", "role", "joined_at"]

    def get_role(self, obj: Membership) -> str:
        """Map backend role names to frontend role names."""
        return "operator" if obj.role == "member" else obj.role


class InvitationSerializer(serializers.ModelSerializer):
    """Read-only representation of an Invitation for the team invitations list."""

    invited_by_email = serializers.SerializerMethodField()
    # Map "member" → "operator" for frontend consistency.
    role = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = [
            "id",
            "token",
            "email",
            "role",
            "status",
            "invited_by_email",
            "created_at",
            "expires_at",
        ]

    def get_invited_by_email(self, obj: Invitation) -> str | None:
        """Return the inviter's email or None if the user was deleted."""
        return obj.invited_by.email if obj.invited_by_id else None

    def get_role(self, obj: Invitation) -> str:
        """Map backend role names to frontend role names."""
        return "operator" if obj.role == "member" else obj.role


class InviteCreateSerializer(serializers.Serializer):
    """Request body for POST /v1/team/invitations/."""

    email = serializers.EmailField()
    # Frontend sends "operator"; we map back to "member" before persisting.
    role = serializers.ChoiceField(choices=["admin", "operator", "viewer"])

    def validate_role(self, value: str) -> str:
        """Normalise frontend "operator" → backend "member"."""
        return "member" if value == "operator" else value


# ---------------------------------------------------------------------------
# Invitation peek / accept serializers
# ---------------------------------------------------------------------------

class InvitationPeekSerializer(serializers.Serializer):
    """Response schema for GET /v1/invitations/:token/peek."""

    email = serializers.EmailField(read_only=True)
    org_name = serializers.CharField(read_only=True)
    # Map "member" → "operator" in the view.
    role = serializers.CharField(read_only=True)


class InvitationAcceptSerializer(serializers.Serializer):
    """Request body for POST /v1/invitations/accept."""

    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(min_length=1, max_length=150)


# ---------------------------------------------------------------------------
# Onboarding serializer
# ---------------------------------------------------------------------------

class OnboardingCreateSerializer(serializers.Serializer):
    """Request body for POST /v1/onboarding/create-org."""

    org_name = serializers.CharField(min_length=2, max_length=100)
    slug = serializers.RegexField(
        regex=r"^[a-z0-9][a-z0-9\-]{1,48}[a-z0-9]$",
        error_messages={
            "invalid": (
                "Slug must be 3–50 lowercase letters, digits, or hyphens and "
                "cannot start or end with a hyphen."
            )
        },
    )
    full_name = serializers.CharField(min_length=1, max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
