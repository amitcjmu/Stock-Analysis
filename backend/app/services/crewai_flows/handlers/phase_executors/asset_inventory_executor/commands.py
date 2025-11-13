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
    """
    Mark raw import records as processed using SQL Core updates.

    Uses SQLAlchemy Core update() statements instead of ORM attribute assignment
    to avoid potential greenlet context issues with async sessions.
    This approach is aligned with our async/tenant-safe architectural patterns.
    """
    try:
        # Build mapping of raw_import_records_id -> asset.id
        # Access attributes while objects are in the same session context
        asset_mapping = {}
        for asset in created_assets:
            raw_record_id = getattr(asset, "raw_import_records_id", None)
            if raw_record_id is not None:
                asset_mapping[raw_record_id] = asset.id

        # Use SQL Core UPDATE statements to avoid ORM attribute access after flush
        # This is the architecturally correct approach per our SQLAlchemy patterns
        for record in raw_records:
            await db.execute(
                update(RawImportRecord)
                .where(RawImportRecord.id == record.id)
                .values(is_processed=True, asset_id=asset_mapping.get(record.id))
            )

        await db.flush()  # Ensure updates are written
        logger.info(f"✅ Marked {len(raw_records)} raw records as processed")

    except Exception as e:
        logger.error(f"❌ CRITICAL: Failed to mark records as processed: {e}")
        import traceback

        # CC: Security fix - Log full traceback only at DEBUG level to prevent information disclosure
        # Production logs (ERROR level) won't expose internal paths/environment details
        logger.debug(f"Traceback: {traceback.format_exc()}")
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

                # Also update master flow status (per ADR-012 - Issue #594)
                from app.services.crewai_flows.flow_state_manager import (
                    FlowStateManager,
                )
                from app.core.context import RequestContext

                context = RequestContext(
                    client_account_id=str(client_account_id),
                    engagement_id=str(engagement_id),
                    flow_id=str(flow_uuid),
                )

                state_manager = FlowStateManager(db, context)
                await state_manager.update_master_flow_status(
                    flow_id=str(flow_uuid),
                    new_status="completed",
                    metadata={
                        "completed_phase": "asset_inventory",
                        "completed_at": datetime.utcnow().isoformat(),
                    },
                )
                logger.info(f"✅ Updated master flow {flow_id} status to completed")

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

        # CC: Security fix - Log full traceback only at DEBUG level to prevent information disclosure
        # Production logs (ERROR level) won't expose internal paths/environment details
        logger.debug(f"Traceback: {traceback.format_exc()}")
        # CC: RAISE exception - this is critical for preventing infinite loops
        # If asset_inventory_completed doesn't get set to True, flow will re-execute after conflict resolution
        raise RuntimeError(
            f"Failed to persist asset_inventory_completed flag: {e}"
        ) from e


__all__ = ["mark_records_processed", "persist_asset_inventory_completion"]
