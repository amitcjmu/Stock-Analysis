"""
Enhanced Error Handler - Error Classification Strategies

Provides error classification logic and message templates for different error types
and user audiences. Handles intelligent error categorization based on error patterns.

Key Features:
- Pattern-based error classification
- Audience-specific message templates
- Service impact assessment
- Recovery strategy recommendations
"""

from collections import defaultdict
from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.services.monitoring.service_health_manager import ServiceType
from app.services.recovery.error_recovery_system import (
    FailureCategory,
    RecoveryPriority,
    RecoveryType,
)

from .base import (
    ErrorCategory,
    ErrorClassification,
    ErrorContext,
    ErrorSeverity,
    UserAudience,
)
from .templates import get_message_templates

logger = get_logger(__name__)


class ErrorClassificationStrategy:
    """Strategy for classifying errors based on patterns and context"""

    def __init__(self):
        # Error pattern learning
        self.error_patterns: Dict[str, Any] = defaultdict(list)
        self.classification_cache: Dict[str, ErrorClassification] = {}

        # Message templates
        self.message_templates = get_message_templates()

        logger.info("ErrorClassificationStrategy initialized")

    async def classify_error(
        self, error: Exception, context: ErrorContext
    ) -> ErrorClassification:
        """Classify an error to determine handling strategy"""

        # Create cache key for classification
        error_key = f"{type(error).__name__}:{str(error)[:100]}"

        # Check cache first
        if error_key in self.classification_cache:
            cached = self.classification_cache[error_key]
            # Use cached classification but update for current context
            return ErrorClassification(
                category=cached.category,
                severity=cached.severity,
                is_recoverable=cached.is_recoverable,
                recovery_type=cached.recovery_type,
                failure_category=cached.failure_category,
                confidence=cached.confidence,
                affected_services=cached.affected_services.copy(),
                fallback_recommended=cached.fallback_recommended,
                recovery_priority=cached.recovery_priority,
                max_retry_attempts=cached.max_retry_attempts,
            )

        # Classify based on error type and message
        classification = await self._perform_error_classification(error, context)

        # Cache the classification
        self.classification_cache[error_key] = classification

        # Limit cache size
        if len(self.classification_cache) > 1000:
            # Remove oldest entries
            keys_to_remove = list(self.classification_cache.keys())[:100]
            for key in keys_to_remove:
                del self.classification_cache[key]

        return classification

    async def _perform_error_classification(
        self, error: Exception, context: ErrorContext
    ) -> ErrorClassification:
        """Perform the actual error classification logic"""

        error_message = str(error).lower()

        # Classification rules based on error type and message content

        # Authentication errors
        if any(
            keyword in error_message
            for keyword in [
                "auth",
                "login",
                "credential",
                "token",
                "unauthorized",
                "401",
            ]
        ):
            return ErrorClassification(
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.HIGH,
                is_recoverable=False,  # User needs to re-authenticate
                affected_services={ServiceType.AUTH_CACHE},
                recovery_priority=RecoveryPriority.HIGH,
            )

        # Authorization errors
        if any(
            keyword in error_message
            for keyword in ["permission", "forbidden", "access denied", "403"]
        ):
            return ErrorClassification(
                category=ErrorCategory.AUTHORIZATION,
                severity=ErrorSeverity.MEDIUM,
                is_recoverable=False,  # User needs proper permissions
                affected_services={ServiceType.AUTH_CACHE, ServiceType.DATABASE},
            )

        # Database errors
        if any(
            keyword in error_message
            for keyword in ["database", "sql", "connection", "timeout", "deadlock"]
        ):
            return ErrorClassification(
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.CRITICAL,
                is_recoverable=True,
                recovery_type=RecoveryType.DELAYED_RETRY,
                failure_category=FailureCategory.PERSISTENT,
                affected_services={ServiceType.DATABASE},
                fallback_recommended=True,
                recovery_priority=RecoveryPriority.CRITICAL,
                max_retry_attempts=3,
            )

        # Cache errors
        if any(
            keyword in error_message
            for keyword in ["redis", "cache", "memory", "key not found"]
        ):
            return ErrorClassification(
                category=ErrorCategory.CACHE,
                severity=ErrorSeverity.MEDIUM,
                is_recoverable=True,
                recovery_type=RecoveryType.IMMEDIATE_RETRY,
                failure_category=FailureCategory.TRANSIENT,
                affected_services={ServiceType.REDIS, ServiceType.AUTH_CACHE},
                fallback_recommended=True,
                recovery_priority=RecoveryPriority.HIGH,
                max_retry_attempts=5,
            )

        # Network errors
        if any(
            keyword in error_message
            for keyword in ["network", "timeout", "connection", "unreachable", "dns"]
        ):
            return ErrorClassification(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH,
                is_recoverable=True,
                recovery_type=RecoveryType.DELAYED_RETRY,
                failure_category=FailureCategory.TRANSIENT,
                fallback_recommended=True,
                recovery_priority=RecoveryPriority.HIGH,
                max_retry_attempts=3,
            )

        # Service unavailable
        if any(
            keyword in error_message
            for keyword in ["unavailable", "503", "502", "504", "circuit breaker"]
        ):
            return ErrorClassification(
                category=ErrorCategory.SERVICE_UNAVAILABLE,
                severity=ErrorSeverity.CRITICAL,
                is_recoverable=True,
                recovery_type=RecoveryType.BACKGROUND_SYNC,
                failure_category=FailureCategory.PERSISTENT,
                fallback_recommended=True,
                recovery_priority=RecoveryPriority.CRITICAL,
                max_retry_attempts=2,
            )

        # Rate limiting
        if any(
            keyword in error_message
            for keyword in [
                "rate limit",
                "throttle",
                "429",
                "quota",
                "too many requests",
            ]
        ):
            return ErrorClassification(
                category=ErrorCategory.RATE_LIMITING,
                severity=ErrorSeverity.MEDIUM,
                is_recoverable=True,
                recovery_type=RecoveryType.DELAYED_RETRY,
                failure_category=FailureCategory.TRANSIENT,
                recovery_priority=RecoveryPriority.LOW,
                max_retry_attempts=2,
            )

        # Validation errors
        if any(
            keyword in error_message
            for keyword in ["validation", "invalid", "format", "required", "422"]
        ):
            return ErrorClassification(
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                is_recoverable=False,  # User needs to correct input
                recovery_priority=RecoveryPriority.LOW,
            )

        # Default classification for unknown errors
        return ErrorClassification(
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            is_recoverable=True,
            recovery_type=RecoveryType.IMMEDIATE_RETRY,
            failure_category=FailureCategory.UNKNOWN,
            confidence=0.5,  # Low confidence for unknown errors
            recovery_priority=RecoveryPriority.NORMAL,
            max_retry_attempts=2,
        )

    def get_message_template(
        self, category: ErrorCategory, audience: UserAudience
    ) -> Dict[str, Any]:
        """Get message template for category and audience"""
        template = self.message_templates.get(category, {}).get(audience, {})

        if not template:
            # Fallback to generic message
            template = {
                "message": "An error occurred while processing your request.",
                "suggestions": [
                    "Please try again",
                    "Contact support if the issue persists",
                ],
            }

        return template

    def clear_cache(self) -> int:
        """Clear classification cache"""
        count = len(self.classification_cache)
        self.classification_cache.clear()
        logger.info(f"Cleared {count} error classifications from cache")
        return count


# Singleton instance
_error_classification_strategy_instance: Optional[ErrorClassificationStrategy] = None


def get_error_classification_strategy() -> ErrorClassificationStrategy:
    """Get singleton ErrorClassificationStrategy instance"""
    global _error_classification_strategy_instance
    if _error_classification_strategy_instance is None:
        _error_classification_strategy_instance = ErrorClassificationStrategy()
    return _error_classification_strategy_instance
