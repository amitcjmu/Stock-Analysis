"""Helper functions for gap grouping and processing."""

import logging
from typing import Any, Dict, List

from ..context_filter import DEFAULT_SAFE_KEYS, get_tenant_safe_keys

logger = logging.getLogger(__name__)


def group_gaps_by_asset(gaps: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group gaps by asset_id.

    Args:
        gaps: List of gap dictionaries

    Returns:
        Dict mapping asset_id to list of gaps
    """
    gaps_by_asset = {}
    for gap in gaps:
        asset_id = gap.get("asset_id")
        if asset_id not in gaps_by_asset:
            gaps_by_asset[asset_id] = []
        gaps_by_asset[asset_id].append(gap)
    return gaps_by_asset


def create_asset_lookup(assets: list) -> Dict[str, Any]:
    """Create asset lookup dictionary.

    Args:
        assets: List of Asset objects

    Returns:
        Dict mapping asset_id (as string) to Asset object
    """
    return {str(a.id): a for a in assets}


async def load_tenant_safe_keys(client_account_id: str, redis_client) -> set:
    """Load tenant-specific safe keys for context filtering.

    Args:
        client_account_id: Client account ID
        redis_client: Redis client (or None)

    Returns:
        Set of tenant safe keys
    """
    tenant_safe_keys = set()

    if redis_client:
        try:
            tenant_safe_keys = await get_tenant_safe_keys(
                client_account_id, redis_client
            )
            logger.info(
                f"📋 Loaded {len(tenant_safe_keys)} tenant safe keys for filtering"
            )
        except Exception as e:
            logger.warning(f"Failed to load tenant safe keys: {e}, using defaults")
            tenant_safe_keys = DEFAULT_SAFE_KEYS
    else:
        tenant_safe_keys = DEFAULT_SAFE_KEYS

    return tenant_safe_keys


def initialize_progress_tracking() -> Dict[str, Any]:
    """Initialize progress tracking counters.

    Returns:
        Dict with progress tracking state
    """
    return {
        "processed_count": 0,
        "failed_count": 0,
        "failed_assets": [],
        "all_enhanced_gaps": {"critical": [], "high": [], "medium": [], "low": []},
        "total_gaps_persisted": 0,
    }
