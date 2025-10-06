"""
Redis job state management for gap analysis enhancement jobs.

Provides helper functions for creating, updating, and querying job state.
"""

import json
import logging
import time
from typing import Any, Dict, Optional

from app.core.redis_config import get_redis_manager

logger = logging.getLogger(__name__)


def get_job_key(collection_flow_id: Any) -> str:
    """Get Redis key for gap enhancement job state.

    Args:
        collection_flow_id: Collection flow internal ID

    Returns:
        Redis key string
    """
    return f"gap_enhancement_job:{collection_flow_id}"


async def create_job_state(
    job_id: str,
    flow_id: str,
    collection_flow_id: Any,
    total_gaps: int,
    total_assets: int,
    idempotency_key: str,
) -> None:
    """Initialize job state in Redis.

    Args:
        job_id: Unique job identifier
        flow_id: Collection flow UUID (business identifier)
        collection_flow_id: Collection flow internal ID
        total_gaps: Total number of gaps to process
        total_assets: Total number of assets to process
        idempotency_key: Hash of gap IDs for idempotency
    """
    redis_manager = get_redis_manager()
    if not redis_manager.is_available():
        logger.warning("Redis unavailable, job state will not be tracked")
        return

    job_key = get_job_key(collection_flow_id)
    job_state = {
        "job_id": job_id,
        "status": "queued",
        "flow_id": str(flow_id),
        "total_gaps": total_gaps,
        "processed_assets": 0,
        "total_assets": total_assets,
        "enhanced_count": 0,
        "failed_count": 0,
        "gaps_persisted": 0,
        "started_at": time.time(),
        "updated_at": time.time(),
        "idempotency_key": idempotency_key,
    }

    await redis_manager.client.set(
        job_key, json.dumps(job_state), ex=3600  # 1-hour TTL
    )

    logger.info(f"✅ Created job {job_id} with idempotency key {idempotency_key}")


async def get_job_state(collection_flow_id: Any) -> Optional[Dict[str, Any]]:
    """Retrieve current job state from Redis.

    Args:
        collection_flow_id: Collection flow internal ID

    Returns:
        Job state dict or None if not found
    """
    redis_manager = get_redis_manager()
    if not redis_manager.is_available():
        return None

    job_key = get_job_key(collection_flow_id)

    try:
        job_state_json = await redis_manager.client.get(job_key)
        if job_state_json:
            return json.loads(job_state_json)
        return None
    except Exception as e:
        logger.warning(f"Failed to retrieve job state: {e}")
        return None


async def update_job_state(collection_flow_id: Any, updates: Dict[str, Any]) -> None:
    """Update job state in Redis atomically using a transaction.

    Uses Redis WATCH to ensure atomic updates and prevent race conditions
    that could lead to data loss from concurrent updates.

    Args:
        collection_flow_id: Collection flow internal ID
        updates: Dictionary of fields to update
    """
    redis_manager = get_redis_manager()
    if not redis_manager.is_available():
        return

    job_key = get_job_key(collection_flow_id)

    try:
        # Retry loop for optimistic locking with WATCH
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with redis_manager.client.pipeline(transaction=True) as pipe:
                    # Watch the key for changes
                    await pipe.watch(job_key)

                    # Get current state
                    job_state_json = await redis_manager.client.get(job_key)
                    if not job_state_json:
                        await pipe.unwatch()
                        return

                    # Update state
                    job_state = json.loads(job_state_json)
                    job_state.update(updates)
                    job_state["updated_at"] = time.time()

                    # Atomic write with multi/exec
                    pipe.multi()
                    await pipe.set(job_key, json.dumps(job_state), ex=3600)
                    await pipe.execute()
                    break  # Success, exit retry loop

            except Exception as watch_error:
                # WatchError or other Redis errors - retry
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Redis transaction conflict on {job_key}, "
                        f"retry {attempt + 1}/{max_retries}: {watch_error}"
                    )
                    continue
                else:
                    raise  # Max retries exceeded

    except Exception as e:
        logger.warning(f"Failed to update job state for {job_key}: {e}")
