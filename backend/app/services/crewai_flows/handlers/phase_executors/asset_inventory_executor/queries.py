"""
Asset Inventory Executor - Query Methods
Contains all database query methods for retrieving data.

CC: Query operations for raw records and field mappings
"""

import logging
from typing import Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_import.core import RawImportRecord

logger = logging.getLogger(__name__)


async def get_raw_records(
    db: AsyncSession,
    data_import_id: str,
    client_account_id: str,
    engagement_id: str,
) -> List[RawImportRecord]:
    """Get raw import records by data_import_id with tenant scoping.

    CC: Raw records are linked by data_import_id, NOT master_flow_id.
    This is the correct field to query as raw records are uploaded via data imports.
    """
    try:
        stmt = select(RawImportRecord).where(
            RawImportRecord.data_import_id == UUID(data_import_id),
            RawImportRecord.client_account_id == UUID(client_account_id),
            RawImportRecord.engagement_id == UUID(engagement_id),
        )
        result = await db.execute(stmt)
        records = result.scalars().all()

        logger.info(
            f"📊 Retrieved {len(records)} raw import records for data_import_id {data_import_id}"
        )
        return list(records)

    except Exception as e:
        logger.error(f"❌ Failed to retrieve raw import records: {e}")
        raise


async def get_field_mappings(
    db: AsyncSession,
    data_import_id: str,
    client_account_id: str,
) -> Dict[str, str]:
    """Get approved field mappings for the data import.

    Returns:
        Dictionary mapping source_field to target_field for approved mappings
    """
    try:
        from app.models.data_import.mapping import ImportFieldMapping

        stmt = select(ImportFieldMapping).where(
            ImportFieldMapping.data_import_id == UUID(data_import_id),
            ImportFieldMapping.client_account_id == UUID(client_account_id),
            ImportFieldMapping.status == "approved",
        )
        result = await db.execute(stmt)
        mappings = result.scalars().all()

        # Build lookup dictionary: source_field -> target_field
        mapping_dict = {
            mapping.source_field: mapping.target_field for mapping in mappings
        }

        logger.debug(
            f"📋 Retrieved {len(mapping_dict)} approved field mappings: {mapping_dict}"
        )
        return mapping_dict

    except Exception as e:
        logger.warning(f"⚠️ Failed to retrieve field mappings: {e}")
        return {}  # Return empty dict to allow asset creation to proceed


__all__ = ["get_raw_records", "get_field_mappings"]
