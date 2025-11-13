"""
Utility functions for intelligent options module.
Handles field type inference and fallback options.
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def infer_field_type_from_config(
    attr_name: str, options: List, critical_attributes_config: Dict
) -> str:
    """Infer field type from CRITICAL_ATTRIBUTES_CONFIG or options count.

    Args:
        attr_name: Field/attribute name
        options: Field options list
        critical_attributes_config: CRITICAL_ATTRIBUTES_CONFIG dict

    Returns:
        Field type string ("select", "multi_select", etc.)
    """
    # Try to get from config first
    if attr_name in critical_attributes_config:
        field_type_enum = critical_attributes_config[attr_name].get("field_type")
        if field_type_enum:
            return (
                field_type_enum.value
                if hasattr(field_type_enum, "value")
                else str(field_type_enum)
            )

    # Infer from options count
    return (
        "multi_select" if isinstance(options, list) and len(options) > 3 else "select"
    )


def get_fallback_field_type_and_options(attr_name: str) -> Tuple[str, List]:
    """Get fallback field type and options for unmapped fields.

    Args:
        attr_name: Field/attribute name

    Returns:
        Tuple of (field_type, options)
    """
    field_type = "text"
    options = []

    if "criticality" in attr_name.lower():
        field_type = "select"
        options = ["Critical", "High", "Medium", "Low"]
    elif attr_name == "compliance_constraints":  # Explicit match only
        field_type = "multi_select"
        options = ["PCI-DSS", "HIPAA", "GDPR", "SOX", "ISO 27001", "None"]
    elif attr_name == "architecture_pattern":
        field_type = "select"
        options = [
            "Monolithic",
            "N-Tier",
            "Microservices",
            "Serverless",
            "Event-Driven",
        ]
    elif attr_name == "technology_stack":
        field_type = "text"
    elif "dependencies" in attr_name.lower():
        field_type = "multi_select"
        options = []

    return field_type, options
