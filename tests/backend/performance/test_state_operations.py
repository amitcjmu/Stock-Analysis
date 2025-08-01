"""
Performance tests for state operations
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.crewai_flows.persistence.postgres_store import (
    ConcurrentModificationError,
    PostgresFlowStateStore,
)


@pytest.fixture
def test_context():
    """Test context for state operations"""
    return {
        "client_account_id": "test-client-123",
        "engagement_id": "test-engagement-456",
        "user_id": "test-user-789",
    }


@pytest.fixture
def small_state():
    """Small state object for basic performance tests"""
    return {
        "flow_id": "test-flow-123",
        "current_phase": "attribute_mapping",
        "progress": 45.5,
        "metadata": {
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T01:00:00Z",
        },
    }


@pytest.fixture
def large_state():
    """Large state object for performance testing"""
    # Create a state with substantial data
    state = {
        "flow_id": "test-flow-large",
        "current_phase": "data_cleansing",
        "progress": 67.8,
        "field_mappings": {},
        "raw_data": [],
        "analysis_results": {},
        "agent_outputs": {},
        "metadata": {
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T02:30:00Z",
            "total_records": 10000,
        },
    }

    # Add 1000 field mappings
    for i in range(1000):
        state["field_mappings"][f"field_{i}"] = {
            "source_column": f"source_field_{i}",
            "target_field": f"target_field_{i}",
            "confidence": 85.5 + (i % 15),
            "validation_status": "pending",
            "sample_values": [f"value_{j}" for j in range(10)],
        }

    # Add 5000 raw data records
    for i in range(5000):
        state["raw_data"].append(
            {
                "record_id": f"record_{i}",
                "hostname": f"server_{i:04d}",
                "ip_address": f"192.168.{i//256}.{i%256}",
                "os_type": "Linux" if i % 2 == 0 else "Windows",
                "cpu_cores": 4 + (i % 16),
                "memory_gb": 8 + (i % 32),
                "disk_gb": 100 + (i % 500),
            }
        )

    # Add analysis results for each phase
    phases = [
        "initialization",
        "attribute_mapping",
        "data_cleansing",
        "inventory_building",
    ]
    for phase in phases:
        state["analysis_results"][phase] = {
            "status": "completed",
            "duration_seconds": 45.5 + (hash(phase) % 60),
            "quality_score": 78.5 + (hash(phase) % 20),
            "findings": [f"Finding {i} for {phase}" for i in range(50)],
        }

    # Add agent outputs
    agents = ["data_analyst", "mapping_specialist", "quality_inspector"]
    for agent in agents:
        state["agent_outputs"][agent] = {
            "recommendations": [f"Recommendation {i} from {agent}" for i in range(100)],
            "confidence_scores": [85.0 + (i % 15) for i in range(100)],
            "processing_time": 23.4 + (hash(agent) % 30),
        }

    return state


@pytest.fixture
async def mock_db_session():
    """Create mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = AsyncMock()
    session.merge = AsyncMock()
    session.refresh = AsyncMock()
    return session


class TestStatePerformance:
    """Ensure state operations meet performance requirements"""

    @pytest.mark.asyncio
    async def test_small_state_save_performance(
        self, mock_db_session, test_context, small_state
    ):
        """Small state save should complete in <10ms"""
        store = PostgresFlowStateStore(mock_db_session, test_context)

        start = time.perf_counter()
        await store.save_state("test-flow-123", small_state, "attribute_mapping")
        duration = (time.perf_counter() - start) * 1000

        assert duration < 10, f"Small state save took {duration:.2f}ms, expected <10ms"
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_large_state_save_performance(
        self, mock_db_session, test_context, large_state
    ):
        """Large state save should complete in <50ms"""
        store = PostgresFlowStateStore(mock_db_session, test_context)

        start = time.perf_counter()
        await store.save_state("test-flow-large", large_state, "data_cleansing")
        duration = (time.perf_counter() - start) * 1000

        assert duration < 50, f"Large state save took {duration:.2f}ms, expected <50ms"
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_state_load_performance(
        self, mock_db_session, test_context, large_state
    ):
        """State load should complete in <30ms"""
        store = PostgresFlowStateStore(mock_db_session, test_context)

        # Mock database result
        mock_state_record = MagicMock()
        mock_state_record.state_data = json.dumps(large_state)
        mock_state_record.version = 1
        mock_state_record.phase = "data_cleansing"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_state_record
        mock_db_session.execute.return_value = mock_result

        start = time.perf_counter()
        loaded_state = await store.load_state("test-flow-large")
        duration = (time.perf_counter() - start) * 1000

        assert duration < 30, f"State load took {duration:.2f}ms, expected <30ms"
        assert loaded_state is not None
        assert loaded_state["flow_id"] == "test-flow-large"

    @pytest.mark.asyncio
    async def test_concurrent_state_updates(
        self, mock_db_session, test_context, small_state
    ):
        """Test optimistic locking prevents conflicts"""
        store = PostgresFlowStateStore(mock_db_session, test_context)

        # Mock version conflict on second update
        call_count = 0

        def mock_commit_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ConcurrentModificationError(
                    "State was modified by another process"
                )

        mock_db_session.commit.side_effect = mock_commit_side_effect

        # First update should succeed
        await store.save_state("test-flow-123", small_state, "attribute_mapping")

        # Second update should raise ConcurrentModificationError
        with pytest.raises(ConcurrentModificationError):
            await store.save_state("test-flow-123", small_state, "attribute_mapping")

        assert mock_db_session.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_bulk_state_operations_performance(
        self, mock_db_session, test_context
    ):
        """Test performance of bulk state operations"""
        store = PostgresFlowStateStore(mock_db_session, test_context)

        # Create 100 small states for bulk testing
        flow_states = []
        for i in range(100):
            state = {
                "flow_id": f"test-flow-{i}",
                "current_phase": "attribute_mapping",
                "progress": i % 100,
                "metadata": {"created_at": "2024-01-01T00:00:00Z"},
            }
            flow_states.append((f"test-flow-{i}", state, "attribute_mapping"))

        start = time.perf_counter()

        # Save all states concurrently
        tasks = [
            store.save_state(flow_id, state, phase)
            for flow_id, state, phase in flow_states
        ]
        await asyncio.gather(*tasks)

        duration = (time.perf_counter() - start) * 1000

        # Should complete 100 operations in under 500ms
        assert duration < 500, f"Bulk state save took {duration:.2f}ms, expected <500ms"
        assert mock_db_session.commit.call_count == 100

    @pytest.mark.asyncio
    async def test_state_serialization_performance(self, large_state):
        """Test JSON serialization performance for large states"""

        start = time.perf_counter()
        serialized = json.dumps(large_state)
        serialize_duration = (time.perf_counter() - start) * 1000

        assert (
            serialize_duration < 20
        ), f"Serialization took {serialize_duration:.2f}ms, expected <20ms"

        start = time.perf_counter()
        deserialized = json.loads(serialized)
        deserialize_duration = (time.perf_counter() - start) * 1000

        assert (
            deserialize_duration < 20
        ), f"Deserialization took {deserialize_duration:.2f}ms, expected <20ms"
        assert deserialized == large_state

    @pytest.mark.asyncio
    async def test_memory_usage_large_state(
        self, mock_db_session, test_context, large_state
    ):
        """Test memory usage doesn't grow excessively with large states"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        store = PostgresFlowStateStore(mock_db_session, test_context)

        # Perform 50 state operations
        for i in range(50):
            modified_state = large_state.copy()
            modified_state["iteration"] = i
            await store.save_state(f"test-flow-{i}", modified_state, "data_cleansing")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (<100MB for this test)
        assert (
            memory_increase < 100
        ), f"Memory increased by {memory_increase:.2f}MB, expected <100MB"

    @pytest.mark.asyncio
    async def test_database_connection_efficiency(
        self, mock_db_session, test_context, small_state
    ):
        """Test database connection usage efficiency"""
        store = PostgresFlowStateStore(mock_db_session, test_context)

        # Track database operation calls
        operation_count = 0
        original_execute = mock_db_session.execute

        def track_execute(*args, **kwargs):
            nonlocal operation_count
            operation_count += 1
            return original_execute(*args, **kwargs)

        mock_db_session.execute.side_effect = track_execute

        # Perform multiple state operations
        for i in range(10):
            await store.save_state(f"test-flow-{i}", small_state, "attribute_mapping")

        # Should use minimal database operations (1 execute + 1 commit per save)
        expected_operations = 10  # One execute per save
        assert (
            operation_count <= expected_operations
        ), f"Used {operation_count} DB operations, expected ≤{expected_operations}"

    @pytest.mark.asyncio
    async def test_state_version_increment_performance(
        self, mock_db_session, test_context, small_state
    ):
        """Test version increment performance doesn't degrade"""
        store = PostgresFlowStateStore(mock_db_session, test_context)

        # Mock existing state with high version number
        mock_state_record = MagicMock()
        mock_state_record.version = 1000  # High version number
        mock_state_record.state_data = json.dumps(small_state)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_state_record
        mock_db_session.execute.return_value = mock_result

        start = time.perf_counter()
        await store.save_state("test-flow-123", small_state, "attribute_mapping")
        duration = (time.perf_counter() - start) * 1000

        # Performance should not degrade with high version numbers
        assert duration < 15, f"Version increment took {duration:.2f}ms, expected <15ms"

    @pytest.mark.asyncio
    async def test_concurrent_read_performance(
        self, mock_db_session, test_context, large_state
    ):
        """Test concurrent read operations don't block each other"""
        store = PostgresFlowStateStore(mock_db_session, test_context)

        # Mock state loading
        mock_state_record = MagicMock()
        mock_state_record.state_data = json.dumps(large_state)
        mock_state_record.version = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_state_record
        mock_db_session.execute.return_value = mock_result

        start = time.perf_counter()

        # Perform 20 concurrent reads
        tasks = [store.load_state("test-flow-large") for _ in range(20)]
        results = await asyncio.gather(*tasks)

        duration = (time.perf_counter() - start) * 1000

        # All reads should complete quickly
        assert (
            duration < 100
        ), f"20 concurrent reads took {duration:.2f}ms, expected <100ms"
        assert len(results) == 20
        assert all(result is not None for result in results)

    @pytest.mark.asyncio
    async def test_state_cleanup_performance(self, mock_db_session, test_context):
        """Test state cleanup operations are efficient"""
        store = PostgresFlowStateStore(mock_db_session, test_context)

        # Mock cleanup operation
        mock_result = MagicMock()
        mock_result.rowcount = 150  # Simulate cleaning up 150 old states
        mock_db_session.execute.return_value = mock_result

        start = time.perf_counter()

        # Simulate cleanup of states older than 30 days
        cutoff_date = "2024-01-01T00:00:00Z"
        await store.cleanup_old_states(cutoff_date)

        duration = (time.perf_counter() - start) * 1000

        # Cleanup should be fast even for many records
        assert duration < 50, f"Cleanup took {duration:.2f}ms, expected <50ms"
        mock_db_session.commit.assert_called_once()

    def test_state_size_limits(self, large_state):
        """Test state size stays within reasonable limits"""
        serialized = json.dumps(large_state)
        size_mb = len(serialized.encode("utf-8")) / 1024 / 1024

        # Large state should stay under 10MB when serialized
        assert size_mb < 10, f"State size is {size_mb:.2f}MB, expected <10MB"

        # Verify state contains expected amount of data
        assert len(large_state["field_mappings"]) == 1000
        assert len(large_state["raw_data"]) == 5000
        assert len(large_state["analysis_results"]) == 4
        assert len(large_state["agent_outputs"]) == 3
