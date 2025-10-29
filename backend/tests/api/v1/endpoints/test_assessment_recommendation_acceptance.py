"""
Integration tests for Assessment Flow Recommendation Acceptance endpoint.

Tests the accept 6R recommendation feature (Phase 6 of Issue #842).
"""

import pytest
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from app.models.asset.models import Asset
from app.models.assessment_flow import AssessmentFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions


@pytest.mark.asyncio
async def test_accept_recommendation_success(
    test_db: AsyncSession,
    test_client: TestClient,
    test_context: dict,
):
    """
    Test successfully accepting a 6R recommendation.

    Workflow:
    1. Create master flow in crewai_flow_state_extensions
    2. Create child assessment flow
    3. Create asset
    4. Accept recommendation via API
    5. Verify asset updated with 6R strategy
    """
    # Step 1: Create master flow
    flow_id = uuid4()
    client_account_id = UUID(test_context["client_account_id"])
    engagement_id = UUID(test_context["engagement_id"])

    master_flow = CrewAIFlowStateExtensions(
        flow_id=flow_id,
        flow_type="assessment",
        flow_status="running",
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=test_context["user_id"],
        flow_configuration={},
        flow_persistence_data={},
    )
    test_db.add(master_flow)
    await test_db.flush()

    # Step 2: Create child assessment flow
    child_flow = AssessmentFlow(
        flow_id=flow_id,
        master_flow_id=master_flow.flow_id,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_name="Test Assessment Flow",
        status="in_progress",
        current_phase="sixr_decisions",
        progress=50,
        selected_application_ids=[],
        selected_asset_ids=[],
        configuration={},
        runtime_state={},
    )
    test_db.add(child_flow)
    await test_db.flush()

    # Step 3: Create asset
    app_id = uuid4()
    asset = Asset(
        id=app_id,
        name="Test Application",
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        master_flow_id=flow_id,
        six_r_strategy=None,  # Not yet decided
        migration_status="discovered",
    )
    test_db.add(asset)
    await test_db.commit()

    # Step 4: Accept recommendation via API
    response = test_client.post(
        f"/api/v1/assessment-flow/{flow_id}/sixr-decisions/{app_id}/accept",
        json={
            "strategy": "rehost",
            "reasoning": "Low complexity, quick migration",
            "confidence_level": 0.9,
        },
        headers={
            "X-Client-Account-ID": str(client_account_id),
            "X-Engagement-ID": str(engagement_id),
            "X-User-ID": test_context["user_id"],
        },
    )

    # Step 5: Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["strategy"] == "rehost"
    assert data["flow_id"] == str(flow_id)
    assert data["app_id"] == str(app_id)

    # Step 6: Verify asset updated in database
    await test_db.refresh(asset)
    assert asset.six_r_strategy == "rehost"
    assert asset.migration_status == "analyzed"
    assert asset.custom_attributes is not None
    assert "sixr_decision" in asset.custom_attributes
    assert asset.custom_attributes["sixr_decision"]["strategy"] == "rehost"
    assert (
        asset.custom_attributes["sixr_decision"]["reasoning"]
        == "Low complexity, quick migration"
    )


@pytest.mark.asyncio
async def test_accept_recommendation_flow_not_found(
    test_client: TestClient,
    test_context: dict,
):
    """Test accepting recommendation with non-existent flow."""
    flow_id = uuid4()
    app_id = uuid4()

    response = test_client.post(
        f"/api/v1/assessment-flow/{flow_id}/sixr-decisions/{app_id}/accept",
        json={
            "strategy": "rehost",
            "reasoning": "Test",
            "confidence_level": 0.9,
        },
        headers={
            "X-Client-Account-ID": test_context["client_account_id"],
            "X-Engagement-ID": test_context["engagement_id"],
            "X-User-ID": test_context["user_id"],
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_accept_recommendation_asset_not_found(
    test_db: AsyncSession,
    test_client: TestClient,
    test_context: dict,
):
    """Test accepting recommendation with non-existent asset."""
    # Create flow but no asset
    flow_id = uuid4()
    client_account_id = UUID(test_context["client_account_id"])
    engagement_id = UUID(test_context["engagement_id"])

    master_flow = CrewAIFlowStateExtensions(
        flow_id=flow_id,
        flow_type="assessment",
        flow_status="running",
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=test_context["user_id"],
        flow_configuration={},
        flow_persistence_data={},
    )
    test_db.add(master_flow)

    child_flow = AssessmentFlow(
        flow_id=flow_id,
        master_flow_id=master_flow.flow_id,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_name="Test Assessment Flow",
        status="in_progress",
        current_phase="sixr_decisions",
        selected_application_ids=[],
        selected_asset_ids=[],
    )
    test_db.add(child_flow)
    await test_db.commit()

    # Try to accept recommendation for non-existent asset
    app_id = uuid4()
    response = test_client.post(
        f"/api/v1/assessment-flow/{flow_id}/sixr-decisions/{app_id}/accept",
        json={
            "strategy": "rehost",
            "reasoning": "Test",
            "confidence_level": 0.9,
        },
        headers={
            "X-Client-Account-ID": str(client_account_id),
            "X-Engagement-ID": str(engagement_id),
            "X-User-ID": test_context["user_id"],
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_accept_recommendation_multi_tenant_isolation(
    test_db: AsyncSession,
    test_client: TestClient,
    test_context: dict,
):
    """Test multi-tenant isolation - cannot accept recommendation for another client's asset."""
    # Create flow and asset for client A
    flow_id = uuid4()
    client_a_id = UUID(test_context["client_account_id"])
    client_b_id = uuid4()  # Different client
    engagement_id = UUID(test_context["engagement_id"])

    master_flow = CrewAIFlowStateExtensions(
        flow_id=flow_id,
        flow_type="assessment",
        flow_status="running",
        client_account_id=client_a_id,
        engagement_id=engagement_id,
        user_id=test_context["user_id"],
        flow_configuration={},
        flow_persistence_data={},
    )
    test_db.add(master_flow)

    child_flow = AssessmentFlow(
        flow_id=flow_id,
        master_flow_id=master_flow.flow_id,
        client_account_id=client_a_id,
        engagement_id=engagement_id,
        flow_name="Test Assessment Flow",
        status="in_progress",
        current_phase="sixr_decisions",
        selected_application_ids=[],
        selected_asset_ids=[],
    )
    test_db.add(child_flow)

    # Create asset for client A
    app_id = uuid4()
    asset = Asset(
        id=app_id,
        name="Client A Application",
        client_account_id=client_a_id,
        engagement_id=engagement_id,
        six_r_strategy=None,
        migration_status="discovered",
    )
    test_db.add(asset)
    await test_db.commit()

    # Try to accept recommendation as client B
    response = test_client.post(
        f"/api/v1/assessment-flow/{flow_id}/sixr-decisions/{app_id}/accept",
        json={
            "strategy": "rehost",
            "reasoning": "Test",
            "confidence_level": 0.9,
        },
        headers={
            "X-Client-Account-ID": str(client_b_id),  # Different client
            "X-Engagement-ID": str(engagement_id),
            "X-User-ID": test_context["user_id"],
        },
    )

    # Should return 404 (not found) because asset doesn't exist for client B
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

    # Verify asset NOT updated
    await test_db.refresh(asset)
    assert asset.six_r_strategy is None
    assert asset.migration_status == "discovered"
