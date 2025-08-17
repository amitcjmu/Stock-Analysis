"""
Uncertainty Quantification Module

This module quantifies and manages uncertainty in agent reasoning,
providing methods to calculate, propagate, and communicate uncertainty.
"""

import logging
from typing import Any, Dict, List

from ..base import ReasoningEvidence
from .probability_core import ProbabilityDistribution

logger = logging.getLogger(__name__)


class UncertaintyQuantification:
    """
    Quantifies and manages uncertainty in agent reasoning.
    Provides methods to calculate, propagate, and communicate uncertainty.
    """

    @staticmethod
    def calculate_evidence_uncertainty(
        evidence_pieces: List[ReasoningEvidence],
    ) -> Dict[str, float]:
        """
        Calculate uncertainty metrics for a collection of evidence.

        Args:
            evidence_pieces: List of evidence to analyze

        Returns:
            Dictionary with uncertainty metrics
        """
        if not evidence_pieces:
            return {
                "confidence_mean": 0.0,
                "confidence_variance": 1.0,
                "evidence_consistency": 0.0,
                "overall_uncertainty": 1.0,
            }

        confidences = [evidence.confidence for evidence in evidence_pieces]

        # Basic statistics
        confidence_mean = sum(confidences) / len(confidences)
        confidence_variance = sum(
            (c - confidence_mean) ** 2 for c in confidences
        ) / len(confidences)

        # Evidence consistency (how well evidence agrees)
        evidence_types = [evidence.evidence_type for evidence in evidence_pieces]
        unique_types = len(set(evidence_types))
        consistency = (
            1.0 - (unique_types / len(evidence_pieces)) if evidence_pieces else 0.0
        )

        # Overall uncertainty combines variance and consistency
        overall_uncertainty = (confidence_variance + (1.0 - consistency)) / 2.0

        return {
            "confidence_mean": confidence_mean,
            "confidence_variance": confidence_variance,
            "evidence_consistency": consistency,
            "overall_uncertainty": overall_uncertainty,
        }

    @staticmethod
    def propagate_uncertainty(
        base_score: float, uncertainty_metrics: Dict[str, float]
    ) -> ProbabilityDistribution:
        """
        Propagate uncertainty through calculations to create a probability distribution.

        Args:
            base_score: Base calculated score
            uncertainty_metrics: Uncertainty metrics from evidence

        Returns:
            Probability distribution representing the uncertain score
        """
        # Use overall uncertainty to determine variance
        variance = uncertainty_metrics.get("overall_uncertainty", 0.5) * 2.0

        return ProbabilityDistribution(
            mean=base_score, variance=variance, distribution_type="normal"
        )

    @staticmethod
    def uncertainty_aware_recommendation(
        score_distribution: ProbabilityDistribution, decision_threshold: float
    ) -> Dict[str, Any]:
        """
        Generate uncertainty-aware recommendations.

        Args:
            score_distribution: Probability distribution of the score
            decision_threshold: Threshold for decision making

        Returns:
            Dictionary with recommendation and uncertainty information
        """
        prob_above_threshold = score_distribution.probability_above_threshold(
            decision_threshold
        )
        confidence_interval = score_distribution.confidence_interval(0.95)

        # Determine recommendation based on probability
        if prob_above_threshold >= 0.8:
            recommendation = "high_confidence_positive"
        elif prob_above_threshold >= 0.6:
            recommendation = "moderate_confidence_positive"
        elif prob_above_threshold >= 0.4:
            recommendation = "uncertain"
        elif prob_above_threshold >= 0.2:
            recommendation = "moderate_confidence_negative"
        else:
            recommendation = "high_confidence_negative"

        return {
            "recommendation": recommendation,
            "probability_above_threshold": prob_above_threshold,
            "confidence_interval": confidence_interval,
            "mean_score": score_distribution.mean,
            "uncertainty_level": score_distribution.std_dev,
        }
