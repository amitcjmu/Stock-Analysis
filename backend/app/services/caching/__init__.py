"""
Caching services for the AI Modernize Migration Platform.

This module provides Redis-based caching for:
- Flow state management
- SSE connection registry
- Agent result caching
- Pattern learning cache
"""

from .redis_cache import RedisCache, get_redis_cache

__all__ = ["get_redis_cache", "RedisCache"]
