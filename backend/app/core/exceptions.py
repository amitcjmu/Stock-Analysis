"""
Core exception classes for the AI Stock Assess Platform.

Provides a comprehensive hierarchy of exceptions with:
- Specific error codes for tracking
- User-friendly messages
- Recovery suggestions
- Context preservation
"""

import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class BaseApplicationError(Exception):
    """Base exception class for application-specific errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None,
        trace_id: Optional[str] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.user_message = user_message or message  # User-friendly message
        self.recovery_suggestions = recovery_suggestions or []
        self.trace_id = trace_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        self.stack_trace = traceback.format_exc()
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error_code": self.error_code,
            "message": self.user_message,  # Use user-friendly message
            "details": self.details,
            "recovery_suggestions": self.recovery_suggestions,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat(),
        }


class ValidationError(BaseApplicationError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs,
    ):
        if field:
            user_message = f"Invalid value for {field}: {message}"
            recovery = [f"Please check the value provided for {field}"]
        else:
            user_message = f"Validation failed: {message}"
            recovery = ["Please check your input values"]

        super().__init__(
            message,
            error_code="VAL_001",
            user_message=user_message,
            recovery_suggestions=recovery,
            **kwargs,
        )
        self.field = field
        self.value = value
        if field:
            self.details["field"] = field
        if value is not None:
            self.details["provided_value"] = str(value)


class ConfigurationError(BaseApplicationError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        user_message = "System configuration error. Please contact support."
        recovery = ["Contact your system administrator", "Check configuration settings"]

        super().__init__(
            message,
            error_code="CFG_001",
            user_message=user_message,
            recovery_suggestions=recovery,
            **kwargs,
        )
        self.config_key = config_key
        if config_key:
            self.details["config_key"] = config_key


class DatabaseError(BaseApplicationError):
    """Raised when database operations fail."""

    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        user_message = "A database error occurred. Please try again later."
        recovery = [
            "Please try your request again in a few moments",
            "If the problem persists, contact support",
        ]

        super().__init__(
            message,
            error_code="DB_001",
            user_message=user_message,
            recovery_suggestions=recovery,
            **kwargs,
        )
        self.operation = operation
        if operation:
            self.details["operation"] = operation


class AuthenticationError(BaseApplicationError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        user_message = "Authentication failed. Please log in again."
        recovery = [
            "Please check your credentials",
            "Try logging in again",
            "If you forgot your password, use the reset option",
        ]

        super().__init__(
            message,
            error_code="AUTH_001",
            user_message=user_message,
            recovery_suggestions=recovery,
            **kwargs,
        )


class AuthorizationError(BaseApplicationError):
    """Raised when authorization fails."""

    def __init__(
        self, message: str = "Access denied", resource: Optional[str] = None, **kwargs
    ):
        if resource:
            user_message = f"You don't have permission to access {resource}"
        else:
            user_message = "You don't have permission to perform this action"

        recovery = [
            "Contact your administrator for access",
            "Check if you're logged into the correct account",
        ]

        super().__init__(
            message,
            error_code="AUTH_002",
            user_message=user_message,
            recovery_suggestions=recovery,
            **kwargs,
        )
        self.resource = resource
        if resource:
            self.details["resource"] = resource


class DataProcessingError(BaseApplicationError):
    """Raised when data processing operations fail."""

    def __init__(self, message: str, stage: Optional[str] = None, **kwargs):
        if stage:
            user_message = f"Data processing failed at {stage} stage"
        else:
            user_message = "Failed to process your data"

        recovery = [
            "Check your data format and try again",
            "Ensure all required fields are present",
            "Try processing smaller batches of data",
        ]

        super().__init__(
            message,
            error_code="PROC_001",
            user_message=user_message,
            recovery_suggestions=recovery,
            **kwargs,
        )
        self.stage = stage
        if stage:
            self.details["stage"] = stage


class AgentError(BaseApplicationError):
    """Raised when AI agent operations fail."""

    def __init__(self, message: str, agent_name: Optional[str] = None, **kwargs):
        if agent_name:
            user_message = f"AI agent '{agent_name}' encountered an error"
        else:
            user_message = "AI processing encountered an error"

        recovery = [
            "The AI agent will retry automatically",
            "If the issue persists, we'll notify our team",
            "You can try restarting the process",
        ]

        super().__init__(
            message,
            error_code="AI_001",
            user_message=user_message,
            recovery_suggestions=recovery,
            **kwargs,
        )
        self.agent_name = agent_name
        if agent_name:
            self.details["agent_name"] = agent_name


class FlowError(BaseApplicationError):
    """Raised when CrewAI flow operations fail."""

    def __init__(
        self,
        message: str,
        flow_name: Optional[str] = None,
        flow_id: Optional[str] = None,
        **kwargs,
    ):
        if flow_name:
            user_message = f"The {flow_name} workflow encountered an issue"
        else:
            user_message = "The workflow encountered an issue"

        recovery = [
            "The workflow will attempt to recover automatically",
            "Check the flow status for more details",
            "You can restart the workflow if needed",
        ]

        super().__init__(
            message,
            error_code="FLOW_001",
            user_message=user_message,
            recovery_suggestions=recovery,
            **kwargs,
        )
        self.flow_name = flow_name
        self.flow_id = flow_id
        if flow_name:
            self.details["flow_name"] = flow_name
        if flow_id:
            self.details["flow_id"] = flow_id


class DependencyError(BaseApplicationError):
    """Raised when dependency analysis fails."""

    def __init__(self, message: str, dependency_type: Optional[str] = None, **kwargs):
        if dependency_type:
            user_message = f"Failed to analyze {dependency_type} dependencies"
        else:
            user_message = "Failed to analyze dependencies"

        recovery = [
            "Ensure all source files are accessible",
            "Check for circular dependencies",
            "Try analyzing a subset of components",
        ]

        super().__init__(
            message,
            error_code="DEP_001",
            user_message=user_message,
            recovery_suggestions=recovery,
            **kwargs,
        )
        self.dependency_type = dependency_type
        if dependency_type:
            self.details["dependency_type"] = dependency_type


class MigrationError(BaseApplicationError):
    """Raised when migration operations fail."""

    def __init__(self, message: str, migration_stage: Optional[str] = None, **kwargs):
        if migration_stage:
            user_message = f"Migration failed during {migration_stage} stage"
        else:
            user_message = "Migration process encountered an error"

        recovery = [
            "Review the migration plan",
            "Check source and target environments",
            "Consider rolling back if necessary",
        ]

        super().__init__(
            message,
            error_code="MIG_001",
            user_message=user_message,
            recovery_suggestions=recovery,
            **kwargs,
        )
        self.migration_stage = migration_stage
        if migration_stage:
            self.details["migration_stage"] = migration_stage


# New specific exception classes


class FlowNotFoundError(FlowError):
    """Raised when a flow cannot be found"""

    def __init__(self, flow_id: str, **kwargs):
        super().__init__(f"Flow {flow_id} not found", flow_id=flow_id, **kwargs)
        self.error_code = "FLOW_002"
        self.user_message = "The requested workflow could not be found"
        self.recovery_suggestions = [
            "Check if the workflow ID is correct",
            "The workflow may have been deleted or completed",
        ]


class InvalidFlowStateError(FlowError):
    """Raised when flow state transition is invalid"""

    def __init__(
        self,
        current_state: str,
        target_state: str,
        flow_id: Optional[str] = None,
        **kwargs,
    ):
        message = f"Cannot transition from {current_state} to {target_state}"
        super().__init__(message, flow_id=flow_id, **kwargs)
        self.error_code = "FLOW_003"
        self.user_message = "Invalid workflow state transition"
        self.recovery_suggestions = [
            "Wait for the current operation to complete",
            "Check the workflow status before retrying",
        ]
        self.details.update(
            {"current_state": current_state, "target_state": target_state}
        )


class TenantIsolationError(AuthorizationError):
    """Raised when tenant isolation is violated"""

    def __init__(
        self,
        client_id: Optional[int] = None,
        engagement_id: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(
            "Tenant isolation violation detected",
            resource="cross-tenant data",
            **kwargs,
        )
        self.error_code = "SEC_001"
        self.user_message = "Access denied to requested resource"
        self.recovery_suggestions = [
            "Ensure you're accessing data from your organization only",
            "Contact support if you believe this is an error",
        ]
        # Don't expose client/engagement IDs in user-facing errors
        self.details["violation_type"] = "tenant_isolation"


class CrewAIExecutionError(AgentError):
    """Raised when CrewAI execution fails"""

    def __init__(
        self,
        message: str,
        crew_name: Optional[str] = None,
        phase: Optional[str] = None,
        **kwargs,
    ):
        agent_name = crew_name or "CrewAI"
        super().__init__(message, agent_name=agent_name, **kwargs)
        self.error_code = "INT_001"
        self.crew_name = crew_name
        self.phase = phase
        if phase:
            self.user_message = f"AI processing failed during {phase} phase"
            self.details["phase"] = phase


class NetworkTimeoutError(BaseApplicationError):
    """Raised when network operations timeout"""

    def __init__(
        self, operation: str, timeout_seconds: Optional[float] = None, **kwargs
    ):
        message = f"Network operation '{operation}' timed out"
        if timeout_seconds:
            message += f" after {timeout_seconds} seconds"

        super().__init__(
            message,
            error_code="NET_001",
            user_message="The operation took too long to complete",
            recovery_suggestions=[
                "Check your network connection",
                "Try again with a smaller data set",
                "The system will retry automatically",
            ],
            **kwargs,
        )
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        self.details.update(
            {"operation": operation, "timeout_seconds": timeout_seconds}
        )


class ResourceExhaustedError(BaseApplicationError):
    """Raised when system resources are exhausted"""

    def __init__(self, resource_type: str, **kwargs):
        super().__init__(
            f"{resource_type} resources exhausted",
            error_code="RES_001",
            user_message="System resources temporarily unavailable",
            recovery_suggestions=[
                "Try again in a few minutes",
                "Consider processing data in smaller batches",
                "Contact support if the issue persists",
            ],
            **kwargs,
        )
        self.resource_type = resource_type
        self.details["resource_type"] = resource_type


class DataImportError(DataProcessingError):
    """Raised when data import fails"""

    def __init__(
        self,
        message: str,
        file_name: Optional[str] = None,
        row_number: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, stage="import", **kwargs)
        self.error_code = "IMP_001"
        self.file_name = file_name
        self.row_number = row_number

        if file_name:
            self.user_message = f"Failed to import data from {file_name}"
            self.details["file_name"] = file_name
        if row_number:
            self.user_message += f" at row {row_number}"
            self.details["row_number"] = row_number


class BackgroundTaskError(BaseApplicationError):
    """Raised when background tasks fail"""

    def __init__(self, task_name: str, task_id: Optional[str] = None, **kwargs):
        super().__init__(
            f"Background task '{task_name}' failed",
            error_code="TASK_001",
            user_message="A background process encountered an error",
            recovery_suggestions=[
                "The task will be retried automatically",
                "Check the task status for updates",
                "You can manually restart the task if needed",
            ],
            **kwargs,
        )
        self.task_name = task_name
        self.task_id = task_id
        self.details.update({"task_name": task_name, "task_id": task_id})


class FlowStateUpdateError(FlowError):
    """Raised when flow state update operations fail"""

    def __init__(self, message: str, flow_id: Optional[str] = None, **kwargs):
        super().__init__(message, flow_id=flow_id, **kwargs)
        self.error_code = "FLOW_004"
        self.user_message = "Failed to update workflow status"
        self.recovery_suggestions = [
            "The system will retry the operation",
            "Try refreshing the page to see current status",
            "Contact support if the issue persists",
        ]
