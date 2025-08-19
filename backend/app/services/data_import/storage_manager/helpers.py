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

    Args:
        data: Parsed JSON data that could be a list or dict with nested data

    Returns:
        List[Dict[str, Any]]: The actual data records to process
    """
    try:
        # If data is already a list, return it directly
        if isinstance(data, list):
            logger.debug(f"Data is already a list with {len(data)} records")
            return data

        # If data is a dict, check for common nested structures
        if isinstance(data, dict):
            # Check for {"data": [...]} structure
            if "data" in data and isinstance(data["data"], list):
                records = data["data"]
                logger.debug(f"Extracted {len(records)} records from nested 'data' key")
                return records

            # Check for other possible keys that might contain the records
            for key in ["records", "items", "results", "rows"]:
                if key in data and isinstance(data[key], list):
                    records = data[key]
                    logger.debug(
                        f"Extracted {len(records)} records from nested '{key}' key"
                    )
                    return records

            # If it's a dict but no recognizable structure, treat as single record
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
