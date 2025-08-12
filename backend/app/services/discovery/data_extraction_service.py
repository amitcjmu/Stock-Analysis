"""
Data Extraction Service for Discovery Flow Operations

This service handles data extraction and transformation for discovery flows.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def extract_raw_data(crewai_state_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract raw_data from crewai_state_data, handling both old dict format and new list format.

    Old format: raw_data: {'data': [...], 'import_metadata': {...}}
    New format: raw_data: [...]
    """
    if not crewai_state_data:
        logger.warning("⚠️ No crewai_state_data provided to extract_raw_data")
        return []

    raw_data = crewai_state_data.get("raw_data", [])
    logger.info(
        f"📊 Raw data type: {type(raw_data)}, has 'data' key: {isinstance(raw_data, dict) and 'data' in raw_data}"
    )

    # If raw_data is a dict with 'data' key, extract the list
    if isinstance(raw_data, dict) and "data" in raw_data:
        extracted_data = raw_data["data"]
        logger.info(
            f"🔄 Converting raw_data from dict format to list format in API response, "
            f"found {len(extracted_data)} records"
        )
        return extracted_data

    # If raw_data is already a list, return it
    if isinstance(raw_data, list):
        logger.info(f"✅ raw_data already in list format with {len(raw_data)} records")
        return raw_data

    # Otherwise, wrap in a list or return empty
    logger.warning(f"⚠️ Unexpected raw_data format: {type(raw_data)}")
    return [raw_data] if raw_data else []


def extract_import_metadata(
    crewai_state_data: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Extract import_metadata from crewai_state_data, handling both locations.

    Could be in:
    1. crewai_state_data['import_metadata']
    2. crewai_state_data['raw_data']['import_metadata'] (old format)
    """
    if not crewai_state_data:
        return None

    # First check direct location
    if "import_metadata" in crewai_state_data:
        return crewai_state_data["import_metadata"]

    # Then check inside raw_data (old format)
    raw_data = crewai_state_data.get("raw_data", {})
    if isinstance(raw_data, dict) and "import_metadata" in raw_data:
        logger.info("🔄 Extracting import_metadata from old raw_data dict format")
        return raw_data["import_metadata"]

    return None


def extract_detected_fields(crewai_state_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract detected fields from raw_data for attribute mapping display."""
    if not crewai_state_data:
        return []

    # First, get the raw_data
    raw_data = extract_raw_data(crewai_state_data)

    if not raw_data or len(raw_data) == 0:
        return []

    # Get field names from the first record
    first_record = (
        raw_data[0] if isinstance(raw_data, list) and len(raw_data) > 0 else {}
    )

    if not first_record:
        return []

    # Create detected_fields array with proper structure
    detected_fields = []
    for field_name in first_record.keys():
        # Analyze field data from multiple records for better type detection
        sample_values = []
        for i, record in enumerate(raw_data[:10]):  # Sample first 10 records
            if field_name in record and record[field_name]:
                sample_values.append(record[field_name])

        # Determine field type based on sample values
        field_type = "string"  # Default
        if sample_values:
            # Check if all values are numbers
            if all(
                isinstance(v, (int, float))
                or (
                    isinstance(v, str) and v.replace(".", "").replace("-", "").isdigit()
                )
                for v in sample_values
            ):
                field_type = "number"
            # Check if all values are booleans
            elif all(
                isinstance(v, bool) or v in ["true", "false", "True", "False"]
                for v in sample_values
            ):
                field_type = "boolean"

        detected_fields.append(
            {
                "name": field_name,
                "type": field_type,
                "sample_values": sample_values[:3],  # Include up to 3 sample values
                "non_null_count": sum(
                    1
                    for record in raw_data
                    if field_name in record and record[field_name]
                ),
                "null_count": sum(
                    1
                    for record in raw_data
                    if field_name not in record or not record[field_name]
                ),
            }
        )

    logger.info(f"🔍 Detected {len(detected_fields)} fields from raw_data")
    return detected_fields
