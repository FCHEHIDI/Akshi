"""
Shared DRF permission classes used across all SentinelOps apps.
"""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

# Maps each role name to the set of permissions it grants.
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": {
        "organization:manage",
        "members:manage",
        "monitoring:write",
        "monitoring:read",
        "incidents:acknowledge",
        "workflows:write",
        "audit:read",
        "audit:export",
        "billing:manage",
    },
    "admin": {
        "members:manage",
        "monitoring:write",
        "monitoring:read",
        "incidents:acknowledge",
        "workflows:write",
        "audit:read",
        "audit:export",
    },
    "member": {
        "monitoring:write",
        "monitoring:read",
        "incidents:acknowledge",
        "workflows:write",
    },
    "viewer": {
        "monitoring:read",
    },
}


def make_org_permission(perm: str) -> type[BasePermission]:
    """
    Factory that returns a DRF permission class checking a single RBAC permission.

    ``TenantMembershipMiddleware`` sets ``request.membership`` (a ``Membership``
    instance) before any view runs.  This factory reads that attribute directly —
    no extra DB query needed.

    Args:
        perm: The permission string to verify, e.g. ``"monitoring:write"``.

    Returns:
        A ``BasePermission`` subclass suitable for use in ``permission_classes``.

    Usage::

        permission_classes = [IsAuthenticated, make_org_permission("monitoring:write")]
    """

    class _OrgPermission(BasePermission):
        required_permission: str = perm

        def has_permission(self, request: Request, view: APIView) -> bool:
            membership = getattr(request, "membership", None)

            # TenantMembershipMiddleware runs before DRF authentication, so
            # request.user is still AnonymousUser at middleware time.  Once DRF
            # has authenticated the request (which happens lazily on first access
            # of request.user inside a view), we can resolve the membership here.
            if membership is None and request.user and request.user.is_authenticated:
                tenant = getattr(request, "tenant", None)
                if tenant is not None:
                    from apps.accounts.models import Membership as MembershipModel  # noqa: PLC0415
                    membership = (
                        MembershipModel.objects.filter(
                            user=request.user,
                            organization=tenant,
                            is_active=True,
                        )
                        .select_related("organization")
                        .first()
                    )
                    request.membership = membership  # cache for subsequent checks

            if membership is None:
                return False
            allowed = ROLE_PERMISSIONS.get(membership.role, set())
            return self.required_permission in allowed

    # Readable name for DRF error messages and logs.
    _OrgPermission.__name__ = f"HasOrgPermission_{perm.replace(':', '_')}"
    _OrgPermission.__qualname__ = _OrgPermission.__name__
    return _OrgPermission