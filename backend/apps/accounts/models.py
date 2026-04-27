"""
Models for the accounts app.

All models here live in the PUBLIC PostgreSQL schema (SHARED_APPS).

Models:
    Organization — TenantMixin; one row = one tenant schema.
    Domain       — DomainMixin; maps a hostname to a tenant.
    User         — Custom AbstractBaseUser (email-based, no username).
    Membership   — M2M pivot: User ↔ Organization with a role.
    APIKey       — Machine credentials scoped to an Organization.
    Invitation   — Pending email invitation to join an Organization.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin

from common.models import TimestampedModel


# ---------------------------------------------------------------------------
# Organization & Domain (django-tenants required models)
# ---------------------------------------------------------------------------


class Organization(TenantMixin, TimestampedModel):
    """
    A SentinelOps customer organisation — maps 1:1 to a PostgreSQL schema.

    When an Organization is created, django-tenants automatically provisions
    a new schema named after ``schema_name`` and runs all TENANT_APPS migrations
    inside it.

    Attributes:
        name: Human-readable organisation name.
        slug: URL-safe identifier, used in API paths and channel group names.
        plan: Billing plan identifier (``"free"``, ``"pro"``, ``"enterprise"``).
        is_active: Set to False to disable access without deleting data.
        auto_create_schema: Tells django-tenants to create the schema on save.
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    plan = models.CharField(max_length=50, default="free")
    is_active = models.BooleanField(default=True)

    # django-tenants: automatically creates the PG schema on first save.
    auto_create_schema = True

    class Meta:
        app_label = "accounts"

    def __str__(self) -> str:
        return self.name


class Domain(DomainMixin):
    """
    Maps a hostname to an Organization tenant.

    Example: ``acme.sentinelops.io`` → Organization(slug="acme").
    django-tenants uses this table to route every request to the correct schema.
    """

    class Meta:
        app_label = "accounts"

    def __str__(self) -> str:
        return self.domain


# ---------------------------------------------------------------------------
# Custom User model (email-based, no username)
# ---------------------------------------------------------------------------


class UserManager(BaseUserManager):
    """Manager for the custom email-based User model."""

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ) -> "User":
        """
        Create and return a regular user.

        Args:
            email: The user's email address (used as login identifier).
            password: Plain-text password (will be hashed).
            **extra_fields: Any additional User field values.

        Returns:
            The newly created User instance.

        Raises:
            ValueError: If email is not provided.
        """
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        user: User = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ) -> "User":
        """
        Create and return a superuser with ``is_staff=True`` and ``is_superuser=True``.

        Args:
            email: The superuser's email address.
            password: Plain-text password.
            **extra_fields: Any additional User field values.

        Returns:
            The newly created superuser instance.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that uses email as the unique identifier.

    Replaces Django's default username-based User.  Auth is via JWT;
    the ``password`` field is kept for admin login and initial onboarding.

    Attributes:
        id: UUID primary key.
        email: Unique login identifier.
        full_name: Display name.
        is_active: Allow login.
        is_staff: Allow Django admin access.
        created_at / updated_at: Timestamps (added manually; no TimestampedModel
            because AbstractBaseUser already has its own meta class).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email + password only

    class Meta:
        app_label = "accounts"
        ordering = ["email"]

    def __str__(self) -> str:
        return self.email


# ---------------------------------------------------------------------------
# Membership — links a User to an Organisation with a role
# ---------------------------------------------------------------------------


class RoleChoices(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    VIEWER = "viewer", "Viewer"


class Membership(TimestampedModel):
    """
    Pivot model between User and Organization, carrying the user's RBAC role.

    A user may be a member of multiple organisations with different roles.
    The TenantMembershipMiddleware resolves and attaches this to ``request.membership``
    on every authenticated request.

    Attributes:
        user: The authenticated user.
        organization: The tenant this membership belongs to.
        role: RBAC role (owner / admin / member / viewer).
        is_active: Set to False to suspend access without deleting the record.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.MEMBER,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "accounts"
        unique_together = [("user", "organization")]

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.organization.slug} [{self.role}]"


# ---------------------------------------------------------------------------
# APIKey
# ---------------------------------------------------------------------------


class APIKey(TimestampedModel):
    """
    Machine credential scoped to an Organisation.

    The raw key is **never** stored — only a SHA-256 hex digest is persisted.
    The raw key is returned once at creation time and must be saved by the client.

    Key format: ``sk_live_<32 url-safe random bytes>``

    Usage::

        raw_key, api_key = APIKey.create(organization=org, name="CI/CD", created_by=user)
        # raw_key is shown once; api_key.key_hash is what's stored.

    Attributes:
        organization: The tenant this key belongs to.
        created_by: The user who generated the key (nullable for system keys).
        name: Human-readable label (e.g. ``"GitHub Actions"``).
        key_hash: SHA-256 hex digest of the raw key.
        prefix: First 8 characters shown in the UI for identification.
        permissions: List of permission strings this key grants.
        last_used_at: Updated on every authenticated request (non-blocking).
        expires_at: Optional expiry timestamp; ``None`` = never expires.
        is_active: Revoke a key by setting this to False.
    """

    PREFIX = "sk_live_"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="api_keys"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=255)
    key_hash = models.CharField(max_length=64, unique=True)  # SHA-256 hex = 64 chars
    prefix = models.CharField(max_length=16)
    permissions = models.JSONField(default=list)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "accounts"

    def __str__(self) -> str:
        return f"{self.name} ({self.prefix}…)"

    # ------------------------------------------------------------------
    # Class-level factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        organization: Organization,
        name: str,
        created_by: User | None = None,
        permissions: list[str] | None = None,
        expires_at=None,
    ) -> tuple[str, "APIKey"]:
        """
        Generate a new API key.

        The raw key is returned **once** and must be shown to the user immediately.
        Only the SHA-256 hash is stored in the database.

        Args:
            organization: The tenant this key belongs to.
            name: Human-readable label for the key.
            created_by: User creating the key (optional for system-generated keys).
            permissions: List of permission strings (defaults to empty list).
            expires_at: Optional expiry datetime.

        Returns:
            A tuple of ``(raw_key, APIKey instance)``.
        """
        raw_key = cls.PREFIX + secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        prefix = raw_key[:8]

        api_key = cls.objects.create(
            organization=organization,
            created_by=created_by,
            name=name,
            key_hash=key_hash,
            prefix=prefix,
            permissions=permissions or [],
            expires_at=expires_at,
        )
        return raw_key, api_key

    @staticmethod
    def hash_raw_key(raw_key: str) -> str:
        """
        Return the SHA-256 hex digest for a raw key string.

        Args:
            raw_key: The plain-text key value.

        Returns:
            64-character hexadecimal SHA-256 digest.
        """
        return hashlib.sha256(raw_key.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Invitation
# ---------------------------------------------------------------------------

class InvitationStatus(models.TextChoices):
    """Lifecycle states for an Invitation."""

    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    CANCELLED = "cancelled", "Cancelled"


class Invitation(TimestampedModel):
    """
    A pending (or resolved) invitation to join an Organization via email.

    Token-based: the invitee receives a URL containing ``token``, which is a
    cryptographically random 86-character URL-safe string generated by
    ``secrets.token_urlsafe(64)``.

    Attributes:
        id: UUID primary key.
        organization: The tenant the invitee will join.
        invited_by: The User who created the invitation (nullable in case
            they are later removed from the org).
        email: Target email address.
        role: Role to assign on acceptance. One of admin/member/viewer.
        token: Single-use URL-safe token included in the invite link.
        status: Current lifecycle state.
        expires_at: Expiry datetime (default: 7 days from creation).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invitations",
    )
    email = models.EmailField()
    role = models.CharField(max_length=20, default=RoleChoices.MEMBER)
    token = models.CharField(max_length=86, unique=True)
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )
    expires_at = models.DateTimeField()

    class Meta:
        app_label = "accounts"
        # Only one *pending* invitation per email per org. Accepted/cancelled
        # ones may coexist to preserve audit history.
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "email"],
                condition=models.Q(status="pending"),
                name="unique_pending_invite_per_org_email",
            ),
        ]

    def __str__(self) -> str:
        return f"Invitation({self.email} → {self.organization_id}, {self.status})"

    @property
    def is_valid(self) -> bool:
        """Return True if invitation is pending and not yet expired."""
        from django.utils import timezone  # noqa: PLC0415

        return self.status == InvitationStatus.PENDING and self.expires_at > timezone.now()
