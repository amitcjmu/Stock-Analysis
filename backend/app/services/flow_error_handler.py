"""
Flow Error Handler

Centralized error handling system for all flow types.
Provides comprehensive error strategies, retry logic, and recovery mechanisms.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Type, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import traceback

from app.core.logging import get_logger
from app.core.exceptions import (
    CrewAIExecutionError,
    NetworkTimeoutError,
    ResourceExhaustedError,
    FlowNotFoundError,
    InvalidFlowStateError,
    BackgroundTaskError
)

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    CRITICAL = "critical"    # Flow must stop, cannot recover
    HIGH = "high"           # Flow should stop unless handled
    MEDIUM = "medium"       # Flow can continue with warnings
    LOW = "low"             # Informational, flow continues


class ErrorCategory(Enum):
    """Error categories for classification"""
    VALIDATION = "validation"
    NETWORK = "network"
    DATABASE = "database"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    PERMISSION = "permission"
    BUSINESS_LOGIC = "business_logic"
    CREW_AI = "crew_ai"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for error handling"""
    operation: str
    flow_id: Optional[str] = None
    flow_type: Optional[str] = None
    phase: Optional[str] = None
    user_id: Optional[str] = None
    additional_context: Dict[str, Any] = None
    
    def __post_init__(self):
        self.additional_context = self.additional_context or {}


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = 3
    initial_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0
    jitter: bool = True
    retry_on_errors: List[Type[Exception]] = None
    
    def __post_init__(self):
        if self.retry_on_errors is None:
            self.retry_on_errors = [
                TimeoutError,
                ConnectionError,
                asyncio.TimeoutError
            ]


@dataclass
class ErrorResolution:
    """Result of error handling"""
    action: str  # retry, fail, continue, pause
    should_retry: bool = False
    retry_delay: float = 0.0
    message: str = ""
    user_action_required: bool = False
    update_flow_status: bool = True
    new_status: Optional[str] = None
    severity: ErrorSeverity = ErrorSeverity.HIGH
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        self.metadata = self.metadata or {}


class FlowErrorHandler:
    """
    Centralized error handling for flows.
    Provides strategies for different error types and retry logic.
    """
    
    def __init__(self):
        # Error strategies by exception type
        self._error_strategies: Dict[Type[Exception], Callable] = {
            ValueError: self._handle_validation_error,
            TimeoutError: self._handle_timeout_error,
            ConnectionError: self._handle_network_error,
            PermissionError: self._handle_permission_error,
            RuntimeError: self._handle_runtime_error,
            asyncio.TimeoutError: self._handle_timeout_error,
            CrewAIExecutionError: self._handle_crewai_error,
            NetworkTimeoutError: self._handle_network_timeout_error,
            ResourceExhaustedError: self._handle_resource_error,
            FlowNotFoundError: self._handle_flow_not_found_error,
            InvalidFlowStateError: self._handle_invalid_state_error,
            BackgroundTaskError: self._handle_background_task_error,
        }
        
        # Error category classifiers
        self._category_classifiers = {
            ErrorCategory.VALIDATION: [ValueError, TypeError, AttributeError],
            ErrorCategory.NETWORK: [ConnectionError, TimeoutError, asyncio.TimeoutError, NetworkTimeoutError],
            ErrorCategory.DATABASE: [],  # Add specific DB exceptions
            ErrorCategory.PERMISSION: [PermissionError],
            ErrorCategory.RESOURCE: [MemoryError, OSError, ResourceExhaustedError],
            ErrorCategory.CREW_AI: [CrewAIExecutionError, RuntimeError],  # RuntimeError often from CrewAI
            ErrorCategory.BUSINESS_LOGIC: [FlowNotFoundError, InvalidFlowStateError],
        }
        
        # Retry attempts tracking
        self._retry_attempts: Dict[str, int] = {}
        
        logger.info("✅ Flow Error Handler initialized")
    
    async def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        retry_config: Optional[RetryConfig] = None
    ) -> ErrorResolution:
        """
        Handle an error with appropriate strategy
        
        Args:
            error: The exception that occurred
            context: Error context information
            retry_config: Optional retry configuration
            
        Returns:
            Error resolution with action to take
        """
        retry_config = retry_config or RetryConfig()
        
        # Log the error
        await self._log_error(error, context)
        
        # Classify the error
        error_category = self._classify_error(error)
        
        # Get retry key for tracking attempts
        retry_key = f"{context.flow_id}:{context.operation}"
        current_attempts = self._retry_attempts.get(retry_key, 0)
        
        # Check if error type is retryable
        is_retryable = any(
            isinstance(error, error_type)
            for error_type in retry_config.retry_on_errors
        )
        
        # Apply error strategy
        error_type = type(error)
        strategy = self._error_strategies.get(
            error_type,
            self._handle_generic_error
        )
        
        resolution = await strategy(error, context, error_category)
        
        # Apply retry logic if applicable
        if resolution.should_retry and is_retryable and current_attempts < retry_config.max_retries:
            self._retry_attempts[retry_key] = current_attempts + 1
            
            # Calculate retry delay with exponential backoff
            delay = min(
                retry_config.initial_delay * (retry_config.backoff_multiplier ** current_attempts),
                retry_config.max_delay
            )
            
            # Add jitter if enabled
            if retry_config.jitter:
                import random
                delay *= (0.5 + random.random())
            
            resolution.retry_delay = delay
            resolution.message = (
                f"{resolution.message} Retry attempt {current_attempts + 1}/{retry_config.max_retries} "
                f"in {delay:.1f} seconds."
            )
            
            logger.info(f"🔄 Scheduling retry for {context.operation}: {resolution.message}")
            
        elif current_attempts >= retry_config.max_retries:
            # Max retries exceeded
            resolution.should_retry = False
            resolution.action = "fail"
            resolution.message = f"{resolution.message} Max retries ({retry_config.max_retries}) exceeded."
            resolution.severity = ErrorSeverity.HIGH
            
            # Clear retry attempts
            self._retry_attempts.pop(retry_key, None)
            
            logger.error(f"❌ Max retries exceeded for {context.operation}")
        
        # Store error in context for audit
        resolution.metadata.update({
            "error_type": error_type.__name__,
            "error_category": error_category.value,
            "retry_attempts": current_attempts,
            "timestamp": datetime.utcnow().isoformat(),
            "traceback": traceback.format_exc()
        })
        
        return resolution
    
    def clear_retry_attempts(self, flow_id: str):
        """Clear retry attempts for a flow"""
        keys_to_remove = [
            key for key in self._retry_attempts.keys()
            if key.startswith(f"{flow_id}:")
        ]
        for key in keys_to_remove:
            self._retry_attempts.pop(key, None)
    
    async def _log_error(self, error: Exception, context: ErrorContext):
        """Log error with context"""
        log_message = (
            f"Error in {context.operation} "
            f"[Flow: {context.flow_id}, Type: {context.flow_type}, Phase: {context.phase}]: "
            f"{type(error).__name__}: {str(error)}"
        )
        
        # Use structured logging with context
        logger.error(
            log_message,
            extra={
                "error_type": type(error).__name__,
                "operation": context.operation,
                "flow_id": context.flow_id,
                "flow_type": context.flow_type,
                "phase": context.phase,
                "user_id": context.user_id,
                "additional_context": context.additional_context,
                "stack_trace": traceback.format_exc()
            }
        )
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """Classify error into category"""
        error_type = type(error)
        
        for category, error_types in self._category_classifiers.items():
            if error_type in error_types:
                return category
        
        # Check error message for patterns
        error_msg = str(error).lower()
        
        if any(keyword in error_msg for keyword in ["timeout", "timed out"]):
            return ErrorCategory.TIMEOUT
        elif any(keyword in error_msg for keyword in ["connection", "network"]):
            return ErrorCategory.NETWORK
        elif any(keyword in error_msg for keyword in ["permission", "access denied", "forbidden"]):
            return ErrorCategory.PERMISSION
        elif any(keyword in error_msg for keyword in ["database", "sql", "query"]):
            return ErrorCategory.DATABASE
        elif any(keyword in error_msg for keyword in ["validation", "invalid", "required"]):
            return ErrorCategory.VALIDATION
        
        return ErrorCategory.UNKNOWN
    
    async def _handle_validation_error(
        self,
        error: ValueError,
        context: ErrorContext,
        category: ErrorCategory
    ) -> ErrorResolution:
        """Handle validation errors"""
        return ErrorResolution(
            action="pause",
            should_retry=False,
            message=f"Validation failed: {str(error)}",
            user_action_required=True,
            severity=ErrorSeverity.MEDIUM,
            new_status="waiting_for_input"
        )
    
    async def _handle_timeout_error(
        self,
        error: Exception,
        context: ErrorContext,
        category: ErrorCategory
    ) -> ErrorResolution:
        """Handle timeout errors"""
        return ErrorResolution(
            action="retry",
            should_retry=True,
            message=f"Operation timed out: {str(error)}",
            user_action_required=False,
            severity=ErrorSeverity.MEDIUM,
            update_flow_status=False
        )
    
    async def _handle_network_error(
        self,
        error: Exception,
        context: ErrorContext,
        category: ErrorCategory
    ) -> ErrorResolution:
        """Handle network-related errors"""
        return ErrorResolution(
            action="retry",
            should_retry=True,
            message=f"Network error: {str(error)}",
            user_action_required=False,
            severity=ErrorSeverity.MEDIUM,
            update_flow_status=False
        )
    
    async def _handle_permission_error(
        self,
        error: PermissionError,
        context: ErrorContext,
        category: ErrorCategory
    ) -> ErrorResolution:
        """Handle permission errors"""
        return ErrorResolution(
            action="fail",
            should_retry=False,
            message=f"Permission denied: {str(error)}",
            user_action_required=True,
            severity=ErrorSeverity.HIGH,
            new_status="failed"
        )
    
    async def _handle_runtime_error(
        self,
        error: RuntimeError,
        context: ErrorContext,
        category: ErrorCategory
    ) -> ErrorResolution:
        """Handle runtime errors"""
        # Check if it's a specific runtime error we can handle
        error_msg = str(error).lower()
        
        if "crew" in error_msg or "agent" in error_msg:
            # CrewAI related runtime error
            return ErrorResolution(
                action="retry",
                should_retry=True,
                message=f"CrewAI runtime error: {str(error)}",
                severity=ErrorSeverity.MEDIUM
            )
        
        # Generic runtime error
        return ErrorResolution(
            action="fail",
            should_retry=False,
            message=f"Runtime error: {str(error)}",
            severity=ErrorSeverity.HIGH,
            new_status="failed"
        )
    
    async def _handle_generic_error(
        self,
        error: Exception,
        context: ErrorContext,
        category: ErrorCategory
    ) -> ErrorResolution:
        """Handle generic/unknown errors"""
        # Default to failing safely
        return ErrorResolution(
            action="fail",
            should_retry=False,
            message=f"Unexpected error: {type(error).__name__}: {str(error)}",
            severity=ErrorSeverity.HIGH,
            new_status="failed",
            metadata={
                "error_class": error.__class__.__module__ + "." + error.__class__.__name__
            }
        )
    
    def register_error_strategy(
        self,
        error_type: Type[Exception],
        strategy: Callable[[Exception, ErrorContext, ErrorCategory], Awaitable[ErrorResolution]]
    ):
        """
        Register a custom error handling strategy
        
        Args:
            error_type: Exception type to handle
            strategy: Async function that returns ErrorResolution
        """
        self._error_strategies[error_type] = strategy
        logger.info(f"✅ Registered error strategy for {error_type.__name__}")
    
    def add_category_classifier(
        self,
        category: ErrorCategory,
        error_types: List[Type[Exception]]
    ):
        """
        Add error types to a category classifier
        
        Args:
            category: Error category
            error_types: List of exception types for this category
        """
        if category not in self._category_classifiers:
            self._category_classifiers[category] = []
        
        self._category_classifiers[category].extend(error_types)
        logger.info(f"✅ Added {len(error_types)} error types to category {category.value}")
    
    async def _handle_crewai_error(
        self,
        error: CrewAIExecutionError,
        context: ErrorContext,
        category: ErrorCategory
    ) -> ErrorResolution:
        """Handle CrewAI execution errors"""
        # CrewAI errors often benefit from retry
        return ErrorResolution(
            action="retry",
            should_retry=True,
            message=f"AI agent execution failed: {str(error)}",
            user_action_required=False,
            severity=ErrorSeverity.MEDIUM,
            update_flow_status=False,
            metadata={
                "crew_name": getattr(error, 'crew_name', None),
                "phase": getattr(error, 'phase', None)
            }
        )
    
    async def _handle_network_timeout_error(
        self,
        error: NetworkTimeoutError,
        context: ErrorContext,
        category: ErrorCategory
    ) -> ErrorResolution:
        """Handle network timeout errors"""
        return ErrorResolution(
            action="retry",
            should_retry=True,
            message=error.user_message,
            user_action_required=False,
            severity=ErrorSeverity.MEDIUM,
            update_flow_status=False,
            metadata={
                "operation": error.operation,
                "timeout_seconds": error.timeout_seconds
            }
        )
    
    async def _handle_resource_error(
        self,
        error: ResourceExhaustedError,
        context: ErrorContext,
        category: ErrorCategory
    ) -> ErrorResolution:
        """Handle resource exhaustion errors"""
        return ErrorResolution(
            action="pause",
            should_retry=True,
            message=error.user_message,
            user_action_required=False,
            severity=ErrorSeverity.HIGH,
            new_status="paused",
            retry_delay=300.0,  # Wait 5 minutes before retry
            metadata={
                "resource_type": error.resource_type
            }
        )
    
    async def _handle_flow_not_found_error(
        self,
        error: FlowNotFoundError,
        context: ErrorContext,
        category: ErrorCategory
    ) -> ErrorResolution:
        """Handle flow not found errors"""
        return ErrorResolution(
            action="fail",
            should_retry=False,
            message=error.user_message,
            user_action_required=True,
            severity=ErrorSeverity.HIGH,
            new_status="failed",
            metadata={
                "requested_flow_id": error.flow_id
            }
        )
    
    async def _handle_invalid_state_error(
        self,
        error: InvalidFlowStateError,
        context: ErrorContext,
        category: ErrorCategory
    ) -> ErrorResolution:
        """Handle invalid flow state errors"""
        return ErrorResolution(
            action="pause",
            should_retry=False,
            message=error.user_message,
            user_action_required=True,
            severity=ErrorSeverity.MEDIUM,
            update_flow_status=False,
            metadata={
                "current_state": error.details.get("current_state"),
                "target_state": error.details.get("target_state")
            }
        )
    
    async def _handle_background_task_error(
        self,
        error: BackgroundTaskError,
        context: ErrorContext,
        category: ErrorCategory
    ) -> ErrorResolution:
        """Handle background task errors"""
        return ErrorResolution(
            action="retry",
            should_retry=True,
            message=error.user_message,
            user_action_required=False,
            severity=ErrorSeverity.MEDIUM,
            update_flow_status=True,
            new_status="retrying",
            metadata={
                "task_name": error.task_name,
                "task_id": error.task_id
            }
        )