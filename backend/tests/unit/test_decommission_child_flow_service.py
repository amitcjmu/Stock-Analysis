"""
Unit Tests for DecommissionChildFlowService

Tests the child flow service implementation following ADR-025 pattern.

Reference:
- backend/app/services/child_flow_services/decommission.py
- Pattern: backend/tests/unit/test_collection_child_flow_service.py (if exists)

Created: Issue #937 (Phase 3 of Decommission Flow Implementation)
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.decommission_flow import DecommissionFlow
from app.services.child_flow_services.decommission import DecommissionChildFlowService


@pytest.fixture
def mock_context():
    """Create mock RequestContext with tenant scoping."""
    context = MagicMock(spec=RequestContext)
    context.client_account_id = uuid.uuid4()
    context.engagement_id = uuid.uuid4()
    return context


@pytest.fixture
def mock_db():
    """Create mock AsyncSession."""
    return MagicMock(spec=AsyncSession)


@pytest.fixture
def sample_flow_data():
    """Sample decommission flow data for testing."""
    flow_id = uuid.uuid4()
    master_flow_id = uuid.uuid4()
    system_ids = [uuid.uuid4(), uuid.uuid4()]

    return {
        "flow_id": flow_id,
        "master_flow_id": master_flow_id,
        "client_account_id": uuid.uuid4(),
        "engagement_id": uuid.uuid4(),
        "flow_name": "Test Decommission Flow",
        "created_by": "test_user",
        "status": "decommission_planning",
        "current_phase": "decommission_planning",
        "selected_system_ids": system_ids,
        "system_count": len(system_ids),
        "decommission_strategy": {"priority": "high", "execution_mode": "sequential"},
        "runtime_state": {},
        "total_systems_decommissioned": 0,
        "estimated_annual_savings": 50000.00,
        "compliance_score": 95.5,
        "decommission_planning_status": "pending",
        "data_migration_status": "pending",
        "system_shutdown_status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_decommission_flow(sample_flow_data):
    """Create mock DecommissionFlow entity."""
    flow = MagicMock(spec=DecommissionFlow)
    for key, value in sample_flow_data.items():
        setattr(flow, key, value)
    return flow


class TestDecommissionChildFlowServiceInitialization:
    """Test service initialization and tenant scoping."""

    def test_service_initialization(self, mock_db, mock_context):
        """Test service initializes with correct tenant scoping."""
        service = DecommissionChildFlowService(mock_db, mock_context)

        assert service.db == mock_db
        assert service.context == mock_context
        assert service.repository is not None
        # Verify repository is initialized with tenant scoping
        assert str(service.repository.client_account_id) == str(
            mock_context.client_account_id
        )
        assert str(service.repository.engagement_id) == str(mock_context.engagement_id)


class TestGetChildStatus:
    """Test get_child_status method."""

    @pytest.mark.asyncio
    async def test_get_child_status_success(
        self, mock_db, mock_context, mock_decommission_flow
    ):
        """Test successful retrieval of child flow status."""
        service = DecommissionChildFlowService(mock_db, mock_context)

        # Mock repository method
        service.repository.get_by_master_flow_id = AsyncMock(
            return_value=mock_decommission_flow
        )

        flow_id = str(mock_decommission_flow.master_flow_id)
        result = await service.get_child_status(flow_id)

        # Verify result
        assert result is not None
        assert result["status"] == mock_decommission_flow.status
        assert result["current_phase"] == mock_decommission_flow.current_phase
        assert result["system_count"] == mock_decommission_flow.system_count
        assert len(result["selected_system_ids"]) == len(
            mock_decommission_flow.selected_system_ids
        )
        assert (
            result["decommission_strategy"]
            == mock_decommission_flow.decommission_strategy
        )
        assert result["compliance_score"] == float(
            mock_decommission_flow.compliance_score
        )
        assert (
            result["decommission_planning_status"]
            == mock_decommission_flow.decommission_planning_status
        )
        assert (
            result["data_migration_status"]
            == mock_decommission_flow.data_migration_status
        )
        assert (
            result["system_shutdown_status"]
            == mock_decommission_flow.system_shutdown_status
        )

        # Verify repository was called correctly
        service.repository.get_by_master_flow_id.assert_called_once_with(
            uuid.UUID(flow_id)
        )

    @pytest.mark.asyncio
    async def test_get_child_status_not_found(self, mock_db, mock_context):
        """Test get_child_status when flow not found."""
        service = DecommissionChildFlowService(mock_db, mock_context)

        # Mock repository method to return None
        service.repository.get_by_master_flow_id = AsyncMock(return_value=None)

        flow_id = str(uuid.uuid4())
        result = await service.get_child_status(flow_id)

        # Verify result is None
        assert result is None

    @pytest.mark.asyncio
    async def test_get_child_status_handles_exception(self, mock_db, mock_context):
        """Test get_child_status handles exceptions gracefully."""
        service = DecommissionChildFlowService(mock_db, mock_context)

        # Mock repository method to raise exception
        service.repository.get_by_master_flow_id = AsyncMock(
            side_effect=Exception("Database error")
        )

        flow_id = str(uuid.uuid4())
        result = await service.get_child_status(flow_id)

        # Verify result is None (exception handled)
        assert result is None


class TestGetByMasterFlowId:
    """Test get_by_master_flow_id method."""

    @pytest.mark.asyncio
    async def test_get_by_master_flow_id_success(
        self, mock_db, mock_context, mock_decommission_flow
    ):
        """Test successful retrieval by master flow ID."""
        service = DecommissionChildFlowService(mock_db, mock_context)

        # Mock repository method
        service.repository.get_by_master_flow_id = AsyncMock(
            return_value=mock_decommission_flow
        )

        flow_id = str(mock_decommission_flow.master_flow_id)
        result = await service.get_by_master_flow_id(flow_id)

        # Verify result
        assert result == mock_decommission_flow
        service.repository.get_by_master_flow_id.assert_called_once_with(
            uuid.UUID(flow_id)
        )

    @pytest.mark.asyncio
    async def test_get_by_master_flow_id_not_found(self, mock_db, mock_context):
        """Test get_by_master_flow_id when flow not found."""
        service = DecommissionChildFlowService(mock_db, mock_context)

        # Mock repository method to return None
        service.repository.get_by_master_flow_id = AsyncMock(return_value=None)

        flow_id = str(uuid.uuid4())
        result = await service.get_by_master_flow_id(flow_id)

        # Verify result is None
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_master_flow_id_handles_exception(self, mock_db, mock_context):
        """Test get_by_master_flow_id handles exceptions gracefully."""
        service = DecommissionChildFlowService(mock_db, mock_context)

        # Mock repository method to raise exception
        service.repository.get_by_master_flow_id = AsyncMock(
            side_effect=Exception("Database error")
        )

        flow_id = str(uuid.uuid4())
        result = await service.get_by_master_flow_id(flow_id)

        # Verify result is None (exception handled)
        assert result is None


class TestExecutePhase:
    """Test execute_phase routing and phase execution."""

    @pytest.mark.asyncio
    async def test_execute_phase_raises_for_not_found(self, mock_db, mock_context):
        """Test execute_phase raises ValueError when flow not found."""
        service = DecommissionChildFlowService(mock_db, mock_context)

        # Mock repository method to return None
        service.repository.get_by_master_flow_id = AsyncMock(return_value=None)

        flow_id = str(uuid.uuid4())

        with pytest.raises(ValueError, match="Decommission flow not found"):
            await service.execute_phase(flow_id, "decommission_planning")

    @pytest.mark.asyncio
    async def test_execute_phase_raises_for_unknown_phase(
        self, mock_db, mock_context, mock_decommission_flow
    ):
        """Test execute_phase raises ValueError for unknown phase."""
        service = DecommissionChildFlowService(mock_db, mock_context)

        # Mock repository method
        service.repository.get_by_master_flow_id = AsyncMock(
            return_value=mock_decommission_flow
        )

        flow_id = str(mock_decommission_flow.master_flow_id)

        with pytest.raises(ValueError, match="Unknown phase"):
            await service.execute_phase(flow_id, "invalid_phase")

    @pytest.mark.asyncio
    async def test_execute_decommission_planning_phase(
        self, mock_db, mock_context, mock_decommission_flow
    ):
        """Test decommission_planning phase execution."""
        service = DecommissionChildFlowService(mock_db, mock_context)

        # Mock repository methods
        service.repository.get_by_master_flow_id = AsyncMock(
            return_value=mock_decommission_flow
        )
        service.repository.update_phase_status = AsyncMock()
        service.repository.update_status = AsyncMock()

        flow_id = str(mock_decommission_flow.master_flow_id)
        result = await service.execute_phase(flow_id, "decommission_planning")

        # Verify result
        assert result["status"] == "success"
        assert result["phase"] == "decommission_planning"
        assert result["execution_type"] == "stub"
        assert result["next_phase"] == "data_migration"

        # Verify phase status updates
        assert service.repository.update_phase_status.call_count == 2
        # First call: set to running
        service.repository.update_phase_status.assert_any_call(
            flow_id=mock_decommission_flow.flow_id,
            phase_name="decommission_planning",
            phase_status="running",
        )
        # Second call: set to completed
        service.repository.update_phase_status.assert_any_call(
            flow_id=mock_decommission_flow.flow_id,
            phase_name="decommission_planning",
            phase_status="completed",
        )

        # Verify flow status update
        service.repository.update_status.assert_called_once_with(
            flow_id=mock_decommission_flow.flow_id,
            status="data_migration",
            current_phase="data_migration",
        )

    @pytest.mark.asyncio
    async def test_execute_data_migration_phase(
        self, mock_db, mock_context, mock_decommission_flow
    ):
        """Test data_migration phase execution."""
        service = DecommissionChildFlowService(mock_db, mock_context)

        # Mock repository methods
        service.repository.get_by_master_flow_id = AsyncMock(
            return_value=mock_decommission_flow
        )
        service.repository.update_phase_status = AsyncMock()
        service.repository.update_status = AsyncMock()

        flow_id = str(mock_decommission_flow.master_flow_id)
        result = await service.execute_phase(flow_id, "data_migration")

        # Verify result
        assert result["status"] == "success"
        assert result["phase"] == "data_migration"
        assert result["execution_type"] == "stub"
        assert result["next_phase"] == "system_shutdown"

        # Verify phase status updates
        assert service.repository.update_phase_status.call_count == 2
        # Verify flow status update to system_shutdown
        service.repository.update_status.assert_called_once_with(
            flow_id=mock_decommission_flow.flow_id,
            status="system_shutdown",
            current_phase="system_shutdown",
        )

    @pytest.mark.asyncio
    async def test_execute_system_shutdown_phase(
        self, mock_db, mock_context, mock_decommission_flow
    ):
        """Test system_shutdown phase execution."""
        service = DecommissionChildFlowService(mock_db, mock_context)

        # Mock repository methods
        service.repository.get_by_master_flow_id = AsyncMock(
            return_value=mock_decommission_flow
        )
        service.repository.update_phase_status = AsyncMock()
        service.repository.update_status = AsyncMock()

        flow_id = str(mock_decommission_flow.master_flow_id)
        result = await service.execute_phase(flow_id, "system_shutdown")

        # Verify result
        assert result["status"] == "success"
        assert result["phase"] == "system_shutdown"
        assert result["execution_type"] == "stub"
        assert result["next_phase"] == "completed"

        # Verify phase status updates
        assert service.repository.update_phase_status.call_count == 2
        # Verify flow status update to completed
        service.repository.update_status.assert_called_once_with(
            flow_id=mock_decommission_flow.flow_id,
            status="completed",
            current_phase="completed",
        )

    @pytest.mark.asyncio
    async def test_execute_phase_handles_exception(
        self, mock_db, mock_context, mock_decommission_flow
    ):
        """Test execute_phase handles exceptions during phase execution."""
        service = DecommissionChildFlowService(mock_db, mock_context)

        # Mock repository methods
        service.repository.get_by_master_flow_id = AsyncMock(
            return_value=mock_decommission_flow
        )
        service.repository.update_phase_status = AsyncMock(
            side_effect=Exception("Database error")
        )

        flow_id = str(mock_decommission_flow.master_flow_id)
        result = await service.execute_phase(flow_id, "decommission_planning")

        # Verify error result
        assert result["status"] == "failed"
        assert result["phase"] == "decommission_planning"
        assert "error" in result
        assert result["error_type"] == "Exception"
