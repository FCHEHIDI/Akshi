# SentinelOps — Vision & Concept Document

**Version:** 1.0  
**Date:** April 17, 2026  
**Status:** Draft  
**Author:** Fares  
**Classification:** Internal — Product

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Solution Overview](#3-solution-overview)
4. [Target Market & Personas](#4-target-market--personas)
5. [Market Positioning](#5-market-positioning)
6. [Key Differentiators](#6-key-differentiators)
7. [Product Philosophy](#7-product-philosophy)
8. [High-Level Feature Map](#8-high-level-feature-map)
9. [Deployment Models](#9-deployment-models)
10. [Monetization Vision](#10-monetization-vision)
11. [Strategic Roadmap (3 Horizons)](#11-strategic-roadmap-3-horizons)

---

## 1. Executive Summary

**SentinelOps** is a B2B infrastructure intelligence platform that unifies service monitoring, workflow automation, and compliance management for hybrid IT environments.

It is designed for engineering and DevOps teams who operate services across cloud, on-premises, or mixed infrastructure — and who need a single, self-hostable platform that gives them observability, automated remediation, and audit-grade accountability.

> **Tagline:** _Know everything. Fix anything. Prove compliance._

---

## 2. Problem Statement

### 2.1 The Landscape

Modern engineering teams operate infrastructure that spans cloud providers, on-premises data centers, and edge environments. They rely on a fragmented stack of disconnected tools:

- **Monitoring** (Uptime Robot, Pingdom, Datadog) — often SaaS-only, expensive at scale
- **Alerting** (PagerDuty, OpsGenie) — bolt-on, no workflow logic
- **Automation** (n8n, Zapier) — general-purpose, not infra-aware
- **Audit/Compliance** (manual exports, spreadsheets) — painful and error-prone

### 2.2 The Pain Points

| Pain | Who Feels It | Current Workaround |
|------|-------------|-------------------|
| No single view of service health across hybrid infra | DevOps lead, SRE | Multiple dashboards, manual correlation |
| Alerts fire but no automated remediation | On-call engineer | Manual runbooks, human response at 3 AM |
| Compliance audits require manual log aggregation | Security/Compliance officer | CSV exports, spreadsheets |
| SaaS tools can't be self-hosted (data sovereignty) | Enterprise IT | Either accept it or build in-house |
| Multi-team environments lack fine-grained access control | Platform engineer | Shared credentials, no audit trail |

### 2.3 The Gap

No existing tool covers the full loop:  
**Detect → Alert → Automate → Audit**  
...in a single product that can be deployed on-premises with enterprise-grade RBAC and multi-tenancy.

---

## 3. Solution Overview

SentinelOps closes this gap by providing:

```
┌─────────────────────────────────────────────────────────────────┐
│                        SentinelOps Platform                     │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  Monitoring  │  │  Automation  │  │  Compliance & Audit   │  │
│  │             │  │              │  │                       │  │
│  │ HTTP checks │  │  Workflows   │  │  Immutable audit logs │  │
│  │ TCP/Ping    │  │  Triggers    │  │  Policy enforcement   │  │
│  │ Cron health │  │  Actions     │  │  PDF/CSV export       │  │
│  │ Real-time   │  │  Celery orch │  │  Non-compliance alerts│  │
│  └─────────────┘  └──────────────┘  └───────────────────────┘  │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Accounts &  │  │   Plugins    │  │       Billing         │  │
│  │    RBAC     │  │              │  │                       │  │
│  │ Multi-tenant│  │ Slack, Teams │  │  Stripe-based         │  │
│  │ JWT + OAuth │  │ PagerDuty    │  │  Usage-based tiers    │  │
│  │ Invitations │  │ Webhooks     │  │  On-prem license      │  │
│  └─────────────┘  └──────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │                                           │
          ▼                                           ▼
  ┌──────────────┐                         ┌─────────────────┐
  │  SaaS Cloud  │                         │  On-Prem Agent  │
  │  (hosted)    │                         │  (Rust/Python)  │
  └──────────────┘                         └─────────────────┘
```

The platform operates in two complementary modes:
- **SaaS**: Managed cloud deployment, zero infrastructure management for the customer
- **On-Prem**: Full self-hosting with a local agent for metric collection inside private networks

---

## 4. Target Market & Personas

### 4.1 Primary Market

**Segment:** Mid-market to Enterprise B2B  
**Verticals:** FinTech, HealthTech, GovTech, SaaS companies, Managed Service Providers (MSPs)  
**Team size:** 20–500 engineers  
**Infrastructure:** Hybrid (cloud + on-prem) or regulated environments requiring data sovereignty

### 4.2 Personas

---

**Persona 1 — Alex, SRE / DevOps Lead**

> _"I manage 80+ services across AWS and our own datacenter. I need one dashboard that tells me exactly what's broken and why, without switching between 5 tools."_

- **Goal:** Centralized observability, fast MTTR
- **Pain:** Alert fatigue, manual correlation, no automated remediation
- **Uses SentinelOps for:** Monitoring, real-time dashboards, automation workflows, on-call integrations

---

**Persona 2 — Sarah, Platform Engineer**

> _"We have 12 teams sharing the same infra. I need to control who sees what, who can do what, and have a full audit trail when something goes wrong."_

- **Goal:** Access control, auditability, multi-team isolation
- **Pain:** Shared admin credentials, no visibility on who changed what
- **Uses SentinelOps for:** RBAC, multi-tenant organizations, audit logs, policy engine

---

**Persona 3 — Marcus, CISO / Security Lead**

> _"Our enterprise clients demand SOC2 compliance reports. I need immutable audit logs I can export on demand, not a spreadsheet I manually maintain."_

- **Goal:** Compliance evidence, regulatory readiness
- **Pain:** Log aggregation is manual, no policy enforcement automation
- **Uses SentinelOps for:** Compliance module, policy engine, audit export (PDF/CSV)

---

**Persona 4 — Layla, CTO of a 50-person SaaS startup**

> _"Datadog is burning $8K/month and we only use 20% of it. I want something self-hostable that our team actually understands."_

- **Goal:** Cost control, visibility, self-hosting capability
- **Pain:** Enterprise tools over-priced and over-engineered
- **Uses SentinelOps for:** On-Prem deployment, full feature set at fraction of SaaS cost

---

### 4.3 Total Addressable Market (Indicative)

| Segment | Est. Market Size |
|---------|-----------------|
| Infrastructure monitoring tools | ~$5B globally (2025) |
| IT automation/orchestration | ~$8B globally (2025) |
| IT compliance management | ~$3B globally (2025) |
| **SentinelOps addressable overlap** | **~$1–2B (serviceable)** |

---

## 5. Market Positioning

### 5.1 Competitive Landscape

| Tool | Monitoring | Automation | Compliance | On-Prem | Multi-tenant | Price |
|------|-----------|-----------|-----------|---------|-------------|-------|
| Datadog | ★★★★★ | ★★★ | ★★★ | ✗ | ✗ | $$$$$ |
| New Relic | ★★★★ | ★★ | ★★★ | ✗ | ✗ | $$$$ |
| Uptime Robot | ★★★ | ✗ | ✗ | ✗ | ✗ | $ |
| n8n | ✗ | ★★★★ | ✗ | ✓ | ✗ | $$ |
| Grafana Stack | ★★★★ | ★★ | ★★ | ✓ | ✗ | $$$ |
| **SentinelOps** | **★★★★** | **★★★★** | **★★★★** | **✓** | **✓** | **$$** |

### 5.2 Positioning Statement

> *For DevOps and platform engineering teams operating hybrid infrastructure,*  
> *SentinelOps is the unified monitoring + automation + compliance platform*  
> *that — unlike Datadog or Grafana — can be fully self-hosted, is natively multi-tenant,*  
> *and closes the loop from incident detection to automated remediation to audit-grade reporting.*

---

## 6. Key Differentiators

### D1 — Full Loop: Detect → Automate → Audit
Most tools stop at alerting. SentinelOps closes the loop with workflow automation triggered by monitoring events, and every action is logged in an immutable audit trail.

### D2 — On-Prem First, SaaS Optional
Built from day one for self-hosting. Regulated industries (finance, health, government) can deploy entirely within their own infrastructure with no data leaving their perimeter.

### D3 — Native Multi-Tenancy
Not an afterthought. Organizations, projects, and roles are first-class citizens — built for MSPs managing multiple clients or enterprises with multiple business units.

### D4 — Lightweight On-Prem Agent
A small, efficient agent (Rust/Python) that runs inside private networks, collects metrics, and communicates back via mTLS — no firewall exceptions required beyond outbound HTTPS.

### D5 — Transparent, Usage-Based Pricing
Pricing tied to what you actually use (number of checks, data retention), not arbitrary "host units" or opaque enterprise pricing.

---

## 7. Product Philosophy

**1. Simplicity over completeness.**  
Every feature must earn its place. We prefer doing fewer things better than everything poorly.

**2. Observable by default.**  
SentinelOps itself is fully instrumented — Prometheus metrics, structured logs, OpenTelemetry traces. We eat our own dog food.

**3. API-first.**  
Every feature accessible through the UI is also accessible via API. The UI is just a client of our own API.

**4. Security is non-negotiable.**  
mTLS for agent communication, JWT with refresh rotation, RBAC with deny-by-default, immutable audit logs. These are not features — they are foundations.

**5. Operator-friendly.**  
One-command deployment. Clear upgrade paths. Good documentation. On-prem operators are first-class citizens.

---

## 8. High-Level Feature Map

### Core (V1 — Monitoring-First)

| Feature Area | Key Capabilities |
|-------------|----------------|
| **Service Monitoring** | HTTP, TCP, Ping, Cron health checks; configurable intervals; thresholds; incident lifecycle |
| **Real-time Dashboard** | WebSocket-powered latency/uptime feed; incident stream; service health map |
| **Alerting** | Multi-channel (email, Slack, webhook); escalation policies; alert deduplication |
| **Automation Workflows** | Event-triggered workflows; action library (notify, restart, script, webhook) |
| **Accounts & RBAC** | Multi-tenant organizations; granular role/permission model; JWT auth; API keys |
| **Audit Logs** | Immutable event store; filter/search; PDF/CSV export |
| **Plugin System** | Slack, Teams, PagerDuty, custom webhooks |
| **Public API** | Versioned REST API; OpenAPI spec; Python SDK |
| **On-Prem Agent** | Lightweight collector; mTLS communication; metric push |

### Extended (V2+)

| Feature Area | Key Capabilities |
|-------------|----------------|
| **Compliance Policies** | Policy engine; non-compliance detection; scheduled reports |
| **Billing** | Stripe integration; usage-based billing; self-serve upgrade/downgrade |
| **GraphQL API** | Alternative query interface for complex dashboard queries |
| **Advanced Automation** | Visual workflow builder; conditional branching; retry logic |
| **Multi-region SaaS** | Regional data residency; global status aggregation |

---

## 9. Deployment Models

### 9.1 SaaS (Cloud-Hosted)

```
Customer Browser
      │
      ▼
  Traefik (reverse proxy + TLS termination)
      │
      ├──► Next.js Frontend (Vercel or Docker)
      │
      └──► Django API Backend
                │
                ├──► PostgreSQL (managed, e.g. RDS / Supabase)
                ├──► Redis (cache + Celery broker)
                ├──► S3/MinIO (file storage)
                └──► Celery Workers
```

Customers access at `{org}.sentinelops.io`. No infrastructure management required.

### 9.2 On-Prem (Self-Hosted)

```
Customer's Private Network
      │
      ├── SentinelOps Stack (Docker Compose / Helm)
      │       ├── Django API
      │       ├── Next.js Frontend
      │       ├── PostgreSQL
      │       ├── Redis
      │       └── Celery Workers
      │
      └── SentinelOps Agent (lightweight binary)
              ├── Collects metrics from internal services
              ├── Executes remediation scripts
              └── Communicates via mTLS → API
```

Delivered as Docker Compose (quick start) and Helm chart (production Kubernetes).

---

## 10. Monetization Vision

### 10.1 Pricing Philosophy

SentinelOps uses a **hybrid pricing model**: a base subscription tier unlocks the platform, and usage-based components ensure pricing scales fairly with actual usage — avoiding the trap of flat-rate plans that punish small teams or subsidize large ones.

### 10.2 SaaS Pricing Tiers

| Plan | Target | Price (indicative) | Included |
|------|--------|-------------------|----------|
| **Starter** | Small teams, startups | $49/month | 1 org, 3 users, 50 checks, 7-day retention |
| **Pro** | Growing engineering teams | $199/month | 1 org, 15 users, 500 checks, 90-day retention |
| **Business** | Multi-team companies | $599/month | 5 orgs, unlimited users, 2000 checks, 1-year retention |
| **Enterprise** | Large orgs, regulated industries | Custom | Custom orgs/users/checks, SLA, SSO, dedicated support |

### 10.3 Usage-Based Overages (Pro & Business)

Beyond plan limits, customers pay for what they use:

| Dimension | Unit Price |
|-----------|-----------|
| Additional check | $0.10/check/month |
| Additional data retention | $5/30 days/month |
| Additional organization (multi-tenant) | $50/org/month |
| Additional API calls (beyond 100k/month) | $0.001/call |

### 10.4 On-Premises License

For customers who self-host, SentinelOps offers:

| License Type | Description | Price (indicative) |
|-------------|-------------|-------------------|
| **Community** | Open-source core, no support | Free |
| **Professional** | Full feature set, email support | $2,000/year |
| **Enterprise** | Full features + SLA + custom integrations + on-site support | $10,000+/year |

### 10.5 How Usage Is Measured

- **Checks**: Number of active monitoring checks configured in the system (HTTP, TCP, Ping, Cron)
- **Users/Seats**: Named users with login access (not API-key-only access)
- **Organizations**: Tenant isolation units — relevant for MSPs managing client environments
- **Data retention**: How far back incident and metric data is queryable
- **API calls**: Metered via API Gateway (rate limiting middleware in Django)

> _Billing events are generated by a background Celery task that runs usage aggregation nightly, stores snapshots in a `UsageRecord` model, and syncs with Stripe's usage-based billing API (`stripe.SubscriptionItem.create_usage_record`)._

---

## 11. Strategic Roadmap (3 Horizons)

### Horizon 1 — Foundation (Months 0–6)
**Goal:** Usable, deployable product with strong monitoring core

- [ ] Core monitoring engine (HTTP, TCP, Ping, Cron)
- [ ] Real-time dashboard (WebSocket)
- [ ] Incident lifecycle management
- [ ] Multi-tenant accounts + RBAC
- [ ] Basic automation workflows (notify actions)
- [ ] Audit logs (read-only)
- [ ] REST API V1 + Python SDK
- [ ] On-Prem agent (Python, basic metric push)
- [ ] Docker Compose deployment
- [ ] SaaS deployment on single region

### Horizon 2 — Growth (Months 6–12)
**Goal:** Production-hardened, commercially viable

- [ ] Compliance policy engine
- [ ] Billing integration (Stripe)
- [ ] Advanced workflow automation (visual builder)
- [ ] Plugin marketplace (Slack, Teams, PagerDuty)
- [ ] On-Prem agent rewrite in Rust (performance)
- [ ] Helm chart for Kubernetes deployment
- [ ] OpenTelemetry integration
- [ ] Self-serve onboarding flow

### Horizon 3 — Scale (Months 12–24)
**Goal:** Enterprise-ready, multi-region

- [ ] GraphQL API
- [ ] Multi-region SaaS (data residency)
- [ ] Advanced RBAC (attribute-based, ABAC)
- [ ] Enterprise SSO (SAML / OIDC)
- [ ] AI-powered anomaly detection
- [ ] Public plugin SDK (third-party contributions)
- [ ] SOC2 certification path

---

*Document maintained by the SentinelOps product team.*  
*Next review: May 17, 2026*
