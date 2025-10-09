"""
Tests for AssetService unified deduplication architecture.

Tests the hierarchical deduplication logic, status returns, and merge strategies
implemented per Qodo PR #531 and GPT-5 architectural guidance.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.asset_service import AssetService
from app.models.asset import Asset, AssetType, AssetStatus
from app.core.context import RequestContext


@pytest.fixture
def mock_db_session():
    """Mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def request_context():
    """Create test request context."""
    return RequestContext(
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        flow_id="33333333-3333-3333-3333-333333333333",
        user_id="44444444-4444-4444-4444-444444444444",
    )


@pytest.fixture
def asset_service(mock_db_session, request_context):
    """Create AssetService instance with mocked dependencies."""
    return AssetService(mock_db_session, request_context)


@pytest.mark.asyncio
class TestCreateOrUpdateAsset:
    """Test unified create_or_update_asset method."""

    async def test_create_new_asset_returns_created_status(
        self, asset_service, mock_db_session
    ):
        """Test creating a new asset returns 'created' status."""
        # Setup: No existing assets
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        asset_data = {
            "name": "TestServer01",
            "asset_type": "server",
            "hostname": "testserver01.local",
        }

        # Execute
        asset, status = await asset_service.create_or_update_asset(asset_data)

        # Assert
        assert status == "created"
        assert asset is not None
        assert asset.name == "TestServer01"
        mock_db_session.flush.assert_called_once()

    async def test_duplicate_asset_returns_existed_status(
        self, asset_service, mock_db_session
    ):
        """Test finding duplicate asset returns 'existed' status."""
        # Setup: Existing asset found
        existing_asset = Asset(
            id=uuid.uuid4(),
            client_account_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            engagement_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            name="TestServer01",
            asset_type=AssetType.SERVER,
            hostname="testserver01.local",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_asset
        mock_db_session.execute.return_value = mock_result

        asset_data = {
            "name": "TestServer01",
            "asset_type": "server",
            "hostname": "testserver01.local",
        }

        # Execute
        asset, status = await asset_service.create_or_update_asset(asset_data)

        # Assert
        assert status == "existed"
        assert asset == existing_asset
        mock_db_session.flush.assert_not_called()  # No new asset created

    async def test_upsert_with_enrich_returns_updated_status(
        self, asset_service, mock_db_session
    ):
        """Test upsert with enrich strategy returns 'updated' status."""
        # Setup: Existing asset found
        existing_asset = Asset(
            id=uuid.uuid4(),
            client_account_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            engagement_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            name="TestServer01",
            asset_type=AssetType.SERVER,
            hostname="testserver01.local",
            description="Original description",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_asset
        mock_db_session.execute.return_value = mock_result

        asset_data = {
            "name": "TestServer01",
            "asset_type": "server",
            "hostname": "testserver01.local",
            "description": "Updated description",
            "operating_system": "Ubuntu 22.04",  # New field
        }

        # Execute with upsert=True
        asset, status = await asset_service.create_or_update_asset(
            asset_data, upsert=True, merge_strategy="enrich"
        )

        # Assert
        assert status == "updated"
        assert asset.operating_system == "Ubuntu 22.04"  # New field added
        # Description kept original (enrich doesn't overwrite)
        mock_db_session.flush.assert_called()


@pytest.mark.asyncio
class TestHierarchicalDeduplication:
    """Test 4-level hierarchical deduplication logic."""

    async def test_priority1_name_and_type_match(
        self, asset_service, mock_db_session
    ):
        """Test Priority 1: name + asset_type deduplication."""
        # Setup: Existing asset with same name and type
        existing_asset = Asset(
            id=uuid.uuid4(),
            client_account_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            engagement_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            name="WebServer01",
            asset_type=AssetType.SERVER,
            hostname="different-hostname.local",  # Different hostname
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_asset
        mock_db_session.execute.return_value = mock_result

        asset_data = {
            "name": "WebServer01",
            "asset_type": "server",
            "hostname": "webserver01.local",  # Different hostname
        }

        # Execute
        asset, status = await asset_service.create_or_update_asset(asset_data)

        # Assert: Found by name+type even with different hostname
        assert status == "existed"
        assert asset == existing_asset

    async def test_priority2_hostname_match(self, asset_service, mock_db_session):
        """Test Priority 2: hostname deduplication."""
        # Setup: Existing asset with same hostname but different name
        existing_asset = Asset(
            id=uuid.uuid4(),
            client_account_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            engagement_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            name="OldServerName",
            asset_type=AssetType.SERVER,
            hostname="server.prod.local",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_asset
        mock_db_session.execute.return_value = mock_result

        asset_data = {
            "name": "NewServerName",  # Different name
            "asset_type": "server",
            "hostname": "server.prod.local",  # Same hostname
        }

        # Execute
        asset, status = await asset_service.create_or_update_asset(asset_data)

        # Assert: Found by hostname
        assert status == "existed"
        assert asset == existing_asset

    async def test_priority2_ip_address_match(self, asset_service, mock_db_session):
        """Test Priority 2: IP address deduplication."""
        # Setup: Existing asset with same IP but different name/hostname
        existing_asset = Asset(
            id=uuid.uuid4(),
            client_account_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            engagement_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            name="Server01",
            asset_type=AssetType.SERVER,
            ip_address="192.168.1.100",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_asset
        mock_db_session.execute.return_value = mock_result

        asset_data = {
            "name": "DifferentServer",
            "asset_type": "server",
            "ip_address": "192.168.1.100",  # Same IP
        }

        # Execute
        asset, status = await asset_service.create_or_update_asset(asset_data)

        # Assert: Found by IP address
        assert status == "existed"
        assert asset == existing_asset


@pytest.mark.asyncio
class TestMergeStrategies:
    """Test enrich vs overwrite merge strategies."""

    async def test_enrich_strategy_preserves_existing_values(
        self, asset_service, mock_db_session
    ):
        """Test enrich strategy keeps existing values, adds new ones."""
        # Setup: Existing asset with some fields populated
        existing_asset = Asset(
            id=uuid.uuid4(),
            client_account_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            engagement_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            name="Server01",
            asset_type=AssetType.SERVER,
            description="Original description",
            operating_system="Ubuntu 20.04",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_asset
        mock_db_session.execute.return_value = mock_result

        asset_data = {
            "name": "Server01",
            "asset_type": "server",
            "description": "New description",  # Should NOT overwrite
            "cpu_cores": 8,  # New field - should add
        }

        # Execute with enrich strategy
        asset, status = await asset_service.create_or_update_asset(
            asset_data, upsert=True, merge_strategy="enrich"
        )

        # Assert
        assert status == "updated"
        assert asset.description == "Original description"  # Preserved
        assert asset.operating_system == "Ubuntu 20.04"  # Preserved
        assert asset.cpu_cores == 8  # New field added

    async def test_overwrite_strategy_replaces_values(
        self, asset_service, mock_db_session
    ):
        """Test overwrite strategy replaces existing values."""
        # Setup: Existing asset
        existing_asset = Asset(
            id=uuid.uuid4(),
            client_account_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            engagement_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            name="Server01",
            asset_type=AssetType.SERVER,
            description="Original description",
            operating_system="Ubuntu 20.04",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_asset
        mock_db_session.execute.return_value = mock_result

        asset_data = {
            "name": "Server01",
            "asset_type": "server",
            "description": "New description",  # Should overwrite
            "operating_system": "Ubuntu 22.04",  # Should overwrite
        }

        # Execute with overwrite strategy
        asset, status = await asset_service.create_or_update_asset(
            asset_data, upsert=True, merge_strategy="overwrite"
        )

        # Assert
        assert status == "updated"
        assert asset.description == "New description"  # Overwritten
        assert asset.operating_system == "Ubuntu 22.04"  # Overwritten


@pytest.mark.asyncio
class TestBulkCreateOrUpdateAssets:
    """Test batch-optimized bulk_create_or_update_assets."""

    async def test_bulk_prefetch_eliminates_n_plus_1(
        self, asset_service, mock_db_session
    ):
        """Test bulk method uses single prefetch query."""
        # Setup: Multiple assets
        assets_data = [
            {"name": f"Server{i:02d}", "asset_type": "server", "hostname": f"server{i:02d}.local"}
            for i in range(1, 101)  # 100 assets
        ]

        # Mock: Single prefetch returns no duplicates
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        # Execute
        results = await asset_service.bulk_create_or_update_assets(assets_data)

        # Assert: Only 1 database query (prefetch), not 100+
        assert mock_db_session.execute.call_count == 1
        assert len(results) == 100
        assert all(status == "created" for _, status in results)

    async def test_bulk_handles_mixed_new_and_duplicate(
        self, asset_service, mock_db_session
    ):
        """Test bulk processing correctly categorizes new vs duplicate assets."""
        # Setup: 5 assets, 2 are duplicates
        existing_assets = [
            Asset(
                id=uuid.uuid4(),
                client_account_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                engagement_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
                name="Server01",
                asset_type=AssetType.SERVER,
            ),
            Asset(
                id=uuid.uuid4(),
                client_account_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                engagement_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
                name="Server03",
                asset_type=AssetType.SERVER,
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = existing_assets
        mock_db_session.execute.return_value = mock_result

        assets_data = [
            {"name": "Server01", "asset_type": "server"},  # Duplicate
            {"name": "Server02", "asset_type": "server"},  # New
            {"name": "Server03", "asset_type": "server"},  # Duplicate
            {"name": "Server04", "asset_type": "server"},  # New
            {"name": "Server05", "asset_type": "server"},  # New
        ]

        # Execute
        results = await asset_service.bulk_create_or_update_assets(assets_data)

        # Assert
        assert len(results) == 5
        statuses = [status for _, status in results]
        assert statuses.count("existed") == 2  # 2 duplicates
        assert statuses.count("created") == 3  # 3 new

        # Only 1 prefetch query + 1 flush for new assets
        assert mock_db_session.execute.call_count == 1
        mock_db_session.flush.assert_called_once()


@pytest.mark.asyncio
class TestMultiTenantIsolation:
    """Test multi-tenant scoping in deduplication."""

    async def test_different_tenants_can_have_same_asset_name(
        self, mock_db_session
    ):
        """Test assets with same name in different tenants are separate."""
        # Tenant 1
        context1 = RequestContext(
            client_account_id="11111111-1111-1111-1111-111111111111",
            engagement_id="22222222-2222-2222-2222-222222222222",
        )
        service1 = AssetService(mock_db_session, context1)

        # Tenant 2
        context2 = RequestContext(
            client_account_id="AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA",
            engagement_id="BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB",
        )
        service2 = AssetService(mock_db_session, context2)

        # Setup: No existing assets
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        asset_data = {"name": "SharedServerName", "asset_type": "server"}

        # Execute: Create same asset name in both tenants
        asset1, status1 = await service1.create_or_update_asset(asset_data)
        asset2, status2 = await service2.create_or_update_asset(asset_data)

        # Assert: Both are created (not duplicates)
        assert status1 == "created"
        assert status2 == "created"
        assert asset1.client_account_id != asset2.client_account_id
