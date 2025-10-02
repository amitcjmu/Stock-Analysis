"""
Helper methods for API responses and field organization.

Contains utility functions for organizing fields by category and priority,
used in API responses and UI rendering.
"""

from typing import Dict, List
from .base_schemas import FieldCategory, FieldPriority
from .field_definitions import get_fields_for_asset_type


def get_fields_by_category(asset_type: str = None) -> Dict[FieldCategory, List[str]]:
    """
    Get fields organized by category.

    Args:
        asset_type: Optional asset type to filter fields

    Returns:
        Dictionary mapping categories to field names
    """
    fields = get_fields_for_asset_type(asset_type or "application")

    categorized = {}
    for field_name, field_def in fields.items():
        category = field_def["category"]
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(field_name)

    return categorized


def get_critical_fields(asset_type: str = None) -> List[str]:
    """
    Get all CRITICAL priority fields for an asset type.

    Args:
        asset_type: Optional asset type to filter fields

    Returns:
        List of critical field names
    """
    fields = get_fields_for_asset_type(asset_type or "application")
    return [
        field_name
        for field_name, field_def in fields.items()
        if field_def.get("priority") == FieldPriority.CRITICAL
    ]


def get_high_priority_fields(asset_type: str = None) -> List[str]:
    """
    Get all HIGH priority fields for an asset type.

    Args:
        asset_type: Optional asset type to filter fields

    Returns:
        List of high priority field names
    """
    fields = get_fields_for_asset_type(asset_type or "application")
    return [
        field_name
        for field_name, field_def in fields.items()
        if field_def.get("priority") == FieldPriority.HIGH
    ]
