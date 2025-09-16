"""
Enhanced Error Handler - Main Handler Class

Main EnhancedErrorHandler class that orchestrates error handling operations.
Integrates all components to provide comprehensive error handling with
intelligent recovery and structured logging.

Key Features:
- Comprehensive error processing pipeline
- Integration with service health and recovery systems
- Automatic error classification and recovery
- Structured error logging and reporting
- Pattern learning and optimization
"""

from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger
from app.services.auth.fallback_orchestrator import (
    FallbackOrchestrator,
    get_fallback_orchestrator,
)
from app.services.monitoring.service_health_manager import (
    ServiceHealthManager,
    get_service_health_manager,
)
from app.services.recovery.error_recovery_system import (
    ErrorRecoverySystem,
    get_error_recovery_system,
)

from .base import ErrorContext, ErrorResponse, ErrorSeverity, UserAudience
from .formatters import ErrorResponseFormatter, get_error_response_formatter
from .recovery import ErrorRecoveryManager, get_error_recovery_manager
from .strategies import ErrorClassificationStrategy, get_error_classification_strategy
from .utils import ErrorHandlerUtils, get_error_handler_utils

logger = get_logger(__name__)


class EnhancedErrorHandler:
    """
    Enhanced Error Handler with Intelligent Recovery

    Provides comprehensive error handling with structured logging, user-friendly
    messages, and integration with service health and recovery systems.
    """

    def __init__(
        self,
        health_manager: Optional[ServiceHealthManager] = None,
        fallback_orchestrator: Optional[FallbackOrchestrator] = None,
        recovery_system: Optional[ErrorRecoverySystem] = None,
        classification_strategy: Optional[ErrorClassificationStrategy] = None,
        response_formatter: Optional[ErrorResponseFormatter] = None,
        recovery_manager: Optional[ErrorRecoveryManager] = None,
        utils: Optional[ErrorHandlerUtils] = None,
    ):
        # Core dependencies
        self.health_manager = health_manager or get_service_health_manager()
        self.fallback_orchestrator = (
            fallback_orchestrator or get_fallback_orchestrator()
        )
        self.recovery_system = recovery_system or get_error_recovery_system()

        # Error handling components
        self.classification_strategy = (
            classification_strategy or get_error_classification_strategy()
        )
        self.response_formatter = response_formatter or get_error_response_formatter()
        self.recovery_manager = recovery_manager or get_error_recovery_manager()
        self.utils = utils or get_error_handler_utils()

        # Configuration
        self.enable_debug_info = getattr(settings, "DEBUG", False)
        self.enable_recovery = getattr(settings, "ERROR_RECOVERY_ENABLED", True)
        self.enable_pattern_learning = getattr(settings, "ERROR_PATTERN_LEARNING", True)

        logger.info(
            "EnhancedErrorHandler initialized with intelligent recovery capabilities"
        )

    async def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        audience: UserAudience = UserAudience.END_USER,
        operation_func: Optional[Any] = None,
        operation_args: Optional[Tuple] = None,
        operation_kwargs: Optional[Dict[str, Any]] = None,
    ) -> ErrorResponse:
        """
        Handle an error with comprehensive error processing

        Args:
            error: The exception that occurred
            context: Error context information
            audience: Target audience for the error message
            operation_func: Function that failed (for recovery)
            operation_args: Arguments for the failed operation
            operation_kwargs: Keyword arguments for the failed operation

        Returns:
            ErrorResponse: Structured error response
        """
        if context is None:
            context = ErrorContext()

        try:
            # Classify the error
            classification = await self.classification_strategy.classify_error(
                error, context
            )

            # Enrich context with system state
            await self.utils.enrich_context_with_system_state(context)

            # Generate structured error response
            error_response = await self.response_formatter.generate_error_response(
                error, classification, context, audience
            )

            # Log the error (structured and sanitized)
            await self.response_formatter.log_error_structured(
                error, classification, context, error_response
            )

            # Initiate recovery if appropriate
            if (
                self.enable_recovery
                and classification.is_recoverable
                and operation_func is not None
            ):
                recovery_initiated = await self.recovery_manager.initiate_recovery(
                    error,
                    classification,
                    context,
                    operation_func,
                    operation_args or (),
                    operation_kwargs or {},
                )
                error_response.recovery_initiated = recovery_initiated

            # Learn from error pattern if enabled
            if self.enable_pattern_learning:
                await self.recovery_manager.learn_from_error_pattern(
                    error, classification, context
                )

            return error_response

        except Exception as handling_error:
            # Fallback error handling
            logger.critical(
                f"Error in error handler: {handling_error}",
                exc_info=True,
                extra={
                    "original_error": str(error),
                    "context_error_id": context.error_id,
                },
            )

            return ErrorResponse(
                error_code="SYS_ERROR_HANDLER_FAILURE",
                message="An error occurred while processing your request.",
                severity=ErrorSeverity.CRITICAL,
                category=self.classification_strategy.message_templates.get(
                    "SYSTEM", {}
                ).get("category", "system"),
                recovery_suggestions=[
                    "Please try your request again",
                    "Contact support if the issue persists",
                ],
                error_id=context.error_id,
            )

    async def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error handling statistics"""
        return self.utils.get_error_statistics()

    async def clear_error_patterns(self) -> int:
        """Clear learned error patterns"""
        return self.recovery_manager.clear_error_patterns()

    async def clear_all_caches(self) -> Dict[str, int]:
        """Clear all error handling caches"""
        return self.utils.clear_all_caches()

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate error handler configuration"""
        return self.utils.validate_configuration()

    async def get_recovery_recommendations(
        self, error_category: str, service_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get recovery recommendations for an error category"""
        recommendations = self.recovery_manager.get_recovery_recommendations(
            error_category, service_type
        )

        return {
            "category": error_category,
            "service_type": service_type,
            "recommendations": recommendations,
            "timestamp": (
                context.timestamp.isoformat() if hasattr(self, "context") else None
            ),
        }

    def format_user_message(
        self, error_response: ErrorResponse, audience: UserAudience
    ) -> str:
        """Format user-friendly error message"""
        return self.response_formatter.format_user_message(error_response, audience)

    def get_recovery_guidance(self, error_response: ErrorResponse) -> dict:
        """Get detailed recovery guidance for an error"""
        return self.response_formatter.get_recovery_guidance(error_response)


# Singleton instance
_enhanced_error_handler_instance: Optional[EnhancedErrorHandler] = None


def get_enhanced_error_handler() -> EnhancedErrorHandler:
    """Get singleton EnhancedErrorHandler instance"""
    global _enhanced_error_handler_instance
    if _enhanced_error_handler_instance is None:
        _enhanced_error_handler_instance = EnhancedErrorHandler()
    return _enhanced_error_handler_instance


# Cleanup function for app shutdown
async def shutdown_enhanced_error_handler():
    """Shutdown enhanced error handler (call during app shutdown)"""
    global _enhanced_error_handler_instance
    if _enhanced_error_handler_instance:
        await _enhanced_error_handler_instance.clear_error_patterns()
        _enhanced_error_handler_instance = None
