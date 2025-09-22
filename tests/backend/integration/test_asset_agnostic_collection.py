"""
Integration tests for Asset-Agnostic Collection feature (Phase 2).

Tests the complete implementation including:
- AssetFieldConflict model
- Asset collection endpoints
- ConflictDetectionService
"""

import pytest
from typing import Dict, Any
from uuid import UUID, uuid4
import sys
import os

# Add the backend directory to the path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../backend"))

from httpx import AsyncClient
from sqlalchemy import select, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

# Import app modules
from app.models.asset_agnostic.asset_field_conflicts import AssetFieldConflict
from app.models.asset import Asset
from app.core.database import Base
from app.core.context import RequestContext
from app.services.collection_gaps.conflict_detection_service import ConflictDetectionService


# Test database URL - using SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine):
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_context() -> RequestContext:
    """Create a test request context with tenant scoping."""
    return RequestContext(
        client_account_id=uuid4(),
        engagement_id=uuid4(),
        user_id=uuid4(),
        correlation_id=str(uuid4())
    )


class TestAssetFieldConflictModel:
    """Test the AssetFieldConflict model."""

    @pytest.mark.asyncio
    async def test_create_conflict(self, test_db_session: AsyncSession, test_context: RequestContext):
        """Test creating an asset field conflict."""
        # Create a test asset first
        asset = Asset(
            id=uuid4(),
            name="Test Server",
            asset_type="server",
            client_account_id=test_context.client_account_id,
            engagement_id=test_context.engagement_id,
            custom_attributes={"cpu_cores": 8},
            technical_details={"memory_gb": 32}
        )
        test_db_session.add(asset)
        await test_db_session.flush()

        # Create a conflict
        conflict = AssetFieldConflict(
            asset_id=asset.id,
            client_account_id=test_context.client_account_id,
            engagement_id=test_context.engagement_id,
            field_name="cpu_cores",
            conflicting_values=[
                {"value": 8, "source": "custom_attributes", "confidence": 0.7},
                {"value": 16, "source": "import_file", "confidence": 0.9}
            ],
            resolution_status="pending"
        )
        test_db_session.add(conflict)
        await test_db_session.commit()

        # Verify the conflict was created
        result = await test_db_session.execute(
            select(AssetFieldConflict).where(
                AssetFieldConflict.asset_id == asset.id
            )
        )
        saved_conflict = result.scalar_one()

        assert saved_conflict.field_name == "cpu_cores"
        assert saved_conflict.resolution_status == "pending"
        assert len(saved_conflict.conflicting_values) == 2
        assert saved_conflict.client_account_id == test_context.client_account_id
        assert saved_conflict.engagement_id == test_context.engagement_id

    @pytest.mark.asyncio
    async def test_resolve_conflict(self, test_db_session: AsyncSession, test_context: RequestContext):
        """Test resolving a conflict."""
        # Create asset and conflict
        asset = Asset(
            id=uuid4(),
            name="Test Database",
            asset_type="database",
            client_account_id=test_context.client_account_id,
            engagement_id=test_context.engagement_id
        )
        test_db_session.add(asset)

        conflict = AssetFieldConflict(
            asset_id=asset.id,
            client_account_id=test_context.client_account_id,
            engagement_id=test_context.engagement_id,
            field_name="version",
            conflicting_values=[
                {"value": "12.0", "source": "scan"},
                {"value": "13.0", "source": "manual"}
            ],
            resolution_status="pending"
        )
        test_db_session.add(conflict)
        await test_db_session.flush()

        # Resolve the conflict
        conflict.resolution_status = "manual_resolved"
        conflict.resolved_value = "13.0"
        conflict.resolved_by = test_context.user_id
        conflict.resolution_rationale = "Manual entry is more recent"

        await test_db_session.commit()

        # Verify resolution
        result = await test_db_session.execute(
            select(AssetFieldConflict).where(
                AssetFieldConflict.asset_id == asset.id
            )
        )
        resolved = result.scalar_one()

        assert resolved.resolution_status == "manual_resolved"
        assert resolved.resolved_value == "13.0"
        assert resolved.resolved_by == test_context.user_id
        assert resolved.resolution_rationale == "Manual entry is more recent"


class TestConflictDetectionService:
    """Test the ConflictDetectionService."""

    @pytest.mark.asyncio
    async def test_detect_conflicts_from_multiple_sources(
        self, test_db_session: AsyncSession, test_context: RequestContext
    ):
        """Test detecting conflicts from multiple data sources."""
        # Create an asset with conflicting data in different fields
        asset = Asset(
            id=uuid4(),
            name="Test Application",
            asset_type="application",
            client_account_id=test_context.client_account_id,
            engagement_id=test_context.engagement_id,
            custom_attributes={
                "version": "2.0.0",
                "port": 8080
            },
            technical_details={
                "version": "2.1.0",  # Conflict!
                "port": 8080,  # Same value, no conflict
                "memory_limit": "4GB"
            }
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        # Initialize service and detect conflicts
        service = ConflictDetectionService(
            db=test_db_session,
            client_account_id=test_context.client_account_id,
            engagement_id=test_context.engagement_id
        )

        conflicts = await service.detect_conflicts(str(asset.id))

        # Should find 1 conflict for "version" field
        assert len(conflicts) == 1
        assert conflicts[0].field_name == "version"
        assert conflicts[0].resolution_status == "pending"

        # Check conflicting values
        values = conflicts[0].conflicting_values
        assert len(values) == 2
        versions = [v["value"] for v in values]
        assert "2.0.0" in versions
        assert "2.1.0" in versions

    @pytest.mark.asyncio
    async def test_auto_resolution_high_confidence(
        self, test_db_session: AsyncSession, test_context: RequestContext
    ):
        """Test auto-resolution when one source has high confidence."""
        asset = Asset(
            id=uuid4(),
            name="Test Device",
            asset_type="device",
            client_account_id=test_context.client_account_id,
            engagement_id=test_context.engagement_id,
            custom_attributes={"ip_address": "10.0.0.1"}
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        # Create a conflict with different confidence levels
        conflict = AssetFieldConflict(
            asset_id=asset.id,
            client_account_id=test_context.client_account_id,
            engagement_id=test_context.engagement_id,
            field_name="ip_address",
            conflicting_values=[
                {"value": "10.0.0.1", "source": "scan", "confidence": 0.6},
                {"value": "10.0.0.2", "source": "verified_import", "confidence": 0.95}
            ],
            resolution_status="pending"
        )
        test_db_session.add(conflict)
        await test_db_session.commit()

        service = ConflictDetectionService(
            db=test_db_session,
            client_account_id=test_context.client_account_id,
            engagement_id=test_context.engagement_id
        )

        # Attempt auto-resolution
        resolved = await service.auto_resolve_conflict(conflict)

        assert resolved is True
        assert conflict.resolution_status == "auto_resolved"
        assert conflict.resolved_value == "10.0.0.2"  # High confidence value
        assert "high confidence" in conflict.resolution_rationale.lower()


class TestAssetCollectionEndpoints:
    """Test the asset collection API endpoints."""

    @pytest.mark.asyncio
    async def test_start_collection_endpoint(self):
        """Test starting asset-agnostic collection."""
        # This would need a TestClient setup with the FastAPI app
        # For now, we'll validate the endpoint structure exists
        from app.api.v1.endpoints.collection_gaps import assets

        # Verify the router exists and has the expected endpoints
        assert hasattr(assets, 'router')

        # Check that the start endpoint is defined
        routes = [route.path for route in assets.router.routes]
        assert "/start" in routes

    @pytest.mark.asyncio
    async def test_get_conflicts_endpoint(self):
        """Test getting conflicts for an asset."""
        from app.api.v1.endpoints.collection_gaps import assets

        routes = [route.path for route in assets.router.routes]
        assert "/{asset_id}/conflicts" in routes

    @pytest.mark.asyncio
    async def test_resolve_conflict_endpoint(self):
        """Test resolving a conflict."""
        from app.api.v1.endpoints.collection_gaps import assets

        routes = [route.path for route in assets.router.routes]
        assert "/{asset_id}/conflicts/{field_name}/resolve" in routes


# Run with: python -m pytest tests/backend/integration/test_asset_agnostic_collection.py -v
