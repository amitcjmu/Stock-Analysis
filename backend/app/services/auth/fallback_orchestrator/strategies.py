"""
Fallback Strategy Methods

This module contains the strategy execution logic for determining
optimal fallback sequences based on performance, reliability, and
service health metrics.
"""

from typing import Dict, List, Optional, Tuple, Any

from app.core.logging import get_logger
from app.services.monitoring.service_health_manager import (
    ServiceHealthManager,
    ServiceType,
)

from .base import (
    FallbackConfig,
    FallbackLevel,
    FallbackStrategy,
    ServiceLevelMapping,
    OperationType,
)

logger = get_logger(__name__)


class FallbackStrategyManager:
    """Manages fallback strategy execution and routing decisions"""

    def __init__(self, health_manager: ServiceHealthManager):
        self.health_manager = health_manager

    async def determine_fallback_sequence(
        self,
        operation_type: OperationType,
        config: FallbackConfig,
        mapping: ServiceLevelMapping,
        context_data: Optional[Dict[str, Any]],
    ) -> List[Tuple[FallbackLevel, List[ServiceType]]]:
        """Determine the optimal fallback sequence based on strategy and health"""

        if config.strategy == FallbackStrategy.EMERGENCY_ONLY:
            return [(FallbackLevel.EMERGENCY, [])]

        # Get current system health
        await self.health_manager.get_system_health_status()

        # Base sequence
        base_sequence = [
            (FallbackLevel.PRIMARY, mapping.primary_services),
            (FallbackLevel.SECONDARY, mapping.secondary_services),
            (FallbackLevel.TERTIARY, mapping.tertiary_services),
        ]

        # Filter and reorder based on strategy
        if config.strategy == FallbackStrategy.FAIL_FAST:
            # Only try primary level
            return [base_sequence[0]]

        elif config.strategy == FallbackStrategy.PERFORMANCE_FIRST:
            # Reorder based on current performance metrics
            return await self._reorder_by_performance(base_sequence, config)

        elif config.strategy == FallbackStrategy.RELIABILITY_FIRST:
            # Reorder based on reliability metrics
            return await self._reorder_by_reliability(base_sequence, config)

        else:  # GRACEFUL_DEGRADATION
            # Filter out completely unavailable services
            filtered_sequence = []
            for level, services in base_sequence:
                available_services = []
                for service in services:
                    if await self.health_manager.is_service_available(service):
                        available_services.append(service)

                if available_services or level == FallbackLevel.TERTIARY:
                    # Always include tertiary as last resort
                    filtered_sequence.append((level, available_services or services))

            return filtered_sequence

    async def _reorder_by_performance(
        self,
        sequence: List[Tuple[FallbackLevel, List[ServiceType]]],
        config: FallbackConfig,
    ) -> List[Tuple[FallbackLevel, List[ServiceType]]]:
        """Reorder sequence based on performance metrics"""
        level_performance = {}

        for level, services in sequence:
            total_response_time = 0.0
            available_count = 0

            for service in services:
                metrics = await self.health_manager.get_service_metrics(service)
                if metrics and metrics.is_available:
                    total_response_time += metrics.response_time_ms
                    available_count += 1

            if available_count > 0:
                avg_response_time = total_response_time / available_count
                level_performance[level] = avg_response_time
            else:
                level_performance[level] = float(
                    "inf"
                )  # Unavailable services get worst score

        # Sort by performance (lower response time is better)
        sorted_levels = sorted(level_performance.items(), key=lambda x: x[1])

        # Rebuild sequence maintaining service mappings
        reordered_sequence = []
        level_to_services = dict(sequence)

        for level_item, _ in sorted_levels:
            services = level_to_services[level_item]
            # Only include if performance is acceptable
            if level_performance[level_item] <= config.performance_threshold_ms:
                reordered_sequence.append((level_item, services))

        # Add remaining levels as fallback, sorted by performance
        remaining_levels = []
        for level, services in sequence:
            if not any(level_item == level for level_item, _ in reordered_sequence):
                remaining_levels.append((level, services, level_performance[level]))

        # Sort remaining levels by performance and add them
        remaining_levels.sort(key=lambda x: x[2])  # Sort by performance score
        for level, services, _ in remaining_levels:
            reordered_sequence.append((level, services))

        return reordered_sequence

    async def _reorder_by_reliability(
        self,
        sequence: List[Tuple[FallbackLevel, List[ServiceType]]],
        config: FallbackConfig,
    ) -> List[Tuple[FallbackLevel, List[ServiceType]]]:
        """Reorder sequence based on reliability metrics"""
        level_reliability = {}

        for level, services in sequence:
            total_success_rate = 0.0
            available_count = 0

            for service in services:
                metrics = await self.health_manager.get_service_metrics(service)
                if metrics and metrics.is_available:
                    total_success_rate += metrics.success_rate
                    available_count += 1

            if available_count > 0:
                avg_success_rate = total_success_rate / available_count
                level_reliability[level] = avg_success_rate
            else:
                level_reliability[level] = 0.0  # Unavailable services get worst score

        # Sort by reliability (higher success rate is better)
        sorted_levels = sorted(
            level_reliability.items(), key=lambda x: x[1], reverse=True
        )

        # Rebuild sequence maintaining service mappings
        reordered_sequence = []
        level_to_services = dict(sequence)

        for level_item, _ in sorted_levels:
            services = level_to_services[level_item]
            # Only include if reliability is acceptable
            if level_reliability[level_item] >= config.reliability_threshold_percent:
                reordered_sequence.append((level_item, services))

        # Add remaining levels as fallback, sorted by reliability
        remaining_levels = []
        for level, services in sequence:
            if not any(level_item == level for level_item, _ in reordered_sequence):
                remaining_levels.append((level, services, level_reliability[level]))

        # Sort remaining levels by reliability (higher is better) and add them
        remaining_levels.sort(
            key=lambda x: x[2], reverse=True
        )  # Sort by reliability score
        for level, services, _ in remaining_levels:
            reordered_sequence.append((level, services))

        return reordered_sequence

    async def should_skip_level(
        self, level: FallbackLevel, services: List[ServiceType], config: FallbackConfig
    ) -> bool:
        """Determine if a fallback level should be skipped"""
        if not services:
            return True

        # Skip if all services in this level have open circuit breakers
        all_circuits_open = True
        for service in services:
            if await self.health_manager.is_service_available(service):
                all_circuits_open = False
                break

        if all_circuits_open:
            logger.debug(f"Skipping {level} level - all circuit breakers open")
            return True

        return False
