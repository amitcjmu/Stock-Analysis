"""
Integration Tests for Decommission Flow MFO Integration (Issue #934)

Tests the Master Flow Orchestrator (MFO) integration layer for decommission flows,
verifying atomic transactions, ADR-012 compliance, and multi-tenant scoping.

Reference:
- backend/app/api/v1/endpoints/decommission_flow/mfo_integration.py
- Pattern: tests/backend/integration/conftest.py
- ADR-006: Master Flow Orchestrator
- ADR-012: Flow Status Management Separation
"""

import pytest
import pytest_asyncio
import uuid
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.decommission_flow import DecommissionFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.api.v1.endpoints.decommission_flow.mfo_integration import (
    create_decommission_via_mfo,
    get_decommission_status_via_mfo,
    update_decommission_phase_via_mfo,
    resume_decommission_flow,
    pause_decommission_flow,
)


# Test Database Configuration
# Use Docker service name when running inside Docker container
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432/migration_db"


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create isolated database session for each test.

    Uses actual database with transaction rollback for isolation.
    Note: Does NOT start a nested transaction - functions handle their own transactions.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()

    await engine.dispose()


@pytest.fixture
def test_client_account_id() -> uuid.UUID:
    """Client account UUID for testing (Demo Corporation from seed data)."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def test_engagement_id() -> uuid.UUID:
    """Engagement UUID for testing (Azure Transformation 2025 from seed data)."""
    return uuid.UUID("10a0d8b2-6c9b-48ef-816b-97e4a878cfbf")


@pytest.fixture
def test_system_ids() -> list[uuid.UUID]:
    """List of system UUIDs for testing."""
    return [uuid.uuid4() for _ in range(3)]


@pytest.fixture
def test_user_id() -> str:
    """User ID for testing."""
    return "test-user-123"


@pytest.mark.asyncio
class TestCreateDecommissionViaMFO:
    """Test suite for create_decommission_via_mfo function."""

    async def test_atomic_creation_success(
        self,
        db_session: AsyncSession,
        test_client_account_id: uuid.UUID,
        test_engagement_id: uuid.UUID,
        test_system_ids: list[uuid.UUID],
        test_user_id: str,
    ):
        """
        Test atomic creation of master + child flows.

        Verifies:
        - Both master and child flows created in single transaction
        - Same flow_id used for both
        - Master flow_id matches child master_flow_id
        """
        # Act
        result = await create_decommission_via_mfo(
            client_account_id=test_client_account_id,
            engagement_id=test_engagement_id,
            system_ids=test_system_ids,
            user_id=test_user_id,
            flow_name="Test Decommission",
            decommission_strategy={"priority": "high"},
            db=db_session,
        )

        # Assert result structure
        assert "flow_id" in result
        assert "master_flow_id" in result
        assert result["flow_id"] == result["master_flow_id"]
        assert result["status"] == "initialized"
        assert result["current_phase"] == "decommission_planning"
        assert result["selected_systems"] == len(test_system_ids)

        # Verify master flow in database
        flow_id = uuid.UUID(result["flow_id"])
        master_query = select(CrewAIFlowStateExtensions).where(
            CrewAIFlowStateExtensions.flow_id == flow_id
        )
        master_result = await db_session.execute(master_query)
        master_flow = master_result.scalar_one_or_none()

        assert master_flow is not None
        assert master_flow.flow_type == "decommission"
        assert master_flow.flow_status == "running"
        assert master_flow.client_account_id == test_client_account_id
        assert master_flow.engagement_id == test_engagement_id

        # Verify child flow in database
        child_query = select(DecommissionFlow).where(
            DecommissionFlow.flow_id == flow_id
        )
        child_result = await db_session.execute(child_query)
        child_flow = child_result.scalar_one_or_none()

        assert child_flow is not None
        assert child_flow.master_flow_id == master_flow.flow_id
        assert child_flow.status == "initialized"
        assert child_flow.current_phase == "decommission_planning"
        assert len(child_flow.selected_system_ids) == len(test_system_ids)
        assert child_flow.system_count == len(test_system_ids)
        assert child_flow.decommission_planning_status == "pending"
        assert child_flow.data_migration_status == "pending"
        assert child_flow.system_shutdown_status == "pending"

    async def test_atomic_rollback_on_failure(
        self,
        db_session: AsyncSession,
        test_client_account_id: uuid.UUID,
        test_engagement_id: uuid.UUID,
        test_user_id: str,
    ):
        """
        Test transaction rollback when creation fails.

        Verifies:
        - Neither master nor child flow created if transaction fails
        - No orphaned records in database
        """
        # Act - Attempt creation with invalid input (empty system_ids)
        with pytest.raises(ValueError, match="At least one system ID is required"):
            await create_decommission_via_mfo(
                client_account_id=test_client_account_id,
                engagement_id=test_engagement_id,
                system_ids=[],  # Invalid: empty list
                user_id=test_user_id,
                flow_name="Test Decommission",
                decommission_strategy=None,
                db=db_session,
            )

        # Assert no flows were created
        master_count_query = select(CrewAIFlowStateExtensions).where(
            CrewAIFlowStateExtensions.client_account_id == test_client_account_id
        )
        master_count = await db_session.execute(master_count_query)
        assert len(master_count.scalars().all()) == 0

        child_count_query = select(DecommissionFlow).where(
            DecommissionFlow.client_account_id == test_client_account_id
        )
        child_count = await db_session.execute(child_count_query)
        assert len(child_count.scalars().all()) == 0

    async def test_multi_tenant_scoping(
        self,
        db_session: AsyncSession,
        test_system_ids: list[uuid.UUID],
        test_user_id: str,
    ):
        """
        Test multi-tenant isolation.

        Verifies:
        - Each tenant's flows are isolated by client_account_id + engagement_id
        - No cross-tenant data leakage
        """
        # Create flows for two different tenants
        tenant1_client_id = uuid.uuid4()
        tenant1_engagement_id = uuid.uuid4()
        tenant2_client_id = uuid.uuid4()
        tenant2_engagement_id = uuid.uuid4()

        # Create flow for tenant 1
        result1 = await create_decommission_via_mfo(
            client_account_id=tenant1_client_id,
            engagement_id=tenant1_engagement_id,
            system_ids=test_system_ids[:2],
            user_id=test_user_id,
            flow_name="Tenant 1 Decommission",
            decommission_strategy=None,
            db=db_session,
        )

        # Create flow for tenant 2
        result2 = await create_decommission_via_mfo(
            client_account_id=tenant2_client_id,
            engagement_id=tenant2_engagement_id,
            system_ids=test_system_ids[2:],
            user_id=test_user_id,
            flow_name="Tenant 2 Decommission",
            decommission_strategy=None,
            db=db_session,
        )

        # Verify flows are isolated
        assert result1["flow_id"] != result2["flow_id"]

        # Query tenant 1's flows
        tenant1_query = select(DecommissionFlow).where(
            DecommissionFlow.client_account_id == tenant1_client_id
        )
        tenant1_flows = await db_session.execute(tenant1_query)
        tenant1_results = tenant1_flows.scalars().all()
        assert len(tenant1_results) == 1
        assert str(tenant1_results[0].flow_id) == result1["flow_id"]

        # Query tenant 2's flows
        tenant2_query = select(DecommissionFlow).where(
            DecommissionFlow.client_account_id == tenant2_client_id
        )
        tenant2_flows = await db_session.execute(tenant2_query)
        tenant2_results = tenant2_flows.scalars().all()
        assert len(tenant2_results) == 1
        assert str(tenant2_results[0].flow_id) == result2["flow_id"]


@pytest.mark.asyncio
class TestGetDecommissionStatusViaMFO:
    """Test suite for get_decommission_status_via_mfo function."""

    async def test_adr012_child_status_returned(
        self,
        db_session: AsyncSession,
        test_client_account_id: uuid.UUID,
        test_engagement_id: uuid.UUID,
        test_system_ids: list[uuid.UUID],
        test_user_id: str,
    ):
        """
        Test ADR-012 compliance: Child status returned for operational decisions.

        Verifies:
        - Child flow status is primary operational state
        - Master flow status included for coordination only
        - Frontend/agents should use child status
        """
        # Arrange - Create flow
        create_result = await create_decommission_via_mfo(
            client_account_id=test_client_account_id,
            engagement_id=test_engagement_id,
            system_ids=test_system_ids,
            user_id=test_user_id,
            flow_name="Test Decommission",
            decommission_strategy=None,
            db=db_session,
        )
        flow_id = uuid.UUID(create_result["flow_id"])

        # Act - Get status
        status = await get_decommission_status_via_mfo(
            flow_id=flow_id,
            db=db_session,
            client_account_id=test_client_account_id,
            engagement_id=test_engagement_id,
        )

        # Assert - Child status is primary (ADR-012)
        assert "status" in status  # Child operational status
        assert "master_status" in status  # Master lifecycle status
        assert status["status"] == "initialized"  # Child status for UI
        assert status["master_status"] == "running"  # Master lifecycle
        assert status["current_phase"] == "decommission_planning"

        # Verify phase progress from child flow
        assert "phase_progress" in status
        assert "decommission_planning" in status["phase_progress"]
        assert "data_migration" in status["phase_progress"]
        assert "system_shutdown" in status["phase_progress"]

    async def test_tenant_scoping_enforcement(
        self,
        db_session: AsyncSession,
        test_system_ids: list[uuid.UUID],
        test_user_id: str,
    ):
        """
        Test tenant scoping prevents cross-tenant access.

        Verifies:
        - Cannot access another tenant's flow
        - Raises ValueError if flow not found for tenant
        """
        # Arrange - Create flow for tenant 1
        tenant1_client_id = uuid.uuid4()
        tenant1_engagement_id = uuid.uuid4()

        create_result = await create_decommission_via_mfo(
            client_account_id=tenant1_client_id,
            engagement_id=tenant1_engagement_id,
            system_ids=test_system_ids,
            user_id=test_user_id,
            flow_name="Tenant 1 Decommission",
            decommission_strategy=None,
            db=db_session,
        )
        flow_id = uuid.UUID(create_result["flow_id"])

        # Act - Try to access with different tenant credentials
        tenant2_client_id = uuid.uuid4()
        tenant2_engagement_id = uuid.uuid4()

        with pytest.raises(ValueError, match=f"Decommission flow {flow_id} not found"):
            await get_decommission_status_via_mfo(
                flow_id=flow_id,
                db=db_session,
                client_account_id=tenant2_client_id,  # Different tenant
                engagement_id=tenant2_engagement_id,
            )

    async def test_phase_progress_tracking(
        self,
        db_session: AsyncSession,
        test_client_account_id: uuid.UUID,
        test_engagement_id: uuid.UUID,
        test_system_ids: list[uuid.UUID],
        test_user_id: str,
    ):
        """
        Test phase progress tracking per ADR-027 FlowTypeConfig.

        Verifies:
        - Each phase has dedicated status column
        - Phase timestamps tracked correctly
        - Phase progression reflected in status
        """
        # Arrange - Create and progress flow
        create_result = await create_decommission_via_mfo(
            client_account_id=test_client_account_id,
            engagement_id=test_engagement_id,
            system_ids=test_system_ids,
            user_id=test_user_id,
            flow_name="Test Decommission",
            decommission_strategy=None,
            db=db_session,
        )
        flow_id = uuid.UUID(create_result["flow_id"])

        # Complete first phase
        await update_decommission_phase_via_mfo(
            flow_id=flow_id,
            phase_name="decommission_planning",
            phase_status="completed",
            phase_data={"plans_generated": 3},
            db=db_session,
        )

        # Act - Get updated status
        status = await get_decommission_status_via_mfo(
            flow_id=flow_id,
            db=db_session,
        )

        # Assert - Phase progress tracked
        assert (
            status["phase_progress"]["decommission_planning"]["status"] == "completed"
        )
        assert (
            status["phase_progress"]["decommission_planning"]["completed_at"]
            is not None
        )
        assert status["current_phase"] == "data_migration"  # Advanced to next phase


@pytest.mark.asyncio
class TestUpdateDecommissionPhaseViaMFO:
    """Test suite for update_decommission_phase_via_mfo function."""

    async def test_atomic_master_child_sync(
        self,
        db_session: AsyncSession,
        test_client_account_id: uuid.UUID,
        test_engagement_id: uuid.UUID,
        test_system_ids: list[uuid.UUID],
        test_user_id: str,
    ):
        """
        Test atomic synchronization of master + child flows.

        Verifies:
        - Both master and child updated in single transaction
        - Master status syncs with child phase progression
        - Rollback on failure
        """
        # Arrange - Create flow
        create_result = await create_decommission_via_mfo(
            client_account_id=test_client_account_id,
            engagement_id=test_engagement_id,
            system_ids=test_system_ids,
            user_id=test_user_id,
            flow_name="Test Decommission",
            decommission_strategy=None,
            db=db_session,
        )
        flow_id = uuid.UUID(create_result["flow_id"])

        # Act - Update phase to completed
        result = await update_decommission_phase_via_mfo(
            flow_id=flow_id,
            phase_name="decommission_planning",
            phase_status="completed",
            phase_data={"dependency_count": 5},
            db=db_session,
        )

        # Assert - Both flows updated
        assert (
            result["phase_progress"]["decommission_planning"]["status"] == "completed"
        )
        assert result["current_phase"] == "data_migration"  # Advanced
        assert result["master_status"] == "running"  # Still running

        # Verify in database
        master_query = select(CrewAIFlowStateExtensions).where(
            CrewAIFlowStateExtensions.flow_id == flow_id
        )
        master_result = await db_session.execute(master_query)
        master_flow = master_result.scalar_one()
        assert master_flow.flow_status == "running"

        child_query = select(DecommissionFlow).where(
            DecommissionFlow.flow_id == flow_id
        )
        child_result = await db_session.execute(child_query)
        child_flow = child_result.scalar_one()
        assert child_flow.decommission_planning_status == "completed"
        assert child_flow.current_phase == "data_migration"
        assert child_flow.decommission_planning_completed_at is not None

    async def test_failed_phase_syncs_master(
        self,
        db_session: AsyncSession,
        test_client_account_id: uuid.UUID,
        test_engagement_id: uuid.UUID,
        test_system_ids: list[uuid.UUID],
        test_user_id: str,
    ):
        """
        Test failed phase syncs master flow to failed status.

        Verifies:
        - Phase failure propagates to master flow
        - Child status set to failed
        - Master status set to failed
        """
        # Arrange - Create flow
        create_result = await create_decommission_via_mfo(
            client_account_id=test_client_account_id,
            engagement_id=test_engagement_id,
            system_ids=test_system_ids,
            user_id=test_user_id,
            flow_name="Test Decommission",
            decommission_strategy=None,
            db=db_session,
        )
        flow_id = uuid.UUID(create_result["flow_id"])

        # Act - Mark phase as failed
        result = await update_decommission_phase_via_mfo(
            flow_id=flow_id,
            phase_name="decommission_planning",
            phase_status="failed",
            phase_data={"error": "dependency conflict"},
            db=db_session,
        )

        # Assert - Both flows marked as failed
        assert result["status"] == "failed"
        assert result["master_status"] == "failed"
        assert result["phase_progress"]["decommission_planning"]["status"] == "failed"

    async def test_completion_syncs_master(
        self,
        db_session: AsyncSession,
        test_client_account_id: uuid.UUID,
        test_engagement_id: uuid.UUID,
        test_system_ids: list[uuid.UUID],
        test_user_id: str,
    ):
        """
        Test final phase completion syncs master to completed.

        Verifies:
        - Last phase completion sets child to completed
        - Master flow syncs to completed
        - current_phase set to completed
        """
        # Arrange - Create flow and complete all phases
        create_result = await create_decommission_via_mfo(
            client_account_id=test_client_account_id,
            engagement_id=test_engagement_id,
            system_ids=test_system_ids,
            user_id=test_user_id,
            flow_name="Test Decommission",
            decommission_strategy=None,
            db=db_session,
        )
        flow_id = uuid.UUID(create_result["flow_id"])

        # Complete phase 1
        await update_decommission_phase_via_mfo(
            flow_id=flow_id,
            phase_name="decommission_planning",
            phase_status="completed",
            phase_data={},
            db=db_session,
        )

        # Complete phase 2
        await update_decommission_phase_via_mfo(
            flow_id=flow_id,
            phase_name="data_migration",
            phase_status="completed",
            phase_data={},
            db=db_session,
        )

        # Act - Complete final phase
        result = await update_decommission_phase_via_mfo(
            flow_id=flow_id,
            phase_name="system_shutdown",
            phase_status="completed",
            phase_data={},
            db=db_session,
        )

        # Assert - Flow completed
        assert result["status"] == "completed"
        assert result["master_status"] == "completed"
        assert result["current_phase"] == "completed"


@pytest.mark.asyncio
class TestResumeDecommissionFlow:
    """Test suite for resume_decommission_flow function."""

    async def test_resume_from_paused(
        self,
        db_session: AsyncSession,
        test_client_account_id: uuid.UUID,
        test_engagement_id: uuid.UUID,
        test_system_ids: list[uuid.UUID],
        test_user_id: str,
    ):
        """
        Test resuming paused flow.

        Verifies:
        - Paused flow can be resumed
        - Master status updated to running
        - Child status restored to current phase
        - Resume timestamp recorded
        """
        # Arrange - Create and pause flow
        create_result = await create_decommission_via_mfo(
            client_account_id=test_client_account_id,
            engagement_id=test_engagement_id,
            system_ids=test_system_ids,
            user_id=test_user_id,
            flow_name="Test Decommission",
            decommission_strategy=None,
            db=db_session,
        )
        flow_id = uuid.UUID(create_result["flow_id"])

        # Pause flow
        await pause_decommission_flow(flow_id=flow_id, db=db_session)

        # Act - Resume flow
        result = await resume_decommission_flow(flow_id=flow_id, db=db_session)

        # Assert - Flow resumed
        assert result["master_status"] == "running"
        assert result["status"] == "decommission_planning"  # Restored to current phase
        assert "resumed_at" in result["runtime_state"]

    async def test_resume_non_paused_fails(
        self,
        db_session: AsyncSession,
        test_client_account_id: uuid.UUID,
        test_engagement_id: uuid.UUID,
        test_system_ids: list[uuid.UUID],
        test_user_id: str,
    ):
        """
        Test resuming non-paused flow fails.

        Verifies:
        - Cannot resume flow that isn't paused
        - Raises ValueError with clear message
        """
        # Arrange - Create running flow (not paused)
        create_result = await create_decommission_via_mfo(
            client_account_id=test_client_account_id,
            engagement_id=test_engagement_id,
            system_ids=test_system_ids,
            user_id=test_user_id,
            flow_name="Test Decommission",
            decommission_strategy=None,
            db=db_session,
        )
        flow_id = uuid.UUID(create_result["flow_id"])

        # Act & Assert - Cannot resume running flow
        with pytest.raises(ValueError, match="cannot be resumed"):
            await resume_decommission_flow(flow_id=flow_id, db=db_session)


@pytest.mark.asyncio
class TestPauseDecommissionFlow:
    """Test suite for pause_decommission_flow function."""

    async def test_pause_running_flow(
        self,
        db_session: AsyncSession,
        test_client_account_id: uuid.UUID,
        test_engagement_id: uuid.UUID,
        test_system_ids: list[uuid.UUID],
        test_user_id: str,
    ):
        """
        Test pausing running flow.

        Verifies:
        - Running flow can be paused
        - Master status updated to paused
        - Current status stored before pause
        - Pause timestamp recorded
        """
        # Arrange - Create running flow
        create_result = await create_decommission_via_mfo(
            client_account_id=test_client_account_id,
            engagement_id=test_engagement_id,
            system_ids=test_system_ids,
            user_id=test_user_id,
            flow_name="Test Decommission",
            decommission_strategy=None,
            db=db_session,
        )
        flow_id = uuid.UUID(create_result["flow_id"])

        # Act - Pause flow
        result = await pause_decommission_flow(flow_id=flow_id, db=db_session)

        # Assert - Flow paused
        assert result["master_status"] == "paused"
        assert "paused_at" in result["runtime_state"]
        assert "status_before_pause" in result["runtime_state"]
        assert result["runtime_state"]["status_before_pause"] == "initialized"
