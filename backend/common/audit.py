"""
@audit_action decorator for automatic AuditEvent creation on service calls.
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


def audit_action(action: str, resource_type: str) -> Callable:
    """
    Decorator for service methods that should be recorded in the audit log.

    After the wrapped function executes successfully, creates an ``AuditEvent``
    record.  The decorator expects the wrapped function to accept an ``actor``
    keyword argument (a User instance) and to return the affected resource.

    Args:
        action: Dot-notation event name, e.g. ``"check.created"``.
        resource_type: Model name for the affected resource, e.g. ``"check"``.

    Returns:
        The decorated function with audit logging side-effect.

    Example::

        @audit_action("check.created", "check")
        def create_check(self, organization, actor, **data):
            check = Check.objects.create(**data)
            return check
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            # Import here to avoid circular imports at module load time.
            from apps.compliance.models import AuditEvent  # noqa: PLC0415

            actor = kwargs.get("actor")
            if actor is None:
                logger.warning(
                    "audit_action(%s): 'actor' keyword argument not found, AuditEvent will have no actor. "
                    "Decorated function: %s",
                    action,
                    func.__qualname__,
                )
            try:
                AuditEvent.objects.create(
                    actor_id=getattr(actor, "id", None),
                    actor_email=getattr(actor, "email", ""),
                    action=action,
                    resource_type=resource_type,
                    resource_id=getattr(result, "id", None),
                )
            except Exception:
                # Never let audit failures break the primary operation.
                logger.exception(
                    "Failed to write AuditEvent for action=%s resource_type=%s",
                    action,
                    resource_type,
                )
            return result

        return wrapper
    return decorator
