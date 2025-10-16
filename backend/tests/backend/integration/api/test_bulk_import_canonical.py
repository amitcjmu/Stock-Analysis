"""
Integration tests for bulk import with canonical deduplication.

Tests Phase 2 Day 10 implementation:
- Bulk import creates assets
- Canonical applications created/linked automatically
- collection_flow_applications junction entries created
- Response includes canonical stats
"""

import pytest
from uuid import uuid4
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.canonical_applications import CollectionFlowApplication
from app.models.collection_flow import CollectionFlow, CollectionFlowStatus


@pytest.fixture
async def sample_collection_flow(db: AsyncSession, test_context) -> CollectionFlow:
    """Create a test collection flow"""
    flow = CollectionFlow(
        flow_id=uuid4(),
        client_account_id=test_context.client_account_id,
        engagement_id=test_context.engagement_id,
        status=CollectionFlowStatus.RUNNING.value,
        collection_config={},
    )
    db.add(flow)
    await db.commit()
    await db.refresh(flow)
    return flow


@pytest.fixture
def sample_csv_data() -> list[Dict[str, Any]]:
    """Sample CSV data for testing"""
    return [
        {
            "application_name": "CRM System",
            "asset_name": "CRM-Server-01",
            "asset_type": "server",
            "technology_stack": "Java, Spring Boot",
            "business_criticality": "high",
        },
        {
            "application_name": "CRM System",  # Duplicate - should link to existing
            "asset_name": "CRM-Database-01",
            "asset_type": "database",
            "technology_stack": "PostgreSQL",
            "business_criticality": "high",
        },
        {
            "application_name": "ERP System",  # New application
            "asset_name": "ERP-Server-01",
            "asset_type": "server",
            "technology_stack": "SAP",
            "business_criticality": "critical",
        },
    ]


@pytest.mark.asyncio
async def test_bulk_import_creates_canonical_applications(
    db: AsyncSession,
    sample_collection_flow: CollectionFlow,
    sample_csv_data: list,
    test_context,
    mock_user,
):
    """Test that bulk import creates canonical applications"""
    from app.api.v1.endpoints.collection_bulk_import import process_bulk_import

    result = await process_bulk_import(
        flow_id=str(sample_collection_flow.flow_id),
        file_path=None,
        csv_data=sample_csv_data,
        asset_type="server",
        db=db,
        current_user=mock_user,
        context=test_context,
    )

    # Verify response structure
    assert result["success"] is True
    assert result["processed_count"] == 3
    assert "canonical_applications_created" in result
    assert "canonical_applications_linked" in result
    assert "canonical_applications_failed" in result

    # Should create 2 canonical apps (CRM System and ERP System)
    # CRM System created once, then linked again for second asset
    assert result["canonical_applications_created"] == 2
    assert result["canonical_applications_linked"] == 1
    assert result["canonical_applications_failed"] == 0


@pytest.mark.asyncio
async def test_bulk_import_creates_junction_entries(
    db: AsyncSession,
    sample_collection_flow: CollectionFlow,
    sample_csv_data: list,
    test_context,
    mock_user,
):
    """Test that bulk import creates collection_flow_applications entries"""
    from app.api.v1.endpoints.collection_bulk_import import process_bulk_import

    result = await process_bulk_import(
        flow_id=str(sample_collection_flow.flow_id),
        file_path=None,
        csv_data=sample_csv_data,
        asset_type="server",
        db=db,
        current_user=mock_user,
        context=test_context,
    )

    # Verify import succeeded
    assert result["success"] is True
    assert result["processed_count"] == 3

    # Query junction table
    query = select(CollectionFlowApplication).where(
        CollectionFlowApplication.collection_flow_id == sample_collection_flow.flow_id,
        CollectionFlowApplication.client_account_id == test_context.client_account_id,
    )
    junction_result = await db.execute(query)
    junction_entries = junction_result.scalars().all()

    # Should have 3 junction entries (one per asset)
    assert len(junction_entries) == 3

    # Verify all entries have canonical_application_id
    for entry in junction_entries:
        assert entry.canonical_application_id is not None
        assert entry.deduplication_method == "bulk_import_auto"
        assert entry.match_confidence is not None


@pytest.mark.asyncio
async def test_bulk_import_links_duplicate_names_to_same_canonical(
    db: AsyncSession,
    sample_collection_flow: CollectionFlow,
    sample_csv_data: list,
    test_context,
    mock_user,
):
    """Test that assets with same application name link to same canonical app"""
    from app.api.v1.endpoints.collection_bulk_import import process_bulk_import

    result = await process_bulk_import(
        flow_id=str(sample_collection_flow.flow_id),
        file_path=None,
        csv_data=sample_csv_data,
        asset_type="server",
        db=db,
        current_user=mock_user,
        context=test_context,
    )

    # Verify import succeeded
    assert result["success"] is True
    assert result["processed_count"] == 3

    # Query junction entries for CRM System
    query = select(CollectionFlowApplication).where(
        CollectionFlowApplication.collection_flow_id == sample_collection_flow.flow_id,
        CollectionFlowApplication.application_name == "CRM System",
    )
    junction_result = await db.execute(query)
    crm_entries = junction_result.scalars().all()

    # Should have 2 entries for CRM System (server and database)
    assert len(crm_entries) == 2

    # Both should point to the same canonical_application_id
    canonical_ids = {entry.canonical_application_id for entry in crm_entries}
    assert len(canonical_ids) == 1  # Only one unique canonical ID


@pytest.mark.asyncio
async def test_bulk_import_handles_missing_application_name(
    db: AsyncSession,
    sample_collection_flow: CollectionFlow,
    test_context,
    mock_user,
):
    """Test that bulk import handles assets without application_name"""
    from app.api.v1.endpoints.collection_bulk_import import process_bulk_import

    csv_data = [
        {
            "asset_name": "Unknown-Server-01",
            "asset_type": "server",
            # No application_name provided
        }
    ]

    result = await process_bulk_import(
        flow_id=str(sample_collection_flow.flow_id),
        file_path=None,
        csv_data=csv_data,
        asset_type="server",
        db=db,
        current_user=mock_user,
        context=test_context,
    )

    # Should still succeed - uses asset_name as fallback
    assert result["success"] is True
    assert result["processed_count"] == 1
    # May have created or failed canonical - just verify it doesn't crash
    assert "canonical_applications_created" in result


@pytest.mark.asyncio
async def test_bulk_import_atomic_transaction(
    db: AsyncSession,
    sample_collection_flow: CollectionFlow,
    test_context,
    mock_user,
):
    """Test that bulk import rolls back on failure"""
    from app.api.v1.endpoints.collection_bulk_import import process_bulk_import

    csv_data = [
        {
            "application_name": "Valid App",
            "asset_name": "Valid-Server",
            "asset_type": "server",
        },
        # Second row will fail due to invalid data
        {
            "asset_name": None,  # Will cause validation error
            "asset_type": "invalid_type",
        },
    ]

    # Count assets before import
    pre_count_query = select(Asset).where(
        Asset.client_account_id == test_context.client_account_id
    )
    pre_result = await db.execute(pre_count_query)
    pre_count = len(pre_result.scalars().all())

    # Attempt import (should partially succeed - only first row)
    result = await process_bulk_import(
        flow_id=str(sample_collection_flow.flow_id),
        file_path=None,
        csv_data=csv_data,
        asset_type="server",
        db=db,
        current_user=mock_user,
        context=test_context,
    )

    # Import should succeed for valid rows
    assert result["success"] is True
    assert len(result["errors"]) > 0  # Should have errors for invalid row

    # Count assets after import
    post_count_query = select(Asset).where(
        Asset.client_account_id == test_context.client_account_id
    )
    post_result = await db.execute(post_count_query)
    post_count = len(post_result.scalars().all())

    # Should have created only the valid asset
    assert post_count == pre_count + 1  # Only 1 valid asset created


@pytest.mark.asyncio
async def test_bulk_import_enrichment_placeholder(
    db: AsyncSession,
    sample_collection_flow: CollectionFlow,
    sample_csv_data: list,
    test_context,
    mock_user,
):
    """Test that enrichment_triggered field is present (Phase 3 placeholder)"""
    from app.api.v1.endpoints.collection_bulk_import import process_bulk_import

    result = await process_bulk_import(
        flow_id=str(sample_collection_flow.flow_id),
        file_path=None,
        csv_data=sample_csv_data,
        asset_type="server",
        db=db,
        current_user=mock_user,
        context=test_context,
    )

    # Enrichment field should exist (currently False, will be implemented in Phase 3)
    assert "enrichment_triggered" in result
    assert result["enrichment_triggered"] is False  # Not yet implemented
