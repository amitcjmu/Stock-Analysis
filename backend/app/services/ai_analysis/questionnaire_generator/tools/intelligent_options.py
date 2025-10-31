"""
Intelligent Options Module
Extracted from section_builders.py for modularization.
Contains context-aware pattern detection logic for questionnaire field options.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def get_security_vulnerabilities_options(
    asset_context: Dict,
) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """Provide intelligent vulnerability options based on EOL technology assessment.

    Args:
        asset_context: Dict with asset data including 'eol_technology', etc.

    Returns:
        Tuple of (field_type, options) or None if not applicable
    """
    eol_status = asset_context.get("eol_technology", "").upper()

    # EOL expired → High vulnerability risk
    if "EOL_EXPIRED" in eol_status or "UNSUPPORTED" in eol_status:
        options = [
            {
                "value": "high_severity",
                "label": "High Severity - Critical vulnerabilities exist",
            },
            {
                "value": "medium_severity",
                "label": "Medium Severity - Moderate risk, should be addressed",
            },
            {"value": "not_assessed", "label": "Not Assessed - Security scan needed"},
            {"value": "low_severity", "label": "Low Severity - Minor issues, low risk"},
            {
                "value": "none_known",
                "label": "None Known - No vulnerabilities identified",
            },
        ]
        logger.info(
            f"Providing high-risk vulnerability options for EOL status: {eol_status}"
        )
        return "select", options

    # EOL soon → Medium vulnerability risk
    elif "EOL_SOON" in eol_status or "DEPRECATED" in eol_status:
        options = [
            {
                "value": "medium_severity",
                "label": "Medium Severity - Moderate risk, should be addressed",
            },
            {"value": "not_assessed", "label": "Not Assessed - Security scan needed"},
            {"value": "low_severity", "label": "Low Severity - Minor issues, low risk"},
            {
                "value": "high_severity",
                "label": "High Severity - Critical vulnerabilities exist",
            },
            {
                "value": "none_known",
                "label": "None Known - No vulnerabilities identified",
            },
        ]
        logger.info(
            f"Providing medium-risk vulnerability options for EOL status: {eol_status}"
        )
        return "select", options

    # Current/Supported → Lower vulnerability risk
    elif "CURRENT" in eol_status or "SUPPORTED" in eol_status:
        options = [
            {
                "value": "none_known",
                "label": "None Known - No vulnerabilities identified",
            },
            {"value": "low_severity", "label": "Low Severity - Minor issues, low risk"},
            {"value": "not_assessed", "label": "Not Assessed - Security scan needed"},
            {
                "value": "medium_severity",
                "label": "Medium Severity - Moderate risk, should be addressed",
            },
            {
                "value": "high_severity",
                "label": "High Severity - Critical vulnerabilities exist",
            },
        ]
        logger.info(
            f"Providing low-risk vulnerability options for EOL status: {eol_status}"
        )
        return "select", options

    # If eol_technology field exists but doesn't match patterns, return None
    return None


def get_business_logic_complexity_options(
    asset_context: Dict,
) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """Suggest complexity levels based on technology stack patterns.

    Args:
        asset_context: Dict with asset data including 'technology_stack', etc.

    Returns:
        Tuple of (field_type, options) or None if not applicable
    """
    tech_stack = asset_context.get("technology_stack", "")
    if isinstance(tech_stack, list):
        # Join list items for pattern matching
        tech_stack = " ".join(tech_stack).upper()
    else:
        tech_stack = str(tech_stack).upper()

    # Detect enterprise middleware → Typically very complex business rules
    if any(
        keyword in tech_stack
        for keyword in ["WEBSPHERE", "WEBLOGIC", "SAP", "ORACLE", "MAINFRAME"]
    ):
        options = [
            {
                "value": "very_complex",
                "label": "Very Complex - Intricate business rules, regulatory logic",
            },
            {
                "value": "complex",
                "label": "Complex - Advanced workflows, multi-step processes",
            },
            {
                "value": "moderate",
                "label": "Moderate - Standard business rules, some workflows",
            },
            {"value": "simple", "label": "Simple - Basic CRUD, minimal business logic"},
        ]
        logger.info(
            f"Providing enterprise complexity options for tech stack: {tech_stack[:50]}"
        )
        return "select", options

    # Detect modern microservices → Tends toward simple/moderate per service
    elif any(
        keyword in tech_stack
        for keyword in ["DOCKER", "KUBERNETES", "NODEJS", "PYTHON", "GO"]
    ):
        options = [
            {"value": "simple", "label": "Simple - Basic CRUD, minimal business logic"},
            {
                "value": "moderate",
                "label": "Moderate - Standard business rules, some workflows",
            },
            {
                "value": "complex",
                "label": "Complex - Advanced workflows, multi-step processes",
            },
            {
                "value": "very_complex",
                "label": "Very Complex - Intricate business rules, regulatory logic",
            },
        ]
        logger.info(
            f"Providing microservices complexity options for tech stack: {tech_stack[:50]}"
        )
        return "select", options

    # Detect .NET/Java enterprise → Moderate to complex
    elif any(keyword in tech_stack for keyword in ["DOTNET", ".NET", "JAVA", "SPRING"]):
        options = [
            {
                "value": "moderate",
                "label": "Moderate - Standard business rules, some workflows",
            },
            {
                "value": "complex",
                "label": "Complex - Advanced workflows, multi-step processes",
            },
            {"value": "simple", "label": "Simple - Basic CRUD, minimal business logic"},
            {
                "value": "very_complex",
                "label": "Very Complex - Intricate business rules, regulatory logic",
            },
        ]
        logger.info(
            f"Providing enterprise app complexity options for tech stack: {tech_stack[:50]}"
        )
        return "select", options

    # If technology_stack is present but doesn't match patterns, return None
    return None


def get_change_tolerance_options(
    asset_context: Dict,
) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """Suggest change tolerance based on business criticality.

    Args:
        asset_context: Dict with asset data including 'business_criticality', etc.

    Returns:
        Tuple of (field_type, options) or None if not applicable
    """
    business_criticality = asset_context.get("business_criticality", "")

    # Mission critical → Show "Very Low" tolerance first (change averse)
    if business_criticality == "mission_critical":
        options = [
            {
                "value": "very_low",
                "label": "Very Low (Change averse, extensive change management)",
            },
            {
                "value": "low",
                "label": "Low (Significant training needed, resistance to change)",
            },
            {
                "value": "medium",
                "label": "Medium (Some training required, moderate adaptation)",
            },
            {
                "value": "high",
                "label": "High (Users adapt quickly, minimal training needed)",
            },
        ]
        logger.info(
            f"Providing mission-critical change_tolerance options (very_low first) "
            f"for business_criticality: {business_criticality}"
        )
        return "select", options

    # Business critical → Show "Low/Medium" tolerance first
    elif business_criticality == "business_critical":
        options = [
            {
                "value": "low",
                "label": "Low (Significant training needed, resistance to change)",
            },
            {
                "value": "medium",
                "label": "Medium (Some training required, moderate adaptation)",
            },
            {
                "value": "very_low",
                "label": "Very Low (Change averse, extensive change management)",
            },
            {
                "value": "high",
                "label": "High (Users adapt quickly, minimal training needed)",
            },
        ]
        logger.info(
            f"Providing business-critical change_tolerance options (low/medium first) "
            f"for business_criticality: {business_criticality}"
        )
        return "select", options

    # Low priority (development/testing) → Show "High" tolerance first
    elif business_criticality == "low":
        options = [
            {
                "value": "high",
                "label": "High (Users adapt quickly, minimal training needed)",
            },
            {
                "value": "medium",
                "label": "Medium (Some training required, moderate adaptation)",
            },
            {
                "value": "low",
                "label": "Low (Significant training needed, resistance to change)",
            },
            {
                "value": "very_low",
                "label": "Very Low (Change averse, extensive change management)",
            },
        ]
        logger.info(
            f"Providing low-priority change_tolerance options (high first) "
            f"for business_criticality: {business_criticality}"
        )
        return "select", options

    # Important or Standard → Show balanced options (Medium first)
    elif business_criticality in ["important", "standard"]:
        options = [
            {
                "value": "medium",
                "label": "Medium (Some training required, moderate adaptation)",
            },
            {
                "value": "high",
                "label": "High (Users adapt quickly, minimal training needed)",
            },
            {
                "value": "low",
                "label": "Low (Significant training needed, resistance to change)",
            },
            {
                "value": "very_low",
                "label": "Very Low (Change averse, extensive change management)",
            },
        ]
        logger.info(
            f"Providing balanced change_tolerance options (medium first) "
            f"for business_criticality: {business_criticality}"
        )
        return "select", options

    # If business_criticality is present but doesn't match patterns, return None
    return None


def get_availability_requirements_options(
    asset_context: Dict,
) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """Suggest availability SLAs based on business criticality.

    Args:
        asset_context: Dict with asset data including 'business_criticality', etc.

    Returns:
        Tuple of (field_type, options) or None if not applicable
    """
    business_criticality = asset_context.get("business_criticality", "").lower()

    # Mission critical → 99.99% first (highest SLA)
    if "mission" in business_criticality or "mission_critical" in business_criticality:
        options = [
            {"value": "99.99", "label": "99.99% (4 minutes downtime/month)"},
            {"value": "99.9", "label": "99.9% (43 minutes downtime/month)"},
            {"value": "99.5", "label": "99.5% (3.6 hours downtime/month)"},
            {"value": "99.0", "label": "99.0% (7.2 hours downtime/month)"},
            {"value": "95.0", "label": "95.0% (36 hours downtime/month)"},
            {"value": "best_effort", "label": "Best Effort (No SLA)"},
        ]
        logger.info(
            f"Providing mission-critical availability_requirements (99.99% first) "
            f"for business_criticality: {business_criticality}"
        )
        return "select", options

    # Business critical → 99.9% first (high SLA)
    elif (
        "business" in business_criticality
        or "business_critical" in business_criticality
    ):
        options = [
            {"value": "99.9", "label": "99.9% (43 minutes downtime/month)"},
            {"value": "99.99", "label": "99.99% (4 minutes downtime/month)"},
            {"value": "99.5", "label": "99.5% (3.6 hours downtime/month)"},
            {"value": "99.0", "label": "99.0% (7.2 hours downtime/month)"},
            {"value": "95.0", "label": "95.0% (36 hours downtime/month)"},
            {"value": "best_effort", "label": "Best Effort (No SLA)"},
        ]
        logger.info(
            f"Providing business-critical availability_requirements (99.9% first) "
            f"for business_criticality: {business_criticality}"
        )
        return "select", options

    # Important/Standard → 99.5% first (moderate SLA)
    elif "important" in business_criticality or "standard" in business_criticality:
        options = [
            {"value": "99.5", "label": "99.5% (3.6 hours downtime/month)"},
            {"value": "99.9", "label": "99.9% (43 minutes downtime/month)"},
            {"value": "99.0", "label": "99.0% (7.2 hours downtime/month)"},
            {"value": "99.99", "label": "99.99% (4 minutes downtime/month)"},
            {"value": "95.0", "label": "95.0% (36 hours downtime/month)"},
            {"value": "best_effort", "label": "Best Effort (No SLA)"},
        ]
        logger.info(
            f"Providing standard availability_requirements (99.5% first) "
            f"for business_criticality: {business_criticality}"
        )
        return "select", options

    # Low priority/Development/Test → Best Effort first
    elif (
        "low" in business_criticality
        or "development" in business_criticality
        or "testing" in business_criticality
    ):
        options = [
            {"value": "best_effort", "label": "Best Effort (No SLA)"},
            {"value": "95.0", "label": "95.0% (36 hours downtime/month)"},
            {"value": "99.0", "label": "99.0% (7.2 hours downtime/month)"},
            {"value": "99.5", "label": "99.5% (3.6 hours downtime/month)"},
            {"value": "99.9", "label": "99.9% (43 minutes downtime/month)"},
            {"value": "99.99", "label": "99.99% (4 minutes downtime/month)"},
        ]
        logger.info(
            f"Providing low-priority availability_requirements (Best Effort first) "
            f"for business_criticality: {business_criticality}"
        )
        return "select", options

    # If business_criticality is present but doesn't match patterns, return None
    return None


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
