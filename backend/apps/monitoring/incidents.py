"""
Incident state machine — Phase 1, Bloc 3.

process_result() is called by run_check after every CheckResult is saved.
It decides whether to open, keep open, acknowledge or resolve an Incident.

Implemented in Bloc 3.  The stub is here so that tasks.py can import it
without errors while Bloc 2 is in place.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def process_result(check: object, result: object) -> None:
    """
    Update incident state based on the latest CheckResult.

    Args:
        check: The ``Check`` instance that was just executed.
        result: The ``CheckResult`` instance that was just saved.

    Note:
        Full implementation in Bloc 3 (``apps/monitoring/incidents.py``).
    """
    # Bloc 3 — placeholder
    pass
