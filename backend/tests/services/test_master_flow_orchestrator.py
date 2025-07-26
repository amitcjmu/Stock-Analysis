"""
Unit Tests for Master Flow Orchestrator

Tests the core functionality of the MasterFlowOrchestrator including:
- Flow creation for all types
- Phase execution with validation
- Pause/resume functionality
- Error handling and retry logic
- Multi-tenant isolation
- Performance tracking
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import RequestContext
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.master_flow_orchestrator import (
    FlowOperationType,
    MasterFlowOrchestrator,
)


@pytest.fixture
def mock_db():
    """Mock database session"""
    mock = AsyncMock(spec=AsyncSession)
    return mock


@pytest.fixture
def test_context():
    """Test request context"""
    return RequestContext(
        client_account_id=str(uuid.uuid4()),
        engagement_id=str(uuid.uuid4()),
        user_id="test-user",
    )


@pytest.fixture
def mock_flow_registry():
    """Mock flow type registry"""
    mock_registry = Mock()

    # Mock flow configuration
    mock_flow_config = Mock()
    mock_flow_config.display_name = "Test Flow"
    mock_flow_config.default_configuration = {}
    mock_flow_config.initialization_handler = None
    mock_flow_config.phases = [
        Mock(
            name="phase1",
            validators=[],
            crew_config={"agents": ["agent1"], "tasks": ["task1"]},
        ),
        Mock(
            name="phase2",
            validators=[],
            crew_config={"agents": ["agent2"], "tasks": ["task2"]},
        ),
    ]
    mock_flow_config.get_phase_config = lambda name: next(
        (p for p in mock_flow_config.phases if p.name == name), None
    )
    mock_flow_config.get_next_phase = lambda last: (
        "phase2" if last == "phase1" else None
    )

    mock_registry.is_registered.return_value = True
    mock_registry.get_flow_config.return_value = mock_flow_config

    return mock_registry


@pytest.fixture
def mock_master_repo():
    """Mock CrewAI flow state extensions repository"""
    mock_repo = AsyncMock()

    # Mock master flow record
    mock_flow = Mock(spec=CrewAIFlowStateExtensions)
    mock_flow.flow_id = uuid.uuid4()
    mock_flow.flow_type = "discovery"
    mock_flow.flow_name = "Test Flow"
    mock_flow.flow_status = "initialized"
    mock_flow.flow_configuration = {}
    mock_flow.flow_persistence_data = {}
    mock_flow.phase_execution_times = {}
    mock_flow.agent_collaboration_log = []
    mock_flow.created_at = datetime.utcnow()
    mock_flow.updated_at = datetime.utcnow()
    mock_flow.to_dict = lambda: {
        "flow_id": str(mock_flow.flow_id),
        "flow_type": mock_flow.flow_type,
        "flow_status": mock_flow.flow_status,
    }
    mock_flow.get_performance_summary = lambda: {"total_phases": 0}
    mock_flow.update_phase_execution_time = Mock()

    mock_repo.create_master_flow.return_value = mock_flow
    mock_repo.get_by_flow_id.return_value = mock_flow
    mock_repo.update_flow_status.return_value = mock_flow
    mock_repo.get_active_flows.return_value = [mock_flow]
    mock_repo.get_flows_by_type.return_value = [mock_flow]
    mock_repo.delete_master_flow.return_value = True

    return mock_repo


@pytest.fixture
def orchestrator(mock_db, test_context, mock_flow_registry, mock_master_repo):
    """Create orchestrator with mocked dependencies"""
    with patch(
        "app.services.master_flow_orchestrator.FlowTypeRegistry",
        return_value=mock_flow_registry,
    ):
        with patch(
            "app.services.master_flow_orchestrator.CrewAIFlowStateExtensionsRepository",
            return_value=mock_master_repo,
        ):
            orchestrator = MasterFlowOrchestrator(mock_db, test_context)
            orchestrator.flow_registry = mock_flow_registry
            orchestrator.master_repo = mock_master_repo
            return orchestrator


class TestMasterFlowOrchestrator:
    """Test cases for Master Flow Orchestrator"""

    @pytest.mark.asyncio
    async def test_create_flow_success(self, orchestrator, mock_master_repo):
        """Test successful flow creation"""
        # Act
        flow_id, flow_details = await orchestrator.create_flow(
            flow_type="discovery",
            flow_name="Test Discovery Flow",
            configuration={"test": "config"},
            initial_state={"test": "state"},
        )

        # Assert
        assert flow_id is not None
        assert flow_details["flow_type"] == "discovery"
        assert flow_details["flow_status"] == "initialized"

        # Verify repository was called correctly
        mock_master_repo.create_master_flow.assert_called_once()
        call_args = mock_master_repo.create_master_flow.call_args[1]
        assert call_args["flow_type"] == "discovery"
        assert call_args["flow_name"] == "Test Discovery Flow"

    @pytest.mark.asyncio
    async def test_create_flow_invalid_type(self, orchestrator, mock_flow_registry):
        """Test flow creation with invalid type"""
        # Arrange
        mock_flow_registry.is_registered.return_value = False

        # Act & Assert
        with pytest.raises(ValueError, match="Unknown flow type"):
            await orchestrator.create_flow(flow_type="invalid_type")

    @pytest.mark.asyncio
    async def test_execute_phase_success(self, orchestrator, mock_master_repo):
        """Test successful phase execution"""
        # Act
        result = await orchestrator.execute_phase(
            flow_id=str(uuid.uuid4()),
            phase_name="phase1",
            phase_input={"test": "input"},
        )

        # Assert
        assert result["phase"] == "phase1"
        assert result["status"] == "completed"
        assert "execution_time_ms" in result
        assert result["results"]["crew_results"]["phase"] == "phase1"

        # Verify flow status was updated
        assert mock_master_repo.update_flow_status.call_count >= 2  # Start and complete

    @pytest.mark.asyncio
    async def test_execute_phase_flow_not_found(self, orchestrator, mock_master_repo):
        """Test phase execution when flow not found"""
        # Arrange
        mock_master_repo.get_by_flow_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Flow not found"):
            await orchestrator.execute_phase(
                flow_id=str(uuid.uuid4()), phase_name="phase1"
            )

    @pytest.mark.asyncio
    async def test_execute_phase_invalid_status(self, orchestrator, mock_master_repo):
        """Test phase execution with invalid flow status"""
        # Arrange
        mock_flow = mock_master_repo.get_by_flow_id.return_value
        mock_flow.flow_status = "deleted"

        # Act & Assert
        with pytest.raises(RuntimeError, match="Cannot execute phase in status"):
            await orchestrator.execute_phase(
                flow_id=str(uuid.uuid4()), phase_name="phase1"
            )

    @pytest.mark.asyncio
    async def test_pause_flow_success(self, orchestrator, mock_master_repo):
        """Test successful flow pause"""
        # Arrange
        mock_flow = mock_master_repo.get_by_flow_id.return_value
        mock_flow.flow_status = "running"

        # Act
        result = await orchestrator.pause_flow(
            flow_id=str(uuid.uuid4()), reason="User requested pause"
        )

        # Assert
        assert result["status"] == "paused"
        assert result["reason"] == "User requested pause"
        assert "paused_at" in result

        # Verify status was updated
        mock_master_repo.update_flow_status.assert_called_once()
        call_args = mock_master_repo.update_flow_status.call_args[1]
        assert call_args["status"] == "paused"

    @pytest.mark.asyncio
    async def test_pause_flow_invalid_status(self, orchestrator, mock_master_repo):
        """Test pausing flow with invalid status"""
        # Arrange
        mock_flow = mock_master_repo.get_by_flow_id.return_value
        mock_flow.flow_status = "completed"

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot pause flow in status"):
            await orchestrator.pause_flow(flow_id=str(uuid.uuid4()))

    @pytest.mark.asyncio
    async def test_resume_flow_success(self, orchestrator, mock_master_repo):
        """Test successful flow resume"""
        # Arrange
        mock_flow = mock_master_repo.get_by_flow_id.return_value
        mock_flow.flow_status = "paused"
        mock_flow.flow_persistence_data = {"last_completed_phase": "phase1"}

        # Act
        result = await orchestrator.resume_flow(
            flow_id=str(uuid.uuid4()), resume_context={"test": "context"}
        )

        # Assert
        assert result["status"] == "resumed"
        assert result["resume_phase"] == "phase2"
        assert "resumed_at" in result

        # Verify status was updated
        mock_master_repo.update_flow_status.assert_called_once()
        call_args = mock_master_repo.update_flow_status.call_args[1]
        assert call_args["status"] == "resumed"

    @pytest.mark.asyncio
    async def test_delete_flow_soft_delete(self, orchestrator, mock_master_repo):
        """Test soft delete flow"""
        # Act
        result = await orchestrator.delete_flow(
            flow_id=str(uuid.uuid4()), soft_delete=True, reason="No longer needed"
        )

        # Assert
        assert result["deleted"] is True
        assert result["soft_delete"] is True
        assert "deleted_at" in result

        # Verify soft delete was performed
        mock_master_repo.update_flow_status.assert_called_once()
        call_args = mock_master_repo.update_flow_status.call_args[1]
        assert call_args["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_delete_flow_hard_delete(self, orchestrator, mock_master_repo):
        """Test hard delete flow"""
        # Act
        result = await orchestrator.delete_flow(
            flow_id=str(uuid.uuid4()), soft_delete=False
        )

        # Assert
        assert result["deleted"] is True
        assert result["soft_delete"] is False

        # Verify hard delete was performed
        mock_master_repo.delete_master_flow.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_flow_status_with_details(self, orchestrator, mock_master_repo):
        """Test getting flow status with details"""
        # Act
        status = await orchestrator.get_flow_status(
            flow_id=str(uuid.uuid4()), include_details=True
        )

        # Assert
        assert status["flow_type"] == "discovery"
        assert status["flow_status"] == "initialized"
        assert "configuration" in status
        assert "phases" in status
        assert "performance" in status
        assert "collaboration_log" in status

    @pytest.mark.asyncio
    async def test_get_flow_status_without_details(
        self, orchestrator, mock_master_repo
    ):
        """Test getting flow status without details"""
        # Act
        status = await orchestrator.get_flow_status(
            flow_id=str(uuid.uuid4()), include_details=False
        )

        # Assert
        assert status["flow_type"] == "discovery"
        assert status["flow_status"] == "initialized"
        assert "configuration" not in status
        assert "phases" not in status

    @pytest.mark.asyncio
    async def test_get_active_flows_all_types(self, orchestrator, mock_master_repo):
        """Test getting active flows of all types"""
        # Act
        flows = await orchestrator.get_active_flows(limit=5)

        # Assert
        assert len(flows) == 1
        assert flows[0]["flow_type"] == "discovery"

        # Verify repository was called correctly
        mock_master_repo.get_active_flows.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_get_active_flows_by_type(self, orchestrator, mock_master_repo):
        """Test getting active flows by type"""
        # Act
        flows = await orchestrator.get_active_flows(flow_type="discovery", limit=10)

        # Assert
        assert len(flows) == 1
        assert flows[0]["flow_type"] == "discovery"

        # Verify repository was called correctly
        mock_master_repo.get_flows_by_type.assert_called_once_with("discovery", 10)

    @pytest.mark.asyncio
    async def test_error_handling_with_retry(self, orchestrator, mock_master_repo):
        """Test error handling with retry logic"""
        # Arrange
        mock_master_repo.create_master_flow.side_effect = [
            RuntimeError("Temporary error"),
            mock_master_repo.create_master_flow.return_value,
        ]

        # Mock error handler to allow retry
        with patch.object(
            orchestrator.error_handler, "handle_error"
        ) as mock_error_handler:
            mock_error_handler.return_value = AsyncMock(
                should_retry=True, retry_delay=0.01  # Short delay for testing
            )

            # Act
            flow_id, flow_details = await orchestrator.create_flow(
                flow_type="discovery"
            )

            # Assert
            assert flow_id is not None
            mock_error_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_audit_logging(self, orchestrator):
        """Test audit logging functionality"""
        # Arrange
        with patch.object(orchestrator, "_log_audit_event") as mock_audit:
            # Act
            await orchestrator.create_flow(flow_type="discovery")

            # Assert
            mock_audit.assert_called()
            call_args = mock_audit.call_args[1]
            assert call_args["operation"] == FlowOperationType.CREATE
            assert call_args["success"] is True

    @pytest.mark.asyncio
    async def test_performance_tracking(self, orchestrator):
        """Test performance tracking"""
        # Arrange
        with patch.object(
            orchestrator.performance_tracker, "start_operation"
        ) as mock_start:
            with patch.object(
                orchestrator.performance_tracker, "end_operation"
            ) as mock_end:
                mock_start.return_value = "tracking-id-123"

                # Act
                await orchestrator.create_flow(flow_type="discovery")

                # Assert
                mock_start.assert_called_once()
                mock_end.assert_called_once_with(
                    "tracking-id-123",
                    success=True,
                    result_metadata={"flow_id": Mock.ANY},
                )

    @pytest.mark.asyncio
    async def test_phase_validation(self, orchestrator):
        """Test phase validation"""
        # Arrange
        mock_validator = AsyncMock(
            return_value={
                "valid": False,
                "errors": ["Missing required field"],
                "warnings": [],
            }
        )

        with patch.object(
            orchestrator.validator_registry,
            "get_validator",
            return_value=mock_validator,
        ):
            # Update phase config to include validator
            phase_config = orchestrator.flow_registry.get_flow_config(
                "discovery"
            ).phases[0]
            phase_config.validators = ["test_validator"]

            # Act & Assert
            with pytest.raises(ValueError, match="Phase validation failed"):
                await orchestrator.execute_phase(
                    flow_id=str(uuid.uuid4()), phase_name="phase1"
                )

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self, orchestrator, test_context):
        """Test multi-tenant isolation is enforced"""
        # Assert context is properly set
        assert orchestrator.context.client_account_id == test_context.client_account_id
        assert orchestrator.context.engagement_id == test_context.engagement_id
        assert orchestrator.context.user_id == test_context.user_id

        # Verify repository was initialized with correct context
        assert (
            orchestrator.master_repo.client_account_id == test_context.client_account_id
        )
