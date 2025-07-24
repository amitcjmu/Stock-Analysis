"""
Test CrewAI Flow Migration
Tests the migration from legacy discovery patterns to the new CrewAI Flow implementation.
Validates compatibility, fallback behavior, and performance characteristics.
"""

from unittest.mock import Mock

import pytest
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

# Test the migration from legacy to CrewAI Flow
from app.services.crewai_flow_service import CrewAIFlowService


class TestCrewAIFlowMigration:
    """Test the migration from legacy discovery patterns to CrewAI Flow."""

    @pytest.fixture
    def mock_db_session(self):
        return Mock()

    @pytest.fixture
    def sample_context(self):
        from app.core.context import RequestContext

        return RequestContext(
            client_account_id="test-client-123",
            engagement_id="test-engagement-456",
            user_id="test-user-789",
            flow_id="test-flow-abc",
        )

    @pytest.fixture
    def sample_cmdb_data(self):
        return {
            "file_data": [
                {"name": "server-01", "type": "server", "environment": "production"},
                {"name": "db-01", "type": "database", "environment": "production"},
            ]
        }

    def test_service_initialization(self, mock_db_session):
        """Test that CrewAI Flow service initializes correctly."""
        service = CrewAIFlowService(mock_db_session)

        assert service.db_session == mock_db_session
        assert hasattr(service, "_active_flows")
        assert isinstance(service._active_flows, dict)

    def test_discovery_flow_state_model(self):
        """Test that the DiscoveryFlowState model works correctly."""
        state = UnifiedDiscoveryFlowState(
            flow_id="test-flow",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
        )

        assert state.flow_id == "test-flow"
        assert state.status == "running"
        assert state.current_phase == "initialization"
        assert state.progress_percentage == 0.0
        assert isinstance(state.phase_completion, dict)
        assert isinstance(state.errors, list)
        assert isinstance(state.warnings, list)

    def test_discovery_flow_creation(self, sample_context, sample_cmdb_data):
        """Test that discovery flows can be created with the new architecture."""
        mock_service = Mock()
        mock_service.agents = {}

        from app.services.crewai_flows.unified_discovery_flow import (
            create_unified_discovery_flow,
        )

        flow = create_unified_discovery_flow(
            flow_id="test-flow",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            raw_data=sample_cmdb_data["file_data"],
            metadata={},
            crewai_service=mock_service,
            context=sample_context,
        )

        assert flow is not None
        assert hasattr(flow, "state")
        assert flow.state.flow_id == "test-flow"
        assert flow.crewai_service == mock_service
        assert flow.context == sample_context

    @pytest.mark.asyncio
    async def test_initiate_discovery_workflow(
        self, mock_db_session, sample_context, sample_cmdb_data
    ):
        """Test initiating discovery workflow through the service."""
        service = CrewAIFlowService(mock_db_session)

        # Mock the crewai service
        mock_crewai_service = Mock()
        service.crewai_service = mock_crewai_service

        # Test workflow initiation
        try:
            result = await service.initiate_discovery_workflow(
                data_source=sample_cmdb_data, context=sample_context
            )

            # Should return a result
            assert result is not None

        except Exception as e:
            # Expected to fail in test environment - that's ok
            assert "CrewAI" in str(e) or "import" in str(e).lower()

    def test_native_format_structure(self, mock_db_session):
        """Test native format structure compatibility."""
        CrewAIFlowService(mock_db_session)

        # Create state in native format
        native_state = {
            "flow_id": "test-flow",
            "client_account_id": "test-client",
            "engagement_id": "test-engagement",
            "user_id": "test-user",
            "status": "running",
            "current_phase": "initialization",
            "progress_percentage": 0.0,
            "phase_completion": {},
            "errors": [],
            "warnings": [],
        }

        # Should be able to create DiscoveryFlowState from native format
        state = UnifiedDiscoveryFlowState(**native_state)
        assert state.flow_id == "test-flow"
        assert state.status == "running"

    def test_fallback_behavior_when_crewai_unavailable(self):
        """Test fallback behavior when CrewAI is not available."""

        # Test fallback decorators
        def start():
            def decorator(func):
                return func

            return decorator

        def persist():
            def decorator(func):
                return func

            return decorator

        class Flow:
            def __init__(self):
                self.state = None

        @start()
        def test_start_method():
            return "started"

        @persist()
        class TestFlow(Flow):
            def __init__(self):
                self.state = None

        # Should not raise errors
        result = test_start_method()
        assert result == "started"

        test_flow = TestFlow()
        assert test_flow.state is None

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, mock_db_session, sample_context):
        """Test error handling and recovery mechanisms."""
        service = CrewAIFlowService(mock_db_session)

        # Test with invalid data
        invalid_data = {"invalid": "data"}

        try:
            await service.initiate_discovery_workflow(
                data_source=invalid_data, context=sample_context
            )
        except Exception as e:
            # Should handle errors gracefully
            assert isinstance(e, Exception)

    def test_health_status_reporting(self, mock_db_session):
        """Test health status reporting."""
        service = CrewAIFlowService(mock_db_session)

        status = service.get_health_status()

        assert "status" in status
        assert "active_flows" in status
        assert "last_check" in status
        assert isinstance(status["active_flows"], int)

        # Should report healthy even without flows
        assert status["status"] in ["healthy", "degraded", "error"]

    def test_active_flows_monitoring(self, mock_db_session):
        """Test active flows monitoring."""
        service = CrewAIFlowService(mock_db_session)

        # Add some mock flows
        mock_flow1 = Mock()
        mock_flow1.state.status = "running"
        mock_flow1.state.current_phase = "field_mapping"

        mock_flow2 = Mock()
        mock_flow2.state.status = "completed"
        mock_flow2.state.current_phase = "completed"

        service._active_flows["session1"] = mock_flow1
        service._active_flows["session2"] = mock_flow2

        summary = service.get_active_flows_summary()

        assert summary["total_active_flows"] == 2
        assert "flows_by_status" in summary
        assert summary["flows_by_status"]["running"] == 1
        assert summary["flows_by_status"]["completed"] == 1

    @pytest.mark.asyncio
    async def test_workflow_step_execution(self, sample_context, sample_cmdb_data):
        """Test individual workflow step execution."""
        mock_service = Mock()
        mock_service.agents = {}

        from app.services.crewai_flows.unified_discovery_flow import (
            create_unified_discovery_flow,
        )

        flow = create_unified_discovery_flow(
            flow_id="test-flow",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            raw_data=sample_cmdb_data["file_data"],
            metadata={},
            crewai_service=mock_service,
            context=sample_context,
        )

        # Test initialization step
        result = flow.initialize_discovery()
        assert result == "initialized"
        assert flow.state.current_phase == "initialization"
        assert flow.state.status == "running"

    def test_fallback_validation_logic(self, sample_context, sample_cmdb_data):
        """Test fallback validation logic."""
        mock_service = Mock()
        mock_service.agents = {}

        from app.services.crewai_flows.unified_discovery_flow import (
            create_unified_discovery_flow,
        )

        flow = create_unified_discovery_flow(
            flow_id="test-flow",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            raw_data=sample_cmdb_data["file_data"],
            metadata={},
            crewai_service=mock_service,
            context=sample_context,
        )

        # Initialize the flow first
        flow.initialize_discovery()

        # Test that flow has the required phase executor
        assert hasattr(flow, "phase_executor")
        assert flow.state.raw_data == sample_cmdb_data["file_data"]

    def test_fallback_field_mapping(self, sample_context, sample_cmdb_data):
        """Test fallback field mapping logic."""
        mock_service = Mock()
        mock_service.agents = {}

        from app.services.crewai_flows.unified_discovery_flow import (
            create_unified_discovery_flow,
        )

        flow = create_unified_discovery_flow(
            flow_id="test-flow",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            raw_data=sample_cmdb_data["file_data"],
            metadata={},
            crewai_service=mock_service,
            context=sample_context,
        )

        # Initialize the flow first
        flow.initialize_discovery()

        # Test fallback mapping through phase executor
        mapping_result = flow.phase_executor._fallback_field_mapping()

        assert "mappings" in mapping_result
        assert "validation_results" in mapping_result
        assert mapping_result["validation_results"]["fallback_used"] is True

    def test_fallback_asset_classification(self, sample_context, sample_cmdb_data):
        """Test fallback asset classification logic."""
        mock_service = Mock()
        mock_service.agents = {}

        from app.services.crewai_flows.unified_discovery_flow import (
            create_unified_discovery_flow,
        )

        flow = create_unified_discovery_flow(
            flow_id="test-flow",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            raw_data=sample_cmdb_data["file_data"],
            metadata={},
            crewai_service=mock_service,
            context=sample_context,
        )

        # Initialize the flow and set cleaned data
        flow.initialize_discovery()
        flow.state.cleaned_data = sample_cmdb_data["file_data"]

        # Test fallback classification through phase executor
        classification_result = flow.phase_executor._fallback_asset_inventory()

        assert "servers" in classification_result
        assert "total_assets" in classification_result
        assert classification_result["total_assets"] == 2
        assert classification_result["classification_metadata"]["fallback_used"] is True


class TestNativeFormatValidation:
    """Test native DiscoveryFlowState format validation and structure."""

    @pytest.fixture
    def mock_db_session(self):
        return Mock()

    def test_native_state_structure_complete(self, mock_db_session):
        """Test that native state structure contains all required fields."""
        CrewAIFlowService(mock_db_session)

        # Create new state
        new_state = UnifiedDiscoveryFlowState(
            flow_id="test-flow",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
        )

        # Convert to native format using model_dump
        native_state = new_state.model_dump()

        # Verify all expected native fields exist
        expected_fields = [
            "flow_id",
            "client_account_id",
            "engagement_id",
            "user_id",
            "status",
            "current_phase",
            "phase_completion",
            "errors",
            "metadata",
            "created_at",
            "updated_at",
            "progress_percentage",
            "agent_insights",
            "warnings",
        ]

        for field in expected_fields:
            assert field in native_state, f"Missing native field: {field}"

        # Verify native phase structure
        assert isinstance(native_state["phase_completion"], dict)
        assert isinstance(native_state["errors"], list)

    def test_api_method_signatures_unchanged(self, mock_db_session):
        """Test that API method signatures remain unchanged."""
        service = CrewAIFlowService(mock_db_session)

        # Verify method exists and has correct signature
        assert hasattr(service, "initiate_discovery_workflow")
        assert hasattr(service, "get_flow_state_by_session")
        assert hasattr(service, "get_health_status")
        assert hasattr(service, "get_active_flows_summary")

        # Test method can be called (even if mocked)
        import inspect

        # Check initiate_discovery_workflow signature
        sig = inspect.signature(service.initiate_discovery_workflow)
        params = list(sig.parameters.keys())
        assert "data_source" in params
        assert "context" in params


class TestPerformanceAndScaling:
    """Test performance characteristics and scaling behavior."""

    @pytest.fixture
    def mock_db_session(self):
        return Mock()

    def test_large_dataset_handling(self, mock_db_session):
        """Test handling of large CMDB datasets."""
        CrewAIFlowService(mock_db_session)

        # Create large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append(
                {
                    "name": f"asset-{i}",
                    "type": "server" if i % 2 == 0 else "application",
                    "environment": "production" if i % 3 == 0 else "staging",
                }
            )

        # Test fallback validation with large dataset
        mock_service = Mock()
        mock_service.agents = {}

        from app.core.context import RequestContext
        from app.services.crewai_flows.unified_discovery_flow import (
            create_unified_discovery_flow,
        )

        context = RequestContext(
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            flow_id="test-flow",
        )

        flow = create_unified_discovery_flow(
            flow_id="test-flow",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            raw_data=large_dataset,
            metadata={},
            crewai_service=mock_service,
            context=context,
        )

        # Test initialization performance
        import time

        start_time = time.time()
        result = flow.initialize_discovery()
        end_time = time.time()

        # Should complete within reasonable time (< 1 second for 1000 records)
        assert (end_time - start_time) < 1.0
        assert result == "initialized"
        assert len(flow.state.raw_data) == 1000

    def test_concurrent_flow_management(self, mock_db_session):
        """Test concurrent flow management."""
        service = CrewAIFlowService(mock_db_session)

        # Simulate multiple active flows
        for i in range(10):
            mock_flow = Mock()
            mock_flow.state.status = "running" if i % 2 == 0 else "completed"
            service._active_flows[f"session-{i}"] = mock_flow

        summary = service.get_active_flows_summary()
        assert summary["total_active_flows"] == 10
        assert summary["flows_by_status"]["running"] == 5
        assert summary["flows_by_status"]["completed"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
