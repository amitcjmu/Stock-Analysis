"""
Unit tests for UnifiedAssessmentFlow with mock agents

This module tests the core assessment flow logic with mocked CrewAI agents
to ensure fast, isolated unit testing using Master Flow Orchestrator (MFO) patterns.

Generated with CC for MFO compliance.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import MFO fixtures and markers
from tests.fixtures.mfo_fixtures import (
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    DEMO_USER_ID,
    MockRequestContext,
    mock_tenant_scoped_agent_pool,
)

# Import assessment flow components (these will be created by other agents)
try:
    from app.core.flow_context import FlowContext
    from app.models.assessment_flow import AssessmentFlowState, AssessmentPhase
    from app.repositories.assessment_flow_repository import AssessmentFlowRepository
    from app.services.crewai_flows.unified_assessment_flow import UnifiedAssessmentFlow

    ASSESSMENT_AVAILABLE = True
except ImportError:
    # Mock classes for when components don't exist yet
    ASSESSMENT_AVAILABLE = False

    class UnifiedAssessmentFlow:
        def __init__(self, crewai_service, context):
            self.crewai_service = crewai_service
            self.context = context
            self.repository = MagicMock()
            self.postgres_store = MagicMock()

    class AssessmentFlowState:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class AssessmentPhase:
        ARCHITECTURE_MINIMUMS = "architecture_minimums"
        TECH_DEBT_ANALYSIS = "tech_debt_analysis"
        COMPONENT_SIXR_STRATEGIES = "component_sixr_strategies"
        APP_ON_PAGE_GENERATION = "app_on_page_generation"

    FlowContext = MagicMock
    AssessmentFlowRepository = MagicMock

from tests.fixtures.assessment_fixtures import (
    mock_assessment_repository,
)


class TestUnifiedAssessmentFlow:
    """Unit tests for UnifiedAssessmentFlow with mock agents - MFO compliant"""

    @pytest.fixture
    async def assessment_flow(self, mock_flow_context, mock_crewai_service):
        """Create assessment flow instance with mocked dependencies - MFO compliant"""
        # Use MockRequestContext instead of generic mock
        if not isinstance(mock_flow_context, MockRequestContext):
            mock_flow_context = MockRequestContext(
                client_account_id=DEMO_CLIENT_ACCOUNT_ID,
                engagement_id=DEMO_ENGAGEMENT_ID,
                user_id=DEMO_USER_ID,
            )

        flow = UnifiedAssessmentFlow(mock_crewai_service, mock_flow_context)

        # Mock repository and store with MFO compliance
        flow.repository = mock_assessment_repository()
        flow.postgres_store = AsyncMock()

        # Mock TenantScopedAgentPool
        with patch('app.services.persistent_agents.TenantScopedAgentPool') as mock_pool_class:
            mock_pool = mock_tenant_scoped_agent_pool()
            mock_pool_class.return_value = mock_pool
            flow.agent_pool = mock_pool

        return flow

    @pytest.mark.mfo
    @pytest.mark.assessment_flow
    @pytest.mark.database
    @pytest.mark.async_test
    async def test_initialize_assessment_success(
        self, assessment_flow, sample_applications
    ):
        """Test successful assessment flow initialization - MFO compliant"""

        # Mock repository methods
        assessment_flow.repository.create_assessment_flow = AsyncMock(
            return_value="test-flow-123"
        )
        assessment_flow.repository.save_flow_state = AsyncMock()

        # Mock application selection logic
        with patch.object(
            assessment_flow, "_select_applications_for_assessment"
        ) as mock_select:
            mock_select.return_value = sample_applications

            # Execute initialization
            result = await assessment_flow.initialize_assessment()

            # Assertions
            assert result.flow_id == "test-flow-123"
            assert result.status == "initialized"
            assert result.current_phase == AssessmentPhase.ARCHITECTURE_MINIMUMS
            assert result.progress == 10
            assert len(result.selected_application_ids) > 0

            # Verify repository calls
            assessment_flow.repository.create_assessment_flow.assert_called_once()
            assessment_flow.repository.save_flow_state.assert_called_once()

    @pytest.mark.mfo
    @pytest.mark.assessment_flow
    @pytest.mark.architecture_standards
    @pytest.mark.agent
    @pytest.mark.async_test
    async def test_capture_architecture_minimums_with_defaults(
        self,
        assessment_flow,
        sample_assessment_flow_state,
        sample_architecture_standards,
    ):
        """Test architecture minimums capture with default standards - MFO compliant"""

        # Create flow state object
        flow_state = AssessmentFlowState(**sample_assessment_flow_state)

        # Mock engagement standards loading
        with patch.object(assessment_flow, "_load_engagement_standards") as mock_load:
            mock_load.return_value = []

            with patch.object(
                assessment_flow, "_initialize_default_standards"
            ) as mock_init:
                mock_init.return_value = sample_architecture_standards

                # Mock state persistence
                assessment_flow.repository.save_flow_state = AsyncMock()

                # Execute phase
                result = await assessment_flow.capture_architecture_minimums(flow_state)

                # Assertions
                assert result.current_phase == AssessmentPhase.ARCHITECTURE_MINIMUMS
                assert result.status == "paused_for_user_input"
                assert "architecture_minimums" in result.pause_points
                assert len(result.engagement_architecture_standards) == 3
                assert result.progress == 20

                # Verify standards were properly set
                standards = result.engagement_architecture_standards
                java_standard = next(
                    (s for s in standards if s["requirement_type"] == "java_versions"),
                    None,
                )
                assert java_standard is not None
                assert java_standard["mandatory"] is True

    @pytest.mark.mfo
    @pytest.mark.assessment_flow
    @pytest.mark.tech_debt
    @pytest.mark.agent
    @pytest.mark.async_test
    async def test_analyze_technical_debt_with_components(
        self,
        assessment_flow,
        sample_assessment_flow_state,
        sample_component_analysis_result,
    ):
        """Test technical debt analysis with component identification - MFO compliant"""

        # Create flow state object
        flow_state = AssessmentFlowState(**sample_assessment_flow_state)
        flow_state.engagement_architecture_standards = [
            {"requirement_type": "java_versions", "supported_versions": {"java": "11+"}}
        ]

        # Setup mock crew result
        assessment_flow.crewai_service.run_crew.return_value = (
            sample_component_analysis_result
        )

        # Mock application metadata
        with patch.object(
            assessment_flow, "_get_application_metadata"
        ) as mock_metadata:
            mock_metadata.return_value = {"app_type": "web_application"}

            # Mock state persistence
            assessment_flow.repository.save_flow_state = AsyncMock()

            # Execute phase
            result = await assessment_flow.analyze_technical_debt(flow_state)

            # Assertions
            assert result.current_phase == AssessmentPhase.TECH_DEBT_ANALYSIS
            assert result.status == "paused_for_user_input"
            assert len(result.application_components) > 0
            assert len(result.tech_debt_analysis) > 0
            assert result.progress == 50

            # Verify crew was called correctly
            assessment_flow.crewai_service.run_crew.assert_called_with(
                "component_analysis_crew", context=pytest.Any
            )

            # Verify component analysis results
            assert "app-1" in result.application_components
            components = result.application_components["app-1"]["components"]
            assert len(components) == 3

            # Verify tech debt analysis
            tech_debt = result.tech_debt_analysis["app-1"]
            assert tech_debt["overall_tech_debt_score"] == 7.2
            assert len(tech_debt["tech_debt_items"]) == 2

    @pytest.mark.mfo
    @pytest.mark.assessment_flow
    @pytest.mark.sixr_strategy
    @pytest.mark.agent
    @pytest.mark.async_test
    async def test_determine_sixr_strategies_with_validation(
        self, assessment_flow, sample_assessment_flow_state, sample_sixr_strategy_result
    ):
        """Test 6R strategy determination with compatibility validation - MFO compliant"""

        # Create flow state object with previous phase data
        flow_state = AssessmentFlowState(**sample_assessment_flow_state)
        flow_state.current_phase = AssessmentPhase.TECH_DEBT_ANALYSIS
        flow_state.application_components = {
            "app-1": {"components": [{"name": "frontend", "type": "ui"}]}
        }
        flow_state.tech_debt_analysis = {"app-1": {"overall_tech_debt_score": 7.2}}

        # Setup mock crew result
        assessment_flow.crewai_service.run_crew.return_value = (
            sample_sixr_strategy_result
        )

        # Mock application name lookup
        with patch.object(assessment_flow, "_get_application_name") as mock_name:
            mock_name.return_value = "Test Application"

            # Mock state persistence
            assessment_flow.repository.save_flow_state = AsyncMock()

            # Execute phase
            result = await assessment_flow.determine_component_sixr_strategies(
                flow_state
            )

            # Assertions
            assert result.current_phase == AssessmentPhase.COMPONENT_SIXR_STRATEGIES
            assert result.status == "paused_for_user_input"
            assert len(result.sixr_decisions) > 0
            assert result.progress == 75

            # Verify decision structure
            app_id = list(result.sixr_decisions.keys())[0]
            decision = result.sixr_decisions[app_id]
            assert decision["overall_strategy"] == "refactor"
            assert decision["confidence_score"] == 0.85
            assert len(decision["component_treatments"]) == 3

            # Verify component treatments
            treatments = decision["component_treatments"]
            frontend_treatment = next(
                (t for t in treatments if t["component_name"] == "frontend"), None
            )
            assert frontend_treatment is not None
            assert frontend_treatment["recommended_strategy"] == "refactor"

    @pytest.mark.mfo
    @pytest.mark.assessment_flow
    @pytest.mark.sixr_strategy
    @pytest.mark.agent
    @pytest.mark.async_test
    async def test_generate_app_on_page_summary(
        self, assessment_flow, sample_assessment_flow_state
    ):
        """Test app-on-page generation with complete flow data - MFO compliant"""

        # Create flow state with complete assessment data
        flow_state = AssessmentFlowState(**sample_assessment_flow_state)
        flow_state.current_phase = AssessmentPhase.COMPONENT_SIXR_STRATEGIES
        flow_state.sixr_decisions = {
            "app-1": {
                "application_name": "Frontend Portal",
                "overall_strategy": "refactor",
                "confidence_score": 0.85,
                "component_treatments": [
                    {"component_name": "frontend", "recommended_strategy": "refactor"}
                ],
            }
        }

        # Mock app-on-page crew result
        mock_app_page_result = {
            "applications_summary": [
                {
                    "application_id": "app-1",
                    "application_name": "Frontend Portal",
                    "recommended_strategy": "refactor",
                    "business_justification": "Modernization for better performance",
                    "technical_summary": "React upgrade and containerization",
                    "effort_estimate": "16 weeks",
                    "risk_assessment": "Medium risk with good mitigation strategies",
                }
            ],
            "assessment_summary": {
                "total_applications": 1,
                "strategy_distribution": {"refactor": 1},
                "overall_readiness": "high",
            },
        }

        assessment_flow.crewai_service.run_crew.return_value = mock_app_page_result
        assessment_flow.repository.save_flow_state = AsyncMock()

        # Execute phase
        result = await assessment_flow.generate_app_on_page_summary(flow_state)

        # Assertions
        assert result.current_phase == AssessmentPhase.APP_ON_PAGE_GENERATION
        assert result.status == "completed"
        assert result.progress == 100
        assert len(result.apps_ready_for_planning) > 0

        # Verify app-on-page results
        app_summary = result.assessment_results["applications_summary"][0]
        assert app_summary["application_name"] == "Frontend Portal"
        assert app_summary["recommended_strategy"] == "refactor"

    @pytest.mark.mfo
    @pytest.mark.assessment_flow
    @pytest.mark.database
    @pytest.mark.async_test
    async def test_resume_from_phase_with_user_input(
        self, assessment_flow, sample_assessment_flow_state
    ):
        """Test flow resume functionality with user input - MFO compliant"""

        user_input = {
            "architecture_standards": [
                {
                    "requirement_type": "custom_standard",
                    "description": "Custom requirement",
                    "mandatory": False,
                }
            ]
        }

        # Mock state loading and saving
        flow_state = AssessmentFlowState(**sample_assessment_flow_state)
        assessment_flow.postgres_store.load_flow_state = AsyncMock(
            return_value=flow_state
        )
        assessment_flow.repository.save_user_input = AsyncMock()

        # Mock next phase execution
        with patch.object(assessment_flow, "analyze_technical_debt") as mock_next_phase:
            mock_next_phase.return_value = flow_state

            # Execute resume
            result = await assessment_flow.resume_from_phase(
                AssessmentPhase.ARCHITECTURE_MINIMUMS, user_input
            )

            # Assertions
            assert result is not None
            assessment_flow.repository.save_user_input.assert_called_once()
            mock_next_phase.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_during_crew_execution(
        self, assessment_flow, sample_assessment_flow_state
    ):
        """Test error handling when CrewAI execution fails"""

        flow_state = AssessmentFlowState(**sample_assessment_flow_state)

        # Setup crew to raise exception
        assessment_flow.crewai_service.run_crew.side_effect = Exception(
            "Crew execution failed"
        )

        # Execute phase and expect exception
        with pytest.raises(Exception) as exc_info:
            await assessment_flow.analyze_technical_debt(flow_state)

        assert "Crew execution failed" in str(exc_info.value)

    @pytest.mark.mfo
    @pytest.mark.assessment_flow
    @pytest.mark.tenant_isolation
    @pytest.mark.async_test
    async def test_multi_tenant_isolation(self):
        """Test that flows maintain multi-tenant isolation - MFO compliant"""

        # Create flows for different clients using MockRequestContext
        context_1 = MockRequestContext(
            client_account_id=DEMO_CLIENT_ACCOUNT_ID,
            engagement_id=DEMO_ENGAGEMENT_ID,
            user_id=DEMO_USER_ID,
        )

        context_2 = MockRequestContext(
            client_account_id="tenant-2-1111-1111-1111-111111111111",
            engagement_id="engage-2-2222-2222-2222-222222222222",
            user_id="user-2-3333-3333-3333-333333333333",
        )

        mock_crewai = AsyncMock()

        flow_1 = UnifiedAssessmentFlow(mock_crewai, context_1)
        flow_2 = UnifiedAssessmentFlow(mock_crewai, context_2)

        # Mock repositories with different client contexts
        flow_1.repository = MagicMock()
        flow_1.repository.client_account_id = DEMO_CLIENT_ACCOUNT_ID
        flow_1.repository.get_assessment_flow_state = AsyncMock(return_value=None)

        flow_2.repository = MagicMock()
        flow_2.repository.client_account_id = "tenant-2-1111-1111-1111-111111111111"
        flow_2.repository.get_assessment_flow_state = AsyncMock(return_value=None)

        # Verify different client contexts
        assert flow_1.context.client_account_id == DEMO_CLIENT_ACCOUNT_ID
        assert flow_2.context.client_account_id == "tenant-2-1111-1111-1111-111111111111"
        assert flow_1.repository.client_account_id == DEMO_CLIENT_ACCOUNT_ID
        assert flow_2.repository.client_account_id == "tenant-2-1111-1111-1111-111111111111"

    @pytest.mark.asyncio
    async def test_phase_transition_validation(
        self, assessment_flow, sample_assessment_flow_state
    ):
        """Test that phase transitions are properly validated"""

        flow_state = AssessmentFlowState(**sample_assessment_flow_state)

        # Test invalid phase transition (skipping phases)
        flow_state.current_phase = AssessmentPhase.ARCHITECTURE_MINIMUMS

        with pytest.raises(ValueError) as exc_info:
            # Try to jump to 6R strategies without completing tech debt analysis
            await assessment_flow.determine_component_sixr_strategies(flow_state)

        assert "Invalid phase transition" in str(
            exc_info.value
        ) or "Prerequisites not met" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_flow_state_persistence(
        self, assessment_flow, sample_assessment_flow_state
    ):
        """Test that flow state is properly persisted at each phase"""

        flow_state = AssessmentFlowState(**sample_assessment_flow_state)
        assessment_flow.repository.save_flow_state = AsyncMock()

        # Mock successful crew execution
        assessment_flow.crewai_service.run_crew.return_value = {"status": "completed"}

        with patch.object(assessment_flow, "_load_engagement_standards") as mock_load:
            mock_load.return_value = []

            with patch.object(
                assessment_flow, "_initialize_default_standards"
            ) as mock_init:
                mock_init.return_value = []

                # Execute phase
                await assessment_flow.capture_architecture_minimums(flow_state)

                # Verify state was persisted
                assessment_flow.repository.save_flow_state.assert_called()

                # Verify state contains expected data
                saved_state = assessment_flow.repository.save_flow_state.call_args[0][0]
                assert (
                    saved_state.current_phase == AssessmentPhase.ARCHITECTURE_MINIMUMS
                )
                assert saved_state.status == "paused_for_user_input"


class TestAssessmentFlowEdgeCases:
    """Test edge cases and error conditions - MFO compliant"""

    @pytest.fixture
    async def assessment_flow(self, mock_flow_context, mock_crewai_service):
        """Create assessment flow instance - MFO compliant"""
        # Ensure we use MockRequestContext
        if not isinstance(mock_flow_context, MockRequestContext):
            mock_flow_context = MockRequestContext(
                client_account_id=DEMO_CLIENT_ACCOUNT_ID,
                engagement_id=DEMO_ENGAGEMENT_ID,
                user_id=DEMO_USER_ID,
            )

        flow = UnifiedAssessmentFlow(mock_crewai_service, mock_flow_context)
        flow.repository = mock_assessment_repository()
        flow.postgres_store = AsyncMock()

        # Mock TenantScopedAgentPool
        with patch('app.services.persistent_agents.TenantScopedAgentPool') as mock_pool_class:
            mock_pool = mock_tenant_scoped_agent_pool()
            mock_pool_class.return_value = mock_pool
            flow.agent_pool = mock_pool

        return flow

    @pytest.mark.mfo
    @pytest.mark.assessment_flow
    @pytest.mark.async_test
    async def test_empty_application_list(self, assessment_flow):
        """Test handling of empty application list - MFO compliant"""

        # Mock empty application selection
        with patch.object(
            assessment_flow, "_select_applications_for_assessment"
        ) as mock_select:
            mock_select.return_value = []

            with pytest.raises(ValueError) as exc_info:
                await assessment_flow.initialize_assessment()

            assert "No applications" in str(exc_info.value)

    @pytest.mark.mfo
    @pytest.mark.assessment_flow
    @pytest.mark.agent
    @pytest.mark.async_test
    async def test_crew_timeout_handling(
        self, assessment_flow, sample_assessment_flow_state
    ):
        """Test handling of crew execution timeouts - MFO compliant"""

        flow_state = AssessmentFlowState(**sample_assessment_flow_state)

        # Mock crew timeout
        assessment_flow.crewai_service.run_crew.side_effect = asyncio.TimeoutError(
            "Crew execution timed out"
        )

        with pytest.raises(asyncio.TimeoutError):
            await assessment_flow.analyze_technical_debt(flow_state)

    @pytest.mark.mfo
    @pytest.mark.assessment_flow
    @pytest.mark.async_test
    async def test_invalid_user_input_handling(
        self, assessment_flow, sample_assessment_flow_state
    ):
        """Test handling of invalid user input - MFO compliant"""

        invalid_user_input = {"invalid_field": "invalid_value"}

        with pytest.raises(ValueError) as exc_info:
            await assessment_flow.resume_from_phase(
                AssessmentPhase.ARCHITECTURE_MINIMUMS, invalid_user_input
            )

        assert "Invalid user input" in str(
            exc_info.value
        ) or "Required fields missing" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
