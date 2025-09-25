"""
Unit Tests for State Management Components - High Impact

This module provides comprehensive unit tests for state management components
in the discovery flow, covering state persistence, transitions, and recovery.

Test Coverage:
- StateManager
- FlowStateBridge
- UnifiedFlowManagement
- FlowManager
- FlowFinalizer
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
from typing import Any, Dict, List
import uuid

# Import state management components
from app.services.crewai_flows.unified_discovery_flow.state_management import StateManager
from app.services.crewai_flows.unified_discovery_flow.flow_state_bridge import FlowStateBridge
from app.services.crewai_flows.handlers.unified_flow_management import UnifiedFlowManagement
from app.services.crewai_flows.unified_discovery_flow.flow_management import FlowManager
from app.services.crewai_flows.unified_discovery_flow.flow_finalization import FlowFinalizer
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState


class MockState:
    """Mock state object for testing"""

    def __init__(self):
        self.flow_id = str(uuid.uuid4())
        self.client_account_id = str(uuid.uuid4())
        self.engagement_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.current_phase = "initialization"
        self.progress_percentage = 0.0
        self.status = "running"
        self.phase_data = {}
        self.phase_completion = {}
        self.errors = []
        self.warnings = []
        self.agent_insights = []
        self.raw_data = []
        self.field_mappings = {}
        self.cleaned_data = []
        self.asset_inventory = {}
        self.dependencies = []
        self.tech_debt_analysis = {}
        self.started_at = datetime.now().isoformat()
        self.completed_at = None

    def add_error(self, phase: str, error: str, details: Dict = None):
        """Add error to state"""
        self.errors.append({
            "phase": phase,
            "error": error,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })

    def add_warning(self, phase: str, warning: str):
        """Add warning to state"""
        self.warnings.append({
            "phase": phase,
            "warning": warning,
            "timestamp": datetime.now().isoformat()
        })

    def add_agent_insight(self, agent_name: str, insight: str, confidence: float = 0.8):
        """Add agent insight to state"""
        self.agent_insights.append({
            "agent": agent_name,
            "insight": insight,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        })


class MockFlowBridge:
    """Mock flow bridge for testing"""

    def __init__(self):
        self.state_updates = []
        self.recovered_states = {}

    async def sync_state_update(self, state, phase_name: str, crew_results: Any = None):
        """Mock state sync"""
        self.state_updates.append({
            "phase": phase_name,
            "state": state,
            "results": crew_results,
            "timestamp": datetime.now().isoformat()
        })

    async def recover_flow_state(self, flow_id: str):
        """Mock state recovery"""
        return self.recovered_states.get(flow_id)

    async def persist_flow_state(self, state):
        """Mock state persistence"""
        self.recovered_states[state.flow_id] = state


@pytest.fixture
def mock_state():
    """Create mock state for testing"""
    return MockState()


@pytest.fixture
def mock_flow_bridge():
    """Create mock flow bridge for testing"""
    return MockFlowBridge()


@pytest.fixture
def sample_phase_results():
    """Sample phase results for testing"""
    return {
        "data_import": {
            "is_valid": True,
            "file_analysis": {"detected_type": "CSV", "confidence": 0.95},
            "validated_data": [{"hostname": "server-01", "ip": "192.168.1.10"}]
        },
        "field_mapping": {
            "field_mappings": {
                "hostname": {"target_field": "server_name", "confidence": 0.95}
            },
            "mapping_summary": {"total_fields": 5, "mapped_fields": 4}
        },
        "data_cleansing": {
            "cleaned_data": [{"id": 1, "hostname": "server-01", "ip": "192.168.1.10"}],
            "quality_metrics": {"data_quality_score": 0.95}
        }
    }


class TestStateManager:
    """Test StateManager functionality"""

    @pytest.fixture
    def state_manager(self, mock_state, mock_flow_bridge):
        """Create state manager instance"""
        return StateManager(mock_state, mock_flow_bridge)

    def test_initialization(self, state_manager, mock_state, mock_flow_bridge):
        """Test state manager initialization"""
        assert state_manager.state == mock_state
        assert state_manager.flow_bridge == mock_flow_bridge

    def test_store_phase_result(self, state_manager, sample_phase_results):
        """Test storing phase results"""
        phase_name = "data_import"
        result = sample_phase_results["data_import"]

        state_manager._store_phase_result(phase_name, result)

        assert state_manager.state.phase_data[phase_name] == result
        assert state_manager.state.phase_completion[phase_name] is True

    def test_store_validation_results(self, state_manager, sample_phase_results):
        """Test storing validation results"""
        result = sample_phase_results["data_import"]

        state_manager._store_validation_results(result)

        assert state_manager.state.data_validation_results == result
        assert state_manager.state.phase_completion["data_import"] is True

    def test_store_field_mapping_results(self, state_manager, sample_phase_results):
        """Test storing field mapping results"""
        result = sample_phase_results["field_mapping"]

        state_manager._store_field_mapping_results(result)

        assert state_manager.state.field_mappings == result["field_mappings"]
        assert state_manager.state.phase_completion["attribute_mapping"] is True

    def test_store_cleansing_results(self, state_manager, sample_phase_results):
        """Test storing data cleansing results"""
        result = sample_phase_results["data_cleansing"]

        state_manager._store_cleansing_results(result)

        assert state_manager.state.cleaned_data == result["cleaned_data"]
        assert state_manager.state.data_quality_metrics == result["quality_metrics"]
        assert state_manager.state.phase_completion["data_cleansing"] is True

    def test_store_inventory_results(self, state_manager):
        """Test storing inventory results"""
        result = {
            "assets_created": 5,
            "asset_types": ["server", "database"],
            "inventory_summary": {"total_assets": 5}
        }

        state_manager._store_inventory_results(result)

        assert state_manager.state.asset_inventory == result
        assert state_manager.state.phase_completion["asset_inventory"] is True

    def test_store_dependency_results(self, state_manager):
        """Test storing dependency results"""
        result = {
            "dependencies": [{"source": "app-1", "target": "db-1", "type": "database"}],
            "summary": {"total_dependencies": 1}
        }

        state_manager._store_dependency_results(result)

        assert state_manager.state.dependencies == result["dependencies"]
        assert state_manager.state.phase_completion["dependency_analysis"] is True

    def test_store_tech_debt_results(self, state_manager):
        """Test storing tech debt results"""
        result = {
            "tech_debt_analysis": {"risk_score": 0.75, "effort_estimate": "medium"},
            "debt_categories": {"legacy_technologies": 3}
        }

        state_manager._store_tech_debt_results(result)

        assert state_manager.state.tech_debt_analysis == result["tech_debt_analysis"]
        assert state_manager.state.phase_completion["tech_debt_assessment"] is True

    def test_add_error(self, state_manager):
        """Test adding errors to state"""
        phase = "data_import"
        error = "Validation failed"
        details = {"field": "hostname", "reason": "invalid_format"}

        state_manager.add_error(phase, error, details)

        assert len(state_manager.state.errors) == 1
        assert state_manager.state.errors[0]["phase"] == phase
        assert state_manager.state.errors[0]["error"] == error
        assert state_manager.state.errors[0]["details"] == details
        assert "timestamp" in state_manager.state.errors[0]

    def test_add_warning(self, state_manager):
        """Test adding warnings to state"""
        phase = "field_mapping"
        warning = "Low confidence mapping detected"

        state_manager.add_warning(phase, warning)

        assert len(state_manager.state.warnings) == 1
        assert state_manager.state.warnings[0]["phase"] == phase
        assert state_manager.state.warnings[0]["warning"] == warning
        assert "timestamp" in state_manager.state.warnings[0]

    def test_add_agent_insight(self, state_manager):
        """Test adding agent insights to state"""
        agent_name = "DataValidator"
        insight = "High quality data detected"
        confidence = 0.95

        state_manager.add_agent_insight(agent_name, insight, confidence)

        assert len(state_manager.state.agent_insights) == 1
        assert state_manager.state.agent_insights[0]["agent"] == agent_name
        assert state_manager.state.agent_insights[0]["insight"] == insight
        assert state_manager.state.agent_insights[0]["confidence"] == confidence
        assert "timestamp" in state_manager.state.agent_insights[0]

    @pytest.mark.asyncio
    async def test_safe_update_flow_state(self, state_manager):
        """Test safe flow state updates"""
        with patch.object(state_manager.flow_bridge, 'sync_state_update') as mock_sync:
            await state_manager.safe_update_flow_state()

            # Should sync current state
            mock_sync.assert_called_once()
            call_args = mock_sync.call_args
            assert call_args[0][0] == state_manager.state
            assert call_args[0][1] == state_manager.state.current_phase


class TestFlowStateBridge:
    """Test FlowStateBridge functionality"""

    @pytest.fixture
    def mock_context(self):
        """Create mock context"""
        context = Mock()
        context.client_account_id = str(uuid.uuid4())
        context.engagement_id = str(uuid.uuid4())
        context.user_id = str(uuid.uuid4())
        return context

    @pytest.fixture
    def flow_bridge(self, mock_context):
        """Create flow bridge instance"""
        return FlowStateBridge(mock_context)

    def test_initialization(self, flow_bridge, mock_context):
        """Test flow bridge initialization"""
        assert flow_bridge.context == mock_context
        assert flow_bridge.client_account_id == mock_context.client_account_id
        assert flow_bridge.engagement_id == mock_context.engagement_id
        assert flow_bridge.user_id == mock_context.user_id

    @pytest.mark.asyncio
    async def test_sync_state_update(self, flow_bridge, mock_state):
        """Test state synchronization"""
        phase_name = "data_import"
        crew_results = {"status": "success"}

        with patch.object(flow_bridge, '_persist_state_to_database') as mock_persist:
            await flow_bridge.sync_state_update(mock_state, phase_name, crew_results)

            mock_persist.assert_called_once_with(mock_state)

    @pytest.mark.asyncio
    async def test_recover_flow_state(self, flow_bridge):
        """Test flow state recovery"""
        flow_id = str(uuid.uuid4())

        with patch.object(flow_bridge, '_load_state_from_database') as mock_load:
            mock_load.return_value = None
            result = await flow_bridge.recover_flow_state(flow_id)

            assert result is None
            mock_load.assert_called_once_with(flow_id)

    @pytest.mark.asyncio
    async def test_persist_flow_state(self, flow_bridge, mock_state):
        """Test flow state persistence"""
        with patch.object(flow_bridge, '_persist_state_to_database') as mock_persist:
            await flow_bridge.persist_flow_state(mock_state)

            mock_persist.assert_called_once_with(mock_state)


class TestUnifiedFlowManagement:
    """Test UnifiedFlowManagement functionality"""

    @pytest.fixture
    def flow_management(self, mock_state):
        """Create flow management instance"""
        return UnifiedFlowManagement(mock_state)

    def test_initialization(self, flow_management, mock_state):
        """Test flow management initialization"""
        assert flow_management.state == mock_state

    @pytest.mark.asyncio
    async def test_start_flow(self, flow_management):
        """Test starting a flow"""
        flow_config = {
            "flow_type": "discovery",
            "client_account_id": str(uuid.uuid4()),
            "engagement_id": str(uuid.uuid4())
        }

        result = await flow_management.start_flow(flow_config)

        assert result["status"] == "started"
        assert result["flow_id"] == flow_management.state.flow_id
        assert flow_management.state.status == "running"
        assert flow_management.state.current_phase == "initialization"

    @pytest.mark.asyncio
    async def test_pause_flow(self, flow_management):
        """Test pausing a flow"""
        reason = "User requested pause"

        result = await flow_management.pause_flow(reason)

        assert result["status"] == "paused"
        assert result["reason"] == reason
        assert flow_management.state.status == "paused"

    @pytest.mark.asyncio
    async def test_resume_flow(self, flow_management):
        """Test resuming a flow"""
        resume_context = {
            "current_phase": "data_import",
            "progress_percentage": 16.67
        }

        result = await flow_management.resume_flow(resume_context)

        assert result["status"] == "resumed"
        assert flow_management.state.status == "running"
        assert flow_management.state.current_phase == "data_import"
        assert flow_management.state.progress_percentage == 16.67

    @pytest.mark.asyncio
    async def test_complete_flow(self, flow_management):
        """Test completing a flow"""
        final_results = {
            "total_phases": 6,
            "completed_phases": 6,
            "success_rate": 1.0
        }

        result = await flow_management.complete_flow(final_results)

        assert result["status"] == "completed"
        assert flow_management.state.status == "completed"
        assert flow_management.state.completed_at is not None
        assert flow_management.state.progress_percentage == 100.0

    @pytest.mark.asyncio
    async def test_fail_flow(self, flow_management):
        """Test failing a flow"""
        error_message = "Critical error occurred"
        error_details = {"phase": "data_cleansing", "error_code": "CLEANSING_FAILED"}

        result = await flow_management.fail_flow(error_message, error_details)

        assert result["status"] == "failed"
        assert result["error"] == error_message
        assert flow_management.state.status == "failed"
        assert len(flow_management.state.errors) == 1
        assert flow_management.state.errors[0]["error"] == error_message


class TestFlowManager:
    """Test FlowManager functionality"""

    @pytest.fixture
    def state_manager(self, mock_state, mock_flow_bridge):
        """Create state manager"""
        return StateManager(mock_state, mock_flow_bridge)

    @pytest.fixture
    def flow_management(self, mock_state):
        """Create flow management"""
        return UnifiedFlowManagement(mock_state)

    @pytest.fixture
    def flow_manager(self, mock_state, state_manager, flow_management):
        """Create flow manager"""
        return FlowManager(mock_state, state_manager, flow_management)

    def test_initialization(self, flow_manager, mock_state, state_manager, flow_management):
        """Test flow manager initialization"""
        assert flow_manager.state == mock_state
        assert flow_manager.state_manager == state_manager
        assert flow_manager.flow_management == flow_management

    @pytest.mark.asyncio
    async def test_pause_flow(self, flow_manager):
        """Test pausing flow through manager"""
        reason = "Maintenance required"

        result = await flow_manager.pause_flow(reason)

        assert result["status"] == "paused"
        assert result["reason"] == reason

    @pytest.mark.asyncio
    async def test_resume_flow_from_state(self, flow_manager):
        """Test resuming flow from state"""
        resume_context = {
            "current_phase": "field_mapping",
            "progress_percentage": 33.33,
            "phase_data": {"data_import": {"status": "completed"}}
        }

        result = await flow_manager.resume_flow_from_state(resume_context)

        assert result["status"] == "resumed"
        assert flow_manager.state.current_phase == "field_mapping"
        assert flow_manager.state.progress_percentage == 33.33

    def test_get_flow_info(self, flow_manager):
        """Test getting flow information"""
        info = flow_manager.get_flow_info()

        assert info["flow_id"] == flow_manager.state.flow_id
        assert info["status"] == flow_manager.state.status
        assert info["current_phase"] == flow_manager.state.current_phase
        assert info["progress_percentage"] == flow_manager.state.progress_percentage
        assert info["client_account_id"] == flow_manager.state.client_account_id
        assert info["engagement_id"] == flow_manager.state.engagement_id


class TestFlowFinalizer:
    """Test FlowFinalizer functionality"""

    @pytest.fixture
    def state_manager(self, mock_state, mock_flow_bridge):
        """Create state manager"""
        return StateManager(mock_state, mock_flow_bridge)

    @pytest.fixture
    def flow_finalizer(self, mock_state, state_manager):
        """Create flow finalizer"""
        return FlowFinalizer(mock_state, state_manager)

    def test_initialization(self, flow_finalizer, mock_state, state_manager):
        """Test flow finalizer initialization"""
        assert flow_finalizer.state == mock_state
        assert flow_finalizer.state_manager == state_manager

    @pytest.mark.asyncio
    async def test_finalize_flow_success(self, flow_finalizer):
        """Test successful flow finalization"""
        final_results = {
            "total_assets": 100,
            "total_dependencies": 50,
            "migration_readiness": "high",
            "recommended_strategy": "hybrid_approach"
        }

        result = await flow_finalizer.finalize_flow(final_results)

        assert result["status"] == "completed"
        assert result["final_results"] == final_results
        assert flow_finalizer.state.status == "completed"
        assert flow_finalizer.state.completed_at is not None
        assert flow_finalizer.state.progress_percentage == 100.0

    @pytest.mark.asyncio
    async def test_finalize_flow_with_errors(self, flow_finalizer):
        """Test flow finalization with errors"""
        final_results = {
            "total_assets": 100,
            "total_dependencies": 50,
            "errors": ["Phase 3 failed", "Data quality issues"],
            "warnings": ["Low confidence mappings"]
        }

        result = await flow_finalizer.finalize_flow(final_results)

        assert result["status"] == "completed_with_issues"
        assert result["final_results"] == final_results
        assert len(flow_finalizer.state.errors) > 0
        assert len(flow_finalizer.state.warnings) > 0

    @pytest.mark.asyncio
    async def test_generate_final_report(self, flow_finalizer):
        """Test generating final report"""
        final_results = {
            "total_assets": 100,
            "total_dependencies": 50,
            "migration_readiness": "high"
        }

        report = await flow_finalizer.generate_final_report(final_results)

        assert "flow_summary" in report
        assert "phase_results" in report
        assert "recommendations" in report
        assert report["flow_summary"]["total_assets"] == 100
        assert report["flow_summary"]["total_dependencies"] == 50
        assert report["flow_summary"]["migration_readiness"] == "high"


class TestStateManagementIntegration:
    """Test integration between state management components"""

    @pytest.mark.asyncio
    async def test_complete_flow_lifecycle(self, mock_state, mock_flow_bridge):
        """Test complete flow lifecycle with state management"""
        # Initialize components
        state_manager = StateManager(mock_state, mock_flow_bridge)
        flow_management = UnifiedFlowManagement(mock_state)
        flow_manager = FlowManager(mock_state, state_manager, flow_management)
        flow_finalizer = FlowFinalizer(mock_state, state_manager)

        # Start flow
        flow_config = {
            "flow_type": "discovery",
            "client_account_id": mock_state.client_account_id,
            "engagement_id": mock_state.engagement_id
        }

        start_result = await flow_management.start_flow(flow_config)
        assert start_result["status"] == "started"

        # Simulate phase completions
        phase_results = {
            "data_import": {"is_valid": True, "validated_data": []},
            "field_mapping": {"field_mappings": {}, "status": "success"},
            "data_cleansing": {"cleaned_data": [], "quality_metrics": {}},
            "asset_inventory": {"assets_created": 5},
            "dependency_analysis": {"dependencies": []},
            "tech_debt_assessment": {"risk_score": 0.75}
        }

        for phase, result in phase_results.items():
            state_manager._store_phase_result(phase, result)

        # Complete flow
        final_results = {
            "total_assets": 5,
            "total_dependencies": 3,
            "migration_readiness": "medium"
        }

        final_result = await flow_finalizer.finalize_flow(final_results)

        assert final_result["status"] == "completed"
        assert mock_state.status == "completed"
        assert mock_state.progress_percentage == 100.0
        assert all(mock_state.phase_completion.values())

    @pytest.mark.asyncio
    async def test_error_recovery_flow(self, mock_state, mock_flow_bridge):
        """Test error recovery flow"""
        state_manager = StateManager(mock_state, mock_flow_bridge)
        flow_management = UnifiedFlowManagement(mock_state)

        # Start flow
        await flow_management.start_flow({"flow_type": "discovery"})

        # Add error
        state_manager.add_error("data_cleansing", "Cleansing failed", {"reason": "invalid_data"})

        # Pause flow
        await flow_management.pause_flow("Error recovery")

        # Resume with fixed state
        resume_context = {
            "current_phase": "data_cleansing",
            "progress_percentage": 33.33,
            "skip_failed_phase": True
        }

        resume_result = await flow_management.resume_flow(resume_context)

        assert resume_result["status"] == "resumed"
        assert mock_state.status == "running"
        assert len(mock_state.errors) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
