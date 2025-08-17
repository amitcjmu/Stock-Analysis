"""
Storage Manager Metadata Manager Module

Handles metadata operations, storage statistics, and file indexing.
This module provides comprehensive metrics collection and monitoring capabilities.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


class MetricType(str, Enum):
    """Types of metrics that can be collected"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"


class AggregationPeriod(str, Enum):
    """Periods for aggregating metrics"""

    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class MetricDataPoint:
    """Individual metric data point"""

    timestamp: datetime
    value: Union[int, float]
    labels: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def now(
        cls, value: Union[int, float], labels: Optional[Dict[str, str]] = None
    ) -> "MetricDataPoint":
        """Create a data point with current timestamp"""
        return cls(timestamp=datetime.utcnow(), value=value, labels=labels or {})


@dataclass
class AggregatedMetrics:
    """Aggregated metrics over a time period"""

    period: AggregationPeriod
    start_time: datetime
    end_time: datetime
    count: int = 0
    sum_value: float = 0.0
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None

    def __post_init__(self):
        """Calculate derived values"""
        if self.count > 0:
            self.avg_value = self.sum_value / self.count


@dataclass
class OperationMetadata:
    """Metadata for storage operations"""

    operation_id: str
    operation_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "pending"
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        """Get operation duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_completed(self) -> bool:
        """Check if operation is completed"""
        return self.status in {"completed", "failed", "cancelled"}


class MetricsCollector:
    """Collects and manages storage metrics"""

    def __init__(self, max_data_points: int = 10000):
        self.max_data_points = max_data_points
        self._metrics: Dict[str, List[MetricDataPoint]] = {}
        self._operations: Dict[str, OperationMetadata] = {}
        self._start_time = datetime.utcnow()

    def record_metric(
        self,
        name: str,
        value: Union[int, float],
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Record a metric value"""
        if name not in self._metrics:
            self._metrics[name] = []

        data_point = MetricDataPoint.now(value, labels)
        self._metrics[name].append(data_point)

        # Trim old data points if we exceed the limit
        if len(self._metrics[name]) > self.max_data_points:
            self._metrics[name] = self._metrics[name][-self.max_data_points :]

    def start_operation(
        self,
        operation_id: str,
        operation_type: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> OperationMetadata:
        """Start tracking an operation"""
        metadata = OperationMetadata(
            operation_id=operation_id,
            operation_type=operation_type,
            start_time=datetime.utcnow(),
            labels=labels or {},
        )
        self._operations[operation_id] = metadata
        return metadata

    def complete_operation(
        self,
        operation_id: str,
        status: str = "completed",
        error_message: Optional[str] = None,
        additional_metrics: Optional[Dict[str, Any]] = None,
    ):
        """Mark an operation as completed"""
        if operation_id in self._operations:
            operation = self._operations[operation_id]
            operation.end_time = datetime.utcnow()
            operation.status = status
            operation.error_message = error_message

            if additional_metrics:
                operation.metrics.update(additional_metrics)

            # Record operation duration as a metric
            if operation.duration:
                self.record_metric(
                    f"operation_duration_{operation.operation_type}",
                    operation.duration,
                    MetricType.TIMER,
                    operation.labels,
                )

    def get_metrics(
        self, name: Optional[str] = None
    ) -> Dict[str, List[MetricDataPoint]]:
        """Get collected metrics"""
        if name:
            return {name: self._metrics.get(name, [])}
        return self._metrics.copy()

    def get_aggregated_metrics(
        self,
        name: str,
        period: AggregationPeriod,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Optional[AggregatedMetrics]:
        """Get aggregated metrics for a period"""
        if name not in self._metrics:
            return None

        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=1)
        if end_time is None:
            end_time = datetime.utcnow()

        relevant_points = [
            point
            for point in self._metrics[name]
            if start_time <= point.timestamp <= end_time
        ]

        if not relevant_points:
            return AggregatedMetrics(
                period=period, start_time=start_time, end_time=end_time
            )

        values = [point.value for point in relevant_points]
        return AggregatedMetrics(
            period=period,
            start_time=start_time,
            end_time=end_time,
            count=len(values),
            sum_value=sum(values),
            min_value=min(values),
            max_value=max(values),
        )

    def get_operation_stats(self) -> Dict[str, Any]:
        """Get operation statistics"""
        completed_ops = [op for op in self._operations.values() if op.is_completed]
        failed_ops = [op for op in completed_ops if op.status == "failed"]

        return {
            "total_operations": len(self._operations),
            "completed_operations": len(completed_ops),
            "failed_operations": len(failed_ops),
            "success_rate": (
                (len(completed_ops) - len(failed_ops)) / len(completed_ops)
                if completed_ops
                else 0.0
            ),
            "uptime": (datetime.utcnow() - self._start_time).total_seconds(),
        }

    def reset(self):
        """Reset all collected metrics"""
        self._metrics.clear()
        self._operations.clear()
        self._start_time = datetime.utcnow()


# Global metrics collector instance
_global_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector


def shutdown_metrics_collector():
    """Shutdown the global metrics collector"""
    global _global_metrics_collector
    if _global_metrics_collector:
        _global_metrics_collector.reset()
        _global_metrics_collector = None


class MetadataManager:
    """Metadata manager - handles storage metadata operations"""

    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        self.metrics_collector = metrics_collector or get_metrics_collector()
        self._metadata_cache: Dict[str, Any] = {}

    def store_metadata(self, key: str, metadata: Dict[str, Any]):
        """Store metadata for a key"""
        self._metadata_cache[key] = {
            "metadata": metadata,
            "timestamp": datetime.utcnow(),
            "access_count": 0,
        }

        self.metrics_collector.record_metric(
            "metadata_stored", 1, MetricType.COUNTER, {"key": key}
        )

    def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a key"""
        if key in self._metadata_cache:
            self._metadata_cache[key]["access_count"] += 1
            self.metrics_collector.record_metric(
                "metadata_accessed", 1, MetricType.COUNTER, {"key": key}
            )
            return self._metadata_cache[key]["metadata"]
        return None

    def remove_metadata(self, key: str) -> bool:
        """Remove metadata for a key"""
        if key in self._metadata_cache:
            del self._metadata_cache[key]
            self.metrics_collector.record_metric(
                "metadata_removed", 1, MetricType.COUNTER, {"key": key}
            )
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get metadata manager statistics"""
        total_metadata = len(self._metadata_cache)
        total_access_count = sum(
            entry["access_count"] for entry in self._metadata_cache.values()
        )

        return {
            "total_metadata_entries": total_metadata,
            "total_access_count": total_access_count,
            "average_access_count": (
                total_access_count / total_metadata if total_metadata > 0 else 0
            ),
        }


class StorageMetadata:
    """Storage metadata - placeholder implementation"""

    def __init__(
        self,
        storage_type: str,
        size: int = 0,
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.storage_type = storage_type
        self.size = size
        self.created_at = created_at or datetime.utcnow()
        self.metadata = metadata or {}
        self.last_accessed = datetime.utcnow()

    def update_access_time(self):
        """Update last accessed time"""
        self.last_accessed = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "storage_type": self.storage_type,
            "size": self.size,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "metadata": self.metadata,
        }


class FileMetadata:
    """File metadata - placeholder implementation"""

    def __init__(
        self,
        file_path: str,
        size: int = 0,
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None,
    ):
        self.file_path = file_path
        self.size = size
        self.created_at = created_at or datetime.utcnow()
        self.modified_at = modified_at or datetime.utcnow()
        self.access_count = 0

    def update_modification_time(self):
        """Update modification time"""
        self.modified_at = datetime.utcnow()

    def increment_access_count(self):
        """Increment access count"""
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "file_path": self.file_path,
            "size": self.size,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "access_count": self.access_count,
        }


class DirectoryMetadata:
    """Directory metadata - placeholder implementation"""

    def __init__(self, directory_path: str, file_count: int = 0, total_size: int = 0):
        self.directory_path = directory_path
        self.file_count = file_count
        self.total_size = total_size
        self.created_at = datetime.utcnow()
        self.last_scanned = datetime.utcnow()

    def update_scan_time(self):
        """Update last scan time"""
        self.last_scanned = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "directory_path": self.directory_path,
            "file_count": self.file_count,
            "total_size": self.total_size,
            "created_at": self.created_at.isoformat(),
            "last_scanned": self.last_scanned.isoformat(),
        }


# Re-export main classes
__all__ = [
    "MetricType",
    "AggregationPeriod",
    "OperationMetadata",
    "MetricDataPoint",
    "AggregatedMetrics",
    "MetricsCollector",
    "get_metrics_collector",
    "shutdown_metrics_collector",
    "MetadataManager",
    "StorageMetadata",
    "FileMetadata",
    "DirectoryMetadata",
]
