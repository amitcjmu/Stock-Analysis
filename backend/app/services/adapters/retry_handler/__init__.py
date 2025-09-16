"""
Error Handling and Retry Logic for ADCS Platform Adapters

This module provides comprehensive error handling, retry logic, and circuit breaker
patterns for all platform adapters to ensure resilient data collection.

This module has been modularized for better maintainability. All previous imports
remain available for backward compatibility.
"""

# Import all base types and enums
from .base import (
    CircuitBreakerState,
    ErrorPattern,
    ErrorRecord,
    ErrorSeverity,
    ErrorType,
    RetryConfig,
    RetryStrategy,
)

# Import exception classes
from .exceptions import CircuitBreakerOpenError, MaxRetriesExceededError

# Import main handler classes and decorator
from .adapter_error_handler import AdapterErrorHandler
from .handler import RetryHandler, retry_adapter_operation

# Import strategy and classification classes
from .strategies import ErrorClassifier

# Export all public API for backward compatibility
__all__ = [
    # Enums
    "ErrorType",
    "ErrorSeverity",
    "RetryStrategy",
    # Data classes
    "ErrorPattern",
    "RetryConfig",
    "ErrorRecord",
    "CircuitBreakerState",
    # Exception classes
    "CircuitBreakerOpenError",
    "MaxRetriesExceededError",
    # Handler classes
    "RetryHandler",
    "AdapterErrorHandler",
    "ErrorClassifier",
    # Decorators
    "retry_adapter_operation",
]
