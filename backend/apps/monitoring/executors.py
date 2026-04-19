"""
Check executors for Phase 1 — HTTP, TCP, and Ping.

Each executor is a plain async function that accepts a ``config`` dict,
runs the probe, and returns a structured ``ExecutorResult`` dataclass.
The callers (Celery tasks) run them via ``asyncio.run()``.

Config shapes
-------------
HTTP::

    {
        "url": "https://api.example.com/health",
        "method": "GET",                      # optional, default GET
        "expected_status": 200,               # optional, default 200
        "timeout_seconds": 10,                # optional, default 10
        "headers": {"X-Api-Key": "..."},      # optional
        "body": "...",                         # optional, for POST/PUT
    }

TCP::

    {
        "host": "db.example.com",
        "port": 5432,
        "timeout_seconds": 5,                 # optional, default 5
    }

Ping::

    {
        "host": "10.0.0.1",
        "count": 3,                           # optional, default 3
        "timeout_seconds": 5,                 # optional, default 5
    }
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

import httpx
import icmplib

from apps.monitoring.models import CheckStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ExecutorResult:
    """
    Normalised outcome of a single check execution.

    Attributes:
        status: Final check status (ok / fail / timeout / unknown).
        duration_ms: Wall-clock duration of the probe in milliseconds.
        response_code: HTTP status code for HTTP checks, ``None`` otherwise.
        error_message: Human-readable error description; empty string on success.
        raw: Optional extra data from the probe (e.g. ICMP packet loss %).
    """

    status: CheckStatus
    duration_ms: int
    response_code: int | None = None
    error_message: str = ""
    raw: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# HTTP executor
# ---------------------------------------------------------------------------


async def run_http_check(config: dict) -> ExecutorResult:
    """
    Perform an HTTP(S) health check.

    Args:
        config: Check configuration dict (see module docstring for shape).

    Returns:
        ExecutorResult with status, duration, response_code and error_message.

    Raises:
        No exceptions — all errors are captured into the returned result.
    """
    url: str = config["url"]
    method: str = config.get("method", "GET").upper()
    expected_status: int = int(config.get("expected_status", 200))
    timeout_seconds: float = float(config.get("timeout_seconds", 10))
    headers: dict = config.get("headers") or {}
    body: str | None = config.get("body")

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(timeout_seconds),
        ) as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                content=body.encode() if body else None,
            )
        duration_ms = int((time.monotonic() - start) * 1000)

        if response.status_code == expected_status:
            return ExecutorResult(
                status=CheckStatus.OK,
                duration_ms=duration_ms,
                response_code=response.status_code,
            )

        return ExecutorResult(
            status=CheckStatus.FAIL,
            duration_ms=duration_ms,
            response_code=response.status_code,
            error_message=(
                f"Expected HTTP {expected_status}, got {response.status_code}"
            ),
        )

    except httpx.TimeoutException as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.debug("HTTP check timeout: url=%s error=%s", url, exc)
        return ExecutorResult(
            status=CheckStatus.TIMEOUT,
            duration_ms=duration_ms,
            error_message=f"Request timed out after {timeout_seconds}s",
        )

    except httpx.RequestError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.debug("HTTP check request error: url=%s error=%s", url, exc)
        return ExecutorResult(
            status=CheckStatus.FAIL,
            duration_ms=duration_ms,
            error_message=f"Request error: {exc}",
        )

    except Exception as exc:  # noqa: BLE001
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning("HTTP check unexpected error: url=%s error=%s", url, exc, exc_info=True)
        return ExecutorResult(
            status=CheckStatus.UNKNOWN,
            duration_ms=duration_ms,
            error_message=f"Unexpected error: {exc}",
        )


# ---------------------------------------------------------------------------
# TCP executor
# ---------------------------------------------------------------------------


async def run_tcp_check(config: dict) -> ExecutorResult:
    """
    Open a TCP connection to ``host:port`` and close it immediately.

    Args:
        config: Check configuration dict (see module docstring for shape).

    Returns:
        ExecutorResult with status, duration and error_message.

    Raises:
        No exceptions — all errors are captured into the returned result.
    """
    host: str = config["host"]
    port: int = int(config["port"])
    timeout_seconds: float = float(config.get("timeout_seconds", 5))

    start = time.monotonic()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout_seconds,
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        writer.close()
        await writer.wait_closed()
        return ExecutorResult(
            status=CheckStatus.OK,
            duration_ms=duration_ms,
        )

    except asyncio.TimeoutError:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.debug("TCP check timeout: host=%s port=%s", host, port)
        return ExecutorResult(
            status=CheckStatus.TIMEOUT,
            duration_ms=duration_ms,
            error_message=f"Connection timed out after {timeout_seconds}s",
        )

    except OSError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.debug("TCP check OS error: host=%s port=%s error=%s", host, port, exc)
        return ExecutorResult(
            status=CheckStatus.FAIL,
            duration_ms=duration_ms,
            error_message=f"Connection refused or unreachable: {exc}",
        )

    except Exception as exc:  # noqa: BLE001
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning(
            "TCP check unexpected error: host=%s port=%s error=%s", host, port, exc, exc_info=True
        )
        return ExecutorResult(
            status=CheckStatus.UNKNOWN,
            duration_ms=duration_ms,
            error_message=f"Unexpected error: {exc}",
        )


# ---------------------------------------------------------------------------
# Ping (ICMP) executor
# ---------------------------------------------------------------------------


async def run_ping_check(config: dict) -> ExecutorResult:
    """
    Send ICMP echo requests using icmplib.

    ``icmplib.async_ping`` requires root/CAP_NET_RAW on Linux.
    On environments without that privilege the result will be UNKNOWN.

    Args:
        config: Check configuration dict (see module docstring for shape).

    Returns:
        ExecutorResult with status, duration, error_message and raw packet stats.

    Raises:
        No exceptions — all errors are captured into the returned result.
    """
    host: str = config["host"]
    count: int = int(config.get("count", 3))
    timeout_seconds: float = float(config.get("timeout_seconds", 5))

    start = time.monotonic()
    try:
        host_result = await icmplib.async_ping(
            address=host,
            count=count,
            timeout=timeout_seconds,
            privileged=False,  # use unprivileged UDP sockets where available
        )
        duration_ms = int((time.monotonic() - start) * 1000)

        raw = {
            "packets_sent": host_result.packets_sent,
            "packets_received": host_result.packets_received,
            "packet_loss": host_result.packet_loss,
            "avg_rtt": host_result.avg_rtt,
            "min_rtt": host_result.min_rtt,
            "max_rtt": host_result.max_rtt,
        }

        if host_result.is_alive:
            return ExecutorResult(
                status=CheckStatus.OK,
                duration_ms=duration_ms,
                raw=raw,
            )

        return ExecutorResult(
            status=CheckStatus.FAIL,
            duration_ms=duration_ms,
            error_message=(
                f"Host unreachable — "
                f"{host_result.packets_received}/{host_result.packets_sent} packets received"
            ),
            raw=raw,
        )

    except icmplib.NameLookupError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.debug("Ping check DNS error: host=%s error=%s", host, exc)
        return ExecutorResult(
            status=CheckStatus.FAIL,
            duration_ms=duration_ms,
            error_message=f"DNS resolution failed: {exc}",
        )

    except icmplib.SocketPermissionError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning(
            "Ping check requires elevated privileges: host=%s error=%s", host, exc
        )
        return ExecutorResult(
            status=CheckStatus.UNKNOWN,
            duration_ms=duration_ms,
            error_message=f"Insufficient privileges for ICMP: {exc}",
        )

    except Exception as exc:  # noqa: BLE001
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning(
            "Ping check unexpected error: host=%s error=%s", host, exc, exc_info=True
        )
        return ExecutorResult(
            status=CheckStatus.UNKNOWN,
            duration_ms=duration_ms,
            error_message=f"Unexpected error: {exc}",
        )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_EXECUTOR_MAP = {
    "http": run_http_check,
    "tcp": run_tcp_check,
    "ping": run_ping_check,
}


async def run_executor(check_type: str, config: dict) -> ExecutorResult:
    """
    Dispatch to the right executor by ``check_type``.

    Args:
        check_type: One of ``"http"``, ``"tcp"``, ``"ping"``.
        config: The Check.config dict.

    Returns:
        ExecutorResult from the appropriate executor.

    Raises:
        ValueError: If ``check_type`` is not supported.
    """
    executor = _EXECUTOR_MAP.get(check_type)
    if executor is None:
        raise ValueError(
            f"Unsupported check_type '{check_type}'. "
            f"Supported: {list(_EXECUTOR_MAP.keys())}"
        )
    return await executor(config)
