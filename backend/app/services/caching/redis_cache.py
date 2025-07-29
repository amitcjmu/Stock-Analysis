"""
Redis cache service for the AI Modernize Migration Platform.

Provides caching functionality with graceful fallback to in-memory storage
when Redis is unavailable.
"""

import json
import asyncio
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from functools import wraps

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def redis_fallback(func):
    """Decorator to provide graceful fallback when Redis operations fail."""

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.enabled:
            return self._get_fallback_result(func.__name__)

        try:
            return await asyncio.wait_for(
                func(self, *args, **kwargs),
                timeout=0.5,  # 500ms timeout for cache operations
            )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Redis operation {func.__name__} failed: {str(e)}")
            return self._get_fallback_result(func.__name__)

    return wrapper


class RedisCache:
    """Service for managing Redis cache with graceful fallback."""

    def __init__(self):
        self.enabled = getattr(settings, "REDIS_ENABLED", False)
        self.client = None
        self._in_memory_cache = {}  # Fallback cache
        self._in_memory_ttl = {}  # TTL tracking for in-memory cache

        if self.enabled:
            try:
                # Try to import Redis clients
                redis_url = getattr(settings, "REDIS_URL", None)
                upstash_url = getattr(settings, "UPSTASH_REDIS_URL", None)

                if upstash_url:
                    # Use Upstash Redis for production
                    from upstash_redis import Redis

                    self.client = Redis(
                        url=upstash_url,
                        token=getattr(settings, "UPSTASH_REDIS_TOKEN", ""),
                    )
                    logger.info("Connected to Upstash Redis")
                elif redis_url:
                    # Use standard Redis for local development
                    try:
                        import redis.asyncio as redis

                        self.client = redis.from_url(redis_url, decode_responses=True)
                        logger.info("Connected to local Redis")
                    except ImportError:
                        import redis

                        # Fallback to sync Redis client wrapped in async
                        self.client = redis.from_url(redis_url, decode_responses=True)
                        logger.info("Connected to local Redis (sync client)")
                else:
                    logger.warning("Redis enabled but no URL configured")
                    self.enabled = False

                self.default_ttl = getattr(settings, "REDIS_DEFAULT_TTL", 3600)

            except ImportError as e:
                logger.warning(f"Redis client not installed: {str(e)}")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {str(e)}")
                self.enabled = False
        else:
            logger.info("Redis cache is disabled, using in-memory fallback")

    def _get_fallback_result(self, operation: str) -> Any:
        """Get appropriate fallback result based on operation type."""
        fallback_results = {
            "get": None,
            "set": True,
            "delete": True,
            "get_flow_state": None,
            "get_import_sample": None,
            "get_mapping_pattern": None,
            "get_sse_connections": {},
            "acquire_lock": "local-lock",
            "release_lock": True,
            "publish_event": False,
            "increment_metric": False,
        }
        return fallback_results.get(operation, None)

    def _clean_expired_in_memory(self):
        """Clean expired entries from in-memory cache."""
        now = datetime.utcnow()
        expired_keys = [
            key
            for key, expiry in self._in_memory_ttl.items()
            if expiry and expiry < now
        ]
        for key in expired_keys:
            self._in_memory_cache.pop(key, None)
            self._in_memory_ttl.pop(key, None)

    @redis_fallback
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if isinstance(self.client, type(None)):
            # In-memory fallback
            self._clean_expired_in_memory()
            value = self._in_memory_cache.get(key)
            if value:
                return json.loads(value)
            return None

        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None

    @redis_fallback
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        ttl = ttl or self.default_ttl
        serialized = json.dumps(value, default=str)

        if isinstance(self.client, type(None)):
            # In-memory fallback
            self._in_memory_cache[key] = serialized
            if ttl:
                self._in_memory_ttl[key] = datetime.utcnow() + timedelta(seconds=ttl)
            return True

        # Check if we're using Upstash or standard Redis
        if hasattr(self.client, "setex"):
            await self.client.setex(key, ttl, serialized)
        else:
            await self.client.set(key, serialized, ex=ttl)
        return True

    @redis_fallback
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if isinstance(self.client, type(None)):
            # In-memory fallback
            self._in_memory_cache.pop(key, None)
            self._in_memory_ttl.pop(key, None)
            return True

        await self.client.delete(key)
        return True

    # Flow State Caching
    async def cache_flow_state(
        self, flow_id: str, state: Dict[str, Any], ttl: int = 3600
    ) -> bool:
        """Cache flow state for quick access."""
        key = f"flow:state:{flow_id}"
        return await self.set(key, state, ttl)

    async def get_flow_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get flow state from cache."""
        key = f"flow:state:{flow_id}"
        return await self.get(key)

    # Import Sample Caching
    async def cache_import_sample(
        self, import_id: str, sample_data: List[Dict[str, Any]], ttl: int = 3600
    ) -> bool:
        """Cache import sample for agent analysis."""
        key = f"import:sample:{import_id}"
        return await self.set(key, sample_data, ttl)

    async def get_import_sample(self, import_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get import sample from cache."""
        key = f"import:sample:{import_id}"
        return await self.get(key)

    # Pattern Learning Cache
    async def cache_mapping_pattern(
        self, pattern_key: str, pattern: Dict[str, Any], ttl: int = 86400  # 24 hours
    ) -> bool:
        """Cache field mapping pattern."""
        key = f"pattern:mapping:{pattern_key}"
        return await self.set(key, pattern, ttl)

    async def get_mapping_pattern(self, pattern_key: str) -> Optional[Dict[str, Any]]:
        """Get mapping pattern from cache."""
        key = f"pattern:mapping:{pattern_key}"
        return await self.get(key)

    # SSE Connection Registry
    async def register_sse_connection(
        self, flow_id: str, connection_id: str, metadata: Dict[str, Any]
    ) -> bool:
        """Register SSE connection for cross-instance updates."""
        key = f"sse:connections:{flow_id}"

        # Get existing connections
        connections = await self.get(key) or {}

        # Add new connection
        connections[connection_id] = {
            **metadata,
            "registered_at": datetime.utcnow().isoformat(),
        }

        # Store with 1 hour TTL (connections should refresh)
        return await self.set(key, connections, 3600)

    async def unregister_sse_connection(self, flow_id: str, connection_id: str) -> bool:
        """Unregister SSE connection."""
        key = f"sse:connections:{flow_id}"

        connections = await self.get(key) or {}
        if connection_id in connections:
            del connections[connection_id]
            return await self.set(key, connections, 3600)
        return True

    async def get_sse_connections(self, flow_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all SSE connections for a flow."""
        key = f"sse:connections:{flow_id}"
        return await self.get(key) or {}

    # Distributed Locking
    @redis_fallback
    async def acquire_lock(self, resource: str, ttl: int = 30) -> Optional[str]:
        """Acquire distributed lock."""
        if isinstance(self.client, type(None)):
            # In-memory fallback - always grant lock
            return "local-lock"

        key = f"lock:{resource}"
        lock_id = f"{datetime.utcnow().timestamp()}"

        # SET NX (set if not exists)
        if hasattr(self.client, "set"):
            result = await self.client.set(
                key,
                lock_id,
                nx=True,  # Only set if not exists
                ex=ttl,  # Expire after TTL
            )
        else:
            # Upstash Redis
            existing = await self.client.get(key)
            if existing:
                return None
            await self.client.setex(key, ttl, lock_id)
            result = True

        if result:
            return lock_id
        return None

    @redis_fallback
    async def release_lock(self, resource: str, lock_id: str) -> bool:
        """Release distributed lock."""
        if isinstance(self.client, type(None)):
            # In-memory fallback
            return True

        key = f"lock:{resource}"

        # Only delete if we own the lock
        current_lock = await self.get(key)
        if current_lock == lock_id:
            return await self.delete(key)
        return False

    # Event Broadcasting
    @redis_fallback
    async def publish_event(self, channel: str, event: Dict[str, Any]) -> bool:
        """Publish event for cross-instance communication."""
        if isinstance(self.client, type(None)):
            # In-memory fallback - can't broadcast
            return False

        serialized = json.dumps(event, default=str)

        if hasattr(self.client, "publish"):
            await self.client.publish(channel, serialized)
        else:
            # Upstash doesn't support pub/sub, use a list instead
            list_key = f"events:{channel}"
            await self.client.lpush(list_key, serialized)
            # Trim to last 100 events
            await self.client.ltrim(list_key, 0, 99)

        return True

    # Performance Metrics
    @redis_fallback
    async def increment_metric(self, metric_name: str, value: int = 1) -> bool:
        """Increment a metric counter."""
        if isinstance(self.client, type(None)):
            # In-memory fallback
            return False

        key = f"metric:{metric_name}:{datetime.utcnow().strftime('%Y%m%d')}"

        if hasattr(self.client, "incrby"):
            await self.client.incrby(key, value)
            await self.client.expire(key, 604800)  # 7 days
        else:
            # Upstash Redis
            current = await self.client.get(key) or "0"
            new_value = int(current) + value
            await self.client.setex(key, 604800, str(new_value))

        return True

    async def close(self):
        """Close Redis connection."""
        if self.enabled and self.client and hasattr(self.client, "close"):
            await self.client.close()


# Singleton instance
redis_cache = RedisCache()
