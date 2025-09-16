"""
Exception classes for retry handling.

This module contains custom exception classes used throughout the retry
handling system for proper error propagation and handling.
"""


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""

    pass


class MaxRetriesExceededError(Exception):
    """Raised when maximum retry attempts are exceeded"""

    pass
