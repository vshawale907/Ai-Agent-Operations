"""
Caching Service with Redis integration and in-memory fallback.

Provides fast key-value caching for repeated queries, analytics metrics,
and schema metadata. Uses Redis when configured and reachable, with seamless
in-memory fallback for local development or testing.
"""

import json
import time
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheEntry:
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expires_at = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class CacheService:
    """Production-grade TTL caching service with Redis and in-memory fallback."""

    def __init__(self):
        self._memory_store: Dict[str, CacheEntry] = {}
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
            logger.info(f"Connected to Redis cache at {settings.redis_url}")
        except Exception as e:
            logger.info(f"Redis unavailable ({e}), using in-memory cache fallback")
            self._redis = None

        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache if not expired."""
        redis_client = await self._get_redis()
        if redis_client:
            try:
                raw = await redis_client.get(key)
                if raw is not None:
                    try:
                        return json.loads(raw)
                    except (json.JSONDecodeError, TypeError):
                        return raw
                return None
            except Exception as e:
                logger.warning(f"Redis get failed, falling back to memory: {e}")

        # In-memory fallback
        entry = self._memory_store.get(key)
        if entry is None:
            return None

        if entry.is_expired():
            del self._memory_store[key]
            return None

        return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Store value with expiration in seconds."""
        redis_client = await self._get_redis()
        if redis_client:
            try:
                serialized = json.dumps(value) if not isinstance(value, str) else value
                await redis_client.set(key, serialized, ex=ttl_seconds)
                return
            except Exception as e:
                logger.warning(f"Redis set failed, falling back to memory: {e}")

        # In-memory fallback
        if len(self._memory_store) > 1000:
            now = time.time()
            expired = [k for k, v in self._memory_store.items() if v.expires_at < now]
            for k in expired:
                del self._memory_store[k]

        self._memory_store[key] = CacheEntry(value, ttl_seconds)

    async def delete(self, key: str) -> None:
        """Remove a key from cache."""
        redis_client = await self._get_redis()
        if redis_client:
            try:
                await redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        self._memory_store.pop(key, None)

    async def clear_prefix(self, prefix: str) -> None:
        """Invalidate all keys starting with prefix."""
        redis_client = await self._get_redis()
        if redis_client:
            try:
                cursor = 0
                while True:
                    cursor, keys = await redis_client.scan(cursor=cursor, match=f"{prefix}*", count=100)
                    if keys:
                        await redis_client.delete(*keys)
                    if cursor == 0:
                        break
            except Exception as e:
                logger.warning(f"Redis clear_prefix failed: {e}")

        matching = [k for k in self._memory_store.keys() if k.startswith(prefix)]
        for k in matching:
            del self._memory_store[k]

    async def close(self) -> None:
        """Close Redis connection pool on shutdown."""
        if self._redis:
            try:
                await self._redis.aclose()
            except Exception:
                pass
            self._redis = None
            self._redis_checked = False


cache = CacheService()
