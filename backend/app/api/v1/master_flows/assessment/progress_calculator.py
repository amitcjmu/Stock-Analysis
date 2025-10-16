"""
Progress calculation utilities for assessment endpoints.

Provides category-based progress tracking for 22 critical assessment attributes.
"""

from typing import Any, Dict, List


# Define 22 critical attribute categories
ATTRIBUTE_CATEGORIES = [
    {
        "name": "Infrastructure",
        "attributes": [
            "asset_name",
            "technology_stack",
            "operating_system",
            "cpu_cores",
            "memory_gb",
            "storage_gb",
        ],
    },
    {
        "name": "Application",
        "attributes": [
            "business_criticality",
            "application_type",
            "architecture_pattern",
            "dependencies",
            "user_base",
            "data_sensitivity",
            "compliance_requirements",
            "sla_requirements",
        ],
    },
    {
        "name": "Business Context",
        "attributes": [
            "business_owner",
            "annual_operating_cost",
            "business_value",
            "strategic_importance",
        ],
    },
    {
        "name": "Technical Debt",
        "attributes": [
            "code_quality_score",
            "last_update_date",
            "support_status",
            "known_vulnerabilities",
        ],
    },
]


def calculate_progress_categories(assets: List[Any]) -> Dict[str, Any]:
    """
    Calculate attribute completion progress by category.

    Args:
        assets: List of Asset model instances

    Returns:
        Dict with categories and overall progress
    """
    categories = []

    for category_def in ATTRIBUTE_CATEGORIES:
        category = {
            "name": category_def["name"],
            "attributes": category_def["attributes"],
            "completed": 0,
            "total": len(category_def["attributes"]) * len(assets),
        }

        # Count completed attributes for each asset
        for asset in assets:
            for attr_name in category["attributes"]:
                # Check if attribute has a value
                attr_value = getattr(asset, attr_name, None)
                if attr_value is not None:
                    # Handle special cases
                    if isinstance(attr_value, list) and len(attr_value) > 0:
                        category["completed"] += 1
                    elif isinstance(attr_value, dict) and len(attr_value) > 0:
                        category["completed"] += 1
                    elif isinstance(attr_value, str) and attr_value.strip():
                        category["completed"] += 1
                    elif isinstance(attr_value, (int, float)) and attr_value > 0:
                        category["completed"] += 1
                    elif isinstance(attr_value, bool):
                        category["completed"] += 1

        # Calculate progress percent for category
        if category["total"] > 0:
            category["progress_percent"] = round(
                (category["completed"] / category["total"]) * 100, 1
            )
        else:
            category["progress_percent"] = 0.0

        categories.append(category)

    # Calculate overall progress
    total_completed = sum(c["completed"] for c in categories)
    total_attributes = sum(c["total"] for c in categories)
    overall_progress = (
        round((total_completed / total_attributes) * 100, 1)
        if total_attributes > 0
        else 0.0
    )

    return {
        "categories": categories,
        "overall_progress": overall_progress,
    }
