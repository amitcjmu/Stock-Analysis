"""
Core cache operations for Authentication Cache Service

Contains the fundamental cache read/write/delete operations and performance monitoring
that are used as building blocks by all other cache service functionality.
"""

import time
from typing import Any, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheOperationsMixin:
    """
    Mixin providing core cache operations functionality

    Provides the fundamental cache operations that other mixins depend on:
    - Get/Set/Delete with fallback strategy
    - Performance monitoring and timing
    - Statistics tracking

    Requires:
    - self.redis_cache
    - self.fallback_cache
    - self.stats
    - self._request_times
    """

    async def _record_request_time(self, operation: str, start_time: float) -> None:
        """Record request timing for performance monitoring"""
        duration = time.time() - start_time
        self._request_times.append(duration)

        # Update running average (simple moving average)
        if len(self._request_times) > 0:
            self.stats.average_response_time = sum(self._request_times) / len(
                self._request_times
            )

        # Log slow operations
        if duration > 0.5:  # Log operations taking more than 500ms
            logger.warning(f"Slow cache operation: {operation} took {duration:.3f}s")

    async def _update_stats(self, hit: bool = False, error: bool = False) -> None:
        """Update cache statistics"""
        self.stats.total_requests += 1
        if hit:
            self.stats.hits += 1
        else:
            self.stats.misses += 1
        if error:
            self.stats.errors += 1

    async def _get_from_cache(self, key: str, use_secure: bool = True) -> Optional[Any]:
        """
        Get value from cache with fallback strategy

        Fallback order: Redis (secure/regular) → In-Memory → None
        """
        start_time = time.time()

        try:
            # Try Redis first
            if self.redis_cache.enabled:
                if use_secure:
                    value = await self.redis_cache.get_secure(key)
                else:
                    value = await self.redis_cache.get(key)

                if value is not None:
                    await self._update_stats(hit=True)
                    await self._record_request_time(f"redis_get_{key}", start_time)
                    return value

            # Try in-memory fallback
            value = await self.fallback_cache.get(key)
            if value is not None:
                await self._update_stats(hit=True)
                await self._record_request_time(f"memory_get_{key}", start_time)
                logger.debug(f"Cache hit from in-memory fallback for key: {key}")
                return value

            # Cache miss
            await self._update_stats(hit=False)
            await self._record_request_time(f"miss_{key}", start_time)
            return None

        except Exception as e:
            await self._update_stats(error=True)
            logger.error(f"Error getting from cache key {key}: {e}")
            return None

    async def _set_to_cache(
        self, key: str, value: Any, ttl: Optional[int] = None, use_secure: bool = True
    ) -> bool:
        """
        Set value to cache with fallback strategy

        Attempts to set in both Redis and in-memory cache for redundancy
        """
        start_time = time.time()
        success = False

        try:
            # Try Redis first
            if self.redis_cache.enabled:
                if use_secure:
                    redis_success = await self.redis_cache.set_secure(key, value, ttl)
                else:
                    redis_success = await self.redis_cache.set(key, value, ttl)

                if redis_success:
                    success = True
                    logger.debug(f"Successfully set cache key in Redis: {key}")

            # Always try to set in fallback cache as well
            fallback_success = await self.fallback_cache.set(key, value, ttl)
            if fallback_success and not success:
                success = True
                logger.debug(f"Successfully set cache key in fallback: {key}")

            await self._record_request_time(f"set_{key}", start_time)
            return success

        except Exception as e:
            await self._update_stats(error=True)
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    async def _delete_from_cache(self, key: str) -> bool:
        """Delete value from cache (both Redis and fallback)"""
        start_time = time.time()
        success = False

        try:
            # Delete from Redis
            if self.redis_cache.enabled:
                redis_success = await self.redis_cache.delete(key)
                if redis_success:
                    success = True

            # Delete from fallback cache
            fallback_success = await self.fallback_cache.delete(key)
            if fallback_success and not success:
                success = True

            await self._record_request_time(f"delete_{key}", start_time)
            return success

        except Exception as e:
            await self._update_stats(error=True)
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
