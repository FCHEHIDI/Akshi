#!/usr/bin/env bash
# =============================================================================
# docker-entrypoint.sh — SentinelOps container startup script
#
# Rôle : avant de lancer le process principal (web / worker / beat),
#        s'assurer que la base de données est prête et les migrations appliquées.
#
# Usage (défini dans docker-compose.yml) :
#   web    → ./docker-entrypoint.sh web
#   worker → ./docker-entrypoint.sh worker
#   beat   → ./docker-entrypoint.sh beat
# =============================================================================

set -e  # Stopper immédiatement si une commande échoue.

# ---------------------------------------------------------------------------
# 1. Attendre que PostgreSQL soit prêt
#    Docker lance les services en parallèle. Sans cette attente, Django
#    crasherait au démarrage car PG n'est pas encore accepter les connexions.
# ---------------------------------------------------------------------------
echo "[entrypoint] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
until python -c "
import socket, sys
s = socket.socket()
s.settimeout(1)
try:
    s.connect(('${DB_HOST}', ${DB_PORT}))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
"; do
  sleep 1
done
echo "[entrypoint] PostgreSQL is up."

# ---------------------------------------------------------------------------
# 2. Appliquer les migrations Django-tenants
#    migrate_schemas applique :
#      - les migrations partagées (schéma public)
#      - les migrations tenant (tous les schémas locataires existants)
#    C'est idempotent : safe à relancer à chaque démarrage.
# ---------------------------------------------------------------------------
echo "[entrypoint] Running migrate_schemas..."
python manage.py migrate_schemas --executor=multiprocessing
echo "[entrypoint] Migrations done."

# ---------------------------------------------------------------------------
# 3. Lancer le bon process selon le rôle du container
# ---------------------------------------------------------------------------
case "$1" in
  web)
    echo "[entrypoint] Starting Django web server (Daphne ASGI)..."
    # Daphne : serveur ASGI de Django Channels (gère HTTP + WebSocket).
    # -b 0.0.0.0 : écoute sur toutes les interfaces du container.
    # -p 8000    : port interne exposé.
    exec daphne -b 0.0.0.0 -p 8000 sentinelops.asgi:application
    ;;

  worker)
    echo "[entrypoint] Starting Celery worker (queue: checks)..."
    # -A sentinelops : application Celery définie dans sentinelops/celery.py
    # -Q checks      : ce worker ne traite QUE les tâches de la queue "checks"
    # --concurrency=4: 4 processus parallèles (ajuster selon les CPU dispo)
    # -l info        : niveau de log
    exec celery -A sentinelops worker -Q checks --concurrency=4 -l info
    ;;

  beat)
    echo "[entrypoint] Starting Celery Beat scheduler..."
    # Beat lit CELERY_BEAT_SCHEDULE et envoie dispatch_due_checks toutes les 30s.
    # --scheduler django_celery_beat.schedulers:DatabaseScheduler :
    #   stocke le planning en base (permet de modifier via Django admin).
    exec celery -A sentinelops beat -l info \
      --scheduler django_celery_beat.schedulers:DatabaseScheduler
    ;;

  *)
    echo "[entrypoint] Unknown role: '$1'. Use: web | worker | beat"
    exit 1
    ;;
esac
