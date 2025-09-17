"""
Performance monitoring and health checks for Authentication Cache Service

Provides comprehensive monitoring capabilities including performance statistics,
health checks, cache statistics, and utility operations for cache management.
"""

import time
import uuid
from typing import Any, Dict

from app.core.logging import get_logger

from .base import CacheStats

logger = get_logger(__name__)


class MonitoringMixin:
    """
    Mixin providing performance monitoring and health check functionality

    Handles:
    - Cache performance statistics
    - Health check operations
    - Cache utility operations (clear all, reset stats)

    Requires:
    - self.redis_cache
    - self.fallback_cache
    - self.stats (CacheStats)
    - self._request_times (deque)
    - self.activity_buffers (Dict)
    - self.last_buffer_flush (datetime)
    - self.invalidate_pattern()
    """

    # Performance Monitoring and Statistics

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        # Update cache size estimate
        if self.redis_cache.enabled:
            try:
                # This is an approximation - Redis doesn't provide exact memory usage per key
                self.stats.cache_size_estimate = (
                    len(self.activity_buffers) * 100
                )  # Rough estimate
            except Exception:
                pass

        fallback_stats = self.fallback_cache.get_stats()

        return {
            "redis_enabled": self.redis_cache.enabled,
            "total_requests": self.stats.total_requests,
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "errors": self.stats.errors,
            "hit_rate": self.stats.hit_rate,
            "error_rate": self.stats.error_rate,
            "average_response_time_ms": self.stats.average_response_time * 1000,
            "cache_size_estimate": self.stats.cache_size_estimate,
            "last_reset": self.stats.last_reset.isoformat(),
            "fallback_cache": fallback_stats,
            "activity_buffers": {
                "active_users": len(self.activity_buffers),
                "total_buffered_activities": sum(
                    len(activities) for activities in self.activity_buffers.values()
                ),
                "last_flush": self.last_buffer_flush.isoformat(),
            },
        }

    async def reset_stats(self) -> bool:
        """Reset cache statistics"""
        self.stats = CacheStats()
        self._request_times.clear()
        logger.info("Cache statistics reset")
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on cache systems"""
        health = {
            "status": "healthy",
            "redis": {"available": False, "latency_ms": None},
            "fallback": {"available": False, "size": 0},
            "issues": [],
        }

        # Test Redis
        if self.redis_cache.enabled:
            try:
                start_time = time.time()
                test_key = f"health_check_{uuid.uuid4().hex[:8]}"

                # Test write
                await self.redis_cache.set(test_key, "health_check_value", ttl=10)

                # Test read
                await self.redis_cache.get(test_key)

                # Test delete
                await self.redis_cache.delete(test_key)

                latency = (time.time() - start_time) * 1000
                health["redis"]["available"] = True
                health["redis"]["latency_ms"] = round(latency, 2)

                if latency > 1000:  # More than 1 second
                    health["issues"].append(f"High Redis latency: {latency:.2f}ms")

            except Exception as e:
                health["redis"]["available"] = False
                health["issues"].append(f"Redis error: {str(e)}")

        # Test fallback cache
        try:
            test_key = f"health_check_{uuid.uuid4().hex[:8]}"
            await self.fallback_cache.set(test_key, "health_check_value", ttl=10)
            await self.fallback_cache.get(test_key)
            await self.fallback_cache.delete(test_key)

            fallback_stats = self.fallback_cache.get_stats()
            health["fallback"]["available"] = True
            health["fallback"]["size"] = fallback_stats["size"]

            # Check if fallback cache is getting full
            if fallback_stats["utilization"] > 90:
                health["issues"].append(
                    f"Fallback cache utilization high: {fallback_stats['utilization']:.1f}%"
                )

        except Exception as e:
            health["fallback"]["available"] = False
            health["issues"].append(f"Fallback cache error: {str(e)}")

        # Overall health status
        if not health["redis"]["available"] and not health["fallback"]["available"]:
            health["status"] = "critical"
        elif not health["redis"]["available"]:
            health["status"] = "degraded"
        elif health["issues"]:
            health["status"] = "warning"

        return health

    # Utility Methods

    async def clear_all_caches(self) -> bool:
        """Clear all cached data (use with caution)"""
        success = True

        # Clear Redis cache
        if self.redis_cache.enabled:
            try:
                # Clear auth-related patterns (following naming conventions)
                patterns = [
                    "v1:user:*:session",
                    "v1:user:*:context",
                    "v1:user:*:clients",
                    "v1:client:*:engagements",
                    "v1:user:*:activity:buffer",
                ]

                for pattern in patterns:
                    deleted = await self.invalidate_pattern(pattern)
                    logger.info(f"Cleared {deleted} entries for pattern: {pattern}")

            except Exception as e:
                logger.error(f"Error clearing Redis cache: {e}")
                success = False

        # Clear fallback cache
        try:
            await self.fallback_cache.clear()
        except Exception as e:
            logger.error(f"Error clearing fallback cache: {e}")
            success = False

        # Clear activity buffers
        self.activity_buffers.clear()

        # Reset stats
        await self.reset_stats()

        logger.info("All caches cleared")
        return success
