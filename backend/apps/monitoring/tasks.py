"""
Celery tasks for the monitoring app — Phase 1: Check Engine.

Two tasks
---------
dispatch_due_checks
    Beat task (every 30 s).  Iterates every active tenant, finds enabled
    Checks whose ``next_run_at`` is due (or NULL for first run), atomically
    advances ``next_run_at``, then enqueues ``run_check`` for each.
    Updating *before* dispatching prevents double-dispatch when Beat fires
    twice in quick succession.

run_check(check_id, schema_name)
    Worker task.  Sets the tenant schema, loads the Check, calls the right
    executor (HTTP / TCP / Ping), persists a ``CheckResult``, and forwards
    the result to the incident state machine (Bloc 3).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from django.db.models import DurationField, ExpressionWrapper, F, Q
from django.db.models.functions import Now
from django.utils import timezone
from django_tenants.utils import schema_context

from sentinelops.celery import app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Beat task — dispatch due checks across all tenants
# ---------------------------------------------------------------------------


@app.task(
    name="monitoring.dispatch_due_checks",
    queue="checks",
    ignore_result=True,
)
def dispatch_due_checks() -> None:
    """
    Find every due Check across all active tenants and enqueue ``run_check``.

    Runs every 30 seconds via Celery Beat (configured in settings, Bloc 5).
    """
    # Imported inside the function to avoid a circular import at module load.
    from apps.accounts.models import Organization  # noqa: PLC0415

    now = timezone.now()
    active_tenants = Organization.objects.filter(is_active=True).only(
        "schema_name", "slug"
    )

    for tenant in active_tenants:
        with schema_context(tenant.schema_name):
            _dispatch_tenant_checks(tenant.schema_name, now)


def _dispatch_tenant_checks(schema_name: str, now: timezone.datetime) -> None:
    """
    Dispatch due checks within a single tenant schema.

    Args:
        schema_name: PostgreSQL schema name (== Organization.schema_name).
        now: Reference timestamp used for the due-check query.
    """
    from apps.monitoring.models import Check  # noqa: PLC0415

    # Select checks that are enabled and due (next_run_at <= now OR first run).
    due_qs = Check.objects.filter(is_enabled=True).filter(
        Q(next_run_at__isnull=True) | Q(next_run_at__lte=now)
    )
    check_ids: list[str] = list(due_qs.values_list("id", flat=True))

    if not check_ids:
        return

    # Advance next_run_at atomically in one UPDATE *before* dispatching to
    # prevent double-dispatch if Beat fires again before workers finish.
    Check.objects.filter(id__in=check_ids).update(
        next_run_at=Now()
        + ExpressionWrapper(
            F("interval_seconds") * timedelta(seconds=1),
            output_field=DurationField(),
        )
    )

    for check_id in check_ids:
        run_check.delay(str(check_id), schema_name)

    logger.info(
        "dispatch_due_checks: schema=%s dispatched=%d",
        schema_name,
        len(check_ids),
    )


# ---------------------------------------------------------------------------
# Worker task — execute a single check
# ---------------------------------------------------------------------------


@app.task(
    name="monitoring.run_check",
    queue="checks",
    ignore_result=True,
    max_retries=0,  # Executors capture all errors; Celery retries add no value.
)
def run_check(check_id: str, schema_name: str) -> None:
    """
    Execute one Check and persist the result.

    Args:
        check_id: UUID string of the Check to run.
        schema_name: PostgreSQL schema to activate (== Organization.schema_name).
    """
    with schema_context(schema_name):
        _execute_check(check_id, schema_name)


def _execute_check(check_id: str, schema_name: str) -> None:
    """
    Core logic for run_check — separated to keep the task function minimal.

    Args:
        check_id: UUID string of the target Check.
        schema_name: Already-active PostgreSQL schema name (for log messages).
    """
    from apps.monitoring.executors import run_executor  # noqa: PLC0415
    from apps.monitoring.incidents import process_result  # noqa: PLC0415
    from apps.monitoring.models import Check, CheckResult  # noqa: PLC0415

    # --- Load the check ---------------------------------------------------
    try:
        check = Check.objects.select_related("service").get(id=check_id)
    except Check.DoesNotExist:
        logger.warning(
            "run_check: check not found schema=%s check_id=%s — skipping",
            schema_name,
            check_id,
        )
        return

    # Guard: check may have been disabled between dispatch and execution.
    if not check.is_enabled:
        logger.debug(
            "run_check: check disabled, skipping schema=%s check_id=%s",
            schema_name,
            check_id,
        )
        return

    logger.debug(
        "run_check: start schema=%s check=%s type=%s",
        schema_name,
        check.name,
        check.check_type,
    )

    # --- Run the executor -------------------------------------------------
    try:
        result = asyncio.run(run_executor(check.check_type, check.config))
    except ValueError as exc:
        # Unsupported check_type — configuration error, not transient.
        logger.error(
            "run_check: unsupported check_type schema=%s check=%s error=%s",
            schema_name,
            check.name,
            exc,
        )
        return

    # --- Persist the result (append-only) ---------------------------------
    check_result = CheckResult.objects.create(
        health_check=check,
        status=result.status,
        duration_ms=result.duration_ms,
        response_code=result.response_code,
        error_message=result.error_message,
    )

    logger.info(
        "run_check: done schema=%s check=%s status=%s duration=%dms",
        schema_name,
        check.name,
        result.status,
        result.duration_ms,
    )

    # --- Trigger incident state machine (Bloc 3) --------------------------
    process_result(check, check_result)
