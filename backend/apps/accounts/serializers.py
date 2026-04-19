"""Serializers for the accounts app."""

from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import APIKey, Membership, Organization, User


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
