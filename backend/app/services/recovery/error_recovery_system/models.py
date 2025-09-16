"""
Data models and enums for error recovery system.

Defines core data structures for recovery operations, results, and configurations.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.services.auth.fallback_orchestrator import OperationType
from app.services.monitoring.service_health_manager import ServiceType


class RecoveryType(str, Enum):
    """Types of recovery operations"""

    IMMEDIATE_RETRY = "immediate_retry"
    DELAYED_RETRY = "delayed_retry"
    BACKGROUND_SYNC = "background_sync"
    DATA_REPAIR = "data_repair"
    DEAD_LETTER = "dead_letter"
    MANUAL_INTERVENTION = "manual_intervention"


class FailureCategory(str, Enum):
    """Categories of failures for recovery strategies"""

    TRANSIENT = "transient"  # Network timeouts, temporary unavailability
    PERSISTENT = "persistent"  # Configuration errors, service down
    DATA_CORRUPTION = "data_corruption"  # Data integrity issues
    AUTHENTICATION = "authentication"  # Auth/permission failures
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # Memory, disk, quota issues
    UNKNOWN = "unknown"  # Unclassified failures


class RecoveryPriority(str, Enum):
    """Priority levels for recovery operations"""

    CRITICAL = "critical"  # User-facing operations, auth failures
    HIGH = "high"  # Important background operations
    NORMAL = "normal"  # Regular cache updates, sync operations
    LOW = "low"  # Cleanup, maintenance operations


@dataclass
class RecoveryOperation:
    """Represents a recovery operation to be executed"""

    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recovery_type: RecoveryType = RecoveryType.IMMEDIATE_RETRY
    failure_category: FailureCategory = FailureCategory.UNKNOWN
    priority: RecoveryPriority = RecoveryPriority.NORMAL
    operation_type: OperationType = OperationType.CACHE_READ
    service_type: ServiceType = ServiceType.REDIS

    # Operation details
    operation_func: Optional[Callable] = None
    operation_args: Tuple = field(default_factory=tuple)
    operation_kwargs: Dict[str, Any] = field(default_factory=dict)

    # Recovery configuration
    max_retry_attempts: int = 5
    retry_count: int = 0
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 300.0  # 5 minutes
    backoff_multiplier: float = 2.0
    jitter_enabled: bool = True

    # Timing and scheduling
    created_at: datetime = field(default_factory=datetime.utcnow)
    next_retry_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None

    # Context and metadata
    context_data: Dict[str, Any] = field(default_factory=dict)
    failure_history: List[Dict[str, Any]] = field(default_factory=list)
    recovery_metadata: Dict[str, Any] = field(default_factory=dict)

    # Callback functions
    success_callback: Optional[Callable] = None
    failure_callback: Optional[Callable] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "operation_id": self.operation_id,
            "recovery_type": self.recovery_type.value,
            "failure_category": self.failure_category.value,
            "priority": self.priority.value,
            "operation_type": self.operation_type.value,
            "service_type": self.service_type.value,
            "max_retry_attempts": self.max_retry_attempts,
            "retry_count": self.retry_count,
            "base_delay_seconds": self.base_delay_seconds,
            "max_delay_seconds": self.max_delay_seconds,
            "backoff_multiplier": self.backoff_multiplier,
            "jitter_enabled": self.jitter_enabled,
            "created_at": self.created_at.isoformat(),
            "next_retry_at": (
                self.next_retry_at.isoformat() if self.next_retry_at else None
            ),
            "last_attempt_at": (
                self.last_attempt_at.isoformat() if self.last_attempt_at else None
            ),
            "context_data": self.context_data,
            "failure_history": self.failure_history,
            "recovery_metadata": self.recovery_metadata,
        }


@dataclass
class RecoveryResult:
    """Result of a recovery operation"""

    operation_id: str
    success: bool
    recovery_type: RecoveryType
    attempts_made: int
    total_time_seconds: float
    final_error: Optional[str] = None
    recovered_data: Any = None
    consistency_check_passed: bool = True
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SyncJob:
    """Background synchronization job"""

    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_type: ServiceType = ServiceType.REDIS
    sync_type: str = "full_sync"
    source_keys: List[str] = field(default_factory=list)
    target_keys: List[str] = field(default_factory=list)
    data_items: List[Dict[str, Any]] = field(default_factory=list)
    priority: RecoveryPriority = RecoveryPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    error_message: Optional[str] = None
