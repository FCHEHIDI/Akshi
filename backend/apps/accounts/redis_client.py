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