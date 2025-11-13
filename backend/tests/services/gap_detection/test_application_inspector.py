"""
Unit tests for ApplicationInspector.

Tests CanonicalApplication metadata completeness including:
- Application metadata fields
- Technology stack completeness
- Business context fields
- Completeness scoring
- No application linked scenario

Performance target: <10ms per asset
"""

import pytest
from unittest.mock import Mock

from app.services.gap_detection.inspectors.application_inspector import (
    ApplicationInspector,
)
from app.services.gap_detection.schemas import DataRequirements


@pytest.mark.asyncio
async def test_application_inspector_complete():
    """Test asset with complete CanonicalApplication."""
    asset = Mock()
    asset.id = "test-asset-id"
    asset.asset_name = "Test Server"

    application = Mock()
    application.id = "test-app-id"
    application.canonical_name = "CRM System"
    application.description = "Customer relationship management system"
    application.application_type = "web_application"
    application.business_criticality = "tier_1_critical"
    application.technology_stack = {"languages": ["Python"], "frameworks": ["Django"]}
    application.created_by = "user-uuid"
    application.updated_by = "user-uuid"

    requirements = DataRequirements()

    inspector = ApplicationInspector()
    report = await inspector.inspect(
        asset=asset,
        application=application,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score == 1.0
    assert len(report.missing_metadata) == 0
    assert len(report.incomplete_tech_stack) == 0
    assert len(report.missing_business_context) == 0


@pytest.mark.asyncio
async def test_application_inspector_no_application():
    """Test asset with no CanonicalApplication linked."""
    asset = Mock()
    asset.id = "test-asset-id"
    asset.asset_name = "Orphan Server"

    requirements = DataRequirements()

    inspector = ApplicationInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score == 0.0
    assert len(report.missing_metadata) == 4  # All metadata fields missing
    assert len(report.incomplete_tech_stack) == 1  # Tech stack missing
    assert len(report.missing_business_context) == 2  # Business context missing


@pytest.mark.asyncio
async def test_application_inspector_missing_metadata():
    """Test application with missing metadata fields."""
    asset = Mock()
    asset.id = "test-asset-id"

    application = Mock()
    application.id = "test-app-id"
    application.canonical_name = "CRM System"
    application.description = None  # Missing
    application.application_type = ""  # Empty
    application.business_criticality = None  # Missing
    application.technology_stack = {"languages": ["Python"]}
    application.created_by = "user-uuid"
    application.updated_by = "user-uuid"

    requirements = DataRequirements()

    inspector = ApplicationInspector()
    report = await inspector.inspect(
        asset=asset,
        application=application,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score < 1.0
    assert "description" in report.missing_metadata
    assert "application_type" in report.missing_metadata
    assert "business_criticality" in report.missing_metadata


@pytest.mark.asyncio
async def test_application_inspector_empty_tech_stack():
    """Test application with empty technology stack."""
    asset = Mock()
    asset.id = "test-asset-id"

    application = Mock()
    application.id = "test-app-id"
    application.canonical_name = "Legacy App"
    application.description = "Old system"
    application.application_type = "legacy"
    application.business_criticality = "tier_3"
    application.technology_stack = None  # Missing
    application.created_by = "user-uuid"
    application.updated_by = "user-uuid"

    requirements = DataRequirements()

    inspector = ApplicationInspector()
    report = await inspector.inspect(
        asset=asset,
        application=application,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert "technology_stack" in report.incomplete_tech_stack


@pytest.mark.asyncio
async def test_application_inspector_empty_dict_tech_stack():
    """Test application with empty dict technology stack."""
    asset = Mock()
    asset.id = "test-asset-id"

    application = Mock()
    application.id = "test-app-id"
    application.canonical_name = "New App"
    application.description = "New system"
    application.application_type = "microservice"
    application.business_criticality = "tier_2"
    application.technology_stack = {}  # Empty dict
    application.created_by = "user-uuid"
    application.updated_by = "user-uuid"

    requirements = DataRequirements()

    inspector = ApplicationInspector()
    report = await inspector.inspect(
        asset=asset,
        application=application,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert "technology_stack" in report.incomplete_tech_stack


@pytest.mark.asyncio
async def test_application_inspector_missing_business_context():
    """Test application with missing business context fields."""
    asset = Mock()
    asset.id = "test-asset-id"

    application = Mock()
    application.id = "test-app-id"
    application.canonical_name = "Test App"
    application.description = "Test"
    application.application_type = "test"
    application.business_criticality = "tier_3"
    application.technology_stack = {"languages": ["Go"]}
    application.created_by = None  # Missing
    application.updated_by = None  # Missing

    requirements = DataRequirements()

    inspector = ApplicationInspector()
    report = await inspector.inspect(
        asset=asset,
        application=application,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert "created_by" in report.missing_business_context
    assert "updated_by" in report.missing_business_context


@pytest.mark.asyncio
async def test_application_inspector_partial_completeness():
    """Test partial completeness scoring."""
    asset = Mock()
    asset.id = "test-asset-id"

    application = Mock()
    application.id = "test-app-id"
    application.canonical_name = "Partial App"
    application.description = "Description"
    application.application_type = None  # Missing (2 of 4 metadata)
    application.business_criticality = None  # Missing
    application.technology_stack = {"languages": ["Java"]}  # Present (1 of 1 tech)
    application.created_by = "user-uuid"  # Present (2 of 2 business)
    application.updated_by = "user-uuid"

    requirements = DataRequirements()

    inspector = ApplicationInspector()
    report = await inspector.inspect(
        asset=asset,
        application=application,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    # Total: 4 metadata + 1 tech + 2 business = 7 fields
    # Present: 2 metadata + 1 tech + 2 business = 5 fields
    # Score: 5/7 ≈ 0.714
    assert 0.71 <= report.completeness_score <= 0.72


@pytest.mark.asyncio
async def test_application_inspector_whitespace_values():
    """Test handling of whitespace-only values."""
    asset = Mock()
    asset.id = "test-asset-id"

    application = Mock()
    application.id = "test-app-id"
    application.canonical_name = "   "  # Whitespace only
    application.description = "\t\n"  # Whitespace only
    application.application_type = "web"
    application.business_criticality = "tier_1"
    application.technology_stack = {"languages": ["Python"]}
    application.created_by = "   "  # Whitespace only
    application.updated_by = "user-uuid"

    requirements = DataRequirements()

    inspector = ApplicationInspector()
    report = await inspector.inspect(
        asset=asset,
        application=application,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert "canonical_name" in report.missing_metadata
    assert "description" in report.missing_metadata
    assert "created_by" in report.missing_business_context


@pytest.mark.asyncio
async def test_application_inspector_none_asset():
    """Test error handling for None asset."""
    requirements = DataRequirements()

    inspector = ApplicationInspector()

    with pytest.raises(ValueError, match="Asset cannot be None"):
        await inspector.inspect(
            asset=None,
            application=None,
            requirements=requirements,
            client_account_id="test-client",
            engagement_id="test-engagement",
        )
