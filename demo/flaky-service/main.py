"""
Flaky service — randomly fails ~50% of the time.

Useful for testing SentinelOps incident detection, auto-recovery,
and flapping detection logic.

Endpoints:
    GET /health      → 200 or 503 (random, controlled by FAILURE_RATE env var)
    GET /metrics     → Returns call stats (total, failures, success rate)
    GET /set-rate?r= → Change failure rate at runtime (0.0–1.0)
"""

import logging
import os
import random
import time

from fastapi import FastAPI, Query, Response

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("flaky-service")

app = FastAPI(title="SentinelOps Demo — Flaky Service", version="1.0.0")

# Runtime state
_failure_rate: float = float(os.getenv("FAILURE_RATE", "0.5"))
_total_calls: int = 0
_failure_calls: int = 0
_start_time: float = time.time()


@app.get("/health")
async def health() -> Response:
    """
    Returns 200 with probability (1 - failure_rate), otherwise 503.

    Simulates an unstable service to test SentinelOps detection logic.
    """
    global _total_calls, _failure_calls
    _total_calls += 1

    if random.random() < _failure_rate:
        _failure_calls += 1
        logger.warning(
            "Flaky health: FAIL (call #%d, failure_rate=%.0f%%)",
            _total_calls,
            _failure_rate * 100,
        )
        return Response(
            content='{"status":"unhealthy","reason":"random failure"}',
            status_code=503,
            media_type="application/json",
        )

    logger.debug("Flaky health: OK (call #%d)", _total_calls)
    return Response(
        content='{"status":"ok"}',
        status_code=200,
        media_type="application/json",
    )


@app.get("/metrics")
async def metrics() -> dict:
    """Cumulative call statistics."""
    success = _total_calls - _failure_calls
    rate = (success / _total_calls * 100) if _total_calls else 0.0
    return {
        "total_calls": _total_calls,
        "failures": _failure_calls,
        "successes": success,
        "success_rate_pct": round(rate, 1),
        "configured_failure_rate_pct": round(_failure_rate * 100, 1),
        "uptime_s": round(time.time() - _start_time, 1),
    }


@app.get("/set-rate")
async def set_rate(r: float = Query(..., ge=0.0, le=1.0)) -> dict:
    """Change failure rate at runtime. r=0.0 → always up; r=1.0 → always down."""
    global _failure_rate
    _failure_rate = r
    logger.info("Failure rate set to %.0f%%", r * 100)
    return {"failure_rate_pct": round(r * 100, 1)}
