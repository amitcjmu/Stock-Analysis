"""
Flow Error Handler

Handles error patterns, retry logic, recovery mechanisms, and error classification.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.exceptions import (CrewAIExecutionError, FlowError,
                                 FlowNotFoundError, InvalidFlowStateError)
from app.core.logging import get_logger
from app.services.flow_error_handler import ErrorContext
from app.services.flow_error_handler import \
    FlowErrorHandler as BaseFlowErrorHandler
from app.services.flow_error_handler import RetryConfig

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error category types"""

    VALIDATION = "validation"
    EXECUTION = "execution"
    NETWORK = "network"
    DATABASE = "database"
    PERMISSION = "permission"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    BUSINESS_LOGIC = "business_logic"
    UNKNOWN = "unknown"


class FlowErrorHandler:
    """
    Enhanced error handling for flow operations with classification, retry logic, and recovery mechanisms.
    """

    def __init__(self):
        """Initialize the Flow Error Handler"""
        self.base_handler = BaseFlowErrorHandler()
        self.error_history: Dict[str, List[Dict[str, Any]]] = {}
        self.recovery_strategies: Dict[str, callable] = {}
        self._register_recovery_strategies()

        logger.info("✅ Flow Error Handler initialized")

    def _register_recovery_strategies(self):
        """Register recovery strategies for different error types"""
        self.recovery_strategies = {
            ErrorCategory.DATABASE.value: self._recover_database_error,
            ErrorCategory.NETWORK.value: self._recover_network_error,
            ErrorCategory.TIMEOUT.value: self._recover_timeout_error,
            ErrorCategory.RESOURCE.value: self._recover_resource_error,
            ErrorCategory.VALIDATION.value: self._recover_validation_error,
            ErrorCategory.EXECUTION.value: self._recover_execution_error,
            ErrorCategory.PERMISSION.value: self._recover_permission_error,
            ErrorCategory.BUSINESS_LOGIC.value: self._recover_business_logic_error,
        }

    async def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        retry_config: Optional[RetryConfig] = None,
    ) -> Dict[str, Any]:
        """
        Handle errors with enhanced classification and recovery

        Args:
            error: The exception that occurred
            context: Context information about the error
            retry_config: Configuration for retry behavior

        Returns:
            Error handling result with recovery recommendations
        """
        try:
            # Classify the error
            error_classification = self._classify_error(error)

            # Record error in history
            self._record_error(context.flow_id, error, error_classification, context)

            # Use base handler for retry logic
            base_result = await self.base_handler.handle_error(
                error, context, retry_config
            )

            # Enhance with classification and recovery
            enhanced_result = {
                **base_result.metadata,
                "error_classification": error_classification,
                "severity": error_classification["severity"],
                "category": error_classification["category"],
                "recovery_strategy": error_classification.get("recovery_strategy"),
                "should_retry": base_result.should_retry,
                "retry_delay": base_result.retry_delay,
                "retry_count": getattr(base_result, "retry_count", 0),
                "timestamp": datetime.utcnow().isoformat(),
                "context": {
                    "operation": context.operation,
                    "flow_id": context.flow_id,
                    "flow_type": getattr(context, "flow_type", None),
                    "phase": getattr(context, "phase", None),
                    "user_id": context.user_id,
                },
            }

            # Apply recovery strategy if available
            if error_classification.get("recovery_strategy"):
                try:
                    recovery_result = await self._apply_recovery_strategy(
                        error_classification["category"],
                        error,
                        context,
                        error_classification,
                    )
                    enhanced_result["recovery_result"] = recovery_result
                except Exception as recovery_error:
                    logger.error(f"❌ Recovery strategy failed: {recovery_error}")
                    enhanced_result["recovery_error"] = str(recovery_error)

            logger.info(
                f"🔧 Error handled: {error_classification['category']} - {error_classification['severity']}"
            )

            return enhanced_result

        except Exception as handler_error:
            logger.error(f"❌ Error handler failed: {handler_error}")
            return {
                "should_retry": False,
                "retry_delay": 0,
                "error_classification": {
                    "category": ErrorCategory.UNKNOWN.value,
                    "severity": ErrorSeverity.CRITICAL.value,
                    "message": "Error handler failure",
                },
                "handler_error": str(handler_error),
            }

    def _classify_error(self, error: Exception) -> Dict[str, Any]:
        """
        Classify an error by type, severity, and recovery strategy

        Args:
            error: The exception to classify

        Returns:
            Error classification information
        """
        type(error).__name__
        error_message = str(error).lower()

        # Database errors
        if any(
            db_term in error_message
            for db_term in ["database", "sql", "connection", "session", "integrity"]
        ):
            return {
                "category": ErrorCategory.DATABASE.value,
                "severity": ErrorSeverity.HIGH.value,
                "recovery_strategy": "database_recovery",
                "retryable": True,
                "max_retries": 3,
                "backoff_multiplier": 2,
            }

        # Network errors
        if any(
            net_term in error_message
            for net_term in ["network", "connection", "timeout", "unreachable"]
        ):
            return {
                "category": ErrorCategory.NETWORK.value,
                "severity": ErrorSeverity.MEDIUM.value,
                "recovery_strategy": "network_recovery",
                "retryable": True,
                "max_retries": 5,
                "backoff_multiplier": 1.5,
            }

        # Validation errors
        if any(
            val_term in error_message
            for val_term in ["validation", "invalid", "required", "missing"]
        ):
            return {
                "category": ErrorCategory.VALIDATION.value,
                "severity": ErrorSeverity.LOW.value,
                "recovery_strategy": "validation_recovery",
                "retryable": False,
                "max_retries": 0,
                "backoff_multiplier": 1,
            }

        # Permission errors
        if any(
            perm_term in error_message
            for perm_term in ["permission", "unauthorized", "forbidden", "access"]
        ):
            return {
                "category": ErrorCategory.PERMISSION.value,
                "severity": ErrorSeverity.HIGH.value,
                "recovery_strategy": "permission_recovery",
                "retryable": False,
                "max_retries": 0,
                "backoff_multiplier": 1,
            }

        # Timeout errors
        if any(
            timeout_term in error_message
            for timeout_term in ["timeout", "deadline", "expired"]
        ):
            return {
                "category": ErrorCategory.TIMEOUT.value,
                "severity": ErrorSeverity.MEDIUM.value,
                "recovery_strategy": "timeout_recovery",
                "retryable": True,
                "max_retries": 3,
                "backoff_multiplier": 2,
            }

        # Resource errors
        if any(
            res_term in error_message
            for res_term in ["memory", "disk", "resource", "limit", "quota"]
        ):
            return {
                "category": ErrorCategory.RESOURCE.value,
                "severity": ErrorSeverity.HIGH.value,
                "recovery_strategy": "resource_recovery",
                "retryable": True,
                "max_retries": 2,
                "backoff_multiplier": 3,
            }

        # CrewAI execution errors
        if isinstance(error, CrewAIExecutionError) or "crewai" in error_message:
            return {
                "category": ErrorCategory.EXECUTION.value,
                "severity": ErrorSeverity.HIGH.value,
                "recovery_strategy": "execution_recovery",
                "retryable": True,
                "max_retries": 2,
                "backoff_multiplier": 2,
            }

        # Flow-specific errors
        if isinstance(error, (FlowError, FlowNotFoundError, InvalidFlowStateError)):
            return {
                "category": ErrorCategory.BUSINESS_LOGIC.value,
                "severity": ErrorSeverity.MEDIUM.value,
                "recovery_strategy": "business_logic_recovery",
                "retryable": isinstance(error, FlowError),
                "max_retries": 1,
                "backoff_multiplier": 1,
            }

        # Default classification
        return {
            "category": ErrorCategory.UNKNOWN.value,
            "severity": ErrorSeverity.MEDIUM.value,
            "recovery_strategy": None,
            "retryable": False,
            "max_retries": 0,
            "backoff_multiplier": 1,
        }

    def _record_error(
        self,
        flow_id: str,
        error: Exception,
        classification: Dict[str, Any],
        context: ErrorContext,
    ):
        """Record error in history for analysis"""
        if flow_id not in self.error_history:
            self.error_history[flow_id] = []

        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "classification": classification,
            "context": {
                "operation": context.operation,
                "flow_type": getattr(context, "flow_type", None),
                "phase": getattr(context, "phase", None),
                "user_id": context.user_id,
            },
        }

        self.error_history[flow_id].append(error_record)

        # Keep only last 10 errors per flow
        if len(self.error_history[flow_id]) > 10:
            self.error_history[flow_id] = self.error_history[flow_id][-10:]

    async def _apply_recovery_strategy(
        self,
        category: str,
        error: Exception,
        context: ErrorContext,
        classification: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply recovery strategy based on error category"""
        strategy = self.recovery_strategies.get(category)
        if not strategy:
            return {
                "status": "no_strategy",
                "message": f"No recovery strategy for {category}",
            }

        try:
            return await strategy(error, context, classification)
        except Exception as e:
            logger.error(f"❌ Recovery strategy failed for {category}: {e}")
            return {"status": "failed", "error": str(e)}

    async def _recover_database_error(
        self, error: Exception, context: ErrorContext, classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recovery strategy for database errors"""
        return {
            "status": "attempting_recovery",
            "strategy": "database_recovery",
            "actions": [
                "Retry with fresh database session",
                "Check database connection health",
                "Validate transaction state",
            ],
            "recommendations": [
                "Consider database connection pooling",
                "Check for long-running transactions",
                "Monitor database performance",
            ],
        }

    async def _recover_network_error(
        self, error: Exception, context: ErrorContext, classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recovery strategy for network errors"""
        return {
            "status": "attempting_recovery",
            "strategy": "network_recovery",
            "actions": [
                "Retry with exponential backoff",
                "Check network connectivity",
                "Validate service endpoints",
            ],
            "recommendations": [
                "Implement circuit breaker pattern",
                "Add health checks for external services",
                "Consider request timeout adjustments",
            ],
        }

    async def _recover_timeout_error(
        self, error: Exception, context: ErrorContext, classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recovery strategy for timeout errors"""
        return {
            "status": "attempting_recovery",
            "strategy": "timeout_recovery",
            "actions": [
                "Retry with increased timeout",
                "Check system load",
                "Validate operation complexity",
            ],
            "recommendations": [
                "Optimize slow operations",
                "Implement operation chunking",
                "Add progress tracking",
            ],
        }

    async def _recover_resource_error(
        self, error: Exception, context: ErrorContext, classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recovery strategy for resource errors"""
        return {
            "status": "attempting_recovery",
            "strategy": "resource_recovery",
            "actions": [
                "Wait for resource availability",
                "Check system resources",
                "Validate memory usage",
            ],
            "recommendations": [
                "Implement resource monitoring",
                "Add resource cleanup mechanisms",
                "Consider operation batching",
            ],
        }

    async def _recover_validation_error(
        self, error: Exception, context: ErrorContext, classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recovery strategy for validation errors"""
        return {
            "status": "requires_user_action",
            "strategy": "validation_recovery",
            "actions": [
                "Validate input data",
                "Check required fields",
                "Verify data format",
            ],
            "recommendations": [
                "Improve input validation",
                "Add user guidance",
                "Implement data sanitization",
            ],
        }

    async def _recover_execution_error(
        self, error: Exception, context: ErrorContext, classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recovery strategy for execution errors"""
        return {
            "status": "attempting_recovery",
            "strategy": "execution_recovery",
            "actions": [
                "Retry with clean state",
                "Check execution environment",
                "Validate system dependencies",
            ],
            "recommendations": [
                "Add execution monitoring",
                "Implement graceful degradation",
                "Consider alternative execution paths",
            ],
        }

    async def _recover_permission_error(
        self, error: Exception, context: ErrorContext, classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recovery strategy for permission errors"""
        return {
            "status": "requires_admin_action",
            "strategy": "permission_recovery",
            "actions": [
                "Check user permissions",
                "Validate access rights",
                "Verify authentication",
            ],
            "recommendations": [
                "Review user role assignments",
                "Check tenant isolation",
                "Validate security policies",
            ],
        }

    async def _recover_business_logic_error(
        self, error: Exception, context: ErrorContext, classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recovery strategy for business logic errors"""
        return {
            "status": "analyzing_error",
            "strategy": "business_logic_recovery",
            "actions": [
                "Analyze business rule violation",
                "Check flow state consistency",
                "Validate operation sequence",
            ],
            "recommendations": [
                "Review business rules",
                "Add state validation",
                "Implement operation guards",
            ],
        }

    def get_error_history(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get error history for a specific flow"""
        return self.error_history.get(flow_id, [])

    def get_error_statistics(self, flow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get error statistics for analysis"""
        if flow_id:
            errors = self.error_history.get(flow_id, [])
        else:
            errors = []
            for flow_errors in self.error_history.values():
                errors.extend(flow_errors)

        if not errors:
            return {"total_errors": 0, "categories": {}, "severities": {}}

        # Categorize errors
        categories = {}
        severities = {}

        for error in errors:
            category = error["classification"]["category"]
            severity = error["classification"]["severity"]

            categories[category] = categories.get(category, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1

        return {
            "total_errors": len(errors),
            "categories": categories,
            "severities": severities,
            "most_common_category": (
                max(categories, key=categories.get) if categories else None
            ),
            "most_common_severity": (
                max(severities, key=severities.get) if severities else None
            ),
        }

    def clear_error_history(self, flow_id: Optional[str] = None):
        """Clear error history for a flow or all flows"""
        if flow_id:
            self.error_history.pop(flow_id, None)
        else:
            self.error_history.clear()

        logger.info(
            f"🧹 Cleared error history for {'flow ' + flow_id if flow_id else 'all flows'}"
        )
