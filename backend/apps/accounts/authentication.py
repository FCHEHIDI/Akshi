"""
Custom DRF authentication backends for SentinelOps.

Two backends are registered in REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]:

1. JWTAuthentication  — validates Bearer tokens from the Authorization header.
2. APIKeyAuthentication — validates X-API-Key header (SHA-256 lookup).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone as dt_timezone

import redis
from django.conf import settings
from django.utils import timezone
from jose import ExpiredSignatureError, JWTError, jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from apps.accounts.models import APIKey, User
from apps.accounts.redis_client import get_token_redis

logger = logging.getLogger(__name__)


class JWTAuthentication(BaseAuthentication):
    """
    Authenticates requests using a JWT Bearer token in the Authorization header.

    Expected header format::

        Authorization: Bearer <access_token>

    The token is verified with HS256 and the ``SECRET_KEY``.  The ``user_id``
    claim is used to load the User from the database.

    Raises:
        AuthenticationFailed: If the token is missing, expired, or invalid.
    """

    def authenticate(self, request: Request) -> tuple[User, None] | None:
        """
        Extract and validate the JWT from the Authorization header.

        Args:
            request: The incoming DRF request.

        Returns:
            ``(user, None)`` if authentication succeeds, or ``None`` if no
            Authorization header is present (allows other backends to try).

        Raises:
            AuthenticationFailed: If the token is present but invalid.
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return None

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],  # Explicit whitelist — never trust header alg
                options={"leeway": 30},
            )
        except ExpiredSignatureError:
            raise AuthenticationFailed("Access token has expired.")
        except JWTError as exc:
            logger.debug("JWT decode failed: %s", exc)
            raise AuthenticationFailed("Invalid access token.")

        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationFailed("Token missing user_id claim.")

        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found or inactive.")

        return user, None


class APIKeyAuthentication(BaseAuthentication):
    """
    Authenticates requests using an API key in the X-API-Key header.

    Expected header format::

        X-API-Key: sk_live_<random>

    The raw key is hashed with SHA-256 and looked up in the ``APIKey`` table.
    The associated Organization is attached to ``request.tenant`` so the rest
    of the request can be tenant-scoped normally.

    ``last_used_at`` is updated via ``filter().update()`` to avoid a read-modify-write
    round-trip and prevent blocking the response.

    Raises:
        AuthenticationFailed: If the key is not found, inactive, or expired.
    """

    def authenticate(self, request: Request) -> tuple[User, APIKey] | None:
        """
        Extract and validate the API key from the X-API-Key header.

        Args:
            request: The incoming DRF request.

        Returns:
            ``(user, api_key)`` where ``user`` is the key's creator (or a synthetic
            system user proxy), or ``None`` if no X-API-Key header is present.

        Raises:
            AuthenticationFailed: If the key is present but invalid/revoked/expired.
        """
        raw_key = request.headers.get("X-API-Key", "").strip()
        if not raw_key:
            return None

        key_hash = APIKey.hash_raw_key(raw_key)

        try:
            api_key = APIKey.objects.select_related(
                "organization", "created_by"
            ).get(key_hash=key_hash, is_active=True)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API key.")

        # Check expiry
        if api_key.expires_at and api_key.expires_at < timezone.now():
            raise AuthenticationFailed("API key has expired.")

        # Non-blocking update of last_used_at
        APIKey.objects.filter(pk=api_key.pk).update(last_used_at=timezone.now())

        # Attach tenant so TenantMembershipMiddleware can resolve membership
        request.tenant = api_key.organization  # type: ignore[attr-defined]

        # Use the key creator as the request user; fall back to an anonymous-like sentinel
        user = api_key.created_by
        if user is None or not user.is_active:
            raise AuthenticationFailed("API key creator account is inactive.")

        # Store key on request for downstream permission checks
        request.api_key = api_key  # type: ignore[attr-defined]
        return user, api_key
