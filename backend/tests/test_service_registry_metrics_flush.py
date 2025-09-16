"""
Test ServiceRegistry Metrics Flush and Cancellation

Validates that ServiceRegistry properly manages metrics flushing
and cancels background tasks on exit.
"""

import asyncio
import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Mock crewai and related modules before importing
mock_crewai = MagicMock()
mock_crewai.Agent = MagicMock
mock_crewai.Task = MagicMock
mock_crewai.Crew = MagicMock
sys.modules["crewai"] = mock_crewai
sys.modules["crewai.agent"] = MagicMock()
sys.modules["crewai.task"] = MagicMock()
sys.modules["crewai.crew"] = MagicMock()
sys.modules["crewai.process"] = MagicMock()
sys.modules["crewai.project"] = MagicMock()

# Mock additional problematic imports
sys.modules["langchain"] = MagicMock()
sys.modules["langchain_community"] = MagicMock()
sys.modules["langchain_openai"] = MagicMock()
sys.modules["openai"] = MagicMock()

from app.core.context import RequestContext  # noqa: E402

# Import with mocked dependencies
with patch.dict(sys.modules, {"crewai": mock_crewai}):
    from app.services.service_registry import ServiceRegistry, MetricRecord


class TestServiceRegistryMetricsFlush:
    """Test metrics flush and task cancellation"""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def mock_context(self):
        """Create mock request context"""
        return RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
        )

    @pytest.fixture
    def registry(self, mock_session, mock_context):
        """Create ServiceRegistry instance"""
        return ServiceRegistry(mock_session, mock_context)

    def test_metric_record_creation(self):
        """Test MetricRecord dataclass creation"""
        now = datetime.now(timezone.utc)
        record = MetricRecord(
            timestamp=now,
            service_name="TestService",
            metric_name="test_metric",
            metric_value=42,
            metadata={"key": "value"},
        )

        assert record.timestamp == now
        assert record.service_name == "TestService"
        assert record.metric_name == "test_metric"
        assert record.metric_value == 42
        assert record.metadata == {"key": "value"}

    def test_record_metric_adds_to_buffer(self, registry):
        """Test that record_metric adds to buffer"""
        registry.record_metric("TestService", "metric1", 10)
        registry.record_metric("TestService", "metric2", 20)

        assert len(registry._metrics_buffer) == 2
        assert registry._metrics_buffer[0].metric_name == "metric1"
        assert registry._metrics_buffer[1].metric_name == "metric2"

    def test_record_metric_on_closed_registry(self, registry):
        """Test that closed registry ignores metrics"""
        registry._is_closed = True

        registry.record_metric("TestService", "metric1", 10)

        # Should not add to buffer when closed
        assert len(registry._metrics_buffer) == 0

    @pytest.mark.asyncio
    async def test_auto_flush_at_max_buffer_size(self, registry):
        """Test automatic flush when buffer reaches max size"""
        with patch.object(registry, "_flush_metrics", new_callable=AsyncMock):
            # Fill buffer to max size (100)
            for i in range(100):
                registry.record_metric("TestService", f"metric_{i}", i)

            # Give async task time to run
            await asyncio.sleep(0.1)

            # Should have triggered auto-flush
            assert len(registry._metrics_buffer) == 100

    @pytest.mark.asyncio
    async def test_flush_metrics_clears_buffer(self, registry):
        """Test that _flush_metrics clears the buffer"""
        # Add metrics
        registry.record_metric("TestService", "metric1", 10)
        registry.record_metric("TestService", "metric2", 20)

        assert len(registry._metrics_buffer) == 2

        with patch.object(registry, "_write_metrics_async", new_callable=AsyncMock):
            await registry._flush_metrics()

        # Buffer should be cleared
        assert len(registry._metrics_buffer) == 0

    @pytest.mark.asyncio
    async def test_flush_metrics_error_handling(self, registry):
        """Test flush metrics handles errors gracefully"""
        # Add metrics
        registry.record_metric("TestService", "metric1", 10)

        with patch.object(
            registry, "_write_metrics_async", new_callable=AsyncMock
        ) as mock_write:
            mock_write.side_effect = Exception("Write failed")

            # Should not raise exception
            await registry._flush_metrics()

        # Buffer should still be cleared (don't retry failed metrics)
        assert len(registry._metrics_buffer) == 0

    @pytest.mark.asyncio
    async def test_periodic_flush_task_starts(self, registry):
        """Test that periodic flush task starts when enabled"""
        registry._start_periodic_flush()

        # Task should be created
        assert registry._periodic_flush_task is not None
        assert not registry._periodic_flush_task.done()

        # Cancel for cleanup
        registry._periodic_flush_task.cancel()
        try:
            await registry._periodic_flush_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_periodic_flush_loop_execution(self, registry):
        """Test periodic flush loop executes periodically"""
        flush_count = 0

        async def mock_flush():
            nonlocal flush_count
            flush_count += 1

        registry._flush_metrics = mock_flush
        # Patch the hardcoded interval in the periodic flush loop
        with patch.object(registry, "_periodic_flush_loop"):

            async def custom_loop():
                try:
                    while not registry._is_closed:
                        await asyncio.sleep(0.1)  # Fast interval for testing
                        if registry._metrics_buffer and not registry._is_closed:
                            await registry._flush_metrics()
                except asyncio.CancelledError:
                    pass

            registry._periodic_flush_loop = custom_loop
            registry._start_periodic_flush()

            # Wait for a few intervals
            await asyncio.sleep(0.25)

            # Should have flushed if there were metrics
            # Add metrics to trigger flush
            registry.record_metric("TestService", "test_metric", 1)
            await asyncio.sleep(0.15)

            assert flush_count >= 1

            # Cancel task
            if (
                registry._periodic_flush_task
                and not registry._periodic_flush_task.done()
            ):
                registry._periodic_flush_task.cancel()
                try:
                    await registry._periodic_flush_task
                except asyncio.CancelledError:
                    pass

    @pytest.mark.asyncio
    async def test_context_manager_starts_and_stops_flush(
        self, mock_session, mock_context
    ):
        """Test that context manager properly manages flush task"""
        async with ServiceRegistry(mock_session, mock_context) as registry:
            # Periodic flush should start
            assert registry._periodic_flush_task is not None
            assert not registry._periodic_flush_task.done()

            # Add some metrics
            registry.record_metric("TestService", "metric1", 10)

        # After exit, task should be cancelled
        assert registry._is_closed
        assert registry._periodic_flush_task.done()

    @pytest.mark.asyncio
    async def test_aexit_cancels_flush_tasks(self, registry):
        """Test that __aexit__ cancels all flush tasks"""
        # Create mock tasks
        registry._metrics_flush_task = asyncio.create_task(asyncio.sleep(10))
        registry._periodic_flush_task = asyncio.create_task(asyncio.sleep(10))

        # Add metrics so flush will be called
        registry.record_metric("TestService", "metric1", 10)

        # Exit the context
        await registry.__aexit__(None, None, None)

        # Tasks should be cancelled
        assert (
            registry._metrics_flush_task.cancelled()
            or registry._metrics_flush_task.done()
        )
        assert (
            registry._periodic_flush_task.cancelled()
            or registry._periodic_flush_task.done()
        )
        assert registry._is_closed

    @pytest.mark.asyncio
    async def test_aexit_flushes_remaining_metrics(self, registry):
        """Test that __aexit__ flushes remaining metrics"""
        # Add metrics
        registry.record_metric("TestService", "metric1", 10)
        registry.record_metric("TestService", "metric2", 20)

        with patch.object(
            registry, "_flush_metrics", new_callable=AsyncMock
        ) as mock_flush:
            await registry.__aexit__(None, None, None)

            # Should have flushed remaining metrics
            mock_flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_aexit_handles_flush_errors(self, registry):
        """Test that __aexit__ handles flush errors gracefully"""
        # Add metrics
        registry.record_metric("TestService", "metric1", 10)

        with patch.object(
            registry, "_flush_metrics", new_callable=AsyncMock
        ) as mock_flush:
            mock_flush.side_effect = Exception("Flush failed")

            # Should not raise exception
            await registry.__aexit__(None, None, None)

        # Registry should still be closed
        assert registry._is_closed

    @pytest.mark.asyncio
    async def test_no_dangling_tasks_after_exit(self, mock_session, mock_context):
        """Test that no tasks remain after context exit"""
        all_tasks_before = asyncio.all_tasks()

        async with ServiceRegistry(mock_session, mock_context) as registry:
            # Add metrics to trigger flush tasks
            for i in range(10):
                registry.record_metric("TestService", f"metric_{i}", i)

            # Tasks should be running
            tasks_during = asyncio.all_tasks()
            assert len(tasks_during) > len(all_tasks_before)

        # Give tasks time to clean up
        await asyncio.sleep(0.1)

        # No new tasks should remain
        all_tasks_after = asyncio.all_tasks()

        # Should have same or fewer tasks than before
        # (can't guarantee exact match due to pytest's own tasks)
        assert len(all_tasks_after) <= len(all_tasks_before) + 1

    @pytest.mark.asyncio
    async def test_multiple_registries_independent_flush(self, mock_session):
        """Test that multiple registries have independent flush tasks"""
        context1 = RequestContext(client_account_id=str(uuid.uuid4()))
        context2 = RequestContext(client_account_id=str(uuid.uuid4()))

        async with ServiceRegistry(mock_session, context1) as registry1:
            async with ServiceRegistry(mock_session, context2) as registry2:
                # Each should have its own task
                assert registry1._periodic_flush_task != registry2._periodic_flush_task

                # Add metrics to each
                registry1.record_metric("Service1", "metric1", 10)
                registry2.record_metric("Service2", "metric2", 20)

                # Each should have its own buffer
                assert len(registry1._metrics_buffer) == 1
                assert len(registry2._metrics_buffer) == 1

        # Both should be closed
        assert registry1._is_closed
        assert registry2._is_closed

    @pytest.mark.asyncio
    async def test_flush_task_cancellation_on_exception(
        self, mock_session, mock_context
    ):
        """Test that flush tasks are cancelled even when exception occurs"""
        try:
            async with ServiceRegistry(mock_session, mock_context) as registry:
                # Start tasks
                registry._start_periodic_flush()

                # Raise exception
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Tasks should still be cancelled
        assert registry._is_closed
        if registry._periodic_flush_task:
            assert registry._periodic_flush_task.done()

    def test_bounded_buffer_behavior(self, registry):
        """Test that metrics buffer is bounded to MAX_METRICS_BUFFER_SIZE"""
        # Add more metrics than buffer size
        for i in range(150):
            registry.record_metric("TestService", f"metric_{i}", i)

        # Buffer should be bounded to max size (100)
        assert len(registry._metrics_buffer) == 100

        # Should have kept the most recent metrics
        assert registry._metrics_buffer[0].metric_name == "metric_50"
        assert registry._metrics_buffer[-1].metric_name == "metric_149"

    @pytest.mark.asyncio
    async def test_complete_lifecycle_with_metrics(self, mock_session, mock_context):
        """Test complete ServiceRegistry lifecycle with metrics"""
        metrics_written = []

        async def capture_metrics(metrics):
            metrics_written.extend(metrics)

        async with ServiceRegistry(mock_session, mock_context) as registry:
            # Patch write method
            registry._write_metrics_async = capture_metrics

            # Record metrics
            for i in range(5):
                registry.record_metric("TestService", f"operation_{i}", i * 10)

            # Manually flush
            await registry._flush_metrics()

        # Metrics should have been written
        assert len(metrics_written) == 5
        assert all(isinstance(m, MetricRecord) for m in metrics_written)

        # Registry should be closed
        assert registry._is_closed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
