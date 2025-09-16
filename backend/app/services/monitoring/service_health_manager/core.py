"""
Core Service Health Manager

Main manager class that orchestrates all health monitoring services and provides
the primary interface for service health monitoring functionality.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict

from app.core.logging import get_logger

from .base import (
    HealthCheckResult,
    ServiceConfig,
    ServiceHealth,
    ServiceType,
    SystemHealthStatus,
)
from .circuit_breaker import CircuitBreakerManager
from .config import ServiceHealthConfig
from .health_checks import HealthCheckService
from .metrics import MetricsManager
from .utils import HealthUtils

logger = get_logger(__name__)


class ServiceHealthManager:
    """
    Service Health Manager

    Comprehensive service health monitoring with circuit breakers for the auth performance
    optimization system. Provides multi-layered health monitoring, circuit breaker patterns,
    and service availability tracking to ensure graceful degradation during failures.
    """

    def __init__(self):
        self.enabled = True

        # Core components
        self.circuit_breaker_manager = CircuitBreakerManager()
        self.health_check_service = HealthCheckService()
        self.metrics_manager = MetricsManager()

        # Configuration and state
        self.service_configs: Dict[ServiceType, ServiceConfig] = {}
        self.health_check_tasks: Dict[ServiceType, asyncio.Task] = {}
        self.last_system_health_check = datetime.utcnow()

        # Initialize default configurations
        self._initialize_default_configs()

        logger.info("ServiceHealthManager initialized")

    def _initialize_default_configs(self):
        """Initialize default configurations for monitored services"""
        default_configs = ServiceHealthConfig.get_default_configs()

        for service_type, config in default_configs.items():
            self.register_service(config)

    def register_service(self, config: ServiceConfig) -> bool:
        """Register a service for health monitoring"""
        try:
            self.service_configs[config.service_type] = config

            # Initialize components for this service
            self.metrics_manager.initialize_metrics(config.service_type)
            self.circuit_breaker_manager.initialize_circuit_breaker(config.service_type)

            # Start health check task if enabled
            if self.enabled:
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

        while self.enabled:
            try:
                # Perform health check
                result = await self._perform_health_check(service_type)

                # Update metrics and circuit breaker state
                await self.metrics_manager.update_service_metrics(result, config)
                self.circuit_breaker_manager.update_circuit_breaker(
                    service_type, result, config
                )

                # Check for alerts
                await self.metrics_manager.check_alerts(service_type, config)

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
            circuit_result = self.circuit_breaker_manager.check_circuit_breaker_state(
                service_type, config
            )
            if circuit_result:
                return circuit_result

            # Perform actual health check
            is_healthy, error_message, additional_data = (
                await self.health_check_service.execute_health_check(
                    service_type, config.timeout_seconds
                )
            )

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                service_type=service_type,
                is_healthy=is_healthy,
                response_time_ms=response_time,
                error_message=error_message,
                additional_data=additional_data,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Health check failed for {service_type}: {e}")

            return HealthCheckResult(
                service_type=service_type,
                is_healthy=False,
                response_time_ms=response_time,
                error_message=str(e),
                additional_data={"exception": type(e).__name__},
            )

    async def get_service_health(self, service_type: ServiceType) -> ServiceHealth:
        """Get health status for a specific service"""
        return self.metrics_manager.get_service_health_status(service_type)

    async def get_system_health_status(self) -> SystemHealthStatus:
        """Get comprehensive system health status"""
        service_statuses = {}
        unhealthy_services = []
        degraded_services = []

        # Evaluate each service
        for service_type in self.service_configs.keys():
            health = await self.get_service_health(service_type)
            service_statuses[service_type] = health

            if health == ServiceHealth.CRITICAL:
                unhealthy_services.append(service_type)
            elif health == ServiceHealth.DEGRADED:
                degraded_services.append(service_type)

        # Determine overall system health
        overall_health = HealthUtils.calculate_overall_health(
            self.service_configs, unhealthy_services, degraded_services
        )

        # Generate recommendations
        recommendations = HealthUtils.generate_health_recommendations(
            service_statuses, unhealthy_services, degraded_services
        )

        self.last_system_health_check = datetime.utcnow()

        return SystemHealthStatus(
            overall_health=overall_health,
            timestamp=self.last_system_health_check,
            service_statuses=service_statuses,
            unhealthy_services=unhealthy_services,
            degraded_services=degraded_services,
            recommendations=recommendations,
        )

    async def get_service_metrics(self, service_type: ServiceType):
        """Get metrics for a specific service"""
        return self.metrics_manager.get_service_metrics(service_type)

    async def get_all_metrics(self):
        """Get metrics for all monitored services"""
        return await self.metrics_manager.get_all_metrics()

    async def reset_circuit_breaker(self, service_type: ServiceType) -> bool:
        """Reset circuit breaker for a service"""
        return self.circuit_breaker_manager.reset_circuit_breaker(service_type)

    async def is_service_available(self, service_type: ServiceType) -> bool:
        """Check if a service is available"""
        return self.circuit_breaker_manager.is_service_available(service_type)

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all services"""
        return await self.metrics_manager.get_performance_summary()

    async def shutdown(self):
        """Shutdown the health manager and cancel all tasks"""
        logger.info("Shutting down ServiceHealthManager...")

        self.enabled = False

        # Cancel all health check tasks
        for task in self.health_check_tasks.values():
            if task and not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self.health_check_tasks:
            await asyncio.gather(
                *self.health_check_tasks.values(), return_exceptions=True
            )

        logger.info("ServiceHealthManager shutdown complete")
