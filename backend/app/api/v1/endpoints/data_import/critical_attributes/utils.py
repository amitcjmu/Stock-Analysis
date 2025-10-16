"""
Utility functions for critical attributes analysis
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def agent_determine_criticality(
    source_field: str, target_field: str, enhanced_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Use agent intelligence to determine field criticality.

    This fallback heuristic is used when persisted agent assessments are not available.
    Expected behavior - not an error condition.
    """
    logger.debug(
        "🔄 Using fallback criticality analysis (no persisted assessment found)"
    )

    try:
        # Determine criticality based on field names and patterns
        target_lower = target_field.lower() if target_field else ""

        # High criticality fields for migration
        high_critical_patterns = [
            "asset_name",
            "name",
            "hostname",
            "server_name",
            "host_name",
            "ip_address",
            "ip",
            "environment",
            "env",
            "asset_type",
            "type",
            "business_owner",
            "owner",
            "technical_owner",
            "department",
            "application_name",
            "app_name",
            "application",
            "app",
        ]

        # Medium criticality fields
        medium_critical_patterns = [
            "criticality",
            "business_criticality",
            "priority",
            "operating_system",
            "os",
            "cpu",
            "memory",
            "ram",
            "storage",
            "disk",
            "six_r",
            "migration",
            "complexity",
            "dependencies",
            "mac_address",
            "mac",
        ]

        # Determine if field is critical
        is_high_critical = any(
            pattern in target_lower for pattern in high_critical_patterns
        )
        is_medium_critical = any(
            pattern in target_lower for pattern in medium_critical_patterns
        )

        if is_high_critical:
            category = "infrastructure"
            required = True
            quality_score = 95
            business_impact = "high"
            migration_critical = True
            ai_reasoning = f"High-priority field '{target_field}' is essential for migration planning"
        elif is_medium_critical:
            category = "operational"
            required = True
            quality_score = 85
            business_impact = "medium"
            migration_critical = True
            ai_reasoning = (
                f"Medium-priority field '{target_field}' supports migration assessment"
            )
        else:
            category = "supplementary"
            required = False
            quality_score = 70
            business_impact = "low"
            migration_critical = False
            ai_reasoning = f"Field '{target_field}' provides additional context"

        return {
            "category": category,
            "required": required,
            "quality_score": quality_score,
            "business_impact": business_impact,
            "migration_critical": migration_critical,
            "ai_reasoning": ai_reasoning,
        }

    except Exception as e:
        logger.error(f"Error in fallback criticality analysis: {e}")
        # Return safe defaults to prevent HTTP 500
        return {
            "category": "supplementary",
            "required": False,
            "quality_score": 50,
            "business_impact": "low",
            "migration_critical": False,
            "ai_reasoning": "Default analysis due to error",
        }
