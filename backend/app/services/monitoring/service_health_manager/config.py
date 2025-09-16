"""
Configuration module for Service Health Manager

Contains default configurations and service registration logic.
"""

from typing import Dict

from .base import ServiceConfig, ServiceType


class ServiceHealthConfig:
    """Configuration manager for service health monitoring"""

    @staticmethod
    def get_default_configs() -> Dict[ServiceType, ServiceConfig]:
        """Get default configurations for all monitored services"""
        return {
            ServiceType.REDIS: ServiceConfig(
                service_type=ServiceType.REDIS,
                health_check_interval_seconds=30,
                timeout_seconds=5,
                failure_threshold=3,
                circuit_breaker_threshold=5,
                critical_service=True,
            ),
            ServiceType.DATABASE: ServiceConfig(
                service_type=ServiceType.DATABASE,
                health_check_interval_seconds=60,
                timeout_seconds=10,
                failure_threshold=3,
                circuit_breaker_threshold=5,
                critical_service=True,
            ),
            ServiceType.AUTH_CACHE: ServiceConfig(
                service_type=ServiceType.AUTH_CACHE,
                health_check_interval_seconds=30,
                timeout_seconds=5,
                failure_threshold=3,
                circuit_breaker_threshold=5,
                critical_service=True,
            ),
            ServiceType.STORAGE_MANAGER: ServiceConfig(
                service_type=ServiceType.STORAGE_MANAGER,
                health_check_interval_seconds=30,
                timeout_seconds=5,
                failure_threshold=3,
                circuit_breaker_threshold=5,
                critical_service=False,
            ),
            ServiceType.LLM_SERVICE: ServiceConfig(
                service_type=ServiceType.LLM_SERVICE,
                health_check_interval_seconds=120,
                timeout_seconds=30,
                failure_threshold=5,
                circuit_breaker_threshold=10,
                critical_service=False,
            ),
            ServiceType.EMBEDDING_SERVICE: ServiceConfig(
                service_type=ServiceType.EMBEDDING_SERVICE,
                health_check_interval_seconds=120,
                timeout_seconds=30,
                failure_threshold=5,
                circuit_breaker_threshold=10,
                critical_service=False,
            ),
        }
