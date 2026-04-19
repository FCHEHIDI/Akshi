"""
TenantMembershipMiddleware — resolves request.membership after TenantMiddleware.
"""

from __future__ import annotations

import logging
from typing import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class TenantMembershipMiddleware:
    """
    Resolves the authenticated user's Membership for the current tenant.

    This middleware must come AFTER ``TenantMainMiddleware`` (which sets
    ``request.tenant``) and ``AuthenticationMiddleware`` (which sets
    ``request.user``).

    After this middleware runs, DRF permission classes can access
    ``request.membership`` to check the user's RBAC role without an extra
    database query in every view.

    Attributes:
        get_response: The next middleware or view callable in the chain.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Attach ``request.membership`` if the user is authenticated and a tenant
        is resolved.

        Args:
            request: The current Django request.

        Returns:
            The response from the next middleware or view.
        """
        request.membership = None  # type: ignore[attr-defined]

        tenant = getattr(request, "tenant", None)
        user = getattr(request, "user", None)

        if tenant is not None and user is not None and user.is_authenticated:
            # Import here to avoid circular import at module load time.
            from apps.accounts.models import Membership  # noqa: PLC0415

            try:
                request.membership = (  # type: ignore[attr-defined]
                    Membership.objects.filter(
                        user=user,
                        organization=tenant,
                        is_active=True,
                    )
                    .select_related("organization")
                    .first()
                )
            except Exception:
                logger.exception(
                    "Failed to resolve membership for user=%s tenant=%s",
                    getattr(user, "id", "?"),
                    getattr(tenant, "slug", "?"),
                )

        return self.get_response(request)
