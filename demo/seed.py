#!/usr/bin/env python3
"""
SentinelOps demo seed script.

Creates a JWT user for the `acme` tenant, then registers the 3 mock
services and their health checks via the SentinelOps REST API.

Usage:
    python seed.py

Requirements:
    pip install requests

Environment variables (optional, override defaults):
    SENTINEL_URL   — base URL of SentinelOps (default: http://localhost:8000)
    TENANT_HOST    — Host header for tenant routing (default: acme.localhost)
    ADMIN_EMAIL    — seed user email   (default: admin@acme.localhost)
    ADMIN_PASSWORD — seed user password (default: SentinelDemo!1)
"""

import logging
import os
import sys

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("seed")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL: str = os.getenv("SENTINEL_URL", "http://localhost:8000").rstrip("/")
TENANT_HOST: str = os.getenv("TENANT_HOST", "acme.localhost")
ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@acme.localhost")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "SentinelDemo!1")

HEADERS_BASE: dict = {"Host": TENANT_HOST, "Content-Type": "application/json"}

# ---------------------------------------------------------------------------
# Services to register
# (name, check_type, target, port, expected_status, description)
# ---------------------------------------------------------------------------
DEMO_SERVICES = [
    {
        "name": "FastAPI Demo App",
        "description": "Stable mock service — /health always 200",
        "checks": [
            {
                "name": "HTTP health",
                "check_type": "http",
                "target": "http://demo-fastapi-app:8001/health",
                "expected_status_code": 200,
                "interval_seconds": 30,
                "timeout_seconds": 5,
            },
        ],
    },
    {
        "name": "Flaky Service",
        "description": "50% failure rate — tests incident detection",
        "checks": [
            {
                "name": "HTTP health (flaky)",
                "check_type": "http",
                "target": "http://demo-flaky-service:8002/health",
                "expected_status_code": 200,
                "interval_seconds": 30,
                "timeout_seconds": 5,
            },
        ],
    },
    {
        "name": "TCP Echo Server",
        "description": "Bare TCP echo — tests TCP executor",
        "checks": [
            {
                "name": "TCP connect",
                "check_type": "tcp",
                "target": "demo-grpc-echo",
                "port": 50051,
                "interval_seconds": 60,
                "timeout_seconds": 5,
            },
        ],
    },
]


def api(
    method: str,
    path: str,
    *,
    headers: dict,
    json: dict | None = None,
) -> requests.Response:
    """
    Make an API request to SentinelOps.

    Args:
        method: HTTP method (GET, POST, etc.).
        path: URL path starting with /.
        headers: Request headers including Host and Authorization.
        json: Optional JSON body.

    Returns:
        Response object.

    Raises:
        requests.HTTPError: On 4xx/5xx responses.
    """
    resp = requests.request(method, f"{BASE_URL}{path}", headers=headers, json=json, timeout=10)
    resp.raise_for_status()
    return resp


def get_or_create_user(headers: dict) -> str:
    """
    Create the admin user via Django shell (must be run via manage.py),
    then obtain a JWT token via the login endpoint.

    Args:
        headers: Base headers without auth token.

    Returns:
        JWT access token string.

    Raises:
        requests.HTTPError: On unexpected API errors.
        SystemExit: If login fails (user not created yet).
    """
    logger.info("Obtaining JWT token for %s …", ADMIN_EMAIL)
    resp = requests.post(
        f"{BASE_URL}/api/v1/auth/login/",
        headers=headers,
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=10,
    )
    if resp.status_code == 401:
        logger.error(
            "Login failed — create the user first:\n"
            "  docker compose --env-file .env.docker exec web python manage.py shell -c \""
            "from apps.accounts.models import User; "
            "User.objects.create_superuser('%s', '%s', full_name='Demo Admin')\"",
            ADMIN_EMAIL,
            ADMIN_PASSWORD,
        )
        sys.exit(1)
    resp.raise_for_status()
    token: str = resp.json()["access_token"]
    logger.info("Token obtained OK")
    return token


def seed_services(auth_headers: dict) -> None:
    """
    Register all demo services and their checks.

    Args:
        auth_headers: Headers with Authorization bearer token.
    """
    for svc_def in DEMO_SERVICES:
        checks = svc_def.pop("checks")

        # Create service
        logger.info("Creating service: %s", svc_def["name"])
        try:
            svc_resp = api("POST", "/api/v1/services/", headers=auth_headers, json=svc_def)
            svc_id: int = svc_resp.json()["id"]
            logger.info("  → service id=%d", svc_id)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 400:
                logger.warning("  → service may already exist: %s", exc.response.text)
                continue
            raise

        # Create checks for this service
        for check in checks:
            check["service"] = svc_id
            logger.info("  Creating check: %s", check["name"])
            try:
                check_resp = api("POST", "/api/v1/checks/", headers=auth_headers, json=check)
                logger.info("  → check id=%d", check_resp.json()["id"])
            except requests.HTTPError as exc:
                logger.error("  → failed to create check: %s", exc.response.text if exc.response else exc)


def main() -> None:
    """Entry point — run full seed sequence."""
    logger.info("=== SentinelOps Demo Seed ===")
    logger.info("Target: %s  Tenant: %s", BASE_URL, TENANT_HOST)

    headers = dict(HEADERS_BASE)

    try:
        token = get_or_create_user(headers)
    except requests.HTTPError as exc:
        logger.error("Auth failed: %s", exc)
        sys.exit(1)

    auth_headers = {**headers, "Authorization": f"Bearer {token}"}
    seed_services(auth_headers)

    logger.info("=== Seed complete ===")
    logger.info("You can now watch SentinelOps run checks with:")
    logger.info("  docker compose --env-file .env.docker logs -f worker")


if __name__ == "__main__":
    main()
