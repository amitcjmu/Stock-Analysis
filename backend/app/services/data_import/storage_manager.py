"""
Import Storage Manager Module

Handles all database storage operations including:
- Database storage operations and CRUD
- Data persistence and retrieval
- Storage optimization and indexing
- Raw record management
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.models.data_import import DataImport, ImportFieldMapping, RawImportRecord

logger = get_logger(__name__)


class ImportStorageManager:
    """
    Manages database storage operations for data imports.
    """

    def __init__(self, db: AsyncSession, client_account_id: str):
        self.db = db
        self.client_account_id = client_account_id

    async def find_or_create_import(
        self,
        import_id: uuid.UUID,
        engagement_id: str,
        user_id: str,
        filename: str,
        file_size: int,
        file_type: str,
        intended_type: str,
    ) -> DataImport:
        """
        Find an existing import or create a new one.

        Args:
            import_id: UUID of the import
            engagement_id: Engagement ID
            user_id: User who initiated the import
            filename: Name of the imported file
            file_size: Size of the file in bytes
            file_type: MIME type of the file
            intended_type: Type of data being imported

        Returns:
            DataImport: The found or created import record
        """
        try:
            logger.info(f"Looking for existing import record {import_id}")

            existing_import_query = select(DataImport).where(DataImport.id == import_id)
            result = await self.db.execute(existing_import_query)
            data_import = result.scalar_one_or_none()

            if not data_import:
                # Create new DataImport record since none exists
                logger.info(
                    f"No existing import record found. Creating new DataImport record with ID: {import_id}"
                )
                data_import = DataImport(
                    id=import_id,
                    client_account_id=self.client_account_id,
                    engagement_id=engagement_id,
                    import_name=f"{filename} Import",
                    import_type=intended_type,
                    description=f"Data import for {intended_type} category",
                    filename=filename,
                    file_size=file_size,
                    mime_type=file_type,
                    source_system=intended_type,  # Set source system based on intended type
                    status="pending",
                    progress_percentage=0.0,  # Initialize progress
                    total_records=0,  # Will be updated when records are stored
                    processed_records=0,
                    failed_records=0,
                    imported_by=user_id,
                )
                self.db.add(data_import)
                await self.db.flush()  # Flush to get the record in the session
                logger.info(f"✅ Created new DataImport record: {data_import.id}")
            else:
                logger.info(f"✅ Found existing DataImport record: {data_import.id}")

            return data_import

        except Exception as e:
            logger.error(f"Failed to find or create import record: {e}")
            raise DatabaseError(f"Failed to find or create import record: {str(e)}")

    async def store_raw_records(
        self,
        data_import: DataImport,
        file_data: List[Dict[str, Any]],
        engagement_id: str,
    ) -> int:
        """
        Store raw import records in the database.

        Args:
            data_import: The import record to associate with
            file_data: List of raw data records
            engagement_id: Engagement ID

        Returns:
            int: Number of records stored
        """
        try:
            records_stored = 0

            if file_data:
                # Store the raw records from the CSV
                for idx, record in enumerate(file_data):
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

    async def create_field_mappings(
        self,
        data_import: DataImport,
        file_data: List[Dict[str, Any]],
        master_flow_id: Optional[str] = None,
    ) -> int:
        """
        Create basic field mappings for the import.

        Args:
            data_import: The import record
            file_data: List of raw data records
            master_flow_id: Optional master flow ID to link to

        Returns:
            int: Number of field mappings created
        """
        try:
            mappings_created = 0

            if file_data:
                # Create basic field mappings for each column
                sample_record = file_data[0]

                # Import the intelligent mapping helper
                from app.api.v1.endpoints.data_import.field_mapping.utils.mapping_helpers import (
                    calculate_mapping_confidence,
                    intelligent_field_mapping,
                )

                logger.info(
                    f"🔍 DEBUG: Sample record keys: {list(sample_record.keys())}"
                )
                logger.info(f"🔍 DEBUG: Sample record type: {type(sample_record)}")

                for field_name in sample_record.keys():
                    # NO HARDCODED SKIPPING - Let CrewAI agents decide what's metadata
                    # The agents should determine which fields are metadata vs real data

                    logger.info(
                        f"🔍 DEBUG: Processing field_name: {field_name} (type: {type(field_name)})"
                    )

                    # Use intelligent mapping to get suggested target
                    suggested_target = intelligent_field_mapping(field_name)

                    # Calculate confidence if we have a mapping
                    confidence = 0.3  # Low confidence for unmapped fields
                    match_type = "unmapped"

                    if suggested_target:
                        confidence = calculate_mapping_confidence(
                            field_name, suggested_target
                        )
                        match_type = "intelligent"

                    field_mapping = ImportFieldMapping(
                        data_import_id=data_import.id,
                        client_account_id=self.client_account_id,
                        source_field=field_name,
                        target_field=suggested_target
                        or "UNMAPPED",  # Use UNMAPPED for fields without mapping
                        confidence_score=confidence,
                        match_type=match_type,
                        status="suggested",
                        master_flow_id=master_flow_id,
                    )
                    self.db.add(field_mapping)
                    mappings_created += 1

                logger.info(
                    f"✅ Created {mappings_created} field mappings for import {data_import.id}"
                )

            return mappings_created

        except Exception as e:
            logger.error(f"Failed to create field mappings: {e}")
            raise DatabaseError(f"Failed to create field mappings: {str(e)}")

    async def update_import_status(
        self,
        data_import: DataImport,
        status: str,
        total_records: int = 0,
        processed_records: int = 0,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update the import status and record counts.

        Args:
            data_import: The import record to update
            status: New status for the import
            total_records: Total number of records
            processed_records: Number of processed records
        """
        try:
            data_import.status = status
            data_import.total_records = total_records
            data_import.processed_records = processed_records

            # Calculate and update progress percentage
            if total_records > 0:
                data_import.progress_percentage = (
                    processed_records / total_records
                ) * 100
            else:
                data_import.progress_percentage = 0.0

            if status == "completed":
                data_import.completed_at = datetime.utcnow()
                data_import.progress_percentage = 100.0
            elif status == "discovery_initiated":
                data_import.progress_percentage = 10.0  # Discovery flow started
            elif status in ["failed", "discovery_failed"]:
                data_import.error_message = error_message
                data_import.error_details = error_details
                # Keep existing progress percentage on failure

            logger.info(
                f"✅ Updated import {data_import.id} status to {status} (progress: {data_import.progress_percentage}%)"
            )

        except Exception as e:
            logger.error(f"Failed to update import status: {e}")
            raise DatabaseError(f"Failed to update import status: {str(e)}")

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

    async def link_master_flow_to_import(
        self, data_import_id: uuid.UUID, master_flow_id: uuid.UUID
    ):
        """
        Links a master flow to all relevant records of a data import.

        This function ensures that the DataImport, all its RawImportRecords, and its
        ImportFieldMapping are all associated with a master_flow_id. This should be
        called within an existing transaction to prevent race conditions.

        Args:
            data_import_id: The ID of the data import.
            master_flow_id: The UUID of the master flow to link (this is the flow_id from CrewAI).
        """
        logger.info(
            f"Linking master flow {master_flow_id} to data import {data_import_id} and all associated records."
        )
        try:
            # First, get the database record ID for the CrewAI flow_id
            # The foreign key constraint references crewai_flow_state_extensions.id, not flow_id
            from sqlalchemy import select

            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )

            result = await self.db.execute(
                select(CrewAIFlowStateExtensions.id).where(
                    CrewAIFlowStateExtensions.flow_id == master_flow_id
                )
            )
            flow_record = result.scalar_one_or_none()

            if not flow_record:
                raise ValueError(
                    f"Master flow with flow_id {master_flow_id} not found in database"
                )

            # Use the database record ID for the foreign key
            actual_master_flow_id = flow_record

            # Link the master flow to the main DataImport record
            stmt_data_import = (
                update(DataImport)
                .where(DataImport.id == data_import_id)
                .values(master_flow_id=actual_master_flow_id)
            )
            await self.db.execute(stmt_data_import)

            # Link the master flow to all RawImportRecord children
            stmt_raw_records = (
                update(RawImportRecord)
                .where(RawImportRecord.data_import_id == data_import_id)
                .values(master_flow_id=actual_master_flow_id)
            )
            await self.db.execute(stmt_raw_records)

            # Link the master flow to the ImportFieldMapping child
            stmt_field_mapping = (
                update(ImportFieldMapping)
                .where(ImportFieldMapping.data_import_id == data_import_id)
                .values(master_flow_id=actual_master_flow_id)
            )
            await self.db.execute(stmt_field_mapping)

            logger.info(
                f"Successfully prepared linkage for master flow {master_flow_id} to data import {data_import_id}."
            )
        except Exception as e:
            logger.error(
                f"Failed to link master flow {master_flow_id} to data import {data_import_id}. Error: {e}",
                exc_info=True,
            )
            # Re-raise the exception to be handled by the calling transaction manager
            raise
