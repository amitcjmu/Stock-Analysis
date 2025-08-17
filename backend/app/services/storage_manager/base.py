"""
Storage Manager Base Classes

Contains base interfaces, enums, and data classes shared across
all storage manager modules. This provides the foundation for
the storage system architecture.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class StorageType(str, Enum):
    """Storage backend types"""

    REDIS = "redis"
    LOCAL_STORAGE = "local_storage"
    SESSION_STORAGE = "session_storage"
    DATABASE = "database"
    MEMORY = "memory"


class Priority(str, Enum):
    """Operation priority levels"""

    CRITICAL = "critical"  # 0ms delay, immediate processing
    HIGH = "high"  # 50ms max delay
    NORMAL = "normal"  # 100ms delay (default)
    LOW = "low"  # 500ms delay


class OperationType(str, Enum):
    """Storage operation types"""

    SET = "set"
    GET = "get"
    DELETE = "delete"
    EXISTS = "exists"
    CLEAR = "clear"


@dataclass
class StorageOperation:
    """Represents a storage operation to be batched"""

    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: OperationType = OperationType.SET
    key: str = ""
    value: Any = None
    storage_type: StorageType = StorageType.REDIS
    priority: Priority = Priority.NORMAL
    ttl: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    max_retries: int = 3
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert operation to dictionary for serialization"""
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type.value,
            "key": self.key,
            "value": self.value,
            "storage_type": self.storage_type.value,
            "priority": self.priority.value,
            "ttl": self.ttl,
            "created_at": self.created_at.isoformat(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StorageOperation":
        """Create StorageOperation from dictionary"""
        operation = cls(
            operation_id=data.get("operation_id", str(uuid.uuid4())),
            operation_type=OperationType(data.get("operation_type", "set")),
            key=data.get("key", ""),
            value=data.get("value"),
            storage_type=StorageType(data.get("storage_type", "redis")),
            priority=Priority(data.get("priority", "normal")),
            ttl=data.get("ttl"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {}),
        )

        if "created_at" in data:
            try:
                operation.created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                pass  # Use default

        return operation


@dataclass
class BatchResult:
    """Results from a batch operation"""

    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    duration_ms: float = 0.0
    errors: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_operations == 0:
            return 100.0
        return (self.successful_operations / self.total_operations) * 100

    def add_error(self, operation_id: str, error: str, error_type: str = "unknown"):
        """Add an error to the batch result"""
        self.errors.append(
            {
                "operation_id": operation_id,
                "error": error,
                "error_type": error_type,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def merge(self, other: "BatchResult") -> "BatchResult":
        """Merge another BatchResult into this one"""
        return BatchResult(
            total_operations=self.total_operations + other.total_operations,
            successful_operations=self.successful_operations
            + other.successful_operations,
            failed_operations=self.failed_operations + other.failed_operations,
            duration_ms=max(self.duration_ms, other.duration_ms),
            errors=self.errors + other.errors,
        )


@dataclass
class StorageStats:
    """Storage performance statistics"""

    total_operations: int = 0
    batched_operations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    average_batch_size: float = 0.0
    average_processing_time_ms: float = 0.0
    memory_usage_bytes: int = 0
    queue_length: int = 0
    last_reset: datetime = field(default_factory=datetime.utcnow)

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate as percentage"""
        total_reads = self.cache_hits + self.cache_misses
        if total_reads == 0:
            return 0.0
        return (self.cache_hits / total_reads) * 100

    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage"""
        if self.total_operations == 0:
            return 0.0
        return (self.errors / self.total_operations) * 100

    @property
    def batching_efficiency(self) -> float:
        """Calculate batching efficiency (higher is better)"""
        if self.total_operations == 0:
            return 0.0
        return self.average_batch_size

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for serialization"""
        return {
            "total_operations": self.total_operations,
            "batched_operations": self.batched_operations,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "errors": self.errors,
            "average_batch_size": self.average_batch_size,
            "average_processing_time_ms": self.average_processing_time_ms,
            "memory_usage_bytes": self.memory_usage_bytes,
            "queue_length": self.queue_length,
            "cache_hit_rate": self.cache_hit_rate,
            "error_rate": self.error_rate,
            "batching_efficiency": self.batching_efficiency,
            "last_reset": self.last_reset.isoformat(),
        }


class BaseStorageBackend(ABC):
    """Abstract base class for storage backends"""

    def __init__(self, backend_name: str, default_ttl: int = 3600):
        self.backend_name = backend_name
        self.default_ttl = default_ttl
        self.enabled = True

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from storage"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in storage"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from storage"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in storage"""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all data from storage"""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get backend-specific statistics"""
        return {
            "backend_name": self.backend_name,
            "enabled": self.enabled,
            "default_ttl": self.default_ttl,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the backend"""
        try:
            # Try a simple operation
            test_key = f"health_check_{uuid.uuid4()}"
            await self.set(test_key, "test", ttl=1)
            exists = await self.exists(test_key)
            await self.delete(test_key)

            return {
                "available": True,
                "backend_name": self.backend_name,
                "test_passed": exists,
            }
        except Exception as e:
            return {
                "available": False,
                "backend_name": self.backend_name,
                "error": str(e),
            }


class BaseOperationProcessor(ABC):
    """Abstract base class for operation processors"""

    @abstractmethod
    async def process_operation(self, operation: StorageOperation) -> bool:
        """Process a single storage operation"""
        pass

    @abstractmethod
    async def process_batch(self, operations: List[StorageOperation]) -> BatchResult:
        """Process a batch of storage operations"""
        pass

    def can_handle_operation(self, operation: StorageOperation) -> bool:
        """Check if this processor can handle the given operation"""
        return True

    def get_processing_priority(self, operation: StorageOperation) -> int:
        """Get processing priority for operation (higher = more urgent)"""
        priority_map = {
            Priority.CRITICAL: 1000,
            Priority.HIGH: 100,
            Priority.NORMAL: 10,
            Priority.LOW: 1,
        }
        return priority_map.get(operation.priority, 10)


@dataclass
class StorageConfiguration:
    """Configuration for storage manager"""

    # Queue configuration
    max_queue_size: int = 10000
    max_batch_size: int = 1000

    # Debouncing intervals by priority (in milliseconds)
    debounce_intervals: Dict[Priority, int] = field(
        default_factory=lambda: {
            Priority.CRITICAL: 0,  # Immediate processing
            Priority.HIGH: 50,  # 50ms max delay
            Priority.NORMAL: 100,  # 100ms delay (default)
            Priority.LOW: 500,  # 500ms delay
        }
    )

    # Retry configuration
    base_retry_delay: float = 0.1  # 100ms
    max_retry_delay: float = 5.0  # 5 seconds
    retry_backoff_factor: float = 2.0

    # Performance configuration
    enable_metrics: bool = True
    metrics_collection_interval: int = 60  # seconds
    cleanup_interval: int = 300  # 5 minutes

    # Memory storage configuration
    memory_max_size: int = 10000
    memory_default_ttl: int = 3600

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []

        if self.max_queue_size <= 0:
            issues.append("max_queue_size must be positive")

        if self.max_batch_size <= 0:
            issues.append("max_batch_size must be positive")

        if self.max_batch_size > self.max_queue_size:
            issues.append("max_batch_size cannot exceed max_queue_size")

        if self.base_retry_delay <= 0:
            issues.append("base_retry_delay must be positive")

        if self.max_retry_delay <= self.base_retry_delay:
            issues.append("max_retry_delay must be greater than base_retry_delay")

        if self.retry_backoff_factor <= 1.0:
            issues.append("retry_backoff_factor must be greater than 1.0")

        for priority, interval in self.debounce_intervals.items():
            if interval < 0:
                issues.append(f"debounce_intervals[{priority}] must be non-negative")

        return issues


# Utility functions
def create_operation(
    operation_type: OperationType,
    key: str,
    value: Any = None,
    storage_type: StorageType = StorageType.REDIS,
    priority: Priority = Priority.NORMAL,
    ttl: Optional[int] = None,
    callback: Optional[Callable] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> StorageOperation:
    """Factory function to create storage operations"""
    return StorageOperation(
        operation_type=operation_type,
        key=key,
        value=value,
        storage_type=storage_type,
        priority=priority,
        ttl=ttl,
        callback=callback,
        metadata=metadata or {},
    )


def validate_key(key: str) -> bool:
    """Validate storage key format"""
    if not key:
        return False
    if len(key) > 1000:  # Reasonable limit
        return False
    # Additional validation rules can be added here
    return True


def validate_value(value: Any) -> bool:
    """Validate storage value"""
    if value is None:
        return True

    # Check for callable objects (not serializable)
    if callable(value):
        return False

    # Additional validation rules can be added here
    return True
