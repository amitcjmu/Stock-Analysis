"""
Infrastructure-related intelligent options for questionnaire generation.
Handles availability requirements and SLA configurations.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def get_availability_requirements_options(
    asset_context: Dict,
) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """Suggest availability SLAs based on business criticality.

    Args:
        asset_context: Dict with asset data including 'business_criticality', etc.

    Returns:
        Tuple of (field_type, options) or None if not applicable
    """
    business_criticality_raw = asset_context.get("business_criticality", "")
    # Normalize: strip whitespace, convert to lowercase
    business_criticality = (business_criticality_raw or "").strip().lower()

    # Mission critical → 99.99% first (highest SLA)
    # Use exact matching with normalized enum values to avoid substring matching bugs
    if business_criticality in [
        "mission_critical",
        "mission-critical",
        "critical",
        "mission",
    ]:
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
    elif business_criticality in [
        "business_critical",
        "business-critical",
        "business",
        "high",
    ]:
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
    elif business_criticality in ["important", "standard", "moderate", "medium"]:
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
