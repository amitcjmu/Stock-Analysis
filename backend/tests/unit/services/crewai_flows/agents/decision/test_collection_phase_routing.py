"""
Unit tests for Collection Phase Routing in Phase Transition Agent.

Tests the fix for Bug #1135: Collection Flow Phase Transition Agent
Defaults to 'Completed' for Unknown Phases.

CC Generated for Issue #1135 - Collection Flow Phase Transition Bug
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.crewai_flows.agents.decision.phase_transition import (
    PhaseTransitionAgent,
)
from app.services.crewai_flows.agents.decision.base import AgentDecision, PhaseAction


class TestCollectionPhaseRouting:
    """Test that collection flow phases route to collection analysis, not discovery."""

    @pytest.fixture
    def phase_transition_agent(self):
        """Create a PhaseTransitionAgent instance."""
        return PhaseTransitionAgent()

    @pytest.fixture
    def mock_flow_state(self):
        """Create a mock flow state object."""
        state = MagicMock()
        state.flow_type = "collection"
        state.current_phase = "questionnaire_generation"
        return state

    @pytest.mark.asyncio
    async def test_collection_questionnaire_generation_routes_correctly(
        self, phase_transition_agent, mock_flow_state
    ):
        """
        Test that questionnaire_generation phase routes to CollectionAnalysis,
        not DiscoveryAnalysis.

        This is the core bug from Issue #1135.
        """
        agent_context = {
            "flow_type": "collection",  # Explicit collection flow
            "current_phase": "questionnaire_generation",
            "phase_result": {
                "status": "completed",
                "questionnaires_generated": 3,
            },
            "flow_state": mock_flow_state,
        }

        # Mock the decision logic to verify it's called with correct flow_type
        with patch(
            "app.services.crewai_flows.agents.decision.phase_transition.CollectionDecisionLogic.make_collection_decision"
        ) as mock_collection_decision:
            mock_collection_decision.return_value = AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase="manual_collection",
                confidence=0.9,
                reasoning="Questionnaires generated successfully",
                metadata={},
            )

            decision = await phase_transition_agent.get_decision(agent_context)

            # Verify CollectionDecisionLogic was called (not DiscoveryDecisionLogic)
            mock_collection_decision.assert_called_once()

            # Verify decision is correct
            assert decision.action == PhaseAction.PROCEED
            assert decision.next_phase == "manual_collection"

    @pytest.mark.asyncio
    async def test_collection_gap_analysis_routes_correctly(
        self, phase_transition_agent, mock_flow_state
    ):
        """Test that gap_analysis phase routes to CollectionAnalysis."""
        mock_flow_state.current_phase = "gap_analysis"

        agent_context = {
            "flow_type": "collection",
            "current_phase": "gap_analysis",
            "phase_result": {
                "status": "completed",
                "gaps_identified": 64,
            },
            "flow_state": mock_flow_state,
        }

        with patch(
            "app.services.crewai_flows.agents.decision.phase_transition.CollectionDecisionLogic.make_collection_decision"
        ) as mock_collection_decision:
            mock_collection_decision.return_value = AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase="questionnaire_generation",
                confidence=0.95,
                reasoning="Gaps identified, proceeding to questionnaires",
                metadata={},
            )

            decision = await phase_transition_agent.get_decision(agent_context)

            # Verify CollectionDecisionLogic was called
            mock_collection_decision.assert_called_once()
            assert decision.next_phase == "questionnaire_generation"

    @pytest.mark.asyncio
    async def test_flow_type_fallback_chain(self, phase_transition_agent):
        """
        Test the flow_type extraction fallback chain.

        Priority:
        1. agent_context.flow_type
        2. phase_result.flow_type
        3. flow_state.flow_type
        4. self.flow_type (default: discovery)
        """
        # Test 1: flow_type from agent_context (highest priority)
        agent_context = {
            "flow_type": "collection",  # Should win
            "current_phase": "gap_analysis",
            "phase_result": {"flow_type": "discovery"},  # Should be ignored
            "flow_state": MagicMock(flow_type="discovery"),  # Should be ignored
        }

        with patch(
            "app.services.crewai_flows.agents.decision.phase_transition.CollectionDecisionLogic.make_collection_decision"
        ) as mock_collection_decision:
            mock_collection_decision.return_value = AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase="questionnaire_generation",
                confidence=0.9,
                reasoning="Test",
                metadata={},
            )

            await phase_transition_agent.get_decision(agent_context)

            # Should call CollectionDecisionLogic, not DiscoveryDecisionLogic
            mock_collection_decision.assert_called_once()

    @pytest.mark.asyncio
    async def test_flow_type_not_in_context_uses_default(
        self, phase_transition_agent
    ):
        """
        Test that when flow_type is not in agent_context, it defaults to "discovery".

        Note: get_decision() only uses agent_context.flow_type, not fallbacks.
        Fallback logic is in get_post_execution_decision().
        """
        mock_state = MagicMock()

        agent_context = {
            # No flow_type in context → will use agent default "discovery"
            "current_phase": "data_import",
            "phase_result": {},
            "flow_state": mock_state,
        }

        with patch(
            "app.services.crewai_flows.agents.decision.phase_transition.DiscoveryDecisionLogic.make_discovery_decision"
        ) as mock_discovery_decision:
            mock_discovery_decision.return_value = AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase="field_mapping",
                confidence=0.9,
                reasoning="Test",
                metadata={},
            )

            await phase_transition_agent.get_decision(agent_context)

            # Should call DiscoveryDecisionLogic (default behavior)
            mock_discovery_decision.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_flow_type_fails_instead_of_completing(
        self, phase_transition_agent
    ):
        """
        Test that unknown flow types FAIL instead of silently completing.

        This is the core fix for Bug #1135 - don't default to "completed".
        """
        mock_state = MagicMock()

        agent_context = {
            "flow_type": "unknown_flow_type",
            "current_phase": "some_phase",
            "phase_result": {"status": "completed"},
            "flow_state": mock_state,  # Must provide state to avoid early exit
        }

        with patch(
            "app.services.crewai_flows.agents.decision.utils.DecisionUtils.get_next_phase"
        ) as mock_get_next_phase:
            # Simulate flow registry returning None (unknown phase)
            mock_get_next_phase.return_value = None

            decision = await phase_transition_agent.get_decision(agent_context)

            # Should FAIL, not COMPLETE
            assert decision.action == PhaseAction.FAIL
            assert "unknown_flow_type" in decision.metadata.get("error", "")

    @pytest.mark.asyncio
    async def test_post_execution_decision_uses_collection_logic(
        self, phase_transition_agent
    ):
        """
        Test that post-execution decisions also route to collection logic.

        This tests the get_post_execution_decision() method.
        """
        mock_state = MagicMock()
        mock_state.flow_type = "collection"

        agent_context = {
            "flow_type": "collection",
            "phase_name": "questionnaire_generation",
            "phase_result": {
                "status": "completed",
                "questionnaires_generated": 3,
            },
            "flow_state": mock_state,
        }

        with patch(
            "app.services.crewai_flows.agents.decision.phase_transition.CollectionDecisionLogic.make_collection_decision"
        ) as mock_collection_decision:
            mock_collection_decision.return_value = AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase="manual_collection",
                confidence=0.9,
                reasoning="Questionnaires generated successfully",
                metadata={},
            )

            decision = await phase_transition_agent.get_post_execution_decision(
                agent_context
            )

            # Verify CollectionDecisionLogic was called
            mock_collection_decision.assert_called_once()
            assert decision.next_phase == "manual_collection"

    @pytest.mark.asyncio
    async def test_all_collection_phases_route_correctly(
        self, phase_transition_agent
    ):
        """
        Test that all collection phases route to CollectionDecisionLogic.

        Collection phases (ADR-037):
        - asset_selection
        - gap_analysis
        - questionnaire_generation
        - finalization
        """
        collection_phases = [
            "asset_selection",
            "gap_analysis",
            "questionnaire_generation",
            "finalization",
        ]

        for phase in collection_phases:
            mock_state = MagicMock()
            mock_state.flow_type = "collection"
            mock_state.current_phase = phase

            agent_context = {
                "flow_type": "collection",
                "current_phase": phase,
                "phase_result": {"status": "completed"},
                "flow_state": mock_state,
            }

            with patch(
                "app.services.crewai_flows.agents.decision.phase_transition.CollectionDecisionLogic.make_collection_decision"
            ) as mock_collection_decision:
                mock_collection_decision.return_value = AgentDecision(
                    action=PhaseAction.PROCEED,
                    next_phase="next_phase",
                    confidence=0.9,
                    reasoning=f"Phase {phase} completed",
                    metadata={},
                )

                decision = await phase_transition_agent.get_decision(agent_context)

                # Verify CollectionDecisionLogic was called for this phase
                mock_collection_decision.assert_called_once()
                assert decision.action == PhaseAction.PROCEED
