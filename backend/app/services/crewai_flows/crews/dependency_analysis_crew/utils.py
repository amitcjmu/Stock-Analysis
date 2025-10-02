"""
Dependency Analysis Utilities

This module contains utility functions for dependency analysis result processing,
architecture type determination, and summary generation.
"""

import logging
from typing import Any, Dict, List

from app.services.crewai_flows.crews.dependency_analysis_crew.tools import (
    DependencyAnalysisResult,
)

logger = logging.getLogger(__name__)


def determine_architecture_type_from_asset(asset_data: Dict[str, Any]) -> str:
    """
    Determine architecture type from asset information.

    Args:
        asset_data: Asset dictionary containing type and name information

    Returns:
        String indicating the architecture tier (web_tier, application_tier, etc.)
    """
    asset_type = asset_data.get("type", "").lower()
    asset_name = asset_data.get("name", "").lower()

    if "web" in asset_name or "frontend" in asset_name:
        return "web_tier"
    elif "api" in asset_name or "service" in asset_name:
        return "application_tier"
    elif "database" in asset_type or "db" in asset_type:
        return "data_tier"
    elif "server" in asset_type:
        return "infrastructure"
    else:
        return "standalone"


def generate_dependency_summary(
    analysis_results: List[DependencyAnalysisResult],
) -> Dict[str, Any]:
    """
    Generate comprehensive dependency analysis summary.

    Args:
        analysis_results: List of DependencyAnalysisResult objects

    Returns:
        Dictionary containing summary statistics and recommendations
    """
    # Complexity distribution
    complexity_dist = {}
    for result in analysis_results:
        complexity = result.infrastructure_dependencies.get(
            "dependency_complexity", "medium"
        )
        complexity_dist[complexity] = complexity_dist.get(complexity, 0) + 1

    # Average confidence
    avg_confidence = (
        sum(result.confidence_score for result in analysis_results)
        / len(analysis_results)
        if analysis_results
        else 0
    )

    return {
        "total_assets": len(analysis_results),
        "complexity_distribution": complexity_dist,
        "average_confidence": round(avg_confidence, 2),
        "analysis_quality": (
            "high"
            if avg_confidence > 0.8
            else "medium" if avg_confidence > 0.6 else "low"
        ),
        "recommendations": [
            f"Average analysis confidence of {avg_confidence:.1%} indicates good dependency mapping",
            "Focus on high-complexity assets for detailed migration planning",
        ],
    }


# Export utility functions
__all__ = [
    "determine_architecture_type_from_asset",
    "generate_dependency_summary",
]
