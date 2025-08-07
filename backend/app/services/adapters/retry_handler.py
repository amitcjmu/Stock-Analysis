"""
Error Handling and Retry Logic for ADCS Platform Adapters

This module provides comprehensive error handling, retry logic, and circuit breaker
patterns for all platform adapters to ensure resilient data collection.
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from app.services.collection_flow.adapters import CollectionResponse


class ErrorType(str, Enum):
    """Classification of errors for appropriate handling strategies"""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK_CONNECTIVITY = "network_connectivity"
    RATE_LIMITING = "rate_limiting"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT = "timeout"
    DATA_VALIDATION = "data_validation"
    CONFIGURATION = "configuration"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetryStrategy(str, Enum):
    """Retry strategy types"""

    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    RANDOM_JITTER = "random_jitter"
    NO_RETRY = "no_retry"


@dataclass
class ErrorPattern:
    """Error pattern for classification and handling"""

    error_type: ErrorType
    severity: ErrorSeverity
    retry_strategy: RetryStrategy
    max_retries: int
    base_delay: float
    max_delay: float
    should_circuit_break: bool = False
    keywords: List[str] = field(default_factory=list)
    exception_types: List[type] = field(default_factory=list)


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    jitter: bool = True
    jitter_range: float = 0.1
    timeout_multiplier: float = 1.5
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 300.0  # 5 minutes


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""

    timestamp: datetime
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    adapter_name: str
    platform: str
    exception_type: str
    context: Dict[str, Any] = field(default_factory=dict)
    retry_attempt: int = 0
    total_retries: int = 0


@dataclass
class CircuitBreakerState:
    """State of a circuit breaker"""

    is_open: bool = False
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    next_attempt_time: Optional[datetime] = None
    consecutive_successes: int = 0


T = TypeVar("T")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""

    pass


class MaxRetriesExceededError(Exception):
    """Raised when maximum retry attempts are exceeded"""

    pass


class ErrorClassifier:
    """Classifies errors and determines handling strategies"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ErrorClassifier")
        self._error_patterns = self._initialize_error_patterns()

    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """Initialize known error patterns for classification"""
        return [
            # Authentication errors
            ErrorPattern(
                error_type=ErrorType.AUTHENTICATION,
                severity=ErrorSeverity.CRITICAL,
                retry_strategy=RetryStrategy.NO_RETRY,
                max_retries=0,
                base_delay=0,
                max_delay=0,
                keywords=[
                    "authentication",
                    "auth",
                    "login",
                    "credentials",
                    "unauthorized",
                    "401",
                ],
                exception_types=[PermissionError],
            ),
            # Authorization errors
            ErrorPattern(
                error_type=ErrorType.AUTHORIZATION,
                severity=ErrorSeverity.HIGH,
                retry_strategy=RetryStrategy.NO_RETRY,
                max_retries=0,
                base_delay=0,
                max_delay=0,
                keywords=[
                    "authorization",
                    "forbidden",
                    "access denied",
                    "permission",
                    "403",
                ],
                exception_types=[PermissionError],
            ),
            # Network connectivity errors
            ErrorPattern(
                error_type=ErrorType.NETWORK_CONNECTIVITY,
                severity=ErrorSeverity.MEDIUM,
                retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retries=5,
                base_delay=2.0,
                max_delay=30.0,
                keywords=[
                    "connection",
                    "network",
                    "dns",
                    "host",
                    "unreachable",
                    "timeout",
                ],
                exception_types=[ConnectionError, TimeoutError, OSError],
            ),
            # Rate limiting errors
            ErrorPattern(
                error_type=ErrorType.RATE_LIMITING,
                severity=ErrorSeverity.MEDIUM,
                retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retries=3,
                base_delay=5.0,
                max_delay=120.0,
                keywords=[
                    "rate limit",
                    "throttle",
                    "quota",
                    "429",
                    "too many requests",
                ],
                exception_types=[],
            ),
            # Service unavailable errors
            ErrorPattern(
                error_type=ErrorType.SERVICE_UNAVAILABLE,
                severity=ErrorSeverity.HIGH,
                retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retries=3,
                base_delay=10.0,
                max_delay=300.0,
                should_circuit_break=True,
                keywords=["service unavailable", "502", "503", "504", "maintenance"],
                exception_types=[],
            ),
            # Timeout errors
            ErrorPattern(
                error_type=ErrorType.TIMEOUT,
                severity=ErrorSeverity.MEDIUM,
                retry_strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retries=3,
                base_delay=5.0,
                max_delay=60.0,
                keywords=["timeout", "timed out"],
                exception_types=[TimeoutError, asyncio.TimeoutError],
            ),
            # Data validation errors
            ErrorPattern(
                error_type=ErrorType.DATA_VALIDATION,
                severity=ErrorSeverity.LOW,
                retry_strategy=RetryStrategy.NO_RETRY,
                max_retries=0,
                base_delay=0,
                max_delay=0,
                keywords=["validation", "invalid data", "parse", "format"],
                exception_types=[ValueError, TypeError],
            ),
            # Configuration errors
            ErrorPattern(
                error_type=ErrorType.CONFIGURATION,
                severity=ErrorSeverity.CRITICAL,
                retry_strategy=RetryStrategy.NO_RETRY,
                max_retries=0,
                base_delay=0,
                max_delay=0,
                keywords=["configuration", "config", "invalid", "missing"],
                exception_types=[ValueError, KeyError],
            ),
            # Resource exhausted errors
            ErrorPattern(
                error_type=ErrorType.RESOURCE_EXHAUSTED,
                severity=ErrorSeverity.HIGH,
                retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retries=2,
                base_delay=30.0,
                max_delay=300.0,
                should_circuit_break=True,
                keywords=["memory", "disk space", "cpu", "resource", "exhausted"],
                exception_types=[MemoryError],
            ),
        ]

    def classify_error(
        self, error: Exception, context: Dict[str, Any] = None
    ) -> ErrorPattern:
        """Classify an error and return appropriate handling pattern"""
        context = context or {}
        error_message = str(error).lower()
        type(error)

        # Try to match against known patterns
        for pattern in self._error_patterns:
            # Check exception type match
            if any(isinstance(error, exc_type) for exc_type in pattern.exception_types):
                return pattern

            # Check keyword match
            if any(keyword in error_message for keyword in pattern.keywords):
                return pattern

        # Default pattern for unknown errors
        return ErrorPattern(
            error_type=ErrorType.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            max_retries=2,
            base_delay=1.0,
            max_delay=30.0,
        )

    def update_pattern(self, error_type: ErrorType, **kwargs):
        """Update an existing error pattern"""
        from app.core.security.cache_encryption import (
            encrypt_for_cache,
            is_sensitive_field,
        )
        from app.core.security.secure_setattr import SAFE_ATTRIBUTES, secure_setattr

        for pattern in self._error_patterns:
            if pattern.error_type == error_type:
                # Define allowed attributes for error pattern updates
                allowed_attrs = SAFE_ATTRIBUTES | {
                    "retry_count",
                    "max_retries",
                    "backoff_factor",
                    "max_delay",
                    "error_type",
                    "pattern",
                    "enabled",
                    "last_retry",
                }

                for attr_name, attr_value in kwargs.items():
                    if hasattr(pattern, attr_name):
                        # Encrypt sensitive data before any caching operations
                        safe_value = attr_value
                        if is_sensitive_field(attr_name) and attr_value:
                            encrypted_value = encrypt_for_cache(attr_value)
                            if encrypted_value:
                                safe_value = encrypted_value
                            else:
                                # Skip setting if encryption failed for sensitive data
                                logging.warning(
                                    f"Failed to encrypt sensitive attribute {attr_name}, skipping"
                                )
                                continue

                        # Use secure attribute setting to prevent sensitive data exposure
                        # SECURITY: safe_value is already encrypted if sensitive, safe for caching
                        # nosec: B106 - Values are pre-encrypted for sensitive fields
                        if not secure_setattr(
                            pattern,
                            attr_name,
                            safe_value,
                            allowed_attrs,
                            strict_mode=False,
                        ):
                            logging.warning(
                                f"Skipped updating potentially sensitive attribute: {attr_name}"
                            )
                break


class RetryHandler:
    """Handles retry logic with various strategies and circuit breaking"""

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.logger = logging.getLogger(f"{__name__}.RetryHandler")
        self._error_classifier = ErrorClassifier()
        self._error_history: List[ErrorRecord] = []
        self._circuit_breakers: Dict[str, CircuitBreakerState] = {}

    async def execute_with_retry(
        self,
        func: Callable[..., T],
        *args,
        adapter_name: str = "unknown",
        platform: str = "unknown",
        context: Dict[str, Any] = None,
        custom_config: Optional[RetryConfig] = None,
        **kwargs,
    ) -> T:
        """
        Execute a function with retry logic and circuit breaking

        Args:
            func: Function to execute
            *args: Function arguments
            adapter_name: Name of the adapter for tracking
            platform: Platform name for tracking
            context: Additional context for error handling
            custom_config: Custom retry configuration
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            MaxRetriesExceededError: When max retries exceeded
            CircuitBreakerOpenError: When circuit breaker is open
        """
        config = custom_config or self.config
        context = context or {}
        circuit_key = f"{adapter_name}:{platform}"

        # Check circuit breaker
        if config.circuit_breaker_enabled:
            await self._check_circuit_breaker(circuit_key)

        last_error = None
        retry_count = 0

        while retry_count <= config.max_retries:
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Success - reset circuit breaker
                if config.circuit_breaker_enabled:
                    await self._record_success(circuit_key)

                return result

            except Exception as error:
                last_error = error

                # Classify error
                error_pattern = self._error_classifier.classify_error(error, context)

                # Record error
                error_record = ErrorRecord(
                    timestamp=datetime.utcnow(),
                    error_type=error_pattern.error_type,
                    severity=error_pattern.severity,
                    message=str(error),
                    adapter_name=adapter_name,
                    platform=platform,
                    exception_type=type(error).__name__,
                    context=context,
                    retry_attempt=retry_count,
                    total_retries=config.max_retries,
                )
                self._error_history.append(error_record)

                # Update circuit breaker
                if (
                    config.circuit_breaker_enabled
                    and error_pattern.should_circuit_break
                ):
                    await self._record_failure(circuit_key)

                # Check if we should retry
                if (
                    retry_count >= config.max_retries
                    or error_pattern.retry_strategy == RetryStrategy.NO_RETRY
                ):
                    self.logger.error(
                        f"Max retries exceeded for {adapter_name}:{platform} - "
                        f"Error: {error_pattern.error_type.value} - {str(error)}"
                    )
                    raise MaxRetriesExceededError(
                        f"Max retries ({config.max_retries}) exceeded. Last error: {str(error)}"
                    ) from error

                # Calculate delay and wait
                delay = self._calculate_delay(
                    retry_count,
                    error_pattern.retry_strategy,
                    error_pattern.base_delay or config.base_delay,
                    error_pattern.max_delay or config.max_delay,
                    config.jitter,
                    config.jitter_range,
                )

                self.logger.warning(
                    f"Retry {retry_count + 1}/{config.max_retries} for {adapter_name}:{platform} "
                    f"after {delay:.2f}s - Error: {error_pattern.error_type.value}"
                )

                await asyncio.sleep(delay)
                retry_count += 1

        # This should not be reached, but just in case
        raise MaxRetriesExceededError(
            f"Unexpected retry loop exit. Last error: {str(last_error)}"
        )

    def _calculate_delay(
        self,
        retry_count: int,
        strategy: RetryStrategy,
        base_delay: float,
        max_delay: float,
        jitter: bool,
        jitter_range: float,
    ) -> float:
        """Calculate delay based on retry strategy"""
        if strategy == RetryStrategy.FIXED_DELAY:
            delay = base_delay
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (2**retry_count)
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * (retry_count + 1)
        elif strategy == RetryStrategy.RANDOM_JITTER:
            delay = base_delay + random.uniform(0, base_delay)
        else:
            delay = base_delay

        # Apply max delay limit
        delay = min(delay, max_delay)

        # Apply jitter
        if jitter:
            jitter_amount = delay * jitter_range
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(delay, 0.1)  # Minimum delay of 0.1 seconds

    async def _check_circuit_breaker(self, circuit_key: str):
        """Check if circuit breaker allows execution"""
        if circuit_key not in self._circuit_breakers:
            self._circuit_breakers[circuit_key] = CircuitBreakerState()
            return

        state = self._circuit_breakers[circuit_key]

        if not state.is_open:
            return

        # Check if we can attempt to close the circuit
        if state.next_attempt_time and datetime.utcnow() >= state.next_attempt_time:
            # Half-open state - allow one attempt
            state.is_open = False
            self.logger.info(
                f"Circuit breaker for {circuit_key} entering half-open state"
            )
            return

        # Circuit is still open
        raise CircuitBreakerOpenError(
            f"Circuit breaker is open for {circuit_key}. "
            f"Next attempt allowed at {state.next_attempt_time}"
        )

    async def _record_success(self, circuit_key: str):
        """Record successful execution for circuit breaker"""
        if circuit_key not in self._circuit_breakers:
            return

        state = self._circuit_breakers[circuit_key]
        state.consecutive_successes += 1

        if state.is_open:
            # Close circuit breaker after successful execution in half-open state
            state.is_open = False
            state.failure_count = 0
            state.last_failure_time = None
            state.next_attempt_time = None
            self.logger.info(
                f"Circuit breaker for {circuit_key} closed after successful execution"
            )

    async def _record_failure(self, circuit_key: str):
        """Record failed execution for circuit breaker"""
        if circuit_key not in self._circuit_breakers:
            self._circuit_breakers[circuit_key] = CircuitBreakerState()

        state = self._circuit_breakers[circuit_key]
        state.failure_count += 1
        state.last_failure_time = datetime.utcnow()
        state.consecutive_successes = 0

        # Open circuit breaker if threshold exceeded
        if state.failure_count >= self.config.circuit_breaker_threshold:
            state.is_open = True
            state.next_attempt_time = datetime.utcnow() + timedelta(
                seconds=self.config.circuit_breaker_timeout
            )
            self.logger.warning(
                f"Circuit breaker opened for {circuit_key} after {state.failure_count} failures. "
                f"Next attempt allowed at {state.next_attempt_time}"
            )

    def get_error_history(
        self,
        adapter_name: Optional[str] = None,
        platform: Optional[str] = None,
        error_type: Optional[ErrorType] = None,
        hours: int = 24,
    ) -> List[ErrorRecord]:
        """Get error history with optional filtering"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        filtered_errors = [
            error for error in self._error_history if error.timestamp >= cutoff_time
        ]

        if adapter_name:
            filtered_errors = [
                e for e in filtered_errors if e.adapter_name == adapter_name
            ]

        if platform:
            filtered_errors = [e for e in filtered_errors if e.platform == platform]

        if error_type:
            filtered_errors = [e for e in filtered_errors if e.error_type == error_type]

        return filtered_errors

    def get_circuit_breaker_status(
        self, circuit_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get circuit breaker status"""
        if circuit_key:
            if circuit_key in self._circuit_breakers:
                state = self._circuit_breakers[circuit_key]
                return {
                    "circuit_key": circuit_key,
                    "is_open": state.is_open,
                    "failure_count": state.failure_count,
                    "last_failure_time": (
                        state.last_failure_time.isoformat()
                        if state.last_failure_time
                        else None
                    ),
                    "next_attempt_time": (
                        state.next_attempt_time.isoformat()
                        if state.next_attempt_time
                        else None
                    ),
                    "consecutive_successes": state.consecutive_successes,
                }
            else:
                return {"circuit_key": circuit_key, "status": "not_found"}
        else:
            return {
                "circuit_breakers": {
                    key: {
                        "is_open": state.is_open,
                        "failure_count": state.failure_count,
                        "last_failure_time": (
                            state.last_failure_time.isoformat()
                            if state.last_failure_time
                            else None
                        ),
                        "next_attempt_time": (
                            state.next_attempt_time.isoformat()
                            if state.next_attempt_time
                            else None
                        ),
                        "consecutive_successes": state.consecutive_successes,
                    }
                    for key, state in self._circuit_breakers.items()
                }
            }

    def reset_circuit_breaker(self, circuit_key: str) -> bool:
        """Manually reset a circuit breaker"""
        if circuit_key in self._circuit_breakers:
            self._circuit_breakers[circuit_key] = CircuitBreakerState()
            self.logger.info(f"Circuit breaker for {circuit_key} manually reset")
            return True
        return False

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of errors in the specified time period"""
        errors = self.get_error_history(hours=hours)

        summary = {
            "total_errors": len(errors),
            "time_period_hours": hours,
            "error_types": {},
            "severity_distribution": {},
            "adapter_errors": {},
            "platform_errors": {},
            "top_errors": [],
        }

        # Count by error type
        for error in errors:
            error_type = error.error_type.value
            summary["error_types"][error_type] = (
                summary["error_types"].get(error_type, 0) + 1
            )

            severity = error.severity.value
            summary["severity_distribution"][severity] = (
                summary["severity_distribution"].get(severity, 0) + 1
            )

            adapter = error.adapter_name
            summary["adapter_errors"][adapter] = (
                summary["adapter_errors"].get(adapter, 0) + 1
            )

            platform = error.platform
            summary["platform_errors"][platform] = (
                summary["platform_errors"].get(platform, 0) + 1
            )

        # Get top error messages
        error_messages = {}
        for error in errors:
            msg = error.message[:100]  # Truncate for grouping
            error_messages[msg] = error_messages.get(msg, 0) + 1

        summary["top_errors"] = sorted(
            error_messages.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return summary


def retry_adapter_operation(
    retry_config: Optional[RetryConfig] = None,
    adapter_name: str = "unknown",
    platform: str = "unknown",
):
    """
    Decorator for adding retry logic to adapter operations

    Args:
        retry_config: Custom retry configuration
        adapter_name: Name of the adapter
        platform: Platform name
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get or create retry handler from adapter instance
            if args and hasattr(args[0], "_retry_handler"):
                retry_handler = args[0]._retry_handler
            else:
                retry_handler = RetryHandler(retry_config)

            return await retry_handler.execute_with_retry(
                func, *args, adapter_name=adapter_name, platform=platform, **kwargs
            )

        return wrapper

    return decorator


class AdapterErrorHandler:
    """
    High-level error handler for adapter operations

    Provides unified error handling across all adapters with:
    - Automatic error classification and response
    - Retry logic with circuit breaking
    - Error reporting and analytics
    - Recovery recommendations
    """

    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.retry_handler = RetryHandler(retry_config)
        self.logger = logging.getLogger(f"{__name__}.AdapterErrorHandler")

    async def handle_collection_request(
        self,
        adapter_func: Callable,
        request_args: tuple,
        request_kwargs: dict,
        adapter_name: str,
        platform: str,
    ) -> CollectionResponse:
        """
        Handle a collection request with comprehensive error handling

        Args:
            adapter_func: Adapter's collect_data method
            request_args: Arguments for the adapter function
            request_kwargs: Keyword arguments for the adapter function
            adapter_name: Name of the adapter
            platform: Platform being collected from

        Returns:
            CollectionResponse with success or error information
        """
        try:
            response = await self.retry_handler.execute_with_retry(
                adapter_func,
                *request_args,
                adapter_name=adapter_name,
                platform=platform,
                **request_kwargs,
            )

            # Validate response
            if not isinstance(response, CollectionResponse):
                raise ValueError(
                    f"Adapter returned invalid response type: {type(response)}"
                )

            return response

        except CircuitBreakerOpenError as e:
            self.logger.error(
                f"Circuit breaker open for {adapter_name}:{platform}: {str(e)}"
            )
            return CollectionResponse(
                success=False,
                error_message="Service temporarily unavailable due to repeated failures",
                error_details={
                    "error_type": "circuit_breaker_open",
                    "adapter": adapter_name,
                    "platform": platform,
                    "recovery_time": "Please try again in a few minutes",
                },
            )

        except MaxRetriesExceededError as e:
            self.logger.error(
                f"Max retries exceeded for {adapter_name}:{platform}: {str(e)}"
            )
            return CollectionResponse(
                success=False,
                error_message="Collection failed after multiple retry attempts",
                error_details={
                    "error_type": "max_retries_exceeded",
                    "adapter": adapter_name,
                    "platform": platform,
                    "recommendation": "Check adapter configuration and platform connectivity",
                },
            )

        except Exception as e:
            self.logger.error(
                f"Unexpected error in {adapter_name}:{platform}: {str(e)}"
            )
            error_pattern = self.retry_handler._error_classifier.classify_error(e)

            return CollectionResponse(
                success=False,
                error_message=str(e),
                error_details={
                    "error_type": error_pattern.error_type.value,
                    "severity": error_pattern.severity.value,
                    "adapter": adapter_name,
                    "platform": platform,
                    "exception_type": type(e).__name__,
                },
            )

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of error handling system"""
        error_summary = self.retry_handler.get_error_summary(hours=1)
        circuit_status = self.retry_handler.get_circuit_breaker_status()

        # Determine health status
        critical_errors = error_summary.get("severity_distribution", {}).get(
            "critical", 0
        )
        open_circuits = sum(
            1
            for state in circuit_status.get("circuit_breakers", {}).values()
            if state.get("is_open", False)
        )

        if critical_errors > 0 or open_circuits > 0:
            health = "unhealthy"
        elif error_summary.get("total_errors", 0) > 10:
            health = "degraded"
        else:
            health = "healthy"

        return {
            "health_status": health,
            "error_summary": error_summary,
            "circuit_breaker_status": circuit_status,
            "recommendations": self._get_health_recommendations(
                error_summary, circuit_status
            ),
        }

    def _get_health_recommendations(
        self, error_summary: Dict[str, Any], circuit_status: Dict[str, Any]
    ) -> List[str]:
        """Get health recommendations based on current status"""
        recommendations = []

        # Check for critical errors
        critical_count = error_summary.get("severity_distribution", {}).get(
            "critical", 0
        )
        if critical_count > 0:
            recommendations.append(
                "Critical errors detected - check adapter configurations and credentials"
            )

        # Check for high error rates
        total_errors = error_summary.get("total_errors", 0)
        if total_errors > 50:
            recommendations.append(
                "High error rate detected - consider adjusting retry strategies"
            )

        # Check for open circuit breakers
        open_circuits = [
            key
            for key, state in circuit_status.get("circuit_breakers", {}).items()
            if state.get("is_open", False)
        ]
        if open_circuits:
            recommendations.append(
                f"Circuit breakers open for: {', '.join(open_circuits)} - check service availability"
            )

        # Check for authentication errors
        auth_errors = error_summary.get("error_types", {}).get("authentication", 0)
        if auth_errors > 0:
            recommendations.append(
                "Authentication errors detected - verify credentials and permissions"
            )

        # Check for network errors
        network_errors = error_summary.get("error_types", {}).get(
            "network_connectivity", 0
        )
        if network_errors > 5:
            recommendations.append(
                "Network connectivity issues detected - check network configuration"
            )

        if not recommendations:
            recommendations.append("System is operating normally")

        return recommendations
