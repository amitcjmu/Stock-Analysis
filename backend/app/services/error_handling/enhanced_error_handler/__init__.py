"""
Enhanced Error Handler Module

Comprehensive error handling system that integrates with service health monitoring,
fallback orchestration, and error recovery systems to provide structured logging,
user-friendly messages, and intelligent error recovery.

This module maintains 100% backward compatibility with the original enhanced_error_handler.py
by exposing all public APIs through this __init__.py file.

Key Features:
- Structured error logging without sensitive data exposure
- User-friendly error messages with contextual guidance
- Integration with service health and fallback systems
- Automatic error classification and severity assessment
- Developer debug information (when appropriate)
- Error pattern learning and optimization
- Monitoring and alerting integration

Public API:
- EnhancedErrorHandler: Main error handler class
- ErrorSeverity: Error severity levels enum
- ErrorCategory: Error categories enum
- UserAudience: Target audience for error messages
- ErrorContext: Context information for error handling
- ErrorClassification: Classification result for an error
- ErrorResponse: Structured error response
- get_enhanced_error_handler: Singleton instance getter
- shutdown_enhanced_error_handler: Cleanup function
"""

# Import all public classes and functions to maintain backward compatibility
from .base import (
    ErrorCategory,
    ErrorClassification,
    ErrorContext,
    ErrorResponse,
    ErrorSeverity,
    UserAudience,
)
from .formatters import ErrorResponseFormatter, get_error_response_formatter
from .handler import (
    EnhancedErrorHandler,
    get_enhanced_error_handler,
    shutdown_enhanced_error_handler,
)
from .recovery import (
    ErrorRecoveryManager,
    get_error_recovery_manager,
    shutdown_error_recovery_manager,
)
from .strategies import ErrorClassificationStrategy, get_error_classification_strategy
from .templates import get_message_templates
from .utils import (
    ErrorHandlerUtils,
    get_error_handler_utils,
    shutdown_error_handler_utils,
)

# Maintain the exact same public API as the original file
__all__ = [
    # Core classes and enums
    "ErrorSeverity",
    "ErrorCategory",
    "UserAudience",
    "ErrorContext",
    "ErrorClassification",
    "ErrorResponse",
    # Main handler class
    "EnhancedErrorHandler",
    # Component classes
    "ErrorClassificationStrategy",
    "ErrorResponseFormatter",
    "ErrorRecoveryManager",
    "ErrorHandlerUtils",
    # Singleton getters
    "get_enhanced_error_handler",
    "get_error_classification_strategy",
    "get_error_response_formatter",
    "get_error_recovery_manager",
    "get_error_handler_utils",
    "get_message_templates",
    # Shutdown functions
    "shutdown_enhanced_error_handler",
    "shutdown_error_recovery_manager",
    "shutdown_error_handler_utils",
]

# For any code that imports specific attributes, ensure they're available at module level
# This maintains compatibility with imports like:
# from app.services.error_handling.enhanced_error_handler import ErrorSeverity

# OperationType import removed as it's not used
