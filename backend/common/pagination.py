"""
Global cursor-based pagination for SentinelOps API responses.
"""

from rest_framework.pagination import CursorPagination


class StandardCursorPagination(CursorPagination):
    """
    Cursor pagination applied to all list endpoints by default.

    Cursor pagination is stable under concurrent writes (no page-drift) and
    does not require a COUNT query, making it efficient on large datasets.

    Attributes:
        page_size: Default number of items per page.
        max_page_size: Maximum items a client may request via ``?page_size=``.
        ordering: Default ordering field (most-recent first).
        cursor_query_param: Query parameter name for the cursor token.
    """

    page_size = 50
    max_page_size = 200
    ordering = "-created_at"
    cursor_query_param = "cursor"
