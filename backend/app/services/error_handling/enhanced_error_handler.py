"""
Enhanced Error Handler

Comprehensive error handling system that integrates with service health monitoring,
fallback orchestration, and error recovery systems to provide structured logging,
user-friendly messages, and intelligent error recovery.

Key Features:
- Structured error logging without sensitive data exposure
- User-friendly error messages with contextual guidance
- Integration with service health and fallback systems
- Automatic error classification and severity assessment
- Developer debug information (when appropriate)
- Error pattern learning and optimization
- Monitoring and alerting integration

Error Handling Flow:
1. Error Classification: Determine error type and severity
2. Context Analysis: Gather relevant context without sensitive data
3. Recovery Assessment: Check if automatic recovery is possible
4. User Communication: Generate appropriate user-facing messages
5. Developer Information: Provide debug info for development
6. Recovery Initiation: Trigger appropriate recovery mechanisms
"""

import traceback
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security.cache_encryption import sanitize_for_logging
from app.services.auth.fallback_orchestrator import (
    FallbackOrchestrator,
    OperationType,
    get_fallback_orchestrator,
)
from app.services.monitoring.service_health_manager import (
    ServiceHealthManager,
    ServiceType,
    get_service_health_manager,
)
from app.services.recovery.error_recovery_system import (
    ErrorRecoverySystem,
    FailureCategory,
    RecoveryPriority,
    RecoveryType,
    get_error_recovery_system,
)

logger = get_logger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""

    LOW = "low"  # Minor issues, non-blocking
    MEDIUM = "medium"  # Degraded functionality
    HIGH = "high"  # Significant functionality loss
    CRITICAL = "critical"  # System or security critical


class ErrorCategory(str, Enum):
    """Error categories for classification"""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    SERVICE_UNAVAILABLE = "service_unavailable"
    RATE_LIMITING = "rate_limiting"
    CONFIGURATION = "configuration"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class UserAudience(str, Enum):
    """Target audience for error messages"""

    END_USER = "end_user"  # Regular application users
    ADMIN_USER = "admin_user"  # Administrative users
    DEVELOPER = "developer"  # Developers and support staff
    SYSTEM = "system"  # System-to-system communication


@dataclass
class ErrorContext:
    """Context information for error handling"""

    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: Optional[OperationType] = None
    service_type: Optional[ServiceType] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None

    # Sanitized context data (no sensitive information)
    context_data: Dict[str, Any] = field(default_factory=dict)

    # System state at time of error
    system_health: Optional[str] = None
    active_fallbacks: List[str] = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ErrorClassification:
    """Classification result for an error"""

    category: ErrorCategory
    severity: ErrorSeverity
    is_recoverable: bool
    recovery_type: Optional[RecoveryType] = None
    failure_category: Optional[FailureCategory] = None
    confidence: float = 1.0  # Confidence in classification (0.0-1.0)

    # Service implications
    affected_services: Set[ServiceType] = field(default_factory=set)
    fallback_recommended: bool = False

    # Recovery recommendations
    recovery_priority: RecoveryPriority = RecoveryPriority.NORMAL
    max_retry_attempts: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "is_recoverable": self.is_recoverable,
            "recovery_type": self.recovery_type.value if self.recovery_type else None,
            "failure_category": (
                self.failure_category.value if self.failure_category else None
            ),
            "confidence": self.confidence,
            "affected_services": [s.value for s in self.affected_services],
            "fallback_recommended": self.fallback_recommended,
            "recovery_priority": self.recovery_priority.value,
            "max_retry_attempts": self.max_retry_attempts,
        }


@dataclass
class ErrorResponse:
    """Structured error response"""

    # User-facing information
    error_code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recovery_suggestions: List[str] = field(default_factory=list)

    # System information
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.UNKNOWN

    # Developer information (only in development)
    debug_info: Optional[Dict[str, Any]] = None

    # Recovery information
    recovery_initiated: bool = False
    fallback_active: bool = False
    estimated_recovery_time: Optional[int] = None  # seconds

    def to_dict(self, audience: UserAudience = UserAudience.END_USER) -> Dict[str, Any]:
        """Convert to dictionary based on target audience"""
        response = {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "recovery_suggestions": self.recovery_suggestions,
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "category": self.category.value,
        }

        # Add system information for admin and developer audiences
        if audience in [UserAudience.ADMIN_USER, UserAudience.DEVELOPER]:
            response.update(
                {
                    "recovery_initiated": self.recovery_initiated,
                    "fallback_active": self.fallback_active,
                    "estimated_recovery_time": self.estimated_recovery_time,
                }
            )

        # Add debug information for developers
        if audience == UserAudience.DEVELOPER and self.debug_info:
            response["debug_info"] = self.debug_info

        return response


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
    ):
        self.health_manager = health_manager or get_service_health_manager()
        self.fallback_orchestrator = (
            fallback_orchestrator or get_fallback_orchestrator()
        )
        self.recovery_system = recovery_system or get_error_recovery_system()

        # Error pattern learning
        self.error_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.classification_cache: Dict[str, ErrorClassification] = {}

        # Message templates
        self.message_templates = self._initialize_message_templates()

        # Configuration
        self.enable_debug_info = getattr(settings, "DEBUG", False)
        self.enable_recovery = getattr(settings, "ERROR_RECOVERY_ENABLED", True)
        self.enable_pattern_learning = getattr(settings, "ERROR_PATTERN_LEARNING", True)

        logger.info(
            "EnhancedErrorHandler initialized with intelligent recovery capabilities"
        )

    def _initialize_message_templates(
        self,
    ) -> Dict[ErrorCategory, Dict[UserAudience, Dict[str, Any]]]:
        """Initialize error message templates for different categories and audiences"""
        return {
            ErrorCategory.AUTHENTICATION: {
                UserAudience.END_USER: {
                    "message": "Authentication failed. Please check your credentials.",
                    "suggestions": [
                        "Verify your username and password",
                        "Check if your account is locked",
                        "Try resetting your password if needed",
                    ],
                },
                UserAudience.ADMIN_USER: {
                    "message": "Authentication service error detected.",
                    "suggestions": [
                        "Check authentication service health",
                        "Verify user account status",
                        "Review authentication logs",
                    ],
                },
                UserAudience.DEVELOPER: {
                    "message": "Authentication error in auth service pipeline.",
                    "suggestions": [
                        "Check auth service connectivity",
                        "Verify JWT token validation",
                        "Review authentication middleware logs",
                    ],
                },
            },
            ErrorCategory.CACHE: {
                UserAudience.END_USER: {
                    "message": "System is running slower than usual. Please be patient.",
                    "suggestions": [
                        "Your request is being processed",
                        "Performance will improve shortly",
                        "Try refreshing the page if needed",
                    ],
                },
                UserAudience.ADMIN_USER: {
                    "message": "Cache service degradation detected.",
                    "suggestions": [
                        "Check Redis service status",
                        "Review cache performance metrics",
                        "Consider manual cache warmup",
                    ],
                },
                UserAudience.DEVELOPER: {
                    "message": "Cache layer failure, fallback systems active.",
                    "suggestions": [
                        "Check Redis connectivity and health",
                        "Review cache miss rates",
                        "Verify fallback cache configuration",
                    ],
                },
            },
            ErrorCategory.DATABASE: {
                UserAudience.END_USER: {
                    "message": "We're experiencing technical difficulties. Please try again in a moment.",
                    "suggestions": [
                        "Your data is safe",
                        "Try your request again in a few minutes",
                        "Contact support if the issue persists",
                    ],
                },
                UserAudience.ADMIN_USER: {
                    "message": "Database service error detected.",
                    "suggestions": [
                        "Check database connectivity",
                        "Review database performance metrics",
                        "Verify backup systems are functioning",
                    ],
                },
                UserAudience.DEVELOPER: {
                    "message": "Database connection or query error.",
                    "suggestions": [
                        "Check database connection pool",
                        "Review slow query logs",
                        "Verify database schema integrity",
                    ],
                },
            },
            ErrorCategory.SERVICE_UNAVAILABLE: {
                UserAudience.END_USER: {
                    "message": "Service temporarily unavailable. We're working to restore it.",
                    "suggestions": [
                        "Please try again in a few minutes",
                        "Check our status page for updates",
                        "Your data and settings are preserved",
                    ],
                },
                UserAudience.ADMIN_USER: {
                    "message": "Critical service unavailability detected.",
                    "suggestions": [
                        "Review service health dashboard",
                        "Check if failover systems are active",
                        "Consider manual service restart",
                    ],
                },
                UserAudience.DEVELOPER: {
                    "message": "Service circuit breaker activated or service down.",
                    "suggestions": [
                        "Check service health endpoints",
                        "Review circuit breaker status",
                        "Verify service dependencies",
                    ],
                },
            },
            ErrorCategory.NETWORK: {
                UserAudience.END_USER: {
                    "message": "Connection timeout. Please check your internet connection.",
                    "suggestions": [
                        "Check your internet connection",
                        "Try refreshing the page",
                        "Wait a moment and try again",
                    ],
                },
                UserAudience.ADMIN_USER: {
                    "message": "Network connectivity issues detected.",
                    "suggestions": [
                        "Check network infrastructure",
                        "Review network monitoring alerts",
                        "Verify external service connectivity",
                    ],
                },
                UserAudience.DEVELOPER: {
                    "message": "Network timeout or connectivity error.",
                    "suggestions": [
                        "Check network configuration",
                        "Review timeout settings",
                        "Verify DNS resolution",
                    ],
                },
            },
        }

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
            classification = await self._classify_error(error, context)

            # Enrich context with system state
            await self._enrich_context_with_system_state(context)

            # Generate structured error response
            error_response = await self._generate_error_response(
                error, classification, context, audience
            )

            # Log the error (structured and sanitized)
            await self._log_error_structured(
                error, classification, context, error_response
            )

            # Initiate recovery if appropriate
            if (
                self.enable_recovery
                and classification.is_recoverable
                and operation_func is not None
            ):
                recovery_initiated = await self._initiate_recovery(
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
                await self._learn_from_error_pattern(error, classification, context)

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
                category=ErrorCategory.SYSTEM,
                recovery_suggestions=[
                    "Please try your request again",
                    "Contact support if the issue persists",
                ],
                error_id=context.error_id,
            )

    async def _classify_error(
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

    async def _enrich_context_with_system_state(self, context: ErrorContext):
        """Enrich error context with current system state"""
        try:
            # Get system health status
            system_health = await self.health_manager.get_system_health_status()
            context.system_health = system_health.overall_health.value

            # Get active fallbacks
            if system_health.fallback_active:
                context.active_fallbacks = [
                    service.value for service in system_health.failed_services
                ]

        except Exception as e:
            logger.warning(f"Failed to enrich error context with system state: {e}")

    async def _generate_error_response(
        self,
        error: Exception,
        classification: ErrorClassification,
        context: ErrorContext,
        audience: UserAudience,
    ) -> ErrorResponse:
        """Generate structured error response"""

        # Get message template for category and audience
        template = self.message_templates.get(classification.category, {}).get(
            audience, {}
        )

        if not template:
            # Fallback to generic message
            template = {
                "message": "An error occurred while processing your request.",
                "suggestions": [
                    "Please try again",
                    "Contact support if the issue persists",
                ],
            }

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
            error_response.recovery_initiated = self.enable_recovery

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

    async def _log_error_structured(
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

    async def _initiate_recovery(
        self,
        error: Exception,
        classification: ErrorClassification,
        context: ErrorContext,
        operation_func: Any,
        operation_args: Tuple,
        operation_kwargs: Dict[str, Any],
    ) -> bool:
        """Initiate recovery process for recoverable errors"""

        try:
            # Schedule recovery operation
            recovery_id = await self.recovery_system.schedule_recovery_operation(
                operation_func=operation_func,
                operation_args=operation_args,
                operation_kwargs=operation_kwargs,
                recovery_type=classification.recovery_type
                or RecoveryType.IMMEDIATE_RETRY,
                failure_category=classification.failure_category
                or FailureCategory.UNKNOWN,
                priority=classification.recovery_priority,
                operation_type=context.operation_type or OperationType.CACHE_READ,
                service_type=context.service_type or ServiceType.REDIS,
                context_data=sanitize_for_logging(context.context_data),
                max_retry_attempts=classification.max_retry_attempts,
            )

            logger.info(
                f"Recovery initiated for error {context.error_id}: recovery_id={recovery_id}",
                extra={
                    "error_id": context.error_id,
                    "recovery_id": recovery_id,
                    "recovery_type": (
                        classification.recovery_type.value
                        if classification.recovery_type
                        else None
                    ),
                },
            )

            return True

        except Exception as recovery_error:
            logger.error(
                f"Failed to initiate recovery for error {context.error_id}: {recovery_error}",
                extra={"error_id": context.error_id},
            )
            return False

    async def _learn_from_error_pattern(
        self,
        error: Exception,
        classification: ErrorClassification,
        context: ErrorContext,
    ):
        """Learn from error patterns for improved classification"""

        try:
            pattern_key = f"{classification.category.value}:{type(error).__name__}"

            pattern_data = {
                "timestamp": context.timestamp.isoformat(),
                "error_type": type(error).__name__,
                "classification": classification.to_dict(),
                "context_summary": {
                    "operation_type": (
                        context.operation_type.value if context.operation_type else None
                    ),
                    "service_type": (
                        context.service_type.value if context.service_type else None
                    ),
                    "system_health": context.system_health,
                },
            }

            self.error_patterns[pattern_key].append(pattern_data)

            # Keep only recent patterns (last 100 per pattern)
            if len(self.error_patterns[pattern_key]) > 100:
                self.error_patterns[pattern_key] = self.error_patterns[pattern_key][
                    -100:
                ]

        except Exception as learning_error:
            logger.warning(f"Failed to learn from error pattern: {learning_error}")

    async def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics"""
        pattern_stats = {}

        for pattern_key, patterns in self.error_patterns.items():
            recent_patterns = [
                p
                for p in patterns
                if datetime.fromisoformat(p["timestamp"])
                > datetime.utcnow() - timedelta(hours=24)
            ]

            pattern_stats[pattern_key] = {
                "total_occurrences": len(patterns),
                "recent_24h": len(recent_patterns),
                "latest_occurrence": patterns[-1]["timestamp"] if patterns else None,
            }

        return {
            "total_patterns_learned": len(self.error_patterns),
            "classification_cache_size": len(self.classification_cache),
            "pattern_statistics": pattern_stats,
            "configuration": {
                "debug_info_enabled": self.enable_debug_info,
                "recovery_enabled": self.enable_recovery,
                "pattern_learning_enabled": self.enable_pattern_learning,
            },
        }

    async def clear_error_patterns(self) -> int:
        """Clear learned error patterns"""
        count = len(self.error_patterns)
        self.error_patterns.clear()
        self.classification_cache.clear()

        logger.info(f"Cleared {count} error patterns from learning cache")
        return count


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
