"""
Business Value Reasoning Pattern Module

This module implements specialized reasoning pattern for business value analysis,
evaluating asset business criticality and impact.
"""

import logging
from typing import Any, Dict, List

from ..base import BaseReasoningPattern

logger = logging.getLogger(__name__)


class BusinessValueReasoningPattern(BaseReasoningPattern):
    """
    Specialized reasoning pattern for business value analysis.
    Implements logic for evaluating asset business criticality and impact.
    """

    def __init__(self):
        super().__init__(
            "business_value_reasoning",
            "Business Value Analysis Pattern",
            "Evaluates asset business value based on usage, environment, and technology indicators",
        )

    def evaluate_business_value(
        self, asset_data: Dict[str, Any], evidence_pieces: List
    ) -> tuple[int, float, List[str]]:
        """
        Evaluate business value score with detailed reasoning.

        Args:
            asset_data: Asset data to evaluate
            evidence_pieces: Supporting evidence

        Returns:
            Tuple of (score, confidence, reasoning_parts)
        """
        base_score = 5  # Default medium value
        confidence_factors = []
        reasoning_parts = []

        # Environment analysis
        environment = asset_data.get("environment", "").lower()
        if environment in ["production", "prod"]:
            base_score += 2
            confidence_factors.append(0.9)
            reasoning_parts.append("Production environment (+2 points)")

        # Performance indicators
        cpu_util = asset_data.get("cpu_utilization_percent")
        if cpu_util is not None and cpu_util >= 70:
            base_score += 2
            confidence_factors.append(0.8)
            reasoning_parts.append(f"High CPU utilization ({cpu_util}%) (+2 points)")

        # Technology value indicators
        tech_stack = asset_data.get("technology_stack", "").lower()
        high_value_techs = ["oracle", "sap", "mainframe", "peoplesoft"]
        for tech in high_value_techs:
            if tech in tech_stack:
                base_score += 1
                confidence_factors.append(0.7)
                reasoning_parts.append(f"Enterprise technology {tech} (+1 point)")

        # Business criticality indicators
        name = asset_data.get("name", "").lower()
        critical_keywords = ["finance", "billing", "payment", "customer", "core"]
        for keyword in critical_keywords:
            if keyword in name:
                base_score += 1
                confidence_factors.append(0.6)
                reasoning_parts.append(
                    f"Business-critical naming '{keyword}' (+1 point)"
                )

        # Ensure score is in valid range
        business_value_score = max(1, min(10, base_score))

        # Calculate overall confidence
        overall_confidence = (
            sum(confidence_factors) / len(confidence_factors)
            if confidence_factors
            else 0.5
        )

        return business_value_score, overall_confidence, reasoning_parts
