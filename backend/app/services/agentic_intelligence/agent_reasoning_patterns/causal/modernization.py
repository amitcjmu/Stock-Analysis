"""
Modernization Causal Pattern Module

This module implements causal reasoning patterns for modernization potential.
It identifies cause-and-effect relationships that enable or hinder modernization.
"""

import logging
from typing import Any, Dict, List

from ..base import BaseReasoningPattern, ReasoningEvidence, EvidenceType
from .relationships import CausalRelationship

logger = logging.getLogger(__name__)


class ModernizationCausalPattern(BaseReasoningPattern):
    """
    Causal reasoning pattern for modernization potential.
    Identifies cause-and-effect relationships that enable or hinder modernization.
    """

    def __init__(self):
        super().__init__(
            "modernization_causal",
            "Modernization Causal Analysis",
            "Identifies causal relationships affecting modernization potential",
        )
        self.causal_relationships = self._initialize_modernization_causality()

    def _initialize_modernization_causality(self) -> List[CausalRelationship]:
        """Initialize known causal relationships for modernization"""
        relationships = []

        # Modern Tech + Stateless Architecture → High Modernization Potential
        relationships.append(
            CausalRelationship(
                cause_conditions={
                    "technology_stack": [
                        "kubernetes",
                        "docker",
                        "microservices",
                        "spring boot",
                    ],
                    "asset_type": ["api", "service", "web application"],
                },
                effect_outcomes={
                    "modernization_score": {"operator": ">=", "value": 80}
                },
                relationship_strength=0.9,
                confidence_level=0.85,
                description="Modern technologies with stateless architecture enable easy modernization",
            )
        )

        # Legacy Monolith + Complex Dependencies → Low Modernization Potential
        relationships.append(
            CausalRelationship(
                cause_conditions={
                    "architecture_type": ["monolith", "legacy"],
                    "dependency_complexity": {"operator": ">=", "value": 8},
                },
                effect_outcomes={
                    "modernization_score": {"operator": "<=", "value": 30}
                },
                relationship_strength=0.8,
                confidence_level=0.8,
                description="Legacy monoliths with complex dependencies are difficult to modernize",
            )
        )

        # Cloud-Native Frameworks + Container Support → High Modernization Potential
        relationships.append(
            CausalRelationship(
                cause_conditions={
                    "technology_stack": [
                        ".net core",
                        "spring boot",
                        "nodejs",
                        "python",
                    ],
                    "deployment_model": ["containerized", "docker"],
                },
                effect_outcomes={
                    "modernization_score": {"operator": ">=", "value": 75}
                },
                relationship_strength=0.85,
                confidence_level=0.8,
                description="Cloud-native frameworks with container support are modernization-ready",
            )
        )

        return relationships

    def analyze_modernization_causality(
        self, asset_data: Dict[str, Any]
    ) -> List[ReasoningEvidence]:
        """
        Analyze causal relationships that affect modernization potential.

        Args:
            asset_data: Asset data to analyze

        Returns:
            List of evidence pieces from causal modernization analysis
        """
        evidence_pieces = []

        for relationship in self.causal_relationships:
            conditions_met, effect_strength = relationship.evaluate_causality(
                asset_data
            )

            if conditions_met:
                evidence = ReasoningEvidence(
                    evidence_type=EvidenceType.TECHNOLOGY_STACK,
                    field_name="causal_modernization_relationship",
                    field_value=relationship.description,
                    confidence=relationship.confidence_level * effect_strength,
                    reasoning=f"Modernization causal analysis: {relationship.description}",
                    supporting_patterns=[self.pattern_id],
                )
                evidence_pieces.append(evidence)

        return evidence_pieces
