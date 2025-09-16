"""
Base classes, types, and data structures for retry handling.

This module contains the core enums, dataclasses, and base types used
throughout the retry handling system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorType(str, Enum):
    """Classification of errors for appropriate handling strategies"""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK_CONNECTIVITY = "network_connectivity"
    RATE_LIMITING = "rate_limiting"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT = "timeout"
    DATA_VALIDATION = "data_validation"
    CONFIGURATION = "configuration"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetryStrategy(str, Enum):
    """Retry strategy types"""

    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    RANDOM_JITTER = "random_jitter"
    NO_RETRY = "no_retry"


@dataclass
class ErrorPattern:
    """Error pattern for classification and handling"""

    error_type: ErrorType
    severity: ErrorSeverity
    retry_strategy: RetryStrategy
    max_retries: int
    base_delay: float
    max_delay: float
    should_circuit_break: bool = False
    keywords: List[str] = field(default_factory=list)
    exception_types: List[type] = field(default_factory=list)


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    jitter: bool = True
    jitter_range: float = 0.1
    timeout_multiplier: float = 1.5
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 300.0  # 5 minutes


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""

    timestamp: datetime
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    adapter_name: str
    platform: str
    exception_type: str
    context: Dict[str, Any] = field(default_factory=dict)
    retry_attempt: int = 0
    total_retries: int = 0


@dataclass
class CircuitBreakerState:
    """State of a circuit breaker"""

    is_open: bool = False
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    next_attempt_time: Optional[datetime] = None
    consecutive_successes: int = 0
