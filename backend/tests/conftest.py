"""
Pytest fixtures for SentinelOps test suite.

Fixtures:
    org: Creates a public + tenant Organization schema.
    owner_user: User with owner Membership in ``org``.
    auth_client: DRF APIClient with JWT Bearer token for ``owner_user``.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import Membership, Organization, Domain

User = get_user_model()


@pytest.fixture()
def org(db, transactional_db) -> Organization:
    """
    Create and return an Organization tenant with a matching Domain.

    The ``auto_create_schema=True`` flag on the model causes django-tenants
    to create the PostgreSQL schema automatically on save.

    Args:
        db: Django pytest-django database fixture.
        transactional_db: Required by django-tenants schema creation.

    Returns:
        A saved :class:`~apps.accounts.models.Organization` instance.
    """
    org = Organization.objects.create(
        name="Test Corp",
        slug="testcorp",
        schema_name="testcorp",
    )
    Domain.objects.create(domain="testcorp.localhost", tenant=org, is_primary=True)
    return org


@pytest.fixture()
def owner_user(db, org: Organization) -> User:
    """
    Create a User with owner-level Membership in ``org``.

    Args:
        db: Django pytest-django database fixture.
        org: Organization fixture.

    Returns:
        A saved :class:`~apps.accounts.models.User` instance.
    """
    user = User.objects.create_user(
        email="owner@testcorp.example",
        password="Test1234!",
        full_name="Test Owner",
    )
    Membership.objects.create(user=user, organization=org, role="owner", is_active=True)
    return user


@pytest.fixture()
def auth_client(owner_user: User) -> APIClient:
    """
    Return an APIClient authenticated as ``owner_user``.

    Obtains a JWT access token via the login endpoint and sets the
    ``Authorization: Bearer <token>`` header on the client.

    Args:
        owner_user: Owner user fixture.

    Returns:
        An authenticated :class:`~rest_framework.test.APIClient`.
    """
    from apps.accounts.services import AuthService  # noqa: PLC0415

    tokens = AuthService.login(
        email="owner@testcorp.example",
        password="Test1234!",
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    return client
