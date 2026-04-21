"""
Management command: seed_dev_data

Idempotent command that bootstraps a local development environment with:
  - One Organization (schema: "acme", domain: "localhost")
  - One admin User (admin@sentinelops.local / dev1234!)
  - 6 Services with checks, ~60 recent CheckResults, and 2 open Incidents

Usage:
    python manage.py seed_dev_data
    python manage.py seed_dev_data --flush   # wipe & recreate monitoring data
"""

from __future__ import annotations

import logging
import random
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Seed data definition
# ---------------------------------------------------------------------------

SERVICES_DEF = [
    {
        "name": "API Gateway",
        "description": "Public-facing REST gateway — routes traffic to internal micro-services.",
        "tags": ["api", "production"],
        "sla_target": "99.900",
        "checks": [
            {
                "name": "HTTP health",
                "check_type": "http",
                "config": {"url": "https://api.example.com/health", "expected_status": 200},
                "interval_seconds": 60,
                "healthy": True,
            },
            {
                "name": "TCP port 443",
                "check_type": "tcp",
                "config": {"host": "api.example.com", "port": 443},
                "interval_seconds": 120,
                "healthy": True,
            },
        ],
    },
    {
        "name": "Auth Service",
        "description": "JWT issuance, refresh, and revocation micro-service.",
        "tags": ["auth", "production"],
        "sla_target": "99.950",
        "checks": [
            {
                "name": "HTTP /ping",
                "check_type": "http",
                "config": {"url": "https://auth.example.com/ping", "expected_status": 200},
                "interval_seconds": 60,
                "healthy": True,
            },
        ],
    },
    {
        "name": "PostgreSQL Primary",
        "description": "Primary Postgres 16 instance — all transactional writes land here.",
        "tags": ["database", "production"],
        "sla_target": "99.990",
        "checks": [
            {
                "name": "TCP port 5432",
                "check_type": "tcp",
                "config": {"host": "db-primary.internal", "port": 5432},
                "interval_seconds": 30,
                "healthy": False,  # will trigger incident
            },
        ],
    },
    {
        "name": "Redis Cache",
        "description": "Session store and hot-cache layer (Redis 7).",
        "tags": ["cache", "production"],
        "sla_target": "99.500",
        "checks": [
            {
                "name": "TCP port 6379",
                "check_type": "tcp",
                "config": {"host": "redis.internal", "port": 6379},
                "interval_seconds": 60,
                "healthy": True,
            },
        ],
    },
    {
        "name": "CDN Edge",
        "description": "CloudFront distribution serving static assets globally.",
        "tags": ["cdn", "production"],
        "sla_target": "99.000",
        "checks": [
            {
                "name": "HTTP origin check",
                "check_type": "http",
                "config": {"url": "https://cdn.example.com/health.txt", "expected_status": 200},
                "interval_seconds": 300,
                "healthy": True,
            },
        ],
    },
    {
        "name": "Celery Workers",
        "description": "Async task queue — handles emails, check dispatch, and report generation.",
        "tags": ["workers", "background"],
        "sla_target": "99.000",
        "checks": [
            {
                "name": "Heartbeat cron",
                "check_type": "cron",
                "config": {"name": "celery-heartbeat", "grace_period_seconds": 120},
                "interval_seconds": 60,
                "healthy": False,  # will trigger incident
            },
        ],
    },
]


class Command(BaseCommand):
    """Bootstrap a local dev environment with realistic seed data."""

    help = "Seed the local database with demo organisations, users, and monitoring data."

    def add_arguments(self, parser) -> None:  # type: ignore[override]
        """
        Register command-line options.

        Args:
            parser: argparse ArgumentParser instance.
        """
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing monitoring data in the acme tenant before re-seeding.",
        )

    def handle(self, *args, **options) -> None:  # type: ignore[override]
        """
        Execute the seed command.

        Args:
            args: Positional arguments (unused).
            options: Parsed command-line options dict.
        """
        try:
            self._run(flush=options["flush"])
        except Exception as exc:
            raise CommandError(f"Seed failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run(self, *, flush: bool) -> None:
        """
        Main seed logic.

        Args:
            flush: If True, deletes all monitoring data in the acme tenant before seeding.
        """
        # Import here so Django apps are fully loaded before model access.
        from django_tenants.utils import schema_context  # noqa: PLC0415

        from apps.accounts.models import Domain, Membership, Organization, User  # noqa: PLC0415

        # -----------------------------------------------------------------
        # 1. Public schema — Organisation + Domain + User + Membership
        # -----------------------------------------------------------------
        self.stdout.write("  Creating organisation…")
        org, org_created = Organization.objects.get_or_create(
            schema_name="acme",
            defaults={
                "name": "Acme Corp",
                "slug": "acme",
                "plan": "pro",
                "is_active": True,
            },
        )
        if org_created:
            self.stdout.write(self.style.SUCCESS("  ✓ Organisation 'acme' created (schema provisioned)"))
        else:
            self.stdout.write("  ✓ Organisation 'acme' already exists")

        Domain.objects.get_or_create(
            domain="localhost",
            defaults={"tenant": org, "is_primary": True},
        )
        self.stdout.write("  ✓ Domain localhost → acme")

        user, user_created = User.objects.get_or_create(
            email="admin@sentinelops.local",
            defaults={
                "full_name": "Admin User",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        user.set_password("dev1234!")
        user.save(update_fields=["password"])
        if user_created:
            self.stdout.write(self.style.SUCCESS("  ✓ User admin@sentinelops.local created"))
        else:
            self.stdout.write("  ✓ User admin@sentinelops.local already exists (password reset)")

        Membership.objects.get_or_create(
            user=user,
            organization=org,
            defaults={"role": "admin", "is_active": True},
        )
        self.stdout.write("  ✓ Membership admin → acme")

        # -----------------------------------------------------------------
        # 2. Tenant schema — monitoring data
        # -----------------------------------------------------------------
        with schema_context("acme"):
            self._seed_monitoring(flush=flush)

        self.stdout.write(self.style.SUCCESS("\n✅  Seed complete!"))
        self.stdout.write(
            "   Login: admin@sentinelops.local / dev1234!\n"
            "   Host header required: localhost\n"
            "   Backend: http://localhost:8000\n"
            "   Frontend: http://localhost:3001\n"
        )

    def _seed_monitoring(self, *, flush: bool) -> None:
        """
        Seed monitoring data inside the tenant schema context.

        Args:
            flush: If True, deletes all existing monitoring data first.
        """
        from apps.monitoring.models import (  # noqa: PLC0415
            Check,
            CheckResult,
            CheckStatus,
            Incident,
            IncidentState,
            Service,
            Severity,
        )

        if flush:
            self.stdout.write("  Flushing existing monitoring data…")
            Incident.objects.all().delete()
            CheckResult.objects.all().delete()
            Check.objects.all().delete()
            Service.objects.all().delete()
            self.stdout.write("  ✓ Flushed")

        now = timezone.now()
        incident_checks: list[tuple[Service, Check]] = []

        for svc_def in SERVICES_DEF:
            checks_def = svc_def.pop("checks")
            svc, _ = Service.objects.get_or_create(
                name=svc_def["name"],
                defaults={**svc_def, "status": "active"},
            )
            self.stdout.write(f"  Service: {svc.name}")

            for chk_def in checks_def:
                is_healthy: bool = chk_def.pop("healthy")
                chk, _ = Check.objects.get_or_create(
                    service=svc,
                    name=chk_def["name"],
                    defaults={
                        **chk_def,
                        "retry_count": 3,
                        "is_enabled": True,
                        "next_run_at": now + timedelta(seconds=chk_def["interval_seconds"]),
                    },
                )

                # Generate ~10 recent results per check
                self._create_results(chk, is_healthy=is_healthy, now=now)

                if not is_healthy:
                    incident_checks.append((svc, chk))

        # Create open incidents for failing checks (idempotent)
        for svc, chk in incident_checks:
            if not Incident.objects.filter(
                service=svc,
                health_check=chk,
                state=IncidentState.OPEN,
            ).exists():
                Incident.objects.create(
                    service=svc,
                    health_check=chk,
                    state=IncidentState.OPEN,
                    severity=Severity.HIGH,
                    opened_at=now - timedelta(minutes=random.randint(5, 60)),
                )
                self.stdout.write(
                    self.style.WARNING(f"  ⚠  Incident opened: {svc.name} / {chk.name}")
                )

    def _create_results(
        self,
        check: "Check",  # type: ignore[name-defined]
        *,
        is_healthy: bool,
        now,
    ) -> None:
        """
        Create ~10 synthetic CheckResult rows for a given check.

        Args:
            check: The Check instance to attach results to.
            is_healthy: If True, all results will be ``ok``; otherwise mostly ``fail``.
            now: Current timezone-aware datetime used as the base for timestamps.
        """
        from apps.monitoring.models import CheckResult, CheckStatus  # noqa: PLC0415

        # Only create results that don't already exist (avoid re-seeding duplicates)
        if CheckResult.objects.filter(health_check=check).exists():
            return

        results = []
        for i in range(10):
            ts = now - timedelta(minutes=i * check.interval_seconds // 60 + random.randint(0, 2))

            if is_healthy:
                status = CheckStatus.OK
                duration = random.randint(40, 220)
                code = 200 if check.check_type == "http" else None
                error = ""
            else:
                # Fail all results for unhealthy checks (realistic for a real outage)
                status = CheckStatus.FAIL
                duration = random.randint(5000, 10000)
                code = 503 if check.check_type == "http" else None
                error = "Connection refused" if check.check_type in ("tcp", "ping") else "Service unavailable"

            results.append(
                CheckResult(
                    health_check=check,
                    status=status,
                    duration_ms=duration,
                    response_code=code,
                    error_message=error,
                    checked_via="cloud",
                    created_at=ts,
                )
            )

        CheckResult.objects.bulk_create(results)
