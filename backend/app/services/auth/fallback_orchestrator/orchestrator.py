"""
Main Fallback Orchestrator Class

This module contains the core FallbackOrchestrator class that coordinates
smart routing and fallback coordination for the auth performance optimization system.
"""

import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from app.core.logging import get_logger
from app.services.monitoring.service_health_manager import (
    ServiceHealthManager,
    ServiceType,
    get_service_health_manager,
)

from .base import (
    FallbackConfig,
    FallbackLevel,
    FallbackResult,
    OperationType,
    ServiceLevelMapping,
)
from .configs import DefaultConfigurationManager
from .handlers import EmergencyHandlerManager, LevelExecutor
from .strategies import FallbackStrategyManager

logger = get_logger(__name__)


class FallbackOrchestrator:
    """
    Fallback Orchestrator for Smart Service Routing

    Coordinates fallback between service layers based on health status, performance
    metrics, and operation context to ensure optimal user experience during failures.
    """

    def __init__(self, health_manager: Optional[ServiceHealthManager] = None):
        self.health_manager = health_manager or get_service_health_manager()

        # Fallback configurations by operation type
        self.fallback_configs: Dict[OperationType, FallbackConfig] = {}

        # Service level mappings
        self.service_mappings: Dict[OperationType, ServiceLevelMapping] = {}

        # Performance tracking
        self.performance_history: Dict[str, List[float]] = defaultdict(list)
        self.fallback_stats: Dict[FallbackLevel, Dict[str, int]] = defaultdict(
            lambda: {"attempts": 0, "successes": 0, "failures": 0}
        )

        # Recovery tracking
        self.service_recovery_times: Dict[ServiceType, datetime] = {}
        self.last_successful_levels: Dict[OperationType, FallbackLevel] = {}

        # Component managers
        self.strategy_manager = FallbackStrategyManager(self.health_manager)
        self.emergency_handler_manager = EmergencyHandlerManager()
        self.level_executor = LevelExecutor(self.health_manager)

        # Initialize default configurations
        self._initialize_default_configs()

        logger.info("FallbackOrchestrator initialized with smart routing capabilities")

    def _initialize_default_configs(self):
        """Initialize default fallback configurations"""
        configs, mappings = DefaultConfigurationManager.get_default_configs(
            self.emergency_handler_manager
        )

        for operation_type, config in configs.items():
            mapping = mappings[operation_type]
            self.register_operation_config(operation_type, config, mapping)

    def register_operation_config(
        self,
        operation_type: OperationType,
        config: FallbackConfig,
        mapping: ServiceLevelMapping,
    ):
        """Register fallback configuration for an operation type"""
        self.fallback_configs[operation_type] = config
        self.service_mappings[operation_type] = mapping

        logger.debug(f"Registered fallback config for {operation_type}")

    async def execute_with_fallback(
        self,
        operation_type: OperationType,
        operation_func: Callable,
        *args,
        context_data: Optional[Dict[str, Any]] = None,
        custom_config: Optional[FallbackConfig] = None,
        **kwargs,
    ) -> FallbackResult:
        """
        Execute an operation with intelligent fallback handling

        Args:
            operation_type: Type of operation being performed
            operation_func: Function to execute at each service level
            *args: Arguments for the operation function
            context_data: Additional context for routing decisions
            custom_config: Custom fallback configuration
            **kwargs: Keyword arguments for the operation function

        Returns:
            FallbackResult with success status, value, and attempt details
        """
        start_time = time.time()
        config = custom_config or self.fallback_configs.get(
            operation_type, FallbackConfig(operation_type=operation_type)
        )
        mapping = self.service_mappings.get(operation_type, ServiceLevelMapping())

        result = FallbackResult(success=False)

        try:
            # Determine fallback sequence based on strategy and current health
            fallback_sequence = await self.strategy_manager.determine_fallback_sequence(
                operation_type, config, mapping, context_data
            )

            logger.debug(
                f"Starting fallback execution for {operation_type} with sequence: {fallback_sequence}"
            )

            # Execute fallback sequence
            for level, services in fallback_sequence:
                if await self.strategy_manager.should_skip_level(
                    level, services, config
                ):
                    continue

                level_result = await self.level_executor.execute_level(
                    level, services, operation_func, args, kwargs, config, context_data
                )

                result.attempts.extend(level_result.attempts)
                result.total_attempts += level_result.total_attempts

                if level_result.success:
                    result.success = True
                    result.value = level_result.value
                    result.level_used = level
                    result.service_used = level_result.service_used
                    result.fallback_active = level != FallbackLevel.PRIMARY

                    # Track successful level for future optimizations
                    self.last_successful_levels[operation_type] = level

                    # Update recovery tracking if service recovered
                    if level == FallbackLevel.PRIMARY and result.fallback_active:
                        await self._track_service_recovery(services)

                    break
                else:
                    # Continue to next level
                    result.error_message = level_result.error_message
                    continue

            # If all levels failed, try emergency handler
            if not result.success and mapping.emergency_handler:
                try:
                    emergency_start = time.time()
                    emergency_value = (
                        await self.emergency_handler_manager.execute_emergency_handler(
                            mapping.emergency_handler, args, kwargs, context_data
                        )
                    )
                    (time.time() - emergency_start) * 1000

                    if emergency_value is not None:
                        result.success = True
                        result.value = emergency_value
                        result.level_used = FallbackLevel.EMERGENCY
                        result.fallback_active = True

                        logger.info(f"Emergency handler succeeded for {operation_type}")

                except Exception as e:
                    logger.error(f"Emergency handler failed for {operation_type}: {e}")
                    result.error_message = (
                        f"All fallback levels failed, emergency handler error: {str(e)}"
                    )

            # Calculate total execution time
            result.total_time_ms = (time.time() - start_time) * 1000

            # Update statistics
            await self._update_fallback_stats(result)

            # Log result
            if result.success:
                logger.info(
                    f"Fallback execution succeeded for {operation_type} "
                    f"using {result.level_used} level in {result.total_time_ms:.1f}ms "
                    f"after {result.total_attempts} attempts"
                )
            else:
                logger.error(
                    f"Fallback execution failed for {operation_type} "
                    f"after {result.total_attempts} attempts in {result.total_time_ms:.1f}ms: "
                    f"{result.error_message}"
                )

            return result

        except Exception as e:
            result.total_time_ms = (time.time() - start_time) * 1000
            result.error_message = f"Fallback orchestration error: {str(e)}"
            logger.error(f"Fallback orchestration failed for {operation_type}: {e}")
            return result

    def _track_performance(self, service: ServiceType, response_time_ms: float):
        """Track performance metrics for service optimization"""
        service_key = service.value
        self.performance_history[service_key].append(response_time_ms)

        # Keep only recent history (last 100 measurements)
        if len(self.performance_history[service_key]) > 100:
            self.performance_history[service_key] = self.performance_history[
                service_key
            ][-100:]

    async def _track_service_recovery(self, services: List[ServiceType]):
        """Track service recovery for optimization"""
        current_time = datetime.utcnow()

        for service in services:
            self.service_recovery_times[service] = current_time
            logger.info(f"Service recovery detected for {service}")

    async def _update_fallback_stats(self, result: FallbackResult):
        """Update fallback statistics"""
        if result.level_used:
            level_stats = self.fallback_stats[result.level_used]
            level_stats["attempts"] += 1

            if result.success:
                level_stats["successes"] += 1
            else:
                level_stats["failures"] += 1

    # Public interface methods

    async def get_optimal_service(
        self, operation_type: OperationType
    ) -> Optional[ServiceType]:
        """Get the currently optimal service for an operation type"""
        config = self.fallback_configs.get(operation_type)
        mapping = self.service_mappings.get(operation_type)

        if not config or not mapping:
            return None

        sequence = await self.strategy_manager.determine_fallback_sequence(
            operation_type, config, mapping, None
        )

        for level, services in sequence:
            for service in services:
                if await self.health_manager.is_service_available(service):
                    return service

        return None

    async def get_fallback_status(self) -> Dict[str, Any]:
        """Get comprehensive fallback system status"""
        system_health = await self.health_manager.get_system_health_status()

        status = {
            "system_health": system_health.overall_health.value,
            "fallback_active": system_health.fallback_active,
            "emergency_mode": system_health.emergency_mode,
            "operation_configs": {
                op_type.value: {
                    "strategy": config.strategy.value,
                    "timeout_seconds": config.timeout_per_level_seconds,
                    "circuit_breaker_enabled": config.circuit_breaker_enabled,
                }
                for op_type, config in self.fallback_configs.items()
            },
            "fallback_statistics": {
                level.value: {
                    "attempts": stats["attempts"],
                    "success_rate": (stats["successes"] / max(stats["attempts"], 1))
                    * 100,
                    "failures": stats["failures"],
                }
                for level, stats in self.fallback_stats.items()
            },
            "service_performance": {},
            "emergency_cache_size": len(self.emergency_handler_manager.emergency_cache),
            "last_successful_levels": {
                op_type.value: level.value
                for op_type, level in self.last_successful_levels.items()
            },
        }

        # Add service performance metrics
        for service_type in ServiceType:
            metrics = await self.health_manager.get_service_metrics(service_type)
            if metrics:
                performance_history = self.performance_history.get(
                    service_type.value, []
                )
                avg_response_time = (
                    sum(performance_history) / len(performance_history)
                    if performance_history
                    else 0
                )

                status["service_performance"][service_type.value] = {
                    "is_available": metrics.is_available,
                    "success_rate": metrics.success_rate,
                    "current_response_time_ms": metrics.response_time_ms,
                    "average_response_time_ms": avg_response_time,
                    "circuit_breaker_open": metrics.circuit_breaker_open,
                }

        return status

    async def clear_emergency_cache(self) -> int:
        """Clear emergency cache and return number of items cleared"""
        return await self.emergency_handler_manager.clear_emergency_cache()

    async def reset_fallback_stats(self):
        """Reset fallback statistics"""
        self.fallback_stats.clear()
        self.performance_history.clear()
        self.last_successful_levels.clear()

        logger.info("Reset fallback statistics")
