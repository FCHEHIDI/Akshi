# SentinelOps — Project Charter

**Version:** 1.0  
**Date:** April 17, 2026  
**Status:** Approved  
**Author:** Fares  
**Classification:** Internal — Project Management

---

## Table of Contents

1. [Project Identity](#1-project-identity)
2. [Project Context & Justification](#2-project-context--justification)
3. [Objectives & Success Criteria](#3-objectives--success-criteria)
4. [Scope Definition](#4-scope-definition)
5. [Stakeholders](#5-stakeholders)
6. [Technology Stack](#6-technology-stack)
7. [Project Organization](#7-project-organization)
8. [Constraints & Assumptions](#8-constraints--assumptions)
9. [Risks & Mitigations](#9-risks--mitigations)
10. [Milestones & Timeline](#10-milestones--timeline)
11. [Budget Envelope (indicative)](#11-budget-envelope-indicative)
12. [Go/No-Go Criteria](#12-gono-go-criteria)

---

## 1. Project Identity

| Field | Value |
|-------|-------|
| **Project Name** | SentinelOps |
| **Project Code** | SNT-2026 |
| **Type** | New product development (B2B SaaS + On-Premises) |
| **Domain** | Infrastructure Monitoring, Automation, Compliance |
| **Start Date** | April 17, 2026 |
| **Target V1 Release** | October 17, 2026 (6 months) |
| **Project Lead** | Fares |
| **Document Version** | 1.0 |

---

## 2. Project Context & Justification

### 2.1 Context

Engineering teams at mid-market and enterprise companies manage increasingly complex hybrid infrastructures. The current tooling landscape forces teams to assemble a fragmented stack of 4–7 separate tools to achieve basic observability, alerting, and auditability — leading to high costs, alert fatigue, and compliance gaps.

There is a clear market opportunity for a unified, self-hostable platform that integrates monitoring, automation, and compliance in a single product with native multi-tenancy and enterprise-grade security.

### 2.2 Business Justification

- **Market gap**: No existing tool combines on-premises deployment, multi-tenancy, monitoring, and compliance at an accessible price point.
- **Revenue potential**: Addressable market of $1–2B with a clear ICP (Ideal Customer Profile) in regulated industries and MSPs.
- **Strategic positioning**: A self-hostable alternative to Datadog/New Relic with a compelling open-core model (Community + Enterprise licenses).
- **Technical differentiation**: Native multi-tenancy, RBAC, immutable audit logs, and a lightweight on-prem agent with mTLS — features typically reserved for $100K+ enterprise contracts.

### 2.3 Project Trigger

This project is initiated as a full product build with the intent to:
1. Ship a production-ready V1 within 6 months
2. Onboard initial design partners (early customers) during development
3. Launch publicly on Product Hunt and Hacker News post-V1

---

## 3. Objectives & Success Criteria

### 3.1 Primary Objectives

| # | Objective | Measurable Success Criterion |
|---|-----------|------------------------------|
| O1 | Deliver a functional monitoring core | ≥5 check types operational; <5 min from check creation to first result |
| O2 | Enable real-time observability | Dashboard latency <500ms end-to-end via WebSocket |
| O3 | Ship self-hostable deployment | One-command Docker Compose install; complete in <10 minutes |
| O4 | Establish RBAC + multi-tenancy | ≥3 roles per org; full tenant data isolation verified by integration tests |
| O5 | Deliver REST API + Python SDK | 100% API coverage of core features; SDK published to PyPI |
| O6 | Build automation engine | ≥3 action types; end-to-end workflow test passing |

### 3.2 Quality Objectives

| Dimension | Target |
|-----------|--------|
| Test coverage (backend) | ≥80% (unit + integration) |
| API response time (p95) | <200ms for read endpoints |
| Uptime (SaaS, post-launch) | 99.9% monthly |
| Security | Zero critical/high CVEs in OWASP Top 10 at launch |
| Documentation | All public API endpoints documented with examples |

### 3.3 Non-Objectives (V1)

- Mobile application
- GraphQL API (planned V2)
- AI/ML anomaly detection (planned V3)
- Multi-region SaaS (planned V3)
- Visual drag-and-drop workflow builder (planned V2)

---

## 4. Scope Definition

### 4.1 In Scope — V1

```
✅ MONITORING
   - HTTP checks (GET/POST, custom headers, SSL validation)
   - TCP checks (port reachability)
   - Ping checks (ICMP)
   - Cron job health checks (heartbeat)
   - Configurable check intervals (30s minimum)
   - Incident lifecycle: Open → Acknowledged → Resolved
   - SLA tracking per service

✅ REAL-TIME DASHBOARD
   - WebSocket-driven latency and uptime feed
   - Live incident stream
   - Service health status map
   - Historical charts (7-day, 30-day, 90-day)

✅ ALERTING
   - Email alerts
   - Slack notifications (via webhook)
   - Custom webhook
   - Escalation policies
   - Alert deduplication (no duplicate pages per incident)

✅ AUTOMATION WORKFLOWS
   - Triggers: incident_opened, threshold_exceeded, heartbeat_missed
   - Actions: send_email, send_slack, call_webhook, run_script (on-prem agent)
   - Celery-based async execution
   - Execution history and logs

✅ ACCOUNTS & RBAC
   - Organization model (multi-tenant)
   - Roles: Owner, Admin, Member, Viewer
   - JWT authentication + refresh tokens
   - API key authentication (per organization)
   - User invitations (email-based)
   - Audit log for all auth events

✅ AUDIT LOGS
   - Immutable event store (append-only)
   - Covers: auth events, config changes, incidents, workflow executions
   - Filter/search by date, actor, event type, resource
   - Export to CSV

✅ PLUGIN SYSTEM
   - Slack (incoming webhook)
   - Generic webhook (custom integrations)
   - PagerDuty (API integration)
   - Plugin enable/disable per organization

✅ PUBLIC REST API
   - Versioned under /api/v1/
   - OpenAPI 3.0 specification (auto-generated via drf-spectacular)
   - Rate limiting (per API key and per user)
   - Pagination, filtering, ordering on all list endpoints

✅ PYTHON SDK
   - Auto-generated from OpenAPI spec
   - Published to PyPI as sentinelops-sdk
   - Covers monitoring, incidents, workflows, audit

✅ ON-PREMISES AGENT
   - Python agent (V1); Rust rewrite planned for V2
   - Collects internal service metrics
   - Executes automation scripts
   - Communicates with backend via mTLS (HTTPS + client certificate)
   - Configurable via YAML file

✅ DEPLOYMENT
   - Docker Compose (development + on-prem)
   - Docker images published to GitHub Container Registry
   - Environment-based configuration (.env)
   - Database migrations managed via Django migrations
   - SaaS deployment: single-region (EU-West)
```

### 4.2 Out of Scope — V1

```
❌ Mobile application
❌ GraphQL API
❌ Billing / Stripe integration (planned V2)
❌ Visual workflow builder UI
❌ Kubernetes Helm chart (planned V2)
❌ Teams integration (planned V2)
❌ AI anomaly detection
❌ Multi-region SaaS
❌ SAML/SSO
❌ On-prem agent written in Rust (V2 rewrite)
❌ Agent auto-update mechanism
```

---

## 5. Stakeholders

### 5.1 Core Team

| Role | Name | Responsibilities |
|------|------|----------------|
| **Project Lead & Backend Engineer** | Fares | Architecture, Django backend, API, infrastructure |
| **Frontend Engineer** | TBD | Next.js dashboard, WebSocket integration |
| **DevOps** | TBD (or Fares initially) | Docker, CI/CD, cloud deployment |

### 5.2 External Stakeholders

| Type | Description | Engagement |
|------|-------------|-----------|
| **Design Partners** | 2–3 early-access companies | Monthly feedback sessions; free access in exchange for structured feedback |
| **Community** | Open-source users (on-prem) | GitHub Issues; Discord community |
| **Potential Investors** | Angels / pre-seed funds | Quarterly update; demo access |

### 5.3 RACI Matrix (Key Decisions)

| Decision | Responsible | Accountable | Consulted | Informed |
|----------|-------------|------------|-----------|----------|
| Architecture changes | Fares | Fares | Design Partners | Community |
| Scope changes | Fares | Fares | Design Partners | — |
| Public API breaking changes | Fares | Fares | SDK users | All users |
| Security vulnerabilities | Fares | Fares | — | All users |
| Pricing model | Fares | Fares | Design Partners | Community |

---

## 6. Technology Stack

### 6.1 Backend

| Component | Technology | Justification |
|-----------|-----------|--------------|
| Web framework | **Django 5.x** | Mature, batteries-included, excellent ORM, admin |
| REST API | **Django REST Framework (DRF)** | Industry standard; serializers, viewsets, routers |
| Real-time | **Django Channels + Daphne** | WebSocket support on top of Django; ASGI |
| Async tasks | **Celery 5.x + Redis broker** | Mature, battle-tested, excellent monitoring (Flower) |
| Task scheduler | **Celery Beat** | Cron-like scheduling for checks + usage aggregation |
| Auth | **djangorestframework-simplejwt** | JWT with refresh token rotation |
| API documentation | **drf-spectacular** | OpenAPI 3.0 auto-generation |
| Multi-tenancy | **django-tenants** (schema-based) | PostgreSQL schema isolation per organization |
| Background monitoring | **Custom check engine** | Celery tasks dispatched by Beat scheduler |

### 6.2 Database & Storage

| Component | Technology | Justification |
|-----------|-----------|--------------|
| Primary DB | **PostgreSQL 16** | JSONB support; schema-based multi-tenancy; reliability |
| Cache + Broker | **Redis 7** | Celery broker; Django cache; WebSocket channel layer |
| File storage | **MinIO** (on-prem) / **AWS S3** (SaaS) | S3-compatible; export files (CSV, PDF) |

### 6.3 Frontend

| Component | Technology | Justification |
|-----------|-----------|--------------|
| Framework | **Next.js 14 (App Router)** | SSR/SSG; React ecosystem; TypeScript native |
| Language | **TypeScript** | Type safety; better DX; industry standard |
| UI Library | **shadcn/ui + Tailwind CSS** | Accessible, composable components; rapid development |
| Charts | **Recharts** | React-native charts; WebSocket-compatible |
| Real-time | **native WebSocket API** | Direct ws:// connection to Django Channels |
| State management | **Zustand** | Lightweight; no boilerplate |
| API client | **React Query (TanStack Query)** | Server state management; caching; auto-refetch |

> **Why Next.js over Django Templates?**  
> A SaaS product with real-time dashboards, live incident feeds, and interactive charts requires a reactive, component-driven UI. Next.js + TypeScript delivers significantly better hands-on experience aligned with industry expectations for SaaS frontend engineers, and enables proper separation of concerns between API and UI layers.

### 6.4 Infrastructure & DevOps

| Component | Technology | Justification |
|-----------|-----------|--------------|
| Containerization | **Docker + Docker Compose** | Reproducible environments; on-prem delivery |
| Reverse proxy | **Traefik** | Automatic TLS; routing by domain; Docker-native |
| CI/CD | **GitHub Actions** | Free tier; Docker build/push; test automation |
| Container registry | **GitHub Container Registry (GHCR)** | Free; integrated with GitHub Actions |
| SaaS hosting | **Hetzner Cloud** (initial) | Cost-effective; EU-region; good Postgres support |
| Observability | **Prometheus + Grafana** | SentinelOps monitors itself (dogfooding) |
| Structured logging | **structlog** | JSON logs; compatible with log aggregators |
| Distributed tracing | **OpenTelemetry + Jaeger** | Trace async tasks; API latency |

### 6.5 On-Premises Agent

| Component | Technology | Justification |
|-----------|-----------|--------------|
| Language | **Python 3.12** (V1) | Fast development; rich ecosystem; easy distribution |
| Distribution | **PyInstaller single binary** | No Python install required on target machine |
| Communication | **HTTPS + mTLS** (client certificates) | Mutual authentication; no shared secrets |
| Configuration | **YAML** | Human-readable; operator-friendly |
| V2 rewrite target | **Rust** | Binary size, performance, memory safety |

---

## 7. Project Organization

### 7.1 Repository Structure

```
sentinelops/
├── backend/                    # Django monolith
│   ├── sentinelops/            # Django project config
│   ├── apps/
│   │   ├── accounts/           # Auth, RBAC, multi-tenant
│   │   ├── monitoring/         # Services, checks, incidents
│   │   ├── automations/        # Workflows, triggers, actions
│   │   ├── compliance/         # Audit logs, policies
│   │   ├── plugins/            # Plugin system
│   │   └── billing/            # Stripe (V2)
│   ├── common/                 # Shared utilities, base models
│   ├── tests/                  # Test suite
│   └── requirements/           # requirements by env
│
├── frontend/                   # Next.js App Router
│   ├── app/                    # App router pages
│   ├── components/             # Shared components
│   ├── lib/                    # API client, utils
│   └── hooks/                  # Custom React hooks
│
├── agent/                      # On-prem agent
│   ├── collectors/             # Metric collectors
│   ├── executors/              # Script execution
│   └── transport/              # mTLS communication
│
├── infra/                      # Infrastructure as Code
│   ├── docker-compose.yml      # Local + on-prem
│   ├── docker-compose.prod.yml # SaaS production
│   └── traefik/                # Traefik config
│
├── docs/                       # Documentation
│   ├── 01-vision-concept.md
│   ├── 02-project-charter.md
│   ├── 03-requirements-specification.md
│   └── api/                    # API reference (generated)
│
└── .github/
    └── workflows/              # CI/CD pipelines
```

### 7.2 Development Workflow

- **Branching**: `main` (production) → `develop` → `feature/xxx`, `fix/xxx`
- **PR policy**: All changes via Pull Request; CI must pass; self-review for solo phase
- **Commit convention**: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **Versioning**: Semantic Versioning (MAJOR.MINOR.PATCH)
- **Release cadence**: Bi-weekly sprints; release tags on `main`

---

## 8. Constraints & Assumptions

### 8.1 Constraints

| # | Constraint | Impact |
|---|-----------|--------|
| C1 | Solo developer (initial phase) | Scope must be realistic; no parallel feature teams |
| C2 | 6-month V1 timeline | Strict MVP discipline; defer nice-to-haves aggressively |
| C3 | Budget constraint (bootstrapped) | Prefer open-source infrastructure; minimize cloud costs |
| C4 | On-prem agent must be single binary | No Python runtime assumption on customer machine |
| C5 | Public API must be backward-compatible | No breaking changes within a major version |
| C6 | GDPR compliance required | EU data residency; right to deletion; data processing agreements |

### 8.2 Assumptions

| # | Assumption | If Wrong |
|---|-----------|----------|
| A1 | PostgreSQL schema-based multi-tenancy is sufficient for V1 | May need to migrate to separate databases per tenant if isolation requirements increase |
| A2 | Python agent is fast enough for V1 check execution | Rust rewrite in V2 if performance becomes a bottleneck |
| A3 | Redis is available on all target on-prem environments | Provide bundled Redis in Docker Compose as fallback |
| A4 | Celery Beat is sufficient for check scheduling at V1 scale (<10K checks) | Switch to dedicated scheduler (APScheduler, or custom) if Beat becomes a bottleneck |
| A5 | Design partners will provide timely feedback | Add backup feedback mechanisms (usage analytics, session recordings) |

---

## 9. Risks & Mitigations

| # | Risk | Probability | Impact | Mitigation |
|---|------|------------|--------|-----------|
| R1 | Scope creep delays V1 | High | High | Hard scope freeze after month 2; weekly scope review |
| R2 | Multi-tenancy complexity underestimated | Medium | High | Spike on django-tenants in week 1; validate assumptions early |
| R3 | WebSocket scaling issues under load | Medium | Medium | Load test early; consider Redis channel layer sharding |
| R4 | mTLS agent communication complexity | Medium | Medium | Use well-established library (httpx + client certs); spike in week 2 |
| R5 | PostgreSQL schema migrations slow at scale | Low | High | Test migration performance with 100+ schemas in staging |
| R6 | Single developer burnout | Medium | High | Strict 40h/week; no weekend work; regular milestones = motivation |
| R7 | Design partners disengage | Low | Medium | Regular check-ins; show progress demos every 2 weeks |
| R8 | Celery Beat misses check intervals under load | Medium | High | Monitoring of Celery queue depth; alerting on task lag |
| R9 | Security vulnerability in public API | Low | Critical | OWASP Top 10 audit before launch; dependency scanning in CI |
| R10 | On-prem customers can't install agent | Medium | Medium | Docker-based agent packaging as fallback; clear docs |

---

## 10. Milestones & Timeline

### Phase 0 — Foundation (Weeks 1–2)
> **Goal:** Project skeleton, infrastructure, CI/CD, core models defined

- [ ] Django project scaffold with app structure
- [ ] PostgreSQL + Redis + Docker Compose running
- [ ] CI/CD pipeline (GitHub Actions): lint, test, build
- [ ] Authentication: JWT + multi-tenant middleware
- [ ] Base models: Organization, User, Membership, AuditLog
- [ ] Django admin configured

**Deliverable:** Running development environment; CI green

---

### Phase 1 — Monitoring Core (Weeks 3–7)
> **Goal:** Core monitoring engine working end-to-end

- [ ] Service, Check, Incident models
- [ ] Check engine: HTTP, TCP, Ping, Cron (Celery tasks)
- [ ] Celery Beat scheduler for periodic checks
- [ ] Incident lifecycle state machine
- [ ] REST API: /services/, /checks/, /incidents/
- [ ] Basic alert: email on incident open/close
- [ ] Unit tests: check engine, incident lifecycle

**Deliverable:** Monitoring API fully functional; email alerts working

---

### Phase 2 — Real-Time Dashboard (Weeks 8–11)
> **Goal:** Frontend dashboard with live data

- [ ] Next.js project scaffold (TypeScript + shadcn/ui)
- [ ] Auth flow (login, JWT, refresh)
- [ ] Dashboard: service health map
- [ ] Django Channels: WebSocket consumer for live updates
- [ ] Real-time latency + uptime charts (Recharts)
- [ ] Live incident feed (WebSocket)
- [ ] Historical charts (7-day, 30-day)

**Deliverable:** Live dashboard showing check results in real time

---

### Phase 3 — RBAC, Accounts & Multi-tenancy (Weeks 10–13)
> **Goal:** Production-grade access control

- [ ] Organization model with schema isolation (django-tenants)
- [ ] Role model: Owner, Admin, Member, Viewer
- [ ] Permission checks on all API endpoints
- [ ] User invitation flow (email + token)
- [ ] API key authentication
- [ ] Audit log: all config + auth events logged

**Deliverable:** Multi-tenant isolation verified; RBAC enforced on all endpoints

---

### Phase 4 — Automation & Plugins (Weeks 12–16)
> **Goal:** Workflow automation engine

- [ ] Workflow, Trigger, Action models
- [ ] Trigger: incident_opened, threshold_exceeded, heartbeat_missed
- [ ] Actions: send_email, send_slack, call_webhook
- [ ] Celery-based workflow executor
- [ ] Execution history + logs
- [ ] Plugin system: Slack, Webhook, PagerDuty
- [ ] Plugin enable/disable per org

**Deliverable:** End-to-end workflow test passing (incident → Slack notification)

---

### Phase 5 — On-Prem Agent (Weeks 14–18)
> **Goal:** Deployable agent with secure communication

- [ ] Agent scaffold (Python)
- [ ] mTLS communication (HTTPS + client certificates)
- [ ] Metric collectors: HTTP, TCP, Ping
- [ ] Script executor
- [ ] YAML configuration
- [ ] PyInstaller packaging (single binary)
- [ ] Agent registration API endpoint
- [ ] Integration test: agent → backend

**Deliverable:** Agent binary installable on Ubuntu/CentOS; data visible in dashboard

---

### Phase 6 — Hardening & Launch Prep (Weeks 17–24)
> **Goal:** Production-ready, public launch

- [ ] Security audit (OWASP Top 10)
- [ ] Performance testing (load test API, WebSocket, Celery)
- [ ] API documentation (OpenAPI spec, Swagger UI)
- [ ] Python SDK (auto-generated + manual polish)
- [ ] On-prem Docker Compose polish + docs
- [ ] Monitoring of SentinelOps itself (Prometheus + Grafana)
- [ ] Design partner onboarding (2–3 companies)
- [ ] Launch materials (README, Product Hunt post, HN post)

**Deliverable:** V1.0.0 tag; SaaS live; On-prem packages released

---

### Summary Timeline

```
Week:   1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
Phase:  [P0][──────P1──────][──────P2──────][───P3───][────P4────][──P5──][──────P6──────]
                                                ↑ P3 overlaps P2
                                                              ↑ P5 overlaps P4
```

---

## 11. Budget Envelope (Indicative)

### Infrastructure (SaaS hosting, monthly)

| Resource | Provider | Monthly Cost |
|----------|---------|-------------|
| Application server (4 vCPU, 8GB RAM) | Hetzner CX41 | ~€18 |
| PostgreSQL (managed) | Hetzner or Supabase free tier | €0–€25 |
| Redis | Hetzner (self-hosted) | ~€5 |
| Object storage (MinIO/S3) | Hetzner Volume | ~€5 |
| Traefik + TLS | Included in server | €0 |
| Domain + email | Namecheap + Mailgun | ~€5 |
| **Total infrastructure** | | **~€30–55/month** |

### Development Tools (annual)

| Tool | Cost |
|------|------|
| GitHub Pro | $4/month |
| Sentry (error tracking) | Free tier |
| Linear (project management) | Free tier |
| **Total tooling** | **~$50/year** |

---

## 12. Go/No-Go Criteria

Before declaring V1 production-ready, the following checklist must pass:

### Technical
- [ ] All Phase 1–5 milestones completed
- [ ] Test coverage ≥80% backend
- [ ] Zero OWASP Top 10 critical/high findings
- [ ] p95 API response time <200ms under 100 concurrent users
- [ ] WebSocket latency <500ms end-to-end
- [ ] Docker Compose install completes in <10 minutes (tested on clean Ubuntu 22.04)
- [ ] All public API endpoints documented

### Business
- [ ] At least 1 design partner has run SentinelOps in their environment for ≥2 weeks
- [ ] On-prem installation guide reviewed by someone who did NOT write it
- [ ] Python SDK published to PyPI and installable
- [ ] Privacy policy and terms of service published
- [ ] GDPR data processing documentation complete

---

*Document maintained by the SentinelOps project team.*  
*Next review: May 17, 2026*
