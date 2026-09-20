from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque

import redis.asyncio as redis

from app.core.config import settings


class RateLimitExceeded(Exception):
    pass


class RateLimiter:
    """Distributed Redis limiter with an in-process fallback."""

    def __init__(self):
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()
        self._redis = redis.from_url(settings.REDIS_URL) if settings.REDIS_URL else None

    async def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        if self._redis is None:
            return await self._allow_memory(key, limit, window_seconds)

        redis_key = "rate:" + key
        try:
            count = await self._redis.incr(redis_key)
            if count == 1:
                await self._redis.expire(redis_key, window_seconds)
            return count <= limit
        except redis.RedisError:
            return await self._allow_memory(key, limit, window_seconds)

    async def _allow_memory(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        async with self._lock:
            bucket = self._events[key]
            cutoff = now - window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True


limiter = RateLimiter()
