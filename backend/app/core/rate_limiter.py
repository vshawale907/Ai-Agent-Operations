"""
API Rate Limiting Middleware and Dependency.

Protects sensitive endpoints against abuse using Redis sliding-window
counter when available, with seamless in-memory sliding-window fallback.
Returns 429 Too Many Requests with informative retry headers.
"""

import time
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SlidingWindowRateLimiter:
    """Sliding-window rate limiter supporting Redis and in-memory fallback."""

    def __init__(self):
        # key -> list of request timestamps (in-memory fallback)
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._redis = None
        self._redis_checked = False

    async def _get_redis(self):
        """Lazily initialize Redis connection if available."""
        if self._redis_checked:
            return self._redis

        self._redis_checked = True
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=1.5,
                socket_connect_timeout=1.5,
            )
            await client.ping()
            self._redis = client
            logger.info("Rate limiter connected to Redis")
        except Exception as e:
            logger.info(f"Redis unavailable for rate limiter ({e}), using in-memory fallback")
            self._redis = None

        return self._redis

    async def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request under `key` is allowed within `window_seconds`."""
        now = time.time()
        cutoff = now - window_seconds

        redis_client = await self._get_redis()
        if redis_client:
            try:
                redis_key = f"ratelimit:{key}"
                pipe = redis_client.pipeline()
                pipe.zremrangebyscore(redis_key, 0, cutoff)
                pipe.zcard(redis_key)
                pipe.zadd(redis_key, {str(now): now})
                pipe.expire(redis_key, window_seconds + 5)
                results = await pipe.execute()

                current_count = results[1]
                if current_count >= max_requests:
                    return False
                return True
            except Exception as e:
                logger.warning(f"Redis rate check failed, falling back to memory: {e}")

        # In-memory sliding window fallback
        timestamps = self._requests[key]
        self._requests[key] = [ts for ts in timestamps if ts > cutoff]

        if len(self._requests[key]) >= max_requests:
            return False

        self._requests[key].append(now)
        return True


rate_limiter = SlidingWindowRateLimiter()


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """FastAPI dependency for rate limiting."""

    async def dependency(request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        key = f"{client_ip}:{request.url.path}"

        allowed = await rate_limiter.is_allowed(key, max_requests, window_seconds)
        if not allowed:
            logger.warning(f"Rate limit exceeded for {key} ({max_requests} req / {window_seconds}s)")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Allowed {max_requests} requests per {window_seconds} seconds.",
                headers={"Retry-After": str(window_seconds)},
            )

    return dependency
