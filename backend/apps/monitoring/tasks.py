"""Celery tasks for the monitoring app (stubs — implemented in Phase 1)."""

from sentinelops.celery import app


@app.task(name="monitoring.dispatch_due_checks", queue="checks")
def dispatch_due_checks() -> None:
    """Dispatch all checks whose next_run_at <= now(). Implemented in Phase 1."""
    pass
