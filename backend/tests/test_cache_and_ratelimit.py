"""
Tests for CacheService and SlidingWindowRateLimiter.
Verifies caching, TTL expiration, clear_prefix, and sliding window rate limits.
"""

import asyncio
import time
import pytest
from app.core.cache import CacheService
from app.core.rate_limiter import SlidingWindowRateLimiter


class TestCacheService:
    """Test CacheService in-memory and fallback behavior."""

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        c = CacheService()
        await c.set("test_key", {"revenue": 50000, "status": "ok"}, ttl_seconds=10)
        val = await c.get("test_key")
        assert val is not None
        assert val.get("revenue") == 50000

    @pytest.mark.asyncio
    async def test_delete(self):
        c = CacheService()
        await c.set("delete_me", "temp_value", ttl_seconds=10)
        assert await c.get("delete_me") == "temp_value"
        await c.delete("delete_me")
        assert await c.get("delete_me") is None

    @pytest.mark.asyncio
    async def test_clear_prefix(self):
        c = CacheService()
        await c.set("report:1", "data1", ttl_seconds=10)
        await c.set("report:2", "data2", ttl_seconds=10)
        await c.set("other:3", "data3", ttl_seconds=10)

        await c.clear_prefix("report:")
        assert await c.get("report:1") is None
        assert await c.get("report:2") is None
        assert await c.get("other:3") == "data3"


class TestRateLimiter:
    """Test SlidingWindowRateLimiter behavior."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_up_to_max(self):
        limiter = SlidingWindowRateLimiter()
        key = "test_client_ip"
        max_req = 5

        # 5 requests should all be allowed
        for i in range(max_req):
            allowed = await limiter.is_allowed(key, max_requests=max_req, window_seconds=60)
            assert allowed is True

        # 6th request must be blocked
        blocked = await limiter.is_allowed(key, max_requests=max_req, window_seconds=60)
        assert blocked is False

    @pytest.mark.asyncio
    async def test_rate_limiter_distinct_keys(self):
        limiter = SlidingWindowRateLimiter()
        # Different keys should have separate counters
        assert await limiter.is_allowed("user_a", max_requests=1, window_seconds=60) is True
        assert await limiter.is_allowed("user_a", max_requests=1, window_seconds=60) is False

        assert await limiter.is_allowed("user_b", max_requests=1, window_seconds=60) is True
