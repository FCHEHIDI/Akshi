# SentinelOps

> Plateforme de monitoring d'infrastructure multi-tenant — Phase 1 complète.

SentinelOps surveille en continu des services (HTTP, TCP, ping), déclenche des incidents, envoie des notifications et expose une API REST complète — le tout en mode multi-tenant (un schéma PostgreSQL par organisation).

---

## Stack technique

| Couche | Technologie |
|---|---|
| Backend | Django 5.2 + Django REST Framework |
| Multi-tenancy | django-tenants 3.10 (schéma PostgreSQL par tenant) |
| Serveur ASGI | Daphne 4 + Django Channels 4 |
| Tâches async | Celery 5 + django-celery-beat |
| Broker / Cache | Redis 7 |
| Base de données | PostgreSQL 17 |
| Auth | JWT (simplejwt) + Redis token store |
| Conteneurs | Docker Compose v2 |

---

## Démarrage rapide (Docker)

**Prérequis :** Docker Desktop installé et démarré.

```bash
# 1. Cloner le repo
git clone https://github.com/FCHEHIDI/Akshi.git
cd Akshi

# 2. Créer le fichier d'environnement
cp .env.docker.example .env.docker   # puis éditer si besoin

# 3. Build + démarrage (premier lancement ~3 min)
docker compose --env-file .env.docker up --build

# 4. Créer le tenant de démo (dans un autre terminal)
docker compose exec web python manage.py create_tenant \
  --schema_name=acme \
  --name="Acme Corp" \
  --domain-domain=acme.localhost \
  --domain-is_primary=True
```

L'API est disponible sur **http://localhost:8000/api/v1/**.

---

## Démarrage local (sans Docker)

```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate  # Windows
pip install -r requirements/development.txt

# Variables d'environnement
export DJANGO_SETTINGS_MODULE=sentinelops.settings.development
export DATABASE_URL=postgres://sentinel:sentinel@127.0.0.1:5432/sentinelops
export SECRET_KEY=dev-secret

python manage.py migrate_schemas --executor=multiprocessing
python manage.py runserver          # terminal 1
celery -A sentinelops worker -Q checks --concurrency=4  # terminal 2
celery -A sentinelops beat --scheduler django_celery_beat.schedulers:DatabaseScheduler  # terminal 3
```

---

## Architecture Docker Compose

```
┌──────────────────────────────────────────────────┐
│                  sentinelops_net                 │
│                                                  │
│  ┌───────┐   ┌───────┐   ┌────────────────────┐ │
│  │  db   │   │ redis │   │        web         │ │
│  │ PG 17 │   │  R 7  │   │  Django / Daphne   │─┼─► :8000
│  └───────┘   └───────┘   │    port 8000       │ │
│      ▲            ▲      └────────────────────┘ │
│      │            │      ┌────────────────────┐ │
│      └────────────┼──────│       worker       │ │
│                   │      │  Celery (Q:checks) │ │
│                   │      └────────────────────┘ │
│                   │      ┌────────────────────┐ │
│                   └──────│        beat        │ │
│                          │   Celery Beat      │ │
│                          └────────────────────┘ │
└──────────────────────────────────────────────────┘
```

Chaque service `web`, `worker` et `beat` utilise la même image mais un point d'entrée différent (`docker-entrypoint.sh web|worker|beat`).

---

## API REST — Endpoints

Base URL : `/api/v1/`

### Auth
| Méthode | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register/` | Créer un compte |
| `POST` | `/auth/login/` | Obtenir access + refresh token |
| `POST` | `/auth/refresh/` | Renouveler l'access token |
| `POST` | `/auth/logout/` | Révoquer le token (Redis) |

### Services
| Méthode | Endpoint | Description |
|---|---|---|
| `GET/POST` | `/services/` | Lister / créer des services |
| `GET/PUT/PATCH/DELETE` | `/services/<id>/` | Détail d'un service |

### Health Checks
| Méthode | Endpoint | Description |
|---|---|---|
| `GET/POST` | `/services/<id>/checks/` | Checks d'un service |
| `GET/PUT/PATCH/DELETE` | `/services/<id>/checks/<id>/` | Détail d'un check |
| `GET` | `/checks/<id>/results/` | Historique des résultats |

### Incidents
| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/incidents/` | Lister les incidents actifs |
| `POST` | `/incidents/<id>/acknowledge/` | Acquitter un incident |
| `POST` | `/incidents/<id>/resolve/` | Résoudre un incident |

### Canaux de notification
| Méthode | Endpoint | Description |
|---|---|---|
| `GET/POST` | `/notification-channels/` | Lister / créer des canaux |
| `GET/PUT/PATCH/DELETE` | `/notification-channels/<id>/` | Détail d'un canal |

---

## Modèles de données

```
Organization (tenant)
  └── Domain

Service
  └── Check (HTTP / TCP / Ping)
        └── CheckResult (historique)
              └── Incident (machine à états)
                    └── state: open → acknowledged → resolved

NotificationChannel
  - channel_type: slack | email | webhook
  - config: {"url": "..."} | {"to": ["..."]}
  - filtres: min_severity, notify_on_open, notify_on_resolve
```

---

## Types de checks

| Type | Ce qui est vérifié | Protocole |
|---|---|---|
| `http` | Status code HTTP (attendu vs reçu) | HTTPX |
| `tcp` | Connexion TCP sur host:port | asyncio |
| `ping` | Réponse ICMP | icmplib |

---

## Cycle de vie des incidents

```
        [check échoue]
              │
              ▼
           OPEN ──────────────────────► ACKNOWLEDGED
              │                               │
     [échecs répétés]               [équipe au courant]
     [montée en sévérité]                     │
              │                               │
              └─────────────► RESOLVED ◄──────┘
                           [check repasse OK]
```

À chaque transition, les `NotificationChannel` actifs sont notifiés (Celery task, 2 retries).

---

## Structure du projet

```
Akshi/
├── docker-compose.yml          # Orchestration 5 services
├── .env.docker                 # Variables d'env (non commité)
├── backend/
│   ├── Dockerfile
│   ├── docker-entrypoint.sh    # Boot web / worker / beat
│   ├── manage.py
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── test.txt
│   ├── apps/
│   │   ├── accounts/           # Multi-tenant auth + JWT
│   │   ├── monitoring/         # Services, Checks, Incidents, Notifications
│   │   ├── automations/        # (Phase 2)
│   │   ├── compliance/         # (Phase 2)
│   │   └── plugins/            # (Phase 2)
│   ├── common/                 # Modèles de base, permissions, pagination
│   └── sentinelops/
│       ├── settings/
│       │   ├── base.py
│       │   ├── development.py
│       │   └── production.py
│       ├── celery.py
│       ├── asgi.py
│       └── api_v1_urls.py
└── docs/
    ├── 01-vision-concept.md
    ├── 02-project-charter.md
    ├── 03-requirements-specification.md
    └── 04-architecture.md
```

---

## Roadmap

### Phase 1 — ✅ Complète
- [x] Bloc 1 — Executors HTTP / TCP / Ping
- [x] Bloc 2 — Tasks Celery (`run_check`, `dispatch_due_checks`)
- [x] Bloc 3 — Machine à états des incidents
- [x] Bloc 4 — API REST complète
- [x] Bloc 5 — Celery Beat (dispatch toutes les 30s)
- [x] Bloc 6 — Canaux de notification (Slack / Email / Webhook)
- [x] Docker Compose (web + worker + beat + db + redis)

### Phase 2 — Prochainement
- [ ] Mini-apps démo (FastAPI, Express) pour simuler des services réels
- [ ] Dashboard temps réel (WebSocket via Django Channels)
- [ ] Automations (actions déclenchées sur incident)
- [ ] Compliance checks
- [ ] Plugin system

### Écosystème long terme
- [ ] RevOps SaaS (corrélation pipeline commercial ↔ incidents infra)
- [ ] `mcp-sentinelops` — Serveur MCP exposant incidents et services comme outils
- [ ] `mcp-revops` — Serveur MCP exposant le pipeline deals
- [ ] Multi-agent system (LLM orchestrant les deux sources de données)

---

## Développement

```bash
# Tests
cd backend
pytest

# Linting
ruff check .
black --check .

# Migrations
python manage.py makemigrations
python manage.py migrate_schemas --executor=multiprocessing
```

---

## Commits

```
3356423  feat(monitoring/notifications): implement notification channels — Bloc 6
de9eeea  feat(celery/beat): add dispatch_due_checks periodic schedule — Bloc 5
f6f9e3d  feat(monitoring/api): implement REST API — Bloc 4
44a89ec  feat(monitoring/incidents): implement incident state machine
59a44da  feat(monitoring/tasks): implement dispatch_due_checks and run_check
809c675  feat(monitoring/executors): add HTTP, TCP and Ping check executors
```

---

## Licence

Usage privé — tous droits réservés.
