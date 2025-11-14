"""
Import Commands Module

Contains write operations for data import storage management including:
- Creating and storing import records
- Updating import status and metadata
- Linking imports to master flows
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.models.data_import import DataImport, ImportFieldMapping, RawImportRecord

from .helpers import extract_records_from_data

logger = get_logger(__name__)


class ImportCommandsMixin:
    """
    Mixin providing write operations for import storage management.

    This mixin handles all create and update operations for data imports,
    including storing import data, updating status, and linking to master flows.

    Required attributes:
        db: AsyncSession - Database session
        client_account_id: str - Client account identifier for multi-tenancy
    """

    db: AsyncSession
    client_account_id: str

    async def store_import_data(
        self,
        file_content: bytes,
        filename: str,
        file_content_type: str,
        import_type: str,
        status: str = "processing",
        engagement_id: Optional[str] = None,
        imported_by: Optional[str] = None,
        import_category: Optional[str] = None,
        processing_config: Optional[Dict[str, Any]] = None,
    ) -> DataImport:
        """
        Store import data and create DataImport record.

        Args:
            file_content: The raw file content as bytes
            filename: Name of the imported file
            file_content_type: MIME type of the file
            import_type: Type of import (e.g., 'cmdb')
            import_category: High-level category for processor routing
            processing_config: Optional processor configuration overrides
            status: Initial status for the import
            engagement_id: Optional engagement ID
            imported_by: Optional user ID who imported

        Returns:
            DataImport: The created import record
        """
        try:
            # Generate new import ID
            import_id = uuid.uuid4()

            # Create DataImport record
            data_import = DataImport(
                id=import_id,
                client_account_id=self.client_account_id,
                engagement_id=engagement_id,
                import_name=f"{filename} Import",
                import_type=import_type,
                import_category=import_category,
                processing_config=processing_config or {},
                description=f"Data import for {import_type} category",
                filename=filename,
                file_size=len(file_content),
                mime_type=file_content_type,
                source_system=import_type,
                status=status,
                progress_percentage=0.0,
                total_records=0,
                processed_records=0,
                failed_records=0,
                imported_by=imported_by
                or "33333333-3333-3333-3333-333333333333",  # Demo user fallback
            )
            self.db.add(data_import)
            await self.db.flush()  # Get the record in session

            # Parse and store the file data as raw records
            parsed_data = json.loads(file_content.decode("utf-8"))
            data_type = "list" if isinstance(parsed_data, list) else "dict"
            data_size = len(parsed_data) if isinstance(parsed_data, list) else 1
            logger.info(
                f"📥 Parsed {len(file_content)} bytes as {data_type} with {data_size} items"
            )

            if parsed_data:
                # Extract actual records from potentially nested structure
                extracted_records = extract_records_from_data(parsed_data)
                logger.info(
                    f"📊 Extracted {len(extracted_records)} records for import {data_import.id}"
                )

                # CRITICAL FIX: Validate and fallback for empty extraction
                if not extracted_records and parsed_data:
                    if isinstance(parsed_data, dict) and parsed_data:
                        logger.warning(
                            "🚨 Empty extraction, using fallback to single-record"
                        )
                        extracted_records = [parsed_data]
                    elif isinstance(parsed_data, list) and parsed_data:
                        valid_records = [i for i in parsed_data if isinstance(i, dict)]
                        if valid_records:
                            extracted_records = valid_records
                            logger.info(
                                f"📊 Filtered to {len(valid_records)} valid records"
                            )

                # Store raw records within transaction
                if extracted_records:
                    records_stored = await self.store_raw_records(
                        data_import=data_import,
                        file_data=extracted_records,
                        engagement_id=engagement_id or "unknown",
                    )

                    # Update total records count
                    data_import.total_records = records_stored

                    # Flush changes without committing - let caller own transaction
                    await self.db.flush()
                    logger.info(
                        f"✅ Stored {records_stored} records for import {data_import.id}"
                    )
                else:
                    data_size = (
                        len(parsed_data) if isinstance(parsed_data, list) else "N/A"
                    )
                    logger.error(
                        f"🚨 No valid records for import {data_import.id} "
                        f"(type: {type(parsed_data).__name__}, size: {data_size})"
                    )
                    data_import.total_records = 0

            logger.info(f"✅ Created DataImport record: {data_import.id}")
            return data_import

        except Exception as e:
            logger.error(f"Failed to store import data: {e}")
            raise DatabaseError(f"Failed to store import data: {str(e)}")

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
                    f"No existing import record found. Creating new DataImport "
                    f"record with ID: {import_id}"
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
                    source_system=intended_type,  # Set source system based on type
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
            error_message: Optional error message
            error_details: Optional error details
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
                f"✅ Updated import {data_import.id} status to {status} "
                f"(progress: {data_import.progress_percentage}%)"
            )

        except Exception as e:
            logger.error(f"Failed to update import status: {e}")
            raise DatabaseError(f"Failed to update import status: {str(e)}")

    async def link_master_flow_to_import(
        self, data_import_id: uuid.UUID, master_flow_id: uuid.UUID
    ):
        """
        Links a master flow to all relevant records of a data import.

        This function ensures that the DataImport, all its RawImportRecords,
        and its ImportFieldMapping are all associated with a master_flow_id.
        This should be called within an existing transaction to prevent race
        conditions.

        Args:
            data_import_id: The ID of the data import.
            master_flow_id: The UUID of the master flow to link (this is the
                           flow_id from CrewAI).
        """
        logger.info(
            f"Linking master flow {master_flow_id} to data import {data_import_id} "
            f"and all associated records."
        )
        try:
            # First, get the database record ID for the CrewAI flow_id
            # Foreign key constraint references crewai_flow_state_extensions.id
            from sqlalchemy import select

            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )

            result = await self.db.execute(
                select(CrewAIFlowStateExtensions.flow_id).where(
                    CrewAIFlowStateExtensions.flow_id == master_flow_id
                )
            )
            actual_master_flow_id = result.scalar_one_or_none()

            if not actual_master_flow_id:
                raise ValueError(
                    f"Master flow with flow_id {master_flow_id} not found in database"
                )

            # CRITICAL FIX: Wrap batch updates in transaction for atomicity
            # Link the master flow to the main DataImport record
            stmt_data_import = (
                update(DataImport)
                .where(DataImport.id == data_import_id)
                .values(master_flow_id=actual_master_flow_id)
            )
            result_data_import = await self.db.execute(stmt_data_import)

            # CRITICAL FIX: Check rowcount to verify updates
            if result_data_import.rowcount == 0:
                logger.warning(
                    f"🚨 No DataImport record updated for ID {data_import_id}"
                )

            # Link the master flow to all RawImportRecord children
            stmt_raw_records = (
                update(RawImportRecord)
                .where(RawImportRecord.data_import_id == data_import_id)
                .values(master_flow_id=actual_master_flow_id)
            )
            result_raw_records = await self.db.execute(stmt_raw_records)
            logger.info(
                f"Updated {result_raw_records.rowcount} RawImportRecord(s) with master flow ID"
            )

            # Link the master flow to the ImportFieldMapping child
            stmt_field_mapping = (
                update(ImportFieldMapping)
                .where(ImportFieldMapping.data_import_id == data_import_id)
                .values(master_flow_id=actual_master_flow_id)
            )
            result_field_mapping = await self.db.execute(stmt_field_mapping)
            logger.info(
                f"Updated {result_field_mapping.rowcount} ImportFieldMapping(s) with master flow ID"
            )

            # CRITICAL FIX: Ensure all updates are committed
            await self.db.flush()

            logger.info(
                f"Successfully prepared linkage for master flow {master_flow_id} "
                f"to data import {data_import_id}."
            )
        except Exception as e:
            logger.error(
                f"Failed to link master flow {master_flow_id} to data import "
                f"{data_import_id}. Error: {e}",
                exc_info=True,
            )
            # Re-raise the exception to be handled by the calling transaction manager
            raise

    async def update_import_with_flow_id(
        self, data_import_id: uuid.UUID, flow_id: str
    ) -> None:
        """
        Update the data import record with the master flow ID.

        Args:
            data_import_id: The ID of the data import to update
            flow_id: The master flow ID to link
        """
        try:
            # Update the DataImport record with the master flow ID
            from sqlalchemy import update

            stmt = (
                update(DataImport)
                .where(DataImport.id == data_import_id)
                .values(master_flow_id=flow_id)
            )
            await self.db.execute(stmt)

            logger.info(
                f"✅ Linked master flow {flow_id} to data import {data_import_id}"
            )

        except Exception as e:
            logger.error(f"Failed to update import with flow ID: {e}")
            raise DatabaseError(f"Failed to update import with flow ID: {str(e)}")
