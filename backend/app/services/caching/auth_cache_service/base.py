"""
Base classes and data structures for Authentication Cache Service

Contains shared data classes, constants, and the in-memory fallback cache
that are used across all cache service modules.
"""

import asyncio
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging import get_logger

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert UserContext to dictionary"""
        return asdict(self)


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


# Cache TTL constants (in seconds)
class CacheTTL:
    """Cache TTL constants"""

    USER_SESSION = 24 * 60 * 60  # 24 hours
    USER_CONTEXT = 15 * 60  # 15 minutes
    CLIENT_LIST = 60 * 60  # 1 hour
    ENGAGEMENTS = 30 * 60  # 30 minutes
    ACTIVITY_BUFFER = 5 * 60  # 5 minutes (for batching)


# Cache key templates (following naming conventions: version:context:resource:identifier)
class CacheKeys:
    """Cache key templates"""

    USER_SESSION = "v1:user:{user_id}:session"
    USER_CONTEXT = "v1:user:{user_id}:context"
    USER_CLIENTS = "v1:user:{user_id}:clients"
    CLIENT_ENGAGEMENTS = "v1:client:{client_id}:engagements"
    ACTIVITY_BUFFER = "v1:user:{user_id}:activity:buffer"
    AUTH_STATS = "v1:auth:stats"
