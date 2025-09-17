"""
Authentication Cache Service

High-performance Redis-based caching service for authentication and user context data.
Provides multi-layered caching with encryption for sensitive data, performance monitoring,
and graceful fallback when Redis is unavailable.

This module has been modularized for better organization while maintaining complete
backward compatibility. All previous imports will continue to work exactly as before.

Key Features:
- User session caching with TTL management
- Context data caching (clients, engagements, flows)
- Batched storage operations with debouncing
- Cache invalidation strategies
- Multi-layered fallback (Redis → In-Memory → Database)
- Performance monitoring hooks
- Comprehensive error handling and logging

Cache Key Schema:
- v1:user:{userId}:session           # User session data (TTL: 24h)
- v1:user:{userId}:context           # User context (TTL: 15m)
- v1:user:{userId}:clients           # Client list cache (TTL: 1h)
- v1:client:{clientId}:engagements   # Engagement cache (TTL: 30m)
- v1:user:{userId}:activity:buffer   # Activity buffer for batching
"""

from collections import defaultdict, deque
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.services.caching.redis_cache import get_redis_cache

# Import all components from modular structure
from .activity_management import ActivityManagementMixin
from .base import (
    CacheStats,
    CacheTTL,
    CacheKeys,
    InMemoryFallbackCache,
    UserContext,
    UserSession,
)
from .cache_operations import CacheOperationsMixin
from .client_management import ClientManagementMixin
from .invalidation_strategies import InvalidationStrategiesMixin
from .monitoring import MonitoringMixin
from .session_management import SessionManagementMixin

logger = get_logger(__name__)


class AuthCacheService(
    CacheOperationsMixin,
    SessionManagementMixin,
    ClientManagementMixin,
    ActivityManagementMixin,
    InvalidationStrategiesMixin,
    MonitoringMixin,
):
    """
    Authentication Cache Service

    Provides high-performance caching for authentication and user context data
    with encryption, fallback strategies, and performance monitoring.

    This class is assembled from multiple mixins for better organization while
    maintaining all existing functionality and method signatures.
    """

    # Preserve original constants for backward compatibility
    TTL_USER_SESSION = CacheTTL.USER_SESSION
    TTL_USER_CONTEXT = CacheTTL.USER_CONTEXT
    TTL_CLIENT_LIST = CacheTTL.CLIENT_LIST
    TTL_ENGAGEMENTS = CacheTTL.ENGAGEMENTS
    TTL_ACTIVITY_BUFFER = CacheTTL.ACTIVITY_BUFFER

    # Preserve original key templates for backward compatibility
    KEY_USER_SESSION = CacheKeys.USER_SESSION
    KEY_USER_CONTEXT = CacheKeys.USER_CONTEXT
    KEY_USER_CLIENTS = CacheKeys.USER_CLIENTS
    KEY_CLIENT_ENGAGEMENTS = CacheKeys.CLIENT_ENGAGEMENTS
    KEY_ACTIVITY_BUFFER = CacheKeys.ACTIVITY_BUFFER
    KEY_AUTH_STATS = CacheKeys.AUTH_STATS

    def __init__(self):
        self.redis_cache = get_redis_cache()
        self.fallback_cache = InMemoryFallbackCache()
        self.stats = CacheStats()
        self.activity_buffers = defaultdict(list)
        self.last_buffer_flush = datetime.utcnow()
        self.enabled = settings.REDIS_ENABLED

        # Performance monitoring
        self._request_times = deque(maxlen=1000)  # Keep last 1000 request times

        logger.info(f"AuthCacheService initialized - Redis enabled: {self.enabled}")


# Singleton instance for backward compatibility
_auth_cache_service = None


def get_auth_cache_service() -> AuthCacheService:
    """Get singleton AuthCacheService instance"""
    global _auth_cache_service
    if _auth_cache_service is None:
        _auth_cache_service = AuthCacheService()
    return _auth_cache_service


# Export all public classes and functions for backward compatibility
__all__ = [
    # Main service class and factory
    "AuthCacheService",
    "get_auth_cache_service",
    # Data classes
    "CacheStats",
    "UserSession",
    "UserContext",
    # Infrastructure classes (exposed for advanced usage)
    "InMemoryFallbackCache",
    # Constants (exposed for advanced configuration)
    "CacheTTL",
    "CacheKeys",
    # Mixins (exposed for potential extension)
    "CacheOperationsMixin",
    "SessionManagementMixin",
    "ClientManagementMixin",
    "ActivityManagementMixin",
    "InvalidationStrategiesMixin",
    "MonitoringMixin",
]
