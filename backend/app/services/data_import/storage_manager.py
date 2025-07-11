"""
Import Storage Manager Module

Handles all database storage operations including:
- Database storage operations and CRUD
- Data persistence and retrieval
- Storage optimization and indexing
- Raw record management
"""

import logging
import uuid as uuid_pkg
from typing import Dict, List, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.core.logging import get_logger
from app.core.exceptions import DatabaseError
from app.models.data_import import DataImport, RawImportRecord, ImportFieldMapping

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
        import_id: uuid_pkg.UUID,
        engagement_id: str,
        user_id: str,
        filename: str,
        file_size: int,
        file_type: str,
        intended_type: str
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
                logger.info(f"No existing import record found. Creating new DataImport record with ID: {import_id}")
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
                    status="pending",
                    imported_by=user_id
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
        engagement_id: str
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
                        is_valid=True
                    )
                    self.db.add(raw_record)
                    records_stored += 1
                    
                logger.info(f"✅ Stored {records_stored} raw records for import {data_import.id}")
            
            return records_stored
            
        except Exception as e:
            logger.error(f"Failed to store raw records: {e}")
            raise DatabaseError(f"Failed to store raw records: {str(e)}")
    
    async def create_field_mappings(
        self, 
        data_import: DataImport,
        file_data: List[Dict[str, Any]],
        master_flow_id: Optional[str] = None
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
                for field_name in sample_record.keys():
                    field_mapping = ImportFieldMapping(
                        data_import_id=data_import.id,
                        client_account_id=self.client_account_id,
                        source_field=field_name,
                        target_field=field_name.lower().replace(' ', '_'),
                        confidence_score=0.8,  # Default confidence
                        match_type="direct",
                        status="suggested",
                        master_flow_id=master_flow_id
                    )
                    self.db.add(field_mapping)
                    mappings_created += 1
                    
                logger.info(f"✅ Created {mappings_created} field mappings for import {data_import.id}")
            
            return mappings_created
            
        except Exception as e:
            logger.error(f"Failed to create field mappings: {e}")
            raise DatabaseError(f"Failed to create field mappings: {str(e)}")
    
    async def update_import_status(
        self, 
        data_import: DataImport,
        status: str,
        total_records: int = 0,
        processed_records: int = 0
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
            
            if status == "completed":
                data_import.completed_at = datetime.utcnow()
                
            logger.info(f"✅ Updated import {data_import.id} status to {status}")
            
        except Exception as e:
            logger.error(f"Failed to update import status: {e}")
            raise DatabaseError(f"Failed to update import status: {str(e)}")
    
    async def update_field_mappings_with_flow(
        self, 
        data_import_id: uuid_pkg.UUID,
        master_flow_id: str
    ) -> None:
        """
        Update field mappings with the master flow ID after flow creation.
        
        Args:
            data_import_id: ID of the data import
            master_flow_id: ID of the master flow to link to
        """
        try:
            # Verify the master flow exists first
            from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
            
            check_query = select(CrewAIFlowStateExtensions.flow_id).where(
                CrewAIFlowStateExtensions.flow_id == master_flow_id,
                CrewAIFlowStateExtensions.client_account_id == self.client_account_id
            )
            result = await self.db.execute(check_query)
            master_flow_exists = result.scalar() is not None
            
            if master_flow_exists:
                update_stmt = update(ImportFieldMapping).where(
                    ImportFieldMapping.data_import_id == data_import_id
                ).values(master_flow_id=master_flow_id, updated_at=func.now())
                await self.db.execute(update_stmt)
                logger.info(f"✅ Updated field mappings with master_flow_id: {master_flow_id}")
            else:
                logger.warning(f"⚠️ Master flow {master_flow_id} not found - skipping field mapping update")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to update field mappings with flow ID (non-critical): {e}")
    
    async def get_import_by_id(self, import_id: str) -> Optional[DataImport]:
        """
        Retrieve a data import by its ID.
        
        Args:
            import_id: ID of the import to retrieve
            
        Returns:
            DataImport or None if not found
        """
        try:
            import_query = select(DataImport).where(DataImport.id == import_id)
            result = await self.db.execute(import_query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to retrieve import {import_id}: {e}")
            return None
    
    async def get_raw_records(
        self, 
        data_import_id: uuid_pkg.UUID,
        limit: int = 1000
    ) -> List[RawImportRecord]:
        """
        Retrieve raw import records for a data import.
        
        Args:
            data_import_id: ID of the data import
            limit: Maximum number of records to retrieve
            
        Returns:
            List of RawImportRecord objects
        """
        try:
            records_query = (
                select(RawImportRecord)
                .where(RawImportRecord.data_import_id == data_import_id)
                .order_by(RawImportRecord.row_number)
                .limit(limit)
            )
            
            result = await self.db.execute(records_query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to retrieve raw records: {e}")
            return []