"""
Redis Cache Service with Upstash and Local Redis Support

This service provides a unified interface for Redis caching with support for:
- Upstash Redis (for production)
- redis.asyncio (for local async Redis)
- Synchronous Redis fallback (wrapped in async)
- In-memory fallback when Redis is unavailable

The service is modularized into:
- base: Core client initialization and basic operations
- locking: Distributed locking operations
- flows: Flow state and metadata caching
- imports: Import sample caching
- failures: Failure handling and dead letter queue
- patterns: Pattern learning cache
- sse: Server-sent events client registry
- wrappers: Async compatibility for sync clients
- serializers: JSON serialization/deserialization utilities
- utils: Utility functions and decorators
"""

from .core import RedisCache
from .serializers import datetime_json_deserializer, datetime_json_serializer
from .utils import redis_fallback
from .wrappers import AsyncPipelineWrapper, AsyncRedisWrapper

# Singleton instance
_redis_cache_instance = None


def get_redis_cache() -> RedisCache:
    """Get singleton Redis cache instance"""
    global _redis_cache_instance
    if _redis_cache_instance is None:
        _redis_cache_instance = RedisCache()
    return _redis_cache_instance


# Global instance for easy importing
redis_cache = get_redis_cache()

# Public API - maintain backward compatibility
__all__ = [
    "RedisCache",
    "get_redis_cache",
    "redis_cache",
    "datetime_json_serializer",
    "datetime_json_deserializer",
    "redis_fallback",
    "AsyncRedisWrapper",
    "AsyncPipelineWrapper",
]
