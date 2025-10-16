"""
Helper functions for assessment endpoints.

Functions for calculating missing attributes and actionable guidance.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def get_missing_critical_attributes(asset: Any) -> List[str]:
    """
    Identify which of 22 critical attributes are missing for an asset.

    22 Critical Attributes:
    - Infrastructure: asset_name, technology_stack, operating_system,
                     cpu_cores, memory_gb, storage_gb
    - Application: business_criticality, application_type, architecture_pattern,
                  dependencies, user_base, data_sensitivity,
                  compliance_requirements, sla_requirements
    - Business: business_owner, annual_operating_cost, business_value,
               strategic_importance
    - Tech Debt: code_quality_score, last_update_date, support_status,
                known_vulnerabilities
    """
    critical_attrs = [
        "asset_name",
        "technology_stack",
        "operating_system",
        "cpu_cores",
        "memory_gb",
        "storage_gb",
        "business_criticality",
        "application_type",
        "architecture_pattern",
        "dependencies",
        "user_base",
        "data_sensitivity",
        "compliance_requirements",
        "sla_requirements",
        "business_owner",
        "annual_operating_cost",
        "business_value",
        "strategic_importance",
        "code_quality_score",
        "last_update_date",
        "support_status",
        "known_vulnerabilities",
    ]

    missing = []
    for attr in critical_attrs:
        value = getattr(asset, attr, None)
        if value is None:
            missing.append(attr)
        elif isinstance(value, str) and not value.strip():
            missing.append(attr)
        elif isinstance(value, list) and len(value) == 0:
            missing.append(attr)
        elif isinstance(value, dict) and len(value) == 0:
            missing.append(attr)

    return missing


def categorize_missing_attributes(missing_attrs: List[str]) -> Dict[str, List[str]]:
    """
    Categorize missing attributes into frontend-expected structure.

    Categories align with AssetReadinessDetail TypeScript interface:
    - infrastructure: Technology and resource specifications
    - application: Application-specific attributes
    - business: Business context and ownership
    - technical_debt: Maintenance and quality metrics

    Args:
        missing_attrs: Flat list of missing attribute names

    Returns:
        Dict with categorized attributes matching frontend AssetReadinessDetail type
    """
    # Category definitions (must match get_missing_critical_attributes docstring)
    category_map = {
        "infrastructure": {
            "asset_name",
            "technology_stack",
            "operating_system",
            "cpu_cores",
            "memory_gb",
            "storage_gb",
        },
        "application": {
            "business_criticality",
            "application_type",
            "architecture_pattern",
            "dependencies",
            "user_base",
            "data_sensitivity",
            "compliance_requirements",
            "sla_requirements",
        },
        "business": {
            "business_owner",
            "annual_operating_cost",
            "business_value",
            "strategic_importance",
        },
        "technical_debt": {
            "code_quality_score",
            "last_update_date",
            "support_status",
            "known_vulnerabilities",
        },
    }

    # Initialize result with empty lists for all categories
    result = {
        "infrastructure": [],
        "application": [],
        "business": [],
        "technical_debt": [],
    }

    # Categorize each missing attribute
    for attr in missing_attrs:
        categorized = False
        for category, attrs in category_map.items():
            if attr in attrs:
                result[category].append(attr)
                categorized = True
                break

        # Log warning for uncategorized attributes (shouldn't happen)
        if not categorized:
            logger.warning(
                f"Missing attribute '{attr}' not found in any category - "
                f"may need to update category_map"
            )

    return result


def get_actionable_guidance(blockers: List[Dict[str, Any]]) -> List[str]:
    """Generate actionable guidance based on blockers."""
    if not blockers:
        return ["All assets are ready for assessment"]

    guidance = []

    # Count common missing attributes (check both old and new field names)
    missing_attrs_count: Dict[str, int] = {}
    for blocker in blockers:
        # Support both missing_critical_attributes (flat) and missing_attributes (categorized)
        missing_flat = blocker.get("missing_critical_attributes", [])
        missing_cat = blocker.get("missing_attributes", {})

        # If categorized format, flatten it
        if missing_cat:
            missing_flat = []
            for category_attrs in missing_cat.values():
                if isinstance(category_attrs, list):
                    missing_flat.extend(category_attrs)

        # Count occurrences
        for attr in missing_flat:
            missing_attrs_count[attr] = missing_attrs_count.get(attr, 0) + 1

    # Generate guidance for most common missing attributes (top 3)
    top_missing = sorted(missing_attrs_count.items(), key=lambda x: x[1], reverse=True)[
        :3
    ]

    for attr, count in top_missing:
        guidance.append(
            f"{count} asset(s) missing '{attr.replace('_', ' ')}' - "
            f"Complete this in Collection flow"
        )

    # Overall blockers count
    guidance.insert(0, f"{len(blockers)} asset(s) not ready for assessment")

    return guidance
