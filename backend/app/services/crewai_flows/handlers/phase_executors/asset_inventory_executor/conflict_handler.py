"""
Asset Inventory Executor - Conflict Handler
Handles asset conflict detection, storage, and resolution workflow.

CC: Implements bulk conflict detection and conflict resolution pausing
"""

import logging
from typing import Dict, Any, List, Tuple
from uuid import UUID

from app.services.asset_service import AssetService
from app.models.asset_conflict_resolution import AssetConflictResolution
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from .utils import serialize_uuids_for_jsonb
from .commands import mark_records_processed, persist_asset_inventory_completion

logger = logging.getLogger(__name__)


async def create_conflict_free_assets(
    asset_service: AssetService,
    conflict_free: List[Dict[str, Any]],
    master_flow_id: str,
    db_session,
) -> Tuple[List, List, int]:
    """
    Create conflict-free assets in the database.

    Args:
        asset_service: Service for asset creation
        conflict_free: List of conflict-free asset data
        master_flow_id: Master flow UUID
        db_session: Active database session

    Returns:
        Tuple of (created_assets, duplicate_assets, failed_count)
    """
    logger.info(f"✅ Processing {len(conflict_free)} conflict-free assets")

    created_assets = []
    duplicate_assets = []
    failed_count = 0

    if not conflict_free:
        return created_assets, duplicate_assets, failed_count

    # Create assets via service (transaction managed by caller)
    # CC: Don't start a new transaction - db_session already has an active transaction
    try:
        results = await asset_service.bulk_create_or_update_assets(
            conflict_free, flow_id=master_flow_id
        )

        # Categorize results by status
        for asset, status in results:
            if status == "created":
                created_assets.append(asset)
                logger.debug(f"✅ Created asset: {asset.name}")
            elif status == "existed":
                duplicate_assets.append(asset)
                logger.debug(f"🔄 Duplicate asset skipped: {asset.name}")

    except Exception as e:
        # If batch fails, fall back to individual processing
        logger.warning(f"⚠️ Batch processing failed, falling back to individual: {e}")
        for asset_data in conflict_free:
            try:
                asset, status = await asset_service.create_or_update_asset(
                    asset_data, flow_id=master_flow_id
                )

                if status == "created":
                    created_assets.append(asset)
                    logger.debug(f"✅ Created asset: {asset.name}")
                elif status == "existed":
                    duplicate_assets.append(asset)
                    logger.debug(f"🔄 Duplicate asset skipped: {asset.name}")

            except Exception as e:
                failed_count += 1
                logger.error(
                    f"❌ Failed to create asset {asset_data.get('name', 'unnamed')}: {e}"
                )

    # Flush to make asset IDs available for foreign key relationships
    await db_session.flush()

    logger.info(
        f"✅ Created {len(created_assets)} conflict-free assets, "
        f"{len(duplicate_assets)} duplicates, {failed_count} failed"
    )

    return created_assets, duplicate_assets, failed_count


async def handle_conflicts(
    conflicts_data: List[Dict[str, Any]],
    created_assets: List,
    duplicate_assets: List,
    failed_count: int,
    raw_records: List,
    db_session,
    client_account_id: str,
    engagement_id: str,
    data_import_id: str,
    discovery_flow_id: str,
    master_flow_id: str,
) -> Dict[str, Any]:
    """
    Store conflicts in database and pause flow for user resolution.

    Args:
        conflicts_data: List of detected conflicts
        created_assets: List of successfully created assets
        duplicate_assets: List of duplicate assets
        failed_count: Number of failed asset creations
        raw_records: List of raw import records
        db_session: Active database session
        client_account_id: Client account UUID string
        engagement_id: Engagement UUID string
        data_import_id: Data import UUID string
        discovery_flow_id: Discovery flow UUID string
        master_flow_id: Master flow UUID string

    Returns:
        Dictionary with paused status and conflict information
    """
    logger.warning(
        f"⚠️ Detected {len(conflicts_data)} asset conflicts - pausing for user resolution"
    )

    # Step 1: Get discovery flow record to obtain PK for FK constraint
    # CC FIX: Need both id (PK) and flow_id for different purposes
    discovery_repo = DiscoveryFlowRepository(
        db_session, str(client_account_id), str(engagement_id)
    )
    flow_record = await discovery_repo.get_by_flow_id(str(discovery_flow_id))
    if not flow_record:
        raise ValueError(f"Discovery flow not found for flow_id {discovery_flow_id}")

    flow_pk_id = flow_record.id  # UUID PK for FK constraint in conflict records
    logger.info(
        f"📋 Retrieved discovery flow - PK: {flow_pk_id}, flow_id: {discovery_flow_id}"
    )

    # Step 2: Store conflicts in database
    for conflict in conflicts_data:
        # Serialize UUID objects for JSONB storage compatibility
        serialized_new_asset_data = serialize_uuids_for_jsonb(
            conflict["new_asset_data"]
        )

        conflict_record = AssetConflictResolution(
            client_account_id=UUID(client_account_id),
            engagement_id=UUID(engagement_id),
            data_import_id=UUID(data_import_id) if data_import_id else None,
            discovery_flow_id=flow_pk_id,  # Use PK for FK constraint
            master_flow_id=UUID(master_flow_id),  # Indexed for filtering
            conflict_type=conflict["conflict_type"],
            conflict_key=conflict["conflict_key"],
            existing_asset_id=conflict["existing_asset_id"],
            existing_asset_snapshot=conflict["existing_asset_data"],
            new_asset_data=serialized_new_asset_data,
            resolution_status="pending",
        )
        db_session.add(conflict_record)

    await db_session.flush()

    # Step 3: Mark raw records as processed for conflict-free assets
    # CC: Track which records have been processed (created as assets)
    all_processed_assets = created_assets + duplicate_assets
    if all_processed_assets:
        await mark_records_processed(db_session, raw_records, all_processed_assets)
        logger.info(f"✅ Marked {len(all_processed_assets)} records as processed")

    # Step 4: Mark phase as complete to prevent re-execution
    # CC CRITICAL: Set asset_inventory_completed=true even when pausing for conflicts
    # This prevents auto-execution from re-running the phase and creating duplicate conflicts
    await persist_asset_inventory_completion(
        db_session,
        flow_id=str(discovery_flow_id),
        client_account_id=str(client_account_id),
        engagement_id=str(engagement_id),
        mark_flow_complete=False,  # Don't mark flow as complete yet (conflicts pending)
    )
    logger.info("✅ Marked asset_inventory phase as complete (with pending conflicts)")

    # Step 5: Pause flow via repository - use flow_id for WHERE clause
    # CC FIX: Pass flow_id (business identifier) not id (PK)
    await discovery_repo.set_conflict_resolution_pending(
        UUID(discovery_flow_id),  # flow_id column for WHERE clause
        conflict_count=len(conflicts_data),
        data_import_id=UUID(data_import_id) if data_import_id else None,
    )

    # Step 6: Return paused status
    return {
        "status": "paused",  # Child flow status per ADR-012
        "phase": "asset_inventory",
        "message": f"Found {len(conflicts_data)} duplicate assets. User resolution required.",
        "conflict_count": len(conflicts_data),
        "conflict_free_count": len(created_assets) + len(duplicate_assets),
        "assets_created": len(created_assets),
        "assets_duplicates": len(duplicate_assets),
        "assets_failed": failed_count,
        "data_import_id": str(data_import_id) if data_import_id else None,
        "phase_state": {
            "conflict_resolution_pending": True,
        },
    }


__all__ = [
    "create_conflict_free_assets",
    "handle_conflicts",
]
