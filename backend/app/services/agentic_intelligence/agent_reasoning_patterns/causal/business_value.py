"""
Business Value Causal Pattern Module

This module implements causal reasoning patterns for business value analysis.
It identifies cause-and-effect relationships that drive business value.
"""

import logging
from typing import Any, Dict, List

from ..base import BaseReasoningPattern, ReasoningEvidence, EvidenceType
from .relationships import CausalRelationship

logger = logging.getLogger(__name__)


class BusinessValueCausalPattern(BaseReasoningPattern):
    """
    Causal reasoning pattern for business value analysis.
    Identifies cause-and-effect relationships that drive business value.
    """

    def __init__(self):
        super().__init__(
            "business_value_causal",
            "Business Value Causal Analysis",
            "Identifies causal relationships that drive business value",
        )
        self.causal_relationships = self._initialize_business_value_causality()

    def _initialize_business_value_causality(self) -> List[CausalRelationship]:
        """Initialize known causal relationships for business value"""
        relationships = []

        # High CPU + Production Environment → High Business Value
        # Define key causal relationships for business value
        relationship_configs = [
            (
                {
                    "cpu_utilization_percent": {"operator": ">=", "value": 70},
                    "environment": "production",
                },
                {"business_value_score": {"operator": ">=", "value": 8}},
                0.8,
                0.9,
                "High CPU utilization in production indicates critical business usage",
            ),
            (
                {
                    "name": ["finance", "billing", "payment"],
                    "technology_stack": ["oracle", "sap"],
                },
                {"business_value_score": {"operator": ">=", "value": 9}},
                0.9,
                0.85,
                "Financial systems with enterprise technology are business-critical",
            ),
            (
                {
                    "name": ["customer", "client", "portal"],
                    "environment": ["production", "prod"],
                },
                {"business_value_score": {"operator": ">=", "value": 7}},
                0.7,
                0.8,
                "Customer-facing production systems have high business impact",
            ),
        ]

        for causes, effects, strength, confidence, desc in relationship_configs:
            relationships.append(
                CausalRelationship(causes, effects, strength, confidence, desc)
            )

        return relationships

    def analyze_business_value_causality(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """
        Analyze causal relationships that contribute to business value.

        Args:
            asset_data: Asset data to analyze

        Returns:
            List of evidence pieces from causal analysis
        """
        evidence_pieces = []

        for relationship in self.causal_relationships:
            conditions_met, effect_strength = relationship.evaluate_causality(
                asset_data
            )

            if conditions_met:
                evidence = ReasoningEvidence(
                    evidence_type=EvidenceType.BUSINESS_CRITICALITY,
                    field_name="causal_relationship",
                    field_value=relationship.description,
                    confidence=relationship.confidence_level * effect_strength,
                    reasoning=f"Causal analysis: {relationship.description}",
                    supporting_patterns=[self.pattern_id],
                )
                evidence_pieces.append(evidence)

        return evidence_pieces
