"""
Asset Inventory Executor - Command Methods
Contains all database command methods for write operations.

CC: Command operations for marking records as processed and phase completion
"""

import logging
from typing import List
from uuid import UUID
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_import.core import RawImportRecord
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


async def mark_records_processed(
    db: AsyncSession, raw_records: List[RawImportRecord], created_assets: List
) -> None:
    """Mark raw import records as processed."""
    try:
        # Create asset mapping for linking
        asset_mapping = {}
        for asset in created_assets:
            if asset.raw_import_records_id:
                asset_mapping[asset.raw_import_records_id] = asset.id

        # Update records
        for record in raw_records:
            record.is_processed = True
            record.asset_id = asset_mapping.get(record.id)
            # Don't set processed_at here - let the database handle it

        await db.flush()  # Ensure updates are written
        logger.info(f"✅ Marked {len(raw_records)} raw records as processed")

    except Exception as e:
        logger.error(f"❌ CRITICAL: Failed to mark records as processed: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        # CC: RAISE exception - this is critical for preventing infinite loops
        # If we can't mark records as processed, we'll re-process them after conflict resolution
        raise RuntimeError(
            f"Failed to mark raw_import_records as processed: {e}"
        ) from e


async def persist_asset_inventory_completion(
    db: AsyncSession,
    flow_id: str,
    client_account_id: str,
    engagement_id: str,
    mark_flow_complete: bool = True,
) -> None:
    """
    Mark asset_inventory phase as complete and optionally complete the entire discovery flow.

    Args:
        db: Active database session
        flow_id: The discovery flow ID
        client_account_id: Client account UUID
        engagement_id: Engagement UUID
        mark_flow_complete: If True, mark the entire discovery flow as completed
    """
    try:
        # Convert to UUID if needed
        flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id
        client_uuid = (
            UUID(client_account_id)
            if isinstance(client_account_id, str)
            else client_account_id
        )
        engagement_uuid = (
            UUID(engagement_id) if isinstance(engagement_id, str) else engagement_id
        )

        # Use atomic UPDATE to prevent race conditions (Qodo Issue #1)
        # Build update values based on mark_flow_complete flag
        update_values = {"asset_inventory_completed": True}
        if mark_flow_complete:
            update_values["status"] = "completed"
            update_values["completed_at"] = datetime.utcnow()

        update_stmt = (
            update(DiscoveryFlow)
            .where(
                DiscoveryFlow.flow_id == flow_uuid,
                DiscoveryFlow.client_account_id == client_uuid,
                DiscoveryFlow.engagement_id == engagement_uuid,
            )
            .values(**update_values)
        )

        result = await db.execute(update_stmt)
        await db.flush()  # Flush to ensure statement is executed
        # CC: Don't commit here - transaction managed by caller (phase executor)

        if result.rowcount > 0:
            logger.info(
                f"✅ Marked asset_inventory_completed = True for flow {flow_id}"
            )
            if mark_flow_complete:
                logger.info(f"✅ Marked discovery flow {flow_id} as completed")
            logger.info(
                "✅ Successfully persisted asset_inventory completion to database"
            )
        else:
            error_msg = f"Discovery flow not found for flow_id {flow_id} - UPDATE returned 0 rows"
            logger.error(f"❌ CRITICAL: {error_msg}")
            raise ValueError(error_msg)

    except Exception as e:
        logger.error(f"❌ CRITICAL: Failed to persist asset_inventory completion: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        # CC: RAISE exception - this is critical for preventing infinite loops
        # If asset_inventory_completed doesn't get set to True, flow will re-execute after conflict resolution
        raise RuntimeError(
            f"Failed to persist asset_inventory_completed flag: {e}"
        ) from e


__all__ = ["mark_records_processed", "persist_asset_inventory_completion"]
