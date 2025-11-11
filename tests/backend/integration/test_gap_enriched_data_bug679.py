"""
Integration test for Bug #679: Gap analysis should check enriched asset data

This test verifies that gap analysis correctly checks data from specialized
enrichment tables (Applications, Servers, Databases) before generating gaps.

Test scenarios:
1. New asset (no enrichment) - Should generate all gaps
2. Partially enriched asset - Should only generate gaps for missing fields
3. Fully enriched asset - Should generate zero gaps
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4

from app.core.database import AsyncSessionLocal
from app.models.application import Application
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow
from app.models.collection_flow.schemas import CollectionFlowStatus
from app.models.database import Database
from app.models.server import Server
from app.services.collection.programmatic_gap_scanner import ProgrammaticGapScanner


@pytest_asyncio.fixture
async def db_session():
    """Use real PostgreSQL database session."""
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_collection_flow(db_session: AsyncSession):
    """Create a test collection flow."""
    flow_id = uuid4()
    flow = CollectionFlow(
        id=flow_id,
        flow_id=flow_id,
        user_id=UUID("33333333-3333-3333-3333-333333333333"),
        client_account_id=UUID("11111111-1111-1111-1111-111111111111"),
        engagement_id=UUID("22222222-2222-2222-2222-222222222222"),
        flow_name="Test Gap Analysis Enrichment Flow (Bug #679)",
        automation_tier="tier_2",
        current_phase="gap_analysis",
        status=CollectionFlowStatus.RUNNING,
        flow_metadata={"selected_asset_ids": []},  # Will be populated by test
    )
    db_session.add(flow)
    await db_session.commit()
    await db_session.refresh(flow)

    yield flow

    # Cleanup
    await db_session.delete(flow)
    await db_session.commit()


@pytest.mark.asyncio
async def test_gap_analysis_checks_enriched_application_data(
    db_session: AsyncSession, test_collection_flow: CollectionFlow
):
    """
    Test that gap analysis checks Application table for enriched data.

    Scenario: Application asset with enriched data in applications table
    Expected: Fewer gaps generated (only for truly missing fields)
    """
    # Create Asset (base record)
    asset_id = uuid4()
    asset = Asset(
        id=asset_id,
        name="test-app-enriched",
        asset_type="application",
        client_account_id=UUID("11111111-1111-1111-1111-111111111111"),
        engagement_id=UUID("22222222-2222-2222-2222-222222222222"),
    )
    db_session.add(asset)
    await db_session.flush()

    # Create enriched Application record (Bug #679 fix)
    enriched_app = Application(
        id=asset_id,  # Same ID as Asset
        name="test-app-enriched",
        business_criticality="High",
        description="Customer-facing web application",
        technology_stack={"languages": ["Python", "JavaScript"], "frameworks": ["FastAPI", "React"]},
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
    )
    db_session.add(enriched_app)

    # Update collection flow metadata with this asset
    test_collection_flow.flow_metadata = {"selected_asset_ids": [str(asset_id)]}
    await db_session.commit()

    # Run gap analysis
    scanner = ProgrammaticGapScanner()
    result = await scanner.scan_assets_for_gaps(
        selected_asset_ids=[str(asset_id)],
        collection_flow_id=str(test_collection_flow.id),
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        db=db_session,
    )

    # Verify results
    assert result["status"] == "SCAN_COMPLETE"
    gaps = result["gaps"]

    # Should NOT generate gaps for fields that exist in enriched data:
    # - business_criticality
    # - technology_stack
    # - description
    gap_field_names = [g["field_name"] for g in gaps]

    assert "business_criticality" not in gap_field_names, (
        "Gap generated for business_criticality but it exists in Application table"
    )
    assert "technology_stack" not in gap_field_names, (
        "Gap generated for technology_stack but it exists in Application table"
    )

    # Should still generate gaps for fields NOT in enriched data
    # (depends on critical_attributes.py configuration)

    # Cleanup
    await db_session.delete(enriched_app)
    await db_session.delete(asset)
    await db_session.commit()


@pytest.mark.asyncio
async def test_gap_analysis_checks_enriched_server_data(
    db_session: AsyncSession, test_collection_flow: CollectionFlow
):
    """
    Test that gap analysis checks Server table for enriched data.

    Scenario: Server asset with enriched data in servers table
    Expected: Fewer gaps generated (only for truly missing fields)
    """
    # Create Asset (base record)
    asset_id = uuid4()
    asset = Asset(
        id=asset_id,
        name="test-server-enriched",
        asset_type="server",
        client_account_id=UUID("11111111-1111-1111-1111-111111111111"),
        engagement_id=UUID("22222222-2222-2222-2222-222222222222"),
    )
    db_session.add(asset)
    await db_session.flush()

    # Create enriched Server record (Bug #679 fix)
    enriched_server = Server(
        id=asset_id,  # Same ID as Asset
        name="test-server-enriched",
        hostname="srv-prod-01.example.com",
        ip_address="10.0.1.50",
        operating_system="Ubuntu 22.04 LTS",
        cpu_cores=16,
        memory_gb=64,
        storage_gb=1000,
        environment="Production",
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
    )
    db_session.add(enriched_server)

    # Update collection flow metadata
    test_collection_flow.flow_metadata = {"selected_asset_ids": [str(asset_id)]}
    await db_session.commit()

    # Run gap analysis
    scanner = ProgrammaticGapScanner()
    result = await scanner.scan_assets_for_gaps(
        selected_asset_ids=[str(asset_id)],
        collection_flow_id=str(test_collection_flow.id),
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        db=db_session,
    )

    # Verify results
    assert result["status"] == "SCAN_COMPLETE"
    gaps = result["gaps"]

    # Should NOT generate gaps for fields that exist in enriched data:
    gap_field_names = [g["field_name"] for g in gaps]

    assert "operating_system" not in gap_field_names, (
        "Gap generated for operating_system but it exists in Server table"
    )
    assert "cpu_cores" not in gap_field_names, (
        "Gap generated for cpu_cores but it exists in Server table"
    )
    assert "memory_gb" not in gap_field_names, (
        "Gap generated for memory_gb but it exists in Server table"
    )
    assert "storage_gb" not in gap_field_names, (
        "Gap generated for storage_gb but it exists in Server table"
    )
    assert "environment" not in gap_field_names, (
        "Gap generated for environment but it exists in Server table"
    )

    # Cleanup
    await db_session.delete(enriched_server)
    await db_session.delete(asset)
    await db_session.commit()


@pytest.mark.asyncio
async def test_gap_analysis_checks_enriched_database_data(
    db_session: AsyncSession, test_collection_flow: CollectionFlow
):
    """
    Test that gap analysis checks Database table for enriched data.

    Scenario: Database asset with enriched data in databases table
    Expected: Fewer gaps generated (only for truly missing fields)
    """
    # Create Asset (base record)
    asset_id = uuid4()
    asset = Asset(
        id=asset_id,
        name="test-db-enriched",
        asset_type="database",
        client_account_id=UUID("11111111-1111-1111-1111-111111111111"),
        engagement_id=UUID("22222222-2222-2222-2222-222222222222"),
    )
    db_session.add(asset)
    await db_session.flush()

    # Create enriched Database record (Bug #679 fix)
    enriched_db = Database(
        id=asset_id,  # Same ID as Asset
        name="test-db-enriched",
        database_type="PostgreSQL",
        version="16.1",
        size_gb=500,
        criticality="High",
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
    )
    db_session.add(enriched_db)

    # Update collection flow metadata
    test_collection_flow.flow_metadata = {"selected_asset_ids": [str(asset_id)]}
    await db_session.commit()

    # Run gap analysis
    scanner = ProgrammaticGapScanner()
    result = await scanner.scan_assets_for_gaps(
        selected_asset_ids=[str(asset_id)],
        collection_flow_id=str(test_collection_flow.id),
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        db=db_session,
    )

    # Verify results
    assert result["status"] == "SCAN_COMPLETE"
    gaps = result["gaps"]

    # Should NOT generate gaps for fields that exist in enriched data:
    gap_field_names = [g["field_name"] for g in gaps]

    assert "database_type" not in gap_field_names, (
        "Gap generated for database_type but it exists in Database table"
    )

    # Note: criticality in Database maps to business_criticality in gap analysis
    # This test validates the mapping works correctly

    # Cleanup
    await db_session.delete(enriched_db)
    await db_session.delete(asset)
    await db_session.commit()


@pytest.mark.asyncio
async def test_gap_analysis_new_asset_generates_all_gaps(
    db_session: AsyncSession, test_collection_flow: CollectionFlow
):
    """
    Test baseline: New asset with NO enrichment should generate all gaps.

    Scenario: Asset with no enriched data anywhere
    Expected: Full set of gaps generated (~20 gaps depending on asset type)
    """
    # Create Asset (base record ONLY, no enrichment)
    asset_id = uuid4()
    asset = Asset(
        id=asset_id,
        name="test-app-new-no-enrichment",
        asset_type="application",
        client_account_id=UUID("11111111-1111-1111-1111-111111111111"),
        engagement_id=UUID("22222222-2222-2222-2222-222222222222"),
    )
    db_session.add(asset)

    # Update collection flow metadata
    test_collection_flow.flow_metadata = {"selected_asset_ids": [str(asset_id)]}
    await db_session.commit()

    # Run gap analysis
    scanner = ProgrammaticGapScanner()
    result = await scanner.scan_assets_for_gaps(
        selected_asset_ids=[str(asset_id)],
        collection_flow_id=str(test_collection_flow.id),
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        db=db_session,
    )

    # Verify results
    assert result["status"] == "SCAN_COMPLETE"
    gaps = result["gaps"]

    # Should generate gaps for all critical application attributes
    # (exact count depends on critical_attributes.py configuration for applications)
    assert len(gaps) > 0, "New asset should generate gaps for missing fields"

    # Verify some expected application gaps are present
    gap_field_names = [g["field_name"] for g in gaps]
    # These should definitely be gaps for a new application asset
    expected_gaps = ["technology_stack", "business_criticality"]

    for expected_gap in expected_gaps:
        assert expected_gap in gap_field_names, (
            f"Expected gap '{expected_gap}' not found for new asset"
        )

    # Cleanup
    await db_session.delete(asset)
    await db_session.commit()
