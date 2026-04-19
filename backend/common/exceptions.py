"""
Global DRF exception handler for SentinelOps.

Normalises all error responses to the standard envelope:
    {
        "error": "<human-readable message>",
        "code":  "<machine-readable code>",
        "details": { ... }
    }
"""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


# Maps HTTP status codes to machine-readable error codes.
_STATUS_TO_CODE: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "validation_error",
    status.HTTP_401_UNAUTHORIZED: "unauthorized",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_429_TOO_MANY_REQUESTS: "throttled",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "server_error",
}


def _extract_message(data: Any) -> str:
    """
    Pull the top-level human-readable message from DRF error data.

    Args:
        data: The raw ``response.data`` dict or list from DRF.

    Returns:
        A single string suitable for the ``"error"`` field.
    """
    if isinstance(data, dict):
        # DRF validation errors have field-level lists; grab the first message.
        for value in data.values():
            if isinstance(value, list) and value:
                item = value[0]
                return str(item) if not hasattr(item, "detail") else str(item.detail)
            if isinstance(value, str):
                return value
        return "An error occurred."
    if isinstance(data, list) and data:
        return str(data[0])
    return str(data)


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """
    Custom DRF exception handler that wraps all errors in a standard envelope.

    Args:
        exc: The exception raised by the view.
        context: DRF context dict containing ``view`` and ``request``.

    Returns:
        A DRF Response with a normalised error body, or None if DRF cannot
        handle the exception (which causes Django to return a 500).
    """
    response = exception_handler(exc, context)
    if response is None:
        return None

    raw_data = response.data
    code = _STATUS_TO_CODE.get(response.status_code, "error")

    # For validation errors keep the field-level detail in ``details``.
    details: dict | list = {}
    if isinstance(raw_data, dict):
        details = {
            k: v for k, v in raw_data.items()
            if k not in ("detail",)
        }

    response.data = {
        "error": _extract_message(raw_data),
        "code": code,
        "details": details,
    }
    return response
