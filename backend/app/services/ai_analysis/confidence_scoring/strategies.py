"""
Strategy-specific confidence calculations and assessments.

Handles confidence scoring for different 6R migration strategies.
"""

import logging
from typing import Any, Dict, List

from .models import ConfidenceFactor, SixRStrategy

logger = logging.getLogger(__name__)


class StrategyConfidenceCalculator:
    """Calculator for strategy-specific confidence scores"""

    def __init__(self, strategy_requirements):
        self.strategy_requirements = strategy_requirements

    def calculate_strategy_scores(
        self, asset_data: Dict[str, Any], factors: List[ConfidenceFactor]
    ) -> Dict[SixRStrategy, float]:
        """Calculate confidence scores for each 6R strategy"""
        strategy_scores = {}

        try:
            # Get base confidence from factors
            base_confidence = self._calculate_weighted_score(factors)

            for strategy, requirements in self.strategy_requirements.items():
                # Check availability of critical attributes for this strategy
                critical_attrs = requirements["critical_attributes"]
                available_attrs = [
                    attr
                    for attr in critical_attrs
                    if attr in asset_data
                    and asset_data[attr] is not None
                    and asset_data[attr] != ""
                ]

                # Calculate attribute completeness for this strategy
                attr_completeness = (
                    len(available_attrs) / len(critical_attrs) if critical_attrs else 0
                )

                # Apply strategy-specific adjustments
                strategy_confidence = (
                    base_confidence * 0.7 + (attr_completeness * 100) * 0.3
                )

                # Apply minimum threshold consideration
                min_threshold = requirements.get("minimum_confidence_threshold", 70.0)
                if strategy_confidence < min_threshold:
                    # Reduce confidence more aggressively if below minimum
                    strategy_confidence *= 0.8

                strategy_scores[strategy] = min(100.0, max(0.0, strategy_confidence))

        except Exception as e:
            logger.error(f"Error calculating strategy scores: {e}")
            # Return default scores on error
            for strategy in SixRStrategy:
                strategy_scores[strategy] = 50.0

        return strategy_scores

    def identify_critical_gaps(
        self, asset_data: Dict[str, Any], factors: List[ConfidenceFactor]
    ) -> List[str]:
        """Identify critical gaps affecting confidence"""
        gaps = []

        try:
            # Check for low-scoring factors
            for factor in factors:
                if factor.score < 60:  # Critical threshold
                    gaps.append(f"Low {factor.factor_type.value}: {factor.description}")

            # Check for missing critical attributes
            all_critical_attrs = set()
            for strategy_data in self.strategy_requirements.values():
                all_critical_attrs.update(strategy_data["critical_attributes"])

            missing_attrs = [
                attr
                for attr in all_critical_attrs
                if attr not in asset_data or not asset_data[attr]
            ]

            if missing_attrs:
                gaps.append(
                    f"Missing critical attributes: {', '.join(missing_attrs[:5])}"
                )
                if len(missing_attrs) > 5:
                    gaps.append(
                        f"... and {len(missing_attrs) - 5} more missing attributes"
                    )

        except Exception as e:
            logger.error(f"Error identifying critical gaps: {e}")
            gaps.append(f"Error in gap analysis: {str(e)}")

        return gaps

    def generate_confidence_recommendations(
        self,
        factors: List[ConfidenceFactor],
        strategy_scores: Dict[SixRStrategy, float],
        critical_gaps: List[str],
    ) -> List[str]:
        """Generate recommendations to improve confidence"""
        recommendations = []

        try:
            # Factor-based recommendations
            for factor in factors:
                if factor.score < 70:
                    if factor.factor_type.value == "data_completeness":
                        recommendations.append(
                            "Collect missing critical attributes through targeted questionnaires"
                        )
                    elif factor.factor_type.value == "data_quality":
                        recommendations.append(
                            "Improve data quality through validation and standardization"
                        )
                    elif factor.factor_type.value == "source_reliability":
                        recommendations.append(
                            "Verify data with more reliable sources or additional collection methods"
                        )
                    elif factor.factor_type.value == "validation_status":
                        recommendations.append(
                            "Implement comprehensive data validation processes"
                        )

            # Strategy-specific recommendations
            low_confidence_strategies = [
                strategy.value
                for strategy, score in strategy_scores.items()
                if score < 75
            ]
            if low_confidence_strategies:
                recommendations.append(
                    f"Focus data collection on requirements for: {', '.join(low_confidence_strategies)}"
                )

            # Gap-based recommendations
            if len(critical_gaps) > 3:
                recommendations.append(
                    "Prioritize filling critical data gaps before proceeding with migration planning"
                )
            elif critical_gaps:
                recommendations.append(
                    "Address identified data gaps to improve migration confidence"
                )

            # General recommendations
            overall_score = self._calculate_weighted_score(factors)
            if overall_score < 60:
                recommendations.append(
                    "Consider additional data collection phases before finalizing migration strategy"
                )
            elif overall_score < 80:
                recommendations.append(
                    "Validate current data with subject matter experts"
                )

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append(
                "Review data collection process and consider additional validation"
            )

        return recommendations[:5]  # Limit to top 5 recommendations

    def _calculate_weighted_score(self, factors: List[ConfidenceFactor]) -> float:
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
