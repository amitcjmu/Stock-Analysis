"""
Adaptive Reasoning Engine Module

This module implements adaptive reasoning functionality that enables agents to
adapt reasoning based on feedback and validation results through continuous learning.
"""

import logging
import uuid
from typing import Any, Dict, List

from ..base import ReasoningEvidence, EvidenceType
from ..exceptions import MemoryIntegrationError
from .discovery_engine import PatternDiscoveryEngine

logger = logging.getLogger(__name__)


class AdaptiveReasoningEngine:
    """
    Engine that adapts reasoning based on feedback and validation results.
    Implements continuous learning and pattern refinement.
    """

    def __init__(
        self, memory_manager, client_account_id: uuid.UUID, engagement_id: uuid.UUID
    ):
        self.memory_manager = memory_manager
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.logger = logger
        self.pattern_discovery = PatternDiscoveryEngine(
            memory_manager, client_account_id, engagement_id
        )

    async def adapt_from_feedback(
        self,
        reasoning_result: Dict[str, Any],
        user_feedback: Dict[str, Any],
        agent_name: str,
    ) -> Dict[str, Any]:
        """
        Adapt reasoning patterns based on user feedback.

        Args:
            reasoning_result: Original reasoning result
            user_feedback: User feedback on the reasoning
            agent_name: Name of the agent that provided the reasoning

        Returns:
            Updated reasoning patterns and adaptation metrics
        """
        try:
            adaptation_results = {
                "patterns_updated": [],
                "patterns_created": [],
                "confidence_adjustments": [],
                "learning_insights": [],
            }

            # Analyze feedback for pattern updates
            feedback_score = user_feedback.get("accuracy_score", 0.5)  # 0-1 scale
            feedback_comments = user_feedback.get("comments", "")

            # Adjust pattern confidence based on feedback
            applied_patterns = reasoning_result.get("applied_patterns", [])
            for pattern_id in applied_patterns:
                confidence_adjustment = self._calculate_confidence_adjustment(
                    feedback_score, feedback_comments
                )

                if abs(confidence_adjustment) > 0.1:  # Significant adjustment
                    await self._update_pattern_confidence(
                        pattern_id, confidence_adjustment
                    )
                    adaptation_results["confidence_adjustments"].append(
                        {
                            "pattern_id": pattern_id,
                            "adjustment": confidence_adjustment,
                            "reason": f"User feedback score: {feedback_score}",
                        }
                    )

            # Create new patterns from feedback insights
            if feedback_score < 0.6:  # Poor accuracy suggests missing patterns
                new_patterns = await self._discover_patterns_from_feedback(
                    reasoning_result, user_feedback, agent_name
                )
                adaptation_results["patterns_created"].extend(new_patterns)

            # Generate learning insights
            insights = self._generate_learning_insights(
                reasoning_result, user_feedback, feedback_score
            )
            adaptation_results["learning_insights"].extend(insights)

            return adaptation_results

        except Exception as e:
            self.logger.error(f"Error adapting from feedback: {e}")
            raise MemoryIntegrationError(
                f"Failed to adapt from user feedback: {e}",
                memory_operation="feedback_adaptation",
            )

    def _calculate_confidence_adjustment(
        self, feedback_score: float, feedback_comments: str
    ) -> float:
        """Calculate confidence adjustment based on feedback"""
        # Base adjustment on feedback score
        base_adjustment = (feedback_score - 0.5) * 0.4  # Scale to -0.2 to +0.2

        # Analyze comments for additional insights
        positive_keywords = ["accurate", "correct", "good", "right"]
        negative_keywords = ["wrong", "incorrect", "bad", "inaccurate"]

        comment_lower = feedback_comments.lower()
        positive_mentions = sum(
            1 for keyword in positive_keywords if keyword in comment_lower
        )
        negative_mentions = sum(
            1 for keyword in negative_keywords if keyword in comment_lower
        )

        comment_adjustment = (positive_mentions - negative_mentions) * 0.05

        return base_adjustment + comment_adjustment

    async def _update_pattern_confidence(
        self, pattern_id: str, adjustment: float
    ) -> None:
        """Update pattern confidence in memory system"""
        try:
            # This would integrate with the memory system to update pattern confidence
            # For now, log the update
            self.logger.info(
                f"Updating pattern {pattern_id} confidence by {adjustment}"
            )

            # In a real implementation, this would:
            # 1. Retrieve the pattern from memory
            # 2. Update its confidence score
            # 3. Store the updated pattern back to memory

        except Exception as e:
            self.logger.error(f"Failed to update pattern confidence: {e}")

    async def _discover_patterns_from_feedback(
        self,
        reasoning_result: Dict[str, Any],
        user_feedback: Dict[str, Any],
        agent_name: str,
    ) -> List[Dict[str, Any]]:
        """Discover new patterns based on feedback insights"""
        new_patterns = []

        try:
            # Extract asset data from reasoning result
            asset_data = user_feedback.get("asset_data", {})
            if not asset_data:
                return new_patterns

            # Create evidence from feedback
            evidence_pieces = []
            if user_feedback.get("correct_business_value"):
                evidence_pieces.append(
                    ReasoningEvidence(
                        evidence_type=EvidenceType.BUSINESS_CRITICALITY,
                        field_name="user_validation",
                        field_value=user_feedback["correct_business_value"],
                        confidence=0.9,
                        reasoning="User-validated business value",
                        supporting_patterns=[],
                    )
                )

            # Discover patterns based on corrected assessment
            dimension = reasoning_result.get("dimension")
            if dimension == "business_value":
                patterns = (
                    await self.pattern_discovery.discover_business_value_patterns(
                        asset_data, evidence_pieces, agent_name
                    )
                )
                new_patterns.extend(patterns)
            elif dimension == "risk_assessment":
                patterns = await self.pattern_discovery.discover_risk_patterns(
                    asset_data, evidence_pieces, agent_name
                )
                new_patterns.extend(patterns)
            elif dimension == "modernization_potential":
                patterns = await self.pattern_discovery.discover_modernization_patterns(
                    asset_data, evidence_pieces, agent_name
                )
                new_patterns.extend(patterns)

        except Exception as e:
            self.logger.error(f"Error discovering patterns from feedback: {e}")

        return new_patterns

    def _generate_learning_insights(
        self,
        reasoning_result: Dict[str, Any],
        user_feedback: Dict[str, Any],
        feedback_score: float,
    ) -> List[str]:
        """Generate insights for future learning"""
        insights = []

        if feedback_score < 0.4:
            insights.append(
                "Low feedback score suggests need for better pattern matching or "
                "more comprehensive evidence analysis"
            )

        if len(reasoning_result.get("evidence_pieces", [])) < 3:
            insights.append(
                "Limited evidence pieces may have contributed to poor assessment. "
                "Consider expanding evidence collection strategies"
            )

        applied_patterns = reasoning_result.get("applied_patterns", [])
        if not applied_patterns:
            insights.append(
                "No patterns were applied in reasoning. This suggests either missing "
                "patterns in the knowledge base or poor pattern matching"
            )

        confidence = reasoning_result.get("confidence", 0.5)
        if confidence < 0.6 and feedback_score > 0.8:
            insights.append(
                "Agent had low confidence but user validation was high. "
                "Consider adjusting confidence calculation methods"
            )

        return insights
