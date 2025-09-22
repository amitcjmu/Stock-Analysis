"""
Unit tests for ConflictDetectionService.

Tests the core conflict detection logic for asset-agnostic collection,
including field aggregation, conflict detection, and resolution handling.

Generated with CC for Asset-Agnostic Collection Phase 2.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.collection_gaps.conflict_detection_service import ConflictDetectionService
from app.models.asset import Asset
from app.models.asset_agnostic.asset_field_conflicts import AssetFieldConflict
from app.models.data_import.core import RawImportRecord
from app.core.context import RequestContext


class TestConflictDetectionService:
    """Test ConflictDetectionService functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def sample_context(self):
        """Create sample request context."""
        return RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
        )

    @pytest.fixture
    def service(self, mock_db_session, sample_context):
        """Create ConflictDetectionService instance."""
        return ConflictDetectionService(mock_db_session, sample_context)

    @pytest.fixture
    def sample_asset(self, sample_context):
        """Create sample asset with conflicting data."""
        return Asset(
            id=uuid.uuid4(),
            hostname="test-server-01",
            asset_type="server",
            environment="production",
            client_account_id=uuid.UUID(sample_context.client_account_id),
            engagement_id=uuid.UUID(sample_context.engagement_id),
            custom_attributes={
                "os_version": "Ubuntu 20.04",
                "memory_gb": "16",
                "cpu_cores": "4",
                "empty_field": "",
                "null_field": None,
            },
            technical_details={
                "os_version": "Ubuntu 22.04",
                "memory_gb": "32",  # Conflict with custom_attributes
                "storage_gb": "1000",
                "empty_field": "",
                "null_field": None,
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    @pytest.fixture
    def sample_import_records(self, sample_context):
        """Create sample import records."""
        return [
            RawImportRecord(
                id=uuid.uuid4(),
                asset_id=None,  # Will be set in tests
                client_account_id=uuid.UUID(sample_context.client_account_id),
                engagement_id=uuid.UUID(sample_context.engagement_id),
                source_file="inventory_scan.csv",
                data={
                    "os_version": "Ubuntu 20.04.6",  # Slight difference
                    "memory_gb": "16",  # Matches custom_attributes
                    "network_interfaces": "eth0,eth1",
                    "empty_field": "",
                    "null_field": None,
                },
                created_at=datetime.utcnow(),
            ),
            RawImportRecord(
                id=uuid.uuid4(),
                asset_id=None,  # Will be set in tests
                client_account_id=uuid.UUID(sample_context.client_account_id),
                engagement_id=uuid.UUID(sample_context.engagement_id),
                source_file="cmdb_export.json",
                data={
                    "os_version": "Ubuntu 22.04.1",  # Another variation
                    "cpu_cores": "8",  # Conflict with custom_attributes
                    "environment": "prod",
                },
                created_at=datetime.utcnow(),
            ),
        ]

    @pytest.mark.asyncio
    async def test_detect_conflicts_success(
        self, service, mock_db_session, sample_asset, sample_import_records
    ):
        """Test successful conflict detection."""
        asset_id = sample_asset.id

        # Set asset_id for import records
        for record in sample_import_records:
            record.asset_id = asset_id

        # Mock database responses
        mock_asset_result = MagicMock()
        mock_asset_result.scalar_one_or_none.return_value = sample_asset

        mock_import_result = MagicMock()
        mock_import_result.scalars.return_value.all.return_value = sample_import_records

        mock_existing_conflict_result = MagicMock()
        mock_existing_conflict_result.scalar_one_or_none.return_value = None  # No existing conflicts

        mock_db_session.execute.side_effect = [
            mock_asset_result,  # Asset lookup
            mock_import_result,  # Import records lookup
            mock_existing_conflict_result,  # First conflict check
            mock_existing_conflict_result,  # Second conflict check
            mock_existing_conflict_result,  # Third conflict check
        ]

        # Execute
        conflicts = await service.detect_conflicts(asset_id)

        # Verify
        assert len(conflicts) > 0

        # Should detect conflicts for os_version and memory_gb at minimum
        conflict_fields = [conflict.field_name for conflict in conflicts]
        assert "os_version" in conflict_fields
        assert "memory_gb" in conflict_fields

        # Verify database operations
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
        assert mock_db_session.refresh.called

    @pytest.mark.asyncio
    async def test_detect_conflicts_asset_not_found(
        self, service, mock_db_session
    ):
        """Test conflict detection when asset is not found."""
        asset_id = uuid.uuid4()

        # Mock asset not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute
        conflicts = await service.detect_conflicts(asset_id)

        # Verify
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_detect_conflicts_no_conflicting_data(
        self, service, mock_db_session, sample_context
    ):
        """Test conflict detection when there are no conflicts."""
        asset_id = uuid.uuid4()

        # Create asset with no conflicting data
        asset = Asset(
            id=asset_id,
            hostname="no-conflicts-server",
            asset_type="server",
            environment="production",
            client_account_id=uuid.UUID(sample_context.client_account_id),
            engagement_id=uuid.UUID(sample_context.engagement_id),
            custom_attributes={
                "os_version": "Ubuntu 20.04",
                "memory_gb": "16",
            },
            technical_details={
                "storage_gb": "1000",  # Different field, no conflict
                "network_interfaces": "eth0",
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Mock database responses
        mock_asset_result = MagicMock()
        mock_asset_result.scalar_one_or_none.return_value = asset

        mock_import_result = MagicMock()
        mock_import_result.scalars.return_value.all.return_value = []  # No import records

        mock_db_session.execute.side_effect = [
            mock_asset_result,  # Asset lookup
            mock_import_result,  # Import records lookup
        ]

        # Execute
        conflicts = await service.detect_conflicts(asset_id)

        # Verify
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_detect_conflicts_for_scope_tenant(
        self, service, mock_db_session, sample_context
    ):
        """Test conflict detection for tenant scope."""
        # Create multiple assets
        assets = [
            Asset(
                id=uuid.uuid4(),
                hostname=f"server-{i}",
                asset_type="server",
                environment="production",
                client_account_id=uuid.UUID(sample_context.client_account_id),
                engagement_id=uuid.UUID(sample_context.engagement_id),
            )
            for i in range(3)
        ]

        # Mock database responses
        mock_assets_result = MagicMock()
        mock_assets_result.scalars.return_value.all.return_value = assets
        mock_db_session.execute.return_value = mock_assets_result

        # Mock detect_conflicts to return different numbers of conflicts
        with patch.object(service, 'detect_conflicts') as mock_detect:
            mock_detect.side_effect = [
                [MagicMock(field_name="field1")],  # 1 conflict for asset 1
                [],  # 0 conflicts for asset 2
                [MagicMock(field_name="field2"), MagicMock(field_name="field3")],  # 2 conflicts for asset 3
            ]

            # Execute
            all_conflicts = await service.detect_conflicts_for_scope(
                scope="tenant",
                scope_id=sample_context.client_account_id,
            )

            # Verify
            assert len(all_conflicts) == 2  # Only assets with conflicts
            assert mock_detect.call_count == 3  # Called for each asset

    @pytest.mark.asyncio
    async def test_detect_conflicts_for_scope_engagement(
        self, service, mock_db_session, sample_context
    ):
        """Test conflict detection for engagement scope."""
        assets = [Asset(id=uuid.uuid4(), hostname="test-server")]

        mock_assets_result = MagicMock()
        mock_assets_result.scalars.return_value.all.return_value = assets
        mock_db_session.execute.return_value = mock_assets_result

        with patch.object(service, 'detect_conflicts') as mock_detect:
            mock_detect.return_value = []

            # Execute
            all_conflicts = await service.detect_conflicts_for_scope(
                scope="engagement",
                scope_id=sample_context.engagement_id,
            )

            # Verify scope filter
            assert len(all_conflicts) == 0

    @pytest.mark.asyncio
    async def test_detect_conflicts_for_scope_asset(
        self, service, mock_db_session, sample_context
    ):
        """Test conflict detection for specific asset scope."""
        asset_id = str(uuid.uuid4())
        assets = [Asset(id=uuid.UUID(asset_id), hostname="specific-server")]

        mock_assets_result = MagicMock()
        mock_assets_result.scalars.return_value.all.return_value = assets
        mock_db_session.execute.return_value = mock_assets_result

        with patch.object(service, 'detect_conflicts') as mock_detect:
            mock_detect.return_value = [MagicMock(field_name="test_field")]

            # Execute
            all_conflicts = await service.detect_conflicts_for_scope(
                scope="asset",
                scope_id=asset_id,
            )

            # Verify
            assert len(all_conflicts) == 1
            assert asset_id in all_conflicts

    @pytest.mark.asyncio
    async def test_detect_conflicts_for_scope_with_asset_type_filter(
        self, service, mock_db_session, sample_context
    ):
        """Test conflict detection with asset type filter."""
        assets = [Asset(id=uuid.uuid4(), hostname="server", asset_type="server")]

        mock_assets_result = MagicMock()
        mock_assets_result.scalars.return_value.all.return_value = assets
        mock_db_session.execute.return_value = mock_assets_result

        with patch.object(service, 'detect_conflicts') as mock_detect:
            mock_detect.return_value = []

            # Execute
            await service.detect_conflicts_for_scope(
                scope="tenant",
                scope_id=sample_context.client_account_id,
                asset_type="server",
            )

            # Verify that asset_type filter was applied in query
            mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_conflicts_for_scope_invalid_scope(
        self, service, mock_db_session, sample_context
    ):
        """Test conflict detection with invalid scope."""
        with pytest.raises(ValueError, match="Invalid scope"):
            await service.detect_conflicts_for_scope(
                scope="invalid_scope",
                scope_id="some-id",
            )

    @pytest.mark.asyncio
    async def test_aggregate_field_data(self, service, sample_asset, sample_import_records):
        """Test field data aggregation from multiple sources."""
        # Set asset_id for import records
        for record in sample_import_records:
            record.asset_id = sample_asset.id

        # Mock import records query
        mock_import_result = MagicMock()
        mock_import_result.scalars.return_value.all.return_value = sample_import_records
        service.db.execute.return_value = mock_import_result

        # Execute
        field_sources = await service._aggregate_field_data(sample_asset)

        # Verify
        assert "os_version" in field_sources
        assert "memory_gb" in field_sources
        assert "cpu_cores" in field_sources

        # Check os_version sources (should have 4 sources)
        os_sources = field_sources["os_version"]
        assert len(os_sources) == 4  # custom_attributes + technical_details + 2 imports

        # Verify source types
        source_names = [source["source"] for source in os_sources]
        assert "custom_attributes" in source_names
        assert "technical_details" in source_names
        assert "import:inventory_scan.csv" in source_names
        assert "import:cmdb_export.json" in source_names

        # Verify confidence scores
        for source in os_sources:
            assert 0.0 <= source["confidence"] <= 1.0

        # Verify timestamps are present
        for source in os_sources:
            assert "timestamp" in source

    def test_has_conflict_true(self, service):
        """Test conflict detection when conflicts exist."""
        sources = [
            {"value": "Ubuntu 20.04", "source": "source1"},
            {"value": "Ubuntu 22.04", "source": "source2"},
        ]

        assert service._has_conflict(sources) is True

    def test_has_conflict_false_same_values(self, service):
        """Test conflict detection when values are the same."""
        sources = [
            {"value": "Ubuntu 20.04", "source": "source1"},
            {"value": "Ubuntu 20.04", "source": "source2"},
        ]

        assert service._has_conflict(sources) is False

    def test_has_conflict_false_case_insensitive(self, service):
        """Test conflict detection is case-insensitive."""
        sources = [
            {"value": "Ubuntu 20.04", "source": "source1"},
            {"value": "ubuntu 20.04", "source": "source2"},
        ]

        assert service._has_conflict(sources) is False

    def test_has_conflict_false_single_source(self, service):
        """Test conflict detection with single source."""
        sources = [
            {"value": "Ubuntu 20.04", "source": "source1"},
        ]

        assert service._has_conflict(sources) is False

    def test_has_conflict_false_empty_sources(self, service):
        """Test conflict detection with empty sources."""
        assert service._has_conflict([]) is False

    def test_has_conflict_ignores_empty_values(self, service):
        """Test conflict detection ignores empty values."""
        sources = [
            {"value": "Ubuntu 20.04", "source": "source1"},
            {"value": "", "source": "source2"},
            {"value": "  ", "source": "source3"},
        ]

        assert service._has_conflict(sources) is False

    @pytest.mark.asyncio
    async def test_create_or_update_conflict_new(
        self, service, mock_db_session, sample_context
    ):
        """Test creating a new conflict."""
        asset_id = uuid.uuid4()
        field_name = "test_field"
        sources = [
            {"value": "value1", "source": "source1", "timestamp": datetime.utcnow(), "confidence": 0.8},
            {"value": "value2", "source": "source2", "timestamp": datetime.utcnow(), "confidence": 0.9},
        ]

        # Mock no existing conflict
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_existing_result

        # Execute
        conflict = await service._create_or_update_conflict(asset_id, field_name, sources)

        # Verify
        assert conflict is not None
        assert conflict.asset_id == asset_id
        assert conflict.field_name == field_name
        assert conflict.client_account_id == uuid.UUID(sample_context.client_account_id)
        assert conflict.engagement_id == uuid.UUID(sample_context.engagement_id)
        assert conflict.resolution_status == "pending"
        assert len(conflict.conflicting_values) == 2

        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_or_update_conflict_update_existing(
        self, service, mock_db_session, sample_context
    ):
        """Test updating an existing unresolved conflict."""
        asset_id = uuid.uuid4()
        field_name = "test_field"
        sources = [
            {"value": "new_value1", "source": "source1", "timestamp": datetime.utcnow(), "confidence": 0.8},
        ]

        # Mock existing unresolved conflict
        existing_conflict = AssetFieldConflict(
            id=uuid.uuid4(),
            asset_id=asset_id,
            client_account_id=uuid.UUID(sample_context.client_account_id),
            engagement_id=uuid.UUID(sample_context.engagement_id),
            field_name=field_name,
            conflicting_values=[],
            resolution_status="pending",
        )

        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = existing_conflict
        mock_db_session.execute.return_value = mock_existing_result

        # Execute
        conflict = await service._create_or_update_conflict(asset_id, field_name, sources)

        # Verify
        assert conflict is existing_conflict
        assert len(conflict.conflicting_values) == 1
        assert conflict.updated_at is not None

        # Verify database operations
        mock_db_session.add.assert_not_called()  # Not creating new
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_or_update_conflict_skip_resolved(
        self, service, mock_db_session, sample_context
    ):
        """Test skipping update of already resolved conflict."""
        asset_id = uuid.uuid4()
        field_name = "test_field"
        sources = [
            {"value": "value1", "source": "source1", "timestamp": datetime.utcnow(), "confidence": 0.8},
        ]

        # Mock existing resolved conflict
        existing_conflict = AssetFieldConflict(
            id=uuid.uuid4(),
            asset_id=asset_id,
            client_account_id=uuid.UUID(sample_context.client_account_id),
            engagement_id=uuid.UUID(sample_context.engagement_id),
            field_name=field_name,
            conflicting_values=[],
            resolution_status="manual_resolved",
        )

        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = existing_conflict
        mock_db_session.execute.return_value = mock_existing_result

        # Execute
        conflict = await service._create_or_update_conflict(asset_id, field_name, sources)

        # Verify
        assert conflict is None  # Should return None for resolved conflicts

        # Verify no database changes
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_conflicts_for_asset(self, service, mock_db_session):
        """Test getting all conflicts for a specific asset."""
        asset_id = uuid.uuid4()
        conflicts = [
            MagicMock(field_name="field1"),
            MagicMock(field_name="field2"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = conflicts
        mock_db_session.execute.return_value = mock_result

        # Execute
        result = await service.get_conflicts_for_asset(asset_id)

        # Verify
        assert result == conflicts

    @pytest.mark.asyncio
    async def test_resolve_conflict_success(self, service, mock_db_session, sample_context):
        """Test successfully resolving a conflict."""
        conflict_id = uuid.uuid4()
        resolved_value = "Resolved value"
        rationale = "Test rationale"

        # Mock existing unresolved conflict
        existing_conflict = MagicMock()
        existing_conflict.is_resolved = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_conflict
        mock_db_session.execute.return_value = mock_result

        # Execute
        result = await service.resolve_conflict(
            conflict_id=conflict_id,
            resolved_value=resolved_value,
            rationale=rationale,
            auto_resolved=False,
        )

        # Verify
        assert result == existing_conflict
        existing_conflict.resolve_conflict.assert_called_once_with(
            resolved_value=resolved_value,
            resolved_by=uuid.UUID(sample_context.user_id),
            rationale=rationale,
            auto_resolved=False,
        )
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolve_conflict_not_found(self, service, mock_db_session):
        """Test resolving a non-existent conflict."""
        conflict_id = uuid.uuid4()

        # Mock conflict not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute and verify exception
        with pytest.raises(ValueError, match="not found or not accessible"):
            await service.resolve_conflict(
                conflict_id=conflict_id,
                resolved_value="value",
            )

    @pytest.mark.asyncio
    async def test_resolve_conflict_already_resolved(self, service, mock_db_session):
        """Test resolving an already resolved conflict."""
        conflict_id = uuid.uuid4()

        # Mock existing resolved conflict
        existing_conflict = MagicMock()
        existing_conflict.is_resolved = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_conflict
        mock_db_session.execute.return_value = mock_result

        # Execute and verify exception
        with pytest.raises(ValueError, match="already resolved"):
            await service.resolve_conflict(
                conflict_id=conflict_id,
                resolved_value="value",
            )

    def test_empty_values_handling(self, service, sample_context):
        """Test that empty and null values are properly filtered."""
        asset = Asset(
            id=uuid.uuid4(),
            hostname="test-server",
            asset_type="server",
            client_account_id=uuid.UUID(sample_context.client_account_id),
            engagement_id=uuid.UUID(sample_context.engagement_id),
            custom_attributes={
                "valid_field": "valid_value",
                "empty_string": "",
                "null_value": None,
                "whitespace": "   ",
            },
            technical_details={
                "valid_field": "different_value",  # This should create a conflict
                "empty_string": "",
                "null_value": None,
                "whitespace": "   ",
            },
        )

        # Mock import records query
        mock_import_result = MagicMock()
        mock_import_result.scalars.return_value.all.return_value = []
        service.db.execute.return_value = mock_import_result

        # Execute field aggregation
        import asyncio
        field_sources = asyncio.run(service._aggregate_field_data(asset))

        # Verify that only valid_field has sources (empty/null values filtered out)
        assert "valid_field" in field_sources
        assert "empty_string" not in field_sources
        assert "null_value" not in field_sources
        assert "whitespace" not in field_sources

        # Verify valid_field has conflict
        assert len(field_sources["valid_field"]) == 2
        assert service._has_conflict(field_sources["valid_field"]) is True
