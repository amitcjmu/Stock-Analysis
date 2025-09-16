"""
Base types, enums, and dataclasses for Cache Performance Monitor

Contains all the core data structures used throughout the cache performance monitoring system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class CacheLayer(str, Enum):
    """Cache layer types"""

    REDIS = "redis"
    MEMORY = "memory"
    COMBINED = "combined"


class CacheOperation(str, Enum):
    """Cache operation types"""

    GET = "get"
    SET = "set"
    DELETE = "delete"
    INVALIDATE = "invalidate"
    CLEAR = "clear"
    HEALTH_CHECK = "health_check"
    BATCH_FLUSH = "batch_flush"


class CacheResult(str, Enum):
    """Cache operation results"""

    HIT = "hit"
    MISS = "miss"
    ERROR = "error"
    TIMEOUT = "timeout"
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class CachePerformanceEvent:
    """Individual cache performance event record"""

    operation_id: str
    operation: CacheOperation
    cache_layer: CacheLayer
    key_pattern: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    result: CacheResult = CacheResult.SUCCESS
    data_size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.end_time and not self.duration:
            self.duration = self.end_time - self.start_time

    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds"""
        return (self.duration or 0) * 1000


@dataclass
class CacheLayerStats:
    """Statistics for a specific cache layer"""

    layer: CacheLayer
    total_operations: int = 0
    hit_count: int = 0
    miss_count: int = 0
    error_count: int = 0
    total_response_time_ms: float = 0.0
    total_data_size_bytes: int = 0
    last_operation: Optional[float] = None

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage"""
        total_gets = self.hit_count + self.miss_count
        return (self.hit_count / total_gets * 100) if total_gets > 0 else 0.0

    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage"""
        return (
            (self.error_count / self.total_operations * 100)
            if self.total_operations > 0
            else 0.0
        )

    @property
    def average_response_time_ms(self) -> float:
        """Calculate average response time in milliseconds"""
        return (
            (self.total_response_time_ms / self.total_operations)
            if self.total_operations > 0
            else 0.0
        )


@dataclass
class CacheUtilizationStats:
    """Cache utilization statistics"""

    layer: CacheLayer
    current_size_bytes: int = 0
    max_size_bytes: int = 0
    current_item_count: int = 0
    max_item_count: int = 0
    eviction_count: int = 0
    expiration_count: int = 0
    memory_fragmentation_ratio: float = 0.0
    last_updated: Optional[float] = None

    @property
    def size_utilization_percent(self) -> float:
        """Calculate size utilization percentage"""
        return (
            (self.current_size_bytes / self.max_size_bytes * 100)
            if self.max_size_bytes > 0
            else 0.0
        )

    @property
    def item_utilization_percent(self) -> float:
        """Calculate item count utilization percentage"""
        return (
            (self.current_item_count / self.max_item_count * 100)
            if self.max_item_count > 0
            else 0.0
        )
