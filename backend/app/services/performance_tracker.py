"""
Performance Tracker

Tracks and monitors performance metrics for all flow operations.
Provides insights into execution times, resource usage, and bottlenecks.
"""

import logging
import time

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OperationMetrics:
    """Metrics for a single operation"""

    operation_type: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    cpu_percent_start: Optional[float] = None
    cpu_percent_end: Optional[float] = None
    memory_mb_start: Optional[float] = None
    memory_mb_end: Optional[float] = None
    error: Optional[str] = None


@dataclass
class PerformanceStats:
    """Aggregated performance statistics"""

    operation_type: str
    total_count: int
    success_count: int
    failure_count: int
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p50_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    avg_cpu_delta: float
    avg_memory_delta_mb: float
    last_updated: datetime


class PerformanceTracker:
    """
    Tracks performance metrics for flow operations.
    Provides real-time and historical performance data.
    """

    def __init__(self, history_size: int = 1000):
        """
        Initialize performance tracker

        Args:
            history_size: Number of recent operations to keep in memory
        """
        # Active operations being tracked
        self._active_operations: Dict[str, OperationMetrics] = {}

        # Historical data (limited size deque for each operation type)
        self._history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=history_size)
        )

        # Aggregated statistics cache
        self._stats_cache: Dict[str, PerformanceStats] = {}
        self._stats_cache_ttl = 60  # seconds
        self._stats_cache_timestamps: Dict[str, float] = {}

        # Audit events
        self._audit_events: deque = deque(maxlen=history_size * 2)

        # Performance thresholds for alerting
        self._thresholds: Dict[str, Dict[str, float]] = {
            "flow_creation": {"duration_ms": 5000, "cpu_percent": 80},
            "phase_execution": {"duration_ms": 30000, "cpu_percent": 90},
            "status_check": {"duration_ms": 1000, "cpu_percent": 50},
        }

        # Resource monitoring
        if PSUTIL_AVAILABLE:
            self._process = psutil.Process()
        else:
            self._process = None

        logger.info(f"✅ Performance Tracker initialized (history_size={history_size})")

    def start_operation(
        self, operation_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking an operation

        Args:
            operation_type: Type of operation (e.g., 'flow_creation', 'phase_execution')
            metadata: Optional metadata about the operation

        Returns:
            Tracking ID for the operation
        """
        tracking_id = f"{operation_type}_{int(time.time() * 1000000)}"

        # Get current resource usage
        if self._process:
            cpu_percent = self._process.cpu_percent(interval=0.1)
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
        else:
            cpu_percent = None
            memory_mb = None

        self._active_operations[tracking_id] = OperationMetrics(
            operation_type=operation_type,
            start_time=time.time(),
            metadata=metadata or {},
            cpu_percent_start=cpu_percent,
            memory_mb_start=memory_mb,
        )

        logger.debug(f"📊 Started tracking: {tracking_id}")
        return tracking_id

    def end_operation(
        self,
        tracking_id: str,
        success: bool = True,
        error: Optional[str] = None,
        result_metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        End tracking an operation

        Args:
            tracking_id: The tracking ID returned by start_operation
            success: Whether the operation succeeded
            error: Optional error message if failed
            result_metadata: Optional result metadata
        """
        if tracking_id not in self._active_operations:
            logger.warning(f"Unknown tracking ID: {tracking_id}")
            return

        operation = self._active_operations[tracking_id]
        operation.end_time = time.time()
        operation.duration_ms = (operation.end_time - operation.start_time) * 1000
        operation.success = success
        operation.error = error

        # Get ending resource usage
        if self._process:
            operation.cpu_percent_end = self._process.cpu_percent(interval=0.1)
            memory_info = self._process.memory_info()
            operation.memory_mb_end = memory_info.rss / 1024 / 1024
        else:
            operation.cpu_percent_end = None
            operation.memory_mb_end = None

        # Update metadata
        if result_metadata:
            operation.metadata.update(result_metadata)

        # Move to history
        self._history[operation.operation_type].append(operation)
        del self._active_operations[tracking_id]

        # Check thresholds
        self._check_thresholds(operation)

        # Invalidate stats cache for this operation type
        self._stats_cache_timestamps.pop(operation.operation_type, None)

        logger.debug(
            f"📊 Completed tracking: {tracking_id} "
            f"(duration={operation.duration_ms:.1f}ms, success={success})"
        )

    def get_operation_stats(
        self, operation_type: str, force_refresh: bool = False
    ) -> Optional[PerformanceStats]:
        """
        Get aggregated statistics for an operation type

        Args:
            operation_type: Type of operation
            force_refresh: Force recalculation of stats

        Returns:
            Performance statistics or None if no data
        """
        # Check cache
        if not force_refresh:
            cache_time = self._stats_cache_timestamps.get(operation_type, 0)
            if time.time() - cache_time < self._stats_cache_ttl:
                return self._stats_cache.get(operation_type)

        # Get historical data
        operations = list(self._history.get(operation_type, []))
        if not operations:
            return None

        # Calculate statistics
        durations = [op.duration_ms for op in operations if op.duration_ms is not None]
        if not durations:
            return None

        success_count = sum(1 for op in operations if op.success)
        failure_count = len(operations) - success_count

        # CPU and memory deltas
        cpu_deltas = []
        memory_deltas = []

        for op in operations:
            if op.cpu_percent_start is not None and op.cpu_percent_end is not None:
                cpu_deltas.append(op.cpu_percent_end - op.cpu_percent_start)
            if op.memory_mb_start is not None and op.memory_mb_end is not None:
                memory_deltas.append(op.memory_mb_end - op.memory_mb_start)

        stats = PerformanceStats(
            operation_type=operation_type,
            total_count=len(operations),
            success_count=success_count,
            failure_count=failure_count,
            avg_duration_ms=statistics.mean(durations),
            min_duration_ms=min(durations),
            max_duration_ms=max(durations),
            p50_duration_ms=statistics.median(durations),
            p95_duration_ms=self._calculate_percentile(durations, 95),
            p99_duration_ms=self._calculate_percentile(durations, 99),
            avg_cpu_delta=statistics.mean(cpu_deltas) if cpu_deltas else 0.0,
            avg_memory_delta_mb=(
                statistics.mean(memory_deltas) if memory_deltas else 0.0
            ),
            last_updated=datetime.utcnow(),
        )

        # Update cache
        self._stats_cache[operation_type] = stats
        self._stats_cache_timestamps[operation_type] = time.time()

        return stats

    def get_all_stats(self) -> Dict[str, PerformanceStats]:
        """Get statistics for all operation types"""
        all_stats = {}

        for operation_type in self._history.keys():
            stats = self.get_operation_stats(operation_type)
            if stats:
                all_stats[operation_type] = stats

        return all_stats

    def get_active_operations(self) -> List[Dict[str, Any]]:
        """Get currently active operations"""
        active = []
        current_time = time.time()

        for tracking_id, operation in self._active_operations.items():
            active.append(
                {
                    "tracking_id": tracking_id,
                    "operation_type": operation.operation_type,
                    "duration_ms": (current_time - operation.start_time) * 1000,
                    "metadata": operation.metadata,
                }
            )

        return active

    def get_slow_operations(
        self, operation_type: Optional[str] = None, threshold_percentile: int = 95
    ) -> List[OperationMetrics]:
        """
        Get operations that were slower than the threshold percentile

        Args:
            operation_type: Optional filter by operation type
            threshold_percentile: Percentile threshold (default 95)

        Returns:
            List of slow operations
        """
        slow_operations = []

        if operation_type:
            operation_types = [operation_type]
        else:
            operation_types = list(self._history.keys())

        for op_type in operation_types:
            operations = list(self._history.get(op_type, []))
            if not operations:
                continue

            durations = [
                op.duration_ms for op in operations if op.duration_ms is not None
            ]
            if not durations:
                continue

            threshold = self._calculate_percentile(durations, threshold_percentile)

            for op in operations:
                if op.duration_ms and op.duration_ms > threshold:
                    slow_operations.append(op)

        return sorted(slow_operations, key=lambda x: x.duration_ms or 0, reverse=True)

    def record_audit_event(self, event: Dict[str, Any]):
        """Record an audit event"""
        self._audit_events.append({"timestamp": datetime.utcnow().isoformat(), **event})

    def get_audit_events(
        self,
        flow_id: Optional[str] = None,
        operation: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit events with optional filtering"""
        events = list(self._audit_events)

        # Filter by flow_id
        if flow_id:
            events = [e for e in events if e.get("flow_id") == flow_id]

        # Filter by operation
        if operation:
            events = [e for e in events if e.get("operation") == operation]

        # Return most recent events
        return events[-limit:]

    def set_threshold(self, operation_type: str, metric: str, threshold: float):
        """
        Set performance threshold for alerting

        Args:
            operation_type: Type of operation
            metric: Metric name (e.g., 'duration_ms', 'cpu_percent')
            threshold: Threshold value
        """
        if operation_type not in self._thresholds:
            self._thresholds[operation_type] = {}

        self._thresholds[operation_type][metric] = threshold
        logger.info(f"✅ Set threshold: {operation_type}.{metric} = {threshold}")

    def get_performance_report(self, time_range_minutes: int = 60) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report

        Args:
            time_range_minutes: Time range to consider for the report

        Returns:
            Performance report with insights
        """
        cutoff_time = time.time() - (time_range_minutes * 60)

        report = {
            "time_range_minutes": time_range_minutes,
            "generated_at": datetime.utcnow().isoformat(),
            "operation_stats": {},
            "slow_operations": [],
            "threshold_violations": [],
            "resource_usage": {
                "current_cpu_percent": (
                    self._process.cpu_percent(interval=0.1) if self._process else "N/A"
                ),
                "current_memory_mb": (
                    self._process.memory_info().rss / 1024 / 1024
                    if self._process
                    else "N/A"
                ),
            },
        }

        # Collect stats for each operation type
        for op_type in self._history.keys():
            # Filter operations within time range
            recent_ops = [
                op for op in self._history[op_type] if op.start_time > cutoff_time
            ]

            if recent_ops:
                stats = self.get_operation_stats(op_type)
                if stats:
                    report["operation_stats"][op_type] = {
                        "total_count": len(recent_ops),
                        "success_rate": (
                            sum(1 for op in recent_ops if op.success)
                            / len(recent_ops)
                            * 100
                        ),
                        "avg_duration_ms": stats.avg_duration_ms,
                        "p95_duration_ms": stats.p95_duration_ms,
                    }

        # Find slow operations
        slow_ops = self.get_slow_operations(threshold_percentile=90)
        report["slow_operations"] = [
            {
                "operation_type": op.operation_type,
                "duration_ms": op.duration_ms,
                "metadata": op.metadata,
                "timestamp": datetime.fromtimestamp(op.start_time).isoformat(),
            }
            for op in slow_ops[:10]  # Top 10 slowest
        ]

        # Check threshold violations
        for op_type, thresholds in self._thresholds.items():
            recent_ops = [
                op
                for op in self._history.get(op_type, [])
                if op.start_time > cutoff_time
            ]

            for op in recent_ops:
                if op.duration_ms and op.duration_ms > thresholds.get(
                    "duration_ms", float("inf")
                ):
                    report["threshold_violations"].append(
                        {
                            "operation_type": op_type,
                            "metric": "duration_ms",
                            "value": op.duration_ms,
                            "threshold": thresholds["duration_ms"],
                            "timestamp": datetime.fromtimestamp(
                                op.start_time
                            ).isoformat(),
                        }
                    )

        return report

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of a list of values"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)

        if index >= len(sorted_values):
            return sorted_values[-1]

        return sorted_values[index]

    def _check_thresholds(self, operation: OperationMetrics):
        """Check if operation violated any thresholds"""
        thresholds = self._thresholds.get(operation.operation_type, {})

        violations = []

        # Check duration threshold
        duration_threshold = thresholds.get("duration_ms")
        if (
            duration_threshold
            and operation.duration_ms
            and operation.duration_ms > duration_threshold
        ):
            violations.append(
                f"Duration ({operation.duration_ms:.1f}ms) exceeded threshold ({duration_threshold}ms)"
            )

        # Check CPU threshold
        cpu_threshold = thresholds.get("cpu_percent")
        if (
            cpu_threshold
            and operation.cpu_percent_end
            and operation.cpu_percent_end > cpu_threshold
        ):
            violations.append(
                f"CPU usage ({operation.cpu_percent_end:.1f}%) exceeded threshold ({cpu_threshold}%)"
            )

        if violations:
            logger.warning(
                f"⚠️ Performance threshold violations for {operation.operation_type}: "
                f"{'; '.join(violations)}"
            )


# Global performance tracker instance
performance_tracker = PerformanceTracker()
