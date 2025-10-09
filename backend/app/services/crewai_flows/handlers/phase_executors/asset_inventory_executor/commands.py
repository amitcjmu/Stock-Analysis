"""
Asset Inventory Executor - Command Methods
Contains all database command methods for write operations.

CC: Command operations for marking records as processed and phase completion
"""

import logging
from typing import List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
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
        logger.error(f"❌ Failed to mark records as processed: {e}")
        # Don't raise - asset creation succeeded even if we can't mark records


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

        # Find the discovery flow
        result = await db.execute(
            select(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == flow_uuid,
                DiscoveryFlow.client_account_id == client_uuid,
                DiscoveryFlow.engagement_id == engagement_uuid,
            )
        )

        discovery_flow = result.scalar_one_or_none()

        if discovery_flow:
            # Mark asset_inventory phase as complete
            discovery_flow.asset_inventory_completed = True
            logger.info(
                f"✅ Marked asset_inventory_completed = True for flow {flow_id}"
            )

            # If this is the final phase of discovery, mark flow as completed
            if mark_flow_complete:
                discovery_flow.status = "completed"
                discovery_flow.completed_at = datetime.utcnow()
                logger.info(f"✅ Marked discovery flow {flow_id} as completed")

            await db.flush()
            logger.info(
                "✅ Successfully persisted asset_inventory completion to database"
            )
        else:
            logger.warning(f"⚠️ Could not find discovery flow for flow_id {flow_id}")

    except Exception as e:
        logger.error(f"❌ Failed to persist asset_inventory completion: {e}")
        # Don't raise - asset creation succeeded even if we can't mark phase complete


__all__ = ["mark_records_processed", "persist_asset_inventory_completion"]
