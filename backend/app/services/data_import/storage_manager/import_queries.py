"""
Import Queries Module

Contains read operations for data import storage management including:
- Retrieving import records by ID
- Getting complete import data with metadata and records
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.data_import import DataImport

logger = get_logger(__name__)


class ImportQueriesMixin:
    """
    Mixin providing read operations for import storage management.

    This mixin handles all query operations for retrieving data imports
    and their associated records.

    Required attributes:
        db: AsyncSession - Database session
        client_account_id: str - Client account identifier for multi-tenancy
    """

    db: AsyncSession
    client_account_id: str

    async def get_import_by_id(self, import_id: str) -> Optional[DataImport]:
        """
        Get a data import record by its ID.

        Args:
            import_id: The ID of the import to retrieve

        Returns:
            Optional[DataImport]: The data import record, or None if not found
        """
        try:
            logger.info(f"Retrieving data import record with ID: {import_id}")
            result = await self.db.execute(
                select(DataImport).where(DataImport.id == import_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get import by ID: {e}")
            return None

    async def get_import_data(self, data_import_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete import data including metadata and records.

        Args:
            data_import_id: The ID of the import to retrieve

        Returns:
            Dict containing import data and metadata, or None if not found
        """
        try:
            logger.info(f"Getting import data for ID: {data_import_id}")

            # Get the import record
            import_record = await self.get_import_by_id(data_import_id)
            if not import_record:
                logger.warning(f"No import found for ID: {data_import_id}")
                return None

            # Get raw records
            raw_records = await self.get_raw_records(
                (
                    data_import_id
                    if isinstance(data_import_id, uuid.UUID)
                    else uuid.UUID(data_import_id)
                ),
                limit=1000,
            )

            # Build response data, filtering out any row_index column
            # that might have been inadvertently added during processing
            data = []
            for record in raw_records:
                if record.raw_data:
                    # Filter out row_index if it exists (regression fix)
                    cleaned_data = {
                        k: v for k, v in record.raw_data.items() if k != "row_index"
                    }
                    data.append(cleaned_data)

            # Build metadata
            import_metadata = {
                "import_id": str(import_record.id),
                "filename": import_record.filename,
                "import_type": import_record.import_type,
                "status": import_record.status,
                "record_count": import_record.total_records or 0,
                "total_records": len(data),
                "actual_total_records": len(data),
                "imported_at": (
                    import_record.created_at.isoformat()
                    if import_record.created_at
                    else None
                ),
                "client_account_id": str(import_record.client_account_id),
                "engagement_id": str(import_record.engagement_id),
                "master_flow_id": (
                    str(import_record.master_flow_id)
                    if import_record.master_flow_id
                    else None
                ),
            }

            return {"data": data, "import_metadata": import_metadata, "success": True}

        except Exception as e:
            logger.error(f"Failed to get import data: {e}")
            return None
