"""
Unit tests for PhaseExecutionLockManager

Tests the in-memory lock manager that prevents duplicate concurrent
assessment phase executions (Issue #999).
"""

import pytest
from datetime import datetime, timedelta

from app.services.flow_orchestration.phase_execution_lock_manager import (
    PhaseExecutionLockManager,
    phase_lock_manager,
)


class TestPhaseExecutionLockManager:
    """Test suite for PhaseExecutionLockManager."""

    @pytest.fixture
    def lock_manager(self):
        """Create a fresh lock manager instance for each test."""
        # Reset singleton state
        PhaseExecutionLockManager._locks.clear()
        PhaseExecutionLockManager._lock_timestamps.clear()
        return phase_lock_manager

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """Verify singleton pattern - only one instance exists."""
        manager1 = PhaseExecutionLockManager()
        manager2 = PhaseExecutionLockManager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_acquire_lock_success(self, lock_manager):
        """Test successful lock acquisition."""
        flow_id = "test-flow-123"
        phase = "readiness"

        result = await lock_manager.try_acquire_lock(flow_id, phase)
        assert result is True

        # Verify lock is actually acquired
        lock_key = (flow_id, phase)
        assert lock_key in lock_manager._locks
        assert lock_manager._locks[lock_key].locked()

    @pytest.mark.asyncio
    async def test_acquire_lock_already_locked(self, lock_manager):
        """Test lock rejection when already locked."""
        flow_id = "test-flow-123"
        phase = "readiness"

        # First acquisition succeeds
        result1 = await lock_manager.try_acquire_lock(flow_id, phase)
        assert result1 is True

        # Second acquisition fails (duplicate)
        result2 = await lock_manager.try_acquire_lock(flow_id, phase)
        assert result2 is False

    @pytest.mark.asyncio
    async def test_release_lock(self, lock_manager):
        """Test lock release."""
        flow_id = "test-flow-123"
        phase = "readiness"

        # Acquire lock
        await lock_manager.try_acquire_lock(flow_id, phase)

        # Release lock
        lock_manager.release_lock(flow_id, phase)

        # Verify lock is released
        lock_key = (flow_id, phase)
        assert not lock_manager._locks[lock_key].locked()

        # Should be able to acquire again
        result = await lock_manager.try_acquire_lock(flow_id, phase)
        assert result is True

    @pytest.mark.asyncio
    async def test_lock_granularity(self, lock_manager):
        """Test that locks are per-(flow_id, phase) combination."""
        flow_id = "test-flow-123"
        phase1 = "readiness"
        phase2 = "architecture"

        # Acquire lock for phase1
        result1 = await lock_manager.try_acquire_lock(flow_id, phase1)
        assert result1 is True

        # Should be able to acquire lock for different phase
        result2 = await lock_manager.try_acquire_lock(flow_id, phase2)
        assert result2 is True

        # Both locks should be held
        assert lock_manager._locks[(flow_id, phase1)].locked()
        assert lock_manager._locks[(flow_id, phase2)].locked()

    @pytest.mark.asyncio
    async def test_timeout_cleanup(self, lock_manager):
        """Test automatic timeout cleanup after 5 minutes."""
        flow_id = "test-flow-123"
        phase = "readiness"

        # Acquire lock
        await lock_manager.try_acquire_lock(flow_id, phase)

        # Simulate timeout by backdating timestamp
        lock_key = (flow_id, phase)
        old_timestamp = datetime.utcnow() - timedelta(minutes=6)
        lock_manager._lock_timestamps[lock_key] = old_timestamp

        # Try to acquire again - should succeed due to timeout cleanup
        result = await lock_manager.try_acquire_lock(flow_id, phase)
        assert result is True

    @pytest.mark.asyncio
    async def test_execute_with_lock_success(self, lock_manager):
        """Test execute_with_lock wrapper method."""
        flow_id = "test-flow-123"
        phase = "readiness"
        expected_result = {"status": "success", "data": "test"}

        async def mock_executor():
            return expected_result

        result = await lock_manager.execute_with_lock(flow_id, phase, mock_executor)

        assert result == expected_result
        # Lock should be released after execution
        lock_key = (flow_id, phase)
        assert not lock_manager._locks[lock_key].locked()

    @pytest.mark.asyncio
    async def test_execute_with_lock_already_locked(self, lock_manager):
        """Test execute_with_lock returns early if already locked."""
        flow_id = "test-flow-123"
        phase = "readiness"

        # Acquire lock manually
        await lock_manager.try_acquire_lock(flow_id, phase)

        async def mock_executor():
            return {"status": "success"}

        # Should return "already_running" without executing
        result = await lock_manager.execute_with_lock(flow_id, phase, mock_executor)

        assert result["status"] == "already_running"
        assert result["flow_id"] == flow_id
        assert result["phase"] == phase

    @pytest.mark.asyncio
    async def test_execute_with_lock_exception_handling(self, lock_manager):
        """Test lock is released even if executor raises exception."""
        flow_id = "test-flow-123"
        phase = "readiness"

        async def failing_executor():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await lock_manager.execute_with_lock(flow_id, phase, failing_executor)

        # Lock should be released despite exception
        lock_key = (flow_id, phase)
        assert not lock_manager._locks[lock_key].locked()

    @pytest.mark.asyncio
    async def test_concurrent_executions_different_flows(self, lock_manager):
        """Test that different flows can execute concurrently."""
        flow_id1 = "test-flow-123"
        flow_id2 = "test-flow-456"
        phase = "readiness"

        # Both should acquire successfully
        result1 = await lock_manager.try_acquire_lock(flow_id1, phase)
        result2 = await lock_manager.try_acquire_lock(flow_id2, phase)

        assert result1 is True
        assert result2 is True

    @pytest.mark.asyncio
    async def test_release_without_acquire(self, lock_manager):
        """Test release_lock is safe to call even if lock was never acquired."""
        flow_id = "test-flow-123"
        phase = "readiness"

        # Should not raise exception
        lock_manager.release_lock(flow_id, phase)

    @pytest.mark.asyncio
    async def test_timestamp_tracking(self, lock_manager):
        """Test that lock timestamps are correctly tracked."""
        flow_id = "test-flow-123"
        phase = "readiness"

        before_time = datetime.utcnow()
        await lock_manager.try_acquire_lock(flow_id, phase)
        after_time = datetime.utcnow()

        lock_key = (flow_id, phase)
        timestamp = lock_manager._lock_timestamps[lock_key]

        assert before_time <= timestamp <= after_time

    @pytest.mark.asyncio
    async def test_multiple_rapid_acquires(self, lock_manager):
        """Simulate rapid resume calls (Issue #999 scenario)."""
        flow_id = "test-flow-123"
        phase = "readiness"

        # Simulate 5 rapid resume calls
        results = []
        for _ in range(5):
            result = await lock_manager.try_acquire_lock(flow_id, phase)
            results.append(result)

        # Only first should succeed
        assert results[0] is True
        assert all(r is False for r in results[1:])
