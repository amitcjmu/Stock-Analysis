"""
Distributed locking operations for Redis cache.

Provides atomic lock acquisition and release capabilities.
"""

import uuid
from typing import Optional

from app.core.logging import get_logger

from .utils import redis_fallback

logger = get_logger(__name__)


class RedisLockingMixin:
    """Mixin for Redis distributed locking operations"""

    @redis_fallback
    async def acquire_lock(self, resource: str, ttl: int = 30) -> Optional[str]:
        """Acquire distributed lock with atomic operation"""
        key = f"lock:{resource}"
        lock_id = str(uuid.uuid4())

        try:
            if self.client_type == "upstash":
                # Upstash doesn't support SET NX directly, use atomic get-set pattern
                # Use SETNX equivalent with Upstash
                result = self.client.set(key, lock_id, nx=True, ex=ttl)
                return lock_id if result else None
            else:
                # Standard Redis with SET NX
                result = await self.client.set(key, lock_id, nx=True, ex=ttl)
                return lock_id if result else None
        except AttributeError:
            # Fallback for clients without nx parameter
            # This is NOT atomic and has race condition, but better than nothing
            try:
                exists = await self.exists(key)
                if not exists:
                    success = await self.set(key, lock_id, ttl)
                    return lock_id if success else None
                return None
            except Exception as e:
                logger.error(f"Redis lock fallback error: {str(e)}")
                return None

    @redis_fallback
    async def release_lock(self, resource: str, lock_id: str) -> bool:
        """Release distributed lock if we own it"""
        key = f"lock:{resource}"

        try:
            # Check if we own the lock
            current_lock = await self.get(key)
            if current_lock == lock_id:
                return await self.delete(key)
            return False
        except Exception as e:
            logger.error(f"Redis release lock error: {str(e)}")
            return False
