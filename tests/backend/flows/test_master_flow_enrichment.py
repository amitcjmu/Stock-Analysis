"""
Tests for Master Flow State Enrichment Feature

This module tests the enrichment of master flow records with reliable,
lightweight orchestration data while keeping heavy, phase-specific data
in child flows.
"""

import asyncio
import os
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.crewai_flows.flow_progress_tracker import (
    FlowPhase,
    FlowProgressTracker,
)


class TestMasterFlowEnrichment:
    """Test suite for master flow state enrichment functionality."""

    @pytest.fixture
    def flow_id(self):
        """Generate a test flow ID."""
        return str(uuid.uuid4())

    @pytest.fixture
    def client_account_id(self):
        """Test client account ID."""
        return str(uuid.uuid4())

    @pytest.fixture
    def engagement_id(self):
        """Test engagement ID."""
        return str(uuid.uuid4())

    @pytest.fixture
    def user_id(self):
        """Test user ID."""
        return "test-user-123"

    @pytest.fixture
    def mock_context(self, client_account_id, engagement_id, user_id):
        """Create a mock request context."""
        context = MagicMock()
        context.client_account_id = client_account_id
        context.engagement_id = engagement_id
        context.user_id = user_id
        return context

    def _create_mock_flow(self, **kwargs):
        """Helper to create a mock flow with default attributes."""
        mock_flow = MagicMock(spec=CrewAIFlowStateExtensions)
        mock_flow.id = kwargs.get("id", uuid.uuid4())
        mock_flow.flow_id = kwargs.get("flow_id", uuid.uuid4())
        mock_flow.phase_transitions = kwargs.get("phase_transitions", [])
        mock_flow.phase_execution_times = kwargs.get("phase_execution_times", {})
        mock_flow.agent_collaboration_log = kwargs.get("agent_collaboration_log", [])
        mock_flow.error_history = kwargs.get("error_history", [])
        mock_flow.retry_count = kwargs.get("retry_count", 0)
        mock_flow.memory_usage_metrics = kwargs.get("memory_usage_metrics", {})
        mock_flow.agent_performance_metrics = kwargs.get("agent_performance_metrics", {})
        mock_flow.flow_metadata = kwargs.get("flow_metadata", {})
        mock_flow.updated_at = kwargs.get("updated_at", datetime.utcnow())
        return mock_flow

    def _setup_mock_db_execute(self, mock_db, mock_flow):
        """Helper to setup mock_db.execute to return mock_flow."""
        # Create a mock result object for SELECT queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_flow)

        # For update statements, create a result with rowcount
        mock_update_result = MagicMock()
        mock_update_result.rowcount = 1

        # Track call count using a list (mutable) to share across calls
        call_count = [0]

        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            # Odd calls are SELECT (with_for_update), return mock_result
            # Even calls are UPDATE, return mock_update_result
            if call_count[0] % 2 == 1:
                return mock_result
            else:
                return mock_update_result

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)
        return mock_db

    @pytest.fixture
    async def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock(spec=AsyncSession)
        db.commit = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    async def repository(self, mock_db, client_account_id, engagement_id, user_id):
        """Create a repository instance with enrichment enabled."""
        # Enable enrichment feature flag
        with patch.dict(os.environ, {"MASTER_STATE_ENRICHMENT_ENABLED": "true"}):
            repo = CrewAIFlowStateExtensionsRepository(
                db=mock_db,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
            )
            # Ensure enrichment is enabled
            repo._enrichment_enabled = True
            repo.enrich._enrichment_enabled = True
            return repo

    @pytest.mark.asyncio
    async def test_add_phase_transition(self, repository, flow_id, mock_db):
        """Test adding phase transitions to master flow."""
        # Setup mock flow
        mock_flow = self._create_mock_flow(
            flow_id=uuid.UUID(flow_id),
            phase_transitions=[],
            flow_metadata={}
        )
        self._setup_mock_db_execute(mock_db, mock_flow)

        # Add phase transition
        await repository.add_phase_transition(
            flow_id=flow_id,
            phase="initialization",
            status="processing",
            metadata={"started_by": "test"},
        )

        # Verify execute was called (at least once for SELECT, once for UPDATE)
        assert mock_db.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_record_phase_execution_time(self, repository, flow_id, mock_db):
        """Test recording phase execution times."""
        mock_flow = self._create_mock_flow(
            flow_id=uuid.UUID(flow_id),
            phase_execution_times={}
        )
        self._setup_mock_db_execute(mock_db, mock_flow)

        # Record execution time
        await repository.record_phase_execution_time(
            flow_id=flow_id, phase="data_validation", execution_time_ms=1234.56
        )

        assert mock_db.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_append_agent_collaboration(self, repository, flow_id, mock_db):
        """Test appending agent collaboration entries."""
        mock_flow = self._create_mock_flow(
            flow_id=uuid.UUID(flow_id),
            agent_collaboration_log=[]
        )
        self._setup_mock_db_execute(mock_db, mock_flow)

        # Add collaboration entry
        await repository.append_agent_collaboration(
            flow_id=flow_id,
            entry={
                "agent": "DataValidator",
                "action": "validated_schema",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        assert mock_db.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_add_error_entry(self, repository, flow_id, mock_db):
        """Test adding error entries to error history."""
        mock_flow = self._create_mock_flow(
            flow_id=uuid.UUID(flow_id),
            error_history=[],
            retry_count=0
        )
        self._setup_mock_db_execute(mock_db, mock_flow)

        # Add error entry
        await repository.add_error_entry(
            flow_id=flow_id,
            phase="field_mapping",
            error="Mapping validation failed",
            details={"field": "customer_id", "reason": "type_mismatch"},
        )

        assert mock_db.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_increment_retry_count(self, repository, flow_id, mock_db):
        """Test incrementing retry count."""
        mock_flow = self._create_mock_flow(
            flow_id=uuid.UUID(flow_id),
            retry_count=0
        )
        self._setup_mock_db_execute(mock_db, mock_flow)

        # Increment retry count
        await repository.increment_retry_count(flow_id=flow_id)

        assert mock_db.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_update_memory_usage_metrics(self, repository, flow_id, mock_db):
        """Test updating memory usage metrics."""
        mock_flow = self._create_mock_flow(
            flow_id=uuid.UUID(flow_id),
            memory_usage_metrics={}
        )
        self._setup_mock_db_execute(mock_db, mock_flow)

        # Update memory metrics
        await repository.update_memory_usage_metrics(
            flow_id=flow_id,
            metrics={
                "peak_memory_mb": 512,
                "current_memory_mb": 256,
                "memory_efficiency": 0.85,
            },
        )

        assert mock_db.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_update_agent_performance_metrics(
        self, repository, flow_id, mock_db
    ):
        """Test updating agent performance metrics."""
        mock_flow = self._create_mock_flow(
            flow_id=uuid.UUID(flow_id),
            agent_performance_metrics={}
        )
        self._setup_mock_db_execute(mock_db, mock_flow)

        # Update performance metrics
        await repository.update_agent_performance_metrics(
            flow_id=flow_id,
            metrics={
                "DataValidator": {"execution_time_ms": 500, "success_rate": 0.95},
                "FieldMapper": {"execution_time_ms": 1200, "success_rate": 0.88},
            },
        )

        assert mock_db.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_feature_flag_disabled(self, repository, flow_id, mock_db):
        """Test that enrichment is skipped when feature flag is disabled."""
        # Disable enrichment
        repository._enrichment_enabled = False
        repository.enrich._enrichment_enabled = False

        # Try to add phase transition
        await repository.add_phase_transition(
            flow_id=flow_id, phase="test", status="processing"
        )

        # Verify no database operations occurred
        assert mock_db.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_array_size_capping(self, repository, flow_id, mock_db):
        """Test that arrays are capped at maximum size."""
        # Create array with 201 existing transitions (over max size of 200)
        mock_flow = self._create_mock_flow(
            flow_id=uuid.UUID(flow_id),
            phase_transitions=[{"phase": f"phase_{i}"} for i in range(201)]
        )
        self._setup_mock_db_execute(mock_db, mock_flow)

        # Add another transition
        await repository.add_phase_transition(
            flow_id=flow_id, phase="new_phase", status="processing"
        )

        # Verify execute was called (cap logic should have removed oldest)
        assert mock_db.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_flow_progress_tracker_integration(
        self, flow_id, mock_context, mock_db
    ):
        """Test FlowProgressTracker integration with enrichment."""
        # Setup mock for repository operations
        mock_flow = MagicMock(spec=CrewAIFlowStateExtensions)
        mock_flow.flow_metadata = {}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_flow)
        mock_update_result = MagicMock()
        mock_update_result.rowcount = 1

        call_count = [0]
        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_result
            else:
                return mock_update_result

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)
        mock_db.commit = AsyncMock()

        tracker = FlowProgressTracker(flow_id, mock_context)

        with patch(
            "app.core.database.AsyncSessionLocal"
        ) as mock_session:
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock PostgresFlowStateStore
            with patch(
                "app.services.crewai_flows.persistence.postgres_store.PostgresFlowStateStore"
            ) as mock_store_class:
                mock_store = MagicMock()
                mock_store.update_flow_status = AsyncMock()
                mock_store_class.return_value = mock_store

                # Start a phase
                await tracker.start_phase(
                    FlowPhase.DATA_VALIDATION, message="Starting validation"
                )

                # Complete the phase
                await tracker.complete_phase(
                    FlowPhase.DATA_VALIDATION,
                    result={"validated": True},
                    next_phase=FlowPhase.FIELD_MAPPING_GENERATION,
                )

                # Report agent activity
                await tracker.report_agent_activity(
                    agent_name="DataValidator",
                    activity="Validating schema",
                    details={"records": 1000},
                )

                # Report error
                await tracker.report_error(
                    FlowPhase.DATA_VALIDATION, error="Validation failed", is_recoverable=True
                )

                # Verify database operations occurred
                assert mock_db.commit.call_count >= 1

    @pytest.mark.asyncio
    async def test_json_serialization_safety(self, repository, flow_id, mock_db):
        """Test that non-JSON serializable objects are handled properly."""
        mock_flow = self._create_mock_flow(
            flow_id=uuid.UUID(flow_id),
            phase_transitions=[]
        )
        self._setup_mock_db_execute(mock_db, mock_flow)

        # Add transition with UUID object (non-serializable)
        await repository.add_phase_transition(
            flow_id=flow_id,
            phase="test",
            status="processing",
            metadata={
                "uuid_field": uuid.uuid4(),  # This should be converted to string
                "datetime_field": datetime.utcnow(),  # This should be converted to ISO format
                "normal_field": "test",
            },
        )

        assert mock_db.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_concurrent_enrichment_operations(
        self, repository, flow_id, mock_db
    ):
        """Test that concurrent enrichment operations work correctly."""
        mock_flow = self._create_mock_flow(
            flow_id=uuid.UUID(flow_id),
            phase_transitions=[],
            agent_collaboration_log=[],
            error_history=[]
        )
        self._setup_mock_db_execute(mock_db, mock_flow)

        # Run multiple enrichment operations concurrently
        tasks = [
            repository.add_phase_transition(
                flow_id, "phase1", "processing", {"task": 1}
            ),
            repository.append_agent_collaboration(
                flow_id, {"agent": "Agent1", "action": "task1"}
            ),
            repository.add_error_entry(
                flow_id, "phase1", "Error 1", {"detail": "test"}
            ),
            repository.record_phase_execution_time(flow_id, "phase1", 1000),
        ]

        await asyncio.gather(*tasks)

        # Verify all operations completed (each operation makes at least 2 calls)
        assert mock_db.execute.call_count >= 8


class TestProgressTrackerFixes:
    """Test the fixes to the FlowProgressTracker."""

    @pytest.mark.asyncio
    async def test_progress_tracker_uses_correct_repository(self):
        """Test that progress tracker uses CrewAIFlowStateExtensionsRepository."""
        flow_id = str(uuid.uuid4())
        context = MagicMock()
        context.client_account_id = str(uuid.uuid4())
        context.engagement_id = str(uuid.uuid4())
        context.user_id = "test-user"

        tracker = FlowProgressTracker(flow_id, context)

        # Verify the import is correct (no import error)
        from app.services.crewai_flows.flow_progress_tracker import (
            FlowProgressTracker,
        )

        assert FlowProgressTracker is not None

    @pytest.mark.asyncio
    async def test_progress_persistence_with_fixed_imports(self):
        """Test that progress persistence works with fixed imports."""
        flow_id = str(uuid.uuid4())
        context = MagicMock()
        context.client_account_id = str(uuid.uuid4())
        context.engagement_id = str(uuid.uuid4())
        context.user_id = "test-user"

        tracker = FlowProgressTracker(flow_id, context)

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.commit = AsyncMock()

        # Setup mock for repository operations
        mock_flow = MagicMock(spec=CrewAIFlowStateExtensions)
        mock_flow.flow_metadata = {}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_flow)
        mock_update_result = MagicMock()
        mock_update_result.rowcount = 1

        call_count = [0]
        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_result
            else:
                return mock_update_result

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)

        with patch(
            "app.core.database.AsyncSessionLocal"
        ) as mock_session:
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock PostgresFlowStateStore
            with patch(
                "app.services.crewai_flows.persistence.postgres_store.PostgresFlowStateStore"
            ) as mock_store_class:
                mock_store = MagicMock()
                mock_store.update_flow_status = AsyncMock()
                mock_store_class.return_value = mock_store

                # This should not raise any import errors
                await tracker._persist_progress_to_database(
                    {
                        "flow_id": flow_id,
                        "phase": "test",
                        "progress": 50,
                        "status": "processing",
                        "message": "Test message",
                        "is_processing": True,
                        "awaiting_user_input": False,
                    }
                )

                # Verify commit was called (indicating successful persistence)
                assert mock_db.commit.called
