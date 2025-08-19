"""
Raw Record Operations for Import Storage Management

Contains operations for managing raw import records in the database.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import select, update

from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.models.data_import import DataImport, RawImportRecord

from .helpers import extract_records_from_data

logger = get_logger(__name__)


class RawRecordOperationsMixin:
    """
    Mixin class for raw import record operations.

    This class provides methods for managing raw import records in the database.
    It's designed to be mixed into the main ImportStorageOperations class.
    """

    async def store_raw_records(
        self,
        data_import: DataImport,
        file_data: Union[List[Dict[str, Any]], Dict[str, Any]],
        engagement_id: str,
    ) -> int:
        """
        Store raw import records in the database.

        Args:
            data_import: The import record to associate with
            file_data: List of raw data records (or nested structure that
                       will be unwrapped)
            engagement_id: Engagement ID

        Returns:
            int: Number of records stored
        """
        try:
            records_stored = 0

            # Extract actual records from potentially nested structure
            # This handles cases where file_data might be passed as {"data": [records]}
            # instead of just [records]
            extracted_records = extract_records_from_data(file_data)

            logger.info(
                f"📊 Processing {len(extracted_records)} records for import "
                f"{data_import.id}"
            )

            if extracted_records:
                # Store the raw records
                for idx, record in enumerate(extracted_records):
                    raw_record = RawImportRecord(
                        data_import_id=data_import.id,
                        client_account_id=self.client_account_id,
                        engagement_id=engagement_id,
                        row_number=idx + 1,
                        raw_data=record,
                        is_processed=False,
                        is_valid=True,
                    )
                    self.db.add(raw_record)
                    records_stored += 1

                logger.info(
                    f"✅ Stored {records_stored} raw records for import {data_import.id}"
                )

            return records_stored

        except Exception as e:
            logger.error(f"Failed to store raw records: {e}")
            raise DatabaseError(f"Failed to store raw records: {str(e)}")

    async def get_raw_records(
        self, data_import_id: uuid.UUID, limit: int = 1000
    ) -> List[RawImportRecord]:
        """
        Get raw import records for a given import ID.

        Args:
            data_import_id: The ID of the import
            limit: The maximum number of records to return

        Returns:
            List[RawImportRecord]: A list of raw import records
        """
        try:
            logger.info(
                f"Retrieving raw records for import {data_import_id} (limit: {limit})"
            )

            query = (
                select(RawImportRecord)
                .where(RawImportRecord.data_import_id == data_import_id)
                .limit(limit)
            )

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Failed to get raw records: {e}")
            return []

    async def update_raw_records_with_cleansed_data(
        self,
        data_import_id: uuid.UUID,
        cleansed_data: List[Dict[str, Any]],
        validation_results: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Update raw records with cleansed data and validation results.

        Args:
            data_import_id: The ID of the import
            cleansed_data: List of cleansed data records
            validation_results: Validation results (optional)

        Returns:
            int: Number of records updated
        """
        try:
            logger.info(
                f"Updating raw records with cleansed data for import {data_import_id}"
            )
            records_updated = 0

            for record in cleansed_data:
                # Assuming 'id' in the cleansed data corresponds to RawImportRecord.id
                record_id = record.get("id")
                if not record_id:
                    continue

                update_stmt = (
                    update(RawImportRecord)
                    .where(
                        RawImportRecord.id == record_id,
                        RawImportRecord.data_import_id == data_import_id,
                    )
                    .values(
                        cleansed_data=record,
                        is_processed=True,
                        is_valid=record.get("is_valid", True),
                        validation_errors=record.get("validation_errors"),
                    )
                )
                await self.db.execute(update_stmt)
                records_updated += 1

            logger.info(f"✅ Updated {records_updated} raw records with cleansed data.")
            return records_updated

        except Exception as e:
            logger.error(f"Failed to update raw records with cleansed data: {e}")
            return 0
