"""
Tool Audit Logger

Wraps the existing FlowAuditLogger to provide audit logging specifically for tool operations.
Injected by the orchestrator and maps tool operation parameters to flow audit events.
"""

from typing import Any, Dict, Optional

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.services.flow_orchestration.audit_logger import (
    FlowAuditLogger,
    AuditLevel,
)

logger = get_logger(__name__)

# Text constants to avoid DB enum issues
AUDIT_CATEGORY_TOOL_OPERATION = "TOOL_OPERATION"


class ToolAuditLogger:
    """
    Audit logger specifically for tool operations that wraps FlowAuditLogger.

    This class is injected by the orchestrator (not created by tools) and provides
    a specialized interface for logging tool operations while maintaining consistency
    with the existing audit framework.
    """

    def __init__(self, flow_audit_logger: FlowAuditLogger, context: RequestContext):
        """
        Initialize ToolAuditLogger with existing FlowAuditLogger and context.

        Args:
            flow_audit_logger: The existing FlowAuditLogger instance to wrap
            context: RequestContext containing flow_id, client_account_id, etc.
        """
        self.flow_audit_logger = flow_audit_logger
        self.context = context
        logger.debug("✅ ToolAuditLogger initialized with context")

    async def log_tool_operation(
        self,
        tool_name: str,
        operation: str,
        agent_name: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        input_parameters: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        level: str = "INFO",
    ) -> str:
        """
        Log a tool operation using the underlying FlowAuditLogger.

        Args:
            tool_name: Name of the tool being executed
            operation: Specific operation being performed
            agent_name: Name of the agent executing the tool (optional, defaults to 'unknown')
            success: Whether the operation succeeded
            error_message: Error message if operation failed
            execution_time_ms: Execution time in milliseconds
            input_parameters: Input parameters passed to the tool
            output_data: Output data from the tool operation
            metadata: Additional metadata about the operation
            level: Audit level (INFO, WARNING, ERROR, etc.)

        Returns:
            Audit event ID
        """
        try:
            # Handle missing agent_name gracefully
            if not agent_name:
                agent_name = "unknown"

            # Map string level to AuditLevel enum for internal consistency
            audit_level = self._map_level(level)

            # Use text constant category consistently to avoid enum ALTER TYPE issues
            audit_category = (
                "TOOL_OPERATION"  # Consistent text category for all tool operations
            )

            # Build operation name that includes both tool and operation context
            if operation:
                operation_name = f"tool_{tool_name}_{operation}"
            else:
                operation_name = f"tool_{tool_name}"

            # Build detailed information for the audit event
            details = {
                "tool_name": tool_name,
                "agent_name": agent_name,
                "operation": operation,
                "execution_time_ms": execution_time_ms,
                "input_parameters": self._sanitize_parameters(input_parameters),
                "output_data": self._sanitize_output(output_data),
                "category": AUDIT_CATEGORY_TOOL_OPERATION,  # Use text constant
            }

            # Combine provided metadata with tool-specific data
            combined_metadata = {
                "tool_audit": True,
                "tool_name": tool_name,
                "agent_name": agent_name,
            }
            if metadata:
                combined_metadata.update(metadata)

            # Ensure flow_id is available
            flow_id = self.context.flow_id
            if not flow_id:
                # Log at WARNING with tenant IDs to aid triage
                logger.warning(
                    "⚠️ No flow_id in context for tool audit - using placeholder",
                    extra={
                        "client_account_id": self.context.client_account_id,
                        "engagement_id": self.context.engagement_id,
                        "tool_name": tool_name,
                        "operation": operation,
                    },
                )
                # Use tenant IDs in placeholder for better tracking
                flow_id = f"unknown_flow_{self.context.client_account_id}_{self.context.engagement_id}"

            # Call the actual FlowAuditLogger.log_audit_event() API
            event_id = await self.flow_audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=operation_name,
                category=audit_category,
                level=audit_level,
                context=self.context,
                success=success,
                error_message=error_message,
                details=details,
                metadata=combined_metadata,
            )

            logger.debug(
                f"📝 Tool operation logged: {tool_name}.{operation} -> {event_id}"
            )
            return event_id

        except Exception as e:
            logger.error(
                f"❌ Failed to log tool operation {tool_name}.{operation}: {e}"
            )
            return ""

    def _map_level(self, level: str) -> AuditLevel:
        """
        Map string level to AuditLevel enum.

        Args:
            level: String level (INFO, WARNING, ERROR, etc.)

        Returns:
            AuditLevel enum value
        """
        level_mapping = {
            "DEBUG": AuditLevel.DEBUG,
            "INFO": AuditLevel.INFO,
            "WARNING": AuditLevel.WARNING,
            "ERROR": AuditLevel.ERROR,
            "CRITICAL": AuditLevel.CRITICAL,
        }

        return level_mapping.get(level.upper(), AuditLevel.INFO)

    def _sanitize_parameters(
        self, parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sanitize input parameters to remove sensitive data.

        Args:
            parameters: Raw input parameters

        Returns:
            Sanitized parameters safe for logging
        """
        if not parameters:
            return {}

        sanitized = {}
        sensitive_keys = ["password", "secret", "token", "key", "credential", "api_key"]

        for key, value in parameters.items():
            key_lower = key.lower()
            if any(sensitive_key in key_lower for sensitive_key in sensitive_keys):
                sanitized[key] = "***FILTERED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_parameters(value)
            elif isinstance(value, (str, int, float, bool, list)):
                sanitized[key] = value
            else:
                # Convert complex objects to string representation
                sanitized[key] = str(value)

        return sanitized

    def _sanitize_output(self, output_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sanitize output data to remove sensitive information.

        Args:
            output_data: Raw output data

        Returns:
            Sanitized output data safe for logging
        """
        if not output_data:
            return {}

        # Apply similar sanitization as parameters
        return self._sanitize_parameters(output_data)

    def get_audit_context(self) -> Dict[str, Any]:
        """
        Get the current audit context information.

        Returns:
            Dictionary containing context information for audit purposes
        """
        return {
            "client_account_id": self.context.client_account_id,
            "engagement_id": self.context.engagement_id,
            "user_id": self.context.user_id,
            "flow_id": self.context.flow_id,
            "request_id": self.context.request_id,
            "ip_address": getattr(self.context, "ip_address", None),
            "user_agent": getattr(self.context, "user_agent", None),
        }

    def is_audit_enabled(self) -> bool:
        """
        Check if audit logging is enabled.

        Returns:
            True if audit logging is enabled
        """
        return self.flow_audit_logger is not None

    def __repr__(self) -> str:
        """String representation of ToolAuditLogger."""
        return (
            f"ToolAuditLogger(flow_id={self.context.flow_id}, "
            f"client_id={self.context.client_account_id})"
        )
