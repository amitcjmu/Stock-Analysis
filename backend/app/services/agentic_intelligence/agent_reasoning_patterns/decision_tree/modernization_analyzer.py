"""
Modernization Analyzer Module

This module contains the modernization analysis logic extracted from
the main AgentReasoningEngine for better modularity.
"""

import logging
import uuid
from typing import Any, Dict, List

from ..base import AgentReasoning, ReasoningDimension, ReasoningEvidence, EvidenceType
from ..exceptions import ReasoningEngineError
from .evidence_analyzers import EvidenceAnalyzers
from .utilities import ReasoningUtilities

logger = logging.getLogger(__name__)


class ModernizationAnalyzer:
    """
    Analyzer for modernization potential assessment using agent reasoning patterns.
    """

    def __init__(
        self,
        memory_manager,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        modernization_pattern,
        modernization_causal,
        lifecycle_pattern,
        pattern_discovery,
    ):
        self.memory_manager = memory_manager
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.modernization_pattern = modernization_pattern
        self.modernization_causal = modernization_causal
        self.lifecycle_pattern = lifecycle_pattern
        self.pattern_discovery = pattern_discovery
        self.evidence_analyzers = EvidenceAnalyzers()
        self.logger = logger

    async def analyze_modernization_potential(
        self, asset_data: Dict[str, Any], agent_name: str
    ) -> AgentReasoning:
        """Analyze modernization opportunities using agent reasoning"""
        try:
            evidence_pieces = []
            discovered_patterns = []
            applied_patterns = []

            # Search for modernization patterns
            existing_patterns = await self._search_memory_patterns(
                "modernization cloud migration containerization microservices",
                "MODERNIZATION_OPPORTUNITY",
            )

            # Analyze modernization evidence using multiple approaches
            evidence_pieces.extend(
                await self.evidence_analyzers.analyze_architecture_evidence(asset_data)
            )
            evidence_pieces.extend(
                await self.evidence_analyzers.analyze_cloud_readiness_evidence(
                    asset_data
                )
            )
            evidence_pieces.extend(
                await self.evidence_analyzers.analyze_technology_modernization_evidence(
                    asset_data
                )
            )

            # Apply causal modernization reasoning
            causal_evidence = self.modernization_causal.analyze_modernization_causality(
                asset_data
            )
            evidence_pieces.extend(causal_evidence)

            # Apply temporal reasoning for modernization
            lifecycle_evidence = self.lifecycle_pattern.analyze_asset_lifecycle(
                asset_data
            )
            evidence_pieces.extend(lifecycle_evidence)

            # Apply modernization patterns
            for pattern_result in existing_patterns:
                if pattern_result.tier == "semantic":
                    pattern_data = pattern_result.content
                    pattern_logic = pattern_data.get("pattern_data", {})

                    if self._pattern_matches_asset(pattern_logic, asset_data):
                        applied_patterns.append(pattern_data["id"])

                        evidence = ReasoningEvidence(
                            evidence_type=EvidenceType.TECHNOLOGY_STACK,
                            field_name="modernization_pattern_match",
                            field_value=pattern_data["name"],
                            confidence=pattern_data["confidence"],
                            reasoning=f"Asset matches modernization pattern: {pattern_data['description']}",
                            supporting_patterns=[pattern_data["id"]],
                        )
                        evidence_pieces.append(evidence)

            # Discover new modernization patterns
            new_patterns = await self.pattern_discovery.discover_modernization_patterns(
                asset_data, evidence_pieces, agent_name
            )
            discovered_patterns.extend(new_patterns)

            # Calculate modernization potential using logical reasoning pattern
            modernization_score, confidence, reasoning_parts = (
                self.modernization_pattern.evaluate_modernization_potential(
                    asset_data, evidence_pieces
                )
            )

            recommendations = ReasoningUtilities.generate_modernization_recommendations(
                asset_data, evidence_pieces, modernization_score
            )

            reasoning_summary = (
                f"Modernization potential: {modernization_score}/100. "
                + "; ".join(reasoning_parts)
            )

            return AgentReasoning(
                dimension=ReasoningDimension.MODERNIZATION_POTENTIAL,
                score=modernization_score,
                confidence=confidence,
                reasoning_summary=reasoning_summary,
                evidence_pieces=evidence_pieces,
                discovered_patterns=discovered_patterns,
                applied_patterns=applied_patterns,
                recommendations=recommendations,
            )

        except Exception as e:
            self.logger.error(f"Error in modernization analysis: {e}")
            raise ReasoningEngineError(
                f"Failed to analyze modernization potential: {e}",
                engine_state="modernization_analysis",
            )

    async def _search_memory_patterns(self, query_text: str, pattern_type: str) -> List:
        """Search for patterns in agent memory that might apply to current analysis"""
        try:
            search_results = await self.memory_manager.memory_search(
                client_account_id=self.client_account_id,
                engagement_id=self.engagement_id,
                query_text=query_text,
                top_k=5,
                tier="semantic",
            )

            # Filter results by pattern type
            relevant_patterns = []
            for result in search_results:
                if (
                    result.content.get("type") == pattern_type
                    or pattern_type.lower() in result.content.get("name", "").lower()
                ):
                    relevant_patterns.append(result)

            return relevant_patterns

        except Exception as e:
            self.logger.warning(f"Memory search failed: {e}")
            return []

    def _pattern_matches_asset(
        self, pattern_logic: Dict[str, Any], asset_data: Dict[str, Any]
    ) -> bool:
        """
        Check if a discovered pattern applies to the current asset.
        This implements basic pattern matching logic.
        """
        try:
            conditions = pattern_logic.get("conditions", [])

            for condition in conditions:
                field = condition.get("field")
                operator = condition.get("operator", "equals")
                value = condition.get("value")

                asset_value = asset_data.get(field)

                if operator == "contains" and isinstance(asset_value, str):
                    if value.lower() not in asset_value.lower():
                        return False
                elif operator == "equals":
                    if str(asset_value).lower() != str(value).lower():
                        return False
                elif operator == "greater_than" and isinstance(
                    asset_value, (int, float)
                ):
                    if asset_value <= value:
                        return False

            return True  # All conditions matched

        except Exception as e:
            self.logger.warning(f"Pattern matching error: {e}")
            return False
