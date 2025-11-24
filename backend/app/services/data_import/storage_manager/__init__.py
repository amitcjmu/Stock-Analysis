"""
Storage Manager Package

This package contains the modularized components for import storage management:
- helpers: Utility functions for data processing
- operations: Core business logic operations (main coordination)
- record_operations: Raw import record management operations
- mapping_operations: Field mapping operations

All public APIs are re-exported for backward compatibility.
"""

import uuid
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_import import DataImport, RawImportRecord

from .helpers import extract_records_from_data
from .mapping_operations import FieldMappingOperationsMixin
from .operations import ImportStorageOperations
from .record_operations import RawRecordOperationsMixin


class ImportStorageManager:
    """
    Manages database storage operations for data imports.

    This is a facade class that maintains backward compatibility while
    delegating actual operations to modular components.
    """

    def __init__(self, db: AsyncSession, client_account_id: str):
        self.db = db
        self.client_account_id = client_account_id
        self._operations = ImportStorageOperations(db, client_account_id)

    # Backward compatibility method - delegate to helpers
    def _extract_records_from_data(self, data: Any) -> List[Dict[str, Any]]:
        """
        Extract actual data records from potentially nested JSON structures.

        This method is kept for backward compatibility and delegates to the
        helper function.
        """
        return extract_records_from_data(data)

    # Delegate all operations to the operations class
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
        return await self._operations.store_import_data(
            file_content=file_content,
            filename=filename,
            file_content_type=file_content_type,
            import_type=import_type,
            status=status,
            engagement_id=engagement_id,
            imported_by=imported_by,
            import_category=import_category,
            processing_config=processing_config,
        )

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
        return await self._operations.find_or_create_import(
            import_id=import_id,
            engagement_id=engagement_id,
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            file_type=file_type,
            intended_type=intended_type,
        )

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
        return await self._operations.store_raw_records(
            data_import=data_import,
            file_data=file_data,
            engagement_id=engagement_id,
        )

    async def create_field_mappings(
        self,
        data_import: DataImport,
        file_data: Union[List[Dict[str, Any]], Dict[str, Any]],
        master_flow_id: Optional[str] = None,
    ) -> int:
        """
        Create basic field mappings for the import.

        Args:
            data_import: The import record
            file_data: List of raw data records (or nested structure that
                       will be unwrapped)
            master_flow_id: Optional master flow ID to link to

        Returns:
            int: Number of field mappings created
        """
        return await self._operations.create_field_mappings(
            data_import=data_import,
            file_data=file_data,
            master_flow_id=master_flow_id,
        )

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
        return await self._operations.update_import_status(
            data_import=data_import,
            status=status,
            total_records=total_records,
            processed_records=processed_records,
            error_message=error_message,
            error_details=error_details,
        )

    async def get_import_by_id(self, import_id: str) -> Optional[DataImport]:
        """
        Get a data import record by its ID.

        Args:
            import_id: The ID of the import to retrieve

        Returns:
            Optional[DataImport]: The data import record, or None if not found
        """
        return await self._operations.get_import_by_id(import_id=import_id)

    async def get_import_data(self, data_import_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete import data including metadata and records.

        Args:
            data_import_id: The ID of the import to retrieve

        Returns:
            Dict containing import data and metadata, or None if not found
        """
        return await self._operations.get_import_data(data_import_id=data_import_id)

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
        return await self._operations.get_raw_records(
            data_import_id=data_import_id, limit=limit
        )

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
        return await self._operations.update_raw_records_with_cleansed_data(
            data_import_id=data_import_id,
            cleansed_data=cleansed_data,
            validation_results=validation_results,
            master_flow_id=master_flow_id,
        )

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
        return await self._operations.link_master_flow_to_import(
            data_import_id=data_import_id, master_flow_id=master_flow_id
        )

    async def update_import_with_flow_id(
        self, data_import_id: uuid.UUID, flow_id: str
    ) -> None:
        """
        Update the data import record with the master flow ID.

        Args:
            data_import_id: The ID of the data import to update
            flow_id: The master flow ID to link
        """
        return await self._operations.update_import_with_flow_id(
            data_import_id=data_import_id, flow_id=flow_id
        )


__all__ = [
    "extract_records_from_data",
    "ImportStorageOperations",
    "ImportStorageManager",
    "RawRecordOperationsMixin",
    "FieldMappingOperationsMixin",
]
