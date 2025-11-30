"""
Test Utilities for Integration Tests

Provides BaseIntegrationTest class and monitoring fixtures.
"""

import asyncio
from typing import Dict

import pytest


@pytest.mark.asyncio
class BaseIntegrationTest:
    """Base class for integration tests with common utilities."""

    async def assert_workflow_completion(
        self,
        workflow_context,
        expected_phases: list = None,
        min_confidence: float = 0.0,
    ):
        """Assert workflow completed successfully."""
        assert workflow_context is not None
        assert workflow_context.engagement_id is not None

        if expected_phases:
            completed_phases = [
                entry["phase"]
                for entry in workflow_context.phase_history
                if entry["status"] == "completed"
            ]
            for phase in expected_phases:
                assert phase in completed_phases

        if min_confidence > 0:
            confidence = workflow_context.data_quality_metrics.get(
                "overall_confidence", 0.0
            )
            assert confidence >= min_confidence

    async def assert_validation_quality(
        self,
        validation_result,
        max_critical_issues: int = 0,
        min_overall_score: float = 0.7,
    ):
        """Assert validation meets quality standards."""
        assert validation_result is not None
        assert validation_result.overall_score >= min_overall_score

        critical_issues = [
            issue
            for issue in validation_result.issues
            if issue.severity.value == "critical"
        ]
        assert len(critical_issues) <= max_critical_issues

    async def assert_sync_health(self, sync_context, max_conflicts: int = 0):
        """Assert synchronization is healthy."""
        assert sync_context is not None
        assert len(sync_context.conflicts) <= max_conflicts

        # Check that flows are properly tracked
        if sync_context.flows:
            for flow_type, flow_state in sync_context.flows.items():
                assert flow_state.flow_id is not None
                assert flow_state.status is not None

    async def measure_performance(self, operation_func, max_duration: float = 30.0):
        """Measure and assert operation performance."""
        import time

        start_time = time.time()
        result = await operation_func()
        end_time = time.time()

        duration = end_time - start_time
        assert (
            duration <= max_duration
        ), f"Operation took {duration:.2f}s, max allowed: {max_duration}s"

        return result, duration


@pytest.fixture
def performance_monitor():
    """Performance monitoring utilities."""

    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {}

        async def time_operation(self, operation_name: str, operation_func):
            """Time an async operation."""
            import time

            start_time = time.time()
            result = await operation_func()
            end_time = time.time()

            duration = end_time - start_time
            self.metrics[operation_name] = duration

            return result, duration

        def get_metrics(self) -> Dict[str, float]:
            """Get collected performance metrics."""
            return self.metrics.copy()

        def assert_performance(
            self, operation_name: str, max_duration: float, message: str = None
        ):
            """Assert operation met performance requirements."""
            duration = self.metrics.get(operation_name)
            assert (
                duration is not None
            ), f"No metrics found for operation: {operation_name}"

            error_msg = (
                message
                or f"Operation {operation_name} took {duration:.2f}s, max: {max_duration}s"
            )
            assert duration <= max_duration, error_msg

    return PerformanceMonitor()


@pytest.fixture
def memory_monitor():
    """Memory usage monitoring utilities."""

    class MemoryMonitor:
        def __init__(self):
            self.snapshots = {}

        def take_snapshot(self, name: str):
            """Take memory usage snapshot."""
            import os

            import psutil

            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            self.snapshots[name] = {
                "rss": memory_info.rss,
                "vms": memory_info.vms,
                "timestamp": asyncio.get_event_loop().time(),
            }

        def get_memory_diff(
            self, start_snapshot: str, end_snapshot: str
        ) -> Dict[str, int]:
            """Get memory difference between snapshots."""
            start = self.snapshots.get(start_snapshot)
            end = self.snapshots.get(end_snapshot)

            assert start is not None, f"Start snapshot '{start_snapshot}' not found"
            assert end is not None, f"End snapshot '{end_snapshot}' not found"

            return {
                "rss_diff": end["rss"] - start["rss"],
                "vms_diff": end["vms"] - start["vms"],
                "duration": end["timestamp"] - start["timestamp"],
            }

        def assert_memory_usage(
            self,
            start_snapshot: str,
            end_snapshot: str,
            max_memory_increase: int = 50 * 1024 * 1024,  # 50MB
        ):
            """Assert memory usage stayed within bounds."""
            diff = self.get_memory_diff(start_snapshot, end_snapshot)

            assert diff["rss_diff"] <= max_memory_increase, (
                f"Memory increased by {diff['rss_diff'] / 1024 / 1024:.1f}MB, "
                f"max allowed: {max_memory_increase / 1024 / 1024:.1f}MB"
            )

    return MemoryMonitor()
