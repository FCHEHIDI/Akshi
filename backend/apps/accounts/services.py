"""
Business logic for the accounts app.

All views delegate to these service functions.  Services contain the only place
where database writes and Redis operations are allowed in the accounts domain.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Any

from django.conf import settings
from django.utils import timezone
from jose import jwt

from apps.accounts.models import APIKey, Membership, Organization, User
from apps.accounts.redis_client import get_token_redis

logger = logging.getLogger(__name__)



def _make_access_token(user: User) -> str:
    """
    Mint a short-lived JWT access token for a user.

    Args:
        user: The authenticated User instance.

    Returns:
        Signed JWT string valid for ``JWT_ACCESS_TOKEN_LIFETIME``.
    """
    lifetime: timedelta = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
    now = datetime.now(tz=dt_timezone.utc)
    payload = {
        "token_type": "access",
        "user_id": str(user.id),
        "email": user.email,
        "iat": now,
        "exp": now + lifetime,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def _make_refresh_token(user: User) -> tuple[str, str]:
    """
    Mint a refresh token and persist its JTI in Redis.

    The token is stored under the key ``rt:{user_id}:{jti}`` with a TTL equal
    to the configured refresh token lifetime.

    Args:
        user: The authenticated User instance.

    Returns:
        Tuple of ``(raw_token, jti)``.
    """
    lifetime: timedelta = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    now = datetime.now(tz=dt_timezone.utc)
    jti = str(uuid.uuid4())
    payload = {
        "token_type": "refresh",
        "user_id": str(user.id),
        "iat": now,
        "exp": now + lifetime,
        "jti": jti,
    }
    raw_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    r = get_token_redis()
    redis_key = f"rt:{user.id}:{jti}"
    r.setex(redis_key, int(lifetime.total_seconds()), "1")

    return raw_token, jti


class AuthService:
    """
    Handles login, token refresh, and logout operations.

    All methods are static so they can be called without an instance from views
    and Celery tasks alike.
    """

    @staticmethod
    def login(email: str, password: str) -> dict[str, str]:
        """
        Authenticate a user by email and password.

        Args:
            email: The user's email address.
            password: The plain-text password to verify.

        Returns:
            Dict with ``access_token`` and ``refresh_token`` keys.

        Raises:
            ValueError: If credentials are invalid or the account is inactive.
        """
        try:
            user = User.objects.get(email=email.lower().strip())
        except User.DoesNotExist:
            raise ValueError("Invalid credentials.")

        if not user.is_active:
            raise ValueError("Account is disabled.")

        if not user.check_password(password):
            raise ValueError("Invalid credentials.")

        access_token = _make_access_token(user)
        refresh_token, _ = _make_refresh_token(user)

        logger.info("User %s logged in.", user.id)
        return {"access_token": access_token, "refresh_token": refresh_token}

    @staticmethod
    def refresh(refresh_token_raw: str) -> dict[str, str]:
        """
        Issue a new access token (and rotated refresh token) from a valid refresh token.

        Implements token rotation with a 5-second grace period to handle race conditions
        (e.g. two tabs refreshing simultaneously).

        Args:
            refresh_token_raw: The raw refresh token JWT string.

        Returns:
            Dict with fresh ``access_token`` and ``refresh_token``.

        Raises:
            ValueError: If the token is invalid, expired, or already revoked.
        """
        from jose import ExpiredSignatureError, JWTError, jwt as jose_jwt  # noqa: PLC0415

        try:
            payload = jose_jwt.decode(
                refresh_token_raw,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={"leeway": 30},
            )
        except ExpiredSignatureError:
            raise ValueError("Refresh token has expired.")
        except JWTError:
            raise ValueError("Invalid refresh token.")

        if payload.get("token_type") != "refresh":
            raise ValueError("Token type mismatch.")

        user_id = payload["user_id"]
        jti = payload["jti"]
        r = get_token_redis()
        redis_key = f"rt:{user_id}:{jti}"

        if not r.exists(redis_key):
            # Token already used — potential reuse attack: revoke ALL sessions.
            logger.warning(
                "Refresh token reuse detected for user_id=%s jti=%s — revoking all sessions.",
                user_id,
                jti,
            )
            for key in r.scan_iter(f"rt:{user_id}:*"):
                r.delete(key)
            raise ValueError("Refresh token already used. All sessions have been revoked.")

        # Revoke the old token
        r.delete(redis_key)

        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise ValueError("User not found or inactive.")

        access_token = _make_access_token(user)
        new_refresh_token, _ = _make_refresh_token(user)

        return {"access_token": access_token, "refresh_token": new_refresh_token}

    @staticmethod
    def logout(refresh_token_raw: str, all_devices: bool = False) -> None:
        """
        Revoke a refresh token (single device) or all refresh tokens for the user.

        Args:
            refresh_token_raw: The raw refresh token JWT string.
            all_devices: If True, revoke every session for the user.

        Raises:
            ValueError: If the token cannot be decoded.
        """
        from jose import JWTError, jwt as jose_jwt  # noqa: PLC0415

        try:
            payload = jose_jwt.decode(
                refresh_token_raw,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_exp": False, "leeway": 30},
            )
        except JWTError:
            raise ValueError("Invalid refresh token.")

        user_id = payload.get("user_id")
        jti = payload.get("jti")
        r = get_token_redis()

        if all_devices:
            for key in r.scan_iter(f"rt:{user_id}:*"):
                r.delete(key)
            logger.info("Revoked all sessions for user_id=%s.", user_id)
        else:
            r.delete(f"rt:{user_id}:{jti}")
            logger.info("Revoked session jti=%s for user_id=%s.", jti, user_id)


class APIKeyService:
    """Service for creating and revoking API keys."""

    @staticmethod
    def create_key(
        organization: Organization,
        name: str,
        actor: User,
        permissions: list[str] | None = None,
        expires_at: datetime | None = None,
    ) -> tuple[str, APIKey]:
        """
        Create a new API key for an organisation.

        Args:
            organization: The tenant to scope this key to.
            name: Human-readable label (e.g. ``"GitHub Actions"``).
            actor: The user creating the key (stored as ``created_by``).
            permissions: Optional list of permission strings to grant.
            expires_at: Optional expiry datetime.

        Returns:
            Tuple of ``(raw_key, APIKey)``.  ``raw_key`` is shown once and
            must be copied by the user — it is **never** stored.
        """
        raw_key, api_key = APIKey.create(
            organization=organization,
            name=name,
            created_by=actor,
            permissions=permissions or [],
            expires_at=expires_at,
        )
        logger.info(
            "API key created: id=%s org=%s by=%s",
            api_key.id,
            organization.slug,
            actor.id,
        )
        return raw_key, api_key

    @staticmethod
    def revoke_key(api_key: APIKey, actor: User) -> None:
        """
        Revoke an API key by marking it inactive.

        Args:
            api_key: The APIKey instance to revoke.
            actor: The user performing the revocation (for audit purposes).

        Raises:
            ValueError: If the key is already inactive.
        """
        if not api_key.is_active:
            raise ValueError("API key is already revoked.")
        APIKey.objects.filter(pk=api_key.pk).update(is_active=False)
        logger.info(
            "API key revoked: id=%s org=%s by=%s",
            api_key.id,
            api_key.organization.slug,
            actor.id,
        )
