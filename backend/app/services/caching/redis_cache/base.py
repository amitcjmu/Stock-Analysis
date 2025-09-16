"""
Base Redis cache client initialization and core operations.

Handles client setup for different Redis providers (Upstash, async, sync).
"""

import json
from typing import Any, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security.cache_encryption import SecureCache

from .serializers import datetime_json_serializer, datetime_json_deserializer
from .utils import redis_fallback
from .wrappers import AsyncRedisWrapper

logger = get_logger(__name__)


class RedisBaseCache:
    """Base Redis cache service with client initialization"""

    def __init__(self):
        self.enabled = settings.REDIS_ENABLED
        self.client = None
        self.client_type = None
        self.default_ttl = settings.REDIS_DEFAULT_TTL

        if not self.enabled:
            logger.info("Redis cache is disabled")
            return

        # Try to initialize Redis client
        self._initialize_client()
        # Initialize secure cache wrapper for sensitive data
        self.secure_cache = SecureCache(self)

    def _initialize_client(self):
        """Initialize the appropriate Redis client based on configuration"""
        # Try Upstash Redis first (for production)
        if hasattr(settings, "UPSTASH_REDIS_URL") and settings.UPSTASH_REDIS_URL:
            try:
                from upstash_redis import Redis as UpstashRedis

                self.client = UpstashRedis(
                    url=settings.UPSTASH_REDIS_URL, token=settings.UPSTASH_REDIS_TOKEN
                )
                self.client_type = "upstash"
                logger.info("Connected to Upstash Redis")
                return
            except Exception as e:
                logger.warning(f"Failed to connect to Upstash Redis: {e}")

        # Try async Redis (for local development)
        if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
            try:
                import redis.asyncio as redis_async

                self.client = redis_async.from_url(
                    settings.REDIS_URL, decode_responses=True
                )
                self.client_type = "async"
                logger.info("Connected to async Redis")
                return
            except Exception as e:
                logger.warning(f"Failed to connect to async Redis: {e}")

        # Fallback to sync Redis wrapped in async
        if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
            try:
                import redis

                sync_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self.client = AsyncRedisWrapper(sync_client)
                self.client_type = "sync_wrapped"
                logger.info("Connected to Redis (sync client wrapped)")
                return
            except Exception as e:
                logger.warning(f"Failed to connect to sync Redis: {e}")

        # If all fail, disable Redis
        logger.warning("No Redis connection available, caching disabled")
        self.enabled = False

    @redis_fallback
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with robust error handling"""
        try:
            if self.client_type == "upstash":
                value = self.client.get(key)
            else:
                value = await self.client.get(key)

            if value is None:
                return None

            # Handle bytes values explicitly before JSON parsing
            if isinstance(value, (bytes, bytearray)):
                try:
                    # Attempt to decode as UTF-8
                    value_str = value.decode("utf-8")
                except UnicodeDecodeError:
                    # If not valid UTF-8, return as raw bytes
                    logger.warning(
                        f"Non-UTF8 bytes found in cache key {key}, returning raw bytes"
                    )
                    return value
            elif isinstance(value, str):
                value_str = value
            else:
                # Non-string, non-bytes value - return as-is
                return value

            # Attempt JSON parsing with comprehensive error handling
            try:
                parsed_value = json.loads(value_str)
                # Apply recursive deserializer to reconstruct typed objects
                return datetime_json_deserializer(parsed_value)
            except json.JSONDecodeError as e:
                # Log JSON parse errors but return raw string value
                logger.debug(
                    f"JSON decode failed for key {key}: {str(e)}, returning raw string"
                )
                return value_str
            except (TypeError, ValueError) as e:
                # Handle other parsing errors
                logger.warning(
                    f"Value parsing error for key {key}: {str(e)}, returning raw value"
                )
                return value_str

        except Exception as e:
            logger.error(f"Redis get error for key {key}: {str(e)}")
            return None

    @redis_fallback
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            ttl = ttl or self.default_ttl
            serialized = (
                json.dumps(value, default=datetime_json_serializer, ensure_ascii=False)
                if not isinstance(value, str)
                else value
            )

            if self.client_type == "upstash":
                # Upstash uses setex with different parameter order
                self.client.setex(key, ttl, serialized)
            elif hasattr(self.client, "setex"):
                # Standard Redis clients
                await self.client.setex(key, ttl, serialized)
            else:
                # Use set with ex parameter
                await self.client.set(key, serialized, ex=ttl)

            return True
        except Exception as e:
            # Sanitize error logging to prevent sensitive data exposure
            logger.error(
                f"Redis set error for key {key}: {str(e)} (value type: {type(value).__name__})"
            )
            return False

    async def set_secure(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        force_encrypt: bool = False,
    ) -> bool:
        """Set value in cache with automatic encryption for sensitive data"""
        return await self.secure_cache.set(key, value, ttl, force_encrypt)

    async def get_secure(self, key: str) -> Optional[Any]:
        """Get value from cache with automatic decryption"""
        return await self.secure_cache.get(key)

    @redis_fallback
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.client_type == "upstash":
                self.client.delete(key)
            else:
                await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {str(e)}")
            return False

    @redis_fallback
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            if self.client_type == "upstash":
                return bool(self.client.exists(key))
            else:
                result = await self.client.exists(key)
                return bool(result)
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {str(e)}")
            return False
