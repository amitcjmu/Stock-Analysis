"""
Data Utilities Module

This module contains data loading and manipulation utilities extracted from the base_flow.py
to improve maintainability and code organization.
"""

import logging
import uuid
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DataUtilities:
    """
    Handles data loading and manipulation operations for the UnifiedDiscoveryFlow
    """

    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance"""
        self.flow = flow_instance
        self.logger = logger

    async def load_raw_data_from_database(self, state):
        """Load raw data from database tables into flow state"""
        try:
            flow_id_to_use = self.flow._flow_id
            self.logger.info(f"🔍 Loading raw data for flow {flow_id_to_use}")

            from sqlalchemy import select

            from app.core.database import AsyncSessionLocal
            from app.models.data_import import DataImport, RawImportRecord
            from app.models.discovery_flow import DiscoveryFlow

            async with AsyncSessionLocal() as db:
                # First, try to get the discovery flow record
                flow_query = select(DiscoveryFlow).where(
                    DiscoveryFlow.flow_id == flow_id_to_use
                )
                flow_result = await db.execute(flow_query)
                discovery_flow = flow_result.scalar_one_or_none()

                data_import_id = None

                if discovery_flow and discovery_flow.data_import_id:
                    data_import_id = discovery_flow.data_import_id
                    self.logger.info(
                        f"🔍 Found discovery flow with data_import_id: {data_import_id}"
                    )
                else:
                    # Fallback: Check if flow_id is actually a data_import_id
                    self.logger.info(
                        f"🔍 No discovery flow found, checking if {flow_id_to_use} is a data_import_id"
                    )
                    import_query = select(DataImport).where(
                        DataImport.id == flow_id_to_use
                    )
                    import_result = await db.execute(import_query)
                    data_import = import_result.scalar_one_or_none()

                    if data_import:
                        data_import_id = data_import.id
                        self.logger.info(
                            f"✅ Found data import directly with id: {data_import_id}"
                        )

                if data_import_id:
                    # Load raw records from raw_import_records table
                    records_query = (
                        select(RawImportRecord)
                        .where(RawImportRecord.data_import_id == data_import_id)
                        .order_by(RawImportRecord.row_number)
                    )

                    records_result = await db.execute(records_query)
                    raw_records = records_result.scalars().all()

                    # Convert to list of dictionaries
                    raw_data = []
                    for record in raw_records:
                        raw_data.append(
                            {
                                "id": str(record.id),
                                "row_number": record.row_number,
                                "data": record.raw_data,
                                "created_at": (
                                    record.created_at.isoformat()
                                    if record.created_at
                                    else None
                                ),
                            }
                        )

                    self.logger.info(
                        f"✅ Loaded {len(raw_data)} raw records from database"
                    )

                    # Store in state
                    state.raw_data = raw_data
                    state.data_import_id = str(data_import_id)

                    return raw_data
                else:
                    self.logger.warning(
                        f"⚠️ No data import found for flow {flow_id_to_use}"
                    )
                    return []

        except Exception as e:
            self.logger.error(f"❌ Failed to load raw data from database: {e}")
            return []

    async def process_data_for_validation(
        self, raw_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process raw data for validation phase"""
        try:
            if not raw_data:
                return {
                    "status": "no_data",
                    "message": "No raw data available for validation",
                    "record_count": 0,
                }

            # Extract headers from multiple records for robustness (handle heterogeneous datasets)
            headers = []
            header_set = set()

            # Sample up to 10 records to detect all possible columns
            sample_size = min(10, len(raw_data))

            for i in range(sample_size):
                if i < len(raw_data) and "data" in raw_data[i]:
                    record_data = raw_data[i]["data"]
                    if isinstance(record_data, dict):
                        # Collect all keys from this record
                        for key in record_data.keys():
                            if key is not None and str(key).strip():
                                header_set.add(str(key).strip())
                    elif isinstance(record_data, list) and record_data and i == 0:
                        # Only treat as headers if it's the first record and contains string values
                        if all(isinstance(item, str) for item in record_data):
                            headers = record_data
                            break

            # Convert set to sorted list for consistency (if we collected from dicts)
            if not headers and header_set:
                headers = sorted(list(header_set))

            # Basic data statistics
            total_records = len(raw_data)
            non_empty_records = sum(1 for record in raw_data if record.get("data"))

            processed_data = {
                "status": "success",
                "record_count": total_records,
                "non_empty_records": non_empty_records,
                "headers": headers,
                "header_count": len(headers),
                "data_preview": (
                    raw_data[:5] if raw_data else []
                ),  # First 5 records for preview
                "data_quality_metrics": {
                    "completeness": (
                        (non_empty_records / total_records * 100)
                        if total_records > 0
                        else 0
                    ),
                    "header_consistency": True if headers else False,
                },
            }

            self.logger.info(f"✅ Processed {total_records} records for validation")
            return processed_data

        except Exception as e:
            self.logger.error(f"❌ Failed to process data for validation: {e}")
            return {
                "status": "error",
                "message": f"Data processing failed: {str(e)}",
                "record_count": 0,
            }

    async def extract_field_information(
        self, processed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract field information for mapping phase"""
        try:
            headers = processed_data.get("headers", [])
            raw_data = processed_data.get("data_preview", [])

            field_info = {}

            for header in headers:
                # Analyze field characteristics
                field_values = []
                for record in raw_data:
                    if "data" in record and isinstance(record["data"], dict):
                        value = record["data"].get(header)
                        if value is not None:
                            field_values.append(value)

                # Basic field analysis
                field_analysis = {
                    "name": header,
                    "sample_values": field_values[:5],  # First 5 non-null values
                    "non_null_count": len(field_values),
                    "data_types": list(set(type(v).__name__ for v in field_values)),
                    "suggested_type": self._suggest_field_type(field_values),
                    "mapping_suggestions": self._suggest_field_mappings(
                        header, field_values
                    ),
                }

                field_info[header] = field_analysis

            result = {
                "status": "success",
                "field_count": len(headers),
                "field_info": field_info,
                "mapping_ready": True,
            }

            self.logger.info(f"✅ Extracted information for {len(headers)} fields")
            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to extract field information: {e}")
            return {
                "status": "error",
                "message": f"Field extraction failed: {str(e)}",
                "field_count": 0,
            }

    async def apply_data_transformations(
        self, data: List[Dict[str, Any]], mappings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply data transformations based on field mappings"""
        try:
            if not data or not mappings:
                return {
                    "status": "no_data_or_mappings",
                    "transformed_data": [],
                    "transformation_count": 0,
                }

            transformed_data = []
            transformation_stats = {
                "total_records": len(data),
                "successful_transformations": 0,
                "failed_transformations": 0,
                "field_mappings_applied": 0,
            }

            for record in data:
                try:
                    transformed_record = {}
                    original_data = record.get("data", {})

                    if isinstance(original_data, dict):
                        # Apply field mappings
                        for source_field, mapping_info in mappings.items():
                            if source_field in original_data:
                                target_field = mapping_info.get(
                                    "target_field", source_field
                                )
                                transformation = mapping_info.get(
                                    "transformation", "direct_copy"
                                )

                                value = original_data[source_field]
                                transformed_value = self._apply_transformation(
                                    value, transformation
                                )

                                transformed_record[target_field] = transformed_value
                                transformation_stats["field_mappings_applied"] += 1

                        # Add metadata
                        transformed_record["_source_id"] = record.get("id")
                        transformed_record["_row_number"] = record.get("row_number")

                        transformed_data.append(transformed_record)
                        transformation_stats["successful_transformations"] += 1

                except Exception as record_error:
                    self.logger.warning(
                        f"⚠️ Failed to transform record {record.get('id', 'unknown')}: {record_error}"
                    )
                    transformation_stats["failed_transformations"] += 1
                    continue

            result = {
                "status": "success",
                "transformed_data": transformed_data,
                "transformation_stats": transformation_stats,
                "record_count": len(transformed_data),
            }

            self.logger.info(
                f"✅ Transformed {len(transformed_data)} records with "
                f"{transformation_stats['field_mappings_applied']} field mappings"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to apply data transformations: {e}")
            return {
                "status": "error",
                "message": f"Data transformation failed: {str(e)}",
                "transformed_data": [],
            }

    async def create_asset_records(
        self, transformed_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create asset records from transformed data"""
        try:
            if not transformed_data:
                return {"status": "no_data", "assets_created": [], "asset_count": 0}

            assets = []
            creation_stats = {
                "total_records": len(transformed_data),
                "assets_created": 0,
                "validation_failures": 0,
            }

            for record in transformed_data:
                try:
                    # Create asset record with minimal required fields
                    asset = {
                        "id": str(uuid.uuid4()),
                        "source_id": record.get("_source_id"),
                        "flow_id": self.flow._flow_id,
                        "asset_type": self._determine_asset_type(record),
                        "name": self._extract_asset_name(record),
                        "properties": self._extract_asset_properties(record),
                        "metadata": {
                            "source_row": record.get("_row_number"),
                            "transformation_timestamp": self._get_current_timestamp(),
                            "validation_status": "pending",
                        },
                    }

                    # Basic validation
                    if self._validate_asset_record(asset):
                        assets.append(asset)
                        creation_stats["assets_created"] += 1
                    else:
                        creation_stats["validation_failures"] += 1

                except Exception as asset_error:
                    self.logger.warning(
                        f"⚠️ Failed to create asset from record: {asset_error}"
                    )
                    creation_stats["validation_failures"] += 1
                    continue

            result = {
                "status": "success",
                "assets_created": assets,
                "creation_stats": creation_stats,
                "asset_count": len(assets),
            }

            self.logger.info(
                f"✅ Created {len(assets)} asset records from transformed data"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to create asset records: {e}")
            return {
                "status": "error",
                "message": f"Asset creation failed: {str(e)}",
                "assets_created": [],
            }

    def _suggest_field_type(self, values: List[Any]) -> str:
        """Suggest field type based on sample values"""
        if not values:
            return "unknown"

        # Simple type detection
        types = [type(v).__name__ for v in values]
        most_common_type = max(set(types), key=types.count)

        # Map Python types to more descriptive types
        type_mapping = {
            "str": "text",
            "int": "integer",
            "float": "decimal",
            "bool": "boolean",
            "dict": "object",
            "list": "array",
        }

        return type_mapping.get(most_common_type, most_common_type)

    def _suggest_field_mappings(self, field_name: str, values: List[Any]) -> List[str]:
        """Suggest possible target field mappings"""
        suggestions = []

        # Common field name patterns
        name_lower = field_name.lower()

        if any(keyword in name_lower for keyword in ["name", "title", "label"]):
            suggestions.append("asset_name")
        elif any(keyword in name_lower for keyword in ["type", "category", "class"]):
            suggestions.append("asset_type")
        elif any(keyword in name_lower for keyword in ["id", "identifier", "key"]):
            suggestions.append("asset_id")
        elif any(keyword in name_lower for keyword in ["description", "desc", "notes"]):
            suggestions.append("description")
        elif any(keyword in name_lower for keyword in ["status", "state", "condition"]):
            suggestions.append("status")
        else:
            suggestions.append("custom_attribute")

        return suggestions

    def _apply_transformation(self, value: Any, transformation: str) -> Any:
        """Apply transformation to a value"""
        try:
            if transformation == "direct_copy":
                return value
            elif transformation == "to_string":
                return str(value) if value is not None else ""
            elif transformation == "to_uppercase":
                return str(value).upper() if value is not None else ""
            elif transformation == "to_lowercase":
                return str(value).lower() if value is not None else ""
            elif transformation == "trim_whitespace":
                return str(value).strip() if value is not None else ""
            else:
                return value
        except Exception:
            return value

    def _determine_asset_type(self, record: Dict[str, Any]) -> str:
        """Determine asset type from record data"""
        # Simple asset type detection logic
        for key, value in record.items():
            if "type" in key.lower() and isinstance(value, str):
                return value

        return "generic_asset"

    def _extract_asset_name(self, record: Dict[str, Any]) -> str:
        """Extract asset name from record data"""
        # Look for name-like fields
        for key, value in record.items():
            if any(
                keyword in key.lower() for keyword in ["name", "title", "label"]
            ) and isinstance(value, str):
                return value

        # Fallback to first string value
        for key, value in record.items():
            if isinstance(value, str) and value.strip():
                return value

        return f"Asset_{record.get('_row_number', 'unknown')}"

    def _extract_asset_properties(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Extract asset properties from record data"""
        properties = {}

        # Exclude metadata fields
        exclude_keys = {"_source_id", "_row_number"}

        for key, value in record.items():
            if key not in exclude_keys:
                properties[key] = value

        return properties

    def _validate_asset_record(self, asset: Dict[str, Any]) -> bool:
        """Validate asset record"""
        required_fields = ["id", "name", "asset_type"]

        for field in required_fields:
            if field not in asset or not asset[field]:
                return False

        return True

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime

        return datetime.now().isoformat()
