"""
Asset Inventory Executor - Command Methods
Contains all database command methods for write operations.

CC: Command operations for marking records as processed
"""

import logging
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_import.core import RawImportRecord

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


__all__ = ["mark_records_processed"]
