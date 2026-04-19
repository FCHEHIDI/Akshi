# SentinelOps — Refactoring Phase 0

4 refactors à faire dans l'ordre indiqué. Chacun est indépendant des autres.
Quand c'est fait, donne le diff ou la version finale et je corrige.

---

## RF-01 — `common/permissions.py` — Réparer `HasOrgPermission`

### Pourquoi

DRF résout les `permission_classes` en appelant `perm()` (sans argument) sur chaque
élément de la liste pour instancier la classe. Le design actuel avec `__init__(required_permission)` ne marche **que si tu passes une instance pré-construite** :

```python
# Fonctionne accidentellement (instance, pas classe) :
permission_classes = [IsAuthenticated, HasOrgPermission("monitoring:write")]

# Explose dès qu'un ViewSet l'utilise normalement :
permission_classes = [HasOrgPermission]   # DRF fait HasOrgPermission() → TypeError
```

Aussi, `ModelViewSet.get_permissions()` clone les classes — un `__init__` avec des
arguments requis est incompatible.

### Ce qu'il faut faire

Remplacer toute la classe `HasOrgPermission` par une **factory** qui retourne une
sous-classe de `BasePermission` avec `required_permission` comme attribut de classe.
Garder `ROLE_PERMISSIONS` tel quel, il est correct.

**Signature cible :**

```python
def make_org_permission(perm: str) -> type[BasePermission]:
    ...
```

**Utilisation dans les vues :**

```python
permission_classes = [IsAuthenticated, make_org_permission("monitoring:write")]
```

### Contraintes

- La factory doit donner un `__name__` lisible à la classe retournée (utile pour les
  logs DRF et les erreurs) : `HasOrgPermission_monitoring_write`.
- La logique `has_permission` reste identique : lire `request.membership`, lookup dans
  `ROLE_PERMISSIONS`, retourner `True/False`.
- Supprimer l'ancienne classe `HasOrgPermission` entièrement — ne pas laisser les deux.
- Mettre à jour les imports dans tous les fichiers qui importent `HasOrgPermission`
  (cherche dans `apps/accounts/views.py` et partout ailleurs).

---

## RF-02 — Créer `apps/accounts/redis_client.py`

### Pourquoi

`services.py` et `authentication.py` ont chacun leur propre factory Redis qui pointe
sur la même URL. Si `JWT_REFRESH_TOKEN_REDIS_URL` change, il faut le changer à deux
endroits. De plus, `services.py` recrée une **nouvelle connexion à chaque appel** —
c'est un leak de connexions sous charge.

```python
# services.py — BUG : nouveau client (= nouvelle connexion TCP) à chaque login
def _redis() -> redis.Redis:
    return redis.Redis.from_url(settings.JWT_REFRESH_TOKEN_REDIS_URL, ...)
```

### Ce qu'il faut faire

**Créer le fichier `apps/accounts/redis_client.py`** avec :

1. Un `ConnectionPool` initialisé une seule fois au niveau module.
2. Une fonction `get_token_redis() -> redis.Redis` qui retourne un client utilisant ce pool.

```python
# Structure attendue (implémente-la toi-même) :
import redis
from django.conf import settings

_pool: redis.ConnectionPool | None = None

def get_token_redis() -> redis.Redis:
    """Return a Redis client backed by a shared connection pool (DB for JWT tokens)."""
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(
            settings.JWT_REFRESH_TOKEN_REDIS_URL,
            decode_responses=True,
        )
    return redis.Redis(connection_pool=_pool)
```

Ensuite **mettre à jour les deux fichiers consommateurs** :

**`apps/accounts/services.py`** :
- Supprimer la fonction `_redis()` et l'import `redis` au niveau module si plus utilisé directement.
- Ajouter `from apps.accounts.redis_client import get_token_redis`.
- Remplacer tous les appels `_redis()` → `get_token_redis()`.

**`apps/accounts/authentication.py`** :
- Supprimer le bloc `_redis_client: redis.Redis | None = None` et la fonction `_get_redis()`.
- Ajouter `from apps.accounts.redis_client import get_token_redis`.
- Remplacer tous les appels `_get_redis()` → `get_token_redis()`.

### Contraintes

- Le pool doit être lazy (initialisé au premier appel, pas à l'import) pour ne pas
  crasher lors du `manage.py check` si Redis n'est pas démarré.
- `decode_responses=True` doit rester — le code existant lit des strings.

---

## RF-03 — `common/audit.py` — Durcir la résolution de `actor`

### Pourquoi

L'`actor` est résolu par une heuristique fragile basée sur la position des arguments :

```python
actor = kwargs.get("actor") or (args[1] if len(args) > 1 else None)
```

Si une fonction décorée n'est pas une méthode (pas de `self`), `args[1]` est le
**deuxième paramètre positionnel**, pas l'actor. Si la signature est refactorée,
les audits échouent silencieusement avec `actor=None` — impossible à détecter.

### Ce qu'il faut faire

Modifier `wrapper` pour que `actor` soit **obligatoirement passé en keyword argument**.
Si `actor` n'est pas trouvé dans `kwargs`, logger un warning explicite (ne pas lever
d'exception — l'audit ne doit jamais casser l'opération principale).

**Logique cible :**

```python
actor = kwargs.get("actor")
if actor is None:
    logger.warning(
        "audit_action(%s): 'actor' keyword argument not found, AuditEvent will have no actor. "
        "Decorated function: %s",
        action,
        func.__qualname__,
    )
```

Supprimer la ligne `or (args[1] if len(args) > 1 else None)` entièrement.

### Contraintes

- Ne jamais lever d'exception dans le decorator — le `try/except` existant autour de
  `AuditEvent.objects.create()` doit rester.
- Le warning doit inclure `func.__qualname__` pour faciliter le debug.
- Si `actor is None`, continuer quand même la création de l'`AuditEvent` avec
  `actor_id=None` et `actor_email=""` — c'est le comportement actuel, à conserver.

---

## RF-04 — `sentinelops/settings/base.py` — Valider `SECRET_KEY`

### Pourquoi

`SECRET_KEY` a un fallback vide `""` :

```python
SECRET_KEY = os.environ.get("SECRET_KEY", "")
```

Django accepte une clé vide sans erreur. En staging ou prod, si la variable
d'environnement n'est pas injectée (oubli dans le `.env`, bug de déploiement),
**tous les JWT signés avec `""` sont identiques et prédictibles**. Un attaquant peut
signer ses propres tokens valides.

### Ce qu'il faut faire

Juste après la ligne `SECRET_KEY = os.environ.get(...)`, ajouter une validation
conditionnelle — **seulement si `DEBUG` est False** pour ne pas casser les tests
(`test.py` override `SECRET_KEY` après l'import de `base`).

```python
SECRET_KEY = os.environ.get("SECRET_KEY", "")

# Validation : ne s'applique qu'en prod/staging (DEBUG=False)
# test.py et development.py overrident SECRET_KEY après cet import.
if not DEBUG and not SECRET_KEY:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        "SECRET_KEY environment variable must be set in production. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(50))\""
    )
```

### Contraintes

- La validation doit venir **après** la ligne `DEBUG = False` dans `base.py` — vérifier
  l'ordre actuel dans le fichier.
- Ne pas changer la valeur par défaut `""` — c'est voulu pour que `development.py`
  puisse fonctionner sans `SECRET_KEY` dans l'env (il override la valeur lui-même).
- `test.py` override `SECRET_KEY = "test-secret-key-not-for-production"` — ce RF ne
  doit pas casser les tests. Si `DEBUG=False` dans `test.py`, ajouter
  `SECRET_KEY` avant que `base.py` soit évalué ne suffira pas — il faudra peut-être
  aussi setter `DEBUG=True` dans `test.py`. Vérifie et ajuste.

---

## Ordre d'implémentation conseillé

```
RF-02 → RF-01 → RF-03 → RF-04
```

RF-02 en premier car RF-01 et les futurs views dépendent d'un client Redis fiable.
RF-04 en dernier car c'est le seul qui peut casser l'environnement si mal ordonné.

## Checklist de validation après chaque RF

Après chaque refactor, lancer :

```bash
cd /c/Users/Fares/Akshi/backend

# Check système Django (0 erreur attendu)
DATABASE_URL=postgres://sentinel:sentinel@127.0.0.1:5432/sentinelops \
SECRET_KEY=dev-secret \
python manage.py check

# Smoke test login (doit retourner access_token + refresh_token)
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "Host: acme.localhost" \
  -d '{"email":"admin@acme.example","password":"Admin1234!"}' | python -m json.tool
```
