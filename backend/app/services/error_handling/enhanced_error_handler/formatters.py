"""
Enhanced Error Handler - Error Formatting and Response Generation

Handles error response generation, structured logging, and message formatting
for different audiences. Provides contextual error information and debug data.

Key Features:
- Audience-specific error response generation
- Structured error logging without sensitive data
- Debug information for development environments
- Recovery time estimation
- Context enrichment for error responses
"""

import traceback
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security.cache_encryption import sanitize_for_logging
from app.services.recovery.error_recovery_system import RecoveryType

from .base import (
    ErrorClassification,
    ErrorContext,
    ErrorResponse,
    ErrorSeverity,
    UserAudience,
)
from .strategies import ErrorClassificationStrategy, get_error_classification_strategy

logger = get_logger(__name__)


class ErrorResponseFormatter:
    """Formats error responses and handles structured logging"""

    def __init__(
        self, classification_strategy: Optional[ErrorClassificationStrategy] = None
    ):
        self.classification_strategy = (
            classification_strategy or get_error_classification_strategy()
        )

        # Configuration
        self.enable_debug_info = getattr(settings, "DEBUG", False)

        logger.info("ErrorResponseFormatter initialized")

    async def generate_error_response(
        self,
        error: Exception,
        classification: ErrorClassification,
        context: ErrorContext,
        audience: UserAudience,
    ) -> ErrorResponse:
        """Generate structured error response"""

        # Get message template for category and audience
        template = self.classification_strategy.get_message_template(
            classification.category, audience
        )

        # Generate error code
        error_code = f"{classification.category.value.upper()}_{classification.severity.value.upper()}"

        # Create base response
        error_response = ErrorResponse(
            error_code=error_code,
            message=template["message"],
            recovery_suggestions=template["suggestions"],
            error_id=context.error_id,
            severity=classification.severity,
            category=classification.category,
        )

        # Add contextual details (sanitized)
        if context.operation_type:
            error_response.details["operation"] = context.operation_type.value

        if context.service_type:
            error_response.details["service"] = context.service_type.value

        if context.system_health:
            error_response.details["system_health"] = context.system_health

        if context.active_fallbacks:
            error_response.fallback_active = True
            error_response.details["active_fallbacks"] = context.active_fallbacks

        # Add recovery information
        if classification.is_recoverable:
            error_response.recovery_initiated = True

            # Estimate recovery time based on recovery type
            if classification.recovery_type == RecoveryType.IMMEDIATE_RETRY:
                error_response.estimated_recovery_time = 5  # 5 seconds
            elif classification.recovery_type == RecoveryType.DELAYED_RETRY:
                error_response.estimated_recovery_time = 30  # 30 seconds
            elif classification.recovery_type == RecoveryType.BACKGROUND_SYNC:
                error_response.estimated_recovery_time = 300  # 5 minutes

        # Add debug information for developers
        if audience == UserAudience.DEVELOPER and self.enable_debug_info:
            error_response.debug_info = {
                "error_type": type(error).__name__,
                "classification": classification.to_dict(),
                "context": {
                    "error_id": context.error_id,
                    "timestamp": context.timestamp.isoformat(),
                    "operation_type": (
                        context.operation_type.value if context.operation_type else None
                    ),
                    "service_type": (
                        context.service_type.value if context.service_type else None
                    ),
                    "sanitized_context": sanitize_for_logging(context.context_data),
                },
                "stack_trace": traceback.format_exception(
                    type(error), error, error.__traceback__
                )[
                    -5:
                ],  # Last 5 frames
            }

        return error_response

    async def log_error_structured(
        self,
        error: Exception,
        classification: ErrorClassification,
        context: ErrorContext,
        error_response: ErrorResponse,
    ):
        """Log error with structured format and no sensitive data"""

        # Determine log level based on severity
        if classification.severity == ErrorSeverity.CRITICAL:
            log_func = logger.critical
        elif classification.severity == ErrorSeverity.HIGH:
            log_func = logger.error
        elif classification.severity == ErrorSeverity.MEDIUM:
            log_func = logger.warning
        else:
            log_func = logger.info

        # Create structured log entry
        log_data = {
            "error_id": context.error_id,
            "error_type": type(error).__name__,
            "error_category": classification.category.value,
            "error_severity": classification.severity.value,
            "is_recoverable": classification.is_recoverable,
            "recovery_initiated": error_response.recovery_initiated,
            "fallback_active": error_response.fallback_active,
            "operation_type": (
                context.operation_type.value if context.operation_type else None
            ),
            "service_type": (
                context.service_type.value if context.service_type else None
            ),
            "system_health": context.system_health,
            "affected_services": [s.value for s in classification.affected_services],
            "user_id_hash": (
                hash(context.user_id) if context.user_id else None
            ),  # Hashed for privacy
            "endpoint": context.endpoint,
            "method": context.method,
            "timestamp": context.timestamp.isoformat(),
            "sanitized_context": sanitize_for_logging(context.context_data),
        }

        # Log the error
        log_func(
            f"Structured error: {classification.category.value} - {error_response.message}",
            extra=log_data,
            exc_info=classification.severity
            in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL],
        )

    def format_user_message(
        self, error_response: ErrorResponse, audience: UserAudience
    ) -> str:
        """Format user-friendly error message"""
        if audience == UserAudience.END_USER:
            # Simple message for end users
            return error_response.message
        elif audience == UserAudience.ADMIN_USER:
            # More detailed message for admins
            details = []
            if error_response.details.get("system_health"):
                details.append(
                    f"System Health: {error_response.details['system_health']}"
                )
            if error_response.fallback_active:
                details.append("Fallback systems are active")
            if error_response.recovery_initiated:
                details.append("Recovery has been initiated")

            message = error_response.message
            if details:
                message += f" ({', '.join(details)})"
            return message
        else:
            # Technical message for developers
            return (
                f"[{error_response.error_code}] {error_response.message} "
                f"(Error ID: {error_response.error_id})"
            )

    def get_recovery_guidance(self, error_response: ErrorResponse) -> dict:
        """Get detailed recovery guidance for the error"""
        guidance = {
            "immediate_actions": error_response.recovery_suggestions,
            "recovery_initiated": error_response.recovery_initiated,
            "estimated_time": error_response.estimated_recovery_time,
            "fallback_active": error_response.fallback_active,
        }

        # Add category-specific guidance
        if error_response.category.value == "database":
            guidance["monitoring_points"] = [
                "Database connection pool status",
                "Query execution times",
                "Lock contention metrics",
            ]
        elif error_response.category.value == "cache":
            guidance["monitoring_points"] = [
                "Redis service health",
                "Cache hit/miss ratios",
                "Memory usage patterns",
            ]
        elif error_response.category.value == "network":
            guidance["monitoring_points"] = [
                "Network latency metrics",
                "DNS resolution times",
                "External service availability",
            ]

        return guidance


# Singleton instance
_error_response_formatter_instance: Optional[ErrorResponseFormatter] = None


def get_error_response_formatter() -> ErrorResponseFormatter:
    """Get singleton ErrorResponseFormatter instance"""
    global _error_response_formatter_instance
    if _error_response_formatter_instance is None:
        _error_response_formatter_instance = ErrorResponseFormatter()
    return _error_response_formatter_instance
