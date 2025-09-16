"""
Main retry handler classes for executing operations with retry logic.

This module contains the core RetryHandler class that provides retry execution,
circuit breaking, and error handling capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar


from .backoff import BackoffCalculator
from .base import (
    CircuitBreakerState,
    ErrorRecord,
    RetryConfig,
    RetryStrategy,
)
from .exceptions import CircuitBreakerOpenError, MaxRetriesExceededError
from .strategies import ErrorClassifier

T = TypeVar("T")


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
                delay = BackoffCalculator.calculate_delay(
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
        error_type: Optional[str] = None,
        hours: int = 24,
    ) -> List[ErrorRecord]:
        """Get error history with optional filtering"""
        from .base import ErrorType

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
            error_type_enum = ErrorType(error_type)
            filtered_errors = [
                e for e in filtered_errors if e.error_type == error_type_enum
            ]

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
