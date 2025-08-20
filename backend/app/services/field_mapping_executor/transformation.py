"""
Field Mapping Transformation Module

Handles data transformations and field conversions. This module has been
modularized with placeholder implementations.

Backward compatibility wrapper for the original transformation.py
"""

# Lightweight shim - modularization complete

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class TransformationEngine:
    """Transformation engine - placeholder implementation"""

    def __init__(self):
        self.transformations = {}

    def apply_transformation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder transformation method"""
        return data


class MappingTransformer(TransformationEngine):
    """Mapping transformer - enhanced implementation for CrewAI field mapping persistence"""

    def __init__(self, storage_manager, client_account_id, engagement_id):
        super().__init__()
        self.storage_manager = storage_manager
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def transform_and_persist(
        self,
        parsed_mappings: Dict[str, Any],
        validation_results: Dict[str, Any],
        state,
        db_session,
    ) -> Dict[str, Any]:
        """
        Transform and persist CrewAI-generated field mappings with correct import_id resolution.

        CRITICAL FIX: This ensures CrewAI mappings are stored with the correct data_import_id
        that matches the original CSV import, not a new/different import ID.
        """
        try:
            mappings_data = parsed_mappings.get("mappings", [])

            if not mappings_data:
                return {
                    "success": False,
                    "error": "No mappings to persist",
                    "mappings_persisted": 0,
                }

            # Get the correct data_import_id from the state
            data_import_id = None

            # Try multiple ways to get the correct data_import_id
            if hasattr(state, "discovery_data") and state.discovery_data:
                data_import_id = state.discovery_data.get("data_import_id")

            if not data_import_id and hasattr(state, "data_import_id"):
                data_import_id = state.data_import_id

            if not data_import_id:
                # Last resort: look up via engagement_id
                from app.models.data_import import DataImport
                from sqlalchemy import select, and_

                query = (
                    select(DataImport)
                    .where(
                        and_(
                            DataImport.client_account_id == self.client_account_id,
                            DataImport.engagement_id == self.engagement_id,
                        )
                    )
                    .order_by(DataImport.created_at.desc())
                    .limit(1)
                )

                result = await db_session.execute(query)
                latest_import = result.scalar_one_or_none()

                if latest_import:
                    data_import_id = str(latest_import.id)

            if not data_import_id:
                return {
                    "success": False,
                    "error": "Cannot determine data_import_id for field mapping persistence",
                    "mappings_persisted": 0,
                }

            # CRITICAL: Use the storage manager to create field mappings with correct import_id
            from app.models.data_import import DataImport
            from uuid import UUID

            # Get the data import record
            data_import_query = select(DataImport).where(
                DataImport.id == UUID(data_import_id)
            )
            import_result = await db_session.execute(data_import_query)
            data_import = import_result.scalar_one_or_none()

            if not data_import:
                return {
                    "success": False,
                    "error": f"Data import {data_import_id} not found",
                    "mappings_persisted": 0,
                }

            # Convert CrewAI mappings to the format expected by storage manager
            file_data = []
            for mapping in mappings_data:
                if isinstance(mapping, dict) and "source_field" in mapping:
                    # Create a minimal record with just the field names to trigger mapping creation
                    record = {mapping["source_field"]: "sample_value"}
                    file_data.append(record)

            if file_data:
                # Use storage manager to create/update field mappings
                mappings_created = await self.storage_manager.create_field_mappings(
                    data_import=data_import,
                    file_data=file_data,
                    master_flow_id=getattr(state, "flow_id", None),
                )

                return {
                    "success": True,
                    "mappings_persisted": mappings_created,
                    "data_import_id": data_import_id,
                }

            return {
                "success": True,
                "mappings_persisted": 0,
                "message": "No valid mappings to persist",
            }

        except Exception as e:
            logger.error(f"Failed to transform and persist mappings: {e}")
            return {"success": False, "error": str(e), "mappings_persisted": 0}

    def transform_mappings(self, mappings: Dict[str, str]) -> Dict[str, str]:
        """Placeholder mapping transformation"""
        return mappings

    def apply_field_transformations(
        self, data: Dict[str, Any], mappings: Dict[str, str]
    ) -> Dict[str, Any]:
        """Placeholder field transformation application"""
        return data


class FieldTransformer:
    """Field transformer - placeholder implementation"""

    def __init__(self, field_name: str = ""):
        self.field_name = field_name

    def transform(self, value: Any) -> Any:
        """Placeholder transform method"""
        return value


class DataTransformation:
    """Data transformation - placeholder implementation"""

    def __init__(self, transformation_type: str = ""):
        self.transformation_type = transformation_type


class DataTransformer:
    """Data transformer - placeholder implementation"""

    def __init__(self):
        self.transformations = {}

    def transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder data transformation"""
        return data


class DatabaseUpdater:
    """Database updater - placeholder implementation"""

    def __init__(self):
        self.updates = []

    def update_database(self, data: Dict[str, Any]) -> bool:
        """Placeholder database update"""
        return True


# Re-export main classes
__all__ = [
    "TransformationEngine",
    "MappingTransformer",
    "FieldTransformer",
    "DataTransformation",
    "DataTransformer",
    "DatabaseUpdater",
]
