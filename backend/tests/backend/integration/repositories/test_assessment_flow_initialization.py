"""
Integration tests for enhanced Assessment flow initialization (Phase 2 Days 8-9).

Tests verify that create_assessment_flow() properly populates:
- application_asset_groups (canonical application grouping)
- enrichment_status (7 enrichment tables)
- readiness_summary (assessment readiness metrics)
"""

import pytest
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.assessment_flow_repository.commands.flow_commands import (
    FlowCommands,
)
from app.models.asset import Asset
from app.models.canonical_applications import (
    CanonicalApplication,
    CollectionFlowApplication,
)
from app.models.assessment_flow import AssessmentFlow

# Use existing Demo Corporation client account and engagement for integration tests
DEMO_CLIENT_ACCOUNT_ID = UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"


@pytest.mark.asyncio
async def test_create_assessment_flow_with_enrichment_metadata(
    async_db_session: AsyncSession,
):
    """Integration test uses async_db_session fixture."""
    db_session = async_db_session
    """
    Test assessment flow creation populates enrichment metadata correctly.

    Scenario:
    - Create 2 assets with different readiness states
    - Create canonical application
    - Link assets to canonical app via collection_flow_applications
    - Create assessment flow
    - Verify all new fields populated
    """
    # Setup: Generate tenant context
    client_account_id = DEMO_CLIENT_ACCOUNT_ID
    engagement_id = DEMO_ENGAGEMENT_ID
    collection_flow_id = uuid4()

    # Setup: Create assets
    asset1 = Asset(
        id=uuid4(),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        asset_name="Test Server",
        name="Test Server",
        asset_type="server",
        assessment_readiness="ready",
        assessment_readiness_score=0.85,
    )
    asset2 = Asset(
        id=uuid4(),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        asset_name="Test Database",
        name="Test Database",
        asset_type="database",
        assessment_readiness="not_ready",
        assessment_readiness_score=0.45,
    )
    db_session.add_all([asset1, asset2])
    await db_session.flush()

    # Setup: Create canonical application
    canonical_app = CanonicalApplication(
        id=uuid4(),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        canonical_name="Test Application",
        application_type="web_application",
    )
    db_session.add(canonical_app)
    await db_session.flush()

    # Setup: Link assets to canonical application
    link1 = CollectionFlowApplication(
        collection_flow_id=collection_flow_id,
        asset_id=asset1.id,
        application_name="Test Application",
        canonical_application_id=canonical_app.id,
        deduplication_method="manual",
        match_confidence=1.0,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )
    link2 = CollectionFlowApplication(
        collection_flow_id=collection_flow_id,
        asset_id=asset2.id,
        application_name="Test Application",
        canonical_application_id=canonical_app.id,
        deduplication_method="manual",
        match_confidence=1.0,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )
    db_session.add_all([link1, link2])
    await db_session.commit()

    # Execute: Create assessment flow
    flow_commands = FlowCommands(db=db_session, client_account_id=client_account_id)
    assessment_flow_id = await flow_commands.create_assessment_flow(
        engagement_id=engagement_id,
        selected_application_ids=[str(asset1.id), str(asset2.id)],
        created_by="test_user",
        collection_flow_id=str(collection_flow_id),
    )

    # Query created flow
    result = await db_session.execute(
        select(AssessmentFlow).where(AssessmentFlow.id == assessment_flow_id)
    )
    assessment_flow = result.scalar_one()

    # Assert: Check new fields populated
    assert assessment_flow.selected_asset_ids == [str(asset1.id), str(asset2.id)]
    assert str(canonical_app.id) in assessment_flow.selected_canonical_application_ids

    # Assert: Check application_asset_groups structure
    assert len(assessment_flow.application_asset_groups) == 1
    app_group = assessment_flow.application_asset_groups[0]
    assert app_group["canonical_application_name"] == "Test Application"
    assert app_group["asset_count"] == 2
    assert set(app_group["asset_types"]) == {"server", "database"}

    # Assert: Check enrichment_status (should be empty since no enrichment data)
    assert assessment_flow.enrichment_status is not None
    assert isinstance(assessment_flow.enrichment_status, dict)

    # Assert: Check readiness_summary
    assert assessment_flow.readiness_summary is not None
    assert assessment_flow.readiness_summary["total_assets"] == 2
    assert assessment_flow.readiness_summary["ready"] == 1
    assert assessment_flow.readiness_summary["not_ready"] == 1
    assert 0.0 <= assessment_flow.readiness_summary["avg_completeness_score"] <= 1.0


@pytest.mark.asyncio
async def test_create_assessment_flow_with_unmapped_assets(
    async_db_session: AsyncSession,
):
    """Integration test uses async_db_session fixture."""
    db_session = async_db_session
    """
    Test assessment flow creation handles unmapped assets gracefully.

    Scenario:
    - Create asset WITHOUT canonical mapping
    - Create assessment flow
    - Verify unmapped asset grouped separately
    """
    # Setup: Generate tenant context
    client_account_id = DEMO_CLIENT_ACCOUNT_ID
    engagement_id = DEMO_ENGAGEMENT_ID

    # Setup: Create asset WITHOUT canonical mapping
    asset = Asset(
        id=uuid4(),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        asset_name="Unmapped Server",
        name="Unmapped Server",
        asset_type="server",
        assessment_readiness="not_ready",
        assessment_readiness_score=0.3,
    )
    db_session.add(asset)
    await db_session.commit()

    # Execute: Create assessment flow
    flow_commands = FlowCommands(db=db_session, client_account_id=client_account_id)
    assessment_flow_id = await flow_commands.create_assessment_flow(
        engagement_id=engagement_id,
        selected_application_ids=[str(asset.id)],
        created_by="test_user",
    )

    # Query created flow
    result = await db_session.execute(
        select(AssessmentFlow).where(AssessmentFlow.id == assessment_flow_id)
    )
    assessment_flow = result.scalar_one()

    # Assert: Unmapped asset grouped separately
    assert len(assessment_flow.application_asset_groups) == 1
    app_group = assessment_flow.application_asset_groups[0]
    assert app_group["canonical_application_id"] is None
    assert app_group["canonical_application_name"] == "Unmapped Server"


@pytest.mark.asyncio
async def test_create_assessment_flow_empty_assets(async_db_session: AsyncSession):
    """Integration test uses async_db_session fixture."""
    db_session = async_db_session
    """
    Test assessment flow creation with empty asset list.

    Scenario:
    - Create assessment flow with no assets
    - Verify flow created but metadata empty
    """
    # Setup: Generate tenant context
    client_account_id = DEMO_CLIENT_ACCOUNT_ID
    engagement_id = DEMO_ENGAGEMENT_ID

    # Execute: Create assessment flow with empty asset list
    flow_commands = FlowCommands(db=db_session, client_account_id=client_account_id)
    assessment_flow_id = await flow_commands.create_assessment_flow(
        engagement_id=engagement_id,
        selected_application_ids=[],
        created_by="test_user",
    )

    # Query created flow
    result = await db_session.execute(
        select(AssessmentFlow).where(AssessmentFlow.id == assessment_flow_id)
    )
    assessment_flow = result.scalar_one()

    # Assert: Flow created with empty metadata
    assert assessment_flow.selected_asset_ids == []
    assert assessment_flow.selected_canonical_application_ids == []
    assert assessment_flow.application_asset_groups == []
    assert assessment_flow.enrichment_status == {}
    assert assessment_flow.readiness_summary == {}


@pytest.mark.asyncio
async def test_create_assessment_flow_multiple_applications(
    async_db_session: AsyncSession,
):
    """Integration test uses async_db_session fixture."""
    db_session = async_db_session
    """
    Test assessment flow creation with assets from multiple canonical applications.

    Scenario:
    - Create 3 assets
    - Create 2 canonical applications
    - Link 2 assets to app1, 1 asset to app2
    - Create assessment flow
    - Verify 2 application groups created
    """
    # Setup: Generate tenant context
    client_account_id = DEMO_CLIENT_ACCOUNT_ID
    engagement_id = DEMO_ENGAGEMENT_ID
    collection_flow_id = uuid4()

    # Setup: Create assets
    asset1 = Asset(
        id=uuid4(),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        asset_name="CRM Server",
        name="CRM Server",
        asset_type="server",
        assessment_readiness="ready",
        assessment_readiness_score=0.9,
    )
    asset2 = Asset(
        id=uuid4(),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        asset_name="CRM Database",
        name="CRM Database",
        asset_type="database",
        assessment_readiness="ready",
        assessment_readiness_score=0.85,
    )
    asset3 = Asset(
        id=uuid4(),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        asset_name="ERP Server",
        name="ERP Server",
        asset_type="server",
        assessment_readiness="not_ready",
        assessment_readiness_score=0.5,
    )
    db_session.add_all([asset1, asset2, asset3])
    await db_session.flush()

    # Setup: Create 2 canonical applications
    crm_app = CanonicalApplication(
        id=uuid4(),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        canonical_name="CRM System",
        application_type="web_application",
    )
    erp_app = CanonicalApplication(
        id=uuid4(),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        canonical_name="ERP System",
        application_type="enterprise_application",
    )
    db_session.add_all([crm_app, erp_app])
    await db_session.flush()

    # Setup: Link assets to canonical applications
    links = [
        CollectionFlowApplication(
            collection_flow_id=collection_flow_id,
            asset_id=asset1.id,
            application_name="CRM System",
            canonical_application_id=crm_app.id,
            deduplication_method="auto",
            match_confidence=0.95,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        ),
        CollectionFlowApplication(
            collection_flow_id=collection_flow_id,
            asset_id=asset2.id,
            application_name="CRM System",
            canonical_application_id=crm_app.id,
            deduplication_method="auto",
            match_confidence=0.90,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        ),
        CollectionFlowApplication(
            collection_flow_id=collection_flow_id,
            asset_id=asset3.id,
            application_name="ERP System",
            canonical_application_id=erp_app.id,
            deduplication_method="auto",
            match_confidence=0.88,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        ),
    ]
    db_session.add_all(links)
    await db_session.commit()

    # Execute: Create assessment flow
    flow_commands = FlowCommands(db=db_session, client_account_id=client_account_id)
    assessment_flow_id = await flow_commands.create_assessment_flow(
        engagement_id=engagement_id,
        selected_application_ids=[str(asset1.id), str(asset2.id), str(asset3.id)],
        created_by="test_user",
        collection_flow_id=str(collection_flow_id),
    )

    # Query created flow
    result = await db_session.execute(
        select(AssessmentFlow).where(AssessmentFlow.id == assessment_flow_id)
    )
    assessment_flow = result.scalar_one()

    # Assert: Check 2 application groups created
    assert len(assessment_flow.application_asset_groups) == 2

    # Find CRM group
    crm_group = next(
        g
        for g in assessment_flow.application_asset_groups
        if g["canonical_application_name"] == "CRM System"
    )
    assert crm_group["asset_count"] == 2
    assert set(crm_group["asset_types"]) == {"server", "database"}
    assert crm_group["readiness_summary"]["ready"] == 2

    # Find ERP group
    erp_group = next(
        g
        for g in assessment_flow.application_asset_groups
        if g["canonical_application_name"] == "ERP System"
    )
    assert erp_group["asset_count"] == 1
    assert erp_group["asset_types"] == ["server"]
    assert erp_group["readiness_summary"]["not_ready"] == 1

    # Assert: Check canonical application IDs
    assert len(assessment_flow.selected_canonical_application_ids) == 2
    assert str(crm_app.id) in assessment_flow.selected_canonical_application_ids
    assert str(erp_app.id) in assessment_flow.selected_canonical_application_ids


@pytest.mark.asyncio
async def test_create_assessment_flow_backward_compatibility(
    async_db_session: AsyncSession,
):
    """Integration test uses async_db_session fixture."""
    db_session = async_db_session
    """
    Test that old selected_application_ids field is still populated for backward compatibility.

    Scenario:
    - Create assessment flow
    - Verify BOTH selected_application_ids (old) and selected_asset_ids (new) populated
    """
    # Setup: Generate tenant context
    client_account_id = DEMO_CLIENT_ACCOUNT_ID
    engagement_id = DEMO_ENGAGEMENT_ID

    # Setup: Create asset
    asset = Asset(
        id=uuid4(),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        asset_name="Test Asset",
        name="Test Asset",
        asset_type="server",
        assessment_readiness="ready",
        assessment_readiness_score=0.8,
    )
    db_session.add(asset)
    await db_session.commit()

    # Execute: Create assessment flow
    flow_commands = FlowCommands(db=db_session, client_account_id=client_account_id)
    assessment_flow_id = await flow_commands.create_assessment_flow(
        engagement_id=engagement_id,
        selected_application_ids=[str(asset.id)],
        created_by="test_user",
    )

    # Query created flow
    result = await db_session.execute(
        select(AssessmentFlow).where(AssessmentFlow.id == assessment_flow_id)
    )
    assessment_flow = result.scalar_one()

    # Assert: Both old and new fields populated
    assert assessment_flow.selected_application_ids == [str(asset.id)]
    assert assessment_flow.selected_asset_ids == [str(asset.id)]
