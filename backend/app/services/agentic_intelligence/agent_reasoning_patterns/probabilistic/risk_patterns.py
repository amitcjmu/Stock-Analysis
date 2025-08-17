"""
Probabilistic Risk Patterns Module

This module implements probabilistic reasoning patterns for risk assessment using
Monte Carlo-style analysis and probability distributions for risk evaluation.
"""

import logging
from typing import Any, Dict, List, Tuple

from ..base import BaseReasoningPattern, ReasoningEvidence
from .probability_core import BayesianInference

logger = logging.getLogger(__name__)


class ProbabilisticRiskPattern(BaseReasoningPattern):
    """
    Probabilistic reasoning pattern for risk assessment.
    Uses Monte Carlo-style analysis and probability distributions for risk evaluation.
    """

    def __init__(self):
        super().__init__(
            "probabilistic_risk",
            "Probabilistic Risk Assessment",
            "Uses probabilistic methods to assess risk under uncertainty",
        )

    def calculate_risk_probability(
        self, asset_data: Dict[str, Any], evidence_pieces: List[ReasoningEvidence]
    ) -> Tuple[Dict[str, float], float, List[str]]:
        """
        Calculate probabilistic risk assessment across multiple risk categories.

        Args:
            asset_data: Asset data
            evidence_pieces: Supporting evidence

        Returns:
            Tuple of (risk_probabilities, overall_confidence, reasoning_steps)
        """
        risk_categories = {
            "security_risk": self._assess_security_risk_probability(
                asset_data, evidence_pieces
            ),
            "availability_risk": self._assess_availability_risk_probability(
                asset_data, evidence_pieces
            ),
            "compliance_risk": self._assess_compliance_risk_probability(
                asset_data, evidence_pieces
            ),
            "operational_risk": self._assess_operational_risk_probability(
                asset_data, evidence_pieces
            ),
        }

        reasoning_steps = []
        overall_confidence = 0.0

        for risk_type, (probability, confidence, reasoning) in risk_categories.items():
            reasoning_steps.extend(reasoning)
            overall_confidence += confidence

        overall_confidence /= len(risk_categories)

        # Extract just probabilities for return
        risk_probabilities = {
            risk_type: data[0] for risk_type, data in risk_categories.items()
        }

        return risk_probabilities, overall_confidence, reasoning_steps

    def _assess_security_risk_probability(
        self, asset_data: Dict[str, Any], evidence_pieces: List[ReasoningEvidence]
    ) -> Tuple[float, float, List[str]]:
        """Assess security risk probability"""
        return self._assess_risk_by_category(
            asset_data, 0.2, ["java 8", "windows server 2012"], "security"
        )

    def _assess_availability_risk_probability(
        self, asset_data: Dict[str, Any], evidence_pieces: List[ReasoningEvidence]
    ) -> Tuple[float, float, List[str]]:
        """Assess availability risk probability"""
        return self._assess_risk_by_category(
            asset_data, 0.15, ["single", "standalone"], "availability"
        )

    def _assess_compliance_risk_probability(
        self, asset_data: Dict[str, Any], evidence_pieces: List[ReasoningEvidence]
    ) -> Tuple[float, float, List[str]]:
        """Assess compliance risk probability"""
        return self._assess_risk_by_category(
            asset_data, 0.1, ["centos 6", "ubuntu 14"], "compliance"
        )

    def _assess_operational_risk_probability(
        self, asset_data: Dict[str, Any], evidence_pieces: List[ReasoningEvidence]
    ) -> Tuple[float, float, List[str]]:
        """Assess operational risk probability"""
        bayesian_inference = BayesianInference(0.25)
        reasoning_steps = []
        tech_stack = asset_data.get("technology_stack", "").lower()
        if len(tech_stack.split()) > 3:
            bayesian_inference.update_belief(
                0.5, 0.6, "Complex technology stack increases operational risk"
            )
            reasoning_steps.append("Complex tech stack increases operational risk")
        return (
            bayesian_inference.prior_probability,
            min(0.9, 0.5 + len(reasoning_steps) * 0.1),
            reasoning_steps,
        )

    def _assess_risk_by_category(
        self,
        asset_data: Dict[str, Any],
        prior: float,
        indicators: List[str],
        category: str,
    ) -> Tuple[float, float, List[str]]:
        """Generic risk assessment helper"""
        bayesian_inference = BayesianInference(prior)
        reasoning_steps = []
        content = " ".join(
            [asset_data.get("technology_stack", ""), asset_data.get("name", "")]
        ).lower()

        for indicator in indicators:
            if indicator in content:
                bayesian_inference.update_belief(
                    0.8, 0.9, f"{category.title()} risk from {indicator}"
                )
                reasoning_steps.append(f"{indicator} increases {category} risk")

        return (
            bayesian_inference.prior_probability,
            min(0.9, 0.5 + len(reasoning_steps) * 0.1),
            reasoning_steps,
        )
