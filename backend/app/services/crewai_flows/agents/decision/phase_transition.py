"""
Phase Transition Decision Agent

Agent responsible for making intelligent decisions about phase transitions
based on data quality, business context, and flow objectives.
"""

import logging
from typing import Any, Dict

from .base import AgentDecision, BaseDecisionAgent, PhaseAction
from .collection_analysis import CollectionAnalysis
from .collection_decisions import CollectionDecisionLogic
from .discovery_analysis import DiscoveryAnalysis
from .discovery_decisions import DiscoveryDecisionLogic

logger = logging.getLogger(__name__)


class PhaseTransitionAgent(BaseDecisionAgent):
    """Agent that decides phase transitions based on data analysis and business context"""

    # Declare flow_type as a proper field for Pydantic v2 compatibility
    flow_type: str = "discovery"
    flow_registry: Any = None

    def __init__(self, flow_type: str = None, flow_registry=None, **kwargs):
        # Dynamically determine backstory based on flow_type if provided
        if flow_type:
            backstory = f"""You are an expert in workflow optimization with deep understanding of:
            - Data quality assessment and validation
            - Business process optimization
            - Risk management and decision theory
            - {flow_type.title()} flow best practices

            You make intelligent decisions about when to proceed, pause for human input,
            or skip phases based on comprehensive analysis of the current situation."""
        else:
            # Generic backstory when flow type is determined at runtime
            backstory = """You are an expert in workflow optimization with deep understanding of:
            - Data quality assessment and validation
            - Business process optimization
            - Risk management and decision theory
            - Multi-flow orchestration best practices

            You make intelligent decisions about when to proceed, pause for human input,
            or skip phases based on comprehensive analysis of the current situation."""

        super().__init__(
            role="Flow Orchestration Strategist",
            goal="Determine optimal phase transitions based on data quality, business context, and flow objectives",
            backstory=backstory,
            flow_type=flow_type
            or "discovery",  # Default to discovery for backward compatibility
            flow_registry=flow_registry,
            **kwargs,
        )

    async def analyze_phase_transition(
        self, current_phase: str, results: Any, state: Any, flow_type: str = None
    ) -> AgentDecision:
        """Analyze and decide on phase transition"""
        effective_flow_type = flow_type or self.flow_type
        logger.info(
            f"🤖 Analyzing {effective_flow_type} phase transition from: {current_phase}"
        )

        # Analyze current state using flow-type aware methods
        analysis = self._analyze_current_state(
            current_phase, results, state, effective_flow_type
        )

        # Make decision based on analysis
        decision = self._make_transition_decision(
            current_phase, analysis, effective_flow_type
        )

        logger.info(
            f"📊 Decision: {decision.action.value} -> {decision.next_phase} (confidence: {decision.confidence})"
        )

        return decision

    def _analyze_current_state(
        self, phase: str, results: Any, state: Any, flow_type: str
    ) -> Dict[str, Any]:
        """Comprehensive state analysis with flow-type awareness"""
        from app.services.crewai_flows.agents.decision.utils import DecisionUtils

        analysis = {
            "phase": phase,
            "flow_type": flow_type,
            "state": state,  # Include state for downstream decision helpers
            "has_errors": DecisionUtils.check_for_errors(state),
            "data_quality": DecisionUtils.assess_data_quality(state),
            "completeness": DecisionUtils.assess_completeness(phase, state),
            "complexity": DecisionUtils.assess_complexity(state),
            "risk_factors": DecisionUtils.identify_risk_factors(state),
        }

        # Flow-type specific analysis using modular components
        if flow_type == "discovery":
            discovery_analysis = DiscoveryAnalysis.analyze_discovery_phase_results(
                phase, results, state
            )
            # Map discovery analysis results to expected keys
            if phase == "data_import":
                analysis["import_metrics"] = discovery_analysis
            elif phase == "field_mapping":
                analysis["mapping_quality"] = discovery_analysis
            elif phase == "data_cleansing":
                analysis["cleansing_impact"] = discovery_analysis
            elif phase == "asset_creation":
                analysis["asset_creation_results"] = discovery_analysis

        elif flow_type == "collection":
            collection_analysis = CollectionAnalysis.analyze_collection_phase_results(
                phase, results, state
            )
            # Map collection analysis results to expected keys
            if phase == "platform_detection":
                analysis["platform_detection_results"] = collection_analysis
            elif phase == "automated_collection":
                analysis["collection_metrics"] = collection_analysis
            elif phase == "gap_analysis":
                analysis["gap_analysis_results"] = collection_analysis
            elif phase == "questionnaire_generation":
                analysis["questionnaire_quality"] = collection_analysis
            elif phase == "manual_collection":
                analysis["manual_collection_results"] = collection_analysis
            elif phase == "synthesis":
                analysis["synthesis_results"] = collection_analysis

        return analysis

    def _make_transition_decision(
        self, current_phase: str, analysis: Dict[str, Any], flow_type: str = None
    ) -> AgentDecision:
        """Make decision based on analysis with flow-type awareness"""
        from app.services.crewai_flows.agents.decision.utils import DecisionUtils

        effective_flow_type = flow_type or analysis.get("flow_type", self.flow_type)

        # Check for critical errors first
        if analysis["has_errors"]:
            return AgentDecision(
                action=PhaseAction.FAIL,
                next_phase="",
                confidence=0.95,
                reasoning=f"Critical errors detected in {current_phase} phase that prevent continuation",
                metadata={
                    "errors": analysis.get("errors", []),
                    "flow_type": effective_flow_type,
                },
            )

        # Flow-type specific decision logic using modular components
        if effective_flow_type == "discovery":
            return DiscoveryDecisionLogic.make_discovery_decision(
                current_phase, analysis
            )
        elif effective_flow_type == "collection":
            return CollectionDecisionLogic.make_collection_decision(
                current_phase, analysis
            )
        else:
            # Default progression using flow registry fallback
            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase=DecisionUtils.get_next_phase(
                    current_phase, effective_flow_type
                ),
                confidence=0.8,
                reasoning=f"Phase {current_phase} completed successfully in {effective_flow_type} flow",
                metadata=analysis,
            )

    async def get_decision(self, agent_context: Dict[str, Any]) -> AgentDecision:
        """
        Get phase transition decision from agent context.
        This method is called by the execution engine to determine next steps.
        """
        try:
            # Extract key components from agent context
            current_phase = agent_context.get("current_phase", "")
            phase_result = agent_context.get("phase_result", {})
            flow_state = agent_context.get("flow_state")

            logger.info(
                f"🤖 PhaseTransitionAgent.get_decision called for phase: {current_phase}"
            )

            if not flow_state:
                logger.warning("⚠️ No flow state provided in agent context")
                return AgentDecision(
                    action=PhaseAction.FAIL,
                    next_phase="",
                    confidence=0.9,
                    reasoning="No flow state available for decision making",
                    metadata={"error": "missing_flow_state"},
                )

            # Convert flow_state to UnifiedDiscoveryFlowState if needed
            if isinstance(flow_state, dict):
                from app.models.unified_discovery_flow_state import (
                    UnifiedDiscoveryFlowState,
                )

                try:
                    state = UnifiedDiscoveryFlowState(**flow_state)
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to convert flow_state dict to UnifiedDiscoveryFlowState: {e}"
                    )
                    # Create minimal state for decision making
                    state = UnifiedDiscoveryFlowState()
                    state.current_phase = current_phase
            else:
                state = flow_state

            # Use the existing analyze_phase_transition method
            decision = await self.analyze_phase_transition(
                current_phase, phase_result, state
            )

            logger.info(
                f"✅ PhaseTransitionAgent decision: {decision.action.value} -> {decision.next_phase}"
            )
            return decision

        except Exception as e:
            logger.error(f"❌ PhaseTransitionAgent.get_decision failed: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            # Return safe fallback decision
            return AgentDecision(
                action=PhaseAction.FAIL,
                next_phase="",
                confidence=0.8,
                reasoning=f"Decision making failed due to error: {str(e)}",
                metadata={"error": str(e), "fallback": True},
            )

    async def get_post_execution_decision(
        self, agent_context: Dict[str, Any]
    ) -> AgentDecision:
        """
        Get post-execution decision after a phase has completed.
        This method is called after phase execution to determine next steps.
        """
        try:
            # Extract key components from agent context
            phase_name = agent_context.get("phase_name", "")
            phase_result = agent_context.get("phase_result", {})
            flow_state = agent_context.get("flow_state")

            logger.info(
                f"🤖 PhaseTransitionAgent.get_post_execution_decision called for phase: {phase_name}"
            )

            if not flow_state:
                logger.warning(
                    "⚠️ No flow state provided in agent context for post-execution decision"
                )
                return AgentDecision(
                    action=PhaseAction.FAIL,
                    next_phase="",
                    confidence=0.9,
                    reasoning="No flow state available for post-execution decision making",
                    metadata={"error": "missing_flow_state"},
                )

            # Convert flow_state to UnifiedDiscoveryFlowState if needed
            if isinstance(flow_state, dict):
                from app.models.unified_discovery_flow_state import (
                    UnifiedDiscoveryFlowState,
                )

                try:
                    state = UnifiedDiscoveryFlowState(**flow_state)
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to convert flow_state dict to UnifiedDiscoveryFlowState: {e}"
                    )
                    # Create minimal state for decision making
                    state = UnifiedDiscoveryFlowState()
                    state.current_phase = phase_name
            else:
                state = flow_state

            # Extract flow_type from runtime context instead of using self.flow_type default
            # Per ADR-023/ADR-028: Flow type must be determined from actual flow state
            flow_type = (
                agent_context.get("flow_type")  # First priority: explicit context
                or phase_result.get("flow_type")  # Second: phase result metadata
                or getattr(state, "flow_type", None)  # Third: flow state attribute
                or self.flow_type  # Fallback: agent default (discovery)
            )

            logger.info(f"🔍 Extracted flow_type for phase transition: {flow_type}")

            # Analyze the phase result and determine next steps
            analysis = self._analyze_current_state(
                phase_name, phase_result, state, flow_type
            )

            # Check if phase was successful based on result
            # CC FIX: Recognize that "paused" status is NOT always a failure
            # When paused for conflict resolution (conflict_resolution_pending=True), it's expected behavior
            phase_status = phase_result.get("status")
            phase_successful = phase_status == "completed"

            # Check if paused for user action (conflict resolution, manual review, etc.)
            crew_results = phase_result.get("crew_results", {})
            conflict_pending = crew_results.get("phase_state", {}).get(
                "conflict_resolution_pending", False
            )
            is_paused_for_user = phase_status == "paused" and conflict_pending

            # Paused for user action is considered successful (waiting for user, not failed)
            if is_paused_for_user:
                logger.info(
                    f"✅ Phase {phase_name} paused for user action (conflict resolution)"
                )
                return AgentDecision(
                    action=PhaseAction.PAUSE,
                    next_phase=phase_name,  # Stay on same phase until user resolves
                    confidence=0.95,
                    reasoning=f"Phase {phase_name} paused waiting for conflict resolution",
                    metadata={
                        "paused_for": "conflict_resolution",
                        "conflict_count": crew_results.get("conflict_count", 0),
                        "phase_result": phase_result,
                    },
                )

            if not phase_successful:
                # Phase failed, decide on retry or failure
                error_info = phase_result.get("error", "Unknown error")
                return AgentDecision(
                    action=(
                        PhaseAction.RETRY
                        if "timeout" in str(error_info).lower()
                        else PhaseAction.FAIL
                    ),
                    next_phase=phase_name,
                    confidence=0.8,
                    reasoning=f"Phase {phase_name} failed: {error_info}",
                    metadata={"error": error_info, "phase_result": phase_result},
                )

            # Phase successful, determine next phase
            decision = self._make_transition_decision(phase_name, analysis, flow_type)

            logger.info(
                f"✅ PhaseTransitionAgent post-execution decision: {decision.action.value} -> {decision.next_phase}"
            )
            return decision

        except Exception as e:
            logger.error(
                f"❌ PhaseTransitionAgent.get_post_execution_decision failed: {e}"
            )
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            # Return safe fallback decision
            return AgentDecision(
                action=PhaseAction.FAIL,
                next_phase="",
                confidence=0.8,
                reasoning=f"Post-execution decision making failed due to error: {str(e)}",
                metadata={"error": str(e), "fallback": True},
            )
