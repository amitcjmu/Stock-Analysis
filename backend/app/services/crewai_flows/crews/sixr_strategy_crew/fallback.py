"""
Six R Strategy Fallback - Fallback Implementation

This module contains the fallback implementation for Six R strategy determination
when CrewAI is not available. It uses heuristic-based strategy selection to provide
basic functionality while the full crew implementation is being set up.

Note: This follows the enterprise pattern of graceful degradation - the system
can operate in fallback mode until full integration is complete.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.models.asset import SixRStrategy

logger = logging.getLogger(__name__)


async def execute_fallback(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback implementation for Six R strategy determination.

    Uses simple heuristics to determine component strategies when CrewAI is not available.
    This provides basic functionality while maintaining system operation.

    Args:
        context: Execution context containing components and analysis data

    Returns:
        Dictionary containing component treatments, overall strategy, and hints
    """
    app_id = context.get("application_id", "unknown")
    components = context.get("components", [])

    logger.info(f"Executing Six R Strategy analysis in fallback mode for {app_id}")

    # Generate component treatments based on simple heuristics
    component_treatments = []
    for component in components:
        component_name = component.get("name", "unknown")
        component_type = component.get("type", "unknown")
        complexity_score = component.get("complexity_score", 5.0)

        # Simple strategy selection based on complexity and type
        if complexity_score >= 8.0:
            strategy = SixRStrategy.REWRITE.value
            confidence = 0.7
            rationale = "High complexity suggests rewrite for modernization"
        elif complexity_score >= 6.0:
            strategy = SixRStrategy.REFACTOR.value
            confidence = 0.8
            rationale = "Moderate complexity suitable for refactoring"
        else:
            strategy = SixRStrategy.REPLATFORM.value
            confidence = 0.75
            rationale = "Low complexity suitable for replatforming"

        # Adjust for component type
        if "database" in component_type.lower():
            strategy = SixRStrategy.REHOST.value
            rationale = "Database components typically rehosted with minimal changes"
        elif "frontend" in component_type.lower():
            strategy = SixRStrategy.REFACTOR.value
            rationale = "Frontend components benefit from modernization"

        component_treatments.append(
            {
                "component_name": component_name,
                "component_type": component_type,
                "strategy": strategy,
                "confidence": confidence,
                "rationale": rationale,
                "effort_estimate_hours": int(complexity_score * 20),
                "risk_factors": ["Limited analysis in fallback mode"],
                "business_benefits": [
                    "Cloud cost optimization",
                    "Improved maintainability",
                ],
            }
        )

    # Determine overall strategy (most common component strategy)
    strategy_counts = {}
    for treatment in component_treatments:
        strategy = treatment["strategy"]
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

    overall_strategy = (
        max(strategy_counts, key=strategy_counts.get)
        if strategy_counts
        else SixRStrategy.REPLATFORM.value
    )

    # Calculate overall confidence
    confidence_scores = [t["confidence"] for t in component_treatments]
    overall_confidence = (
        sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.6
    )

    # Generate move group hints
    move_group_hints = [
        {
            "group_type": "technology_affinity",
            "group_name": f"{app_id}_components",
            "applications": [app_id],
            "rationale": "Components within same application should migrate together",
            "priority": "medium",
            "estimated_effort": sum(
                t["effort_estimate_hours"] for t in component_treatments
            ),
        }
    ]

    return {
        "component_treatments": component_treatments,
        "overall_strategy": overall_strategy,
        "confidence_score": overall_confidence,
        "rationale": f"Application assessment recommends {overall_strategy} approach based on component analysis",
        "move_group_hints": move_group_hints,
        "compatibility_issues": [],  # No detailed analysis in fallback mode
        "crew_confidence": 0.6,  # Lower confidence in fallback mode
        "execution_mode": "fallback",
    }


def process_crew_results(
    result: Any, application_id: str, flow_id: str
) -> Dict[str, Any]:
    """
    Process and structure crew execution results.

    Transforms raw crew results into a consistent structure for consumption
    by downstream systems.

    Args:
        result: Raw crew execution results
        application_id: Application identifier
        flow_id: Flow identifier

    Returns:
        Structured result dictionary
    """
    try:
        # Extract component treatments
        component_treatments = result.get("component_treatments", [])

        # Structure treatments for consistency
        structured_treatments = []
        for treatment in component_treatments:
            structured_treatments.append(
                {
                    "component_name": treatment.get("component_name", ""),
                    "component_type": treatment.get("component_type", ""),
                    "strategy": treatment.get(
                        "strategy", SixRStrategy.REPLATFORM.value
                    ),
                    "confidence": treatment.get("confidence", 0.7),
                    "rationale": treatment.get("rationale", ""),
                    "effort_estimate_hours": treatment.get("effort_estimate_hours", 0),
                    "risk_factors": treatment.get("risk_factors", []),
                    "business_benefits": treatment.get("business_benefits", []),
                    "technical_benefits": treatment.get("technical_benefits", []),
                }
            )

        # Extract overall strategy and confidence
        overall_strategy = result.get("overall_strategy", SixRStrategy.REPLATFORM.value)
        confidence_score = result.get("confidence_score", 0.7)
        rationale = result.get("rationale", "Strategy determined by crew analysis")

        # Extract move group hints
        move_group_hints = result.get("move_group_hints", [])

        # Extract compatibility issues
        compatibility_issues = result.get("compatibility_issues", [])

        return {
            "component_treatments": structured_treatments,
            "overall_strategy": overall_strategy,
            "confidence_score": confidence_score,
            "rationale": rationale,
            "move_group_hints": move_group_hints,
            "compatibility_issues": compatibility_issues,
            "crew_confidence": result.get("crew_confidence", 0.8),
            "execution_metadata": {
                "crew_type": "sixr_strategy",
                "application_id": application_id,
                "execution_time": datetime.utcnow().isoformat(),
                "flow_id": flow_id,
            },
        }

    except Exception as e:
        logger.error(f"Error processing crew results: {e}")
        # Return basic structure to prevent flow failure
        return {
            "component_treatments": [],
            "overall_strategy": SixRStrategy.REPLATFORM.value,
            "confidence_score": 0.5,
            "rationale": "Error processing crew results",
            "move_group_hints": [],
            "compatibility_issues": [],
            "crew_confidence": 0.5,
            "processing_error": str(e),
        }


# Export for backward compatibility
__all__ = ["execute_fallback", "process_crew_results"]
