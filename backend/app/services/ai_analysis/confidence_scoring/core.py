"""
Core confidence scoring implementation.

Main ConfidenceScorer class that orchestrates the confidence assessment process.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .config import ConfidenceScoringConfig
from .factors import ConfidenceFactorCalculator
from .models import ConfidenceAssessment
from .strategies import StrategyConfidenceCalculator
from .utils import create_error_assessment

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Advanced confidence scoring system for ADCS data collection and 6R recommendations.

    Uses multiple algorithms and weighting factors to provide accurate confidence
    assessments that improve over time through learning and validation.
    """

    def __init__(self):
        """Initialize confidence scorer with default weights and parameters"""
        self.factor_weights = ConfidenceScoringConfig.get_factor_weights()
        self.strategy_requirements = ConfidenceScoringConfig.get_strategy_requirements()
        self.quality_thresholds = ConfidenceScoringConfig.get_quality_thresholds()

        # Initialize calculators
        self.factor_calculator = ConfidenceFactorCalculator(
            self.factor_weights, self.strategy_requirements
        )
        self.strategy_calculator = StrategyConfidenceCalculator(
            self.strategy_requirements
        )

    def calculate_overall_confidence(
        self,
        asset_data: Dict[str, Any],
        collection_metadata: Dict[str, Any],
        business_context: Optional[Dict[str, Any]] = None,
    ) -> ConfidenceAssessment:
        """
        Calculate overall confidence score for an asset's data.

        Args:
            asset_data: Collected asset data
            collection_metadata: Metadata about data collection process
            business_context: Business context information

        Returns:
            Complete confidence assessment
        """
        try:
            # Calculate individual confidence factors
            factors = []

            # Data Completeness Factor
            completeness_factor = self.factor_calculator.calculate_completeness_factor(
                asset_data
            )
            factors.append(completeness_factor)

            # Data Quality Factor
            quality_factor = self.factor_calculator.calculate_quality_factor(
                asset_data, collection_metadata
            )
            factors.append(quality_factor)

            # Source Reliability Factor
            reliability_factor = self.factor_calculator.calculate_reliability_factor(
                collection_metadata
            )
            factors.append(reliability_factor)

            # Validation Status Factor
            validation_factor = self.factor_calculator.calculate_validation_factor(
                asset_data, collection_metadata
            )
            factors.append(validation_factor)

            # Business Context Factor
            if business_context:
                context_factor = (
                    self.factor_calculator.calculate_business_context_factor(
                        asset_data, business_context
                    )
                )
                factors.append(context_factor)

            # Temporal Freshness Factor
            freshness_factor = self.factor_calculator.calculate_freshness_factor(
                collection_metadata
            )
            factors.append(freshness_factor)

            # Cross-validation Factor
            cross_val_factor = self.factor_calculator.calculate_cross_validation_factor(
                asset_data, collection_metadata
            )
            factors.append(cross_val_factor)

            # Calculate weighted overall score
            overall_score = self.strategy_calculator._calculate_weighted_score(factors)

            # Calculate strategy-specific confidence scores
            strategy_scores = self.strategy_calculator.calculate_strategy_scores(
                asset_data, factors
            )

            # Identify critical gaps
            critical_gaps = self.strategy_calculator.identify_critical_gaps(
                asset_data, factors
            )

            # Generate recommendations
            recommendations = (
                self.strategy_calculator.generate_confidence_recommendations(
                    factors, strategy_scores, critical_gaps
                )
            )

            return ConfidenceAssessment(
                overall_score=overall_score,
                strategy_scores=strategy_scores,
                contributing_factors=factors,
                critical_gaps=critical_gaps,
                recommendations=recommendations,
                last_updated=datetime.now(timezone.utc),
                assessment_metadata={
                    "algorithm_version": "confidence_v1.0",
                    "factor_count": len(factors),
                    "calculation_method": "weighted_composite",
                },
            )

        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return create_error_assessment(str(e))
