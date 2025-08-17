"""
Modernization Reasoning Pattern Module

This module implements specialized reasoning pattern for modernization potential analysis,
evaluating cloud readiness and modernization opportunities.
"""

import logging
from typing import Any, Dict, List

from ..base import BaseReasoningPattern

logger = logging.getLogger(__name__)


class ModernizationReasoningPattern(BaseReasoningPattern):
    """
    Specialized reasoning pattern for modernization potential analysis.
    Implements logic for evaluating cloud readiness and modernization opportunities.
    """

    def __init__(self):
        super().__init__(
            "modernization_reasoning",
            "Modernization Potential Analysis Pattern",
            "Evaluates asset modernization opportunities and cloud readiness",
        )

    def evaluate_modernization_potential(
        self, asset_data: Dict[str, Any], evidence_pieces: List
    ) -> tuple[int, float, List[str]]:
        """
        Evaluate modernization potential score with detailed reasoning.

        Args:
            asset_data: Asset data to evaluate
            evidence_pieces: Supporting evidence

        Returns:
            Tuple of (modernization_score, confidence, reasoning_parts)
        """
        base_score = 50  # Default medium modernization potential
        confidence_factors = []
        reasoning_parts = []

        tech_stack = asset_data.get("technology_stack", "").lower()
        asset_type = asset_data.get("asset_type", "").lower()

        # Cloud-native technology indicators
        modern_techs = {
            "kubernetes": 25,
            "docker": 20,
            "microservices": 25,
            "spring boot": 15,
            ".net core": 15,
            "nodejs": 10,
        }

        for tech, score_boost in modern_techs.items():
            if tech in tech_stack:
                base_score += score_boost
                confidence_factors.append(0.8)
                reasoning_parts.append(
                    f"Modern technology {tech} (+{score_boost} points)"
                )

        # Architecture patterns
        if "microservices" in tech_stack or "api" in asset_type:
            base_score += 15
            confidence_factors.append(0.7)
            reasoning_parts.append("Microservices/API architecture (+15 points)")

        if "stateless" in asset_data.get("description", "").lower():
            base_score += 10
            confidence_factors.append(0.6)
            reasoning_parts.append("Stateless application design (+10 points)")

        # Database modernization potential
        if "database" in asset_type:
            modern_dbs = ["postgresql", "mysql", "mongodb"]
            if any(db in tech_stack for db in modern_dbs):
                base_score += 10
                confidence_factors.append(0.7)
                reasoning_parts.append("Modern database technology (+10 points)")

        # Legacy penalties
        legacy_techs = ["java 8", "windows server 2012", "oracle 11g"]
        for legacy_tech in legacy_techs:
            if legacy_tech in tech_stack:
                base_score -= 15
                confidence_factors.append(0.8)
                reasoning_parts.append(f"Legacy technology {legacy_tech} (-15 points)")

        modernization_score = max(0, min(100, base_score))
        overall_confidence = (
            sum(confidence_factors) / len(confidence_factors)
            if confidence_factors
            else 0.5
        )

        return modernization_score, overall_confidence, reasoning_parts
