"""
Retry Utilities for CrewAI Flows
Implements exponential backoff, error classification, and retry logic
"""

import asyncio
import logging
import random
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorCategory(Enum):
    """Error categorization for retry logic"""

    TRANSIENT = "transient"  # Network, timeout, rate limit - retry
    PERMANENT = "permanent"  # Validation, auth, not found - fail fast
    RESOURCE = "resource"  # Memory, disk, CPU - backoff and retry
    UNKNOWN = "unknown"  # Default category - conservative retry


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on: Optional[list] = None,
        dont_retry_on: Optional[list] = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on = retry_on or []
        self.dont_retry_on = dont_retry_on or []


def classify_error(error: Exception) -> ErrorCategory:
    """
    Classify an error to determine retry strategy
    """
    error_type = type(error).__name__
    error_msg = str(error).lower()

    # Transient errors - should retry
    transient_patterns = [
        "timeout",
        "timed out",
        "connection",
        "network",
        "temporary",
        "rate limit",
        "429",
        "503",
        "502",
        "504",
        "unavailable",
        "retryable",
        "transient",
        "handshake",
        "reset by peer",
    ]

    # Permanent errors - should not retry
    permanent_patterns = [
        "invalid",
        "validation",
        "unauthorized",
        "forbidden",
        "401",
        "403",
        "not found",
        "404",
        "bad request",
        "400",
        "missing required",
        "does not exist",
        "permission denied",
        "authentication failed",
    ]

    # Resource errors - should backoff significantly
    resource_patterns = [
        "memory",
        "disk",
        "space",
        "quota",
        "limit exceeded",
        "507",
        "insufficient",
        "out of",
        "resource",
        "capacity",
    ]

    # Check patterns
    for pattern in transient_patterns:
        if pattern in error_msg:
            return ErrorCategory.TRANSIENT

    for pattern in permanent_patterns:
        if pattern in error_msg:
            return ErrorCategory.PERMANENT

    for pattern in resource_patterns:
        if pattern in error_msg:
            return ErrorCategory.RESOURCE

    # Check specific exception types
    if error_type in [
        "TimeoutError",
        "asyncio.TimeoutError",
        "ConnectionError",
        "ConnectionRefusedError",
    ]:
        return ErrorCategory.TRANSIENT
    elif error_type in ["ValueError", "TypeError", "KeyError", "AttributeError"]:
        return ErrorCategory.PERMANENT
    elif error_type in ["MemoryError", "OSError"]:
        return ErrorCategory.RESOURCE

    return ErrorCategory.UNKNOWN


def calculate_delay(
    attempt: int, config: RetryConfig, error_category: ErrorCategory
) -> float:
    """
    Calculate delay for next retry with exponential backoff
    """
    # Base delay calculation
    delay = config.base_delay * (config.exponential_base**attempt)

    # Adjust based on error category
    if error_category == ErrorCategory.RESOURCE:
        # Resource errors need longer backoff
        delay *= 2.0
    elif error_category == ErrorCategory.TRANSIENT:
        # Transient errors can retry faster
        delay *= 0.8

    # Cap at max delay
    delay = min(delay, config.max_delay)

    # Add jitter to prevent thundering herd
    if config.jitter:
        jitter_amount = delay * 0.2  # 20% jitter
        delay += random.uniform(-jitter_amount, jitter_amount)

    return max(0.1, delay)  # Minimum 100ms delay


async def retry_with_backoff(
    func: Callable[..., T], *args, config: Optional[RetryConfig] = None, **kwargs
) -> T:
    """
    Execute an async function with retry logic and exponential backoff

    Args:
        func: Async function to execute
        config: Retry configuration
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result from successful execution

    Raises:
        Last exception if all retries exhausted
    """
    config = config or RetryConfig()
    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            # Log attempt
            if attempt > 0:
                logger.info(
                    f"🔄 Retry attempt {attempt}/{config.max_retries} for {func.__name__}"
                )

            # Execute function
            result = await func(*args, **kwargs)

            # Success - log if it was a retry
            if attempt > 0:
                logger.info(f"✅ Retry successful after {attempt} attempts")

            return result

        except Exception as e:
            last_exception = e
            error_category = classify_error(e)

            # Check if we should retry this error
            error_type = type(e).__name__

            # Don't retry if in dont_retry_on list
            if config.dont_retry_on and error_type in config.dont_retry_on:
                logger.error(f"❌ Error type {error_type} is non-retryable: {e}")
                raise

            # Don't retry permanent errors unless specified
            if (
                error_category == ErrorCategory.PERMANENT
                and error_type not in config.retry_on
            ):
                logger.error(f"❌ Permanent error, not retrying: {e}")
                raise

            # Check if we have retries left
            if attempt >= config.max_retries:
                logger.error(
                    f"❌ Max retries ({config.max_retries}) exhausted for {func.__name__}"
                )
                raise

            # Calculate delay
            delay = calculate_delay(attempt, config, error_category)

            logger.warning(
                f"⚠️ {error_category.value.capitalize()} error in {func.__name__}: {e}. "
                f"Retrying in {delay:.1f}s... (attempt {attempt + 1}/{config.max_retries})"
            )

            # Wait before retry
            await asyncio.sleep(delay)

    # Should not reach here, but just in case
    if last_exception:
        raise last_exception
    else:
        raise RuntimeError(f"Unexpected retry logic error in {func.__name__}")


def retry_decorator(config: Optional[RetryConfig] = None):
    """
    Decorator for adding retry logic to async functions

    Usage:
        @retry_decorator(RetryConfig(max_retries=5))
        async def my_function():
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(func, *args, config=config, **kwargs)

        return wrapper

    return decorator


class RetryMetrics:
    """Track retry metrics for monitoring"""

    def __init__(self):
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.retry_counts = {}
        self.error_counts = {}
        self.start_time = datetime.utcnow()

    def record_call(
        self,
        func_name: str,
        success: bool,
        retries: int = 0,
        error: Optional[str] = None,
    ):
        """Record metrics for a function call"""
        self.total_calls += 1

        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            if error:
                self.error_counts[error] = self.error_counts.get(error, 0) + 1

        if retries > 0:
            self.retry_counts[func_name] = self.retry_counts.get(func_name, 0) + retries

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        runtime = (datetime.utcnow() - self.start_time).total_seconds()
        success_rate = (
            self.successful_calls / self.total_calls if self.total_calls > 0 else 0
        )

        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": success_rate,
            "total_retries": sum(self.retry_counts.values()),
            "functions_with_retries": list(self.retry_counts.keys()),
            "top_errors": sorted(
                self.error_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "runtime_seconds": runtime,
            "calls_per_minute": (self.total_calls / runtime * 60) if runtime > 0 else 0,
        }


# Global metrics instance
retry_metrics = RetryMetrics()


async def retry_with_metrics(
    func: Callable[..., T],
    func_name: str,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs,
) -> T:
    """
    Execute function with retry logic and metrics tracking
    """
    retries = 0
    error_msg = None

    try:
        for attempt in range((config or RetryConfig()).max_retries + 1):
            try:
                result = await retry_with_backoff(func, *args, config=config, **kwargs)
                retry_metrics.record_call(func_name, True, retries)
                return result
            except Exception as e:
                retries = attempt
                error_msg = str(e)
                if attempt >= (config or RetryConfig()).max_retries:
                    raise

    except Exception:
        retry_metrics.record_call(func_name, False, retries, error_msg)
        raise
