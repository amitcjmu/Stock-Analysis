"""
Asset Inventory Executor - Preview Handler
Handles asset preview generation, storage, and approval workflow.

CC: Implements Issue #907 - Asset Preview and Approval Workflow
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from .utils import serialize_uuids_for_jsonb

logger = logging.getLogger(__name__)


async def check_preview_and_approval(
    master_flow_repo: CrewAIFlowStateExtensionsRepository,
    master_flow_id: str,
) -> Tuple[Optional[List[Dict]], Optional[List[str]], bool, Optional[Dict[str, Dict]]]:
    """
    Check if preview data exists and if assets are approved.

    CRITICAL FIX (Issue #1072): Now also returns updated_assets_map with user edits

    Returns:
        Tuple of (assets_preview, approved_asset_ids, assets_already_created, updated_assets_map)
    """
    master_flow = await master_flow_repo.get_by_flow_id(str(master_flow_id))
    if not master_flow:
        logger.error(f"❌ Master flow {master_flow_id} not found")
        raise ValueError(f"Master flow {master_flow_id} not found")

    persistence_data = master_flow.flow_persistence_data or {}

    assets_preview = persistence_data.get("assets_preview")
    approved_asset_ids = persistence_data.get("approved_asset_ids")
    assets_already_created = persistence_data.get("assets_created", False)
    updated_assets_map = persistence_data.get(
        "updated_assets_map"
    )  # CRITICAL FIX (Issue #1072)

    return (
        assets_preview,
        approved_asset_ids,
        assets_already_created,
        updated_assets_map,
    )


async def store_preview_data(
    master_flow_repo: CrewAIFlowStateExtensionsRepository,
    master_flow_id: str,
    assets_data: List[Dict[str, Any]],
    db_session,
) -> Dict[str, Any]:
    """
    Store asset preview data and return paused status.

    Args:
        master_flow_repo: Repository for master flow operations
        master_flow_id: Master flow UUID
        assets_data: List of asset data dictionaries
        db_session: Active database session

    Returns:
        Dictionary with paused status and preview information
    """
    logger.info(f"📋 Storing {len(assets_data)} assets for preview (Issue #907)")

    master_flow = await master_flow_repo.get_by_flow_id(str(master_flow_id))
    if not master_flow:
        raise ValueError(f"Master flow {master_flow_id} not found")

    persistence_data = master_flow.flow_persistence_data or {}

    # Serialize assets_data for JSONB storage (convert UUIDs to strings)
    serialized_assets = []
    for i, asset in enumerate(assets_data):
        serialized_asset = serialize_uuids_for_jsonb(asset)
        # CC FIX (Issue #907): Use 'id' field for frontend compatibility
        # Frontend AssetPreviewData interface expects 'id', not 'temp_id'
        serialized_asset["id"] = f"asset-{i}"
        serialized_assets.append(serialized_asset)

    # CC FIX (Issue #907): Use dictionary reassignment for SQLAlchemy change tracking
    # Creating a new dictionary triggers automatic change detection for JSONB columns
    master_flow.flow_persistence_data = {
        **persistence_data,
        "assets_preview": serialized_assets,
        "preview_generated_at": datetime.utcnow().isoformat(),
    }

    await db_session.commit()

    logger.info(
        f"✅ Stored {len(serialized_assets)} assets for preview. "
        "Waiting for user approval via /api/v1/asset-preview/{flow_id}/approve"
    )

    return {
        "status": "paused",  # Per ADR-012: Child flow status
        "phase": "asset_inventory",
        "message": (
            f"Preview ready: {len(serialized_assets)} assets transformed. "
            "Waiting for user approval before database creation."
        ),
        "preview_count": len(serialized_assets),
        "preview_ready": True,
        "phase_state": {
            "preview_pending_approval": True,
        },
    }


def filter_approved_assets(
    assets_data: List[Dict[str, Any]],
    approved_asset_ids: List[str],
    updated_assets_map: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Filter assets_data to only include approved assets and merge user edits.

    CRITICAL FIX (Issue #1072): Now merges user edits from updated_assets_map

    Args:
        assets_data: List of all asset data dictionaries
        approved_asset_ids: List of approved asset temp_ids (e.g., ["asset-0", "asset-1"])
        updated_assets_map: Optional dict mapping asset_id -> updated asset data with user edits

    Returns:
        List of approved asset data dictionaries with user edits applied
    """
    approved_assets_data = []
    updated_count = 0

    for asset_index, asset in enumerate(assets_data):
        temp_id = f"asset-{asset_index}"
        if temp_id in approved_asset_ids:
            # CRITICAL FIX (Issue #1072): Merge user edits if available
            if updated_assets_map and temp_id in updated_assets_map:
                updated_asset = updated_assets_map[temp_id]
                # Merge user edits into original asset data (user edits take precedence)
                merged_asset = {**asset, **updated_asset}
                # Remove the 'id' field if it exists (it's just a temp_id, not a real asset ID)
                merged_asset.pop("id", None)
                approved_assets_data.append(merged_asset)
                updated_count += 1
                logger.debug(
                    f"✅ Applied user edits to asset {temp_id}: {list(updated_asset.keys())}"
                )
            else:
                # No user edits, use original asset data
                approved_assets_data.append(asset)

    logger.info(
        f"📋 Filtered to {len(approved_assets_data)} approved assets "
        f"(from {len(assets_data)} total, {updated_count} with user edits)"
    )

    return approved_assets_data


async def mark_assets_created(
    master_flow_repo: CrewAIFlowStateExtensionsRepository,
    master_flow_id: str,
    assets_created_count: int,
    db_session,
) -> None:
    """
    Mark assets as created in flow_persistence_data to prevent re-creation.

    Args:
        master_flow_repo: Repository for master flow operations
        master_flow_id: Master flow UUID
        assets_created_count: Number of assets created
        db_session: Active database session
    """
    master_flow = await master_flow_repo.get_by_flow_id(str(master_flow_id))
    if not master_flow:
        raise ValueError(f"Master flow {master_flow_id} not found")

    persistence_data = master_flow.flow_persistence_data or {}

    # Mark assets as created (Issue #907)
    persistence_data["assets_created"] = True
    persistence_data["assets_created_at"] = datetime.utcnow().isoformat()
    persistence_data["assets_created_count"] = assets_created_count
    master_flow.flow_persistence_data = persistence_data

    # CC FIX (Issue #907): Mark JSONB column as modified for SQLAlchemy change tracking
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(master_flow, "flow_persistence_data")

    await db_session.flush()  # Persist the flag
    logger.info(
        f"✅ Marked {assets_created_count} assets as created in flow_persistence_data"
    )


__all__ = [
    "check_preview_and_approval",
    "store_preview_data",
    "filter_approved_assets",
    "mark_assets_created",
]
