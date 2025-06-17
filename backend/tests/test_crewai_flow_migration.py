"""
CrewAI Flow Migration Validation Tests
Tests the successful migration from legacy handlers to native CrewAI Flow patterns.

This test suite validates:
1. New CrewAI Flow service functionality
2. Backward compatibility with legacy API contracts
3. Fallback behavior when CrewAI Flow is unavailable
4. State management and persistence
5. Error handling and recovery
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any

# Test imports
from app.services.crewai_flow_service import CrewAIFlowService
from app.services.crewai_flows.discovery_flow import (
    DiscoveryFlow, 
    DiscoveryFlowState, 
    create_discovery_flow,
    CREWAI_FLOW_AVAILABLE
)
from app.core.context import RequestContext
from app.schemas.flow_schemas import DiscoveryFlowState as LegacyDiscoveryFlowState


class TestCrewAIFlowMigration:
    """Test suite for CrewAI Flow migration validation."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def sample_context(self):
        """Sample request context for testing."""
        return RequestContext(
            client_account_id="test-client-123",
            engagement_id="test-engagement-456",
            user_id="test-user-789",
            session_id="test-session-abc"
        )
    
    @pytest.fixture
    def sample_cmdb_data(self):
        """Sample CMDB data for testing."""
        return {
            "file_data": [
                {
                    "name": "web-server-01",
                    "type": "server",
                    "environment": "production"
                },
                {
                    "name": "customer-db", 
                    "type": "database",
                    "environment": "production"
                }
            ],
            "metadata": {
                "source": "test_upload",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def test_service_initialization(self, mock_db_session):
        """Test that the new CrewAI Flow service initializes correctly."""
        service = CrewAIFlowService(mock_db_session)
        
        assert service.db == mock_db_session
        assert hasattr(service, 'state_service')
        assert hasattr(service, 'service_available')
        assert hasattr(service, '_active_flows')
        assert isinstance(service._active_flows, dict)
    
    def test_discovery_flow_state_model(self):
        """Test the DiscoveryFlowState model follows best practices."""
        state = DiscoveryFlowState(
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user"
        )
        
        # Test required fields
        assert state.session_id == "test-session"
        assert state.current_phase == "initialization"
        assert state.status == "running"
        assert state.progress_percentage == 0.0
        
        # Test methods
        state.add_error("test_phase", "test error")
        assert len(state.errors) == 1
        
        state.mark_phase_complete("data_validation", {"result": "success"})
        assert state.phases_completed["data_validation"] is True
        assert state.progress_percentage == 20.0  # 1/5 phases complete
    
    def test_discovery_flow_creation(self, sample_context, sample_cmdb_data):
        """Test discovery flow creation with proper state initialization."""
        mock_service = Mock()
        mock_service.agents = {}
        
        flow = create_discovery_flow(
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement", 
            user_id="test-user",
            cmdb_data=sample_cmdb_data,
            metadata={"test": "metadata"},
            crewai_service=mock_service,
            context=sample_context
        )
        
        assert isinstance(flow, DiscoveryFlow)
        assert flow.state.session_id == "test-session"
        assert flow.state.cmdb_data == sample_cmdb_data
        assert flow.crewai_service == mock_service
        assert flow.context == sample_context
    
    @pytest.mark.asyncio
    async def test_initiate_discovery_workflow(self, mock_db_session, sample_context, sample_cmdb_data):
        """Test the main workflow initiation method."""
        with patch('app.services.crewai_flow_service.WorkflowStateService'):
            service = CrewAIFlowService(mock_db_session)
            
            # Mock the create_discovery_flow function
            with patch('app.services.crewai_flow_service.create_discovery_flow') as mock_create:
                mock_flow = Mock()
                mock_flow.state = DiscoveryFlowState(
                    session_id="test-session",
                    client_account_id="test-client",
                    engagement_id="test-engagement",
                    user_id="test-user"
                )
                mock_create.return_value = mock_flow
                
                # Mock asyncio.create_task to avoid actual background execution
                with patch('asyncio.create_task'):
                    result = await service.initiate_discovery_workflow(
                        sample_cmdb_data, sample_context
                    )
                
                # Verify result structure
                assert "session_id" in result
                assert "client_account_id" in result
                assert "status" in result
                assert "current_phase" in result
                
                # Verify flow was created and stored
                mock_create.assert_called_once()
                assert "test-session" in service._active_flows or len(service._active_flows) > 0
    
    def test_native_format_structure(self, mock_db_session):
        """Test that the service returns native DiscoveryFlowState format."""
        service = CrewAIFlowService(mock_db_session)
        
        # Create a test state
        new_state = DiscoveryFlowState(
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user"
        )
        new_state.mark_phase_complete("data_validation", {"records": 100})
        
        # Convert to native format using model_dump
        native_format = new_state.model_dump()
        
        # Verify native structure
        assert native_format["session_id"] == "test-session"
        assert native_format["status"] == "running"
        assert native_format["phases_completed"]["data_validation"] is True
        assert native_format["results"]["data_validation"]["records"] == 100
    
    def test_fallback_behavior_when_crewai_unavailable(self):
        """Test that the system works correctly when CrewAI Flow is not available."""
        from app.services.crewai_flows.discovery_flow import Flow, start, listen, persist
        
        # Test mock decorators
        @start()
        def test_start_method():
            return "started"
        
        @persist()
        class TestFlow(Flow):
            def __init__(self):
                super().__init__()
        
        # Verify mock behavior
        assert callable(test_start_method)
        
        # Test Flow subscripting works
        flow_instance = TestFlow()
        assert hasattr(flow_instance, 'kickoff')
        assert flow_instance.kickoff() == "completed"
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, mock_db_session, sample_context):
        """Test error handling in the workflow."""
        service = CrewAIFlowService(mock_db_session)
        
        # Test with invalid data
        invalid_data = {"file_data": None}
        
        result = await service.initiate_discovery_workflow(invalid_data, sample_context)
        
        assert result["status"] == "error"
        assert "message" in result
    
    def test_health_status_reporting(self, mock_db_session):
        """Test service health status reporting."""
        service = CrewAIFlowService(mock_db_session)
        
        health = service.get_health_status()
        
        assert health["service_name"] == "CrewAI Flow Service"
        assert "status" in health
        assert "features" in health
        
        # Verify features
        features = health["features"]
        assert "fallback_execution" in features
        assert "state_persistence" in features
    
    def test_active_flows_monitoring(self, mock_db_session):
        """Test active flows monitoring and summary."""
        service = CrewAIFlowService(mock_db_session)
        
        # Add some mock active flows
        mock_flow1 = Mock()
        mock_flow1.state.status = "running"
        mock_flow2 = Mock()
        mock_flow2.state.status = "completed"
        
        service._active_flows["session1"] = mock_flow1
        service._active_flows["session2"] = mock_flow2
        
        summary = service.get_active_flows_summary()
        
        assert summary["total_active_flows"] == 2
        assert "session1" in summary["active_sessions"]
        assert "session2" in summary["active_sessions"]
        assert summary["flows_by_status"]["running"] == 1
        assert summary["flows_by_status"]["completed"] == 1
        assert "service_available" in summary
        assert "timestamp" in summary
    
    @pytest.mark.asyncio
    async def test_workflow_step_execution(self, sample_context, sample_cmdb_data):
        """Test individual workflow step execution."""
        mock_service = Mock()
        mock_service.agents = {}
        
        flow = create_discovery_flow(
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            cmdb_data=sample_cmdb_data,
            metadata={},
            crewai_service=mock_service,
            context=sample_context
        )
        
        # Test initialization step
        result = flow.initialize_discovery()
        assert result == "initialized"
        assert flow.state.current_phase == "initialization"
        
        # Test data validation step
        result = flow.validate_data_quality("initialized")
        assert result == "validation_completed"
        assert flow.state.phases_completed["data_validation"] is True
        
        # Test field mapping step
        result = flow.map_source_fields("validation_completed")
        assert result == "mapping_completed"
        assert flow.state.phases_completed["field_mapping"] is True
    
    def test_fallback_validation_logic(self, sample_context, sample_cmdb_data):
        """Test fallback validation when agents are not available."""
        mock_service = Mock()
        mock_service.agents = {}
        
        flow = create_discovery_flow(
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            cmdb_data=sample_cmdb_data,
            metadata={},
            crewai_service=mock_service,
            context=sample_context
        )
        
        # Test fallback validation
        validation_result = flow._perform_fallback_validation(sample_cmdb_data["file_data"])
        
        assert validation_result["total_records"] == 2
        assert validation_result["valid_records"] == 2
        assert validation_result["validation_rate"] == 100.0
        assert validation_result["method"] == "fallback_validation"
    
    def test_fallback_field_mapping(self, sample_context, sample_cmdb_data):
        """Test fallback field mapping logic."""
        mock_service = Mock()
        mock_service.agents = {}
        
        flow = create_discovery_flow(
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            cmdb_data=sample_cmdb_data,
            metadata={},
            crewai_service=mock_service,
            context=sample_context
        )
        
        # Test fallback mapping
        mapping_result = flow._perform_fallback_mapping(sample_cmdb_data["file_data"])
        
        assert "field_mappings" in mapping_result
        assert mapping_result["method"] == "fallback_mapping"
        assert mapping_result["total_fields"] > 0
        
        # Should map common fields
        mappings = mapping_result["field_mappings"]
        assert "name" in mappings or "type" in mappings
    
    def test_fallback_asset_classification(self, sample_context, sample_cmdb_data):
        """Test fallback asset classification logic."""
        mock_service = Mock()
        mock_service.agents = {}
        
        flow = create_discovery_flow(
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            cmdb_data=sample_cmdb_data,
            metadata={},
            crewai_service=mock_service,
            context=sample_context
        )
        
        # Test fallback classification
        field_mappings = {"type": "type", "name": "name"}
        classification_result = flow._perform_fallback_classification(
            sample_cmdb_data["file_data"], field_mappings
        )
        
        assert "classified_assets" in classification_result
        assert classification_result["total_assets"] == 2
        assert classification_result["method"] == "fallback_classification"
        
        # Check classification summary
        summary = classification_result["classification_summary"]
        assert "server" in summary
        assert "database" in summary
        
        # Verify assets have required fields
        assets = classification_result["classified_assets"]
        for asset in assets:
            assert "id" in asset
            assert "asset_type" in asset
            assert "migration_strategy" in asset
            assert "confidence" in asset


class TestNativeFormatValidation:
    """Test native DiscoveryFlowState format validation and structure."""
    
    @pytest.fixture
    def mock_db_session(self):
        return Mock()
    
    def test_native_state_structure_complete(self, mock_db_session):
        """Test that native state structure contains all required fields."""
        service = CrewAIFlowService(mock_db_session)
        
        # Create new state
        new_state = DiscoveryFlowState(
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user"
        )
        
        # Convert to native format using model_dump
        native_state = new_state.model_dump()
        
        # Verify all expected native fields exist
        expected_fields = [
            "session_id", "client_account_id", "engagement_id", "user_id",
            "status", "current_phase", "phases_completed", "results", "errors",
            "metadata", "started_at", "completed_at", "progress_percentage",
            "agent_insights", "recommendations", "warnings"
        ]
        
        for field in expected_fields:
            assert field in native_state, f"Missing native field: {field}"
        
        # Verify native phase structure
        assert isinstance(native_state["phases_completed"], dict)
        assert isinstance(native_state["results"], dict)
        assert isinstance(native_state["errors"], list)
    
    def test_api_method_signatures_unchanged(self, mock_db_session):
        """Test that API method signatures remain unchanged."""
        service = CrewAIFlowService(mock_db_session)
        
        # Verify method exists and has correct signature
        assert hasattr(service, 'initiate_discovery_workflow')
        assert hasattr(service, 'get_flow_state_by_session')
        assert hasattr(service, 'get_health_status')
        assert hasattr(service, 'get_active_flows_summary')
        
        # Test method can be called (even if mocked)
        import inspect
        
        # Check initiate_discovery_workflow signature
        sig = inspect.signature(service.initiate_discovery_workflow)
        params = list(sig.parameters.keys())
        assert 'data_source' in params
        assert 'context' in params


class TestPerformanceAndScaling:
    """Test performance characteristics and scaling behavior."""
    
    @pytest.fixture
    def mock_db_session(self):
        return Mock()
    
    def test_large_dataset_handling(self, mock_db_session):
        """Test handling of large CMDB datasets."""
        service = CrewAIFlowService(mock_db_session)
        
        # Create large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append({
                "name": f"asset-{i}",
                "type": "server" if i % 2 == 0 else "application",
                "environment": "production" if i % 3 == 0 else "staging"
            })
        
        # Test fallback validation with large dataset
        mock_service = Mock()
        mock_service.agents = {}
        
        from app.services.crewai_flows.discovery_flow import create_discovery_flow
        from app.core.context import RequestContext
        
        context = RequestContext(
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            session_id="test-session"
        )
        
        flow = create_discovery_flow(
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            cmdb_data={"file_data": large_dataset},
            metadata={},
            crewai_service=mock_service,
            context=context
        )
        
        # Test validation performance
        import time
        start_time = time.time()
        result = flow._perform_fallback_validation(large_dataset)
        end_time = time.time()
        
        # Should complete within reasonable time (< 5 seconds for 1000 records)
        assert (end_time - start_time) < 5.0
        assert result["total_records"] == 1000
        assert result["valid_records"] == 1000
    
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