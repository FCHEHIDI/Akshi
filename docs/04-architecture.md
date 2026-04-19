# SentinelOps — Architecture Technique Détaillée

**Version:** 1.0  
**Date:** April 18, 2026  
**Status:** Draft  
**Author:** Fares  
**Classification:** Internal — Engineering

> Ce document est le pont entre la spec fonctionnelle (03) et le code.  
> Il définit les conventions, patterns, et décisions d'implémentation qui guident tout le développement.

---

## Table of Contents

1. [Stratégie de couches](#1-stratégie-de-couches)
2. [Structure du dépôt](#2-structure-du-dépôt)
3. [Structure Django détaillée](#3-structure-django-détaillée)
4. [Base Models & Mixins](#4-base-models--mixins)
5. [Multi-tenancy — django-tenants](#5-multi-tenancy--django-tenants)
6. [Authentification & RBAC](#6-authentification--rbac)
7. [Check Engine (Celery)](#7-check-engine-celery)
8. [WebSocket Architecture (Django Channels)](#8-websocket-architecture-django-channels)
9. [Audit Log — Pattern immuable](#9-audit-log--pattern-immuable)
10. [Plugin System](#10-plugin-system)
11. [API Conventions](#11-api-conventions)
12. [Agent On-Prem](#12-agent-on-prem)
13. [Configuration & Settings](#13-configuration--settings)
14. [Tests](#14-tests)
15. [Héritage de SixStars](#15-héritage-de-sixstars)

---

## 1. Stratégie de couches

```
┌──────────────────────────────────────────────────────────────────────┐
│                         COUCHE RÉSEAU                                │
│   Traefik  →  TLS termination, domain-based tenant routing           │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌─────────────────────────┐     ┌──────────────────────────────────────┐
│   COUCHE HTTP (REST)    │     │        COUCHE TEMPS RÉEL             │
│   Django ASGI + DRF     │     │   Django Channels + Daphne (ASGI)    │
│   /api/v1/...           │     │   ws://domain/ws/dashboard/          │
│   Auth: JWT | API Key   │     │   Channel layer: Redis               │
└──────────┬──────────────┘     └────────────────┬─────────────────────┘
           │                                     │
           └──────────────┬──────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       COUCHE SERVICE                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  ┌───────────┐  │
│  │ Check Engine │  │  Workflow    │  │ Audit Log │  │  Plugin   │  │
│  │ (Celery Beat │  │  Orchestr.   │  │  Service  │  │  Manager  │  │
│  │  + Workers)  │  │  (Celery)    │  │           │  │           │  │
│  └──────────────┘  └──────────────┘  └───────────┘  └───────────┘  │
└──────────────────────────────────────────────────────────────────────┘
           │                                     │
           ▼                                     ▼
┌────────────────────────┐     ┌─────────────────────────────────────┐
│      PostgreSQL 16     │     │             Redis 7                 │
│  schema-based tenants  │     │  - Celery broker & result backend   │
│  shared: public schema │     │  - Django cache                     │
│  tenant: per-org schema│     │  - Channel layer (WebSocket groups) │
│                        │     │  - Refresh token store              │
└────────────────────────┘     └─────────────────────────────────────┘
           │
           ▼
┌────────────────────────┐
│      MinIO / S3        │
│  exports CSV/PDF,      │
│  agent certs, assets   │
└────────────────────────┘
```

**Règles fondamentales :**

| Règle | Détail |
|-------|--------|
| **Django est ASGI** | `daphne` sert à la fois REST et WebSocket. Pas de séparation de processus HTTP/WS en dev. |
| **Pas de logique dans les vues** | Les vues DRF délèguent à des **services** (`services.py` par app). Les serializers valident, les services opèrent. |
| **Pas de logique dans les modèles** | Les modèles sont des structures de données + managers. La logique métier est dans les services. |
| **Celery pour tout ce qui est async** | Checks, workflows, notifications, exports PDF — jamais dans le thread HTTP. |
| **Redis = infrastructure centrale** | Broker Celery + Cache Django + Channel Layer + Token store. Un seul Redis, plusieurs DBs (0=cache, 1=celery, 2=channels, 3=tokens). |
| **Audit log = append-only** | Aucun `UPDATE`/`DELETE` sur `AuditEvent`. Override `save()` + `delete()` pour garantir l'immuabilité. |
| **Multi-tenant = schéma PostgreSQL** | Tout tenant routing passe par `TenantMiddleware`. Jamais de filtre manuel `organization=request.org`. |

---

## 2. Structure du dépôt

```
sentinelops/
├── backend/
│   ├── sentinelops/                    # Django project root
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── base.py                 # Settings communs
│   │   │   ├── development.py          # Dev overrides (DEBUG=True, SQLite optionnel)
│   │   │   ├── production.py           # Prod overrides (SECURE_*, ALLOWED_HOSTS)
│   │   │   └── test.py                 # Test overrides (faster hasher, no celery)
│   │   ├── urls.py                     # URL root (inclut tous les routers)
│   │   ├── asgi.py                     # Point d'entrée ASGI (HTTP + WebSocket)
│   │   └── celery.py                   # Instance Celery globale
│   │
│   ├── apps/
│   │   ├── accounts/                   # Auth, RBAC, multi-tenant
│   │   ├── monitoring/                 # Services, checks, incidents
│   │   ├── automations/                # Workflows, triggers, actions
│   │   ├── compliance/                 # Audit logs, policies
│   │   ├── plugins/                    # Plugin system
│   │   └── billing/                    # Plans, subscriptions (V2)
│   │
│   ├── common/                         # Partagé entre toutes les apps
│   │   ├── models.py                   # UUIDModel, TimestampedModel, SoftDeleteModel
│   │   ├── permissions.py              # Classes de permissions DRF réutilisables
│   │   ├── pagination.py               # CursorPagination globale
│   │   ├── exceptions.py               # DRF exception handler custom
│   │   ├── audit.py                    # Décorateur @audit_action
│   │   └── tasks.py                    # Tâches Celery communes (cleanup, etc.)
│   │
│   ├── tests/
│   │   ├── conftest.py                 # Fixtures globales (org, user, tokens)
│   │   ├── factories/                  # factory_boy factories
│   │   └── integration/                # Tests end-to-end API
│   │
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   │
│   ├── manage.py
│   └── Dockerfile
│
├── frontend/                           # Next.js 14 (App Router)
│   ├── app/
│   ├── components/
│   ├── lib/
│   │   ├── api.ts                      # TanStack Query hooks
│   │   └── websocket.ts                # WebSocket client
│   ├── hooks/
│   └── package.json
│
├── agent/                              # On-prem agent (Python)
│   ├── sentinelops_agent/
│   │   ├── collectors/                 # http.py, tcp.py, ping.py, cron.py
│   │   ├── executors/                  # script.py
│   │   ├── transport/                  # client.py (mTLS HTTPS)
│   │   └── config.py                   # YAML loader
│   ├── main.py
│   └── sentinelops-agent.yml.example
│
├── infra/
│   ├── docker-compose.yml              # Dev + on-prem
│   ├── docker-compose.prod.yml         # SaaS prod
│   └── traefik/
│       ├── traefik.yml
│       └── dynamic.yml
│
├── docs/
│   ├── 01-vision-concept.md
│   ├── 02-project-charter.md
│   ├── 03-requirements-specification.md
│   └── 04-architecture.md              # CE FICHIER
│
└── .github/
    └── workflows/
        ├── ci.yml                      # lint + test + build
        └── deploy.yml                  # push to GHCR + deploy
```

---

## 3. Structure Django détaillée

### 3.1 Anatomie d'une app

Chaque app Django suit la même structure interne :

```
apps/<nom>/
├── __init__.py
├── apps.py                  # AppConfig avec ready() pour signal registration
├── models.py                # Modèles Django uniquement (pas de logique)
├── managers.py              # QuerySet / Manager custom
├── services.py              # Logique métier (fonctions pures, appelées par vues + tâches)
├── serializers.py           # DRF serializers (validation + représentation)
├── views.py                 # DRF ViewSets (orchestration uniquement)
├── urls.py                  # Router DRF local
├── permissions.py           # Permission classes spécifiques à l'app
├── tasks.py                 # Tâches Celery de l'app
├── signals.py               # Django signals (enregistrés dans apps.py ready())
├── consumers.py             # Django Channels WebSocket consumers (si applicable)
├── admin.py                 # Django admin
├── migrations/
└── tests/
    ├── test_models.py
    ├── test_services.py
    ├── test_views.py
    └── test_tasks.py
```

### 3.2 Règle : séparation View / Service

```python
# ✅ CORRECT — la vue orchestre, le service opère
class CheckViewSet(viewsets.ModelViewSet):
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        check = CheckService.create_check(
            organization=request.tenant,
            actor=request.user,
            **serializer.validated_data,
        )
        return Response(CheckSerializer(check).data, status=201)

# ❌ INTERDIT — logique métier dans la vue
class CheckViewSet(viewsets.ModelViewSet):
    def create(self, request, *args, **kwargs):
        check = Check.objects.create(...)  # Non
        if check.type == "http":           # Non
            ...
```

---

## 4. Base Models & Mixins

Définis dans `common/models.py`, hérités par tous les modèles métier.

```python
import uuid
from django.db import models


class UUIDModel(models.Model):
    """Remplace l'auto-increment integer par un UUID v4 stable et non-devinable."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(UUIDModel):
    """Ajoute created_at et updated_at automatiques."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class SoftDeleteModel(TimestampedModel):
    """
    Soft delete : les objets ne sont jamais vraiment supprimés.
    deleted_at=None → actif. deleted_at≠None → supprimé.
    Le manager par défaut exclut les objets supprimés.
    """
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()      # exclut deleted_at__isnull=False
    all_objects = models.Manager()     # inclut tout

    def delete(self, *args, **kwargs):
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    class Meta:
        abstract = True


class TenantScopedModel(TimestampedModel):
    """
    Modèle appartenant à un tenant (organisation).
    Utilisé dans les apps tenant-aware (monitoring, automations, compliance, plugins).
    Pas de FK explicite vers Organization — le schéma PostgreSQL fournit l'isolation.
    """
    class Meta:
        abstract = True
```

### 4.1 Quand utiliser quoi

| Modèle base | Utilisé par |
|-------------|-------------|
| `UUIDModel` | Modèles publics sans timestamps (ex: `AuditEvent` a ses propres timestamps) |
| `TimestampedModel` | La majorité des modèles métier |
| `SoftDeleteModel` | `Service`, `Check`, `Workflow` — des choses qu'on "archive" sans perdre l'historique |
| `TenantScopedModel` | Tout ce qui vit dans le schéma tenant (≠ schéma public) |

---

## 5. Multi-tenancy — django-tenants

### 5.1 Schéma PostgreSQL

`django-tenants` maintient deux niveaux de schémas :

```
PostgreSQL
├── public                    (schéma partagé)
│   ├── accounts_organization
│   ├── accounts_user         (utilisateurs globaux)
│   ├── accounts_membership
│   └── django_migrations
│
├── acme                      (schéma du tenant "ACME Corp")
│   ├── monitoring_service
│   ├── monitoring_check
│   ├── monitoring_incident
│   ├── automations_workflow
│   ├── compliance_auditevent
│   └── ...
│
└── globex                    (schéma du tenant "Globex Inc")
    ├── monitoring_service
    └── ...
```

### 5.2 Modèles partagés vs. tenant-only

```python
# settings/base.py
SHARED_APPS = [
    "django_tenants",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "apps.accounts",         # Organization, User, Membership vivent dans public
]

TENANT_APPS = [
    "django.contrib.admin",  # admin par tenant
    "apps.monitoring",
    "apps.automations",
    "apps.compliance",
    "apps.plugins",
]

TENANT_MODEL = "accounts.Organization"
TENANT_DOMAIN_MODEL = "accounts.Domain"
```

### 5.3 Modèles accounts (schéma public)

```python
# apps/accounts/models.py
from django_tenants.models import TenantMixin, DomainMixin
from common.models import TimestampedModel


class Organization(TenantMixin, TimestampedModel):
    """Un tenant = une organisation cliente."""
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)           # utilisé dans les URLs API
    plan = models.CharField(max_length=50, default="free")
    is_active = models.BooleanField(default=True)

    # django-tenants obligatoire
    auto_create_schema = True

    class Meta:
        app_label = "accounts"


class Domain(DomainMixin):
    """Associe un hostname à un tenant (acme.sentinelops.io → org acme)."""
    pass
```

### 5.4 Routing

```python
# sentinelops/asgi.py / urls.py
# django-tenants injecte automatiquement le tenant dans request.tenant
# via TenantMiddleware — basé sur request.get_host()

# Dans les vues, on accède au tenant via :
request.tenant   # → Organisation instance
connection.schema_name   # → "acme"
```

### 5.5 Migrations

```bash
# Créer une migration pour une shared app
python manage.py makemigrations accounts

# Créer une migration pour une tenant app
python manage.py makemigrations monitoring

# Appliquer aux shared apps (schéma public)
python manage.py migrate_schemas --shared

# Appliquer à tous les tenants
python manage.py migrate_schemas --tenant
```

---

## 6. Authentification & RBAC

### 6.1 Flux d'authentification

```
Client
  │
  ├─ POST /api/v1/auth/login/  {email, password}
  │         │
  │         └─ Retourne: { access_token (15min), refresh_token (7j) }
  │                       refresh_token stocké en Redis (key: rt:{user_id}:{jti})
  │
  ├─ Requêtes authentifiées:
  │    Authorization: Bearer <access_token>
  │    OU
  │    X-API-Key: sk_live_xxx
  │
  ├─ POST /api/v1/auth/refresh/  {refresh_token}
  │         │
  │         └─ Vérifie Redis (révocation possible)
  │            Rotation: ancien token invalidé, nouveau émis
  │
  └─ POST /api/v1/auth/logout/
            │
            └─ Supprime le refresh_token de Redis (révocation immédiate)
```

### 6.2 API Keys

```python
# apps/accounts/models.py
class APIKey(TimestampedModel):
    """
    Clé d'API scoped à une organisation.
    Jamais stockée en clair — seul le hash SHA-256 est persisté.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    key_hash = models.CharField(max_length=64, unique=True)  # SHA-256
    prefix = models.CharField(max_length=8)                  # sk_live_ (pour affichage)
    permissions = models.JSONField(default=list)             # ["monitoring:read", ...]
    last_used_at = models.DateTimeField(null=True)
    expires_at = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)

# Lors de la création :
# raw_key = "sk_live_" + secrets.token_urlsafe(32)
# key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
# → raw_key affiché UNE FOIS à l'utilisateur, jamais stocké
```

### 6.3 RBAC — Matrice des permissions

| Permission | Owner | Admin | Member | Viewer |
|-----------|-------|-------|--------|--------|
| `organization:manage` | ✅ | ❌ | ❌ | ❌ |
| `members:manage` | ✅ | ✅ | ❌ | ❌ |
| `monitoring:write` | ✅ | ✅ | ✅ | ❌ |
| `monitoring:read` | ✅ | ✅ | ✅ | ✅ |
| `incidents:acknowledge` | ✅ | ✅ | ✅ | ❌ |
| `workflows:write` | ✅ | ✅ | ✅ | ❌ |
| `audit:read` | ✅ | optimize✅ | ❌ | ❌ |
| `audit:export` | ✅ | ✅ | ❌ | ❌ |
| `billing:manage` | ✅ | ❌ | ❌ | ❌ |

```python
# common/permissions.py
from rest_framework.permissions import BasePermission


class HasOrgPermission(BasePermission):
    """
    Permission DRF générique basée sur la matrice RBAC.
    Usage: permission_classes = [IsAuthenticated, HasOrgPermission("monitoring:write")]
    """
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def has_permission(self, request, view) -> bool:
        membership = getattr(request, "membership", None)
        if not membership:
            return False
        allowed = ROLE_PERMISSIONS[membership.role]
        return self.required_permission in allowed
```

### 6.4 Middleware de tenant + membership

```python
# apps/accounts/middleware.py
class TenantMembershipMiddleware:
    """
    Après TenantMiddleware (qui résout request.tenant),
    ce middleware résout request.membership pour l'utilisateur courant.
    Nécessaire pour les checks de permission RBAC.
    """
    def __call__(self, request):
        if hasattr(request, "tenant") and request.user.is_authenticated:
            request.membership = Membership.objects.filter(
                user=request.user,
                organization=request.tenant,
            ).select_related("role").first()
        return self.get_response(request)
```

---

## 7. Check Engine (Celery)

### 7.1 Architecture Celery

```
Celery Beat (scheduler)
    │
    ├─ Toutes les 30s : dispatch_due_checks()
    │        │
    │        └─ Récupère les checks dont next_run_at <= now()
    │           Pour chaque check : send_task("monitoring.run_check", check_id)
    │
Celery Workers (pool)
    │
    ├─ run_http_check(check_id)
    ├─ run_tcp_check(check_id)
    ├─ run_ping_check(check_id)
    └─ run_cron_check(check_id)   # heartbeat : fail si pas reçu dans l'intervalle
```

### 7.2 Queues Celery

```python
# sentinelops/celery.py
CELERY_TASK_ROUTES = {
    "monitoring.run_*":      {"queue": "checks"},      # workers dédiés aux checks
    "automations.execute_*": {"queue": "workflows"},   # workers dédiés aux workflows
    "compliance.export_*":   {"queue": "exports"},     # workers I/O bound (S3)
    "plugins.*":             {"queue": "plugins"},     # workers pour intégrations externes
}

# Démarrage en dev :
# celery -A sentinelops worker -Q checks,workflows,exports,plugins -c 4 -l info
# celery -A sentinelops beat -l info
```

### 7.3 Modèles Check Engine

```python
# apps/monitoring/models.py (résumé)

class Service(SoftDeleteModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list)             # ["api", "production"]
    status = models.CharField(choices=ServiceStatus, default="active")
    sla_target = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    # ex: 99.900 → 99.9% uptime target


class Check(SoftDeleteModel):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="checks")
    name = models.CharField(max_length=255)
    check_type = models.CharField(choices=CheckType)    # http | tcp | ping | cron
    config = models.JSONField()                         # type-specific config (voir ci-dessous)
    interval_seconds = models.IntegerField(default=60)
    retry_count = models.IntegerField(default=3)
    is_enabled = models.BooleanField(default=True)
    next_run_at = models.DateTimeField(db_index=True)  # utilisé par Beat pour dispatch


class CheckResult(TimestampedModel):
    """Append-only. Jamais mis à jour après création."""
    check = models.ForeignKey(Check, on_delete=models.CASCADE, related_name="results")
    status = models.CharField(choices=CheckStatus)      # ok | fail | timeout
    duration_ms = models.IntegerField()
    response_code = models.IntegerField(null=True)
    error_message = models.TextField(blank=True)
    checked_via = models.CharField(default="cloud")     # "cloud" | agent_id


class Incident(TimestampedModel):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    check = models.ForeignKey(Check, on_delete=models.CASCADE)
    state = models.CharField(choices=IncidentState, default="open")
    severity = models.CharField(choices=Severity, default="medium")
    opened_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True)
    resolved_at = models.DateTimeField(null=True)
    ack_note = models.TextField(blank=True)
```

### 7.4 Config JSON par type de check

```python
# HTTP check config
{
    "url": "https://api.example.com/health",
    "method": "GET",                        # GET | POST
    "headers": {"Authorization": "..."},    # optionnel
    "expected_status": 200,
    "body_contains": "ok",                  # optionnel
    "timeout_seconds": 10,
    "verify_ssl": true,
}

# TCP check config
{
    "host": "db.internal",
    "port": 5432,
    "timeout_seconds": 5,
}

# Ping check config
{
    "host": "10.0.1.50",
    "count": 3,
    "timeout_seconds": 5,
}

# Cron health check config (heartbeat)
{
    "grace_period_seconds": 300,   # délai max entre deux heartbeats
    "last_heartbeat_url": null,    # généré automatiquement par le système
}
```

### 7.5 Incident state machine

```
             check fails (retry_count exhausted)
                         │
                         ▼
                      ┌──────┐
                      │ open │ ◄─────────────────────────────┐
                      └──┬───┘                               │
                         │  user acknowledges                │
                         ▼                                   │ check fails again
              ┌────────────────────┐                         │ (re-open)
              │    acknowledged    │                         │
              └────────┬───────────┘                         │
                       │  check passes                       │
                       ▼                                     │
                  ┌──────────┐                               │
                  │ resolved │ ──────────────────────────────┘
                  └──────────┘
```

---

## 8. WebSocket Architecture (Django Channels)

### 8.1 Routing ASGI

```python
# sentinelops/asgi.py
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/dashboard/", DashboardConsumer.as_asgi()),
            path("ws/incidents/", IncidentFeedConsumer.as_asgi()),
        ])
    ),
})
```

### 8.2 Channel Groups

```
Redis Channel Layer
├── group: "dashboard:{org_slug}"         # tous les clients du dashboard d'une org
├── group: "incidents:{org_slug}"         # feed incident en temps réel
└── group: "service:{service_id}"         # canal par service (latency sparklines)
```

### 8.3 Émission d'un event depuis Celery

```python
# Après qu'un check s'exécute, la tâche Celery émet vers le channel layer

# apps/monitoring/tasks.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def _broadcast_check_result(result: CheckResult) -> None:
    """Émet le résultat vers tous les clients WebSocket de l'organisation."""
    channel_layer = get_channel_layer()
    group_name = f"dashboard:{result.check.service.organization.slug}"
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "service.status",
            "service_id": str(result.check.service_id),
            "status": _compute_service_status(result),
            "check_id": str(result.check_id),
            "duration_ms": result.duration_ms,
            "timestamp": result.created_at.isoformat(),
        }
    )
```

### 8.4 Consumer

```python
# apps/monitoring/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class DashboardConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Authentification par JWT dans le query string (?token=...)
        # ou par cookie (si Django session)
        org_slug = self.scope["url_route"]["kwargs"]["org_slug"]
        self.group_name = f"dashboard:{org_slug}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def service_status(self, event):
        """Reçoit un message de type 'service.status' et le forward au client."""
        await self.send_json(event)

    async def incident_opened(self, event):
        await self.send_json(event)

    async def incident_resolved(self, event):
        await self.send_json(event)
```

---

## 9. Audit Log — Pattern immuable

### 9.1 Modèle

```python
# apps/compliance/models.py
class AuditEvent(UUIDModel):
    """
    Append-only. Override save() et delete() pour garantir l'immuabilité.
    Vit dans le schéma tenant (isolation par organisation).
    """
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    actor_id = models.UUIDField(null=True)          # null = système (tâche Celery)
    actor_email = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=100, db_index=True)
    # ex: "check.created", "incident.acknowledged", "api_key.revoked"

    resource_type = models.CharField(max_length=100)
    resource_id = models.UUIDField(null=True)
    diff = models.JSONField(default=dict)           # {"before": {...}, "after": {...}}
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)       # données contextuelles libres

    class Meta:
        ordering = ["-timestamp"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("AuditEvent is immutable. Create a new one instead.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("AuditEvent cannot be deleted.")
```

### 9.2 Décorateur @audit_action

```python
# common/audit.py
from functools import wraps
from apps.compliance.models import AuditEvent


def audit_action(action: str, resource_type: str):
    """
    Décorateur pour les méthodes de service.
    Enregistre automatiquement un AuditEvent après exécution réussie.

    Usage:
        @audit_action("check.created", "check")
        def create_check(self, organization, actor, **data):
            check = Check.objects.create(**data)
            return check   # ← le return value est utilisé comme resource
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Extraction du contexte depuis les kwargs
            actor = kwargs.get("actor") or (args[1] if len(args) > 1 else None)
            AuditEvent.objects.create(
                actor_id=getattr(actor, "id", None),
                actor_email=getattr(actor, "email", ""),
                action=action,
                resource_type=resource_type,
                resource_id=getattr(result, "id", None),
            )
            return result
        return wrapper
    return decorator
```

---

## 10. Plugin System

### 10.1 Interface de base

```python
# apps/plugins/base.py
from abc import ABC, abstractmethod
from typing import Any


class BasePlugin(ABC):
    """
    Interface que tout plugin doit implémenter.
    Les plugins built-in sont dans apps/plugins/builtins/.
    Les plugins tiers découverts via entry_points (setuptools).
    """
    plugin_id: str        # identifiant unique, ex: "slack"
    display_name: str     # "Slack"
    description: str
    version: str
    config_schema: dict   # JSONSchema pour valider la config

    @abstractmethod
    def send_notification(self, payload: dict[str, Any], config: dict[str, Any]) -> bool:
        """Envoie une notification. Retourne True si succès."""
        ...

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Retourne une liste d'erreurs (vide = valide)."""
        ...
```

### 10.2 Plugins built-in

```
apps/plugins/builtins/
├── slack.py          # Incoming webhook
├── webhook.py        # Generic HTTP POST
└── pagerduty.py      # Events API v2
```

### 10.3 Stockage config chiffré

```python
# apps/plugins/models.py
from django.db import models
from cryptography.fernet import Fernet

class PluginConfig(TimestampedModel):
    plugin_id = models.CharField(max_length=100)
    is_enabled = models.BooleanField(default=True)
    _config_encrypted = models.BinaryField()   # Fernet-chiffré

    @property
    def config(self) -> dict:
        f = Fernet(settings.PLUGIN_ENCRYPTION_KEY)
        return json.loads(f.decrypt(self._config_encrypted))

    @config.setter
    def config(self, value: dict):
        f = Fernet(settings.PLUGIN_ENCRYPTION_KEY)
        self._config_encrypted = f.encrypt(json.dumps(value).encode())
```

---

## 11. API Conventions

### 11.1 Format de réponse standard

```python
# Succès (liste)
{
    "count": 42,
    "next": "https://api.../services/?cursor=xxx",
    "previous": null,
    "results": [...]
}

# Succès (objet)
{
    "id": "uuid",
    "name": "...",
    ...
}

# Erreur
{
    "error": "Check not found.",
    "code": "not_found",
    "details": {}
}

# Erreur de validation
{
    "error": "Validation failed.",
    "code": "validation_error",
    "details": {
        "url": ["This field is required."],
        "interval_seconds": ["Must be one of: 30, 60, 300, 600, 1800, 3600."]
    }
}
```

### 11.2 Pagination cursor-based

```python
# common/pagination.py
from rest_framework.pagination import CursorPagination

class StandardCursorPagination(CursorPagination):
    page_size = 50
    max_page_size = 200
    ordering = "-created_at"
    cursor_query_param = "cursor"
```

### 11.3 Gestion des erreurs globale

```python
# common/exceptions.py
from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "error": _extract_message(response.data),
            "code": _map_status_to_code(response.status_code),
            "details": response.data if isinstance(response.data, dict) else {},
        }
    return response
```

### 11.4 Versionnement URL

```python
# sentinelops/urls.py
urlpatterns = [
    path("api/v1/", include("sentinelops.api_v1_urls")),   # tous les routers v1
    path("api/schema/", SpectacularAPIView.as_view()),     # OpenAPI JSON
    path("api/docs/", SpectacularSwaggerView.as_view()),   # Swagger UI
]
```

---

## 12. Agent On-Prem

### 12.1 Architecture

```
sentinelops-agent (processus unique)
├── Scheduler interne (asyncio)
│   ├── Toutes les N secondes : execute_pending_checks()
│   └── Toutes les 5s : flush_result_queue()
│
├── Collectors (async)
│   ├── HttpCollector.run(config) → CheckResult
│   ├── TcpCollector.run(config)  → CheckResult
│   └── PingCollector.run(config) → CheckResult
│
├── Executor
│   └── ScriptExecutor.run(script_path, timeout) → ExecutionResult
│       (sandboxé dans un subprocess avec timeout)
│
└── Transport (HTTPS + mTLS)
    ├── GET  /api/v1/agent/checks/          → liste des checks à exécuter
    ├── POST /api/v1/agent/results/         → envoi des résultats
    └── POST /api/v1/agent/executions/      → résultat de script
```

### 12.2 Authentification mTLS

```python
# agent/transport/client.py
import httpx

def build_client(config: AgentConfig) -> httpx.AsyncClient:
    """
    Client HTTPS avec certificat client pour mTLS.
    Le backend vérifie le certificat contre la CA interne.
    """
    return httpx.AsyncClient(
        base_url=config.backend.url,
        cert=(config.backend.tls.cert, config.backend.tls.key),
        verify=config.backend.tls.ca,
        headers={"X-Agent-ID": config.agent.id},
        timeout=10.0,
    )
```

---

## 13. Configuration & Settings

### 13.1 Hiérarchie des settings

```python
# settings/base.py (valeurs communes à tous les envs)
# settings/development.py (DEBUG=True, console email backend)
# settings/production.py  (SECURE_HSTS_*, CONN_MAX_AGE, etc.)
# settings/test.py        (PASSWORD_HASHERS = ['...UnsaltedMD5...'], CELERY_TASK_ALWAYS_EAGER)

DJANGO_SETTINGS_MODULE = os.environ.get("DJANGO_SETTINGS_MODULE", "sentinelops.settings.development")
```

### 13.2 Variables d'environnement critiques

```bash
# .env.example
SECRET_KEY=change-me-in-production
DEBUG=False
ALLOWED_HOSTS=api.sentinelops.io,localhost

# Database
DATABASE_URL=postgres://user:pass@localhost:5432/sentinelops

# Redis
REDIS_URL=redis://localhost:6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# S3 / MinIO
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=sentinelops

# Auth
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Plugin encryption
PLUGIN_ENCRYPTION_KEY=     # Fernet key (Fernet.generate_key())

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.xxx
```

---

## 14. Tests

### 14.1 Stratégie

| Niveau | Framework | Scope | Objectif |
|--------|-----------|-------|----------|
| **Unit** | pytest + pytest-django | Service functions, models | Logique métier pure, rapide |
| **Integration** | pytest + APIClient | Endpoints DRF complets | Auth, RBAC, flux complet |
| **Task** | pytest + Celery `task_always_eager` | Tâches Celery | Check engine, workflows |
| **WebSocket** | pytest + `channels.testing` | Consumers | Events temps réel |
| **E2E** | pytest + docker-compose test env | Scénarios complets | Régression majeure |

### 14.2 Fixtures globales (conftest.py)

```python
# tests/conftest.py
import pytest
from apps.accounts.models import Organization, User, Membership

@pytest.fixture
def org(db) -> Organization:
    org = Organization.objects.create(name="Test Corp", slug="testcorp")
    org.create_schema(check_if_exists=True)
    return org

@pytest.fixture
def owner(org) -> User:
    user = User.objects.create_user(email="owner@test.com", password="testpass123")
    Membership.objects.create(user=user, organization=org, role="owner")
    return user

@pytest.fixture
def auth_client(owner, org):
    from rest_framework.test import APIClient
    client = APIClient()
    # Simule le tenant routing
    client.defaults["SERVER_NAME"] = f"testcorp.sentinelops.io"
    client.force_authenticate(user=owner)
    return client
```

### 14.3 Couverture cible

```bash
# Commande de test
pytest --cov=apps --cov-report=html --cov-fail-under=80

# Par app :
# accounts    → 90%  (critique : auth, RBAC)
# monitoring  → 85%  (check engine, incident lifecycle)
# automations → 80%
# compliance  → 85%  (audit log immuabilité)
# plugins     → 75%
```

---

## 15. Héritage de SixStars

SixStars était le terrain d'entraînement. Les patterns ci-dessous ont été validés là-bas et sont repris directement dans SentinelOps :

| Pattern SixStars | App source | Repris dans SentinelOps |
|-----------------|------------|------------------------|
| SHA-256 fingerprinting + `get_or_create` pour dédup | `asterion` | `monitoring` — dédup des incidents (même check, même état) |
| `uuid.uuid5` pour clés d'idempotence | `idem` | `automations` — chaque `WorkflowExecution` a une clé déterministe |
| Append-only `CheckResult` + `downsampling` | `chronos` | `monitoring.CheckResult` + agrégation SLA (p50/p95/p99) |
| Spans liés par `trace_id` | `hermes` | OpenTelemetry sur toutes les requêtes API + tâches Celery |
| State machine `open→ack→resolved` | `siren` | `Incident` state machine (section 7.5) |
| Consumer offsets + fan-out indépendant | `aether` | WebSocket channel groups (section 8.2) + queues Celery dédiées |

> **Différence clé :** SixStars utilisait SQLite + un event bus maison.
> SentinelOps utilise PostgreSQL (multi-tenant) + Redis (Celery broker + Channel Layer).
> La logique de domaine reste identique, l'infrastructure est production-grade.

---

## Annexe A — Dépendances Python (base.txt)

```txt
# Framework
django==5.2.*
djangorestframework==3.15.*
django-tenants==3.7.*
daphne==4.*
channels==4.*
channels-redis==4.*

# Auth
djangorestframework-simplejwt==5.*

# Tasks
celery==5.*
redis==5.*

# API docs
drf-spectacular==0.27.*

# Storage
boto3==1.*                  # S3 / MinIO
django-storages==1.*

# Plugins
cryptography==42.*          # Fernet pour config chiffré

# Observability
opentelemetry-sdk==1.*
opentelemetry-instrumentation-django==0.*
opentelemetry-instrumentation-celery==0.*
structlog==24.*

# Tests
pytest==8.*
pytest-django==4.*
pytest-asyncio==0.*
factory-boy==3.*
```

---

## Annexe B — Docker Compose (dev)

```yaml
# infra/docker-compose.yml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: sentinelops
      POSTGRES_USER: sentinel
      POSTGRES_PASSWORD: sentinel
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"

  backend:
    build: ./backend
    command: daphne -b 0.0.0.0 -p 8000 sentinelops.asgi:application
    depends_on: [db, redis]
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app

  worker:
    build: ./backend
    command: celery -A sentinelops worker -Q checks,workflows,exports,plugins -c 4 -l info
    depends_on: [db, redis]
    env_file: .env

  beat:
    build: ./backend
    command: celery -A sentinelops beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    depends_on: [db, redis]
    env_file: .env

  flower:
    build: ./backend
    command: celery -A sentinelops flower --port=5555
    depends_on: [redis]
    ports:
      - "5555:5555"

volumes:
  pgdata:
```
