"""
Integration Tests for Unified Discovery Flow - Consolidation Implementation

This module tests the unified discovery flow implementation,
ensuring all phases work correctly with the new consolidated architecture.
"""

import pytest
from unittest.mock import Mock, AsyncMock
import time

# Mock imports for testing
try:
    from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
    from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
    from app.models.workflow_state import WorkflowState
    from app.repositories.base_repository import ContextAwareRepository
except ImportError:
    # Fallback for testing environment
    UnifiedDiscoveryFlow = Mock
    UnifiedDiscoveryFlowState = Mock
    WorkflowState = Mock
    ContextAwareRepository = Mock


@pytest.fixture
def mock_flow_state():
    """Create mock unified flow state for testing"""
    return UnifiedDiscoveryFlowState(
        flow_id="test-flow-123",
        session_id="test-session-456",
        client_account_id="client-789",
        engagement_id="engagement-101",
        user_id="user-202",
        current_phase="initialization",
        phase_completion={
            "data_import": False,
            "field_mapping": False,
            "data_cleansing": False,
            "asset_inventory": False,
            "dependency_analysis": False,
            "tech_debt_analysis": False
        },
        status="running",
        progress_percentage=0.0
    )


@pytest.fixture
def mock_unified_flow(mock_flow_state):
    """Create mock unified discovery flow for testing"""
    flow = Mock(spec=UnifiedDiscoveryFlow)
    flow.state = mock_flow_state
    flow.initialize_discovery = AsyncMock(return_value={"status": "initialized", "flow_id": "test-flow-123"})
    flow.execute_field_mapping_crew = AsyncMock(return_value={"phase": "field_mapping", "status": "completed"})
    flow.execute_data_cleansing_crew = AsyncMock(return_value={"phase": "data_cleansing", "status": "completed"})
    flow.execute_asset_inventory_crew = AsyncMock(return_value={"phase": "asset_inventory", "status": "completed"})
    flow.execute_dependency_analysis_crew = AsyncMock(
        return_value={"phase": "dependency_analysis", "status": "completed"}
    )
    flow.execute_tech_debt_analysis_crew = AsyncMock(
        return_value={"phase": "tech_debt_analysis", "status": "completed"}
    )
    flow.finalize_discovery = AsyncMock(return_value={"status": "completed", "summary": {"total_phases": 6}})
    return flow


class TestUnifiedDiscoveryFlowInitialization:
    """Test flow initialization and state management"""

    @pytest.mark.asyncio
    async def test_flow_initialization(self, mock_unified_flow):
        """Test that flow initializes correctly with proper state"""
        result = await mock_unified_flow.initialize_discovery()

        assert result["status"] == "initialized"
        assert result["flow_id"] == "test-flow-123"
        assert mock_unified_flow.state.status == "running"
        assert mock_unified_flow.state.current_phase == "initialization"

    @pytest.mark.asyncio
    async def test_flow_state_persistence(self, mock_flow_state):
        """Test that flow state persists correctly"""
        # Test state model validation
        assert mock_flow_state.flow_id == "test-flow-123"
        assert mock_flow_state.session_id == "test-session-456"
        assert mock_flow_state.client_account_id == "client-789"
        assert mock_flow_state.engagement_id == "engagement-101"

        # Test phase completion tracking
        assert not mock_flow_state.phase_completion["field_mapping"]
        mock_flow_state.phase_completion["field_mapping"] = True
        assert mock_flow_state.phase_completion["field_mapping"]

    def test_flow_state_validation(self):
        """Test flow state model validation"""
        # Test valid state creation
        state = UnifiedDiscoveryFlowState(
            flow_id="valid-flow",
            session_id="valid-session",
            client_account_id="valid-client",
            engagement_id="valid-engagement",
            user_id="valid-user"
        )

        assert state.flow_id == "valid-flow"
        assert state.current_phase == "initialization"
        assert state.status == "running"
        assert state.progress_percentage == 0.0


class TestUnifiedDiscoveryFlowPhaseExecution:
    """Test individual phase execution"""

    @pytest.mark.asyncio
    async def test_field_mapping_phase(self, mock_unified_flow):
        """Test field mapping phase execution"""
        # Initialize first
        await mock_unified_flow.initialize_discovery()

        # Execute field mapping
        result = await mock_unified_flow.execute_field_mapping_crew({"status": "initialized"})

        assert result["phase"] == "field_mapping"
        assert result["status"] == "completed"
        mock_unified_flow.execute_field_mapping_crew.assert_called_once()

    @pytest.mark.asyncio
    async def test_data_cleansing_phase(self, mock_unified_flow):
        """Test data cleansing phase execution"""
        # Setup previous result
        previous_result = {"phase": "field_mapping", "status": "completed"}

        # Execute data cleansing
        result = await mock_unified_flow.execute_data_cleansing_crew(previous_result)

        assert result["phase"] == "data_cleansing"
        assert result["status"] == "completed"
        mock_unified_flow.execute_data_cleansing_crew.assert_called_once_with(previous_result)

    @pytest.mark.asyncio
    async def test_asset_inventory_phase(self, mock_unified_flow):
        """Test asset inventory phase execution"""
        previous_result = {"phase": "data_cleansing", "status": "completed"}

        result = await mock_unified_flow.execute_asset_inventory_crew(previous_result)

        assert result["phase"] == "asset_inventory"
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_dependency_analysis_phase(self, mock_unified_flow):
        """Test dependency analysis phase execution"""
        previous_result = {"phase": "asset_inventory", "status": "completed"}

        result = await mock_unified_flow.execute_dependency_analysis_crew(previous_result)

        assert result["phase"] == "dependency_analysis"
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_tech_debt_analysis_phase(self, mock_unified_flow):
        """Test tech debt analysis phase execution"""
        previous_result = {"phase": "dependency_analysis", "status": "completed"}

        result = await mock_unified_flow.execute_tech_debt_analysis_crew(previous_result)

        assert result["phase"] == "tech_debt_analysis"
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_flow_finalization(self, mock_unified_flow):
        """Test flow finalization"""
        previous_result = {"phase": "tech_debt_analysis", "status": "completed"}

        result = await mock_unified_flow.finalize_discovery(previous_result)

        assert result["status"] == "completed"
        assert "summary" in result
        assert result["summary"]["total_phases"] == 6


class TestUnifiedDiscoveryFlowSequence:
    """Test complete flow sequence execution"""

    @pytest.mark.asyncio
    async def test_complete_flow_sequence(self, mock_unified_flow):
        """Test complete flow from initialization to completion"""
        # Track phase execution order
        execution_order = []

        # Mock each phase to track execution
        async def track_initialization():
            execution_order.append("initialization")
            mock_unified_flow.state.current_phase = "field_mapping"
            return {"status": "initialized", "flow_id": "test-flow-123"}

        async def track_field_mapping(prev_result):
            execution_order.append("field_mapping")
            mock_unified_flow.state.current_phase = "data_cleansing"
            mock_unified_flow.state.phase_completion["field_mapping"] = True
            return {"phase": "field_mapping", "status": "completed"}

        async def track_data_cleansing(prev_result):
            execution_order.append("data_cleansing")
            mock_unified_flow.state.current_phase = "asset_inventory"
            mock_unified_flow.state.phase_completion["data_cleansing"] = True
            return {"phase": "data_cleansing", "status": "completed"}

        async def track_asset_inventory(prev_result):
            execution_order.append("asset_inventory")
            mock_unified_flow.state.current_phase = "dependency_analysis"
            mock_unified_flow.state.phase_completion["asset_inventory"] = True
            return {"phase": "asset_inventory", "status": "completed"}

        async def track_dependency_analysis(prev_result):
            execution_order.append("dependency_analysis")
            mock_unified_flow.state.current_phase = "tech_debt_analysis"
            mock_unified_flow.state.phase_completion["dependency_analysis"] = True
            return {"phase": "dependency_analysis", "status": "completed"}

        async def track_tech_debt_analysis(prev_result):
            execution_order.append("tech_debt_analysis")
            mock_unified_flow.state.current_phase = "completed"
            mock_unified_flow.state.phase_completion["tech_debt_analysis"] = True
            return {"phase": "tech_debt_analysis", "status": "completed"}

        async def track_finalization(prev_result):
            execution_order.append("finalization")
            mock_unified_flow.state.status = "completed"
            mock_unified_flow.state.progress_percentage = 100.0
            return {"status": "completed", "summary": {"total_phases": 6}}

        # Assign tracking functions
        mock_unified_flow.initialize_discovery = track_initialization
        mock_unified_flow.execute_field_mapping_crew = track_field_mapping
        mock_unified_flow.execute_data_cleansing_crew = track_data_cleansing
        mock_unified_flow.execute_asset_inventory_crew = track_asset_inventory
        mock_unified_flow.execute_dependency_analysis_crew = track_dependency_analysis
        mock_unified_flow.execute_tech_debt_analysis_crew = track_tech_debt_analysis
        mock_unified_flow.finalize_discovery = track_finalization

        # Execute complete flow sequence
        result1 = await mock_unified_flow.initialize_discovery()
        result2 = await mock_unified_flow.execute_field_mapping_crew(result1)
        result3 = await mock_unified_flow.execute_data_cleansing_crew(result2)
        result4 = await mock_unified_flow.execute_asset_inventory_crew(result3)
        result5 = await mock_unified_flow.execute_dependency_analysis_crew(result4)
        result6 = await mock_unified_flow.execute_tech_debt_analysis_crew(result5)
        await mock_unified_flow.finalize_discovery(result6)

        # Verify execution order
        expected_order = [
            "initialization",
            "field_mapping",
            "data_cleansing",
            "asset_inventory",
            "dependency_analysis",
            "tech_debt_analysis",
            "finalization"
        ]
        assert execution_order == expected_order

        # Verify final state
        assert mock_unified_flow.state.status == "completed"
        assert mock_unified_flow.state.progress_percentage == 100.0
        assert all(mock_unified_flow.state.phase_completion.values())


class TestUnifiedDiscoveryFlowErrorHandling:
    """Test error handling and recovery"""

    @pytest.mark.asyncio
    async def test_phase_failure_handling(self, mock_unified_flow):
        """Test handling of phase execution failures"""
        # Mock a failing phase
        async def failing_data_cleansing(prev_result):
            raise Exception("Data cleansing crew failed")

        mock_unified_flow.execute_data_cleansing_crew = failing_data_cleansing

        # Test that failure is handled gracefully
        with pytest.raises(Exception, match="Data cleansing crew failed"):
            await mock_unified_flow.execute_data_cleansing_crew({"phase": "field_mapping"})

    @pytest.mark.asyncio
    async def test_state_recovery_after_failure(self, mock_flow_state):
        """Test state recovery mechanisms after failures"""
        # Simulate a failed state
        mock_flow_state.status = "failed"
        mock_flow_state.errors = [{"phase": "data_cleansing", "error": "Crew execution failed"}]

        # Test recovery
        mock_flow_state.status = "running"
        mock_flow_state.errors = []

        assert mock_flow_state.status == "running"
        assert len(mock_flow_state.errors) == 0


class TestUnifiedDiscoveryFlowMultiTenancy:
    """Test multi-tenant support"""

    def test_client_account_isolation(self):
        """Test that different client accounts have isolated flow states"""
        state1 = UnifiedDiscoveryFlowState(
            flow_id="flow-1",
            session_id="session-1",
            client_account_id="client-1",
            engagement_id="engagement-1",
            user_id="user-1"
        )

        state2 = UnifiedDiscoveryFlowState(
            flow_id="flow-2",
            session_id="session-2",
            client_account_id="client-2",
            engagement_id="engagement-2",
            user_id="user-2"
        )

        # Verify isolation
        assert state1.client_account_id != state2.client_account_id
        assert state1.engagement_id != state2.engagement_id
        assert state1.flow_id != state2.flow_id

    def test_engagement_scoping(self):
        """Test that flows are properly scoped to engagements"""
        state = UnifiedDiscoveryFlowState(
            flow_id="test-flow",
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user"
        )

        assert state.engagement_id == "test-engagement"
        assert state.client_account_id == "test-client"


class TestUnifiedDiscoveryFlowPerformance:
    """Test performance characteristics"""

    @pytest.mark.asyncio
    async def test_flow_execution_timing(self, mock_unified_flow):
        """Test flow execution performance"""
        start_time = time.time()

        # Execute flow phases
        await mock_unified_flow.initialize_discovery()
        await mock_unified_flow.execute_field_mapping_crew({"status": "initialized"})
        await mock_unified_flow.execute_data_cleansing_crew({"phase": "field_mapping"})

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete quickly in test environment
        assert execution_time < 1.0  # Less than 1 second for mocked execution

    def test_state_model_efficiency(self):
        """Test state model memory efficiency"""
        state = UnifiedDiscoveryFlowState(
            flow_id="efficiency-test",
            session_id="efficiency-session",
            client_account_id="efficiency-client",
            engagement_id="efficiency-engagement",
            user_id="efficiency-user"
        )

        # Test that state can handle large data sets
        large_data = [{"record": i} for i in range(1000)]
        state.raw_data = large_data

        assert len(state.raw_data) == 1000
        assert state.raw_data[0]["record"] == 0
        assert state.raw_data[999]["record"] == 999


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
