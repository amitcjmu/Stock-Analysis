"""
Base types, enums, and dataclasses for Service Health Manager

Contains all the core data structures used throughout the service health monitoring system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ServiceType(str, Enum):
    """Types of services monitored"""

    REDIS = "redis"
    DATABASE = "database"
    AUTH_CACHE = "auth_cache"
    STORAGE_MANAGER = "storage_manager"
    LLM_SERVICE = "llm_service"
    EMBEDDING_SERVICE = "embedding_service"


class ServiceHealth(str, Enum):
    """Service health status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class SystemHealth(str, Enum):
    """Overall system health levels"""

    FULLY_OPERATIONAL = "fully_operational"  # All services healthy
    DEGRADED_PERFORMANCE = "degraded_performance"  # Some services degraded
    LIMITED_FUNCTIONALITY = "limited_functionality"  # Critical services down
    EMERGENCY_MODE = "emergency_mode"  # Most services failing


@dataclass
class HealthMetrics:
    """Health metrics for a service"""

    service_type: ServiceType
    response_time_ms: float = 0.0
    success_rate: float = 100.0
    error_count: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    is_available: bool = True
    circuit_breaker_open: bool = False

    def __post_init__(self):
        if self.last_success is None:
            self.last_success = datetime.utcnow()


@dataclass
class ServiceConfig:
    """Configuration for service monitoring"""

    service_type: ServiceType
    health_check_interval_seconds: int = 30
    timeout_seconds: int = 10
    failure_threshold: int = 5  # Failures before marking as unhealthy
    success_threshold: int = 3  # Successes needed to mark as healthy
    circuit_breaker_threshold: int = 10  # Failures before opening circuit breaker
    circuit_breaker_timeout_seconds: int = 60  # Time before attempting to close circuit
    critical_service: bool = True  # Whether failure affects system health
    dependencies: Set[ServiceType] = field(default_factory=set)


@dataclass
class HealthCheckResult:
    """Result of a health check operation"""

    service_type: ServiceType
    is_healthy: bool
    response_time_ms: float
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealthStatus:
    """Overall system health status"""

    overall_health: SystemHealth
    timestamp: datetime
    service_statuses: Dict[ServiceType, ServiceHealth]
    unhealthy_services: List[ServiceType]
    degraded_services: List[ServiceType]
    recommendations: List[str] = field(default_factory=list)
    estimated_recovery_time_minutes: Optional[int] = None
