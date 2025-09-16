"""
Service Health Manager

Comprehensive service health monitoring with circuit breakers for the auth performance
optimization system. Provides multi-layered health monitoring, circuit breaker patterns,
and service availability tracking to ensure graceful degradation during failures.

Key Features:
- Circuit breaker pattern implementation for all critical services
- Service health monitoring with configurable thresholds
- Automatic recovery detection and service restoration
- Performance metrics collection and alerting
- Multi-layered fallback health status
- Integration with existing retry handlers and storage systems

Service Levels:
- HEALTHY: All services operational
- DEGRADED: Some services unavailable but core functionality maintained
- CRITICAL: Major services down, limited functionality
- EMERGENCY: Core services failing, minimal functionality only

Architecture:
The ServiceHealthManager monitors Redis, database, storage, and auth services using
configurable health checks, circuit breakers, and performance thresholds to provide
real-time service health status and automatic failure recovery.
"""

# Import all base types and enums
from .base import (
    HealthCheckResult,
    HealthMetrics,
    ServiceConfig,
    ServiceHealth,
    ServiceType,
    SystemHealth,
    SystemHealthStatus,
)

# Import main manager class
from .core import ServiceHealthManager

# Import service components (for advanced usage)
from .circuit_breaker import CircuitBreakerManager
from .config import ServiceHealthConfig
from .health_checks import HealthCheckService
from .metrics import MetricsManager
from .utils import HealthUtils

# Global singleton instances
_service_health_manager = None


def get_service_health_manager() -> ServiceHealthManager:
    """Get singleton service health manager instance"""
    global _service_health_manager
    if _service_health_manager is None:
        _service_health_manager = ServiceHealthManager()
    return _service_health_manager


async def shutdown_service_health_manager() -> None:
    """Shutdown the service health manager"""
    global _service_health_manager
    if _service_health_manager is not None:
        await _service_health_manager.shutdown()
        _service_health_manager = None


# Public API exports - maintains backward compatibility
__all__ = [
    # Main manager
    "ServiceHealthManager",
    "get_service_health_manager",
    "shutdown_service_health_manager",
    # Base types and enums
    "ServiceType",
    "ServiceHealth",
    "SystemHealth",
    "HealthMetrics",
    "ServiceConfig",
    "HealthCheckResult",
    "SystemHealthStatus",
    # Service components (for advanced usage)
    "CircuitBreakerManager",
    "HealthCheckService",
    "MetricsManager",
    "ServiceHealthConfig",
    "HealthUtils",
]
