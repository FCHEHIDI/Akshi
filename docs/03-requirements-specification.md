# SentinelOps — Requirements Specification

**Version:** 1.0  
**Date:** April 17, 2026  
**Status:** Draft  
**Author:** Fares  
**Classification:** Internal — Engineering

> **Reading guide:** Requirements are tagged with priority using MoSCoW notation:  
> - **[M]** Must Have — V1 blocker  
> - **[S]** Should Have — V1 target, deferrable under pressure  
> - **[C]** Could Have — V2 candidate  
> - **[W]** Won't Have (this version) — explicitly out of scope

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Functional Requirements — Module by Module](#2-functional-requirements)
   - [2.1 Accounts & RBAC](#21-accounts--rbac)
   - [2.2 Monitoring Engine](#22-monitoring-engine)
   - [2.3 Real-Time Dashboard](#23-real-time-dashboard)
   - [2.4 Alerting](#24-alerting)
   - [2.5 Automation & Workflows](#25-automation--workflows)
   - [2.6 Compliance & Audit](#26-compliance--audit)
   - [2.7 Plugin System](#27-plugin-system)
   - [2.8 Public API & SDK](#28-public-api--sdk)
   - [2.9 On-Premises Agent](#29-on-premises-agent)
   - [2.10 Billing](#210-billing)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [Data Architecture](#4-data-architecture)
5. [API Design Specification](#5-api-design-specification)
6. [Security Requirements](#6-security-requirements)
7. [Integration Requirements](#7-integration-requirements)
8. [Deployment Requirements](#8-deployment-requirements)
9. [Testing Requirements](#9-testing-requirements)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                   │
│   ┌──────────────────────┐        ┌────────────────────────────────┐   │
│   │   Next.js Frontend   │        │     External Clients           │   │
│   │  (Browser / HTTPS)   │        │  (API Keys / SDK / Webhooks)   │   │
│   └──────────┬───────────┘        └───────────────┬────────────────┘   │
└──────────────┼────────────────────────────────────┼────────────────────┘
               │ HTTPS + WSS                         │ HTTPS
               ▼                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         GATEWAY LAYER                                   │
│                     Traefik (TLS termination, routing)                  │
└─────────────┬───────────────────────────────────────┬───────────────────┘
              │ HTTP                                   │ HTTP
              ▼                                        ▼
┌─────────────────────────┐           ┌───────────────────────────────────┐
│   Django API (ASGI)     │           │     Django Channels (ASGI)        │
│   DRF REST Endpoints    │           │     WebSocket Consumers           │
│   Auth / RBAC layer     │           │     (monitoring events)           │
└──────┬──────────────────┘           └──────────────┬────────────────────┘
       │                                             │
       ▼                                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SERVICE LAYER                                   │
│   ┌──────────────┐  ┌──────────────┐  ┌───────────┐  ┌─────────────┐  │
│   │  Check Engine│  │ Workflow Orch│  │ Audit Log │  │ Plugin Mgr  │  │
│   │  (Celery)    │  │ (Celery)     │  │  Service  │  │             │  │
│   └──────┬───────┘  └──────┬───────┘  └─────┬─────┘  └─────────────┘  │
└──────────┼─────────────────┼────────────────┼────────────────────────────┘
           │                 │                │
           ▼                 ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                      │
│   ┌──────────────────┐  ┌───────────────┐  ┌──────────────────────┐   │
│   │  PostgreSQL 16   │  │   Redis 7     │  │  S3 / MinIO          │   │
│   │  (per-tenant     │  │  (cache +     │  │  (exports, assets)   │   │
│   │   schemas)       │  │   broker +    │  │                      │   │
│   │                  │  │   channels)   │  │                      │   │
│   └──────────────────┘  └───────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
           ▲
           │ mTLS (HTTPS + client cert)
┌──────────┴───────────────────────┐
│   On-Premises Agent              │
│   (Python binary, customer infra)│
│   - Metric collectors            │
│   - Script executor              │
└──────────────────────────────────┘
```

### 1.2 Django Application Map

| Django App | Domain | Key Models |
|-----------|--------|-----------|
| `accounts` | Auth, RBAC, multi-tenancy | `Organization`, `User`, `Membership`, `Role`, `APIKey`, `Invitation` |
| `monitoring` | Service health | `Service`, `Check`, `CheckResult`, `Incident`, `SLAPolicy` |
| `automations` | Workflow engine | `Workflow`, `Trigger`, `Action`, `WorkflowExecution` |
| `compliance` | Audit & policies | `AuditEvent`, `Policy`, `ComplianceReport` |
| `plugins` | Integration hub | `Plugin`, `PluginConfig`, `PluginExecution` |
| `billing` | Monetization | `Plan`, `Subscription`, `UsageRecord`, `Invoice` |
| `common` | Shared utilities | `TimestampedModel`, `SoftDeleteModel`, `UUIDModel` |

---

## 2. Functional Requirements

### 2.1 Accounts & RBAC

#### 2.1.1 Authentication

| ID | Requirement | Priority |
|----|-------------|----------|
| AUTH-01 | System shall support email/password authentication | [M] |
| AUTH-02 | System shall issue JWT access tokens (15-minute expiry) and refresh tokens (7-day expiry) | [M] |
| AUTH-03 | Refresh tokens shall be rotated on each use (sliding window) | [M] |
| AUTH-04 | Refresh tokens shall be stored server-side (Redis) and revocable | [M] |
| AUTH-05 | System shall support API key authentication for programmatic access | [M] |
| AUTH-06 | API keys shall be scoped to an organization and carry permissions | [M] |
| AUTH-07 | API keys shall be hashed before storage (never stored in plain text) | [M] |
| AUTH-08 | System shall support social login (Google OAuth2) | [C] |
| AUTH-09 | System shall support SAML 2.0 SSO for enterprise organizations | [W] |

#### 2.1.2 Multi-Tenancy

| ID | Requirement | Priority |
|----|-------------|----------|
| MT-01 | Each organization shall have an isolated PostgreSQL schema | [M] |
| MT-02 | Cross-tenant data access shall be impossible at the ORM level | [M] |
| MT-03 | Tenant routing shall be domain-based (`{org}.sentinelops.io`) | [M] |
| MT-04 | Each organization shall have a unique slug used in API paths | [M] |
| MT-05 | An organization owner may create sub-organizations | [C] |

#### 2.1.3 RBAC

| ID | Requirement | Priority |
|----|-------------|----------|
| RBAC-01 | System shall support 4 built-in roles: Owner, Admin, Member, Viewer | [M] |
| RBAC-02 | Permissions shall be enforced at the API view level via permission classes | [M] |
| RBAC-03 | Role matrix: Owner (all), Admin (all except billing), Member (read/write ops), Viewer (read-only) | [M] |
| RBAC-04 | A user may belong to multiple organizations with different roles | [M] |
| RBAC-05 | All permission denials shall be logged to the audit log | [M] |
| RBAC-06 | Custom roles with fine-grained permission selection | [C] |

#### 2.1.4 User Invitations

| ID | Requirement | Priority |
|----|-------------|----------|
| INV-01 | Admins shall be able to invite users by email | [M] |
| INV-02 | Invitation tokens shall expire after 72 hours | [M] |
| INV-03 | Invitations shall specify the role the invited user will receive | [M] |
| INV-04 | Invited users who already have an account shall be auto-joined on token acceptance | [M] |

---

### 2.2 Monitoring Engine

#### 2.2.1 Services

| ID | Requirement | Priority |
|----|-------------|----------|
| MON-01 | Users shall be able to create, update, delete Services | [M] |
| MON-02 | A Service has: name, description, tags, URL (optional), status (active/paused) | [M] |
| MON-03 | Services shall be organizable with tags for filtering | [S] |
| MON-04 | Services shall support SLA policy assignment (target uptime %) | [S] |

#### 2.2.2 Checks

| ID | Requirement | Priority |
|----|-------------|----------|
| CHK-01 | System shall support HTTP checks (GET, POST, custom headers, expected status code, response body assertion) | [M] |
| CHK-02 | System shall support TCP checks (host:port reachability, timeout) | [M] |
| CHK-03 | System shall support Ping (ICMP) checks | [M] |
| CHK-04 | System shall support Cron health checks (heartbeat: check fires if NOT called within interval) | [M] |
| CHK-05 | Check intervals shall be configurable: 30s, 1m, 5m, 10m, 30m, 1h | [M] |
| CHK-06 | Checks shall support configurable retry count before declaring failure (default: 3) | [M] |
| CHK-07 | Each check shall record: timestamp, duration_ms, status (ok/fail/timeout), response_code, error_message | [M] |
| CHK-08 | Check execution shall be distributed via Celery; multiple workers supported | [M] |
| CHK-09 | Check results shall be stored with configurable retention (default 90 days) | [M] |
| CHK-10 | Checks shall support SSL certificate validation and expiry warnings | [S] |
| CHK-11 | HTTP checks shall support custom request bodies (JSON/form) | [S] |

#### 2.2.3 Incident Lifecycle

| ID | Requirement | Priority |
|----|-------------|----------|
| INC-01 | An incident shall be opened automatically when a check fails after retry_count attempts | [M] |
| INC-02 | Incident states: `open`, `acknowledged`, `resolved` | [M] |
| INC-03 | Incident resolution shall be automatic when the check passes again | [M] |
| INC-04 | Users shall be able to manually acknowledge an incident with a note | [M] |
| INC-05 | Incidents shall have: severity (critical, high, medium, low), duration, MTTR, linked check | [M] |
| INC-06 | Incident history shall be preserved indefinitely (not subject to check result retention) | [S] |
| INC-07 | Post-mortem notes shall be attachable to closed incidents | [C] |

#### 2.2.4 Uptime & SLA Metrics

| ID | Requirement | Priority |
|----|-------------|----------|
| SLA-01 | System shall calculate uptime % per service per time window (24h, 7d, 30d, 90d) | [M] |
| SLA-02 | Average response time (p50, p95, p99) shall be computed per check | [S] |
| SLA-03 | SLA breach events shall trigger an alert | [S] |

---

### 2.3 Real-Time Dashboard

| ID | Requirement | Priority |
|----|-------------|----------|
| DASH-01 | Dashboard shall display a service health map (grid/list view) with color-coded status | [M] |
| DASH-02 | Service health map shall update in real-time via WebSocket (no polling) | [M] |
| DASH-03 | Dashboard shall display a live incident feed | [M] |
| DASH-04 | Dashboard shall display latency sparklines per service | [M] |
| DASH-05 | Dashboard shall display uptime percentage per service (24h, 7d, 30d) | [M] |
| DASH-06 | Historical latency charts shall be interactive (zoom, hover) | [S] |
| DASH-07 | Dashboard shall support filtering by tags, status, check type | [S] |
| DASH-08 | Dashboard shall display active Celery worker count and queue depth | [S] |
| DASH-09 | Dashboard shall support dark/light mode | [C] |
| DASH-10 | Public status page (read-only, no auth) per organization | [C] |

#### 2.3.1 WebSocket Protocol

```
// Server → Client events

// Service status update
{
  "type": "service.status",
  "service_id": "uuid",
  "status": "degraded",          // ok | degraded | down | unknown
  "check_id": "uuid",
  "duration_ms": 342,
  "timestamp": "2026-04-17T12:00:00Z"
}

// Incident opened
{
  "type": "incident.opened",
  "incident_id": "uuid",
  "service_id": "uuid",
  "severity": "critical",
  "message": "HTTP check failed: 502 Bad Gateway",
  "timestamp": "2026-04-17T12:00:00Z"
}

// Incident resolved
{
  "type": "incident.resolved",
  "incident_id": "uuid",
  "service_id": "uuid",
  "duration_seconds": 142,
  "timestamp": "2026-04-17T12:02:22Z"
}
```

---

### 2.4 Alerting

| ID | Requirement | Priority |
|----|-------------|----------|
| ALT-01 | System shall send email alerts on incident open and resolve | [M] |
| ALT-02 | System shall send Slack notifications via incoming webhook | [M] |
| ALT-03 | System shall call custom webhooks (HTTP POST with JSON payload) | [M] |
| ALT-04 | Alert rules shall be configurable per service (which events trigger which channels) | [M] |
| ALT-05 | Alert deduplication: only one alert per incident until resolved | [M] |
| ALT-06 | Escalation policies: if not acknowledged within N minutes, alert next contact | [S] |
| ALT-07 | Alert suppression windows (maintenance mode per service) | [S] |
| ALT-08 | PagerDuty integration (trigger/resolve incidents via Events API v2) | [S] |
| ALT-09 | Microsoft Teams notifications | [C] |

---

### 2.5 Automation & Workflows

#### 2.5.1 Workflow Model

A **Workflow** consists of:
- One **Trigger** (what starts the workflow)
- One or more **Actions** (what happens)
- Execution conditions (optional filters)

#### 2.5.2 Triggers

| ID | Requirement | Priority |
|----|-------------|----------|
| TRG-01 | Trigger: `incident_opened` — fires when a new incident is created | [M] |
| TRG-02 | Trigger: `incident_resolved` — fires when an incident is resolved | [M] |
| TRG-03 | Trigger: `threshold_exceeded` — fires when a metric (latency, error rate) exceeds a configurable threshold | [M] |
| TRG-04 | Trigger: `heartbeat_missed` — fires when a cron health check does not check in | [M] |
| TRG-05 | Trigger: `sla_breach` — fires when uptime drops below SLA target | [S] |
| TRG-06 | Trigger: `scheduled` — fires on a cron schedule (independent of monitoring events) | [C] |

#### 2.5.3 Actions

| ID | Requirement | Priority |
|----|-------------|----------|
| ACT-01 | Action: `send_email` — send templated email to one or more addresses | [M] |
| ACT-02 | Action: `send_slack` — post message to Slack channel | [M] |
| ACT-03 | Action: `call_webhook` — HTTP POST to a configured URL | [M] |
| ACT-04 | Action: `run_script` — execute a script via the on-prem agent | [M] |
| ACT-05 | Action: `create_incident` — manually open an incident on a service | [S] |
| ACT-06 | Action: `suppress_alerts` — enable maintenance window on a service | [S] |
| ACT-07 | Action: `send_pagerduty` — trigger PagerDuty event | [S] |

#### 2.5.4 Execution

| ID | Requirement | Priority |
|----|-------------|----------|
| WF-01 | Workflows shall be executed asynchronously via Celery | [M] |
| WF-02 | Each workflow execution shall produce a `WorkflowExecution` record (status, logs, duration) | [M] |
| WF-03 | Failed actions shall be retried up to 3 times with exponential backoff | [M] |
| WF-04 | Workflow execution history shall be retained for 30 days | [S] |
| WF-05 | Workflows shall support an enabled/disabled state | [M] |

---

### 2.6 Compliance & Audit

#### 2.6.1 Audit Logs

| ID | Requirement | Priority |
|----|-------------|----------|
| AUD-01 | All state-changing operations shall produce an audit event | [M] |
| AUD-02 | Audit events are append-only (no update or delete) | [M] |
| AUD-03 | Audit event schema: `id`, `timestamp`, `actor_id`, `actor_email`, `action`, `resource_type`, `resource_id`, `diff` (JSON), `ip_address` | [M] |
| AUD-04 | Audit events shall be filterable by: date range, actor, action, resource type | [M] |
| AUD-05 | Audit events shall be exportable to CSV | [M] |
| AUD-06 | Audit events shall be exportable to PDF (formatted report) | [S] |
| AUD-07 | Audit log shall cover: auth (login, logout, failed attempts), config changes (service, check, workflow), RBAC changes, API key creation/revocation | [M] |

#### 2.6.2 Compliance Policies (V1 light)

| ID | Requirement | Priority |
|----|-------------|----------|
| POL-01 | System shall support simple policies: "all active services must have at least one check" | [S] |
| POL-02 | Policy violations shall appear in the dashboard as warnings | [S] |
| POL-03 | Policy engine shall be extensible (new policy types without core changes) | [S] |
| POL-04 | Scheduled compliance report generation (weekly/monthly) | [C] |

---

### 2.7 Plugin System

| ID | Requirement | Priority |
|----|-------------|----------|
| PLG-01 | Plugin system shall use Django's app registry + a plugin discovery mechanism | [M] |
| PLG-02 | Each plugin shall be enable/disabled per organization | [M] |
| PLG-03 | Plugin configuration shall be stored encrypted (sensitive fields: tokens, secrets) | [M] |
| PLG-04 | Built-in plugin: Slack (incoming webhook) | [M] |
| PLG-05 | Built-in plugin: Generic Webhook | [M] |
| PLG-06 | Built-in plugin: PagerDuty Events API v2 | [S] |
| PLG-07 | Built-in plugin: Microsoft Teams (incoming webhook) | [C] |
| PLG-08 | Plugin SDK documentation for third-party plugin development | [C] |

---

### 2.8 Public API & SDK

#### 2.8.1 REST API

| ID | Requirement | Priority |
|----|-------------|----------|
| API-01 | API shall be versioned: `/api/v1/` | [M] |
| API-02 | API shall be authenticated via JWT Bearer token or API key (header: `X-API-Key`) | [M] |
| API-03 | All list endpoints shall support pagination (cursor-based preferred), filtering, and ordering | [M] |
| API-04 | API shall return consistent error format: `{error: string, code: string, details: object}` | [M] |
| API-05 | Rate limiting: 1000 req/hour per API key; 100 req/min per IP (unauthenticated) | [M] |
| API-06 | OpenAPI 3.0 spec shall be auto-generated and served at `/api/schema/` | [M] |
| API-07 | Swagger UI shall be served at `/api/docs/` | [S] |
| API-08 | All endpoints shall be idempotent where applicable (PUT, DELETE) | [M] |

#### 2.8.2 Key Endpoints

```
# Monitoring
GET     /api/v1/services/
POST    /api/v1/services/
GET     /api/v1/services/{id}/
PUT     /api/v1/services/{id}/
DELETE  /api/v1/services/{id}/
GET     /api/v1/services/{id}/checks/
GET     /api/v1/services/{id}/incidents/
GET     /api/v1/services/{id}/uptime/        # ?window=24h|7d|30d

GET     /api/v1/checks/
POST    /api/v1/checks/
GET     /api/v1/checks/{id}/
GET     /api/v1/checks/{id}/results/         # paginated history

GET     /api/v1/incidents/
GET     /api/v1/incidents/{id}/
PATCH   /api/v1/incidents/{id}/              # acknowledge / resolve

# Automations
GET     /api/v1/workflows/
POST    /api/v1/workflows/
GET     /api/v1/workflows/{id}/executions/

# Audit
GET     /api/v1/audit/events/
GET     /api/v1/audit/events/export/         # ?format=csv

# Accounts
GET     /api/v1/organizations/
POST    /api/v1/organizations/{slug}/invitations/
GET     /api/v1/organizations/{slug}/members/
DELETE  /api/v1/organizations/{slug}/members/{user_id}/

# Auth
POST    /api/v1/auth/login/
POST    /api/v1/auth/refresh/
POST    /api/v1/auth/logout/
POST    /api/v1/auth/api-keys/
DELETE  /api/v1/auth/api-keys/{id}/
```

#### 2.8.3 Python SDK

| ID | Requirement | Priority |
|----|-------------|----------|
| SDK-01 | Python SDK shall be auto-generated from the OpenAPI spec using `openapi-generator` | [M] |
| SDK-02 | SDK shall be manually polished for ergonomics (Pythonic method names, docstrings) | [S] |
| SDK-03 | SDK shall be published to PyPI as `sentinelops-sdk` | [M] |
| SDK-04 | SDK shall support async usage (asyncio-compatible) | [S] |

```python
# Example SDK usage
from sentinelops import SentinelOpsClient

client = SentinelOpsClient(api_key="sk_live_xxx", base_url="https://api.sentinelops.io")

# List services
services = client.monitoring.list_services()

# Create a check
check = client.monitoring.create_check(
    service_id="uuid",
    type="http",
    config={"url": "https://api.example.com/health", "expected_status": 200},
    interval_seconds=60,
)

# Get uptime
uptime = client.monitoring.get_uptime(service_id="uuid", window="7d")
print(f"7-day uptime: {uptime.percentage:.2f}%")
```

---

### 2.9 On-Premises Agent

| ID | Requirement | Priority |
|----|-------------|----------|
| AGT-01 | Agent shall communicate with the SentinelOps backend via HTTPS + mTLS (client certificate) | [M] |
| AGT-02 | Agent shall register with the backend on first start and receive a unique agent ID | [M] |
| AGT-03 | Agent shall execute HTTP, TCP, and Ping checks locally (for services not accessible from cloud) | [M] |
| AGT-04 | Agent shall push check results to the backend at configurable intervals | [M] |
| AGT-05 | Agent shall execute scripts requested by the automation engine (with sandboxing) | [M] |
| AGT-06 | Agent configuration shall be in YAML (`sentinelops-agent.yml`) | [M] |
| AGT-07 | Agent shall be distributable as a single binary (PyInstaller in V1) | [M] |
| AGT-08 | Agent shall log all activities with configurable log level | [M] |
| AGT-09 | Agent shall handle network interruptions gracefully (local queue + retry) | [S] |
| AGT-10 | Agent shall support auto-update notification (alert user when new version available) | [C] |

```yaml
# sentinelops-agent.yml example
agent:
  id: ""               # filled on first registration
  name: "datacenter-paris-01"
  tags:
    - datacenter
    - paris

backend:
  url: "https://api.sentinelops.io"
  api_key: "sk_agent_xxx"
  tls:
    cert: "/etc/sentinelops/agent.crt"
    key: "/etc/sentinelops/agent.key"
    ca: "/etc/sentinelops/ca.crt"

collectors:
  interval_seconds: 30

executor:
  allowed_scripts_dir: "/opt/sentinelops/scripts"
  timeout_seconds: 30

logging:
  level: INFO
  file: "/var/log/sentinelops-agent.log"
```

---

### 2.10 Billing

| ID | Requirement | Priority |
|----|-------------|----------|
| BIL-01 | System shall integrate with Stripe for payment processing | [C] |
| BIL-02 | Plans shall be: Starter, Pro, Business, Enterprise | [C] |
| BIL-03 | Usage shall be metered nightly by a Celery task and synced to Stripe | [C] |
| BIL-04 | Usage dimensions: active_checks, seats, organizations, api_calls, data_retention_days | [C] |
| BIL-05 | Self-serve upgrade/downgrade via billing portal | [C] |
| BIL-06 | Stripe webhook handler for: `invoice.paid`, `invoice.payment_failed`, `customer.subscription.deleted` | [C] |
| BIL-07 | On plan downgrade, system shall enforce limits (pause excess checks, lock features) | [C] |

---

## 3. Non-Functional Requirements

### 3.1 Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-P01 | API response time (p95, read endpoints) | < 200ms |
| NFR-P02 | API response time (p95, write endpoints) | < 500ms |
| NFR-P03 | WebSocket event delivery latency (server to browser) | < 500ms end-to-end |
| NFR-P04 | Dashboard initial load time | < 2s (LCP) |
| NFR-P05 | Check execution latency overhead (schedule to execution start) | < 5 seconds |
| NFR-P06 | Maximum checks supported per deployment (V1) | 10,000 active checks |
| NFR-P07 | Maximum concurrent WebSocket connections | 1,000 (single server, V1) |

### 3.2 Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-R01 | SaaS uptime SLA | 99.9% monthly |
| NFR-R02 | Check engine resilience: Celery worker crash shall not lose pending checks | Beat reschedules; idempotent tasks |
| NFR-R03 | Database: automated daily backups with 30-day retention | |
| NFR-R04 | Graceful degradation: API continues to serve cached data if DB is temporarily unavailable | [S] |

### 3.3 Scalability

| ID | Requirement |
|----|-------------|
| NFR-S01 | Celery workers shall be horizontally scalable (add workers without code change) |
| NFR-S02 | Check engine shall support sharding (checks distributed across workers by hash) |
| NFR-S03 | API servers shall be stateless (no local state; all state in DB/Redis) |
| NFR-S04 | PostgreSQL schema-based tenancy shall support up to 500 organizations per V1 deployment |

### 3.4 Security

| ID | Requirement |
|----|-------------|
| NFR-SEC01 | All OWASP Top 10 vulnerabilities mitigated |
| NFR-SEC02 | All data in transit encrypted via TLS 1.2+ |
| NFR-SEC03 | All passwords hashed with Argon2 (Django default) |
| NFR-SEC04 | API keys hashed with SHA-256 before storage |
| NFR-SEC05 | Agent mTLS: mutual certificate authentication required |
| NFR-SEC06 | Plugin secrets (tokens, webhooks) encrypted at rest with AES-256 (Django `cryptography` field) |
| NFR-SEC07 | All dependency versions pinned; automated CVE scanning in CI (Safety / pip-audit) |
| NFR-SEC08 | Rate limiting applied at API gateway level (not just application level) |
| NFR-SEC09 | CSRF protection enabled for session-based views |
| NFR-SEC10 | Content Security Policy headers on all HTML responses |

### 3.5 Observability

| ID | Requirement |
|----|-------------|
| NFR-OBS01 | Application shall expose Prometheus metrics at `/metrics` (auth-protected) |
| NFR-OBS02 | Key metrics: API request rate, error rate, latency histogram, Celery queue depth, check execution rate |
| NFR-OBS03 | All application logs shall be structured JSON (via structlog) |
| NFR-OBS04 | OpenTelemetry traces shall be emitted for API requests and Celery tasks |
| NFR-OBS05 | Health check endpoint at `/health/` returning service status |

### 3.6 Maintainability

| ID | Requirement |
|----|-------------|
| NFR-M01 | Backend test coverage ≥ 80% (unit + integration) |
| NFR-M02 | All public API endpoints documented with request/response examples |
| NFR-M03 | Database migrations must be backward-compatible (no destructive changes without version gate) |
| NFR-M04 | All environment configuration via environment variables (no hardcoded config) |
| NFR-M05 | CI must pass (lint + tests) before merging to main |

---

## 4. Data Architecture

### 4.1 Core Models (simplified)

```python
# accounts/models.py

class Organization(TimestampedModel):
    id: UUID (PK)
    name: str
    slug: str (unique)
    schema_name: str  # django-tenants schema
    domain: str
    plan: ForeignKey(Plan)
    created_at: datetime

class User(AbstractBaseUser):
    id: UUID (PK)
    email: str (unique)
    is_active: bool
    date_joined: datetime

class Membership(TimestampedModel):
    user: ForeignKey(User)
    organization: ForeignKey(Organization)
    role: ForeignKey(Role)
    class Meta:
        unique_together = [("user", "organization")]

class APIKey(TimestampedModel):
    id: UUID (PK)
    organization: ForeignKey(Organization)
    name: str
    key_hash: str  # SHA-256 of raw key
    prefix: str    # first 8 chars for display
    permissions: JSONField
    last_used_at: datetime | None
    expires_at: datetime | None
    is_active: bool

# monitoring/models.py

class Service(TimestampedModel, SoftDeleteModel):
    id: UUID (PK)
    name: str
    description: str
    tags: ArrayField(str)
    status: Enum[ok, degraded, down, unknown, paused]
    sla_policy: ForeignKey(SLAPolicy, null=True)

class Check(TimestampedModel):
    id: UUID (PK)
    service: ForeignKey(Service)
    type: Enum[http, tcp, ping, cron]
    name: str
    config: JSONField  # type-specific config
    interval_seconds: int
    retry_count: int  (default=3)
    timeout_seconds: int  (default=10)
    is_active: bool
    last_checked_at: datetime | None

class CheckResult(TimestampedModel):
    id: UUID (PK)
    check: ForeignKey(Check)
    status: Enum[ok, fail, timeout, error]
    duration_ms: int
    response_code: int | None
    error_message: str | None
    checked_at: datetime
    agent_id: UUID | None  # null = cloud check

class Incident(TimestampedModel):
    id: UUID (PK)
    service: ForeignKey(Service)
    check: ForeignKey(Check)
    status: Enum[open, acknowledged, resolved]
    severity: Enum[critical, high, medium, low]
    opened_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by: ForeignKey(User, null=True)
    resolved_at: datetime | None
    duration_seconds: int | None  # computed on resolve

# compliance/models.py

class AuditEvent(models.Model):
    # Append-only: no update/delete operations permitted
    id: UUID (PK)
    timestamp: datetime (auto_now_add, indexed)
    actor_id: UUID | None  # null for system actions
    actor_email: str
    action: str  # e.g. "check.created", "incident.acknowledged"
    resource_type: str
    resource_id: str
    diff: JSONField | None  # before/after for updates
    ip_address: GenericIPAddressField | None
    meta: JSONField  # additional context

    class Meta:
        # Enforce no updates/deletes via Django signals
        # or database-level triggers
        ordering = ["-timestamp"]
```

### 4.2 Multi-Tenancy Schema Strategy

```
Public schema (shared):
  - accounts_organization
  - accounts_user
  - django_tenants_domain

Per-tenant schema ({org_slug}):
  - monitoring_service
  - monitoring_check
  - monitoring_checkresult
  - monitoring_incident
  - automations_workflow
  - compliance_auditevent
  - plugins_pluginconfig
  - billing_usagerecord
```

---

## 5. API Design Specification

### 5.1 Conventions

- **Base URL**: `https://api.sentinelops.io/api/v1/` (SaaS) or `https://{host}/api/v1/` (On-Prem)
- **Authentication**: `Authorization: Bearer {jwt}` or `X-API-Key: {api_key}`
- **Content-Type**: `application/json`
- **Pagination**: Cursor-based via `?cursor=` and `?limit=` (default 20, max 100)
- **Filtering**: Django-filter style `?status=open&severity=critical`
- **Ordering**: `?ordering=-opened_at` (prefix `-` for descending)
- **Versioning**: URL-based (`/api/v1/`, `/api/v2/`)

### 5.2 Standard Response Formats

```json
// List response
{
  "count": 42,
  "next": "https://api.sentinelops.io/api/v1/incidents/?cursor=abc123",
  "previous": null,
  "results": [ ... ]
}

// Error response
{
  "error": "Not found",
  "code": "RESOURCE_NOT_FOUND",
  "details": {
    "resource": "incident",
    "id": "550e8400-e29b-41d4-a716-446655440000"
  }
}

// Validation error
{
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "details": {
    "interval_seconds": ["Must be at least 30."],
    "config.url": ["Enter a valid URL."]
  }
}
```

---

## 6. Security Requirements

### 6.1 Authentication & Authorization

| Threat | Mitigation |
|--------|-----------|
| Brute-force login | Rate limit: 10 attempts/15min per IP; account lockout after 20 |
| JWT token theft | Short expiry (15min); refresh token rotation; revocation via Redis |
| API key leakage | Store hashed; display prefix only; log all uses |
| Cross-tenant data access | Schema isolation at DB level; tenant middleware enforced |
| Privilege escalation | Role checks on every view; no client-side role inference |

### 6.2 Input Validation

- All API inputs validated at serializer level (DRF)
- File uploads: type whitelist (PDF, CSV only); max size enforced
- Script execution via agent: allowlisted scripts directory; timeout enforced

### 6.3 Infrastructure Security

- TLS 1.2+ enforced at Traefik level; HTTP redirected to HTTPS
- Security headers: `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`
- Dependency scanning: `pip-audit` in CI on every push
- Docker images: non-root user; read-only filesystem where possible; no secrets in image layers

### 6.4 Data Protection

- PII (email addresses) in audit logs: retained 2 years, then anonymized
- On deletion of organization: cascade delete all tenant data (GDPR right to erasure)
- Backups: encrypted at rest (AES-256), separate storage account

---

## 7. Integration Requirements

### 7.1 Email

- Provider: SendGrid (SaaS) or SMTP (on-prem configurable)
- Templates: HTML + plain text; branded SentinelOps design
- Events: incident alert, invitation, SLA breach, weekly summary

### 7.2 Slack

- Method: Incoming Webhook (no OAuth app required for basic use)
- Payload: Block Kit formatted messages with incident details and action buttons

### 7.3 PagerDuty

- Method: Events API v2 (`POST https://events.pagerduty.com/v2/enqueue`)
- Actions: `trigger` (incident open), `resolve` (incident close), `acknowledge`

### 7.4 Prometheus

- Django metrics via `django-prometheus`
- Celery metrics via `celery-prometheus-exporter`
- Custom metrics: check execution rate, incident open/close rate, WebSocket connection count

### 7.5 OpenTelemetry

- Instrumentation: Django (via `opentelemetry-instrumentation-django`), Celery, SQLAlchemy
- Exporter: OTLP → Jaeger (on-prem) or OTLP → Cloud backend (SaaS)

---

## 8. Deployment Requirements

### 8.1 Docker Compose (Development / On-Prem)

```yaml
# docker-compose.yml services required:
services:
  - traefik           # reverse proxy + TLS
  - django            # Django API (ASGI via Daphne)
  - celery-worker     # async task worker
  - celery-beat       # scheduler
  - celery-flower     # Celery monitoring (optional)
  - frontend          # Next.js (or separate Vercel deploy)
  - postgres          # PostgreSQL 16
  - redis             # Redis 7
  - minio             # S3-compatible storage
```

### 8.2 Environment Variables

All configuration shall be injectable via environment variables, following 12-factor principles:

```bash
# Core
SECRET_KEY=
DEBUG=false
ALLOWED_HOSTS=
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://redis:6379/0

# Storage
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_ENDPOINT_URL=  # MinIO endpoint for on-prem

# Email
EMAIL_BACKEND=
SENDGRID_API_KEY=

# Auth
JWT_SECRET_KEY=
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Agent mTLS
AGENT_CA_CERT_PATH=

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=
SENTRY_DSN=  # optional
```

### 8.3 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml — stages

on: [push, pull_request]

jobs:
  lint:
    - ruff check .          # fast Python linter
    - ruff format --check . # format check
    - mypy .                # type checking

  test:
    - pytest --cov=. --cov-report=xml
    - coverage report --fail-under=80

  security:
    - pip-audit             # CVE scan
    - bandit -r backend/    # static security analysis

  build:
    - docker build backend/
    - docker build frontend/
    - docker push ghcr.io/sentinelops/...  # on main only
```

---

## 9. Testing Requirements

### 9.1 Test Strategy

| Level | Framework | Scope | Coverage Target |
|-------|-----------|-------|----------------|
| Unit | pytest + pytest-django | Models, services, utilities | ≥90% |
| Integration | pytest + DRF test client | API endpoints, Celery tasks | ≥80% |
| End-to-end | Playwright | Critical user flows (login, create check, incident) | Key flows only |
| Performance | Locust | API endpoints, WebSocket connections | Before each release |
| Security | OWASP ZAP (automated) | API surface | Before V1 launch |

### 9.2 Critical Test Cases

```python
# Must-pass test scenarios

# Monitoring
- test_http_check_creates_incident_on_failure
- test_incident_auto_resolves_when_check_passes
- test_check_respects_retry_count_before_incident
- test_cron_check_fires_on_missed_heartbeat
- test_uptime_calculation_accuracy

# Multi-tenancy
- test_tenant_a_cannot_access_tenant_b_services
- test_api_key_scoped_to_organization
- test_cross_tenant_incident_isolation

# RBAC
- test_viewer_cannot_create_service
- test_member_cannot_delete_organization
- test_admin_cannot_access_billing

# Audit
- test_audit_event_created_on_service_update
- test_audit_log_is_append_only (no update/delete)

# WebSocket
- test_websocket_delivers_incident_event_under_500ms
- test_websocket_authentication_required
```

---

*Document maintained by the SentinelOps engineering team.*  
*Next review: May 17, 2026*
