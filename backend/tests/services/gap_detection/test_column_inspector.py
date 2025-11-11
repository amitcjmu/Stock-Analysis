"""
Unit tests for ColumnInspector.

Tests verify:
- Complete assets return 100% completeness score
- Missing fields are correctly identified
- Empty strings are detected as gaps
- Null values are detected as gaps
- Empty lists/dicts are detected as gaps
- System columns are excluded from gap analysis
- Score is clamped to [0.0, 1.0]
- Performance is <10ms per asset
"""

import pytest
import time

from app.services.gap_detection.inspectors.column_inspector import ColumnInspector
from app.services.gap_detection.schemas import DataRequirements
from tests.services.gap_detection.fixtures import create_mock_asset


@pytest.mark.asyncio
async def test_column_inspector_complete_asset():
    """Test with asset having all required fields."""
    requirements = DataRequirements(
        required_columns=["asset_name", "technology_stack", "cpu_cores"]
    )

    asset = create_mock_asset(
        asset_name="Test App",
        technology_stack="Python/Django",
        cpu_cores=4,
    )

    inspector = ColumnInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score == 1.0
    assert len(report.missing_attributes) == 0
    assert len(report.empty_attributes) == 0
    assert len(report.null_attributes) == 0


@pytest.mark.asyncio
async def test_column_inspector_missing_fields():
    """Test with asset missing required fields."""
    requirements = DataRequirements(
        required_columns=["asset_name", "technology_stack", "cpu_cores", "memory_gb"]
    )

    asset = create_mock_asset(
        asset_name="Test App",
        technology_stack="",  # Empty string
        cpu_cores=None,  # Null
        memory_gb=None,  # Null
    )

    inspector = ColumnInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    # Only 1/4 fields are complete
    assert report.completeness_score == 0.25

    # Empty string detected
    assert "technology_stack" in report.empty_attributes

    # Null values detected
    assert "cpu_cores" in report.null_attributes
    assert "memory_gb" in report.null_attributes


@pytest.mark.asyncio
async def test_column_inspector_empty_list():
    """Test with asset having empty list."""
    requirements = DataRequirements(required_columns=["some_list_field"])

    asset = create_mock_asset()
    asset.some_list_field = []  # Empty list

    inspector = ColumnInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score == 0.0
    assert "some_list_field" in report.empty_attributes


@pytest.mark.asyncio
async def test_column_inspector_empty_dict():
    """Test with asset having empty dict."""
    requirements = DataRequirements(required_columns=["some_dict_field"])

    asset = create_mock_asset()
    asset.some_dict_field = {}  # Empty dict

    inspector = ColumnInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score == 0.0
    assert "some_dict_field" in report.empty_attributes


@pytest.mark.asyncio
async def test_column_inspector_system_columns_excluded():
    """Test that system columns are excluded from gap analysis."""
    requirements = DataRequirements(
        required_columns=[
            "asset_name",
            "id",  # System column - should be excluded
            "created_at",  # System column - should be excluded
            "client_account_id",  # System column - should be excluded
        ]
    )

    asset = create_mock_asset(asset_name="Test App")

    inspector = ColumnInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    # System columns should be excluded, so only asset_name counts
    # Score should be 1.0 (1 required non-system column, 1 found)
    assert report.completeness_score == 1.0
    assert "id" not in report.missing_attributes
    assert "created_at" not in report.missing_attributes
    assert "client_account_id" not in report.missing_attributes


@pytest.mark.asyncio
async def test_column_inspector_score_clamping():
    """Test that completeness score is clamped to [0.0, 1.0]."""
    requirements = DataRequirements(required_columns=["asset_name"])

    asset = create_mock_asset(asset_name="Test App")

    inspector = ColumnInspector()
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
async def test_column_inspector_no_requirements():
    """Test with empty requirements list (should return 100% complete)."""
    requirements = DataRequirements(required_columns=[])

    asset = create_mock_asset()

    inspector = ColumnInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    # No requirements means 100% complete
    assert report.completeness_score == 1.0
    assert len(report.missing_attributes) == 0


@pytest.mark.asyncio
async def test_column_inspector_performance():
    """Test that ColumnInspector completes in <10ms."""
    requirements = DataRequirements(
        required_columns=[
            "asset_name",
            "technology_stack",
            "cpu_cores",
            "memory_gb",
            "operating_system",
        ]
    )

    asset = create_mock_asset()

    inspector = ColumnInspector()

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

    # Performance target: <10ms per asset
    assert elapsed_ms < 10.0, f"ColumnInspector took {elapsed_ms:.2f}ms (target: <10ms)"


@pytest.mark.asyncio
async def test_column_inspector_none_asset_raises_error():
    """Test that None asset raises ValueError."""
    requirements = DataRequirements(required_columns=["asset_name"])

    inspector = ColumnInspector()

    with pytest.raises(ValueError, match="Asset cannot be None"):
        await inspector.inspect(
            asset=None,
            application=None,
            requirements=requirements,
            client_account_id="test-client",
            engagement_id="test-engagement",
        )


@pytest.mark.asyncio
async def test_column_inspector_none_requirements_raises_error():
    """Test that None requirements raises ValueError."""
    asset = create_mock_asset()

    inspector = ColumnInspector()

    with pytest.raises(ValueError, match="DataRequirements cannot be None"):
        await inspector.inspect(
            asset=asset,
            application=None,
            requirements=None,
            client_account_id="test-client",
            engagement_id="test-engagement",
        )
