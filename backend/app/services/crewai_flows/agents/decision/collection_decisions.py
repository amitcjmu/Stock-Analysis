"""
Collection Flow Phase Transition Decisions

Contains decision logic specific to collection flow phases.
"""

import logging
from typing import Any, Dict

from .base import AgentDecision, PhaseAction

logger = logging.getLogger(__name__)


class CollectionDecisionLogic:
    """Collection-specific decision logic for phase transitions"""

    @staticmethod
    def make_collection_decision(
        current_phase: str, analysis: Dict[str, Any]
    ) -> AgentDecision:
        """Collection-specific decision logic"""
        from app.services.crewai_flows.agents.decision.utils import DecisionUtils

        if current_phase == "platform_detection":
            return CollectionDecisionLogic._decide_after_platform_detection(analysis)
        elif current_phase == "automated_collection":
            return CollectionDecisionLogic._decide_after_automated_collection(analysis)
        elif current_phase == "gap_analysis":
            return CollectionDecisionLogic._decide_after_gap_analysis(analysis)
        elif current_phase == "questionnaire_generation":
            return CollectionDecisionLogic._decide_after_questionnaire_generation(
                analysis
            )
        elif current_phase == "manual_collection":
            return CollectionDecisionLogic._decide_after_manual_collection(analysis)
        elif current_phase == "synthesis":
            return CollectionDecisionLogic._decide_after_synthesis(analysis)
        else:
            # Default progression using flow registry
            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase=DecisionUtils.get_next_phase(current_phase, "collection"),
                confidence=0.8,
                reasoning=f"Phase {current_phase} completed successfully in collection flow",
                metadata=analysis,
            )

    @staticmethod
    def _decide_after_platform_detection(analysis: Dict[str, Any]) -> AgentDecision:
        """Decision logic after platform detection phase"""
        platform_results = analysis.get("platform_detection_results", {})
        platforms_detected = platform_results.get("platforms_detected", 0)
        detection_confidence = platform_results.get("detection_confidence", 0)

        if platforms_detected == 0:
            return AgentDecision(
                action=PhaseAction.FAIL,
                next_phase="",
                confidence=0.9,
                reasoning="No platforms detected for data collection. Review environment configuration.",
                metadata={
                    "platforms_detected": platforms_detected,
                    "user_action": "check_credentials",
                },
            )

        if detection_confidence < 0.7:
            return AgentDecision(
                action=PhaseAction.PAUSE,
                next_phase="platform_detection",
                confidence=0.8,
                reasoning="Platform detection confidence low. Human review recommended.",
                metadata={
                    "detection_confidence": detection_confidence,
                    "user_action": "verify_platforms",
                },
            )

        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="automated_collection",
            confidence=0.9,
            reasoning=f"Platforms successfully detected ({platforms_detected}). Proceeding to automated collection.",
            metadata=platform_results,
        )

    @staticmethod
    def _decide_after_automated_collection(analysis: Dict[str, Any]) -> AgentDecision:
        """Decision logic after automated collection phase"""
        collection_metrics = analysis.get("collection_metrics", {})
        data_collected = collection_metrics.get("data_collected", False)

        if not data_collected:
            return AgentDecision(
                action=PhaseAction.RETRY,
                next_phase="automated_collection",
                confidence=0.8,
                reasoning="No data collected during automated phase. Retrying collection.",
                metadata={"retry_reason": "no_data_collected"},
            )

        # Always proceed to gap analysis to identify what's missing
        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="gap_analysis",
            confidence=0.9,
            reasoning="Automated collection completed. Proceeding to gap analysis to identify missing data.",
            metadata=collection_metrics,
        )

    @staticmethod
    def _decide_after_gap_analysis(analysis: Dict[str, Any]) -> AgentDecision:
        """Decision logic after gap analysis phase"""
        gap_results = analysis.get("gap_analysis_results", {})
        gaps_identified = gap_results.get("gaps_identified", [])
        sixr_impact = gap_results.get("sixr_impact_high", False)

        if not gaps_identified:
            # No gaps - skip questionnaire generation and manual collection
            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase="synthesis",
                confidence=0.95,
                reasoning="No data gaps identified. Skipping questionnaire phases and proceeding to synthesis.",
                metadata={"gaps_count": 0, "skip_reason": "no_gaps"},
            )

        if sixr_impact:
            # High SIXR impact gaps require questionnaires
            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase="questionnaire_generation",
                confidence=0.9,
                reasoning="Critical gaps affecting SIXR strategy identified. Generating questionnaires for resolution.",
                metadata={"gaps_count": len(gaps_identified), "sixr_critical": True},
            )

        # Standard gaps - proceed to questionnaire generation
        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="questionnaire_generation",
            confidence=0.85,
            reasoning=f"Data gaps identified ({len(gaps_identified)}). Generating questionnaires for resolution.",
            metadata=gap_results,
        )

    @staticmethod
    def _decide_after_questionnaire_generation(
        analysis: Dict[str, Any],
    ) -> AgentDecision:
        """Decision logic after questionnaire generation phase"""
        questionnaire_quality = analysis.get("questionnaire_quality", {})
        questionnaires_generated = questionnaire_quality.get("questionnaires_count", 0)
        generation_confidence = questionnaire_quality.get("confidence", 0)

        if questionnaires_generated == 0:
            return AgentDecision(
                action=PhaseAction.FAIL,
                next_phase="",
                confidence=0.9,
                reasoning="No questionnaires generated despite identified gaps. Check gap analysis results.",
                metadata={"questionnaires_count": 0, "user_action": "review_gaps"},
            )

        if generation_confidence < 0.6:
            return AgentDecision(
                action=PhaseAction.PAUSE,
                next_phase="questionnaire_generation",
                confidence=0.8,
                reasoning="Questionnaire generation confidence low. Human review recommended.",
                metadata={
                    "generation_confidence": generation_confidence,
                    "user_action": "review_questionnaires",
                },
            )

        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="manual_collection",
            confidence=0.9,
            reasoning=(
                f"Questionnaires successfully generated ({questionnaires_generated}). "
                "Proceeding to manual collection."
            ),
            metadata=questionnaire_quality,
        )

    @staticmethod
    def _decide_after_manual_collection(analysis: Dict[str, Any]) -> AgentDecision:
        """Decision logic after manual collection phase"""
        manual_results = analysis.get("manual_collection_results", {})
        responses_received = manual_results.get("responses_received", 0)
        response_quality = manual_results.get("response_quality", 0)

        if responses_received == 0:
            return AgentDecision(
                action=PhaseAction.PAUSE,
                next_phase="manual_collection",
                confidence=0.85,
                reasoning="No responses received yet. Waiting for human input on questionnaires.",
                metadata={"user_action": "complete_questionnaires"},
            )

        if response_quality < 0.7:
            return AgentDecision(
                action=PhaseAction.PAUSE,
                next_phase="manual_collection",
                confidence=0.8,
                reasoning="Response quality insufficient. Additional clarification needed.",
                metadata={
                    "response_quality": response_quality,
                    "user_action": "improve_responses",
                },
            )

        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="synthesis",
            confidence=0.9,
            reasoning=(
                f"Manual collection completed successfully ({responses_received} responses). "
                "Proceeding to synthesis."
            ),
            metadata=manual_results,
        )

    @staticmethod
    def _decide_after_synthesis(analysis: Dict[str, Any]) -> AgentDecision:
        """Decision logic after synthesis phase"""
        synthesis_results = analysis.get("synthesis_results", {})
        synthesis_quality = synthesis_results.get("quality_score", 0)
        sixr_readiness = synthesis_results.get("sixr_readiness", 0)

        if synthesis_quality < 0.8:
            return AgentDecision(
                action=PhaseAction.RETRY,
                next_phase="synthesis",
                confidence=0.8,
                reasoning="Synthesis quality below threshold. Retrying data synthesis.",
                metadata={
                    "synthesis_quality": synthesis_quality,
                    "retry_reason": "quality_low",
                },
            )

        if sixr_readiness < 0.75:
            return AgentDecision(
                action=PhaseAction.PAUSE,
                next_phase="synthesis",
                confidence=0.85,
                reasoning="SIXR readiness below threshold. Additional data collection may be needed.",
                metadata={
                    "sixr_readiness": sixr_readiness,
                    "user_action": "review_sixr_requirements",
                },
            )

        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="completed",
            confidence=0.95,
            reasoning="Collection flow completed successfully. Data synthesis meets quality standards.",
            metadata=synthesis_results,
        )
