"""
Unit tests for bulk asset mapping endpoint.

Tests multi-tenant validation, idempotency, atomic transactions, and error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.canonical_applications.bulk_mapping import (
    AssetMapping,
    BulkMappingRequest,
    bulk_map_assets,
)
from app.core.context import RequestContext


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = MagicMock(spec=AsyncSession)
    session.begin = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_context():
    """Create mock request context with tenant information."""
    return RequestContext(
        client_account_id=str(uuid4()), engagement_id=str(uuid4()), user_id=str(uuid4())
    )


@pytest.fixture
def sample_asset_ids():
    """Generate sample asset IDs."""
    return [str(uuid4()) for _ in range(5)]


@pytest.fixture
def sample_canonical_app_id():
    """Generate sample canonical application ID."""
    return str(uuid4())


class TestBulkMappingRequest:
    """Test Pydantic request model validation."""

    def test_valid_request(self, sample_asset_ids, sample_canonical_app_id):
        """Test valid bulk mapping request."""
        mappings = [
            AssetMapping(asset_id=aid, canonical_application_id=sample_canonical_app_id)
            for aid in sample_asset_ids
        ]
        request = BulkMappingRequest(mappings=mappings)

        assert len(request.mappings) == 5
        assert request.collection_flow_id is None

    def test_request_with_collection_flow_id(
        self, sample_asset_ids, sample_canonical_app_id
    ):
        """Test request with optional collection flow ID."""
        collection_flow_id = str(uuid4())
        mappings = [
            AssetMapping(asset_id=aid, canonical_application_id=sample_canonical_app_id)
            for aid in sample_asset_ids[:3]
        ]
        request = BulkMappingRequest(
            mappings=mappings, collection_flow_id=collection_flow_id
        )

        assert len(request.mappings) == 3
        assert request.collection_flow_id == collection_flow_id

    def test_reject_duplicate_asset_ids(self, sample_canonical_app_id):
        """Test rejection of duplicate asset IDs in request."""
        duplicate_id = str(uuid4())
        mappings = [
            AssetMapping(
                asset_id=duplicate_id, canonical_application_id=sample_canonical_app_id
            ),
            AssetMapping(
                asset_id=duplicate_id,  # Duplicate
                canonical_application_id=sample_canonical_app_id,
            ),
        ]

        with pytest.raises(ValueError, match="Duplicate asset_id entries"):
            BulkMappingRequest(mappings=mappings)

    def test_reject_empty_mappings(self):
        """Test rejection of empty mappings list."""
        with pytest.raises(ValueError):
            BulkMappingRequest(mappings=[])

    def test_reject_too_many_mappings(self, sample_canonical_app_id):
        """Test rejection of >100 mappings per request."""
        mappings = [
            AssetMapping(
                asset_id=str(uuid4()), canonical_application_id=sample_canonical_app_id
            )
            for _ in range(101)
        ]

        with pytest.raises(ValueError):
            BulkMappingRequest(mappings=mappings)

    def test_reject_invalid_uuid_format(self):
        """Test rejection of invalid UUID formats."""
        with pytest.raises(ValueError, match="Invalid UUID format"):
            AssetMapping(asset_id="not-a-uuid", canonical_application_id=str(uuid4()))


class TestBulkMapAssets:
    """Test bulk_map_assets endpoint logic."""

    @pytest.mark.asyncio
    async def test_missing_tenant_headers(
        self, mock_db_session, sample_asset_ids, sample_canonical_app_id
    ):
        """Test rejection when tenant headers are missing."""
        context = RequestContext(
            client_account_id=None,  # Missing
            engagement_id=None,  # Missing
            user_id=None,
        )

        mappings = [
            AssetMapping(
                asset_id=sample_asset_ids[0],
                canonical_application_id=sample_canonical_app_id,
            )
        ]
        request = BulkMappingRequest(mappings=mappings)

        with pytest.raises(HTTPException) as exc_info:
            await bulk_map_assets(request, mock_db_session, context)

        assert exc_info.value.status_code == 400
        assert "Missing tenant headers" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_tenant_uuid_format(
        self, mock_db_session, sample_asset_ids, sample_canonical_app_id
    ):
        """Test rejection of invalid tenant UUID format."""
        context = RequestContext(
            client_account_id="invalid-uuid", engagement_id=str(uuid4()), user_id=None
        )

        mappings = [
            AssetMapping(
                asset_id=sample_asset_ids[0],
                canonical_application_id=sample_canonical_app_id,
            )
        ]
        request = BulkMappingRequest(mappings=mappings)

        with pytest.raises(HTTPException) as exc_info:
            await bulk_map_assets(request, mock_db_session, context)

        assert exc_info.value.status_code == 400
        assert "Invalid tenant UUID format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_canonical_app_not_found(
        self, mock_db_session, mock_context, sample_asset_ids, sample_canonical_app_id
    ):
        """Test rejection when canonical application doesn't exist."""
        # Mock empty result for canonical app query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        mappings = [
            AssetMapping(
                asset_id=sample_asset_ids[0],
                canonical_application_id=sample_canonical_app_id,
            )
        ]
        request = BulkMappingRequest(mappings=mappings)

        with pytest.raises(HTTPException) as exc_info:
            await bulk_map_assets(request, mock_db_session, mock_context)

        assert exc_info.value.status_code == 403
        assert "not found or do not belong to tenant" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_successful_bulk_mapping(
        self, mock_db_session, mock_context, sample_asset_ids, sample_canonical_app_id
    ):
        """Test successful bulk mapping of assets."""
        # Mock canonical application validation
        from app.models.canonical_applications.canonical_application import (
            CanonicalApplication,
        )

        mock_canonical_app = MagicMock(spec=CanonicalApplication)
        mock_canonical_app.id = sample_canonical_app_id
        mock_canonical_app.canonical_name = "Test Application"

        mock_canonical_result = MagicMock()
        mock_canonical_result.scalars.return_value.all.return_value = [
            mock_canonical_app
        ]

        # Mock asset validation (return valid assets)
        from app.models.asset.models import Asset

        mock_assets = []
        for asset_id in sample_asset_ids[:3]:
            mock_asset = MagicMock(spec=Asset)
            mock_asset.id = asset_id
            mock_asset.name = f"Asset {asset_id[:8]}"
            mock_assets.append(mock_asset)

        async def execute_side_effect(*args, **kwargs):
            """Mock execute behavior."""
            # First call: canonical app query
            if mock_db_session.execute.call_count == 1:
                return mock_canonical_result
            # Subsequent calls: asset queries and inserts
            else:
                mock_asset_result = MagicMock()
                mock_asset_result.scalar_one_or_none.return_value = mock_assets[
                    (mock_db_session.execute.call_count - 2) % len(mock_assets)
                ]
                return mock_asset_result

        mock_db_session.execute.side_effect = execute_side_effect

        # Mock transaction context
        mock_db_session.begin.return_value.__aenter__ = AsyncMock()
        mock_db_session.begin.return_value.__aexit__ = AsyncMock()

        mappings = [
            AssetMapping(asset_id=aid, canonical_application_id=sample_canonical_app_id)
            for aid in sample_asset_ids[:3]
        ]
        request = BulkMappingRequest(mappings=mappings)

        response = await bulk_map_assets(request, mock_db_session, mock_context)

        assert response.total_requested == 3
        assert response.successfully_mapped == 3
        assert response.already_mapped == 0
        assert len(response.errors) == 0
        assert response.canonical_application_name == "Test Application"

    @pytest.mark.asyncio
    async def test_partial_failure_with_errors(
        self, mock_db_session, mock_context, sample_asset_ids, sample_canonical_app_id
    ):
        """Test handling of partial failures with some invalid assets."""
        # Mock canonical application validation
        from app.models.canonical_applications.canonical_application import (
            CanonicalApplication,
        )

        mock_canonical_app = MagicMock(spec=CanonicalApplication)
        mock_canonical_app.id = sample_canonical_app_id
        mock_canonical_app.canonical_name = "Test Application"

        mock_canonical_result = MagicMock()
        mock_canonical_result.scalars.return_value.all.return_value = [
            mock_canonical_app
        ]

        # Mock assets - first one exists, second one doesn't
        from app.models.asset.models import Asset

        mock_asset_1 = MagicMock(spec=Asset)
        mock_asset_1.id = sample_asset_ids[0]
        mock_asset_1.name = "Valid Asset"

        call_count = 0

        async def execute_side_effect(*args, **kwargs):
            """Mock execute behavior with mixed results."""
            nonlocal call_count
            call_count += 1

            # First call: canonical app query
            if call_count == 1:
                return mock_canonical_result

            # Second call: first asset (exists)
            if call_count == 2:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_asset_1
                return mock_result

            # Third call: first asset insert
            if call_count == 3:
                mock_result = MagicMock()
                mock_result.rowcount = 1
                return mock_result

            # Fourth call: second asset (doesn't exist)
            if call_count == 4:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = None
                return mock_result

            # Default
            return MagicMock()

        mock_db_session.execute.side_effect = execute_side_effect

        # Mock transaction context
        mock_db_session.begin.return_value.__aenter__ = AsyncMock()
        mock_db_session.begin.return_value.__aexit__ = AsyncMock()

        mappings = [
            AssetMapping(
                asset_id=sample_asset_ids[0],
                canonical_application_id=sample_canonical_app_id,
            ),
            AssetMapping(
                asset_id=sample_asset_ids[1],
                canonical_application_id=sample_canonical_app_id,
            ),
        ]
        request = BulkMappingRequest(mappings=mappings)

        response = await bulk_map_assets(request, mock_db_session, mock_context)

        assert response.total_requested == 2
        assert response.successfully_mapped == 1
        assert len(response.errors) == 1
        assert response.errors[0].asset_id == sample_asset_ids[1]
        assert "not found" in response.errors[0].error

    @pytest.mark.asyncio
    async def test_cross_tenant_canonical_app_rejected(
        self, mock_db_session, mock_context, sample_asset_ids
    ):
        """Test rejection of canonical app from different tenant."""
        # Mock empty result for canonical app (cross-tenant)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        cross_tenant_canonical_id = str(uuid4())
        mappings = [
            AssetMapping(
                asset_id=sample_asset_ids[0],
                canonical_application_id=cross_tenant_canonical_id,
            )
        ]
        request = BulkMappingRequest(mappings=mappings)

        with pytest.raises(HTTPException) as exc_info:
            await bulk_map_assets(request, mock_db_session, mock_context)

        assert exc_info.value.status_code == 403
        assert "do not belong to tenant" in exc_info.value.detail


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
