"""
Business-related intelligent options for questionnaire generation.
Handles business logic complexity and change tolerance.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


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
    business_criticality_raw = asset_context.get("business_criticality", "")
    # Normalize: strip whitespace, convert to lowercase
    business_criticality = (business_criticality_raw or "").strip().lower()

    # Mission critical → Show "Very Low" tolerance first (change averse)
    if business_criticality in [
        "mission_critical",
        "mission-critical",
        "critical",
        "mission",
    ]:
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
    elif business_criticality in [
        "business_critical",
        "business-critical",
        "business",
        "high",
    ]:
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
    elif business_criticality in [
        "low",
        "low_priority",
        "development",
        "testing",
        "dev",
        "test",
        "qa",
    ]:
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
    elif business_criticality in ["important", "standard", "moderate", "medium"]:
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
