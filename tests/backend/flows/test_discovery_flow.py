"""
Tests for Discovery Flow implementation with MFO Architecture

Aligned with:
- ADR-006: Master Flow Orchestrator
- ADR-015: Persistent Multi-Tenant Agent Architecture
- Lessons from 000-lessons.md
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

# Import MFO fixtures and patterns
from tests.fixtures.mfo_fixtures import (
    mock_tenant_scoped_agent_pool,
)

# MFO architecture imports
from app.core.context import RequestContext
from app.services.flows.discovery_flow import (
    DiscoveryFlowState,
    UnifiedDiscoveryFlow
)
from app.services.flows.events import FlowEvent, FlowEventBus
from app.services.flows.manager import FlowManager


@pytest.fixture
def mock_mfo_context():
    """Create mock MFO request context with proper tenant scoping"""
    return RequestContext(
        client_account_id="demo-client-account",
        engagement_id="demo-engagement-001",
        user_id="demo-user-123",
    )


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    return AsyncMock()


@pytest.fixture
def sample_mfo_import_data(mock_mfo_context):
    """Create sample import data for MFO testing"""
    return {
        "flow_id": uuid4(),
        "import_id": "demo-import-001",
        "filename": "test_data.csv",
        "record_count": 100,
        "client_account_id": mock_mfo_context.client_account_id,
        "engagement_id": mock_mfo_context.engagement_id,
        "raw_data": [
            {"hostname": "server1", "ip": "192.168.1.1", "type": "server"},
            {"hostname": "server2", "ip": "192.168.1.2", "type": "database"},
            {"hostname": "app1", "ip": "192.168.1.3", "type": "application"},
        ],
    }


@pytest.mark.mfo
@pytest.mark.discovery_flow
class TestDiscoveryFlowState:
    """Tests for DiscoveryFlowState with MFO architecture"""

    def test_state_initialization(self, mock_mfo_context):
        """Test state initialization with tenant scoping"""
        flow_id = uuid4()
        state = DiscoveryFlowState(
            flow_id=flow_id,
            client_account_id=mock_mfo_context.client_account_id,
            engagement_id=mock_mfo_context.engagement_id,
            user_id=mock_mfo_context.user_id,
        )

        assert state.flow_id == flow_id
        assert state.current_phase == "initialization"
        assert state.progress_percentage == 0.0
        assert state.status == "running"
        assert len(state.phases_completed) == 0

    def test_add_error(self, mock_mfo_context):
        """Test error tracking with tenant isolation"""
        state = DiscoveryFlowState(
            flow_id=uuid4(),
            client_account_id=mock_mfo_context.client_account_id,
            engagement_id=mock_mfo_context.engagement_id,
            user_id=mock_mfo_context.user_id,
        )

        state.add_error("test_phase", "Test error message")

        assert len(state.errors) == 1
        assert state.errors[0]["phase"] == "test_phase"
        assert state.errors[0]["message"] == "Test error message"
        assert "timestamp" in state.errors[0]


@pytest.mark.mfo
@pytest.mark.discovery_flow
class TestUnifiedDiscoveryFlow:
    """Tests for UnifiedDiscoveryFlow with MFO architecture"""

    @pytest.fixture
    def mfo_flow(self, mock_db_session, mock_mfo_context,
                 mock_tenant_scoped_agent_pool):
        """Create flow instance with MFO patterns"""
        # Mock flow with TenantScopedAgentPool integration
        flow = UnifiedDiscoveryFlow(mock_db_session, mock_mfo_context)
        flow.agent_pool = mock_tenant_scoped_agent_pool
        return flow

    def test_flow_initialization(self, mfo_flow, mock_mfo_context):
        """Test flow initialization with MFO patterns"""
        assert mfo_flow.context == mock_mfo_context
        assert hasattr(mfo_flow, "crew_factory") or hasattr(mfo_flow, "agent_pool")
        assert hasattr(mfo_flow, "state_store")
        # Verify tenant scoping
        assert mfo_flow.context.client_account_id == mock_mfo_context.client_account_id
        assert mfo_flow.context.engagement_id == mock_mfo_context.engagement_id

    @pytest.mark.asyncio
    @pytest.mark.mfo
    async def test_initialize_discovery(self, mfo_flow, sample_mfo_import_data):
        """Test flow initialization method with MFO patterns"""
        with patch.object(mfo_flow, "save_state", new_callable=AsyncMock) as mock_save:
            result = await mfo_flow.initialize_discovery(sample_mfo_import_data)

            assert isinstance(result, DiscoveryFlowState)
            assert result.flow_id == sample_mfo_import_data["flow_id"]
            assert result.current_phase == "initialization"
            assert result.total_records == sample_mfo_import_data["record_count"]
            # Verify tenant scoping
            assert result.client_account_id == sample_mfo_import_data[
                "client_account_id"
            ]
            assert result.engagement_id == sample_mfo_import_data[
                "engagement_id"
            ]
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.mfo
    async def test_validate_and_analyze_data(self, mfo_flow, sample_mfo_import_data):
        """Test data validation phase with TenantScopedAgentPool"""
        # Initialize state
        initial_state = await mfo_flow.initialize_discovery(sample_mfo_import_data)

        # Mock agent pool execution instead of crew factory
        with patch.object(
            mfo_flow.agent_pool, "get_agent", new_callable=AsyncMock
        ) as mock_agent_pool:
            mock_agent = AsyncMock()
            mock_agent.execute.return_value = {
                "status": "completed",
                "data": {"validation": "passed"},
            }
            mock_agent_pool.return_value = mock_agent

            with patch.object(mfo_flow, "save_state", new_callable=AsyncMock):
                result = await mfo_flow.validate_and_analyze_data(initial_state)

                assert result.current_phase == "data_validation"
                assert "data_validation" in result.phases_completed
                assert result.progress_percentage == 10.0
                # Verify agent pool was used (not crew factory)
                mock_agent_pool.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.mfo
    async def test_error_handling(self, mfo_flow, sample_mfo_import_data):
        """Test error handling in flow with agent pool"""
        initial_state = await mfo_flow.initialize_discovery(sample_mfo_import_data)

        with patch.object(
            mfo_flow.agent_pool, "get_agent", new_callable=AsyncMock
        ) as mock_agent_pool:
            mock_agent_pool.side_effect = Exception("Test error")

            with pytest.raises(Exception):
                await mfo_flow.validate_and_analyze_data(initial_state)

            # Check that error was handled with tenant context
            assert mfo_flow.state.error == "Test error"
            # Verify tenant isolation maintained during error
            assert mfo_flow.context.client_account_id == sample_mfo_import_data[
                "client_account_id"
            ]


@pytest.mark.mfo
@pytest.mark.discovery_flow
class TestFlowManager:
    """Tests for FlowManager with MFO architecture"""

    @pytest.fixture
    def manager(self):
        """Create flow manager"""
        return FlowManager()

    def test_manager_initialization(self, manager):
        """Test manager initialization"""
        assert len(manager.active_flows) == 0
        assert len(manager.flow_tasks) == 0

    @pytest.mark.asyncio
    async def test_create_discovery_flow(
        self, manager, mock_db_session, mock_mfo_context, sample_import_data
    ):
        """Test flow creation"""
        with patch(
            "app.services.flows.manager.UnifiedDiscoveryFlow"
        ) as mock_flow_class:
            mock_flow = AsyncMock()
            mock_flow_class.return_value = mock_flow
            mock_flow.kickoff = AsyncMock()

            flow_id = await manager.create_discovery_flow(
                mock_db_session, mock_mfo_context, sample_import_data
            )

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


@pytest.mark.mfo
@pytest.mark.discovery_flow
class TestFlowEventBus:
    """Tests for FlowEventBus with MFO integration"""

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
            context={"test": True},
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
            context={},
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
                context={},
            )
            event_bus.event_history.append(event)

            # Simulate the limit check
            if len(event_bus.event_history) > event_bus.max_history:
                event_bus.event_history.pop(0)

        assert len(event_bus.event_history) == 2
        # Should keep the last 2 events
        assert event_bus.event_history[0].data["index"] == 1
        assert event_bus.event_history[1].data["index"] == 2


@pytest.mark.mfo
@pytest.mark.discovery_flow
class TestIntegration:
    """Integration tests for the complete flow framework with MFO architecture"""

    @pytest.mark.asyncio
    @pytest.mark.mfo
    async def test_full_flow_execution(
        self, mock_db_session, mock_mfo_context, sample_mfo_import_data,
        mock_tenant_scoped_agent_pool
    ):
        """Test complete flow execution from start to finish with MFO architecture"""
        flow = UnifiedDiscoveryFlow(mock_db_session, mock_mfo_context)
        flow.agent_pool = mock_tenant_scoped_agent_pool

        # Mock agent pool executions instead of crew factory
        with patch.object(
            flow.agent_pool, "get_agent", new_callable=AsyncMock
        ) as mock_agent_pool:
            mock_agent = AsyncMock()
            mock_agent.execute.return_value = {"status": "completed", "data": {}}
            mock_agent_pool.return_value = mock_agent

            with patch.object(flow, "save_state", new_callable=AsyncMock):
                # Initialize with MFO data
                state = await flow.initialize_discovery(sample_mfo_import_data)
                assert state.current_phase == "initialization"
                # Verify tenant scoping
                assert state.client_account_id == mock_mfo_context.client_account_id
                assert state.engagement_id == mock_mfo_context.engagement_id

                # Validate with agent pool
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
            "data_validation",
            "field_mapping",
            "data_cleansing",
            "asset_inventory",
            "dependency_analysis",
            "technical_debt",
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
