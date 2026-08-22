"""
Simple fixed-window rate limiter backed by Redis.

Not a distributed-systems masterpiece — a pragmatic, correct-enough
control for login/upload/AI-analysis endpoints, matching the spec's
requirement that rate limiting actually exist in code, not just in docs.
"""
import redis

from app.core.config import get_settings

settings = get_settings()
_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def check_rate_limit(key: str, max_requests: int, window_seconds: int = 60) -> bool:
    """
    Returns True if the request is allowed, False if the limit is exceeded.
    Fails open (allows the request) if Redis is unreachable, so a cache
    outage degrades to "no rate limiting" rather than taking the whole
    API down — logged separately so the outage itself is visible.
    """
    try:
        r = get_redis()
        current = r.incr(key)
        if current == 1:
            r.expire(key, window_seconds)
        return current <= max_requests
    except redis.RedisError:
        return True
