"""
Cache invalidation strategies for Authentication Cache Service

Provides various cache invalidation patterns including user-specific invalidation,
client-specific invalidation, and pattern-based bulk invalidation operations.
"""

from app.core.logging import get_logger

from .base import CacheKeys

logger = get_logger(__name__)


class InvalidationStrategiesMixin:
    """
    Mixin providing cache invalidation strategies

    Handles:
    - User-specific cache invalidation
    - Client-specific cache invalidation
    - Pattern-based bulk invalidation

    Requires:
    - self._delete_from_cache()
    - self.redis_cache
    - self.activity_buffers (Dict)
    """

    # Cache Invalidation Strategies

    async def invalidate_user_caches(self, user_id: str) -> bool:
        """Invalidate all cache entries for a user"""
        keys_to_invalidate = [
            CacheKeys.USER_SESSION.format(user_id=user_id),
            CacheKeys.USER_CONTEXT.format(user_id=user_id),
            CacheKeys.USER_CLIENTS.format(user_id=user_id),
            CacheKeys.ACTIVITY_BUFFER.format(user_id=user_id),
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
        key = CacheKeys.CLIENT_ENGAGEMENTS.format(client_id=client_id)
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
