"""
Base Types and Data Structures for Fallback Orchestrator

This module contains the core enums, dataclasses, and type definitions
used throughout the fallback orchestrator system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.services.monitoring.service_health_manager import ServiceType


class FallbackLevel(str, Enum):
    """Fallback service levels in order of preference"""

    PRIMARY = "primary"  # Redis cache - optimal performance
    SECONDARY = "secondary"  # In-memory cache - degraded performance
    TERTIARY = "tertiary"  # Direct database - emergency mode
    EMERGENCY = "emergency"  # Static/default data - minimal functionality


class OperationType(str, Enum):
    """Types of operations that require fallback handling"""

    USER_SESSION = "user_session"
    USER_CONTEXT = "user_context"
    CLIENT_DATA = "client_data"
    ENGAGEMENT_DATA = "engagement_data"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CACHE_READ = "cache_read"
    CACHE_WRITE = "cache_write"


class FallbackStrategy(str, Enum):
    """Fallback strategies for different scenarios"""

    FAIL_FAST = "fail_fast"  # Fail immediately if primary unavailable
    GRACEFUL_DEGRADATION = "graceful_degradation"  # Try all levels in sequence
    PERFORMANCE_FIRST = "performance_first"  # Prefer faster services
    RELIABILITY_FIRST = "reliability_first"  # Prefer more reliable services
    EMERGENCY_ONLY = "emergency_only"  # Skip to emergency level


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior"""

    operation_type: OperationType
    strategy: FallbackStrategy = FallbackStrategy.GRACEFUL_DEGRADATION
    max_retry_attempts: int = 3
    timeout_per_level_seconds: float = 5.0
    circuit_breaker_enabled: bool = True
    performance_threshold_ms: float = 1000.0
    reliability_threshold_percent: float = 95.0
    enable_recovery_detection: bool = True
    fallback_data_ttl_seconds: int = 300  # 5 minutes for emergency data


@dataclass
class FallbackAttempt:
    """Record of a fallback attempt"""

    operation_type: OperationType
    level: FallbackLevel
    service_type: ServiceType
    success: bool
    response_time_ms: float
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FallbackResult:
    """Result of a fallback operation"""

    success: bool
    value: Any = None
    level_used: Optional[FallbackLevel] = None
    service_used: Optional[ServiceType] = None
    total_attempts: int = 0
    total_time_ms: float = 0.0
    attempts: List[FallbackAttempt] = field(default_factory=list)
    error_message: Optional[str] = None
    fallback_active: bool = False


@dataclass
class ServiceLevelMapping:
    """Mapping of fallback levels to service implementations"""

    primary_services: List[ServiceType] = field(
        default_factory=lambda: [ServiceType.REDIS]
    )
    secondary_services: List[ServiceType] = field(
        default_factory=lambda: [ServiceType.AUTH_CACHE]
    )
    tertiary_services: List[ServiceType] = field(
        default_factory=lambda: [ServiceType.DATABASE]
    )
    emergency_handler: Optional[Callable] = None
