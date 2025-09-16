"""
Error classification and retry strategies for the retry handling system.

This module contains the ErrorClassifier that analyzes errors and determines
appropriate handling patterns based on error types, patterns, and contexts.
"""

import asyncio
import logging
from typing import Any, Dict, List

from .base import ErrorPattern, ErrorSeverity, ErrorType, RetryStrategy


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
