"""
Probabilistic Business Value Patterns Module

This module implements probabilistic reasoning patterns for business value assessment
using statistical methods to estimate business value under uncertainty.
"""

import logging
from typing import Any, Dict, List, Tuple

from ..base import BaseReasoningPattern, ReasoningEvidence, EvidenceType
from .probability_core import ProbabilityDistribution, BayesianInference

logger = logging.getLogger(__name__)


class ProbabilisticBusinessValuePattern(BaseReasoningPattern):
    """
    Probabilistic reasoning pattern for business value assessment.
    Uses statistical methods to estimate business value under uncertainty.
    """

    def __init__(self):
        super().__init__(
            "probabilistic_business_value",
            "Probabilistic Business Value Assessment",
            "Uses probabilistic methods to assess business value under uncertainty",
        )
        self.value_priors = self._initialize_value_priors()

    def _initialize_value_priors(self) -> Dict[str, float]:
        """Initialize prior probabilities for business value indicators"""
        return {
            "production_environment": 0.8,  # High prior for production assets
            "financial_system": 0.9,  # Very high prior for financial systems
            "customer_facing": 0.7,  # High prior for customer-facing systems
            "internal_tool": 0.3,  # Low prior for internal tools
            "development_environment": 0.1,  # Very low prior for dev environments
        }

    def calculate_probabilistic_business_value(
        self, asset_data: Dict[str, Any], evidence_pieces: List[ReasoningEvidence]
    ) -> Tuple[ProbabilityDistribution, float, List[str]]:
        """
        Calculate probabilistic business value assessment.

        Args:
            asset_data: Asset data
            evidence_pieces: Supporting evidence

        Returns:
            Tuple of (value_distribution, confidence, reasoning_steps)
        """
        # Start with base prior
        bayesian_inference = BayesianInference(0.5)  # Neutral prior
        reasoning_steps = []

        # Update beliefs based on environment
        environment = asset_data.get("environment", "").lower()
        if environment in ["production", "prod"]:
            updated_prob = bayesian_inference.update_belief(
                evidence_likelihood=0.8,
                evidence_strength=0.9,
                evidence_description="Production environment indicates high business value",
            )
            reasoning_steps.append(
                f"Production environment updated probability to {updated_prob:.3f}"
            )

        # Update beliefs based on naming patterns
        name = asset_data.get("name", "").lower()
        financial_keywords = ["finance", "billing", "payment", "accounting"]
        if any(keyword in name for keyword in financial_keywords):
            updated_prob = bayesian_inference.update_belief(
                evidence_likelihood=0.9,
                evidence_strength=0.8,
                evidence_description="Financial system naming indicates critical business value",
            )
            reasoning_steps.append(
                f"Financial naming pattern updated probability to {updated_prob:.3f}"
            )

        # Update beliefs based on performance metrics
        cpu_util = asset_data.get("cpu_utilization_percent")
        if cpu_util and cpu_util >= 70:
            updated_prob = bayesian_inference.update_belief(
                evidence_likelihood=0.7,
                evidence_strength=0.6,
                evidence_description="High CPU utilization suggests business-critical usage",
            )
            reasoning_steps.append(
                f"High CPU utilization updated probability to {updated_prob:.3f}"
            )

        # Update beliefs based on evidence pieces
        for evidence in evidence_pieces:
            if evidence.evidence_type == EvidenceType.BUSINESS_CRITICALITY:
                updated_prob = bayesian_inference.update_belief(
                    evidence_likelihood=evidence.confidence,
                    evidence_strength=0.7,
                    evidence_description=evidence.reasoning,
                )
                reasoning_steps.append(
                    f"Evidence '{evidence.reasoning}' updated probability to {updated_prob:.3f}"
                )

        # Convert probability to business value score and create distribution
        final_probability = bayesian_inference.prior_probability
        business_value_score = int(final_probability * 10)  # Scale to 1-10

        # Create probability distribution with uncertainty
        variance = self._calculate_value_uncertainty(asset_data, evidence_pieces)
        value_distribution = ProbabilityDistribution(
            mean=business_value_score, variance=variance, distribution_type="normal"
        )

        confidence = self._calculate_assessment_confidence(
            bayesian_inference, evidence_pieces
        )

        return value_distribution, confidence, reasoning_steps

    def _calculate_value_uncertainty(
        self, asset_data: Dict[str, Any], evidence_pieces: List[ReasoningEvidence]
    ) -> float:
        """Calculate uncertainty/variance in business value assessment"""
        base_variance = 1.0

        # Reduce variance with more evidence
        evidence_count = len(evidence_pieces)
        variance_reduction = min(0.8, evidence_count * 0.1)

        # Increase variance for conflicting evidence
        confidence_values = [e.confidence for e in evidence_pieces]
        if confidence_values:
            confidence_spread = max(confidence_values) - min(confidence_values)
            variance_increase = confidence_spread * 0.5
        else:
            variance_increase = 0.5  # High uncertainty with no evidence

        final_variance = max(
            0.1, base_variance - variance_reduction + variance_increase
        )
        return final_variance

    def _calculate_assessment_confidence(
        self,
        bayesian_inference: BayesianInference,
        evidence_pieces: List[ReasoningEvidence],
    ) -> float:
        """Calculate overall confidence in the assessment"""
        # Base confidence from Bayesian inference convergence
        evidence_count = len(bayesian_inference.evidence_history)
        base_confidence = min(0.9, 0.3 + (evidence_count * 0.1))

        # Adjust for evidence quality
        if evidence_pieces:
            avg_evidence_confidence = sum(e.confidence for e in evidence_pieces) / len(
                evidence_pieces
            )
            confidence = (base_confidence + avg_evidence_confidence) / 2
        else:
            confidence = base_confidence * 0.5  # Reduce confidence with no evidence

        return confidence
