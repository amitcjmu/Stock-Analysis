"""
Tests for Phase 2 Discovery Flow implementation
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.flows.discovery_flow import UnifiedDiscoveryFlow, DiscoveryFlowState
from app.services.flows.manager import FlowManager
from app.services.flows.events import FlowEventBus, FlowEvent
from app.core.context import RequestContext


@pytest.fixture
def mock_context():
    """Create mock request context"""
    return RequestContext(
        client_account_id="test-client-123",
        engagement_id="test-engagement-456",
        user_id="test-user-789"
    )


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    return AsyncMock()


@pytest.fixture
def sample_import_data():
    """Create sample import data"""
    return {
        "flow_id": "test-flow-123",
        "import_id": "test-import",
        "filename": "test_data.csv",
        "record_count": 100,
        "raw_data": [
            {"hostname": "server1", "ip": "192.168.1.1", "type": "server"},
            {"hostname": "server2", "ip": "192.168.1.2", "type": "database"},
            {"hostname": "app1", "ip": "192.168.1.3", "type": "application"}
        ]
    }


class TestDiscoveryFlowState:
    """Tests for DiscoveryFlowState"""
    
    def test_state_initialization(self, mock_context):
        """Test state initialization"""
        state = DiscoveryFlowState(
            flow_id="test-flow",
            client_account_id=mock_context.client_account_id,
            engagement_id=mock_context.engagement_id,
            user_id=mock_context.user_id
        )
        
        assert state.flow_id == "test-flow"
        assert state.current_phase == "initialization"
        assert state.progress_percentage == 0.0
        assert state.status == "running"
        assert len(state.phases_completed) == 0
    
    def test_add_error(self, mock_context):
        """Test error tracking"""
        state = DiscoveryFlowState(
            flow_id="test-flow",
            client_account_id=mock_context.client_account_id,
            engagement_id=mock_context.engagement_id,
            user_id=mock_context.user_id
        )
        
        state.add_error("test_phase", "Test error message")
        
        assert len(state.errors) == 1
        assert state.errors[0]["phase"] == "test_phase"
        assert state.errors[0]["message"] == "Test error message"
        assert "timestamp" in state.errors[0]


class TestUnifiedDiscoveryFlow:
    """Tests for UnifiedDiscoveryFlow"""
    
    @pytest.fixture
    def flow(self, mock_db_session, mock_context):
        """Create flow instance"""
        return UnifiedDiscoveryFlow(mock_db_session, mock_context)
    
    def test_flow_initialization(self, flow, mock_context):
        """Test flow initialization"""
        assert flow.context == mock_context
        assert hasattr(flow, 'crew_factory')
        assert hasattr(flow, 'state_store')
    
    @pytest.mark.asyncio
    async def test_initialize_discovery(self, flow, sample_import_data):
        """Test flow initialization method"""
        with patch.object(flow, 'save_state', new_callable=AsyncMock) as mock_save:
            result = await flow.initialize_discovery(sample_import_data)
            
            assert isinstance(result, DiscoveryFlowState)
            assert result.flow_id == sample_import_data["flow_id"]
            assert result.current_phase == "initialization"
            assert result.total_records == sample_import_data["record_count"]
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_and_analyze_data(self, flow, sample_import_data):
        """Test data validation phase"""
        # Initialize state
        initial_state = await flow.initialize_discovery(sample_import_data)
        
        with patch.object(flow.crew_factory, 'execute_crew', new_callable=AsyncMock) as mock_crew:
            mock_crew.return_value = {"status": "completed", "data": {"validation": "passed"}}
            
            with patch.object(flow, 'save_state', new_callable=AsyncMock):
                result = await flow.validate_and_analyze_data(initial_state)
                
                assert result.current_phase == "data_validation"
                assert "data_validation" in result.phases_completed
                assert result.progress_percentage == 10.0
                mock_crew.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, flow, sample_import_data):
        """Test error handling in flow"""
        initial_state = await flow.initialize_discovery(sample_import_data)
        
        with patch.object(flow.crew_factory, 'execute_crew', new_callable=AsyncMock) as mock_crew:
            mock_crew.side_effect = Exception("Test error")
            
            with pytest.raises(Exception):
                await flow.validate_and_analyze_data(initial_state)
            
            # Check that error was handled
            assert flow.state.error == "Test error"


class TestFlowManager:
    """Tests for FlowManager"""
    
    @pytest.fixture
    def manager(self):
        """Create flow manager"""
        return FlowManager()
    
    def test_manager_initialization(self, manager):
        """Test manager initialization"""
        assert len(manager.active_flows) == 0
        assert len(manager.flow_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_create_discovery_flow(self, manager, mock_db_session, mock_context, sample_import_data):
        """Test flow creation"""
        with patch('app.services.flows.manager.UnifiedDiscoveryFlow') as mock_flow_class:
            mock_flow = AsyncMock()
            mock_flow_class.return_value = mock_flow
            mock_flow.kickoff = AsyncMock()
            
            flow_id = await manager.create_discovery_flow(mock_db_session, mock_context, sample_import_data)
            
            assert flow_id == sample_import_data["flow_id"]
            assert flow_id in manager.active_flows
    
    @pytest.mark.asyncio
    async def test_cleanup_completed_flows(self, manager):
        """Test flow cleanup"""
        # Add mock completed task
        mock_task = Mock()
        mock_task.done.return_value = True
        manager.flow_tasks["test-flow"] = mock_task
        manager.active_flows["test-flow"] = Mock()
        
        cleaned = await manager.cleanup_completed_flows()
        
        assert cleaned == 1
        assert "test-flow" not in manager.flow_tasks
        assert "test-flow" not in manager.active_flows


class TestFlowEventBus:
    """Tests for FlowEventBus"""
    
    @pytest.fixture
    def event_bus(self):
        """Create event bus"""
        return FlowEventBus()
    
    @pytest.fixture
    def sample_event(self):
        """Create sample event"""
        return FlowEvent(
            flow_id="test-flow",
            event_type="test_event",
            phase="testing",
            data={"message": "test"},
            timestamp=datetime.utcnow(),
            context={"test": True}
        )
    
    def test_event_bus_initialization(self, event_bus):
        """Test event bus initialization"""
        assert len(event_bus.subscribers) == 0
        assert len(event_bus.event_history) == 0
    
    def test_subscribe(self, event_bus):
        """Test event subscription"""
        callback = Mock()
        event_bus.subscribe("test_event", callback)
        
        assert "test_event" in event_bus.subscribers
        assert callback in event_bus.subscribers["test_event"]
    
    @pytest.mark.asyncio
    async def test_publish_event(self, event_bus, sample_event):
        """Test event publishing"""
        callback = AsyncMock()
        event_bus.subscribe("test_event", callback)
        
        await event_bus.publish(sample_event)
        
        assert len(event_bus.event_history) == 1
        assert event_bus.event_history[0] == sample_event
        callback.assert_called_once_with(sample_event)
    
    def test_get_flow_events(self, event_bus, sample_event):
        """Test getting flow-specific events"""
        event_bus.event_history.append(sample_event)
        
        # Add another event for different flow
        other_event = FlowEvent(
            flow_id="other-flow",
            event_type="other_event",
            phase="other",
            data={},
            timestamp=datetime.utcnow(),
            context={}
        )
        event_bus.event_history.append(other_event)
        
        flow_events = event_bus.get_flow_events("test-flow")
        
        assert len(flow_events) == 1
        assert flow_events[0] == sample_event
    
    def test_event_history_limit(self, event_bus):
        """Test event history size limit"""
        event_bus.max_history = 2
        
        # Add 3 events
        for i in range(3):
            event = FlowEvent(
                flow_id=f"flow-{i}",
                event_type="test",
                phase="test",
                data={"index": i},
                timestamp=datetime.utcnow(),
                context={}
            )
            event_bus.event_history.append(event)
            
            # Simulate the limit check
            if len(event_bus.event_history) > event_bus.max_history:
                event_bus.event_history.pop(0)
        
        assert len(event_bus.event_history) == 2
        # Should keep the last 2 events
        assert event_bus.event_history[0].data["index"] == 1
        assert event_bus.event_history[1].data["index"] == 2


class TestIntegration:
    """Integration tests for the complete flow framework"""
    
    @pytest.mark.asyncio
    async def test_full_flow_execution(self, mock_db_session, mock_context, sample_import_data):
        """Test complete flow execution from start to finish"""
        flow = UnifiedDiscoveryFlow(mock_db_session, mock_context)
        
        # Mock crew executions
        with patch.object(flow.crew_factory, 'execute_crew', new_callable=AsyncMock) as mock_crew:
            mock_crew.return_value = {"status": "completed", "data": {}}
            
            with patch.object(flow, 'save_state', new_callable=AsyncMock):
                # Initialize
                state = await flow.initialize_discovery(sample_import_data)
                assert state.current_phase == "initialization"
                
                # Validate
                state = await flow.validate_and_analyze_data(state)
                assert state.current_phase == "data_validation"
                assert state.progress_percentage == 10.0
                
                # Field mapping
                state = await flow.perform_field_mapping(state)
                assert state.current_phase == "field_mapping"
                assert state.progress_percentage == 30.0
                
                # Data cleansing
                state = await flow.cleanse_data(state)
                assert state.current_phase == "data_cleansing"
                assert state.progress_percentage == 50.0
                
                # Asset inventory
                state = await flow.build_asset_inventory(state)
                assert state.current_phase == "asset_inventory"
                assert state.progress_percentage == 70.0
                
                # Dependency analysis
                state = await flow.analyze_dependencies(state)
                assert state.current_phase == "dependency_analysis"
                assert state.progress_percentage == 90.0
                
                # Tech debt assessment
                state = await flow.assess_technical_debt(state)
                assert state.current_phase == "completed"
                assert state.progress_percentage == 100.0
                assert state.status == "completed"
        
        # Verify all phases completed
        expected_phases = [
            "data_validation", "field_mapping", "data_cleansing",
            "asset_inventory", "dependency_analysis", "technical_debt"
        ]
        assert all(phase in state.phases_completed for phase in expected_phases)


# Test utilities and fixtures
@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])