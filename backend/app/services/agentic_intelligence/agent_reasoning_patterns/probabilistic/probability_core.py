"""
Probability Core Module

This module contains core probability and statistical functionality including
probability distributions and Bayesian inference.
"""

import logging
import math
from typing import Tuple

logger = logging.getLogger(__name__)


class ProbabilityDistribution:
    """
    Represents a probability distribution for reasoning about uncertain values.
    """

    def __init__(self, mean: float, variance: float, distribution_type: str = "normal"):
        self.mean = mean
        self.variance = variance
        self.std_dev = math.sqrt(variance)
        self.distribution_type = distribution_type

    def probability_above_threshold(self, threshold: float) -> float:
        """Calculate probability that value is above threshold (simplified normal distribution)"""
        if self.std_dev == 0:
            return 1.0 if self.mean > threshold else 0.0

        # Simplified normal distribution approximation
        z_score = (threshold - self.mean) / self.std_dev

        # Approximate cumulative distribution function
        if z_score < -3:
            return 1.0
        elif z_score > 3:
            return 0.0
        else:
            # Simple approximation using error function
            return 0.5 * (1 - math.erf(z_score / math.sqrt(2)))

    def confidence_interval(
        self, confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval"""
        z_value = 1.96 if confidence_level == 0.95 else 2.58  # 95% or 99%
        margin = z_value * self.std_dev
        return (self.mean - margin, self.mean + margin)


class BayesianInference:
    """
    Implements Bayesian inference for updating beliefs based on evidence.
    """

    def __init__(self, prior_probability: float):
        self.prior_probability = prior_probability
        self.evidence_history = []

    def update_belief(
        self,
        evidence_likelihood: float,
        evidence_strength: float,
        evidence_description: str,
    ) -> float:
        """
        Update belief using Bayesian inference.

        Args:
            evidence_likelihood: P(evidence | hypothesis is true)
            evidence_strength: Weight/importance of this evidence
            evidence_description: Description of the evidence

        Returns:
            Updated posterior probability
        """
        # Store evidence for history
        self.evidence_history.append(
            {
                "likelihood": evidence_likelihood,
                "strength": evidence_strength,
                "description": evidence_description,
            }
        )

        # Simplified Bayesian update
        # P(H|E) = P(E|H) * P(H) / P(E)
        # Assuming P(E) = P(E|H) * P(H) + P(E|¬H) * P(¬H)

        prior = self.prior_probability
        likelihood_true = evidence_likelihood
        likelihood_false = 1.0 - evidence_likelihood  # Simplified assumption

        # Calculate marginal likelihood
        marginal = (likelihood_true * prior) + (likelihood_false * (1 - prior))

        if marginal == 0:
            posterior = prior
        else:
            posterior = (likelihood_true * prior) / marginal

        # Apply evidence strength as weight
        weighted_posterior = (evidence_strength * posterior) + (
            (1 - evidence_strength) * prior
        )

        self.prior_probability = weighted_posterior
        return weighted_posterior

    def get_confidence_level(self) -> str:
        """Get confidence level description based on probability"""
        if self.prior_probability >= 0.9:
            return "very_high"
        elif self.prior_probability >= 0.7:
            return "high"
        elif self.prior_probability >= 0.5:
            return "medium"
        elif self.prior_probability >= 0.3:
            return "low"
        else:
            return "very_low"
