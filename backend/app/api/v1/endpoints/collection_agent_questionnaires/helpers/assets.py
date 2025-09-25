"""
Asset-related helper functions.
Functions for calculating asset completeness and processing asset data.
"""

from app.models import Asset


def calculate_completeness(asset: Asset) -> float:
    """
    Calculate asset completeness score based on filled fields.

    Args:
        asset: Asset instance to evaluate

    Returns:
        Completeness score between 0.0 and 1.0
    """
    # Direct fields to check
    direct_fields = ["name", "asset_type", "business_criticality", "owner"]
    filled_direct = sum(
        1 for field in direct_fields if getattr(asset, field, None) is not None
    )
    direct_complete = filled_direct / len(direct_fields)

    # Technical details fields to check
    technical_fields = ["technology_stack", "environment"]
    filled_technical = sum(
        1 for field in technical_fields if getattr(asset, field, None) is not None
    )
    technical_complete = filled_technical / len(technical_fields)

    # Custom attributes fields to check
    optional_fields_in_custom = [
        "data_classification",
        "compliance_requirements",
        "performance_metrics",
    ]
    optional_complete = 0
    if asset.custom_attributes and optional_fields_in_custom:
        optional_complete = sum(
            1
            for field in optional_fields_in_custom
            if asset.custom_attributes.get(field) is not None
        ) / len(optional_fields_in_custom)

    # Weight: 40% direct, 30% technical, 30% optional
    return (
        (direct_complete * 0.4) + (technical_complete * 0.3) + (optional_complete * 0.3)
    )
