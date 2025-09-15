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
                logger.info(
                    f"💾 Creating {len(extracted_records)} RawImportRecord entries..."
                )

                # Store the raw records
                for idx, record in enumerate(extracted_records):
                    # SECURITY FIX: Validate record type before storing
                    if not isinstance(record, dict):
                        logger.warning(
                            f"🚨 Skipping non-dict record at index {idx}: {type(record)}"
                        )
                        continue

                    logger.debug(
                        f"💾 Creating RawImportRecord {idx+1} with fields: {list(record.keys())}"
                    )

                    raw_record = RawImportRecord(
                        id=uuid.uuid4(),
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

                # CRITICAL FIX: Add proper commit after adding records
                await self.db.flush()  # Ensure all operations are written to DB
                logger.info(
                    f"✅ Successfully added {records_stored} RawImportRecord entries "
                    f"to database session for import {data_import.id}"
                )
                logger.info(
                    "✅ Database flush completed - records should now be visible in raw_import_records table"
                )
            else:
                logger.error(
                    f"🚨 CRITICAL: No extracted records to process for import {data_import.id}"
                )
                logger.error("🚨 This means 0 raw_import_records will be created!")

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

            # CRITICAL FIX: Add ORDER BY row_number for stable results
            query = (
                select(RawImportRecord)
                .where(RawImportRecord.data_import_id == data_import_id)
                .order_by(RawImportRecord.row_number)
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
        master_flow_id: Optional[str] = None,
    ) -> int:
        """
        Update raw records with cleansed data and validation results.

        Args:
            data_import_id: The ID of the import
            cleansed_data: List of cleansed data records
            validation_results: Validation results (optional)
            master_flow_id: The master flow ID for proper asset association

        Returns:
            int: Number of records updated
        """
        try:
            logger.info(
                f"🔄 Updating raw records with cleansed data for import {data_import_id}"
            )
            logger.info(f"📊 Total cleansed_data input length: {len(cleansed_data)}")

            records_updated = 0
            valid_uuid_count = 0
            skipped_count = 0

            for record in cleansed_data:
                # Try to get record ID first (RawImportRecord.id)
                record_id = record.get("id")
                row_number = record.get("row_number")

                # CRITICAL FIX: Add row_number fallback when ID is missing
                if not record_id and row_number:
                    logger.info(
                        f"🔄 Using row_number fallback for record with row_number={row_number}"
                    )
                    # Create a copy without internal fields for storage
                    cleansed_record = {
                        k: v
                        for k, v in record.items()
                        if k not in ["id", "raw_import_record_id", "row_number"]
                    }

                    # Update by row_number instead of ID
                    update_values = {
                        "cleansed_data": cleansed_record,  # Save without internal fields
                        "is_processed": True,
                        "is_valid": record.get("is_valid", True),
                        "validation_errors": record.get("validation_errors"),
                    }

                    # Add master_flow_id if provided
                    if master_flow_id:
                        update_values["master_flow_id"] = (
                            uuid.UUID(master_flow_id)
                            if isinstance(master_flow_id, str)
                            else master_flow_id
                        )

                    update_stmt = (
                        update(RawImportRecord)
                        .where(
                            RawImportRecord.data_import_id == data_import_id,
                            RawImportRecord.row_number == row_number,
                            RawImportRecord.client_account_id
                            == uuid.UUID(self.client_account_id),
                        )
                        .values(**update_values)
                    )
                    result = await self.db.execute(update_stmt)

                    if result.rowcount > 0:
                        records_updated += 1
                        logger.debug(
                            f"✅ Updated record with row_number={row_number} successfully"
                        )
                    else:
                        logger.warning(
                            f"🚨 No rows updated for row_number={row_number} with data_import_id {data_import_id}"
                        )
                    continue

                if not record_id:
                    logger.warning(
                        f"🚨 Skipping record with no ID or row_number: {list(record.keys())}"
                    )
                    skipped_count += 1
                    continue

                # CRITICAL FIX: Convert record ID to UUID before comparing
                try:
                    record_uuid = uuid.UUID(str(record_id))
                    valid_uuid_count += 1
                    logger.debug(f"✅ Valid UUID {record_uuid} for record update")
                except Exception as uuid_error:
                    logger.warning(
                        f"🚨 Invalid record ID (not UUID): {record_id} - {uuid_error}"
                    )
                    skipped_count += 1
                    continue

                # Create a copy without internal fields for storage
                cleansed_record = {
                    k: v
                    for k, v in record.items()
                    if k not in ["id", "raw_import_record_id", "row_number"]
                }

                # CRITICAL FIX: Add tenant scoping for safety
                update_values = {
                    "cleansed_data": cleansed_record,  # Save without internal fields
                    "is_processed": True,
                    "is_valid": record.get("is_valid", True),
                    "validation_errors": record.get("validation_errors"),
                }

                # Add master_flow_id if provided
                if master_flow_id:
                    update_values["master_flow_id"] = (
                        uuid.UUID(master_flow_id)
                        if isinstance(master_flow_id, str)
                        else master_flow_id
                    )

                update_stmt = (
                    update(RawImportRecord)
                    .where(
                        RawImportRecord.id == record_uuid,  # Use UUID instead of string
                        RawImportRecord.data_import_id == data_import_id,
                        RawImportRecord.client_account_id
                        == uuid.UUID(self.client_account_id),  # Tenant scoping
                    )
                    .values(**update_values)
                )
                result = await self.db.execute(update_stmt)

                # CRITICAL FIX: Enhanced logging for debugging
                if result.rowcount > 0:
                    records_updated += 1
                    logger.debug(f"✅ Updated record {record_uuid} successfully")
                else:
                    logger.warning(
                        f"🚨 No rows updated for record UUID {record_uuid} with data_import_id {data_import_id}"
                    )
                    logger.warning(f"🚨 Record data: {record}")

            # CRITICAL FIX: Add proper commit after batch updates
            await self.db.flush()  # Ensure all updates are written to DB

            # CRITICAL: Comprehensive logging for debugging
            logger.info("📊 Processing summary:")
            logger.info(f"  - Valid UUIDs processed: {valid_uuid_count}")
            logger.info(f"  - Records skipped: {skipped_count}")
            logger.info(f"  - Records successfully updated: {records_updated}")
            logger.info(
                f"  - Records with rowcount=0: {valid_uuid_count - records_updated}"
            )

            logger.info(f"✅ Updated {records_updated} raw records with cleansed data.")
            return records_updated

        except Exception as e:
            logger.error(f"Failed to update raw records with cleansed data: {e}")
            return 0
