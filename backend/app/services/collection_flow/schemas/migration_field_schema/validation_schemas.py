"""
Validation and assessment logic for migration field schema.

Contains functions for validating assessment readiness and determining
which 6R strategies can be accurately evaluated based on available data.
"""

from typing import Dict, Any, List
from .field_definitions import get_fields_for_asset_type


def get_six_r_decision_fields(asset_type: str = None) -> Dict[str, List[str]]:
    """
    Get fields organized by which 6R strategy they inform.

    This helps understand what data is needed for each migration strategy:
    - Rehost: Infrastructure specs, dependencies
    - Replatform: Tech stack, cloud readiness
    - Refactor: Architecture, code base
    - Repurchase: Business process, alternatives
    - Retire: Usage, business value
    - Retain: Compliance, constraints

    Args:
        asset_type: Optional asset type to filter fields

    Returns:
        Dictionary mapping 6R strategies to field names that inform that decision
    """
    fields = get_fields_for_asset_type(asset_type or "application")

    six_r_mapping = {
        "rehost": [],
        "replatform": [],
        "refactor": [],
        "repurchase": [],
        "retire": [],
        "retain": [],
    }

    for field_name, field_def in fields.items():
        if "six_r_relevance" in field_def:
            for strategy in field_def["six_r_relevance"]:
                if strategy in six_r_mapping:
                    six_r_mapping[strategy].append(field_name)

    return six_r_mapping


def validate_assessment_readiness(asset, asset_type: str = None) -> Dict[str, Any]:
    """
    Validate if asset has sufficient data for 6R assessment.

    Returns assessment readiness report indicating which 6R strategies
    can be accurately evaluated based on available data.

    Args:
        asset: Asset object to validate
        asset_type: Optional asset type

    Returns:
        Dictionary with readiness status per 6R strategy
    """
    asset_type = asset_type or getattr(asset, "asset_type", "application")
    six_r_fields = get_six_r_decision_fields(asset_type)

    readiness = {}
    for strategy, required_fields in six_r_fields.items():
        if not required_fields:
            continue

        # Check how many required fields are populated
        populated = 0
        for field in required_fields:
            value = getattr(asset, field, None)
            if value and (not isinstance(value, (list, dict)) or len(value) > 0):
                populated += 1

        total = len(required_fields)
        percentage = (populated / total * 100) if total > 0 else 0

        readiness[strategy] = {
            "percentage": percentage,
            "populated_fields": populated,
            "total_fields": total,
            "assessment_viable": percentage >= 70,  # Need 70%+ for reliable assessment
            "missing_fields": [
                f for f in required_fields if not getattr(asset, f, None)
            ],
        }

    # Overall assessment readiness
    viable_strategies = sum(1 for r in readiness.values() if r["assessment_viable"])
    readiness["overall"] = {
        "viable_strategies": viable_strategies,
        "total_strategies": len(readiness),
        "can_assess": viable_strategies >= 3,  # Need at least 3 viable options
    }

    return readiness
