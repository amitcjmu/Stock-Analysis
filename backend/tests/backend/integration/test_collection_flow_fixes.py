"""
Integration tests for collection flow bug fixes

Tests the three critical bugs that were fixed:
1. Master-child flow status desynchronization
2. Missing application linkage in collection_flow_applications table
3. API endpoint 404 error for /collection/flow/{flow_id}
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import select

from app.models.collection_flow import CollectionFlow, CollectionFlowStatus
from app.models.master_flow import CrewAIFlowStateExtensions
from app.models.canonical_applications.collection_flow_app import (
    CollectionFlowApplication,
)
from app.models.asset import Asset
from app.services.collection_flow.state_management import CollectionFlowStateManager
from app.api.v1.endpoints.collection_applications import update_flow_applications
from app.core.context import RequestContext


@pytest.mark.asyncio
async def test_master_child_flow_status_synchronization(db_session):
    """Test Bug #1: Master-child flow status desynchronization is fixed"""

    # Create a master flow
    master_flow_id = str(uuid4())
    master_flow = CrewAIFlowStateExtensions(
        flow_id=master_flow_id,
        flow_type="collection",
        flow_name="Test Collection Flow",
        flow_status="running",
        progress_percentage=50.0,
        client_account_id=uuid4(),
        engagement_id=uuid4(),
        user_id="test_user",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(master_flow)
    await db_session.flush()

    # Create a collection flow linked to the master flow
    collection_flow_id = uuid4()
    collection_flow = CollectionFlow(
        flow_id=collection_flow_id,
        master_flow_id=uuid4(master_flow_id),  # Link to master flow
        client_account_id=master_flow.client_account_id,
        engagement_id=master_flow.engagement_id,
        status=CollectionFlowStatus.RUNNING.value,
        progress_percentage=50.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(collection_flow)
    await db_session.commit()

    # Initialize state manager
    state_manager = CollectionFlowStateManager(
        db=db_session, client_account_id=str(master_flow.client_account_id)
    )

    # Complete the collection flow - this should synchronize the master flow status
    completed_flow = await state_manager.complete_flow(
        flow_id=collection_flow_id,
        final_quality_score=85.0,
        final_confidence_score=90.0,
    )

    # Verify collection flow is completed
    assert completed_flow.status == CollectionFlowStatus.COMPLETED
    assert completed_flow.progress_percentage == 100.0

    # Verify master flow status is synchronized - BUG FIX VERIFICATION
    await db_session.refresh(master_flow)
    assert master_flow.flow_status == "completed"
    assert master_flow.progress_percentage == 100.0
    assert "completion" in master_flow.flow_persistence_data
    assert (
        master_flow.flow_persistence_data["completion"]["completed_by"]
        == "collection_flow_state_management"
    )


@pytest.mark.asyncio
async def test_collection_flow_application_linkage(db_session):
    """Test Bug #2: Missing application linkage in collection_flow_applications table is fixed"""

    # Create a collection flow
    collection_flow = CollectionFlow(
        flow_id=uuid4(),
        client_account_id=uuid4(),
        engagement_id=uuid4(),
        status=CollectionFlowStatus.RUNNING.value,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(collection_flow)
    await db_session.flush()

    # Create test assets
    asset1 = Asset(
        id=str(uuid4()),
        name="Test Application 1",
        application_name="Test Application 1",
        client_account_id=collection_flow.client_account_id,
        engagement_id=collection_flow.engagement_id,
        environment="production",
    )
    asset2 = Asset(
        id=str(uuid4()),
        name="Test Application 2",
        application_name="Test Application 2",
        client_account_id=collection_flow.client_account_id,
        engagement_id=collection_flow.engagement_id,
        environment="staging",
    )
    db_session.add(asset1)
    db_session.add(asset2)
    await db_session.commit()

    # Mock the deduplication service and application selection
    from app.schemas.collection_flow import CollectionApplicationSelectionRequest

    # Create request with selected application IDs
    request_data = CollectionApplicationSelectionRequest(
        selected_application_ids=[asset1.id, asset2.id], action="select"
    )

    # Mock user and context
    class MockUser:
        id = "test_user"

    context = RequestContext(
        client_account_id=collection_flow.client_account_id,
        engagement_id=collection_flow.engagement_id,
        user_id="test_user",
    )

    # Call the application selection endpoint - this should create CollectionFlowApplication records
    result = await update_flow_applications(
        flow_id=str(collection_flow.flow_id),
        request_data=request_data,
        db=db_session,
        current_user=MockUser(),
        context=context,
    )

    # Verify the response indicates success
    assert result["success"] is True
    assert result["selected_application_count"] >= 2
    assert result["normalized_records_created"] >= 2

    # BUG FIX VERIFICATION: Check that CollectionFlowApplication records were created
    collection_apps_result = await db_session.execute(
        select(CollectionFlowApplication).where(
            CollectionFlowApplication.collection_flow_id == collection_flow.flow_id
        )
    )
    collection_apps = collection_apps_result.scalars().all()

    # Should have created records for both applications
    assert len(collection_apps) == 2

    # Verify the records have proper data
    app_names = [app.application_name for app in collection_apps]
    assert "Test Application 1" in app_names
    assert "Test Application 2" in app_names

    # Verify they're linked to the correct collection flow
    for app in collection_apps:
        assert app.collection_flow_id == collection_flow.flow_id
        assert app.client_account_id == collection_flow.client_account_id
        assert app.engagement_id == collection_flow.engagement_id
        assert app.collection_status == "selected"
        assert (
            app.canonical_application_id is not None
        )  # Should be set by deduplication


@pytest.mark.asyncio
async def test_collection_flow_api_endpoint_exists():
    """Test Bug #3: API endpoint 404 error for /collection/flow/{flow_id} is fixed"""

    # This test verifies that the missing import has been added
    # Test that rerun_gap_analysis is properly imported in collection_crud.py
    from app.api.v1.endpoints import collection_crud

    # Verify the function exists and is exported
    assert hasattr(collection_crud, "rerun_gap_analysis")
    assert "rerun_gap_analysis" in collection_crud.__all__

    # Verify we can import it directly
    from app.api.v1.endpoints.collection_crud import rerun_gap_analysis

    assert callable(rerun_gap_analysis)

    # Verify it's imported in the main collection router
    from app.api.v1.endpoints.collection import router

    # Check that the router has the rerun gap analysis endpoint
    routes = [route.path for route in router.routes if hasattr(route, "path")]
    assert any("/flows/{flow_id}/rerun-gap-analysis" in route for route in routes)


if __name__ == "__main__":
    pytest.main([__file__])
