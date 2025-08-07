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

import asyncio
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.logging import get_logger
from app.services.adapters.retry_handler import CircuitBreakerState, RetryHandler

logger = get_logger(__name__)


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
    circuit_breaker_threshold: int = 10  # Failures before opening circuit
    circuit_breaker_timeout_seconds: int = 300  # 5 minutes
    response_time_warning_ms: float = 1000  # Warning threshold
    response_time_critical_ms: float = 5000  # Critical threshold
    enabled: bool = True


@dataclass
class HealthCheckResult:
    """Result of a health check operation"""

    service_type: ServiceType
    is_healthy: bool
    response_time_ms: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SystemHealthStatus:
    """Overall system health status"""

    overall_health: SystemHealth
    service_health: Dict[ServiceType, ServiceHealth]
    available_services: Set[ServiceType]
    degraded_services: Set[ServiceType]
    failed_services: Set[ServiceType]
    fallback_active: bool = False
    emergency_mode: bool = False
    recommendations: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)


class ServiceHealthManager:
    """
    Service Health Manager with Circuit Breaker Patterns

    Monitors service health, implements circuit breakers, and provides fallback
    orchestration for graceful degradation during service failures.
    """

    def __init__(self):
        self.service_configs: Dict[ServiceType, ServiceConfig] = {}
        self.service_metrics: Dict[ServiceType, HealthMetrics] = {}
        self.circuit_breakers: Dict[ServiceType, CircuitBreakerState] = {}
        self.health_check_tasks: Dict[ServiceType, Optional[asyncio.Task]] = {}

        # Health check history for trend analysis
        self.health_history: Dict[ServiceType, deque] = defaultdict(
            lambda: deque(maxlen=100)
        )

        # Performance monitoring
        self.response_times: Dict[ServiceType, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )

        # Alert state management
        self.active_alerts: Dict[ServiceType, List[Dict[str, Any]]] = defaultdict(list)
        self.alert_cooldowns: Dict[str, datetime] = {}

        # System state
        self.system_start_time = datetime.utcnow()
        self.last_system_health_check = datetime.utcnow()
        self.enabled = True

        # Retry handler integration
        self.retry_handler = RetryHandler()

        # Initialize default service configurations
        self._initialize_default_configs()

        logger.info("ServiceHealthManager initialized with circuit breaker patterns")

    def _initialize_default_configs(self):
        """Initialize default configurations for monitored services"""
        default_configs = {
            ServiceType.REDIS: ServiceConfig(
                service_type=ServiceType.REDIS,
                health_check_interval_seconds=30,
                timeout_seconds=5,
                failure_threshold=3,
                circuit_breaker_threshold=5,
                response_time_warning_ms=500,
                response_time_critical_ms=2000,
            ),
            ServiceType.DATABASE: ServiceConfig(
                service_type=ServiceType.DATABASE,
                health_check_interval_seconds=60,
                timeout_seconds=10,
                failure_threshold=3,
                circuit_breaker_threshold=5,
                response_time_warning_ms=1000,
                response_time_critical_ms=5000,
            ),
            ServiceType.AUTH_CACHE: ServiceConfig(
                service_type=ServiceType.AUTH_CACHE,
                health_check_interval_seconds=30,
                timeout_seconds=5,
                failure_threshold=3,
                circuit_breaker_threshold=5,
                response_time_warning_ms=500,
                response_time_critical_ms=2000,
            ),
            ServiceType.STORAGE_MANAGER: ServiceConfig(
                service_type=ServiceType.STORAGE_MANAGER,
                health_check_interval_seconds=30,
                timeout_seconds=5,
                failure_threshold=3,
                circuit_breaker_threshold=5,
                response_time_warning_ms=500,
                response_time_critical_ms=2000,
            ),
            ServiceType.LLM_SERVICE: ServiceConfig(
                service_type=ServiceType.LLM_SERVICE,
                health_check_interval_seconds=120,
                timeout_seconds=30,
                failure_threshold=5,
                circuit_breaker_threshold=10,
                response_time_warning_ms=5000,
                response_time_critical_ms=15000,
            ),
            ServiceType.EMBEDDING_SERVICE: ServiceConfig(
                service_type=ServiceType.EMBEDDING_SERVICE,
                health_check_interval_seconds=120,
                timeout_seconds=30,
                failure_threshold=5,
                circuit_breaker_threshold=10,
                response_time_warning_ms=5000,
                response_time_critical_ms=15000,
            ),
        }

        for service_type, config in default_configs.items():
            self.register_service(config)

    def register_service(self, config: ServiceConfig) -> bool:
        """Register a service for health monitoring"""
        try:
            self.service_configs[config.service_type] = config
            self.service_metrics[config.service_type] = HealthMetrics(
                service_type=config.service_type
            )
            self.circuit_breakers[config.service_type] = CircuitBreakerState()

            # Start health check task if enabled
            if config.enabled and self.enabled:
                self._start_health_check_task(config.service_type)

            logger.info(f"Registered service for monitoring: {config.service_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to register service {config.service_type}: {e}")
            return False

    def _start_health_check_task(self, service_type: ServiceType):
        """Start health check task for a service"""
        if service_type in self.health_check_tasks:
            # Cancel existing task
            existing_task = self.health_check_tasks[service_type]
            if existing_task and not existing_task.done():
                existing_task.cancel()

        # Start new task
        self.health_check_tasks[service_type] = asyncio.create_task(
            self._health_check_loop(service_type)
        )

        logger.debug(f"Started health check task for {service_type}")

    async def _health_check_loop(self, service_type: ServiceType):
        """Continuous health check loop for a service"""
        config = self.service_configs[service_type]

        while self.enabled and config.enabled:
            try:
                # Perform health check
                result = await self._perform_health_check(service_type)

                # Update metrics and circuit breaker state
                await self._update_service_metrics(result)

                # Check for alerts
                await self._check_alerts(service_type)

                # Wait for next check
                await asyncio.sleep(config.health_check_interval_seconds)

            except asyncio.CancelledError:
                logger.debug(f"Health check task cancelled for {service_type}")
                break
            except Exception as e:
                logger.error(f"Error in health check loop for {service_type}: {e}")
                await asyncio.sleep(config.health_check_interval_seconds)

    async def _perform_health_check(
        self, service_type: ServiceType
    ) -> HealthCheckResult:
        """Perform health check for a specific service"""
        config = self.service_configs[service_type]
        start_time = time.time()

        try:
            # Check circuit breaker state first
            circuit_breaker = self.circuit_breakers[service_type]
            if circuit_breaker.is_open:
                # Check if we can attempt to close the circuit
                if (
                    circuit_breaker.next_attempt_time
                    and datetime.utcnow() >= circuit_breaker.next_attempt_time
                ):
                    circuit_breaker.is_open = False
                    logger.info(
                        f"Circuit breaker for {service_type} entering half-open state"
                    )
                else:
                    # Circuit still open
                    response_time = (time.time() - start_time) * 1000
                    return HealthCheckResult(
                        service_type=service_type,
                        is_healthy=False,
                        response_time_ms=response_time,
                        error_message="Circuit breaker is open",
                        metadata={"circuit_breaker_open": True},
                    )

            # Perform actual health check based on service type
            is_healthy, error_message, metadata = (
                await self._execute_service_health_check(
                    service_type, config.timeout_seconds
                )
            )

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                service_type=service_type,
                is_healthy=is_healthy,
                response_time_ms=response_time,
                error_message=error_message,
                metadata=metadata,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Health check failed for {service_type}: {e}")

            return HealthCheckResult(
                service_type=service_type,
                is_healthy=False,
                response_time_ms=response_time,
                error_message=str(e),
                metadata={"exception": type(e).__name__},
            )

    async def _execute_service_health_check(
        self, service_type: ServiceType, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Execute the actual health check for a service"""
        try:
            if service_type == ServiceType.REDIS:
                return await self._check_redis_health(timeout_seconds)
            elif service_type == ServiceType.DATABASE:
                return await self._check_database_health(timeout_seconds)
            elif service_type == ServiceType.AUTH_CACHE:
                return await self._check_auth_cache_health(timeout_seconds)
            elif service_type == ServiceType.STORAGE_MANAGER:
                return await self._check_storage_manager_health(timeout_seconds)
            elif service_type == ServiceType.LLM_SERVICE:
                return await self._check_llm_service_health(timeout_seconds)
            elif service_type == ServiceType.EMBEDDING_SERVICE:
                return await self._check_embedding_service_health(timeout_seconds)
            else:
                return False, f"Unknown service type: {service_type}", {}

        except asyncio.TimeoutError:
            return (
                False,
                f"Health check timeout after {timeout_seconds}s",
                {"timeout": True},
            )
        except Exception as e:
            return False, str(e), {"exception": type(e).__name__}

    async def _check_redis_health(
        self, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check Redis service health"""
        try:
            from app.services.caching.redis_cache import get_redis_cache

            redis_cache = get_redis_cache()
            if not redis_cache.enabled:
                return False, "Redis is disabled", {"enabled": False}

            # Test basic operations with timeout
            test_key = f"health_check_{uuid.uuid4().hex[:8]}"

            await asyncio.wait_for(
                redis_cache.set(test_key, "health_check_value", ttl=10),
                timeout=timeout_seconds,
            )

            await asyncio.wait_for(redis_cache.get(test_key), timeout=timeout_seconds)

            await asyncio.wait_for(
                redis_cache.delete(test_key), timeout=timeout_seconds
            )

            return True, None, {"operations": "set_get_delete_ok"}

        except Exception as e:
            return False, f"Redis health check failed: {str(e)}", {"error": str(e)}

    async def _check_database_health(
        self, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check database service health"""
        try:
            from app.core.database import AsyncSessionLocal

            # Test database connection with timeout and proper session management
            async def db_check():
                session = None
                try:
                    session = AsyncSessionLocal()
                    result = await session.execute("SELECT 1")
                    return result is not None
                finally:
                    if session:
                        await session.close()

            is_healthy = await asyncio.wait_for(db_check(), timeout=timeout_seconds)

            if is_healthy:
                return True, None, {"query": "SELECT 1 ok"}
            else:
                return False, "Database query failed", {}

        except Exception as e:
            return False, f"Database health check failed: {str(e)}", {"error": str(e)}

    async def _check_auth_cache_health(
        self, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check auth cache service health"""
        try:
            from app.services.caching.auth_cache_service import get_auth_cache_service

            auth_cache = get_auth_cache_service()

            # Use the built-in health check if available
            if hasattr(auth_cache, "health_check"):
                health_result = await asyncio.wait_for(
                    auth_cache.health_check(), timeout=timeout_seconds
                )

                is_healthy = health_result.get("status") in ["healthy", "warning"]
                error_message = (
                    None
                    if is_healthy
                    else f"Auth cache status: {health_result.get('status')}"
                )

                return is_healthy, error_message, health_result
            else:
                # Fallback basic check
                return True, None, {"basic_check": "ok"}

        except Exception as e:
            return False, f"Auth cache health check failed: {str(e)}", {"error": str(e)}

    async def _check_storage_manager_health(
        self, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check storage manager service health"""
        try:
            from app.services.storage.storage_manager import get_storage_manager

            storage_manager = get_storage_manager()

            # Use the built-in health check if available
            if hasattr(storage_manager, "health_check"):
                health_result = await asyncio.wait_for(
                    storage_manager.health_check(), timeout=timeout_seconds
                )

                is_healthy = health_result.get("status") in ["healthy", "warning"]
                error_message = (
                    None
                    if is_healthy
                    else f"Storage manager status: {health_result.get('status')}"
                )

                return is_healthy, error_message, health_result
            else:
                # Fallback basic check
                return (
                    storage_manager.enabled,
                    None if storage_manager.enabled else "Storage manager disabled",
                    {},
                )

        except Exception as e:
            return (
                False,
                f"Storage manager health check failed: {str(e)}",
                {"error": str(e)},
            )

    async def _check_llm_service_health(
        self, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check LLM service health"""
        try:
            # This would integrate with your LLM service
            # For now, return a basic check
            return (
                True,
                None,
                {"basic_check": "ok", "note": "LLM health check not implemented"},
            )

        except Exception as e:
            return (
                False,
                f"LLM service health check failed: {str(e)}",
                {"error": str(e)},
            )

    async def _check_embedding_service_health(
        self, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check embedding service health"""
        try:
            # Basic health check for embedding service
            return (
                True,
                None,
                {"basic_check": "ok", "note": "Embedding health check not implemented"},
            )

        except Exception as e:
            return (
                False,
                f"Embedding service health check failed: {str(e)}",
                {"error": str(e)},
            )

    async def _update_service_metrics(self, result: HealthCheckResult):
        """Update service metrics based on health check result"""
        service_type = result.service_type
        metrics = self.service_metrics[service_type]
        config = self.service_configs[service_type]
        circuit_breaker = self.circuit_breakers[service_type]

        # Update basic metrics
        metrics.response_time_ms = result.response_time_ms

        # Add to response time history
        self.response_times[service_type].append(result.response_time_ms)

        # Add to health history
        self.health_history[service_type].append(
            {
                "timestamp": result.timestamp,
                "is_healthy": result.is_healthy,
                "response_time_ms": result.response_time_ms,
                "error_message": result.error_message,
            }
        )

        # Update success/failure tracking
        if result.is_healthy:
            metrics.last_success = result.timestamp
            metrics.consecutive_successes += 1
            metrics.consecutive_failures = 0

            # Update circuit breaker for successful operation
            circuit_breaker.consecutive_successes += 1

            # Close circuit breaker if it was open and we have enough successes
            if (
                circuit_breaker.is_open
                and circuit_breaker.consecutive_successes >= config.success_threshold
            ):
                circuit_breaker.is_open = False
                circuit_breaker.failure_count = 0
                circuit_breaker.last_failure_time = None
                circuit_breaker.next_attempt_time = None
                logger.info(
                    f"Circuit breaker closed for {service_type} after successful health checks"
                )
        else:
            metrics.last_failure = result.timestamp
            metrics.consecutive_failures += 1
            metrics.consecutive_successes = 0
            metrics.error_count += 1

            # Update circuit breaker for failed operation
            circuit_breaker.failure_count += 1
            circuit_breaker.last_failure_time = result.timestamp
            circuit_breaker.consecutive_successes = 0

            # Open circuit breaker if threshold exceeded
            if (
                circuit_breaker.failure_count >= config.circuit_breaker_threshold
                and not circuit_breaker.is_open
            ):
                circuit_breaker.is_open = True
                circuit_breaker.next_attempt_time = result.timestamp + timedelta(
                    seconds=config.circuit_breaker_timeout_seconds
                )
                logger.warning(
                    f"Circuit breaker opened for {service_type} after {circuit_breaker.failure_count} failures"
                )

        # Update availability status
        metrics.is_available = (
            result.is_healthy
            and metrics.consecutive_failures < config.failure_threshold
        )

        metrics.circuit_breaker_open = circuit_breaker.is_open

        # Calculate success rate over recent history
        recent_checks = list(self.health_history[service_type])[-20:]  # Last 20 checks
        if recent_checks:
            successful_checks = sum(1 for check in recent_checks if check["is_healthy"])
            metrics.success_rate = (successful_checks / len(recent_checks)) * 100

        logger.debug(
            f"Updated metrics for {service_type}: "
            f"available={metrics.is_available}, "
            f"success_rate={metrics.success_rate:.1f}%, "
            f"response_time={metrics.response_time_ms:.1f}ms"
        )

    async def _check_alerts(self, service_type: ServiceType):
        """Check for alert conditions and generate alerts"""
        metrics = self.service_metrics[service_type]
        config = self.service_configs[service_type]

        alerts = []

        # Service unavailable alert
        if not metrics.is_available:
            alerts.append(
                {
                    "type": "service_unavailable",
                    "severity": "critical",
                    "message": f"{service_type} is unavailable",
                    "consecutive_failures": metrics.consecutive_failures,
                }
            )

        # Circuit breaker open alert
        if metrics.circuit_breaker_open:
            alerts.append(
                {
                    "type": "circuit_breaker_open",
                    "severity": "critical",
                    "message": f"Circuit breaker is open for {service_type}",
                    "failure_count": self.circuit_breakers[service_type].failure_count,
                }
            )

        # High response time alerts
        if metrics.response_time_ms > config.response_time_critical_ms:
            alerts.append(
                {
                    "type": "high_response_time",
                    "severity": "critical",
                    "message": f"{service_type} response time is critical: {metrics.response_time_ms:.1f}ms",
                    "threshold": config.response_time_critical_ms,
                }
            )
        elif metrics.response_time_ms > config.response_time_warning_ms:
            alerts.append(
                {
                    "type": "high_response_time",
                    "severity": "warning",
                    "message": f"{service_type} response time is high: {metrics.response_time_ms:.1f}ms",
                    "threshold": config.response_time_warning_ms,
                }
            )

        # Low success rate alert
        if metrics.success_rate < 80:
            alerts.append(
                {
                    "type": "low_success_rate",
                    "severity": "warning" if metrics.success_rate > 50 else "critical",
                    "message": f"{service_type} has low success rate: {metrics.success_rate:.1f}%",
                }
            )

        # Process alerts with cooldown
        for alert in alerts:
            alert_key = f"{service_type}:{alert['type']}"
            cooldown_end = self.alert_cooldowns.get(alert_key)

            if cooldown_end is None or datetime.utcnow() > cooldown_end:
                # Log alert
                log_level = (
                    logger.critical
                    if alert["severity"] == "critical"
                    else logger.warning
                )
                log_level(f"ALERT: {alert['message']}")

                # Set cooldown (5 minutes for critical, 15 minutes for warning)
                cooldown_minutes = 5 if alert["severity"] == "critical" else 15
                self.alert_cooldowns[alert_key] = datetime.utcnow() + timedelta(
                    minutes=cooldown_minutes
                )

                # Add to active alerts
                alert["timestamp"] = datetime.utcnow()
                alert["service_type"] = service_type
                self.active_alerts[service_type].append(alert)

        # Clean up old alerts (older than 1 hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        self.active_alerts[service_type] = [
            alert
            for alert in self.active_alerts[service_type]
            if alert["timestamp"] > cutoff_time
        ]

    async def get_service_health(
        self, service_type: ServiceType
    ) -> Optional[ServiceHealth]:
        """Get current health status for a specific service"""
        if service_type not in self.service_metrics:
            return ServiceHealth.UNKNOWN

        metrics = self.service_metrics[service_type]
        config = self.service_configs[service_type]

        # Determine health status based on multiple factors
        if metrics.circuit_breaker_open:
            return ServiceHealth.CRITICAL

        if not metrics.is_available:
            return ServiceHealth.CRITICAL

        if (
            metrics.success_rate < 80
            or metrics.response_time_ms > config.response_time_critical_ms
        ):
            return ServiceHealth.CRITICAL

        if (
            metrics.success_rate < 95
            or metrics.response_time_ms > config.response_time_warning_ms
            or metrics.consecutive_failures > 0
        ):
            return ServiceHealth.DEGRADED

        return ServiceHealth.HEALTHY

    async def get_system_health_status(self) -> SystemHealthStatus:
        """Get comprehensive system health status"""
        service_health = {}
        available_services = set()
        degraded_services = set()
        failed_services = set()

        # Evaluate each service
        for service_type in self.service_configs.keys():
            health = await self.get_service_health(service_type)
            service_health[service_type] = health

            if health == ServiceHealth.HEALTHY:
                available_services.add(service_type)
            elif health == ServiceHealth.DEGRADED:
                available_services.add(service_type)
                degraded_services.add(service_type)
            else:
                failed_services.add(service_type)

        # Determine overall system health
        overall_health = self._calculate_overall_health(
            available_services, degraded_services, failed_services
        )

        # Generate recommendations
        recommendations = self._generate_health_recommendations(
            service_health, failed_services, degraded_services
        )

        # Check if fallback systems are active
        fallback_active = len(failed_services) > 0
        emergency_mode = overall_health == SystemHealth.EMERGENCY_MODE

        self.last_system_health_check = datetime.utcnow()

        return SystemHealthStatus(
            overall_health=overall_health,
            service_health=service_health,
            available_services=available_services,
            degraded_services=degraded_services,
            failed_services=failed_services,
            fallback_active=fallback_active,
            emergency_mode=emergency_mode,
            recommendations=recommendations,
        )

    def _calculate_overall_health(
        self,
        available_services: Set[ServiceType],
        degraded_services: Set[ServiceType],
        failed_services: Set[ServiceType],
    ) -> SystemHealth:
        """Calculate overall system health based on service statuses"""
        total_services = len(self.service_configs)
        critical_services = {
            ServiceType.REDIS,
            ServiceType.DATABASE,
            ServiceType.AUTH_CACHE,
        }

        # Check critical services
        critical_failed = failed_services.intersection(critical_services)
        critical_degraded = degraded_services.intersection(critical_services)

        if len(critical_failed) >= 2:
            return SystemHealth.EMERGENCY_MODE

        if len(critical_failed) == 1 or len(failed_services) > total_services * 0.5:
            return SystemHealth.LIMITED_FUNCTIONALITY

        if len(degraded_services) > 0 or len(critical_degraded) > 0:
            return SystemHealth.DEGRADED_PERFORMANCE

        return SystemHealth.FULLY_OPERATIONAL

    def _generate_health_recommendations(
        self,
        service_health: Dict[ServiceType, ServiceHealth],
        failed_services: Set[ServiceType],
        degraded_services: Set[ServiceType],
    ) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []

        # Critical service failures
        if ServiceType.REDIS in failed_services:
            recommendations.append(
                "Redis service is down - fallback to in-memory cache active. "
                "Check Redis configuration and network connectivity."
            )

        if ServiceType.DATABASE in failed_services:
            recommendations.append(
                "Database service is down - system in emergency mode. "
                "Check database server status and connection parameters."
            )

        if ServiceType.AUTH_CACHE in failed_services:
            recommendations.append(
                "Auth cache service is down - authentication performance degraded. "
                "Check cache service configuration and dependencies."
            )

        # Degraded services
        if degraded_services:
            service_list = ", ".join(s.value for s in degraded_services)
            recommendations.append(
                f"Services operating in degraded mode: {service_list}. "
                "Monitor performance metrics and consider scaling resources."
            )

        # Performance recommendations
        high_response_time_services = []
        for service_type, metrics in self.service_metrics.items():
            config = self.service_configs[service_type]
            if metrics.response_time_ms > config.response_time_warning_ms:
                high_response_time_services.append(service_type.value)

        if high_response_time_services:
            recommendations.append(
                f"High response times detected: {', '.join(high_response_time_services)}. "
                "Consider optimizing queries or scaling resources."
            )

        # Circuit breaker recommendations
        open_circuits = [
            service_type.value
            for service_type, cb in self.circuit_breakers.items()
            if cb.is_open
        ]

        if open_circuits:
            recommendations.append(
                f"Circuit breakers open for: {', '.join(open_circuits)}. "
                "Services will automatically retry after configured timeout period."
            )

        if not recommendations:
            recommendations.append("All systems operating normally.")

        return recommendations

    async def get_service_metrics(
        self, service_type: ServiceType
    ) -> Optional[HealthMetrics]:
        """Get detailed metrics for a specific service"""
        return self.service_metrics.get(service_type)

    async def get_all_metrics(self) -> Dict[ServiceType, HealthMetrics]:
        """Get metrics for all monitored services"""
        return self.service_metrics.copy()

    async def reset_circuit_breaker(self, service_type: ServiceType) -> bool:
        """Manually reset a circuit breaker"""
        if service_type in self.circuit_breakers:
            self.circuit_breakers[service_type] = CircuitBreakerState()
            logger.info(f"Circuit breaker reset for {service_type}")
            return True
        return False

    async def is_service_available(self, service_type: ServiceType) -> bool:
        """Check if a service is currently available"""
        metrics = self.service_metrics.get(service_type)
        if not metrics:
            return False

        circuit_breaker = self.circuit_breakers.get(service_type)
        if circuit_breaker and circuit_breaker.is_open:
            return False

        return metrics.is_available

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all services"""
        summary = {
            "system_uptime_seconds": (
                datetime.utcnow() - self.system_start_time
            ).total_seconds(),
            "last_health_check": self.last_system_health_check.isoformat(),
            "services": {},
            "alerts": {
                "active_count": sum(
                    len(alerts) for alerts in self.active_alerts.values()
                ),
                "critical_count": sum(
                    len([a for a in alerts if a["severity"] == "critical"])
                    for alerts in self.active_alerts.values()
                ),
            },
        }

        for service_type, metrics in self.service_metrics.items():
            config = self.service_configs[service_type]
            response_times = list(self.response_times[service_type])

            service_summary = {
                "health": (await self.get_service_health(service_type)).value,
                "is_available": metrics.is_available,
                "success_rate": metrics.success_rate,
                "consecutive_failures": metrics.consecutive_failures,
                "circuit_breaker_open": metrics.circuit_breaker_open,
                "response_time": {
                    "current_ms": metrics.response_time_ms,
                    "average_ms": (
                        sum(response_times) / len(response_times)
                        if response_times
                        else 0
                    ),
                    "warning_threshold_ms": config.response_time_warning_ms,
                    "critical_threshold_ms": config.response_time_critical_ms,
                },
                "last_success": (
                    metrics.last_success.isoformat() if metrics.last_success else None
                ),
                "last_failure": (
                    metrics.last_failure.isoformat() if metrics.last_failure else None
                ),
            }

            summary["services"][service_type.value] = service_summary

        return summary

    async def shutdown(self):
        """Gracefully shutdown the service health manager"""
        logger.info("Shutting down ServiceHealthManager...")

        self.enabled = False

        # Cancel all health check tasks
        for service_type, task in self.health_check_tasks.items():
            if task and not task.done():
                task.cancel()
                logger.debug(f"Cancelled health check task for {service_type}")

        # Wait for tasks to complete
        await asyncio.sleep(0.1)

        logger.info("ServiceHealthManager shutdown complete")


# Singleton instance
_service_health_manager_instance: Optional[ServiceHealthManager] = None


def get_service_health_manager() -> ServiceHealthManager:
    """Get singleton ServiceHealthManager instance"""
    global _service_health_manager_instance
    if _service_health_manager_instance is None:
        _service_health_manager_instance = ServiceHealthManager()
    return _service_health_manager_instance


# Cleanup function for app shutdown
async def shutdown_service_health_manager():
    """Shutdown service health manager (call during app shutdown)"""
    global _service_health_manager_instance
    if _service_health_manager_instance:
        await _service_health_manager_instance.shutdown()
        _service_health_manager_instance = None
