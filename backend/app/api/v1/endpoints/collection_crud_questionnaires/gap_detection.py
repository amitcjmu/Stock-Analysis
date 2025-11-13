"""
Gap detection utilities for collection questionnaires.
Functions for identifying missing critical fields and assessing data quality.
"""

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Fields that should ALWAYS be shown for user verification (even if present)
VERIFICATION_FIELDS = ["operating_system_version"]  # OS is critical for EOL context


def _check_missing_critical_fields(asset) -> Tuple[List[str], dict]:
    """Check for missing critical fields using 22-attribute assessment system.

    Returns:
        Tuple of (missing_attributes, existing_values)
        - missing_attributes: List of attribute names with no value
        - existing_values: Dict mapping attribute_name -> existing value (for pre-fill)
    """
    try:
        from app.services.crewai_flows.tools.critical_attributes_tool.base import (
            CriticalAttributesDefinition,
        )

        attribute_mapping = CriticalAttributesDefinition.get_attribute_mapping()
        missing_attributes = []
        existing_values = {}

        for attr_name, attr_config in attribute_mapping.items():
            if not attr_config.get("required", False):
                continue

            has_value = False
            current_value = None

            for field_path in attr_config.get("asset_fields", []):
                if "." in field_path:
                    value = asset
                    for part in field_path.split("."):
                        value = getattr(value, part, None) or {}
                        if not isinstance(value, dict):
                            break
                    if value and value != {}:
                        has_value = True
                        current_value = value
                        break
                else:
                    field_value = getattr(asset, field_path, None)
                    if field_value and not (
                        isinstance(field_value, (list, dict)) and len(field_value) == 0
                    ):
                        has_value = True
                        current_value = field_value
                        break

            # Missing fields: always include in questionnaire
            if not has_value:
                missing_attributes.append(attr_name)
            # Verification fields: include even if present (for user confirmation)
            elif attr_name in VERIFICATION_FIELDS:
                existing_values[attr_name] = current_value
                missing_attributes.append(
                    attr_name
                )  # Treat as "missing" to generate question

        return missing_attributes, existing_values

    except ImportError as e:
        logger.warning(
            f"Could not import CriticalAttributesDefinition, using fallback: {e}"
        )
        critical_fields = [
            "business_owner",
            "technical_owner",
            "dependencies",
            "operating_system",
        ]
        missing = [
            field for field in critical_fields if not getattr(asset, field, None)
        ]
        existing = (
            {"operating_system": getattr(asset, "operating_system", None)}
            if getattr(asset, "operating_system", None)
            else {}
        )

        # Always include operating_system for verification
        if "operating_system" not in missing and existing.get("operating_system"):
            missing.append("operating_system")

        return missing, existing


def _assess_data_quality(asset) -> dict:
    """Assess data quality of asset."""
    completeness_score = getattr(asset, "completeness_score", 0.0) or 0.0
    confidence_score = getattr(asset, "confidence_score", 0.0) or 0.0
    if completeness_score < 0.8 or confidence_score < 0.7:
        return {
            "completeness": completeness_score,
            "confidence": confidence_score,
            "needs_validation": True,
        }
    return {}
