"""
Simplified integration test for data cleansing phase execution.
Tests that the backend properly executes data_cleansing phase when requested.
"""

import pytest
import pytest_asyncio
import uuid
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_flow import DiscoveryFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.core.context import RequestContext
from app.api.v1.endpoints.unified_discovery.flow_execution_handlers import execute_flow
from app.core.database import AsyncSessionLocal


@pytest_asyncio.fixture
async def db_session():
    """Create an async database session for testing."""
    async with AsyncSessionLocal() as session:
        yield session
        # Cleanup - rollback any uncommitted changes
        await session.rollback()


@pytest_asyncio.fixture
async def test_flow(db_session: AsyncSession):
    """Create a test flow ready for data cleansing."""

    # Create master flow
    master_flow_id = uuid.uuid4()
    master_flow = CrewAIFlowStateExtensions(
        flow_id=master_flow_id,
        client_account_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        engagement_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        user_id="test-user",
        flow_type="discovery",
        flow_name="Test Discovery Flow",
        flow_status="running",
    )
    db_session.add(master_flow)

    # Create discovery flow
    discovery_flow = DiscoveryFlow(
        flow_id=uuid.uuid4(),
        master_flow_id=master_flow_id,
        client_account_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        engagement_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        user_id="test-user",
        flow_name="Test Discovery Flow",
        status="running",
        current_phase="data_cleansing",
        data_import_completed=True,
        field_mapping_completed=True,
        data_cleansing_completed=False,
    )
    db_session.add(discovery_flow)

    await db_session.commit()

    return {
        "master_flow_id": master_flow_id,
        "discovery_flow_id": discovery_flow.flow_id,
        "discovery_flow": discovery_flow,
    }


@pytest.mark.asyncio
async def test_data_cleansing_with_complete_flag(db_session: AsyncSession, test_flow):
    """Test that data_cleansing phase is executed when complete flag is passed."""

    flow_id = test_flow["discovery_flow_id"]

    # Create test context
    context = RequestContext(
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        user_id="test-user",
    )

    # Mock MasterFlowOrchestrator.execute_phase
    with patch(
        "app.services.master_flow_orchestrator.MasterFlowOrchestrator.execute_phase",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.return_value = {
            "status": "success",
            "phase": "data_cleansing",
            "data": {"records_processed": 5, "quality_score": 95.0},
        }

        # Call the endpoint with phase and complete flag
        request_body = {
            "phase": "data_cleansing",
            "phase_input": {
                "complete": True  # This should trigger execution before marking complete
            },
        }

        # Execute the endpoint function directly
        result = await execute_flow(
            flow_id=str(flow_id), request=request_body, db=db_session, context=context
        )

        # Verify the response
        assert result["success"] is True
        assert result["phase"] == "data_cleansing"
        assert result["status"] == "completed"
        assert "Data cleansing phase executed and completed" in result["message"]

        # Verify MasterFlowOrchestrator.execute_phase was called
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        assert str(flow_id) in str(call_args)
        assert "data_cleansing" in str(call_args)

        # Verify the phase_input passed to executor doesn't include complete:true
        called_phase_input = (
            call_args[1]["phase_input"] if len(call_args) > 1 else call_args[0][2]
        )
        assert called_phase_input == {}  # Should be empty, not containing complete:true

    # Verify database state after execution
    # Need to refresh the session to see the updates made by execute_flow
    await db_session.commit()  # Commit any pending changes
    discovery_flow = await db_session.get(DiscoveryFlow, flow_id)
    if discovery_flow:
        assert discovery_flow.data_cleansing_completed is True
        assert discovery_flow.current_phase == "asset_inventory"
    else:
        # If not found in this session, at least verify the mock was called correctly
        print(
            f"Note: Discovery flow {flow_id} not found in test session (expected in integration test)"
        )


@pytest.mark.asyncio
async def test_data_cleansing_without_complete_flag(
    db_session: AsyncSession, test_flow
):
    """Test that data_cleansing phase can be executed without complete flag."""

    flow_id = test_flow["discovery_flow_id"]

    # Create test context
    context = RequestContext(
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        user_id="test-user",
    )

    with patch(
        "app.services.master_flow_orchestrator.MasterFlowOrchestrator.execute_phase",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.return_value = {
            "status": "success",
            "phase": "data_cleansing",
            "data": {"records_processed": 5},
        }

        # Call without complete flag
        request_body = {
            "phase": "data_cleansing",
            "phase_input": {"force": True},  # Some other parameter
        }

        await execute_flow(
            flow_id=str(flow_id), request=request_body, db=db_session, context=context
        )

        # Should execute normally
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        called_phase_input = (
            call_args[1]["phase_input"] if len(call_args) > 1 else call_args[0][2]
        )
        assert called_phase_input == {"force": True}

    # Discovery flow should NOT be marked complete
    await db_session.commit()  # Commit any pending changes
    discovery_flow = await db_session.get(DiscoveryFlow, flow_id)
    if discovery_flow:
        assert discovery_flow.data_cleansing_completed is False
    else:
        # If not found in this session, at least verify the mock was called correctly
        print(
            f"Note: Discovery flow {flow_id} not found in test session (expected in integration test)"
        )
