"""
Causal Chain Analyzer Module

This module analyzes chains of causal relationships to understand complex dependencies
and multi-step reasoning paths.
"""

import logging
from typing import Any, Dict, List

from ..base import BaseReasoningPattern, ReasoningEvidence
from ..exceptions import PatternMatchingError

logger = logging.getLogger(__name__)


class CausalChainAnalyzer:
    """
    Analyzes chains of causal relationships to understand complex dependencies
    and multi-step reasoning paths.
    """

    def __init__(self):
        self.logger = logger

    def analyze_causal_chain(
        self,
        asset_data: Dict[str, Any],
        causal_patterns: List[BaseReasoningPattern],
    ) -> Dict[str, Any]:
        """
        Analyze complex causal chains across multiple reasoning patterns.

        Args:
            asset_data: Asset data to analyze
            causal_patterns: List of causal reasoning patterns to apply

        Returns:
            Dictionary containing causal chain analysis results
        """
        try:
            chain_analysis = {
                "primary_causes": [],
                "secondary_effects": [],
                "causal_strength": 0.0,
                "confidence": 0.0,
                "reasoning_chain": [],
            }

            all_evidence = []
            for pattern in causal_patterns:
                if hasattr(pattern, "analyze_business_value_causality"):
                    evidence = pattern.analyze_business_value_causality(asset_data)
                elif hasattr(pattern, "analyze_risk_causality"):
                    evidence = pattern.analyze_risk_causality(asset_data)
                elif hasattr(pattern, "analyze_modernization_causality"):
                    evidence = pattern.analyze_modernization_causality(asset_data)
                else:
                    continue

                all_evidence.extend(evidence)

            # Analyze causal chains
            chain_analysis["primary_causes"] = self._identify_primary_causes(
                all_evidence
            )
            chain_analysis["secondary_effects"] = self._identify_secondary_effects(
                all_evidence
            )
            chain_analysis["causal_strength"] = self._calculate_chain_strength(
                all_evidence
            )
            chain_analysis["confidence"] = self._calculate_chain_confidence(
                all_evidence
            )
            chain_analysis["reasoning_chain"] = self._build_reasoning_chain(
                all_evidence
            )

            return chain_analysis

        except Exception as e:
            self.logger.error(f"Causal chain analysis error: {e}")
            raise PatternMatchingError(f"Failed to analyze causal chain: {e}")

    def _identify_primary_causes(
        self, evidence_pieces: List[ReasoningEvidence]
    ) -> List[str]:
        """Identify primary causal factors from evidence"""
        causes = []
        for evidence in evidence_pieces:
            if evidence.confidence >= 0.7:
                causes.append(evidence.field_value)
        return causes[:5]  # Limit to top 5 causes

    def _identify_secondary_effects(
        self, evidence_pieces: List[ReasoningEvidence]
    ) -> List[str]:
        """Identify secondary effects from causal analysis"""
        effects = []
        for evidence in evidence_pieces:
            if "effect" in evidence.reasoning.lower():
                effects.append(evidence.reasoning)
        return effects

    def _calculate_chain_strength(
        self, evidence_pieces: List[ReasoningEvidence]
    ) -> float:
        """Calculate overall strength of the causal chain"""
        if not evidence_pieces:
            return 0.0

        strengths = [evidence.confidence for evidence in evidence_pieces]
        # Use geometric mean for chain strength (weakest link effect)
        product = 1.0
        for strength in strengths:
            product *= strength
        return product ** (1.0 / len(strengths))

    def _calculate_chain_confidence(
        self, evidence_pieces: List[ReasoningEvidence]
    ) -> float:
        """Calculate confidence in the causal chain analysis"""
        if not evidence_pieces:
            return 0.0

        confidences = [evidence.confidence for evidence in evidence_pieces]
        return sum(confidences) / len(confidences)

    def _build_reasoning_chain(
        self, evidence_pieces: List[ReasoningEvidence]
    ) -> List[str]:
        """Build a logical reasoning chain from evidence"""
        reasoning_steps = []
        for evidence in sorted(
            evidence_pieces, key=lambda x: x.confidence, reverse=True
        ):
            reasoning_steps.append(
                f"{evidence.reasoning} (confidence: {evidence.confidence:.2f})"
            )
        return reasoning_steps[:10]  # Limit to top 10 reasoning steps
