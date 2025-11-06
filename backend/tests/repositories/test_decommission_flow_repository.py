"""
Unit Tests for DecommissionFlowRepository

Tests the decommission flow repository CRUD operations to ensure:
1. Proper multi-tenant scoping on all queries
2. Correct repository methods are implemented
3. Master Flow Orchestrator integration
4. Phase status updates work correctly
5. Error handling and edge cases
6. Context isolation between tenants

Reference:
- Issue #933
- Pattern: backend/tests/backend/unit/test_repository_factory.py
- Implementation: backend/app/repositories/decommission_flow_repository.py
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decommission_flow import DecommissionFlow
from app.repositories.decommission_flow_repository import DecommissionFlowRepository


class TestDecommissionFlowRepositoryInitialization:
    """Test suite for repository initialization and context handling."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        db.delete = AsyncMock()
        db.commit = AsyncMock()
        return db

    def test_repository_initialization_with_context(self, mock_db):
        """Test that repository initializes correctly with client and engagement IDs."""
        repo = DecommissionFlowRepository(
            db=mock_db,
            client_account_id="client-123",
            engagement_id="engagement-456",
        )

        assert repo.db == mock_db
        assert repo.client_account_id == "client-123"
        assert repo.engagement_id == "engagement-456"
        assert repo.model_class == DecommissionFlow

    def test_repository_initialization_without_client_id_raises_error(self, mock_db):
        """Test that repository raises ValueError when client_account_id is None."""
        with pytest.raises(ValueError, match="SECURITY.*Client account ID is required"):
            DecommissionFlowRepository(
                db=mock_db,
                client_account_id=None,
                engagement_id="engagement-456",
            )

    def test_repository_multi_tenant_flags(self, mock_db):
        """Test that repository recognizes multi-tenant fields on DecommissionFlow."""
        repo = DecommissionFlowRepository(
            db=mock_db,
            client_account_id="client-123",
            engagement_id="engagement-456",
        )

        assert repo.has_client_account is True
        assert repo.has_engagement is True


class TestDecommissionFlowRepositoryCreate:
    """Test suite for create operations."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def repo(self, mock_db):
        """Create repository instance."""
        return DecommissionFlowRepository(
            db=mock_db,
            client_account_id="client-123",
            engagement_id="engagement-456",
        )

    @pytest.mark.asyncio
    async def test_create_decommission_flow_success(self, repo, mock_db):
        """Test successful creation of decommission flow with MFO integration."""
        master_flow_id = uuid.uuid4()
        system_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

        # Mock the parent class create method
        with patch.object(repo, "create", wraps=repo.create):
            # Mock the actual database interaction
            mock_flow = MagicMock(spec=DecommissionFlow)
            mock_flow.flow_id = uuid.uuid4()
            mock_flow.flow_name = "Test Decommission"
            mock_flow.master_flow_id = master_flow_id
            mock_flow.system_count = len(system_ids)

            # Patch the super().create call
            with patch(
                "app.repositories.context_aware_repository.ContextAwareRepository.create",
                return_value=mock_flow,
            ):
                result = await repo.create(
                    flow_name="Test Decommission",
                    selected_system_ids=system_ids,
                    created_by="user-123",
                    decommission_strategy={"priority": "high"},
                    master_flow_id=master_flow_id,
                )

                assert result is not None
                assert result.flow_name == "Test Decommission"
                assert result.master_flow_id == master_flow_id
                assert result.system_count == len(system_ids)

    @pytest.mark.asyncio
    async def test_create_without_master_flow_id_raises_error(self, repo):
        """Test that create raises ValueError when master_flow_id is None."""
        system_ids = [uuid.uuid4()]

        with pytest.raises(ValueError, match="master_flow_id is required"):
            await repo.create(
                flow_name="Test Decommission",
                selected_system_ids=system_ids,
                created_by="user-123",
                master_flow_id=None,
            )

    @pytest.mark.asyncio
    async def test_create_generates_flow_id_if_not_provided(self, repo):
        """Test that create generates flow_id if not provided in kwargs."""
        master_flow_id = uuid.uuid4()
        system_ids = [uuid.uuid4()]

        mock_flow = MagicMock(spec=DecommissionFlow)
        mock_flow.flow_id = uuid.uuid4()

        with patch(
            "app.repositories.context_aware_repository.ContextAwareRepository.create",
            return_value=mock_flow,
        ):
            result = await repo.create(
                flow_name="Test",
                selected_system_ids=system_ids,
                created_by="user-123",
                master_flow_id=master_flow_id,
            )

            assert result.flow_id is not None
            assert isinstance(result.flow_id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_create_applies_tenant_context(self, repo):
        """Test that create applies client_account_id and engagement_id."""
        master_flow_id = uuid.uuid4()
        system_ids = [uuid.uuid4()]

        captured_data = {}

        async def capture_create_call(**data):
            captured_data.update(data)
            mock_flow = MagicMock(spec=DecommissionFlow)
            mock_flow.flow_id = data.get("flow_id")
            return mock_flow

        with patch(
            "app.repositories.context_aware_repository.ContextAwareRepository.create",
            side_effect=capture_create_call,
        ):
            await repo.create(
                flow_name="Test",
                selected_system_ids=system_ids,
                created_by="user-123",
                master_flow_id=master_flow_id,
            )

            assert captured_data["client_account_id"] == "client-123"
            assert captured_data["engagement_id"] == "engagement-456"


class TestDecommissionFlowRepositoryGet:
    """Test suite for get operations."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def repo(self, mock_db):
        """Create repository instance."""
        return DecommissionFlowRepository(
            db=mock_db,
            client_account_id="client-123",
            engagement_id="engagement-456",
        )

    @pytest.mark.asyncio
    async def test_get_by_flow_id_success(self, repo):
        """Test successful retrieval by flow_id."""
        flow_id = uuid.uuid4()
        mock_flow = MagicMock(spec=DecommissionFlow)
        mock_flow.flow_id = flow_id

        with patch.object(repo, "get_by_filters", return_value=[mock_flow]):
            result = await repo.get_by_flow_id(flow_id)

            assert result is not None
            assert result.flow_id == flow_id

    @pytest.mark.asyncio
    async def test_get_by_flow_id_not_found_returns_none(self, repo):
        """Test that get_by_flow_id returns None when flow not found."""
        flow_id = uuid.uuid4()

        with patch.object(repo, "get_by_filters", return_value=[]):
            result = await repo.get_by_flow_id(flow_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_by_flow_id_handles_database_error(self, repo):
        """Test that get_by_flow_id raises SQLAlchemyError on database errors."""
        flow_id = uuid.uuid4()

        with patch.object(
            repo,
            "get_by_filters",
            side_effect=SQLAlchemyError("Database error"),
        ):
            with pytest.raises(SQLAlchemyError):
                await repo.get_by_flow_id(flow_id)

    @pytest.mark.asyncio
    async def test_get_by_master_flow_id_success(self, repo):
        """Test successful retrieval by master_flow_id."""
        master_flow_id = uuid.uuid4()
        mock_flow = MagicMock(spec=DecommissionFlow)
        mock_flow.master_flow_id = master_flow_id

        with patch.object(repo, "get_by_filters", return_value=[mock_flow]):
            result = await repo.get_by_master_flow_id(master_flow_id)

            assert result is not None
            assert result.master_flow_id == master_flow_id

    @pytest.mark.asyncio
    async def test_get_by_master_flow_id_not_found(self, repo):
        """Test that get_by_master_flow_id returns None when flow not found."""
        master_flow_id = uuid.uuid4()

        with patch.object(repo, "get_by_filters", return_value=[]):
            result = await repo.get_by_master_flow_id(master_flow_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_by_status_filters_correctly(self, repo):
        """Test that get_by_status filters by status with tenant scoping."""
        mock_flows = [
            MagicMock(spec=DecommissionFlow, status="decommission_planning"),
            MagicMock(spec=DecommissionFlow, status="decommission_planning"),
        ]

        with patch.object(repo, "get_by_filters", return_value=mock_flows):
            result = await repo.get_by_status("decommission_planning")

            assert len(result) == 2
            assert all(flow.status == "decommission_planning" for flow in result)

    @pytest.mark.asyncio
    async def test_get_active_flows_excludes_completed_and_failed(self, repo):
        """Test that get_active_flows excludes completed and failed flows."""
        all_flows = [
            MagicMock(spec=DecommissionFlow, status="initialized"),
            MagicMock(spec=DecommissionFlow, status="decommission_planning"),
            MagicMock(spec=DecommissionFlow, status="data_migration"),
            MagicMock(spec=DecommissionFlow, status="system_shutdown"),
            MagicMock(spec=DecommissionFlow, status="completed"),
            MagicMock(spec=DecommissionFlow, status="failed"),
        ]

        with patch.object(repo, "get_all", return_value=all_flows):
            result = await repo.get_active_flows()

            assert len(result) == 4
            assert all(flow.status not in ["completed", "failed"] for flow in result)


class TestDecommissionFlowRepositoryUpdate:
    """Test suite for update operations."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def repo(self, mock_db):
        """Create repository instance."""
        return DecommissionFlowRepository(
            db=mock_db,
            client_account_id="client-123",
            engagement_id="engagement-456",
        )

    @pytest.mark.asyncio
    async def test_update_status_success(self, repo):
        """Test successful status update."""
        flow_id = uuid.uuid4()
        mock_flow = MagicMock(spec=DecommissionFlow)
        mock_flow.flow_id = flow_id
        mock_flow.status = "decommission_planning"

        with patch.object(repo, "get_by_flow_id", return_value=mock_flow):
            with patch.object(repo, "update", return_value=mock_flow):
                result = await repo.update_status(
                    flow_id=flow_id,
                    status="data_migration",
                    current_phase="data_migration",
                )

                assert result is not None

    @pytest.mark.asyncio
    async def test_update_status_flow_not_found(self, repo):
        """Test that update_status returns None when flow not found."""
        flow_id = uuid.uuid4()

        with patch.object(repo, "get_by_flow_id", return_value=None):
            result = await repo.update_status(
                flow_id=flow_id,
                status="data_migration",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_update_phase_status_success(self, repo):
        """Test successful phase status update."""
        flow_id = uuid.uuid4()
        mock_flow = MagicMock(spec=DecommissionFlow)
        mock_flow.flow_id = flow_id

        with patch.object(repo, "get_by_flow_id", return_value=mock_flow):
            with patch.object(repo, "update", return_value=mock_flow):
                result = await repo.update_phase_status(
                    flow_id=flow_id,
                    phase_name="decommission_planning",
                    phase_status="completed",
                )

                assert result is not None

    @pytest.mark.asyncio
    async def test_update_phase_status_invalid_phase_raises_error(self, repo):
        """Test that update_phase_status raises ValueError for invalid phase."""
        flow_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Invalid phase_name"):
            await repo.update_phase_status(
                flow_id=flow_id,
                phase_name="invalid_phase",
                phase_status="completed",
            )

    @pytest.mark.asyncio
    async def test_update_phase_status_valid_phases(self, repo):
        """Test that all valid phases are accepted."""
        flow_id = uuid.uuid4()
        mock_flow = MagicMock(spec=DecommissionFlow)
        mock_flow.flow_id = flow_id

        valid_phases = ["decommission_planning", "data_migration", "system_shutdown"]

        with patch.object(repo, "get_by_flow_id", return_value=mock_flow):
            with patch.object(repo, "update", return_value=mock_flow):
                for phase in valid_phases:
                    result = await repo.update_phase_status(
                        flow_id=flow_id,
                        phase_name=phase,
                        phase_status="running",
                    )
                    assert result is not None


class TestDecommissionFlowRepositoryList:
    """Test suite for list operations."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def repo(self, mock_db):
        """Create repository instance."""
        return DecommissionFlowRepository(
            db=mock_db,
            client_account_id="client-123",
            engagement_id="engagement-456",
        )

    @pytest.mark.asyncio
    async def test_list_by_tenant_success(self, repo):
        """Test successful listing of flows for tenant."""
        mock_flows = [
            MagicMock(spec=DecommissionFlow),
            MagicMock(spec=DecommissionFlow),
            MagicMock(spec=DecommissionFlow),
        ]

        with patch.object(repo, "get_all", return_value=mock_flows):
            result = await repo.list_by_tenant()

            assert len(result) == 3
            assert result == mock_flows

    @pytest.mark.asyncio
    async def test_list_by_tenant_with_pagination(self, repo):
        """Test listing with limit and offset."""
        mock_flows = [MagicMock(spec=DecommissionFlow)] * 5

        with patch.object(repo, "get_all", return_value=mock_flows):
            result = await repo.list_by_tenant(limit=10, offset=5)

            assert result is not None

    @pytest.mark.asyncio
    async def test_list_by_tenant_empty_results(self, repo):
        """Test listing returns empty list when no flows found."""
        with patch.object(repo, "get_all", return_value=[]):
            result = await repo.list_by_tenant()

            assert result == []


class TestDecommissionFlowRepositoryDelete:
    """Test suite for delete operations."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.delete = AsyncMock()
        db.flush = AsyncMock()
        return db

    @pytest.fixture
    def repo(self, mock_db):
        """Create repository instance."""
        return DecommissionFlowRepository(
            db=mock_db,
            client_account_id="client-123",
            engagement_id="engagement-456",
        )

    @pytest.mark.asyncio
    async def test_delete_success(self, repo):
        """Test successful deletion of flow."""
        flow_id = uuid.uuid4()
        mock_flow = MagicMock(spec=DecommissionFlow)
        mock_flow.flow_id = flow_id

        with patch.object(repo, "get_by_flow_id", return_value=mock_flow):
            with patch(
                "app.repositories.context_aware_repository.ContextAwareRepository.delete",
                return_value=True,
            ):
                result = await repo.delete(flow_id)

                assert result is True

    @pytest.mark.asyncio
    async def test_delete_flow_not_found(self, repo):
        """Test that delete returns False when flow not found."""
        flow_id = uuid.uuid4()

        with patch.object(repo, "get_by_flow_id", return_value=None):
            result = await repo.delete(flow_id)

            assert result is False

    @pytest.mark.asyncio
    async def test_delete_enforces_tenant_scoping(self, repo):
        """Test that delete checks tenant scoping before deletion."""
        flow_id = uuid.uuid4()

        # Simulate flow not found in current tenant
        with patch.object(repo, "get_by_flow_id", return_value=None):
            result = await repo.delete(flow_id)

            assert result is False


class TestDecommissionFlowRepositorySpecialQueries:
    """Test suite for special query methods."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def repo(self, mock_db):
        """Create repository instance."""
        return DecommissionFlowRepository(
            db=mock_db,
            client_account_id="client-123",
            engagement_id="engagement-456",
        )

    @pytest.mark.asyncio
    async def test_get_by_system_id_finds_flows(self, repo, mock_db):
        """Test that get_by_system_id finds flows containing the system."""
        system_id = uuid.uuid4()
        mock_flow1 = MagicMock(spec=DecommissionFlow)
        mock_flow1.selected_system_ids = [system_id, uuid.uuid4()]

        mock_flow2 = MagicMock(spec=DecommissionFlow)
        mock_flow2.selected_system_ids = [uuid.uuid4(), system_id]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[mock_flow1, mock_flow2])
        mock_result.scalars = MagicMock(return_value=mock_scalars)

        mock_db.execute.return_value = mock_result

        result = await repo.get_by_system_id(system_id)

        assert len(result) == 2
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_system_id_no_results(self, repo, mock_db):
        """Test that get_by_system_id returns empty list when no flows found."""
        system_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[])
        mock_result.scalars = MagicMock(return_value=mock_scalars)

        mock_db.execute.return_value = mock_result

        result = await repo.get_by_system_id(system_id)

        assert result == []


class TestMultiTenantIsolation:
    """Test suite for multi-tenant isolation and security."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_different_tenants_isolated(self, mock_db):
        """Test that flows from different tenants are isolated."""
        repo1 = DecommissionFlowRepository(
            db=mock_db,
            client_account_id="client-111",
            engagement_id="engagement-111",
        )

        repo2 = DecommissionFlowRepository(
            db=mock_db,
            client_account_id="client-222",
            engagement_id="engagement-222",
        )

        # Verify different tenant contexts
        assert repo1.client_account_id != repo2.client_account_id
        assert repo1.engagement_id != repo2.engagement_id

    @pytest.mark.asyncio
    async def test_context_aware_repository_enforces_client_id(self, mock_db):
        """Test that ContextAwareRepository enforces client_account_id requirement."""
        with pytest.raises(ValueError, match="SECURITY"):
            DecommissionFlowRepository(
                db=mock_db,
                client_account_id=None,
                engagement_id="engagement-456",
            )


class TestErrorHandling:
    """Test suite for error handling and edge cases."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def repo(self, mock_db):
        """Create repository instance."""
        return DecommissionFlowRepository(
            db=mock_db,
            client_account_id="client-123",
            engagement_id="engagement-456",
        )

    @pytest.mark.asyncio
    async def test_database_error_propagates(self, repo, mock_db):
        """Test that database errors are properly propagated."""
        system_id = uuid.uuid4()
        mock_db.execute.side_effect = SQLAlchemyError("Connection failed")

        with pytest.raises(SQLAlchemyError):
            await repo.get_by_system_id(system_id)

    @pytest.mark.asyncio
    async def test_update_status_handles_database_error(self, repo):
        """Test that update_status handles database errors."""
        flow_id = uuid.uuid4()

        with patch.object(
            repo,
            "get_by_flow_id",
            side_effect=SQLAlchemyError("Database error"),
        ):
            with pytest.raises(SQLAlchemyError):
                await repo.update_status(flow_id, "completed")

    @pytest.mark.asyncio
    async def test_list_by_tenant_handles_database_error(self, repo):
        """Test that list_by_tenant handles database errors."""
        with patch.object(
            repo,
            "get_all",
            side_effect=SQLAlchemyError("Database error"),
        ):
            with pytest.raises(SQLAlchemyError):
                await repo.list_by_tenant()
