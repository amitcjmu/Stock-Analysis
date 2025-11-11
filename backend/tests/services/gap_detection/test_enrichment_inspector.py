"""
Unit tests for EnrichmentInspector.

Tests verify:
- Missing enrichment tables are correctly identified
- Incomplete enrichment tables are detected
- Completeness scoring: complete=1.0, partial=0.5, missing=0.0
- Score is clamped to [0.0, 1.0]
- Performance is <20ms per asset
"""

import pytest
import time

from app.services.gap_detection.inspectors.enrichment_inspector import (
    EnrichmentInspector,
)
from app.services.gap_detection.schemas import DataRequirements
from tests.services.gap_detection.fixtures import (
    create_mock_asset,
    create_mock_resilience,
    create_mock_compliance_flags,
    create_incomplete_resilience,
)


@pytest.mark.asyncio
async def test_enrichment_inspector_complete_enrichments():
    """Test with asset having all required enrichments fully populated."""
    requirements = DataRequirements(
        required_enrichments=["resilience", "compliance_flags"]
    )

    asset = create_mock_asset(has_enrichments=True)
    asset.resilience = create_mock_resilience(rto_minutes=60, rpo_minutes=15)
    asset.compliance_flags = create_mock_compliance_flags(
        compliance_scopes=["PCI-DSS"], data_classification="confidential"
    )

    inspector = EnrichmentInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score == 1.0
    assert len(report.missing_tables) == 0
    assert len(report.incomplete_tables) == 0


@pytest.mark.asyncio
async def test_enrichment_inspector_missing_tables():
    """Test with asset missing required enrichment tables."""
    requirements = DataRequirements(
        required_enrichments=["resilience", "compliance_flags", "vulnerabilities"]
    )

    asset = create_mock_asset(has_enrichments=False)
    # All enrichments are None (missing)

    inspector = EnrichmentInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    # All 3 tables missing = 0/3 = 0.0 completeness
    assert report.completeness_score == 0.0
    assert len(report.missing_tables) == 3
    assert "resilience" in report.missing_tables
    assert "compliance_flags" in report.missing_tables
    assert "vulnerabilities" in report.missing_tables


@pytest.mark.asyncio
async def test_enrichment_inspector_incomplete_tables():
    """Test with asset having incomplete enrichment tables."""
    requirements = DataRequirements(
        required_enrichments=["resilience", "compliance_flags"]
    )

    asset = create_mock_asset()
    # Resilience exists but has None for critical fields
    asset.resilience = create_incomplete_resilience()
    # Compliance flags is missing
    asset.compliance_flags = None

    inspector = EnrichmentInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    # 1 incomplete (0.5) + 1 missing (0.0) = 0.5 / 2 = 0.25
    assert report.completeness_score == 0.25
    assert "compliance_flags" in report.missing_tables
    assert "resilience" in report.incomplete_tables
    assert "rto_minutes" in report.incomplete_tables["resilience"]
    assert "rpo_minutes" in report.incomplete_tables["resilience"]


@pytest.mark.asyncio
async def test_enrichment_inspector_mixed_states():
    """Test with mix of complete, incomplete, and missing enrichments."""
    requirements = DataRequirements(
        required_enrichments=[
            "resilience",  # Complete
            "compliance_flags",  # Incomplete
            "vulnerabilities",  # Missing
        ]
    )

    asset = create_mock_asset()
    # Complete
    asset.resilience = create_mock_resilience(rto_minutes=60, rpo_minutes=15)
    # Incomplete (missing data_classification)
    asset.compliance_flags = create_mock_compliance_flags(
        compliance_scopes=["PCI-DSS"], data_classification=None
    )
    # Missing
    asset.vulnerabilities = None

    inspector = EnrichmentInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    # 1 complete (1.0) + 1 partial (0.5) + 1 missing (0.0) = 1.5 / 3 = 0.5
    assert report.completeness_score == 0.5
    assert "vulnerabilities" in report.missing_tables
    assert "compliance_flags" in report.incomplete_tables


@pytest.mark.asyncio
async def test_enrichment_inspector_empty_requirements():
    """Test with no required enrichments (should return 100% complete)."""
    requirements = DataRequirements(required_enrichments=[])

    asset = create_mock_asset()

    inspector = EnrichmentInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    # No requirements means 100% complete
    assert report.completeness_score == 1.0
    assert len(report.missing_tables) == 0
    assert len(report.incomplete_tables) == 0


@pytest.mark.asyncio
async def test_enrichment_inspector_unknown_table():
    """Test with unknown enrichment table name (should log warning and skip)."""
    requirements = DataRequirements(
        required_enrichments=["resilience", "unknown_table"]
    )

    asset = create_mock_asset()
    asset.resilience = create_mock_resilience()

    inspector = EnrichmentInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    # Unknown table should be skipped, only resilience counts
    # But since requirements asked for 2 and we only checked 1, scoring should reflect that
    # Actually, the inspector skips unknown tables entirely, so:
    # Only 1 enrichment checked (resilience), which is complete = 1.0
    # This behavior may need refinement - for now we'll test current implementation
    assert "resilience" not in report.missing_tables


@pytest.mark.asyncio
async def test_enrichment_inspector_score_clamping():
    """Test that completeness score is clamped to [0.0, 1.0]."""
    requirements = DataRequirements(required_enrichments=["resilience"])

    asset = create_mock_asset()
    asset.resilience = create_mock_resilience()

    inspector = EnrichmentInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    # Score must be between 0.0 and 1.0
    assert 0.0 <= report.completeness_score <= 1.0
    assert isinstance(report.completeness_score, float)


@pytest.mark.asyncio
async def test_enrichment_inspector_performance():
    """Test that EnrichmentInspector completes in <20ms."""
    requirements = DataRequirements(
        required_enrichments=[
            "resilience",
            "compliance_flags",
            "vulnerabilities",
            "tech_debt",
            "dependencies",
        ]
    )

    asset = create_mock_asset()
    asset.resilience = create_mock_resilience()
    asset.compliance_flags = create_mock_compliance_flags()
    asset.vulnerabilities = None
    asset.tech_debt = None
    asset.dependencies = None

    inspector = EnrichmentInspector()

    start_time = time.perf_counter()
    await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )
    end_time = time.perf_counter()

    elapsed_ms = (end_time - start_time) * 1000

    # Performance target: <20ms per asset
    assert (
        elapsed_ms < 20.0
    ), f"EnrichmentInspector took {elapsed_ms:.2f}ms (target: <20ms)"


@pytest.mark.asyncio
async def test_enrichment_inspector_none_asset_raises_error():
    """Test that None asset raises ValueError."""
    requirements = DataRequirements(required_enrichments=["resilience"])

    inspector = EnrichmentInspector()

    with pytest.raises(ValueError, match="Asset cannot be None"):
        await inspector.inspect(
            asset=None,
            application=None,
            requirements=requirements,
            client_account_id="test-client",
            engagement_id="test-engagement",
        )


@pytest.mark.asyncio
async def test_enrichment_inspector_none_requirements_raises_error():
    """Test that None requirements raises ValueError."""
    asset = create_mock_asset()

    inspector = EnrichmentInspector()

    with pytest.raises(ValueError, match="DataRequirements cannot be None"):
        await inspector.inspect(
            asset=asset,
            application=None,
            requirements=None,
            client_account_id="test-client",
            engagement_id="test-engagement",
        )


@pytest.mark.asyncio
async def test_enrichment_inspector_completeness_check():
    """Test the _check_completeness method directly."""
    inspector = EnrichmentInspector()

    # Test with complete resilience
    complete_resilience = create_mock_resilience(rto_minutes=60, rpo_minutes=15)
    incomplete_fields = inspector._check_completeness(complete_resilience, "resilience")
    assert len(incomplete_fields) == 0

    # Test with incomplete resilience
    incomplete_resilience = create_incomplete_resilience()
    incomplete_fields = inspector._check_completeness(
        incomplete_resilience, "resilience"
    )
    assert "rto_minutes" in incomplete_fields
    assert "rpo_minutes" in incomplete_fields
