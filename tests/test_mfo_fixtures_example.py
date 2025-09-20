"""
Example Tests Using MFO Fixtures

Demonstrates how to use the new standardized MFO test fixtures
for testing Master Flow Orchestrator patterns.

Generated with CC as examples for MFO fixture usage.
"""

import pytest
import uuid
from datetime import datetime, timezone


@pytest.mark.mfo
@pytest.mark.unit
def test_demo_tenant_context_creation(demo_tenant_context):
    """Test that demo tenant context is properly created."""
    assert demo_tenant_context.client_account_id == "11111111-1111-1111-1111-111111111111"
    assert demo_tenant_context.engagement_id == "22222222-2222-2222-2222-222222222222"
    assert demo_tenant_context.user_email == "demo@demo-corp.com"

    # Test API headers generation
    headers = demo_tenant_context.to_dict()
    assert "X-Client-Account-ID" in headers
    assert "X-Engagement-ID" in headers
    assert "X-User-ID" in headers


@pytest.mark.mfo
@pytest.mark.unit
def test_mock_service_registry_setup(mock_service_registry):
    """Test that mock service registry is properly configured."""
    # Test default services are available
    assert mock_service_registry.get_service("master_flow_service") is not None
    assert mock_service_registry.get_service("discovery_flow_service") is not None
    assert mock_service_registry.get_service("agent_pool") is not None

    # Test service registration
    custom_service = "test_service"
    mock_service_registry.register_service("custom", custom_service)
    assert mock_service_registry.get_service("custom") == custom_service


@pytest.mark.mfo
@pytest.mark.database
@pytest.mark.async_test
async def test_mock_async_session_creation(mock_async_session):
    """Test that async database session is properly configured."""
    # Test session is available and async
    assert mock_async_session is not None

    # Test session can be used in async context
    async with mock_async_session.begin():
        # Simulate transaction
        pass


@pytest.mark.mfo
@pytest.mark.unit
def test_sample_master_flow_data_structure(sample_master_flow_data):
    """Test master flow data has correct structure."""
    required_fields = [
        "flow_id", "client_account_id", "engagement_id", "user_id",
        "flow_type", "flow_name", "flow_status", "flow_configuration"
    ]

    for field in required_fields:
        assert field in sample_master_flow_data

    # Test proper UUID format
    assert uuid.UUID(sample_master_flow_data["flow_id"])
    assert sample_master_flow_data["flow_type"] == "discovery"
    assert sample_master_flow_data["flow_status"] == "initialized"


@pytest.mark.mfo
@pytest.mark.unit
def test_sample_discovery_flow_data_structure(sample_discovery_flow_data):
    """Test discovery flow (child table) data has correct structure."""
    required_fields = [
        "id", "flow_id", "master_flow_id", "client_account_id",
        "engagement_id", "user_id", "status", "current_phase"
    ]

    for field in required_fields:
        assert field in sample_discovery_flow_data

    # Test proper FK relationship
    assert uuid.UUID(sample_discovery_flow_data["master_flow_id"])
    assert sample_discovery_flow_data["learning_scope"] == "engagement"
    assert sample_discovery_flow_data["memory_isolation_level"] == "strict"


@pytest.mark.mfo
@pytest.mark.agent
@pytest.mark.async_test
async def test_mock_tenant_scoped_agent_pool(mock_tenant_scoped_agent_pool):
    """Test mock agent pool functionality."""
    # Test agent acquisition
    agent = await mock_tenant_scoped_agent_pool.get_agent()
    assert agent is not None

    # Test agent execution
    result = await agent.execute()
    assert result["status"] == "completed"
    assert "confidence" in result
    assert "execution_time" in result

    # Test pool stats
    stats = await mock_tenant_scoped_agent_pool.get_pool_stats()
    assert "active_agents" in stats
    assert "memory_usage" in stats


@pytest.mark.mfo
@pytest.mark.unit
def test_mfo_flow_states_scenarios(mfo_flow_states):
    """Test that all flow state scenarios are available."""
    expected_states = [
        "initialized", "running_data_import", "running_field_mapping",
        "completed", "paused", "failed"
    ]

    for state in expected_states:
        assert state in mfo_flow_states

        # Each state should have master and child flow data
        state_data = mfo_flow_states[state]
        assert "master_flow" in state_data
        assert "child_flow" in state_data

        # Test master-child relationship consistency
        master_flow = state_data["master_flow"]
        child_flow = state_data["child_flow"]

        assert "flow_id" in master_flow
        assert "flow_id" in child_flow


@pytest.mark.mfo
@pytest.mark.integration
@pytest.mark.tenant_isolation
def test_tenant_isolation_data(tenant_isolation_test_data):
    """Test tenant isolation test data."""
    assert len(tenant_isolation_test_data) >= 3

    # Each tenant should have unique IDs
    client_ids = [data["client_account_id"] for data in tenant_isolation_test_data]
    assert len(set(client_ids)) == len(client_ids)  # All unique

    # Test data structure
    for tenant_data in tenant_isolation_test_data:
        assert "client_account_id" in tenant_data
        assert "engagement_id" in tenant_data
        assert "user_id" in tenant_data

        # Test UUID format
        assert uuid.UUID(tenant_data["client_account_id"])
        assert uuid.UUID(tenant_data["engagement_id"])


@pytest.mark.mfo
@pytest.mark.performance
def test_mfo_performance_config(mfo_performance_test_config):
    """Test MFO performance configuration."""
    assert "timeouts" in mfo_performance_test_config
    assert "thresholds" in mfo_performance_test_config
    assert "load_test_scenarios" in mfo_performance_test_config

    timeouts = mfo_performance_test_config["timeouts"]
    assert timeouts["flow_creation"] > 0
    assert timeouts["phase_execution"] > 0

    scenarios = mfo_performance_test_config["load_test_scenarios"]
    assert "light" in scenarios
    assert "medium" in scenarios
    assert "heavy" in scenarios


@pytest.mark.mfo
@pytest.mark.unit
def test_helper_functions():
    """Test MFO fixture helper functions."""
    from tests.fixtures.mfo_fixtures import create_mock_mfo_context, create_linked_flow_data

    # Test context creation
    context = create_mock_mfo_context()
    assert context.client_account_id
    assert context.engagement_id

    # Test linked flow data creation
    flow_data = create_linked_flow_data("assessment", "running")
    assert "master_flow" in flow_data
    assert "child_flow" in flow_data
    assert flow_data["master_flow"]["flow_type"] == "assessment"
    assert flow_data["master_flow"]["flow_status"] == "running"
    assert flow_data["child_flow"]["master_flow_id"] == flow_data["master_flow"]["flow_id"]


@pytest.mark.mfo
@pytest.mark.integration
@pytest.mark.async_test
async def test_mfo_test_environment_setup(mock_async_session, demo_tenant_context):
    """Test complete MFO test environment setup."""
    from tests.fixtures.mfo_fixtures import setup_mfo_test_environment

    env = await setup_mfo_test_environment(
        session=mock_async_session,
        context=demo_tenant_context,
        flow_type="discovery"
    )

    assert env["setup_complete"] is True
    assert env["context"] == demo_tenant_context
    assert env["session"] == mock_async_session
    assert "flows" in env

    flows = env["flows"]
    assert flows["master_flow"]["flow_type"] == "discovery"
    assert flows["child_flow"]["master_flow_id"] == flows["master_flow"]["flow_id"]


# Example of using multiple markers
@pytest.mark.mfo
@pytest.mark.integration
@pytest.mark.agent
@pytest.mark.tenant_isolation
@pytest.mark.async_test
async def test_comprehensive_mfo_scenario(
    demo_tenant_context,
    mock_service_registry,
    mock_tenant_scoped_agent_pool,
    mfo_flow_states
):
    """Example comprehensive test using multiple MFO fixtures."""
    # Setup: Get a running flow state
    flow_state = mfo_flow_states["running_field_mapping"]
    master_flow = flow_state["master_flow"]
    child_flow = flow_state["child_flow"]

    # Test: Simulate agent execution for field mapping phase
    agent = await mock_tenant_scoped_agent_pool.get_agent()
    result = await agent.execute()

    # Verify: Agent execution completed successfully
    assert result["status"] == "completed"
    assert result["confidence"] > 0.5

    # Test: Service registry can provide required services
    flow_service = mock_service_registry.get_service("discovery_flow_service")
    assert flow_service is not None

    # Verify: Proper tenant context is maintained
    assert demo_tenant_context.client_account_id
    assert demo_tenant_context.engagement_id

    # Test: Flow state progression
    assert child_flow["current_phase"] == "field_mapping"
    assert "data_import" in child_flow["phases_completed"]
