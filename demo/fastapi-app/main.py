"""
Mock FastAPI service for SentinelOps demo.

Endpoints:
    GET /health      → 200 OK (always healthy)
    GET /crash       → 500 Internal Server Error (simulates a crash)
    GET /slow        → 200 OK after a configurable delay (simulates latency)
    GET /toggle      → Toggles between healthy/unhealthy mode
    GET /status      → Returns current mode info
"""

import asyncio
import logging
import os
import time

from fastapi import FastAPI, Response

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fastapi-app")

app = FastAPI(title="SentinelOps Demo — FastAPI App", version="1.0.0")

# Runtime state
_healthy: bool = True
_slow_delay_ms: int = int(os.getenv("SLOW_DELAY_MS", "3000"))
_start_time: float = time.time()


@app.get("/health")
async def health() -> dict:
    """Health check endpoint — returns 200 when healthy, 503 when toggled off."""
    if not _healthy:
        return Response(
            content='{"status":"unhealthy","reason":"toggled off"}',
            status_code=503,
            media_type="application/json",
        )
    return {"status": "ok", "uptime_s": round(time.time() - _start_time, 1)}


@app.get("/crash")
async def crash() -> Response:
    """Always returns 500 — used to trigger SentinelOps incident creation."""
    logger.error("Simulated crash requested")
    return Response(
        content='{"status":"error","reason":"simulated crash"}',
        status_code=500,
        media_type="application/json",
    )


@app.get("/slow")
async def slow() -> dict:
    """Returns 200 after SLOW_DELAY_MS milliseconds — tests latency-based checks."""
    logger.info("Slow endpoint called, sleeping %dms", _slow_delay_ms)
    await asyncio.sleep(_slow_delay_ms / 1000)
    return {"status": "ok", "delay_ms": _slow_delay_ms}


@app.get("/toggle")
async def toggle() -> dict:
    """Flip healthy/unhealthy state — lets you manually trigger incidents."""
    global _healthy
    _healthy = not _healthy
    state = "healthy" if _healthy else "unhealthy"
    logger.info("Service toggled to: %s", state)
    return {"status": state}


@app.get("/status")
async def status() -> dict:
    """Current runtime status."""
    return {
        "healthy": _healthy,
        "slow_delay_ms": _slow_delay_ms,
        "uptime_s": round(time.time() - _start_time, 1),
    }
