"""
Base Data Cleansing Components

Core data cleansing functionality and basic operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from ..data_cleansing_utils import DataCleansingUtils

logger = logging.getLogger(__name__)


class DataCleansingBase:
    """Base class for data cleansing operations"""

    def _basic_data_cleansing(
        self, raw_import_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Basic data cleansing fallback when agent is not available or fails"""
        logger.info(
            f"🔧 Performing basic data cleansing on {len(raw_import_records)} records"
        )

        cleaned_data = []
        for record in raw_import_records:
            # Create a cleaned version of the record
            cleaned_record = {}

            # CRITICAL: Preserve ALL ID fields for mapping
            if "raw_import_record_id" in record:
                cleaned_record["raw_import_record_id"] = record["raw_import_record_id"]
                cleaned_record["id"] = record["raw_import_record_id"]

            # CRITICAL: Preserve row_number for fallback updating
            if "row_number" in record:
                cleaned_record["row_number"] = record["row_number"]
                logger.debug(f"Preserved row_number: {record['row_number']} for record")

            # Copy over the raw data fields with field name normalization
            raw_data = record.get("raw_data", {})
            if isinstance(raw_data, dict):
                # CRITICAL: Normalize field names from PascalCase to snake_case
                normalized_raw_data = DataCleansingUtils.normalize_record_fields(
                    raw_data
                )
                cleaned_record.update(normalized_raw_data)

            # Basic cleansing operations with field name normalization
            for key, value in record.items():
                if key not in ["raw_import_record_id", "id", "raw_data", "row_number"]:
                    # Clean string values
                    if isinstance(value, str):
                        value = value.strip()
                        # Convert empty strings to None
                        if value == "":
                            value = None
                    # Normalize the field name to snake_case
                    normalized_key = DataCleansingUtils.normalize_field_name(key)
                    cleaned_record[normalized_key] = value

            # Add cleansing metadata
            cleaned_record["cleansing_method"] = "basic_fallback"
            cleaned_record["cleansed_at"] = datetime.utcnow().isoformat()

            cleaned_data.append(cleaned_record)

        logger.info(f"✅ Basic cleansing completed for {len(cleaned_data)} records")
        return cleaned_data

    def _generate_cleansing_results(
        self,
        cleaned_data: List[Dict[str, Any]],
        raw_records_count: int,
        updated_count: int,
        verified_count: int,
    ) -> Dict[str, Any]:
        """Generate standardized cleansing results"""
        return {
            "status": "success",
            "cleaned_data": cleaned_data,
            "cleansing_summary": DataCleansingUtils.generate_cleansing_summary(
                cleaned_data
            ),
            "quality_metrics": DataCleansingUtils.calculate_cleansing_quality_metrics(
                cleaned_data
            ),
            "persistent_agent_used": True,
            "crew_based": False,
            "raw_records_count": raw_records_count,
            "cleaned_records_count": len(cleaned_data),
            "persisted_count": updated_count,
            "verified_count": verified_count,
        }

    def _prepare_crew_input(self) -> Dict[str, Any]:
        """Prepare input for crew-based processing"""
        return {
            "raw_data": self.state.raw_data,
            "field_mappings": getattr(self.state, "field_mappings", {}),
            "cleansing_type": "comprehensive_data_cleansing",
        }
