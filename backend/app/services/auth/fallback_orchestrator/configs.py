"""
Default Configuration Setup

This module contains the default fallback configurations for different
operation types and service level mappings.
"""

from app.services.monitoring.service_health_manager import ServiceType

from .base import (
    FallbackConfig,
    FallbackStrategy,
    OperationType,
    ServiceLevelMapping,
)


class DefaultConfigurationManager:
    """Manages default fallback configurations"""

    @staticmethod
    def get_default_configs(emergency_handler_manager):
        """Get default fallback configurations for all operation types"""
        configs = {}
        mappings = {}

        # User session operations - high performance priority
        configs[OperationType.USER_SESSION] = FallbackConfig(
            operation_type=OperationType.USER_SESSION,
            strategy=FallbackStrategy.PERFORMANCE_FIRST,
            timeout_per_level_seconds=2.0,
            performance_threshold_ms=500.0,
        )
        mappings[OperationType.USER_SESSION] = ServiceLevelMapping(
            primary_services=[ServiceType.REDIS],
            secondary_services=[ServiceType.AUTH_CACHE],
            tertiary_services=[ServiceType.DATABASE],
            emergency_handler=emergency_handler_manager.get_emergency_user_session,
        )

        # User context operations - graceful degradation
        configs[OperationType.USER_CONTEXT] = FallbackConfig(
            operation_type=OperationType.USER_CONTEXT,
            strategy=FallbackStrategy.GRACEFUL_DEGRADATION,
            timeout_per_level_seconds=3.0,
        )
        mappings[OperationType.USER_CONTEXT] = ServiceLevelMapping(
            primary_services=[ServiceType.REDIS],
            secondary_services=[ServiceType.AUTH_CACHE],
            tertiary_services=[ServiceType.DATABASE],
            emergency_handler=emergency_handler_manager.get_emergency_user_context,
        )

        # Authentication operations - reliability first
        configs[OperationType.AUTHENTICATION] = FallbackConfig(
            operation_type=OperationType.AUTHENTICATION,
            strategy=FallbackStrategy.RELIABILITY_FIRST,
            timeout_per_level_seconds=5.0,
            reliability_threshold_percent=99.0,
        )
        mappings[OperationType.AUTHENTICATION] = ServiceLevelMapping(
            primary_services=[ServiceType.AUTH_CACHE, ServiceType.REDIS],
            secondary_services=[ServiceType.DATABASE],
            tertiary_services=[ServiceType.DATABASE],
            emergency_handler=emergency_handler_manager.get_emergency_auth_response,
        )

        # Client data operations - balanced approach
        configs[OperationType.CLIENT_DATA] = FallbackConfig(
            operation_type=OperationType.CLIENT_DATA,
            strategy=FallbackStrategy.GRACEFUL_DEGRADATION,
            timeout_per_level_seconds=4.0,
        )
        mappings[OperationType.CLIENT_DATA] = ServiceLevelMapping(
            primary_services=[ServiceType.REDIS],
            secondary_services=[ServiceType.AUTH_CACHE],
            tertiary_services=[ServiceType.DATABASE],
            emergency_handler=emergency_handler_manager.get_emergency_client_data,
        )

        # Cache read operations - performance optimized
        configs[OperationType.CACHE_READ] = FallbackConfig(
            operation_type=OperationType.CACHE_READ,
            strategy=FallbackStrategy.PERFORMANCE_FIRST,
            timeout_per_level_seconds=1.0,
            performance_threshold_ms=200.0,
        )
        mappings[OperationType.CACHE_READ] = ServiceLevelMapping(
            primary_services=[ServiceType.REDIS],
            secondary_services=[ServiceType.AUTH_CACHE],
            emergency_handler=lambda key: None,  # Cache miss is acceptable
        )

        # Cache write operations - graceful degradation
        configs[OperationType.CACHE_WRITE] = FallbackConfig(
            operation_type=OperationType.CACHE_WRITE,
            strategy=FallbackStrategy.GRACEFUL_DEGRADATION,
            timeout_per_level_seconds=2.0,
        )
        mappings[OperationType.CACHE_WRITE] = ServiceLevelMapping(
            primary_services=[ServiceType.REDIS],
            secondary_services=[
                ServiceType.AUTH_CACHE,
                ServiceType.STORAGE_MANAGER,
            ],
            emergency_handler=lambda key, value: True,  # Silent failure acceptable
        )

        return configs, mappings
