"""
Authentication Cache Service

High-performance Redis-based caching service for authentication and user context data.
Provides multi-layered caching with encryption for sensitive data, performance monitoring,
and graceful fallback when Redis is unavailable.

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

import asyncio
import time
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security.cache_encryption import sanitize_for_logging, secure_setattr
from app.services.caching.redis_cache import get_redis_cache

logger = get_logger(__name__)


@dataclass
class CacheStats:
    """Cache performance statistics"""

    hits: int = 0
    misses: int = 0
    errors: int = 0
    total_requests: int = 0
    average_response_time: float = 0.0
    cache_size_estimate: int = 0
    last_reset: datetime = None

    def __post_init__(self):
        if self.last_reset is None:
            self.last_reset = datetime.utcnow()

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100

    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.errors / self.total_requests) * 100


@dataclass
class UserSession:
    """User session data structure"""

    user_id: str
    email: str
    full_name: str
    role: str
    is_admin: bool
    organization: Optional[str] = None
    role_description: Optional[str] = None
    associations: List[Dict[str, Any]] = None
    created_at: datetime = None
    last_accessed: datetime = None

    def __post_init__(self):
        if self.associations is None:
            self.associations = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_accessed is None:
            self.last_accessed = datetime.utcnow()


@dataclass
class UserContext:
    """User context data structure"""

    user_id: str
    active_client_id: Optional[str] = None
    active_engagement_id: Optional[str] = None
    active_flow_id: Optional[str] = None
    preferences: Dict[str, Any] = None
    permissions: List[str] = None
    recent_activities: List[Dict[str, Any]] = None
    last_updated: datetime = None

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}
        if self.permissions is None:
            self.permissions = []
        if self.recent_activities is None:
            self.recent_activities = []
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


class InMemoryFallbackCache:
    """In-memory fallback cache for when Redis is unavailable"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.access_order = deque()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from in-memory cache"""
        async with self._lock:
            if key in self.cache:
                value, expires_at = self.cache[key]
                if datetime.utcnow() < expires_at:
                    # Move to end of access order (most recently used)
                    if key in self.access_order:
                        self.access_order.remove(key)
                    self.access_order.append(key)
                    return value
                else:
                    # Expired, remove from cache
                    del self.cache[key]
                    if key in self.access_order:
                        self.access_order.remove(key)
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in in-memory cache"""
        async with self._lock:
            ttl = ttl or self.default_ttl
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)

            # Remove if already exists
            if key in self.cache:
                if key in self.access_order:
                    self.access_order.remove(key)

            # Check if we need to evict items
            while len(self.cache) >= self.max_size and self.access_order:
                oldest_key = self.access_order.popleft()
                self.cache.pop(oldest_key, None)

            # Add new item
            self.cache[key] = (value, expires_at)
            self.access_order.append(key)
            return True

    async def delete(self, key: str) -> bool:
        """Delete value from in-memory cache"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
                return True
            return False

    async def clear(self) -> bool:
        """Clear all cached data"""
        async with self._lock:
            self.cache.clear()
            self.access_order.clear()
            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "utilization": len(self.cache) / self.max_size * 100,
        }


class AuthCacheService:
    """
    Authentication Cache Service

    Provides high-performance caching for authentication and user context data
    with encryption, fallback strategies, and performance monitoring.
    """

    # Cache TTL constants (in seconds)
    TTL_USER_SESSION = 24 * 60 * 60  # 24 hours
    TTL_USER_CONTEXT = 15 * 60  # 15 minutes
    TTL_CLIENT_LIST = 60 * 60  # 1 hour
    TTL_ENGAGEMENTS = 30 * 60  # 30 minutes
    TTL_ACTIVITY_BUFFER = 5 * 60  # 5 minutes (for batching)

    # Cache key prefixes (following naming conventions: version:context:resource:identifier)
    KEY_USER_SESSION = "v1:user:{user_id}:session"
    KEY_USER_CONTEXT = "v1:user:{user_id}:context"
    KEY_USER_CLIENTS = "v1:user:{user_id}:clients"
    KEY_CLIENT_ENGAGEMENTS = "v1:client:{client_id}:engagements"
    KEY_ACTIVITY_BUFFER = "v1:user:{user_id}:activity:buffer"
    KEY_AUTH_STATS = "v1:auth:stats"

    def __init__(self):
        self.redis_cache = get_redis_cache()
        self.fallback_cache = InMemoryFallbackCache()
        self.stats = CacheStats()
        self.activity_buffers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.last_buffer_flush = datetime.utcnow()
        self.enabled = settings.REDIS_ENABLED

        # Performance monitoring
        self._request_times = deque(maxlen=1000)  # Keep last 1000 request times

        logger.info(f"AuthCacheService initialized - Redis enabled: {self.enabled}")

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

    # User Session Management

    async def get_user_session(self, user_id: str) -> Optional[UserSession]:
        """Get user session data from cache"""
        key = self.KEY_USER_SESSION.format(user_id=user_id)
        data = await self._get_from_cache(key, use_secure=True)

        if data:
            try:
                # Convert back to UserSession object
                if isinstance(data, dict):
                    # Handle datetime fields
                    if "created_at" in data and isinstance(data["created_at"], str):
                        data["created_at"] = datetime.fromisoformat(data["created_at"])
                    if "last_accessed" in data and isinstance(
                        data["last_accessed"], str
                    ):
                        data["last_accessed"] = datetime.fromisoformat(
                            data["last_accessed"]
                        )

                    return UserSession(**data)
                return data
            except Exception as e:
                logger.error(f"Error deserializing user session for {user_id}: {e}")
                # Invalidate corrupted cache entry
                await self._delete_from_cache(key)

        return None

    async def set_user_session(self, session: UserSession) -> bool:
        """Set user session data in cache"""
        key = self.KEY_USER_SESSION.format(user_id=session.user_id)

        # Update last accessed time
        session.last_accessed = datetime.utcnow()

        # Convert to dict for serialization
        session_data = asdict(session)

        # Convert datetime objects to ISO strings for JSON serialization
        if session_data.get("created_at"):
            session_data["created_at"] = session_data["created_at"].isoformat()
        if session_data.get("last_accessed"):
            session_data["last_accessed"] = session_data["last_accessed"].isoformat()

        success = await self._set_to_cache(
            key, session_data, ttl=self.TTL_USER_SESSION, use_secure=True
        )

        if success:
            logger.debug(f"Cached user session for {session.user_id}")

        return success

    async def invalidate_user_session(self, user_id: str) -> bool:
        """Invalidate user session cache"""
        key = self.KEY_USER_SESSION.format(user_id=user_id)
        success = await self._delete_from_cache(key)

        if success:
            logger.info(f"Invalidated user session cache for {user_id}")

        return success

    # User Context Management

    async def get_user_context(self, user_id: str) -> Optional[UserContext]:
        """Get user context data from cache"""
        key = self.KEY_USER_CONTEXT.format(user_id=user_id)
        data = await self._get_from_cache(key, use_secure=True)

        if data:
            try:
                if isinstance(data, dict):
                    # Handle datetime fields
                    if "last_updated" in data and isinstance(data["last_updated"], str):
                        data["last_updated"] = datetime.fromisoformat(
                            data["last_updated"]
                        )

                    return UserContext(**data)
                return data
            except Exception as e:
                logger.error(f"Error deserializing user context for {user_id}: {e}")
                await self._delete_from_cache(key)

        return None

    async def set_user_context(self, context: UserContext) -> bool:
        """Set user context data in cache"""
        key = self.KEY_USER_CONTEXT.format(user_id=context.user_id)

        # Update last updated time
        context.last_updated = datetime.utcnow()

        # Convert to dict for serialization
        context_data = asdict(context)

        # Convert datetime objects to ISO strings
        if context_data.get("last_updated"):
            context_data["last_updated"] = context_data["last_updated"].isoformat()

        success = await self._set_to_cache(
            key, context_data, ttl=self.TTL_USER_CONTEXT, use_secure=True
        )

        if success:
            logger.debug(f"Cached user context for {context.user_id}")

        return success

    async def update_user_context(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields in user context"""
        # Get existing context
        context = await self.get_user_context(user_id)

        if context is None:
            # Create new context with updates
            context = UserContext(user_id=user_id, **updates)
        else:
            # Update existing context
            for field, value in updates.items():
                if hasattr(context, field):
                    secure_setattr(context, field, value)

        return await self.set_user_context(context)

    async def invalidate_user_context(self, user_id: str) -> bool:
        """Invalidate user context cache"""
        key = self.KEY_USER_CONTEXT.format(user_id=user_id)
        success = await self._delete_from_cache(key)

        if success:
            logger.info(f"Invalidated user context cache for {user_id}")

        return success

    # Client and Engagement Caching

    async def get_user_clients(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get user's client list from cache"""
        key = self.KEY_USER_CLIENTS.format(user_id=user_id)
        return await self._get_from_cache(key, use_secure=False)

    async def set_user_clients(
        self, user_id: str, clients: List[Dict[str, Any]]
    ) -> bool:
        """Set user's client list in cache"""
        key = self.KEY_USER_CLIENTS.format(user_id=user_id)

        # Sanitize sensitive data before caching
        sanitized_clients = []
        for client in clients:
            sanitized_client = sanitize_for_logging(client)
            sanitized_clients.append(sanitized_client)

        success = await self._set_to_cache(
            key, sanitized_clients, ttl=self.TTL_CLIENT_LIST, use_secure=False
        )

        if success:
            logger.debug(f"Cached {len(clients)} clients for user {user_id}")

        return success

    async def get_client_engagements(
        self, client_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get client's engagement list from cache"""
        key = self.KEY_CLIENT_ENGAGEMENTS.format(client_id=client_id)
        return await self._get_from_cache(key, use_secure=False)

    async def set_client_engagements(
        self, client_id: str, engagements: List[Dict[str, Any]]
    ) -> bool:
        """Set client's engagement list in cache"""
        key = self.KEY_CLIENT_ENGAGEMENTS.format(client_id=client_id)

        success = await self._set_to_cache(
            key, engagements, ttl=self.TTL_ENGAGEMENTS, use_secure=False
        )

        if success:
            logger.debug(
                f"Cached {len(engagements)} engagements for client {client_id}"
            )

        return success

    # Activity Buffering for Batched Operations

    async def buffer_user_activity(
        self, user_id: str, activity: Dict[str, Any]
    ) -> bool:
        """Buffer user activity for batched storage"""
        # Add timestamp if not present
        if "timestamp" not in activity:
            activity["timestamp"] = datetime.utcnow().isoformat()

        # Add to in-memory buffer first
        self.activity_buffers[user_id].append(activity)

        # Also try to add to Redis buffer
        key = self.KEY_ACTIVITY_BUFFER.format(user_id=user_id)

        try:
            # Get existing buffer from cache
            existing_buffer = await self._get_from_cache(key, use_secure=False) or []
            existing_buffer.append(activity)

            # Keep buffer size manageable (max 100 activities)
            if len(existing_buffer) > 100:
                existing_buffer = existing_buffer[-100:]

            success = await self._set_to_cache(
                key, existing_buffer, ttl=self.TTL_ACTIVITY_BUFFER, use_secure=False
            )

            logger.debug(f"Buffered activity for user {user_id}")
            return success

        except Exception as e:
            logger.error(f"Error buffering activity for user {user_id}: {e}")
            return False

    async def get_buffered_activities(
        self, user_id: str, clear_buffer: bool = True
    ) -> List[Dict[str, Any]]:
        """Get and optionally clear buffered activities for a user"""
        activities = []

        # Get from in-memory buffer
        if user_id in self.activity_buffers:
            activities.extend(self.activity_buffers[user_id])
            if clear_buffer:
                self.activity_buffers[user_id].clear()

        # Get from Redis buffer
        key = self.KEY_ACTIVITY_BUFFER.format(user_id=user_id)
        cached_activities = await self._get_from_cache(key, use_secure=False)

        if cached_activities:
            activities.extend(cached_activities)
            if clear_buffer:
                await self._delete_from_cache(key)

        # Remove duplicates based on timestamp
        seen_timestamps = set()
        unique_activities = []

        for activity in activities:
            timestamp = activity.get("timestamp")
            if timestamp not in seen_timestamps:
                seen_timestamps.add(timestamp)
                unique_activities.append(activity)

        return unique_activities

    async def flush_activity_buffers(self, max_age_minutes: int = 5) -> int:
        """Flush old activity buffers and return count of flushed activities"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        total_flushed = 0

        # Flush in-memory buffers
        for user_id in list(self.activity_buffers.keys()):
            activities = self.activity_buffers[user_id]

            # Keep only recent activities
            recent_activities = []
            for activity in activities:
                try:
                    activity_time = datetime.fromisoformat(
                        activity.get("timestamp", "")
                    )
                    if activity_time > cutoff_time:
                        recent_activities.append(activity)
                    else:
                        total_flushed += 1
                except (ValueError, TypeError):
                    # Invalid timestamp, remove it
                    total_flushed += 1

            self.activity_buffers[user_id] = recent_activities

            # Clean up empty buffers
            if not recent_activities:
                del self.activity_buffers[user_id]

        self.last_buffer_flush = datetime.utcnow()

        if total_flushed > 0:
            logger.info(f"Flushed {total_flushed} old activity buffer entries")

        return total_flushed

    # Cache Invalidation Strategies

    async def invalidate_user_caches(self, user_id: str) -> bool:
        """Invalidate all cache entries for a user"""
        keys_to_invalidate = [
            self.KEY_USER_SESSION.format(user_id=user_id),
            self.KEY_USER_CONTEXT.format(user_id=user_id),
            self.KEY_USER_CLIENTS.format(user_id=user_id),
            self.KEY_ACTIVITY_BUFFER.format(user_id=user_id),
        ]

        success_count = 0
        for key in keys_to_invalidate:
            if await self._delete_from_cache(key):
                success_count += 1

        # Clear in-memory activity buffer
        if user_id in self.activity_buffers:
            del self.activity_buffers[user_id]

        logger.info(
            f"Invalidated {success_count}/{len(keys_to_invalidate)} cache entries for user {user_id}"
        )
        return success_count == len(keys_to_invalidate)

    async def invalidate_client_caches(self, client_id: str) -> bool:
        """Invalidate all cache entries for a client"""
        key = self.KEY_CLIENT_ENGAGEMENTS.format(client_id=client_id)
        success = await self._delete_from_cache(key)

        if success:
            logger.info(f"Invalidated client cache for {client_id}")

        return success

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache entries matching a pattern (Redis only)"""
        if not self.redis_cache.enabled:
            logger.warning("Pattern invalidation requires Redis - skipping")
            return 0

        try:
            # Use Redis SCAN to find matching keys
            cursor = "0"
            deleted_count = 0

            while True:
                if hasattr(self.redis_cache.client, "scan"):
                    cursor, keys = await self.redis_cache.client.scan(
                        cursor=cursor, match=pattern, count=100
                    )

                    for key in keys:
                        if await self.redis_cache.delete(key):
                            deleted_count += 1

                    if cursor == "0":
                        break
                else:
                    logger.warning("Redis client doesn't support SCAN operation")
                    break

            logger.info(
                f"Invalidated {deleted_count} cache entries matching pattern: {pattern}"
            )
            return deleted_count

        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")
            return 0

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


# Singleton instance
_auth_cache_service = None


def get_auth_cache_service() -> AuthCacheService:
    """Get singleton AuthCacheService instance"""
    global _auth_cache_service
    if _auth_cache_service is None:
        _auth_cache_service = AuthCacheService()
    return _auth_cache_service
