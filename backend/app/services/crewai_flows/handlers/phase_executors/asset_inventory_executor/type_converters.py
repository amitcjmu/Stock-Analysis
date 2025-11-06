"""
Asset Inventory Executor - Type Converters
Contains type conversion utilities for transforming raw data to proper types.

CC: Type conversion helpers for asset creation
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_asset_tags(tags_value: Any) -> list:
    """
    Parse asset tags from various formats into a list.

    Handles:
    - Semicolon-separated string: "custom;pii;legacy" -> ["custom", "pii", "legacy"]
    - Comma-separated string: "custom,pii,legacy" -> ["custom", "pii", "legacy"]
    - Already a list: ["custom", "pii"] -> ["custom", "pii"]
    - None or empty -> []

    Args:
        tags_value: Tags value in any format

    Returns:
        List of tag strings
    """
    if not tags_value:
        return []

    if isinstance(tags_value, list):
        # Already a list, return as-is (strip whitespace from each tag)
        return [str(tag).strip() for tag in tags_value if tag]

    if isinstance(tags_value, str):
        # String format - try semicolon first, then comma
        if ";" in tags_value:
            return [tag.strip() for tag in tags_value.split(";") if tag.strip()]
        elif "," in tags_value:
            return [tag.strip() for tag in tags_value.split(",") if tag.strip()]
        else:
            # Single tag
            return [tags_value.strip()] if tags_value.strip() else []

    # Unknown format, convert to string and try to parse
    return [str(tags_value).strip()] if tags_value else []


def parse_boolean(value: Any) -> bool:
    """
    Parse boolean from various string formats.

    Handles:
    - Boolean: True/False -> True/False
    - String "TRUE"/"FALSE" (case-insensitive) -> True/False
    - String "Yes"/"No" (case-insensitive) -> True/False
    - String "1"/"0" -> True/False
    - Integer 1/0 -> True/False
    - None or empty -> None

    Args:
        value: Value in any format

    Returns:
        Boolean value or None if empty/invalid
    """
    if value is None or value == "":
        return None

    # Already a boolean
    if isinstance(value, bool):
        return value

    # String format
    if isinstance(value, str):
        value_lower = value.strip().lower()

        # TRUE/FALSE variants
        if value_lower in ("true", "t", "yes", "y", "1"):
            return True
        if value_lower in ("false", "f", "no", "n", "0"):
            return False

        logger.warning(f"Unknown boolean format: '{value}', treating as None")
        return None

    # Numeric format (1=True, 0=False)
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False
        logger.warning(f"Unknown numeric boolean value: '{value}', treating as None")
        return None

    # Unknown format
    logger.warning(
        f"Cannot convert '{value}' (type: {type(value)}) to boolean, treating as None"
    )
    return None
