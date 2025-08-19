"""
Field Mapping Operations for Import Storage Management

Contains operations for managing field mappings for data imports.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union


from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.models.data_import import DataImport, ImportFieldMapping

from .helpers import extract_records_from_data

logger = get_logger(__name__)


class FieldMappingOperationsMixin:
    """
    Mixin class for field mapping operations.

    This class provides methods for managing import field mappings in the database.
    It's designed to be mixed into the main ImportStorageOperations class.
    """

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
        try:
            mappings_created = 0

            # Extract actual records from potentially nested structure
            extracted_records = extract_records_from_data(file_data)

            if extracted_records:
                # Create basic field mappings for each column using first record
                sample_record = extracted_records[0]

                # Import the intelligent mapping helper
                from app.api.v1.endpoints.data_import.field_mapping.utils import (
                    mapping_helpers,
                )

                calculate_mapping_confidence = (
                    mapping_helpers.calculate_mapping_confidence
                )
                intelligent_field_mapping = mapping_helpers.intelligent_field_mapping

                logger.info(
                    f"🔍 DEBUG: Sample record keys: {list(sample_record.keys())}"
                )
                logger.info(f"🔍 DEBUG: Sample record type: {type(sample_record)}")

                for field_name in sample_record.keys():
                    # NO HARDCODED SKIPPING - Let CrewAI agents decide what's metadata
                    # The agents should determine which fields are metadata vs real data

                    logger.info(
                        f"🔍 DEBUG: Processing field_name: {field_name} "
                        f"(type: {type(field_name)})"
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
                    f"✅ Created {mappings_created} field mappings for import "
                    f"{data_import.id}"
                )

            return mappings_created

        except Exception as e:
            logger.error(f"Failed to create field mappings: {e}")
            raise DatabaseError(f"Failed to create field mappings: {str(e)}")
