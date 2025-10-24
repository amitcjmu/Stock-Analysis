"""
Unit tests for Collection Flow list operations - Multi-Tenant Isolation

Tests security-critical multi-tenant filtering in collection list endpoints.
Regression test for security issue where get_incomplete_flows was missing client_account_id filter.
"""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow, CollectionFlowStatus
from app.models import User
from app.api.v1.endpoints.collection_crud_queries.lists import (
    get_incomplete_flows,
    get_all_flows,
)


@pytest.mark.asyncio
async def test_get_incomplete_flows_filters_by_client_account_id(
    db_session: AsyncSession,
):
    """
    SECURITY TEST: Ensure get_incomplete_flows filters by BOTH client_account_id and engagement_id.

    Regression test for bug where only engagement_id was checked, allowing cross-tenant data leakage.
    """
    # Setup: Create two different client accounts with same engagement
    engagement_id = uuid.uuid4()
    client_1_id = uuid.uuid4()
    client_2_id = uuid.uuid4()

    # Create flows for client 1
    flow_client_1 = CollectionFlow(
        flow_id=uuid.uuid4(),
        client_account_id=client_1_id,
        engagement_id=engagement_id,
        flow_name="Client 1 Flow",
        status=CollectionFlowStatus.RUNNING,
        automation_tier="TIER_2",
        collection_config={},
        created_at=datetime.now(timezone.utc),
    )

    # Create flows for client 2 (same engagement!)
    flow_client_2 = CollectionFlow(
        flow_id=uuid.uuid4(),
        client_account_id=client_2_id,
        engagement_id=engagement_id,  # Same engagement as client 1
        flow_name="Client 2 Flow",
        status=CollectionFlowStatus.RUNNING,
        automation_tier="TIER_2",
        collection_config={},
        created_at=datetime.now(timezone.utc),
    )

    db_session.add_all([flow_client_1, flow_client_2])
    await db_session.commit()

    # Create mock user
    mock_user = User(id=uuid.uuid4(), email="test@example.com")

    # Test: Request flows for client 1
    context_client_1 = RequestContext(
        client_account_id=str(client_1_id),
        engagement_id=str(engagement_id),
        user_id=str(uuid.uuid4()),
    )

    result_client_1 = await get_incomplete_flows(
        db=db_session,
        current_user=mock_user,
        context=context_client_1,
        limit=50,
    )

    # Assert: Should ONLY see client 1 flows, not client 2
    assert (
        len(result_client_1) == 1
    ), "Should only return flows for the requesting client"
    assert result_client_1[0].flow_name == "Client 1 Flow"

    # Test: Request flows for client 2
    context_client_2 = RequestContext(
        client_account_id=str(client_2_id),
        engagement_id=str(engagement_id),
        user_id=str(uuid.uuid4()),
    )

    result_client_2 = await get_incomplete_flows(
        db=db_session,
        current_user=mock_user,
        context=context_client_2,
        limit=50,
    )

    # Assert: Should ONLY see client 2 flows, not client 1
    assert (
        len(result_client_2) == 1
    ), "Should only return flows for the requesting client"
    assert result_client_2[0].flow_name == "Client 2 Flow"

    # Cleanup
    await db_session.delete(flow_client_1)
    await db_session.delete(flow_client_2)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_all_flows_filters_by_client_account_id(db_session: AsyncSession):
    """
    SECURITY TEST: Ensure get_all_flows filters by BOTH client_account_id and engagement_id.

    This was already correct, but adding test to prevent regression.
    """
    # Setup: Create two different client accounts with same engagement
    engagement_id = uuid.uuid4()
    client_1_id = uuid.uuid4()
    client_2_id = uuid.uuid4()

    # Create completed flow for client 1
    flow_client_1 = CollectionFlow(
        flow_id=uuid.uuid4(),
        client_account_id=client_1_id,
        engagement_id=engagement_id,
        flow_name="Client 1 Completed",
        status=CollectionFlowStatus.COMPLETED,
        automation_tier="TIER_2",
        collection_config={},
        created_at=datetime.now(timezone.utc),
    )

    # Create completed flow for client 2 (same engagement!)
    flow_client_2 = CollectionFlow(
        flow_id=uuid.uuid4(),
        client_account_id=client_2_id,
        engagement_id=engagement_id,
        flow_name="Client 2 Completed",
        status=CollectionFlowStatus.COMPLETED,
        automation_tier="TIER_2",
        collection_config={},
        created_at=datetime.now(timezone.utc),
    )

    db_session.add_all([flow_client_1, flow_client_2])
    await db_session.commit()

    # Create mock user
    mock_user = User(id=uuid.uuid4(), email="test@example.com")

    # Test: Request flows for client 1
    context_client_1 = RequestContext(
        client_account_id=str(client_1_id),
        engagement_id=str(engagement_id),
        user_id=str(uuid.uuid4()),
    )

    result_client_1 = await get_all_flows(
        db=db_session,
        current_user=mock_user,
        context=context_client_1,
        limit=50,
    )

    # Assert: Should ONLY see client 1 flows
    assert len(result_client_1) == 1
    assert result_client_1[0].flow_name == "Client 1 Completed"

    # Test: Request flows for client 2
    context_client_2 = RequestContext(
        client_account_id=str(client_2_id),
        engagement_id=str(engagement_id),
        user_id=str(uuid.uuid4()),
    )

    result_client_2 = await get_all_flows(
        db=db_session,
        current_user=mock_user,
        context=context_client_2,
        limit=50,
    )

    # Assert: Should ONLY see client 2 flows
    assert len(result_client_2) == 1
    assert result_client_2[0].flow_name == "Client 2 Completed"

    # Cleanup
    await db_session.delete(flow_client_1)
    await db_session.delete(flow_client_2)
    await db_session.commit()


@pytest.mark.asyncio
async def test_incomplete_flows_respects_status_filter(db_session: AsyncSession):
    """
    Test that get_incomplete_flows only returns flows with incomplete statuses.
    """
    engagement_id = uuid.uuid4()
    client_id = uuid.uuid4()

    # Create flows with different statuses
    running_flow = CollectionFlow(
        flow_id=uuid.uuid4(),
        client_account_id=client_id,
        engagement_id=engagement_id,
        flow_name="Running",
        status=CollectionFlowStatus.RUNNING,
        automation_tier="TIER_2",
        collection_config={},
        created_at=datetime.now(timezone.utc),
    )

    completed_flow = CollectionFlow(
        flow_id=uuid.uuid4(),
        client_account_id=client_id,
        engagement_id=engagement_id,
        flow_name="Completed",
        status=CollectionFlowStatus.COMPLETED,
        automation_tier="TIER_2",
        collection_config={},
        created_at=datetime.now(timezone.utc),
    )

    failed_flow = CollectionFlow(
        flow_id=uuid.uuid4(),
        client_account_id=client_id,
        engagement_id=engagement_id,
        flow_name="Failed",
        status=CollectionFlowStatus.FAILED,
        automation_tier="TIER_2",
        collection_config={},
        created_at=datetime.now(timezone.utc),
    )

    db_session.add_all([running_flow, completed_flow, failed_flow])
    await db_session.commit()

    # Create mock user and context
    mock_user = User(id=uuid.uuid4(), email="test@example.com")
    context = RequestContext(
        client_account_id=str(client_id),
        engagement_id=str(engagement_id),
        user_id=str(uuid.uuid4()),
    )

    # Test
    result = await get_incomplete_flows(
        db=db_session,
        current_user=mock_user,
        context=context,
        limit=50,
    )

    # Assert: Should include RUNNING and FAILED, but NOT COMPLETED
    assert len(result) == 2
    flow_names = {flow.flow_name for flow in result}
    assert "Running" in flow_names
    assert "Failed" in flow_names
    assert "Completed" not in flow_names

    # Cleanup
    await db_session.delete(running_flow)
    await db_session.delete(completed_flow)
    await db_session.delete(failed_flow)
    await db_session.commit()
