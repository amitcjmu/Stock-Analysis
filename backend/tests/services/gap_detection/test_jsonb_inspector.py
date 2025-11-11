"""
Unit tests for JSONBInspector.

Tests JSONB field inspection including:
- Missing JSONB fields
- Empty values in JSONB
- Nested key checking with dot notation
- Completeness scoring
- Error handling

Performance target: <10ms per asset
"""

import pytest
from unittest.mock import Mock

from app.services.gap_detection.inspectors.jsonb_inspector import JSONBInspector
from app.services.gap_detection.schemas import DataRequirements


@pytest.mark.asyncio
async def test_jsonb_inspector_all_keys_present():
    """Test asset with all required JSONB keys present."""
    # Mock asset with complete JSONB data
    asset = Mock()
    asset.id = "test-asset-id"
    asset.asset_name = "Complete Server"
    asset.custom_attributes = {"environment": "production", "vm_type": "t2.large"}
    asset.technical_details = {
        "api_endpoints": ["https://api.example.com"],
        "dependencies": ["database", "cache"],
    }
    asset.metadata = {"documentation_url": "https://docs.example.com"}

    requirements = DataRequirements(
        required_jsonb_keys={
            "custom_attributes": ["environment", "vm_type"],
            "technical_details": ["api_endpoints", "dependencies"],
            "metadata": ["documentation_url"],
        }
    )

    inspector = JSONBInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score == 1.0
    assert len(report.missing_keys) == 0
    assert len(report.empty_values) == 0


@pytest.mark.asyncio
async def test_jsonb_inspector_missing_field():
    """Test asset with entire JSONB field missing."""
    asset = Mock()
    asset.id = "test-asset-id"
    asset.asset_name = "Incomplete Server"
    asset.custom_attributes = {"environment": "production"}
    # technical_details is missing entirely
    asset.technical_details = None
    asset.metadata = {}

    requirements = DataRequirements(
        required_jsonb_keys={
            "custom_attributes": ["environment"],
            "technical_details": ["api_endpoints", "dependencies"],
            "metadata": ["documentation_url"],
        }
    )

    inspector = JSONBInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score < 1.0
    assert "technical_details" in report.missing_keys
    assert report.missing_keys["technical_details"] == ["api_endpoints", "dependencies"]


@pytest.mark.asyncio
async def test_jsonb_inspector_missing_keys():
    """Test asset with JSONB field present but missing required keys."""
    asset = Mock()
    asset.id = "test-asset-id"
    asset.custom_attributes = {"environment": "production"}  # Missing vm_type
    asset.technical_details = {"api_endpoints": []}  # Missing dependencies
    asset.metadata = {}  # Missing documentation_url

    requirements = DataRequirements(
        required_jsonb_keys={
            "custom_attributes": ["environment", "vm_type"],
            "technical_details": ["api_endpoints", "dependencies"],
            "metadata": ["documentation_url"],
        }
    )

    inspector = JSONBInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score < 1.0
    assert "custom_attributes" in report.missing_keys
    assert "vm_type" in report.missing_keys["custom_attributes"]
    assert "technical_details" in report.missing_keys
    assert "dependencies" in report.missing_keys["technical_details"]


@pytest.mark.asyncio
async def test_jsonb_inspector_empty_values():
    """Test asset with JSONB keys present but empty values."""
    asset = Mock()
    asset.id = "test-asset-id"
    asset.custom_attributes = {"environment": "   ", "vm_type": ""}  # Empty strings
    asset.technical_details = {"api_endpoints": [], "dependencies": []}  # Empty lists
    asset.metadata = {"documentation_url": {}}  # Empty dict

    requirements = DataRequirements(
        required_jsonb_keys={
            "custom_attributes": ["environment", "vm_type"],
            "technical_details": ["api_endpoints", "dependencies"],
            "metadata": ["documentation_url"],
        }
    )

    inspector = JSONBInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score == 0.0
    assert "custom_attributes" in report.empty_values
    assert "technical_details" in report.empty_values
    assert "metadata" in report.empty_values


@pytest.mark.asyncio
async def test_jsonb_inspector_nested_keys():
    """Test nested key checking with dot notation."""
    asset = Mock()
    asset.id = "test-asset-id"
    asset.custom_attributes = {
        "deployment": {"strategy": "rolling", "region": "us-east-1"}
    }

    requirements = DataRequirements(
        required_jsonb_keys={
            "custom_attributes": ["deployment.strategy", "deployment.region"]
        }
    )

    inspector = JSONBInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score == 1.0
    assert len(report.missing_keys) == 0


@pytest.mark.asyncio
async def test_jsonb_inspector_nested_keys_missing():
    """Test nested key missing in JSONB."""
    asset = Mock()
    asset.id = "test-asset-id"
    asset.custom_attributes = {"deployment": {"strategy": "rolling"}}  # Missing region

    requirements = DataRequirements(
        required_jsonb_keys={
            "custom_attributes": ["deployment.strategy", "deployment.region"]
        }
    )

    inspector = JSONBInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score == 0.5
    assert "custom_attributes" in report.missing_keys
    assert "deployment.region" in report.missing_keys["custom_attributes"]


@pytest.mark.asyncio
async def test_jsonb_inspector_non_dict_field():
    """Test JSONB field that is not a dict."""
    asset = Mock()
    asset.id = "test-asset-id"
    asset.custom_attributes = "not a dict"  # Invalid type

    requirements = DataRequirements(
        required_jsonb_keys={"custom_attributes": ["environment"]}
    )

    inspector = JSONBInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score == 0.0
    assert "custom_attributes" in report.missing_keys


@pytest.mark.asyncio
async def test_jsonb_inspector_no_requirements():
    """Test with no JSONB requirements."""
    asset = Mock()
    asset.id = "test-asset-id"

    requirements = DataRequirements(required_jsonb_keys={})

    inspector = JSONBInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    assert report.completeness_score == 1.0
    assert len(report.missing_keys) == 0
    assert len(report.empty_values) == 0


@pytest.mark.asyncio
async def test_jsonb_inspector_partial_completeness():
    """Test partial completeness scoring."""
    asset = Mock()
    asset.id = "test-asset-id"
    asset.custom_attributes = {"environment": "production"}  # 1 of 2
    asset.technical_details = None  # 0 of 2

    requirements = DataRequirements(
        required_jsonb_keys={
            "custom_attributes": ["environment", "vm_type"],
            "technical_details": ["api_endpoints", "dependencies"],
        }
    )

    inspector = JSONBInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    # 1 found out of 4 total = 0.25
    assert report.completeness_score == 0.25


@pytest.mark.asyncio
async def test_jsonb_inspector_none_asset():
    """Test error handling for None asset."""
    requirements = DataRequirements(required_jsonb_keys={})

    inspector = JSONBInspector()

    with pytest.raises(ValueError, match="Asset cannot be None"):
        await inspector.inspect(
            asset=None,
            application=None,
            requirements=requirements,
            client_account_id="test-client",
            engagement_id="test-engagement",
        )


@pytest.mark.asyncio
async def test_jsonb_inspector_none_requirements():
    """Test error handling for None requirements."""
    asset = Mock()
    asset.id = "test-asset-id"

    inspector = JSONBInspector()

    with pytest.raises(ValueError, match="DataRequirements cannot be None"):
        await inspector.inspect(
            asset=asset,
            application=None,
            requirements=None,
            client_account_id="test-client",
            engagement_id="test-engagement",
        )
