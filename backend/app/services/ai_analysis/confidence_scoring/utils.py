"""
Utility functions for confidence scoring system.

Provides helper functions and convenience methods for confidence calculations.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import ConfidenceAssessment, ConfidenceFactor, SixRStrategy

logger = logging.getLogger(__name__)


def calculate_collection_confidence(
    collected_assets: List[Dict[str, Any]],
    collection_metadata: Dict[str, Any],
    business_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calculate confidence scores for a collection of assets.

    Args:
        collected_assets: List of collected asset data
        collection_metadata: Metadata about the collection process
        business_context: Business context information

    Returns:
        Aggregated confidence assessment for the collection
    """
    try:
        from .core import ConfidenceScorer

        scorer = ConfidenceScorer()
        asset_assessments = []

        for asset in collected_assets:
            assessment = scorer.calculate_overall_confidence(
                asset, collection_metadata, business_context
            )
            asset_assessments.append(assessment)

        # Aggregate assessments
        if not asset_assessments:
            return {"error": "No assets to assess"}

        # Calculate aggregate metrics
        overall_scores = [a.overall_score for a in asset_assessments]
        avg_overall_score = sum(overall_scores) / len(overall_scores)

        # Aggregate strategy scores
        aggregate_strategy_scores = {}
        for strategy in SixRStrategy:
            strategy_scores = [
                a.strategy_scores.get(strategy, 0) for a in asset_assessments
            ]
            aggregate_strategy_scores[strategy] = sum(strategy_scores) / len(
                strategy_scores
            )

        # Collect all critical gaps
        all_gaps = []
        for assessment in asset_assessments:
            all_gaps.extend(assessment.critical_gaps)

        # Count gap occurrences
        gap_frequency = {}
        for gap in all_gaps:
            gap_frequency[gap] = gap_frequency.get(gap, 0) + 1

        # Get most common gaps
        common_gaps = sorted(gap_frequency.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        return {
            "collection_confidence": {
                "overall_score": round(avg_overall_score, 2),
                "strategy_scores": {
                    k.value: round(v, 2) for k, v in aggregate_strategy_scores.items()
                },
                "asset_count": len(asset_assessments),
                "confidence_distribution": {
                    "excellent": len([s for s in overall_scores if s >= 90]),
                    "good": len([s for s in overall_scores if 75 <= s < 90]),
                    "acceptable": len([s for s in overall_scores if 60 <= s < 75]),
                    "poor": len([s for s in overall_scores if s < 60]),
                },
            },
            "common_gaps": [
                {"gap": gap, "frequency": freq} for gap, freq in common_gaps
            ],
            "recommendations": [
                "Focus on addressing the most common gaps across assets",
                "Implement consistent data collection standards",
                "Validate data with subject matter experts",
                "Consider additional collection phases for low-confidence assets",
            ],
            "assessment_metadata": {
                "calculation_timestamp": datetime.now(timezone.utc).isoformat(),
                "algorithm_version": "confidence_v1.0",
                "asset_assessments_count": len(asset_assessments),
            },
        }

    except Exception as e:
        logger.error(f"Error calculating collection confidence: {e}")
        return {
            "error": str(e),
            "collection_confidence": {"overall_score": 0, "asset_count": 0},
            "assessment_metadata": {
                "calculation_timestamp": datetime.now(timezone.utc).isoformat(),
                "error": True,
            },
        }


def create_error_assessment(error_msg: str) -> ConfidenceAssessment:
    """Create error assessment for failed confidence calculations"""
    return ConfidenceAssessment(
        overall_score=0.0,
        strategy_scores={strategy: 0.0 for strategy in SixRStrategy},
        contributing_factors=[],
        critical_gaps=[f"Confidence calculation error: {error_msg}"],
        recommendations=[
            "Review data collection process",
            "Retry confidence assessment",
        ],
        last_updated=datetime.now(timezone.utc),
        assessment_metadata={"error": True, "error_message": error_msg},
    )


def calculate_weighted_score(factors: List[ConfidenceFactor]) -> float:
    """Calculate weighted overall confidence score"""
    try:
        total_weighted_score = 0
        total_weight = 0

        for factor in factors:
            weighted_contribution = factor.score * factor.weight
            total_weighted_score += weighted_contribution
            total_weight += factor.weight

        if total_weight == 0:
            return 0.0

        # Normalize to 0-100 scale
        overall_score = total_weighted_score / total_weight

        return min(100.0, max(0.0, overall_score))

    except Exception as e:
        logger.error(f"Error calculating weighted score: {e}")
        return 0.0
