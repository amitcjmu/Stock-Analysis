"""Redis distributed locking for gap enhancement."""

import logging
from typing import Tuple

from fastapi import HTTPException

logger = logging.getLogger(__name__)


async def acquire_enhancement_lock(
    collection_flow_id: str, redis_client
) -> Tuple[bool, str]:
    """Acquire distributed lock for gap enhancement.

    Args:
        collection_flow_id: Collection flow UUID
        redis_client: Redis client instance (or None)

    Returns:
        Tuple of (lock_acquired, lock_key)

    Raises:
        HTTPException: If another worker is already processing
    """
    lock_key = f"gap_enhancement_lock:{collection_flow_id}"
    lock_acquired = False

    if redis_client:
        try:
            lock_acquired = await redis_client.set(
                lock_key, "locked", nx=True, ex=900  # 15-minute TTL
            )

            if not lock_acquired:
                raise HTTPException(
                    status_code=409,
                    detail="Another worker is already processing this flow",
                )
        except Exception as e:
            logger.error(f"Failed to acquire Redis lock: {e}")
            # Continue without lock if Redis fails (single-worker deployment)

    return lock_acquired, lock_key


async def release_enhancement_lock(redis_client, lock_key: str, lock_acquired: bool):
    """Release distributed lock in finally block."""
    if redis_client and lock_acquired:
        try:
            await redis_client.delete(lock_key)
            logger.debug("🔓 Released Redis lock")
        except Exception as e:
            logger.error(f"Failed to release Redis lock: {e}")
