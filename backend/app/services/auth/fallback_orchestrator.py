"""
Fallback Orchestrator

Smart routing and fallback coordination for the auth performance optimization system.
Provides intelligent routing between service layers with graceful degradation patterns
and automatic service recovery detection.

Key Features:
- Multi-layered fallback hierarchy (Redis → In-Memory → Database → Static)
- Smart routing based on service health and performance metrics
- Automatic service recovery detection and restoration
- Performance-aware load balancing across available services
- Context-aware fallback strategies for different operation types
- Integration with service health monitoring and circuit breakers

Fallback Hierarchy:
1. Primary: Redis Cache (optimal performance)
2. Secondary: In-Memory Cache (degraded performance)
3. Tertiary: Direct Database Access (emergency mode)
4. Emergency: Default/Static Data (minimal functionality)

Architecture:
The FallbackOrchestrator coordinates between service layers based on real-time health
status, performance metrics, and operation context to ensure optimal user experience
during service failures while maintaining system functionality.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core.logging import get_logger
from app.services.monitoring.service_health_manager import (
    ServiceHealthManager,
    ServiceType,
    get_service_health_manager,
)

logger = get_logger(__name__)


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

        # Emergency data cache
        self.emergency_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.emergency_cache_lock = asyncio.Lock()

        # Recovery tracking
        self.service_recovery_times: Dict[ServiceType, datetime] = {}
        self.last_successful_levels: Dict[OperationType, FallbackLevel] = {}

        # Initialize default configurations
        self._initialize_default_configs()

        logger.info("FallbackOrchestrator initialized with smart routing capabilities")

    def _initialize_default_configs(self):
        """Initialize default fallback configurations"""
        # User session operations - high performance priority
        self.register_operation_config(
            OperationType.USER_SESSION,
            FallbackConfig(
                operation_type=OperationType.USER_SESSION,
                strategy=FallbackStrategy.PERFORMANCE_FIRST,
                timeout_per_level_seconds=2.0,
                performance_threshold_ms=500.0,
            ),
            ServiceLevelMapping(
                primary_services=[ServiceType.REDIS],
                secondary_services=[ServiceType.AUTH_CACHE],
                tertiary_services=[ServiceType.DATABASE],
                emergency_handler=self._get_emergency_user_session,
            ),
        )

        # User context operations - graceful degradation
        self.register_operation_config(
            OperationType.USER_CONTEXT,
            FallbackConfig(
                operation_type=OperationType.USER_CONTEXT,
                strategy=FallbackStrategy.GRACEFUL_DEGRADATION,
                timeout_per_level_seconds=3.0,
            ),
            ServiceLevelMapping(
                primary_services=[ServiceType.REDIS],
                secondary_services=[ServiceType.AUTH_CACHE],
                tertiary_services=[ServiceType.DATABASE],
                emergency_handler=self._get_emergency_user_context,
            ),
        )

        # Authentication operations - reliability first
        self.register_operation_config(
            OperationType.AUTHENTICATION,
            FallbackConfig(
                operation_type=OperationType.AUTHENTICATION,
                strategy=FallbackStrategy.RELIABILITY_FIRST,
                timeout_per_level_seconds=5.0,
                reliability_threshold_percent=99.0,
            ),
            ServiceLevelMapping(
                primary_services=[ServiceType.AUTH_CACHE, ServiceType.REDIS],
                secondary_services=[ServiceType.DATABASE],
                tertiary_services=[ServiceType.DATABASE],
                emergency_handler=self._get_emergency_auth_response,
            ),
        )

        # Client data operations - balanced approach
        self.register_operation_config(
            OperationType.CLIENT_DATA,
            FallbackConfig(
                operation_type=OperationType.CLIENT_DATA,
                strategy=FallbackStrategy.GRACEFUL_DEGRADATION,
                timeout_per_level_seconds=4.0,
            ),
            ServiceLevelMapping(
                primary_services=[ServiceType.REDIS],
                secondary_services=[ServiceType.AUTH_CACHE],
                tertiary_services=[ServiceType.DATABASE],
                emergency_handler=self._get_emergency_client_data,
            ),
        )

        # Cache operations - performance optimized
        self.register_operation_config(
            OperationType.CACHE_READ,
            FallbackConfig(
                operation_type=OperationType.CACHE_READ,
                strategy=FallbackStrategy.PERFORMANCE_FIRST,
                timeout_per_level_seconds=1.0,
                performance_threshold_ms=200.0,
            ),
            ServiceLevelMapping(
                primary_services=[ServiceType.REDIS],
                secondary_services=[ServiceType.AUTH_CACHE],
                emergency_handler=lambda key: None,  # Cache miss is acceptable
            ),
        )

        self.register_operation_config(
            OperationType.CACHE_WRITE,
            FallbackConfig(
                operation_type=OperationType.CACHE_WRITE,
                strategy=FallbackStrategy.GRACEFUL_DEGRADATION,
                timeout_per_level_seconds=2.0,
            ),
            ServiceLevelMapping(
                primary_services=[ServiceType.REDIS],
                secondary_services=[
                    ServiceType.AUTH_CACHE,
                    ServiceType.STORAGE_MANAGER,
                ],
                emergency_handler=lambda key, value: True,  # Silent failure acceptable
            ),
        )

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
            fallback_sequence = await self._determine_fallback_sequence(
                operation_type, config, mapping, context_data
            )

            logger.debug(
                f"Starting fallback execution for {operation_type} with sequence: {fallback_sequence}"
            )

            # Execute fallback sequence
            for level, services in fallback_sequence:
                if await self._should_skip_level(level, services, config):
                    continue

                level_result = await self._execute_level(
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
                    emergency_value = await self._execute_emergency_handler(
                        mapping.emergency_handler, args, kwargs, context_data
                    )
                    emergency_time = (time.time() - emergency_start) * 1000

                    if emergency_value is not None:
                        result.success = True
                        result.value = emergency_value
                        result.level_used = FallbackLevel.EMERGENCY
                        result.fallback_active = True

                        result.attempts.append(
                            FallbackAttempt(
                                operation_type=operation_type,
                                level=FallbackLevel.EMERGENCY,
                                service_type=ServiceType.DATABASE,  # Placeholder
                                success=True,
                                response_time_ms=emergency_time,
                                metadata={"emergency_handler": True},
                            )
                        )

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

    async def _determine_fallback_sequence(
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

        # Add remaining levels as fallback
        for level, services in sequence:
            if not any(level_item == level for level_item, _ in reordered_sequence):
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

        # Add remaining levels as fallback
        for level, services in sequence:
            if not any(level_item == level for level_item, _ in reordered_sequence):
                reordered_sequence.append((level, services))

        return reordered_sequence

    async def _should_skip_level(
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

    async def _execute_level(
        self,
        level: FallbackLevel,
        services: List[ServiceType],
        operation_func: Callable,
        args: tuple,
        kwargs: dict,
        config: FallbackConfig,
        context_data: Optional[Dict[str, Any]],
    ) -> FallbackResult:
        """Execute operation at a specific fallback level"""
        level_result = FallbackResult(success=False)

        # Try each service in the level
        for service in services:
            if not await self.health_manager.is_service_available(service):
                continue

            attempt_start = time.time()

            try:
                # Execute operation with timeout
                result_value = await asyncio.wait_for(
                    operation_func(*args, service_context=service, **kwargs),
                    timeout=config.timeout_per_level_seconds,
                )

                attempt_time = (time.time() - attempt_start) * 1000

                # Record successful attempt
                attempt = FallbackAttempt(
                    operation_type=config.operation_type,
                    level=level,
                    service_type=service,
                    success=True,
                    response_time_ms=attempt_time,
                    metadata={"context": context_data},
                )

                level_result.attempts.append(attempt)
                level_result.total_attempts += 1
                level_result.success = True
                level_result.value = result_value
                level_result.service_used = service

                # Update performance tracking
                self._track_performance(service, attempt_time)

                logger.debug(
                    f"Service {service} succeeded for {level} level in {attempt_time:.1f}ms"
                )
                return level_result

            except asyncio.TimeoutError:
                attempt_time = (time.time() - attempt_start) * 1000
                error_msg = f"Timeout after {attempt_time:.1f}ms"

                attempt = FallbackAttempt(
                    operation_type=config.operation_type,
                    level=level,
                    service_type=service,
                    success=False,
                    response_time_ms=attempt_time,
                    error_message=error_msg,
                    metadata={"timeout": True},
                )

                level_result.attempts.append(attempt)
                level_result.total_attempts += 1
                level_result.error_message = error_msg

                logger.warning(f"Service {service} timed out for {level} level")
                continue

            except Exception as e:
                attempt_time = (time.time() - attempt_start) * 1000
                error_msg = str(e)

                attempt = FallbackAttempt(
                    operation_type=config.operation_type,
                    level=level,
                    service_type=service,
                    success=False,
                    response_time_ms=attempt_time,
                    error_message=error_msg,
                    metadata={"exception": type(e).__name__},
                )

                level_result.attempts.append(attempt)
                level_result.total_attempts += 1
                level_result.error_message = error_msg

                logger.error(f"Service {service} failed for {level} level: {e}")
                continue

        return level_result

    async def _execute_emergency_handler(
        self,
        handler: Callable,
        args: tuple,
        kwargs: dict,
        context_data: Optional[Dict[str, Any]],
    ) -> Any:
        """Execute emergency fallback handler"""
        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(*args, context=context_data, **kwargs)
            else:
                return handler(*args, context=context_data, **kwargs)
        except Exception as e:
            logger.error(f"Emergency handler failed: {e}")
            raise

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

    # Emergency handler implementations

    async def _get_emergency_user_session(
        self, user_id: str, *args, context=None, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Emergency handler for user session data"""
        cache_key = f"emergency_session_{user_id}"

        async with self.emergency_cache_lock:
            if cache_key in self.emergency_cache:
                data, expires_at = self.emergency_cache[cache_key]
                if datetime.utcnow() < expires_at:
                    logger.debug(
                        f"Returning cached emergency session for user {user_id}"
                    )
                    return data
                else:
                    del self.emergency_cache[cache_key]

        # Generate minimal session data
        emergency_session = {
            "user_id": user_id,
            "email": f"user_{user_id}@emergency.local",
            "full_name": "Emergency User",
            "role": "user",
            "is_admin": False,
            "emergency_mode": True,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
        }

        # Cache for future use
        async with self.emergency_cache_lock:
            expires_at = datetime.utcnow() + timedelta(seconds=300)  # 5 minutes
            self.emergency_cache[cache_key] = (emergency_session, expires_at)

        logger.warning(f"Generated emergency session data for user {user_id}")
        return emergency_session

    async def _get_emergency_user_context(
        self, user_id: str, *args, context=None, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Emergency handler for user context data"""
        emergency_context = {
            "user_id": user_id,
            "active_client_id": None,
            "active_engagement_id": None,
            "active_flow_id": None,
            "preferences": {"theme": "light", "language": "en"},
            "permissions": ["read"],
            "recent_activities": [],
            "emergency_mode": True,
            "last_updated": datetime.utcnow().isoformat(),
        }

        logger.warning(f"Generated emergency context data for user {user_id}")
        return emergency_context

    async def _get_emergency_auth_response(
        self, *args, context=None, **kwargs
    ) -> Dict[str, Any]:
        """Emergency handler for authentication operations"""
        return {
            "authenticated": False,
            "error": "Authentication services temporarily unavailable",
            "emergency_mode": True,
            "retry_after_seconds": 300,
        }

    async def _get_emergency_client_data(
        self, user_id: str, *args, context=None, **kwargs
    ) -> List[Dict[str, Any]]:
        """Emergency handler for client data"""
        return [
            {
                "id": "emergency_client",
                "name": "Emergency Client",
                "status": "limited",
                "emergency_mode": True,
                "available_features": ["basic_viewing"],
            }
        ]

    # Public interface methods

    async def get_optimal_service(
        self, operation_type: OperationType
    ) -> Optional[ServiceType]:
        """Get the currently optimal service for an operation type"""
        config = self.fallback_configs.get(operation_type)
        mapping = self.service_mappings.get(operation_type)

        if not config or not mapping:
            return None

        sequence = await self._determine_fallback_sequence(
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
            "emergency_cache_size": len(self.emergency_cache),
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
        async with self.emergency_cache_lock:
            count = len(self.emergency_cache)
            self.emergency_cache.clear()

        logger.info(f"Cleared {count} items from emergency cache")
        return count

    async def reset_fallback_stats(self):
        """Reset fallback statistics"""
        self.fallback_stats.clear()
        self.performance_history.clear()
        self.last_successful_levels.clear()

        logger.info("Reset fallback statistics")


# Singleton instance
_fallback_orchestrator_instance: Optional[FallbackOrchestrator] = None


def get_fallback_orchestrator() -> FallbackOrchestrator:
    """Get singleton FallbackOrchestrator instance"""
    global _fallback_orchestrator_instance
    if _fallback_orchestrator_instance is None:
        _fallback_orchestrator_instance = FallbackOrchestrator()
    return _fallback_orchestrator_instance


# Cleanup function for app shutdown
async def shutdown_fallback_orchestrator():
    """Shutdown fallback orchestrator (call during app shutdown)"""
    global _fallback_orchestrator_instance
    if _fallback_orchestrator_instance:
        await _fallback_orchestrator_instance.clear_emergency_cache()
        _fallback_orchestrator_instance = None
