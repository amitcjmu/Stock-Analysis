"""
Unit tests for AssessmentApplicationResolver service.

Tests the core business logic for resolving assets to canonical applications
and calculating enrichment/readiness metadata.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.asset import Asset
from app.models.canonical_applications import (
    CanonicalApplication,
    CollectionFlowApplication,
)
from app.models.asset_resilience import (
    AssetComplianceFlags,
    AssetLicenses,
    AssetVulnerabilities,
    AssetResilience,
)
from app.models.asset_agnostic.asset_field_conflicts import AssetFieldConflict
from app.services.assessment.application_resolver import AssessmentApplicationResolver


# Test database URL (in-memory SQLite for unit tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create test database session."""
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
def client_account_id():
    """Test client account ID."""
    return uuid4()


@pytest.fixture
def engagement_id():
    """Test engagement ID."""
    return uuid4()


@pytest.fixture
def collection_flow_id():
    """Test collection flow ID."""
    return uuid4()


@pytest_asyncio.fixture
async def canonical_app(db_session, client_account_id, engagement_id):
    """Create a test canonical application."""
    app = CanonicalApplication(
        id=uuid4(),
        canonical_name="CRM System",
        normalized_name="crm system",
        name_hash="test_hash_crm",
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        application_type="Web Application",
        technology_stack=["Python", "PostgreSQL"],
        confidence_score=0.95,
    )
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)
    return app


@pytest_asyncio.fixture
async def assets_with_canonical(
    db_session, client_account_id, engagement_id, canonical_app, collection_flow_id
):
    """Create test assets linked to canonical application."""
    # Asset 1: Linked to canonical app
    asset1 = Asset(
        id=uuid4(),
        name="CRM Server 1",
        asset_name="CRM Server 1",
        asset_type="server",
        environment="production",
        assessment_readiness="ready",
        assessment_readiness_score=Decimal("0.85"),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )
    db_session.add(asset1)

    # Asset 2: Linked to same canonical app
    asset2 = Asset(
        id=uuid4(),
        name="CRM Database",
        asset_name="CRM Database",
        asset_type="database",
        environment="production",
        assessment_readiness="in_progress",
        assessment_readiness_score=Decimal("0.60"),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )
    db_session.add(asset2)

    await db_session.commit()
    await db_session.refresh(asset1)
    await db_session.refresh(asset2)

    # Create collection flow applications (junction records)
    cfa1 = CollectionFlowApplication(
        id=uuid4(),
        collection_flow_id=collection_flow_id,
        asset_id=asset1.id,
        application_name="CRM Server 1",
        canonical_application_id=canonical_app.id,
        deduplication_method="exact_match",
        match_confidence=0.95,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )
    db_session.add(cfa1)

    cfa2 = CollectionFlowApplication(
        id=uuid4(),
        collection_flow_id=collection_flow_id,
        asset_id=asset2.id,
        application_name="CRM Database",
        canonical_application_id=canonical_app.id,
        deduplication_method="fuzzy_match",
        match_confidence=0.88,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )
    db_session.add(cfa2)

    await db_session.commit()

    return [asset1, asset2]


@pytest_asyncio.fixture
async def unmapped_asset(db_session, client_account_id, engagement_id):
    """Create test asset not linked to any canonical application."""
    asset = Asset(
        id=uuid4(),
        name="Standalone Server",
        asset_name="Standalone Server",
        asset_type="server",
        environment="development",
        assessment_readiness="not_ready",
        assessment_readiness_score=Decimal("0.30"),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)
    return asset


@pytest.mark.asyncio
async def test_resolve_assets_to_applications_with_canonical(
    db_session, client_account_id, engagement_id, assets_with_canonical, canonical_app
):
    """Test resolving assets that are linked to canonical applications."""
    resolver = AssessmentApplicationResolver(
        db=db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    asset_ids = [asset.id for asset in assets_with_canonical]

    groups = await resolver.resolve_assets_to_applications(asset_ids)

    # Should have 1 group (both assets linked to same canonical app)
    assert len(groups) == 1

    group = groups[0]
    assert group.canonical_application_id == canonical_app.id
    assert group.canonical_application_name == "CRM System"
    assert group.asset_count == 2
    assert set(group.asset_types) == {"server", "database"}

    # Check readiness summary
    assert group.readiness_summary["ready"] == 1
    assert group.readiness_summary["in_progress"] == 1
    assert group.readiness_summary["not_ready"] == 0


@pytest.mark.asyncio
async def test_resolve_assets_unmapped(
    db_session, client_account_id, engagement_id, unmapped_asset
):
    """Test resolving assets without canonical application mapping."""
    resolver = AssessmentApplicationResolver(
        db=db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    groups = await resolver.resolve_assets_to_applications([unmapped_asset.id])

    # Should have 1 group for unmapped asset
    assert len(groups) == 1

    group = groups[0]
    assert group.canonical_application_id is None
    assert group.canonical_application_name == "Standalone Server"
    assert group.asset_count == 1
    assert group.asset_types == ["server"]

    # Check readiness
    assert group.readiness_summary["not_ready"] == 1
    assert group.readiness_summary["ready"] == 0


@pytest.mark.asyncio
async def test_resolve_assets_mixed(
    db_session,
    client_account_id,
    engagement_id,
    assets_with_canonical,
    unmapped_asset,
):
    """Test resolving mix of mapped and unmapped assets."""
    resolver = AssessmentApplicationResolver(
        db=db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    asset_ids = [asset.id for asset in assets_with_canonical] + [unmapped_asset.id]

    groups = await resolver.resolve_assets_to_applications(asset_ids)

    # Should have 2 groups (1 canonical app + 1 unmapped)
    assert len(groups) == 2

    # Find canonical group and unmapped group
    canonical_group = next((g for g in groups if g.canonical_application_id), None)
    unmapped_group = next((g for g in groups if not g.canonical_application_id), None)

    assert canonical_group is not None
    assert canonical_group.asset_count == 2

    assert unmapped_group is not None
    assert unmapped_group.asset_count == 1


@pytest.mark.asyncio
async def test_resolve_assets_empty_list(db_session, client_account_id, engagement_id):
    """Test resolving empty asset list."""
    resolver = AssessmentApplicationResolver(
        db=db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    groups = await resolver.resolve_assets_to_applications([])

    assert groups == []


@pytest.mark.asyncio
async def test_calculate_enrichment_status(
    db_session, client_account_id, engagement_id, assets_with_canonical
):
    """Test enrichment status calculation across all 7 tables."""
    resolver = AssessmentApplicationResolver(
        db=db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    asset_ids = [asset.id for asset in assets_with_canonical]
    asset1_id, asset2_id = asset_ids

    # Add enrichment data for asset 1
    # Compliance flags
    compliance = AssetComplianceFlags(
        id=uuid4(),
        asset_id=asset1_id,
        compliance_scopes=["GDPR", "SOX"],
        data_classification="confidential",
    )
    db_session.add(compliance)

    # Vulnerabilities
    vuln = AssetVulnerabilities(
        id=uuid4(),
        asset_id=asset1_id,
        cve_id="CVE-2023-1234",
        severity="high",
    )
    db_session.add(vuln)

    # License
    license = AssetLicenses(
        id=uuid4(),
        asset_id=asset2_id,
        license_type="Commercial",
    )
    db_session.add(license)

    # Resilience
    resilience = AssetResilience(
        id=uuid4(),
        asset_id=asset1_id,
        rto_minutes=60,
        rpo_minutes=15,
    )
    db_session.add(resilience)

    # Field conflict
    conflict = AssetFieldConflict(
        id=uuid4(),
        asset_id=asset2_id,
        field_name="operating_system",
        conflicting_values=[
            {"value": "Windows", "source": "import", "confidence": 0.8},
            {"value": "Linux", "source": "agent", "confidence": 0.9},
        ],
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )
    db_session.add(conflict)

    await db_session.commit()

    # Calculate enrichment status
    status = await resolver.calculate_enrichment_status(asset_ids)

    assert status.compliance_flags == 1
    assert status.vulnerabilities == 1
    assert status.licenses == 1
    assert status.resilience == 1
    assert status.field_conflicts == 1
    # Dependencies and product_links should be 0 (not created)
    assert status.dependencies == 0
    assert status.product_links == 0


@pytest.mark.asyncio
async def test_calculate_enrichment_status_empty(
    db_session, client_account_id, engagement_id
):
    """Test enrichment status with no assets."""
    resolver = AssessmentApplicationResolver(
        db=db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    status = await resolver.calculate_enrichment_status([])

    # All counts should be 0
    assert status.compliance_flags == 0
    assert status.licenses == 0
    assert status.vulnerabilities == 0
    assert status.resilience == 0
    assert status.dependencies == 0
    assert status.product_links == 0
    assert status.field_conflicts == 0


@pytest.mark.asyncio
async def test_calculate_readiness_summary(
    db_session, client_account_id, engagement_id, assets_with_canonical
):
    """Test readiness summary calculation."""
    resolver = AssessmentApplicationResolver(
        db=db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    asset_ids = [asset.id for asset in assets_with_canonical]

    summary = await resolver.calculate_readiness_summary(asset_ids)

    assert summary.total_assets == 2
    assert summary.ready == 1
    assert summary.in_progress == 1
    assert summary.not_ready == 0

    # Average score: (0.85 + 0.60) / 2 = 0.725, rounded to 0.72
    assert summary.avg_completeness_score == 0.72


@pytest.mark.asyncio
async def test_calculate_readiness_summary_all_not_ready(
    db_session, client_account_id, engagement_id, unmapped_asset
):
    """Test readiness summary with all assets not ready."""
    resolver = AssessmentApplicationResolver(
        db=db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    summary = await resolver.calculate_readiness_summary([unmapped_asset.id])

    assert summary.total_assets == 1
    assert summary.ready == 0
    assert summary.not_ready == 1
    assert summary.in_progress == 0
    assert summary.avg_completeness_score == 0.30


@pytest.mark.asyncio
async def test_calculate_readiness_summary_empty(
    db_session, client_account_id, engagement_id
):
    """Test readiness summary with no assets."""
    resolver = AssessmentApplicationResolver(
        db=db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    summary = await resolver.calculate_readiness_summary([])

    assert summary.total_assets == 0
    assert summary.ready == 0
    assert summary.not_ready == 0
    assert summary.in_progress == 0
    assert summary.avg_completeness_score == 0.0


@pytest.mark.asyncio
async def test_multi_tenant_isolation(db_session, client_account_id, engagement_id):
    """Test that resolver only sees assets from correct tenant."""
    # Create asset for correct tenant
    asset1 = Asset(
        id=uuid4(),
        name="Tenant 1 Asset",
        asset_name="Tenant 1 Asset",
        asset_type="server",
        assessment_readiness="ready",
        assessment_readiness_score=Decimal("0.90"),
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )
    db_session.add(asset1)

    # Create asset for different tenant
    other_client_id = uuid4()
    other_engagement_id = uuid4()
    asset2 = Asset(
        id=uuid4(),
        name="Tenant 2 Asset",
        asset_name="Tenant 2 Asset",
        asset_type="server",
        assessment_readiness="ready",
        assessment_readiness_score=Decimal("0.95"),
        client_account_id=other_client_id,
        engagement_id=other_engagement_id,
    )
    db_session.add(asset2)

    await db_session.commit()
    await db_session.refresh(asset1)
    await db_session.refresh(asset2)

    # Resolver should only see tenant 1 asset
    resolver = AssessmentApplicationResolver(
        db=db_session,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    # Try to resolve both assets
    groups = await resolver.resolve_assets_to_applications([asset1.id, asset2.id])

    # Should only get 1 group (tenant 1 asset)
    assert len(groups) == 1
    assert groups[0].asset_count == 1
    assert groups[0].canonical_application_name == "Tenant 1 Asset"

    # Readiness summary should also respect tenant isolation
    summary = await resolver.calculate_readiness_summary([asset1.id, asset2.id])
    assert summary.total_assets == 1  # Only tenant 1 asset
