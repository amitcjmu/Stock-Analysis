"""
Storage Manager Helper Methods

Contains utility and helper functions used by the storage manager operations.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_records_from_data(data: Any) -> List[Dict[str, Any]]:
    """
    Extract actual data records from potentially nested JSON structures.

    Handles formats like:
    - [{"field1": "value1"}, {"field2": "value2"}] (direct list)
    - {"data": [{"field1": "value1"}, {"field2": "value2"}]} (nested structure)

    CRITICAL FIX: Filters out CrewAI JSON response structures that contain
    metadata fields like "mappings", "skipped_fields", "synthesis_required"
    which should not be treated as CSV field names.

    Args:
        data: Parsed JSON data that could be a list or dict with nested data

    Returns:
        List[Dict[str, Any]]: The actual data records to process
    """
    try:
        # CRITICAL FIX: Define CrewAI metadata detection patterns
        crewai_metadata_keys = {
            "mappings",
            "skipped_fields",
            "synthesis_required",
            "confidence_scores",
            "agent_reasoning",
            "transformations",
            "validation_results",
            "agent_insights",
            "unmapped_fields",
        }

        # Additional safety check for common JSON parsing artifacts
        artifact_patterns = ["{", "}", "[", "]", "[]", "{}", "null"]

        # If data is already a list, check each item for metadata contamination
        if isinstance(data, list):
            # If the list contains dict items that look like CrewAI responses, filter them out
            clean_records = []
            for item in data:
                if isinstance(item, dict):
                    item_keys = set(item.keys())
                    # Skip records that contain CrewAI metadata fields
                    if not crewai_metadata_keys.intersection(item_keys):
                        # Also skip records with JSON artifact field names
                        if not any(str(key) in artifact_patterns for key in item_keys):
                            clean_records.append(item)
                        else:
                            logger.warning(
                                f"🚨 Skipping record with JSON artifact field names: {list(item_keys)}"
                            )
                    else:
                        logger.warning(
                            f"🚨 Skipping CrewAI metadata record with keys: {list(item_keys)}"
                        )
                else:
                    clean_records.append(item)

            logger.debug(
                f"Cleaned data list: {len(clean_records)} valid records out of {len(data)} total"
            )
            return clean_records

        # If data is a dict, check for CrewAI response structures first
        if isinstance(data, dict):
            data_keys = set(data.keys())

            # If the dict contains any CrewAI metadata keys, it's not actual CSV data
            if crewai_metadata_keys.intersection(data_keys):
                logger.warning(
                    f"🚨 CRITICAL FIX: Detected CrewAI JSON response structure with keys: {list(data_keys)}. "
                    f"This is metadata, not CSV data. Returning empty list to prevent JSON artifacts "
                    f"from being treated as field names."
                )
                return []

            # Additional safety check for common JSON parsing artifacts
            suspicious_fields = [
                key for key in data_keys if str(key) in artifact_patterns
            ]
            if suspicious_fields:
                logger.warning(
                    f"🚨 CRITICAL FIX: Detected JSON parsing artifacts as field names: {suspicious_fields}. "
                    f"This indicates malformed data. Returning empty list."
                )
                return []

            # Check for {"data": [...]} structure
            if "data" in data and isinstance(data["data"], list):
                records = data["data"]
                logger.debug(f"Extracted {len(records)} records from nested 'data' key")
                # Recursively clean the extracted records
                return extract_records_from_data(records)

            # Check for other possible keys that might contain the records
            for key in ["records", "items", "results", "rows"]:
                if key in data and isinstance(data[key], list):
                    records = data[key]
                    logger.debug(
                        f"Extracted {len(records)} records from nested '{key}' key"
                    )
                    # Recursively clean the extracted records
                    return extract_records_from_data(records)

            # If it's a dict but no recognizable structure, treat as single record
            # but only if it doesn't contain metadata fields
            logger.debug("Data is a single dictionary record, wrapping in list")
            return [data]

        # For any other type, wrap in list if not None/empty
        if data is not None and data != "":
            logger.debug(f"Data is {type(data)}, wrapping in list")
            return [data]

        # Empty or None data
        logger.debug("Data is empty or None")
        return []

    except Exception as e:
        logger.error(f"Error extracting records from data: {e}")
        # Fallback: if we can't process it, return empty list
        return []
