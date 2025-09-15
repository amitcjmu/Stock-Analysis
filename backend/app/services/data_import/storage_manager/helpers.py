"""
Storage Manager Helper Methods

Contains utility and helper functions used by the storage manager operations.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.core.logging import get_logger

logger = get_logger(__name__)


def _is_crewai_metadata_record(item_keys: set, crewai_keys: set, item_values) -> bool:
    """Check if a record appears to be CrewAI metadata rather than CSV data."""
    metadata_intersection = crewai_keys.intersection(item_keys)

    # Only skip if record has 3+ highly specific CrewAI metadata keys
    # AND record has no typical CSV field values (strings/numbers in values)
    if len(metadata_intersection) >= 3:
        # Check if values look like metadata (complex objects) vs CSV data (simple strings/numbers)
        values_look_like_metadata = any(
            isinstance(v, (dict, list)) and v for v in item_values
        )
        return values_look_like_metadata

    return False


def _check_for_nested_data_arrays(data: dict) -> List[Dict[str, Any]]:
    """Check for nested data arrays in common patterns."""
    # Check for nested data structures first (common pattern)
    if "data" in data and isinstance(data["data"], list):
        records = data["data"]
        logger.info(f"📊 Found nested data array with {len(records)} records")
        return extract_records_from_data(records)

    # Check for other possible keys that might contain the records
    for key in ["records", "items", "results", "rows"]:
        if key in data and isinstance(data[key], list):
            records = data[key]
            logger.info(f"📊 Found nested {key} array with {len(records)} records")
            return extract_records_from_data(records)

    return None


def extract_records_from_data(data: Any) -> List[Dict[str, Any]]:
    """
    Extract actual data records from potentially nested JSON structures.

    Handles formats like:
    - [{"field1": "value1"}, {"field2": "value2"}] (direct list)
    - {"data": [{"field1": "value1"}, {"field2": "value2"}]} (nested structure)

    CRITICAL FIX: Only filters out obvious CrewAI JSON response structures.
    Legitimate CSV columns like "Name", "Type", "Status" should NOT be filtered.

    Args:
        data: Parsed JSON data that could be a list or dict with nested data

    Returns:
        List[Dict[str, Any]]: The actual data records to process
    """
    try:
        logger.info(f"📥 extract_records_from_data called with data type: {type(data)}")

        # CRITICAL FIX: Be much more specific about CrewAI metadata detection
        # Only filter objects that have OBVIOUS CrewAI response patterns
        highly_specific_crewai_keys = {
            "mappings",
            "skipped_fields",
            "synthesis_required",
            "agent_reasoning",
            "transformations",
            "validation_results",
            "agent_insights",
            "unmapped_fields",
            "clarifications",
            "execution_metadata",
            "raw_response",
            "phase_name",
        }

        # CRITICAL FIX: Remove common CSV column names from filtering
        # These are legitimate field names that should NOT be filtered:
        # "success", "error", "timestamp" could be CSV columns!

        # Only filter obvious JSON parsing artifacts (not field names)
        artifact_patterns = ["{", "}", "[", "]", "[]", "{}", "null", "undefined"]

        # If data is already a list, process each item
        if isinstance(data, list):
            logger.info(f"📊 Processing list with {len(data)} items")
            clean_records = []

            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    item_keys = set(item.keys())

                    # Check if this appears to be CrewAI metadata
                    if _is_crewai_metadata_record(
                        item_keys, highly_specific_crewai_keys, item.values()
                    ):
                        logger.warning(
                            f"🚨 Skipping likely CrewAI metadata record {idx}"
                        )
                        continue

                    # Skip records with obvious JSON artifact field names
                    if any(str(key) in artifact_patterns for key in item_keys):
                        logger.warning(
                            f"🚨 Skipping record {idx} with JSON artifact field names: {list(item_keys)}"
                        )
                        continue

                    # This looks like legitimate CSV data
                    clean_records.append(item)
                    logger.debug(
                        f"✅ Keeping CSV record {idx} with fields: {list(item.keys())}"
                    )
                else:
                    # Non-dict items in the list - keep them as-is
                    clean_records.append(item)

            logger.info(
                f"📊 Filtered to {len(clean_records)} valid records out of {len(data)} total"
            )
            return clean_records

        # If data is a dict, check for nested structures or treat as single record
        if isinstance(data, dict):
            data_keys = set(data.keys())
            logger.info(f"📊 Processing dict with keys: {list(data_keys)}")

            # Check for nested data structures first
            nested_result = _check_for_nested_data_arrays(data)
            if nested_result is not None:
                return nested_result

            # CRITICAL FIX: Only filter if this dict has MANY highly specific CrewAI keys
            # AND the values look like complex metadata rather than simple CSV values
            metadata_intersection = highly_specific_crewai_keys.intersection(data_keys)

            if len(metadata_intersection) >= 3:
                # Check if this looks like a metadata response vs a single CSV record
                values_look_like_metadata = any(
                    isinstance(v, (dict, list)) and v for v in data.values()
                )

                if values_look_like_metadata:
                    logger.warning(
                        f"🚨 Skipping dict that appears to be CrewAI metadata with keys: {list(data_keys)}"
                    )
                    return []

            # Additional safety check for obvious JSON parsing artifacts
            if any(str(key) in artifact_patterns for key in data_keys):
                logger.warning(
                    f"🚨 Skipping dict with JSON artifact field names: {list(data_keys)}"
                )
                return []

            # This appears to be a single legitimate CSV record
            logger.info(
                f"✅ Treating dict as single CSV record with fields: {list(data_keys)}"
            )
            return [data]

        # For any other type, wrap in list if not None/empty
        if data is not None and data != "":
            logger.info(f"📊 Wrapping {type(data)} data in list")
            return [data]

        # Empty or None data
        logger.info("📊 Data is empty or None, returning empty list")
        return []

    except Exception as e:
        logger.error(f"❌ Error extracting records from data: {e}")
        # CRITICAL FIX: In case of error, try to return the data as-is if it's a list
        if isinstance(data, list):
            logger.warning(
                "🔄 Falling back to returning original list data due to extraction error"
            )
            return data
        return []
