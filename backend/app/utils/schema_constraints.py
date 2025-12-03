"""
Schema constraint extraction utility for data validation.

Extracts column constraints (VARCHAR lengths, nullable status, etc.) from
SQLAlchemy models for use in pre-import validation.

Related: ADR-038, Issue #1204, Issue #1205
"""

import logging
from functools import lru_cache
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_asset_schema_constraints() -> Dict[str, Dict[str, Any]]:
    """
    Extract column constraints from Asset model.

    Returns a dictionary mapping column names to their constraints:
    - type: The SQLAlchemy column type as string
    - nullable: Whether the column allows NULL values
    - max_length: For VARCHAR/String columns, the max length (if defined)

    Results are cached since schema doesn't change at runtime.

    Returns:
        Dict mapping column_name -> constraint info

    Example:
        {
            "application_name": {
                "type": "VARCHAR(255)",
                "nullable": True,
                "max_length": 255
            },
            "hostname": {
                "type": "VARCHAR(255)",
                "nullable": True,
                "max_length": 255
            },
            "description": {
                "type": "TEXT",
                "nullable": True
                # No max_length for TEXT columns
            }
        }
    """
    try:
        from app.models.asset.models import Asset

        constraints: Dict[str, Dict[str, Any]] = {}

        for column in Asset.__table__.columns:
            col_info: Dict[str, Any] = {
                "type": str(column.type),
                "nullable": column.nullable,
            }

            # Extract max_length for String/VARCHAR columns
            if hasattr(column.type, "length") and column.type.length is not None:
                col_info["max_length"] = column.type.length

            # Add column comment if available
            if column.comment:
                col_info["comment"] = column.comment

            constraints[column.name] = col_info

        logger.debug(f"Extracted schema constraints for {len(constraints)} columns")
        return constraints

    except Exception as e:
        logger.error(f"Failed to extract schema constraints: {e}", exc_info=True)
        # Return empty dict rather than failing - validation can proceed with warnings
        return {}


def get_column_max_length(column_name: str) -> Optional[int]:
    """
    Get the maximum length for a specific column.

    Args:
        column_name: Name of the column to check

    Returns:
        Max length if column has VARCHAR constraint, None otherwise
    """
    constraints = get_asset_schema_constraints()
    column_info = constraints.get(column_name, {})
    return column_info.get("max_length")


def get_all_varchar_columns() -> Dict[str, int]:
    """
    Get all VARCHAR columns and their max lengths.

    Useful for bulk field length validation.

    Returns:
        Dict mapping column_name -> max_length for all VARCHAR columns
    """
    constraints = get_asset_schema_constraints()
    return {
        name: info["max_length"]
        for name, info in constraints.items()
        if "max_length" in info
    }


def is_column_nullable(column_name: str) -> bool:
    """
    Check if a column allows NULL values.

    Args:
        column_name: Name of the column to check

    Returns:
        True if nullable, False if NOT NULL required
    """
    constraints = get_asset_schema_constraints()
    column_info = constraints.get(column_name, {})
    return column_info.get("nullable", True)  # Default to nullable if unknown


# Common field length constants (match asset/base.py)
SMALL_STRING_LENGTH = 50
MEDIUM_STRING_LENGTH = 100
LARGE_STRING_LENGTH = 255

# Fields known to have VARCHAR constraints (for quick reference)
KNOWN_VARCHAR_FIELDS = {
    "application_name": LARGE_STRING_LENGTH,
    "hostname": LARGE_STRING_LENGTH,
    "name": LARGE_STRING_LENGTH,
    "asset_name": LARGE_STRING_LENGTH,
    "asset_type": SMALL_STRING_LENGTH,
    "source_phase": SMALL_STRING_LENGTH,
    "current_phase": SMALL_STRING_LENGTH,
    "status": SMALL_STRING_LENGTH,
    "migration_status": SMALL_STRING_LENGTH,
}
