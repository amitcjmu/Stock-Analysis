"""
Field Mapping Operations for Import Storage Management

Contains operations for managing field mappings for data imports.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union


from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.models.data_import import DataImport, ImportFieldMapping
from sqlalchemy import and_, delete

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

                logger.debug(
                    f"Processing field mapping - record field count: {len(sample_record.keys())}"
                )
                logger.debug(f"Sample record type: {type(sample_record)}")

                for field_name in sample_record.keys():
                    # CRITICAL SECURITY FIX: Filter out JSON artifacts and CrewAI metadata
                    # These should never be treated as actual CSV field names

                    # Define prohibited field names that indicate JSON artifacts
                    json_artifacts = {
                        "mappings",
                        "skipped_fields",
                        "synthesis_required",
                        "confidence_scores",
                        "agent_reasoning",
                        "transformations",
                        "validation_results",
                        "agent_insights",
                        "unmapped_fields",
                        "clarifications",
                        "next_phase",
                        "timestamp",
                        "execution_metadata",
                        "raw_response",
                        "success",
                        "error",
                        "phase_name",
                        "{}",
                        "[]",
                        "null",
                        "undefined",
                        "true",
                        "false",
                    }

                    # Convert field_name to string and check for artifacts
                    field_name_str = str(field_name).strip()

                    # Skip field names that are JSON artifacts or CrewAI metadata
                    if field_name_str.lower() in json_artifacts or field_name_str in [
                        "{",
                        "}",
                        "[",
                        "]",
                    ]:
                        logger.warning(
                            f"🚨 SECURITY FIX: Skipping JSON artifact field name: '{field_name_str}' "
                            f"(This is metadata, not a real CSV column)"
                        )
                        continue

                    # Skip field names that look like JSON structures
                    # Only skip if string starts AND ends with brackets/braces (reduce false positives)
                    if (
                        field_name_str.startswith("{") and field_name_str.endswith("}")
                    ) or (
                        field_name_str.startswith("[") and field_name_str.endswith("]")
                    ):
                        logger.warning(
                            f"🚨 SECURITY FIX: Skipping JSON-like field name: '{field_name_str}' "
                            f"(Appears to be JSON structure, not CSV column)"
                        )
                        continue

                    logger.debug(
                        f"Processing valid field_name: {field_name_str} "
                        f"(type: {type(field_name)})"
                    )

                    # Use intelligent mapping to get suggested target (using sanitized field name)
                    suggested_target = intelligent_field_mapping(field_name_str)

                    # Calculate confidence if we have a mapping
                    confidence = 0.3  # Low confidence for unmapped fields
                    match_type = "unmapped"

                    if suggested_target:
                        confidence = calculate_mapping_confidence(
                            field_name_str, suggested_target
                        )
                        match_type = "intelligent"

                    field_mapping = ImportFieldMapping(
                        data_import_id=data_import.id,
                        client_account_id=self.client_account_id,
                        source_field=field_name_str,  # Use sanitized field name
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

    async def cleanup_json_artifact_mappings(self, data_import: DataImport) -> int:
        """
        Clean up existing field mappings that contain JSON artifacts.

        This method removes any field mappings where the source_field contains
        JSON metadata keys like "mappings", "skipped_fields", etc.

        Args:
            data_import: The import record to clean up

        Returns:
            int: Number of artifact mappings removed
        """
        try:
            # Define the same prohibited field names as in create_field_mappings
            json_artifacts = {
                "mappings",
                "skipped_fields",
                "synthesis_required",
                "confidence_scores",
                "agent_reasoning",
                "transformations",
                "validation_results",
                "agent_insights",
                "unmapped_fields",
                "clarifications",
                "next_phase",
                "timestamp",
                "execution_metadata",
                "raw_response",
                "success",
                "error",
                "phase_name",
                "{}",
                "[]",
                "null",
                "undefined",
                "true",
                "false",
            }

            # Convert to list for SQL IN clause
            artifact_list = list(json_artifacts)

            # Delete mappings with JSON artifact source fields
            delete_query = delete(ImportFieldMapping).where(
                and_(
                    ImportFieldMapping.data_import_id == data_import.id,
                    ImportFieldMapping.client_account_id == self.client_account_id,
                    ImportFieldMapping.source_field.in_(artifact_list),
                )
            )

            result = await self.db.execute(delete_query)
            # Flush without committing - let caller own transaction
            await self.db.flush()

            removed_count = result.rowcount

            if removed_count > 0:
                logger.info(
                    f"🧹 CLEANUP: Removed {removed_count} JSON artifact field mappings "
                    f"from import {data_import.id}"
                )
            else:
                logger.info(
                    f"✅ CLEANUP: No JSON artifact field mappings found for import {data_import.id}"
                )

            return removed_count

        except Exception as e:
            logger.error(f"Failed to clean up JSON artifact mappings: {e}")
            raise DatabaseError(f"Failed to clean up JSON artifact mappings: {str(e)}")
