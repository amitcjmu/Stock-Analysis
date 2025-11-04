"""
Asset Inventory Executor - Utility Functions
Contains shared utility functions for data serialization and validation.

CC: Utilities for JSONB serialization and data preparation
"""

from typing import Dict, Any
from uuid import UUID


def serialize_uuids_for_jsonb(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert all UUID objects to strings for JSONB storage compatibility.

    PostgreSQL JSONB columns cannot directly store Python UUID objects.
    This function recursively converts all UUID instances to strings.

    Args:
        data: Dictionary potentially containing UUID objects

    Returns:
        Dictionary with all UUIDs converted to strings
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = serialize_uuids_for_jsonb(value)
        elif isinstance(value, list):
            result[key] = [
                (
                    serialize_uuids_for_jsonb(item)
                    if isinstance(item, dict)
                    else str(item) if isinstance(item, UUID) else item
                )
                for item in value
            ]
        else:
            result[key] = value
    return result


__all__ = ["serialize_uuids_for_jsonb"]
