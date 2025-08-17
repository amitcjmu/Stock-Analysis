"""
Risk Causal Pattern Module

This module implements causal reasoning patterns for risk assessment.
It identifies cause-and-effect relationships that create or amplify risks.
"""

import logging
from typing import Any, Dict, List

from ..base import BaseReasoningPattern, ReasoningEvidence, EvidenceType
from .relationships import CausalRelationship

logger = logging.getLogger(__name__)


class RiskCausalPattern(BaseReasoningPattern):
    """
    Causal reasoning pattern for risk assessment.
    Identifies cause-and-effect relationships that create or amplify risks.
    """

    def __init__(self):
        super().__init__(
            "risk_causal",
            "Risk Causal Analysis",
            "Identifies causal relationships that create or amplify risks",
        )
        self.causal_relationships = self._initialize_risk_causality()

    def _initialize_risk_causality(self) -> List[CausalRelationship]:
        """Initialize known causal relationships for risk factors"""
        relationships = []

        # Legacy Tech + Production → High Risk
        relationships.append(
            CausalRelationship(
                cause_conditions={
                    "technology_stack": ["java 8", "windows server 2012", "oracle 11g"],
                    "environment": "production",
                },
                effect_outcomes={"risk_level": "high"},
                relationship_strength=0.8,
                confidence_level=0.9,
                description="Legacy technologies in production create security and maintenance risks",
            )
        )

        # Single Point of Failure + Critical System → High Risk
        relationships.append(
            CausalRelationship(
                cause_conditions={
                    "name": ["single", "standalone", "solo"],
                    "business_value_score": {"operator": ">=", "value": 7},
                },
                effect_outcomes={"risk_level": "high"},
                relationship_strength=0.85,
                confidence_level=0.8,
                description="Single points of failure in critical systems pose availability risks",
            )
        )

        # Unsupported Platform + Internet Exposure → Critical Risk
        relationships.append(
            CausalRelationship(
                cause_conditions={
                    "technology_stack": [
                        "centos 6",
                        "ubuntu 14",
                        "windows server 2008",
                    ],
                    "network_exposure": ["public", "internet-facing"],
                },
                effect_outcomes={"risk_level": "critical"},
                relationship_strength=0.95,
                confidence_level=0.95,
                description="Unsupported platforms with internet exposure create critical security risks",
            )
        )

        return relationships

    def analyze_risk_causality(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """
        Analyze causal relationships that contribute to risk.

        Args:
            asset_data: Asset data to analyze

        Returns:
            List of evidence pieces from causal risk analysis
        """
        evidence_pieces = []

        for relationship in self.causal_relationships:
            conditions_met, effect_strength = relationship.evaluate_causality(
                asset_data
            )

            if conditions_met:
                evidence = ReasoningEvidence(
                    evidence_type=EvidenceType.TECHNOLOGY_STACK,
                    field_name="causal_risk_relationship",
                    field_value=relationship.description,
                    confidence=relationship.confidence_level * effect_strength,
                    reasoning=f"Risk causal analysis: {relationship.description}",
                    supporting_patterns=[self.pattern_id],
                )
                evidence_pieces.append(evidence)

        return evidence_pieces
