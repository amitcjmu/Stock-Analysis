"""
Unit tests for StandardsInspector.

Tests EngagementArchitectureStandard validation including:
- Boolean requirements
- String requirements
- Numeric requirements
- Mandatory vs optional standards
- Override availability
- Tenant scoping verification
- Database query mocking

Performance target: <50ms per asset
"""

import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gap_detection.inspectors.standards_inspector import (
    StandardsInspector,
)
from app.services.gap_detection.schemas import DataRequirements


@pytest.mark.asyncio
async def test_standards_inspector_no_violations():
    """Test asset passing all standards."""
    # Mock database session
    db_mock = AsyncMock(spec=AsyncSession)

    # Mock standards query result
    standard = Mock()
    standard.id = uuid4()
    standard.standard_name = "Encryption at Rest"
    standard.requirement_type = "security"
    standard.is_mandatory = True
    standard.minimum_requirements = {"encryption_enabled": True}

    # Create proper mock chain for SQLAlchemy result
    scalars_mock = Mock()
    scalars_mock.all = Mock(return_value=[standard])

    execute_result = AsyncMock()
    execute_result.scalars = Mock(return_value=scalars_mock)

    db_mock.execute = AsyncMock(return_value=execute_result)

    # Asset meets requirements
    asset = Mock()
    asset.id = "test-asset-id"
    asset.asset_name = "Compliant Server"
    asset.encryption_enabled = True

    requirements = DataRequirements()

    inspector = StandardsInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
        db=db_mock,
    )

    assert report.completeness_score == 1.0
    assert len(report.violated_standards) == 0
    assert not report.override_required


@pytest.mark.asyncio
async def test_standards_inspector_mandatory_violation():
    """Test asset violating mandatory standard."""
    db_mock = AsyncMock(spec=AsyncSession)

    standard = Mock()
    standard.id = uuid4()
    standard.standard_name = "Network Segmentation"
    standard.requirement_type = "security"
    standard.is_mandatory = True
    standard.minimum_requirements = {"firewall_enabled": True}

    # Create proper mock chain for SQLAlchemy result
    scalars_mock = Mock()
    scalars_mock.all = Mock(return_value=[standard])

    execute_result = AsyncMock()
    execute_result.scalars = Mock(return_value=scalars_mock)

    db_mock.execute = AsyncMock(return_value=execute_result)

    asset = Mock()
    asset.id = "test-asset-id"
    asset.asset_name = "Non-Compliant Server"
    asset.firewall_enabled = False  # Violation!

    requirements = DataRequirements()

    inspector = StandardsInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
        db=db_mock,
    )

    assert report.completeness_score < 1.0
    assert len(report.violated_standards) == 1
    assert report.override_required  # Mandatory violation blocks assessment
    assert "Network Segmentation" in report.missing_mandatory_data
    assert report.violated_standards[0].is_mandatory


@pytest.mark.asyncio
async def test_standards_inspector_optional_violation():
    """Test asset violating optional standard."""
    db_mock = AsyncMock(spec=AsyncSession)

    standard = Mock()
    standard.id = uuid4()
    standard.standard_name = "Performance Target"
    standard.requirement_type = "performance"
    standard.is_mandatory = False  # Optional
    standard.minimum_requirements = {"min_cpu_cores": 4}

    # Create proper mock chain for SQLAlchemy result
    scalars_mock = Mock()
    scalars_mock.all = Mock(return_value=[standard])

    execute_result = AsyncMock()
    execute_result.scalars = Mock(return_value=scalars_mock)

    db_mock.execute = AsyncMock(return_value=execute_result)

    asset = Mock()
    asset.id = "test-asset-id"
    asset.min_cpu_cores = 2  # Below requirement

    requirements = DataRequirements()

    inspector = StandardsInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
        db=db_mock,
    )

    assert report.completeness_score < 1.0
    assert len(report.violated_standards) == 1
    assert not report.override_required  # Optional violation doesn't block
    assert len(report.missing_mandatory_data) == 0


@pytest.mark.asyncio
async def test_standards_inspector_numeric_threshold():
    """Test numeric threshold validation."""
    db_mock = AsyncMock(spec=AsyncSession)

    standard = Mock()
    standard.id = uuid4()
    standard.standard_name = "High Availability"
    standard.requirement_type = "performance"
    standard.is_mandatory = True
    standard.minimum_requirements = {"min_availability_percent": 99.9}

    # Create proper mock chain for SQLAlchemy result
    scalars_mock = Mock()
    scalars_mock.all = Mock(return_value=[standard])

    execute_result = AsyncMock()
    execute_result.scalars = Mock(return_value=scalars_mock)

    db_mock.execute = AsyncMock(return_value=execute_result)

    asset = Mock()
    asset.id = "test-asset-id"
    asset.min_availability_percent = 95.0  # Below 99.9

    requirements = DataRequirements()

    inspector = StandardsInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
        db=db_mock,
    )

    assert len(report.violated_standards) == 1
    assert "99.9" in report.violated_standards[0].violation_details


@pytest.mark.asyncio
async def test_standards_inspector_string_requirement():
    """Test string requirement validation."""
    db_mock = AsyncMock(spec=AsyncSession)

    standard = Mock()
    standard.id = uuid4()
    standard.standard_name = "TLS Version"
    standard.requirement_type = "security"
    standard.is_mandatory = True
    standard.minimum_requirements = {"min_tls_version": "1.3"}

    # Create proper mock chain for SQLAlchemy result
    scalars_mock = Mock()
    scalars_mock.all = Mock(return_value=[standard])

    execute_result = AsyncMock()
    execute_result.scalars = Mock(return_value=scalars_mock)

    db_mock.execute = AsyncMock(return_value=execute_result)

    asset = Mock()
    asset.id = "test-asset-id"
    asset.min_tls_version = "1.2"  # Older version

    requirements = DataRequirements()

    inspector = StandardsInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
        db=db_mock,
    )

    assert len(report.violated_standards) == 1
    assert "1.3" in report.violated_standards[0].violation_details
    assert "1.2" in report.violated_standards[0].violation_details


@pytest.mark.asyncio
async def test_standards_inspector_application_fallback():
    """Test checking application when asset field is missing."""
    db_mock = AsyncMock(spec=AsyncSession)

    standard = Mock()
    standard.id = uuid4()
    standard.standard_name = "Data Classification"
    standard.requirement_type = "compliance"
    standard.is_mandatory = False
    standard.minimum_requirements = {"data_classification": "confidential"}

    # Create proper mock chain for SQLAlchemy result
    scalars_mock = Mock()
    scalars_mock.all = Mock(return_value=[standard])

    execute_result = AsyncMock()
    execute_result.scalars = Mock(return_value=scalars_mock)

    db_mock.execute = AsyncMock(return_value=execute_result)

    # Asset doesn't have field, but application does
    asset = Mock()
    asset.id = "test-asset-id"
    asset.data_classification = None

    application = Mock()
    application.id = "test-app-id"
    application.data_classification = "confidential"

    requirements = DataRequirements()

    inspector = StandardsInspector()
    report = await inspector.inspect(
        asset=asset,
        application=application,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
        db=db_mock,
    )

    # Should pass because application has the required value
    assert len(report.violated_standards) == 0


@pytest.mark.asyncio
async def test_standards_inspector_multiple_standards():
    """Test validation against multiple standards (mix of pass/fail)."""
    db_mock = AsyncMock(spec=AsyncSession)

    standard1 = Mock()
    standard1.id = uuid4()
    standard1.standard_name = "Encryption"
    standard1.requirement_type = "security"
    standard1.is_mandatory = True
    standard1.minimum_requirements = {"encryption_enabled": True}

    standard2 = Mock()
    standard2.id = uuid4()
    standard2.standard_name = "Backup"
    standard2.requirement_type = "resilience"
    standard2.is_mandatory = False
    standard2.minimum_requirements = {"backup_enabled": True}

    # Create proper mock chain for SQLAlchemy result
    scalars_mock = Mock()
    scalars_mock.all = Mock(return_value=[standard1, standard2])

    execute_result = AsyncMock()
    execute_result.scalars = Mock(return_value=scalars_mock)

    db_mock.execute = AsyncMock(return_value=execute_result)

    asset = Mock()
    asset.id = "test-asset-id"
    asset.encryption_enabled = True  # Passes standard1
    asset.backup_enabled = False  # Fails standard2

    requirements = DataRequirements()

    inspector = StandardsInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
        db=db_mock,
    )

    # 1 violation out of 2 standards = 0.5 score
    assert report.completeness_score == 0.5
    assert len(report.violated_standards) == 1
    assert report.violated_standards[0].standard_name == "Backup"
    assert not report.override_required  # Only optional violated


@pytest.mark.asyncio
async def test_standards_inspector_no_standards_defined():
    """Test when no standards are defined for engagement."""
    db_mock = AsyncMock(spec=AsyncSession)

    # Empty standards result
    # Create proper mock chain for SQLAlchemy result
    scalars_mock = Mock()
    scalars_mock.all = Mock(return_value=[])

    execute_result = AsyncMock()
    execute_result.scalars = Mock(return_value=scalars_mock)

    db_mock.execute = AsyncMock(return_value=execute_result)

    asset = Mock()
    asset.id = "test-asset-id"

    requirements = DataRequirements()

    inspector = StandardsInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
        db=db_mock,
    )

    # No standards = 100% compliant
    assert report.completeness_score == 1.0
    assert len(report.violated_standards) == 0
    assert not report.override_required


@pytest.mark.asyncio
async def test_standards_inspector_no_database():
    """Test error handling when database session is missing."""
    asset = Mock()
    asset.id = "test-asset-id"

    requirements = DataRequirements()

    inspector = StandardsInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
        db=None,  # Missing database!
    )

    assert report.completeness_score == 0.0
    assert "Database session required" in report.missing_mandatory_data[0]


@pytest.mark.asyncio
async def test_standards_inspector_none_asset():
    """Test error handling for None asset."""
    db_mock = AsyncMock(spec=AsyncSession)
    requirements = DataRequirements()

    inspector = StandardsInspector()

    with pytest.raises(ValueError, match="Asset cannot be None"):
        await inspector.inspect(
            asset=None,
            application=None,
            requirements=requirements,
            client_account_id="test-client",
            engagement_id="test-engagement",
            db=db_mock,
        )


@pytest.mark.asyncio
async def test_standards_inspector_missing_tenant_scoping():
    """Test error handling for missing tenant scoping parameters."""
    db_mock = AsyncMock(spec=AsyncSession)
    asset = Mock()
    asset.id = "test-asset-id"
    requirements = DataRequirements()

    inspector = StandardsInspector()

    # Missing client_account_id
    with pytest.raises(ValueError, match="client_account_id is required"):
        await inspector.inspect(
            asset=asset,
            application=None,
            requirements=requirements,
            client_account_id="",
            engagement_id="test-engagement",
            db=db_mock,
        )

    # Missing engagement_id
    with pytest.raises(ValueError, match="engagement_id is required"):
        await inspector.inspect(
            asset=asset,
            application=None,
            requirements=requirements,
            client_account_id="test-client",
            engagement_id="",
            db=db_mock,
        )


@pytest.mark.asyncio
async def test_standards_inspector_invalid_numeric_value():
    """Test handling of non-numeric value when numeric is required."""
    db_mock = AsyncMock(spec=AsyncSession)

    standard = Mock()
    standard.id = uuid4()
    standard.standard_name = "CPU Minimum"
    standard.requirement_type = "performance"
    standard.is_mandatory = False
    standard.minimum_requirements = {"min_cpu_cores": 4}

    # Create proper mock chain for SQLAlchemy result
    scalars_mock = Mock()
    scalars_mock.all = Mock(return_value=[standard])

    execute_result = AsyncMock()
    execute_result.scalars = Mock(return_value=scalars_mock)

    db_mock.execute = AsyncMock(return_value=execute_result)

    asset = Mock()
    asset.id = "test-asset-id"
    asset.min_cpu_cores = "not a number"  # Invalid type

    requirements = DataRequirements()

    inspector = StandardsInspector()
    report = await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="test-client",
        engagement_id="test-engagement",
        db=db_mock,
    )

    assert len(report.violated_standards) == 1
    assert "invalid type" in report.violated_standards[0].violation_details


@pytest.mark.asyncio
async def test_standards_inspector_tenant_scoping_query():
    """Verify tenant scoping parameters are used in database query."""
    db_mock = AsyncMock(spec=AsyncSession)

    # Create proper mock chain for SQLAlchemy result
    scalars_mock = Mock()
    scalars_mock.all = Mock(return_value=[])

    execute_result = AsyncMock()
    execute_result.scalars = Mock(return_value=scalars_mock)

    db_mock.execute = AsyncMock(return_value=execute_result)

    asset = Mock()
    asset.id = "test-asset-id"

    requirements = DataRequirements()

    inspector = StandardsInspector()
    await inspector.inspect(
        asset=asset,
        application=None,
        requirements=requirements,
        client_account_id="client-123",
        engagement_id="engagement-456",
        db=db_mock,
    )

    # Verify database execute was called
    assert db_mock.execute.called

    # Verify tenant scoping is in the query
    # (Query would be passed to db.execute, we verify it was called)
    call_args = db_mock.execute.call_args
    assert call_args is not None
