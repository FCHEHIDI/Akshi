"""
Incident state machine — Phase 1, Bloc 3.

process_result() is called by run_check after every CheckResult is saved.
It decides whether to open, keep open or resolve an Incident.

State transitions
-----------------
::

    [no incident]
        + consecutive failures >= retry_count  →  open OPEN incident

    [OPEN or ACKNOWLEDGED]
        + result is OK                         →  transition to RESOLVED
        + result is FAIL / TIMEOUT / UNKNOWN   →  stay (no-op)

    [RESOLVED]
        + consecutive failures >= retry_count  →  re-open as new OPEN incident
        + result is OK                         →  no-op

Severity mapping
----------------
Derived from the consecutive failure count relative to the retry threshold:

* 1× threshold  → MEDIUM
* 2× threshold  → HIGH
* 3× threshold  → CRITICAL
* < threshold   → LOW (only used internally, incident is not opened yet)
"""

from __future__ import annotations

import logging

from django.utils import timezone

logger = logging.getLogger(__name__)

# Statuses that count as a failure for the state machine.
_FAILING_STATUSES = {"fail", "timeout", "unknown"}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def process_result(check: object, result: object) -> None:
    """
    Update incident state based on the latest CheckResult.

    Called by ``run_check`` immediately after each ``CheckResult`` is saved.
    Imports are deferred to avoid circular imports at module load time.

    Args:
        check: The ``Check`` instance that was just executed.
        result: The ``CheckResult`` instance that was just saved.
    """
    from apps.monitoring.models import (  # noqa: PLC0415
        Check,
        CheckResult,
        Incident,
        IncidentState,
    )

    # Re-cast to typed variables for IDE/mypy benefit.
    check: Check = check  # type: ignore[no-redef]
    result: CheckResult = result  # type: ignore[no-redef]

    is_failing = result.status in _FAILING_STATUSES

    if is_failing:
        _handle_failure(check, result, Incident, IncidentState)
    else:
        _handle_recovery(check, Incident, IncidentState)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _consecutive_failures(check: object, retry_count: int) -> int:
    """
    Return the number of consecutive FAIL/TIMEOUT/UNKNOWN results for *check*.

    Reads at most ``retry_count * 3`` recent results to bound the query.

    Args:
        check: The ``Check`` instance.
        retry_count: Check's configured retry threshold (used to cap the query).

    Returns:
        Number of trailing failures (0 if the most recent result is OK).
    """
    from apps.monitoring.models import CheckResult  # noqa: PLC0415

    window = max(retry_count * 3, 10)
    recent = list(
        CheckResult.objects.filter(health_check=check)
        .order_by("-created_at")
        .values_list("status", flat=True)[:window]
    )

    count = 0
    for status in recent:
        if status in _FAILING_STATUSES:
            count += 1
        else:
            break
    return count


def _severity_from_failures(consecutive: int, threshold: int) -> str:
    """
    Map consecutive failure count to an incident severity string.

    Args:
        consecutive: Number of consecutive failures observed.
        threshold: Check's ``retry_count`` value.

    Returns:
        One of ``"medium"``, ``"high"``, ``"critical"``.
    """
    if consecutive >= threshold * 3:
        return "critical"
    if consecutive >= threshold * 2:
        return "high"
    return "medium"


def _handle_failure(
    check: object,
    result: object,
    Incident: type,
    IncidentState: type,
) -> None:
    """
    Evaluate whether a new incident should be opened (or re-opened).

    Args:
        check: The failing ``Check``.
        result: The latest failing ``CheckResult``.
        Incident: The ``Incident`` model class (passed to avoid repeated import).
        IncidentState: The ``IncidentState`` choices enum.
    """
    consecutive = _consecutive_failures(check, check.retry_count)

    if consecutive < check.retry_count:
        # Not yet at threshold — log and wait.
        logger.debug(
            "incidents: below threshold check=%s consecutive=%d/%d",
            check.name,
            consecutive,
            check.retry_count,
        )
        return

    severity = _severity_from_failures(consecutive, check.retry_count)

    # Check for an existing open/acknowledged incident.
    active_incident = (
        Incident.objects.filter(
            health_check=check,
            state__in=[IncidentState.OPEN, IncidentState.ACKNOWLEDGED],
        )
        .order_by("-opened_at")
        .first()
    )

    if active_incident:
        # Already tracking — update severity if it escalated.
        if active_incident.severity != severity:
            active_incident.severity = severity
            active_incident.save(update_fields=["severity", "updated_at"])
            logger.info(
                "incidents: severity escalated check=%s incident=%s severity=%s",
                check.name,
                active_incident.id,
                severity,
            )
        return

    # No active incident — open a new one.
    incident = Incident.objects.create(
        service=check.service,
        health_check=check,
        state=IncidentState.OPEN,
        severity=severity,
    )
    logger.warning(
        "incidents: opened check=%s incident=%s consecutive=%d severity=%s",
        check.name,
        incident.id,
        consecutive,
        severity,
    )


def _handle_recovery(
    check: object,
    Incident: type,
    IncidentState: type,
) -> None:
    """
    Resolve any open/acknowledged incident when the check passes.

    Args:
        check: The ``Check`` that just returned OK.
        Incident: The ``Incident`` model class.
        IncidentState: The ``IncidentState`` choices enum.
    """
    active_incident = (
        Incident.objects.filter(
            health_check=check,
            state__in=[IncidentState.OPEN, IncidentState.ACKNOWLEDGED],
        )
        .order_by("-opened_at")
        .first()
    )

    if not active_incident:
        return

    active_incident.state = IncidentState.RESOLVED
    active_incident.resolved_at = timezone.now()
    active_incident.save(update_fields=["state", "resolved_at", "updated_at"])

    logger.info(
        "incidents: resolved check=%s incident=%s",
        check.name,
        active_incident.id,
    )
