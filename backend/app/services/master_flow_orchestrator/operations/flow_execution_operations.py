"""
Flow Execution Operations

Handles phase execution operations with clean separation from lifecycle management.
Focused responsibility for execution engine integration.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.flow_orchestration import FlowAuditLogger
from app.services.flow_orchestration.audit_logger import AuditCategory, AuditLevel

from .enums import FlowOperationType
from .mock_monitor import MockFlowPerformanceMonitor

logger = logging.getLogger(__name__)


class FlowExecutionOperations:
    """Handles flow phase execution operations"""

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
        flow_registry,
        performance_monitor: MockFlowPerformanceMonitor,
        audit_logger: FlowAuditLogger,
        execution_engine,
    ):
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        self.performance_monitor = performance_monitor
        self.audit_logger = audit_logger
        self.execution_engine = execution_engine

    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Optional[Dict[str, Any]] = None,
        validation_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a specific phase of a flow

        Args:
            flow_id: Flow identifier
            phase_name: Name of the phase to execute
            phase_input: Input data for the phase
            validation_overrides: Validation overrides for forced execution

        Returns:
            Execution result dictionary
        """
        tracking_id = None

        try:
            # Start performance monitoring
            tracking_id = self.performance_monitor.start_operation(
                flow_id=flow_id,
                operation_type="execute_phase",
                metadata={"phase_name": phase_name},
            )

            logger.info(f"🎯 Executing phase '{phase_name}' for flow {flow_id}")

            # Get flow from database
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")

            # Validate phase execution
            await self._validate_phase_execution(
                master_flow, phase_name, validation_overrides
            )

            # Execute phase through execution engine
            result = await self.execution_engine.execute_phase(
                flow_id=flow_id,
                phase_name=phase_name,
                phase_input=phase_input or {},
                validation_overrides=validation_overrides,
            )

            # Update flow state based on execution result
            await self._update_flow_after_execution(master_flow, phase_name, result)

            # Log successful execution
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.EXECUTE_PHASE.value,
                category=AuditCategory.FLOW_EXECUTION,
                level=AuditLevel.INFO,
                context=self.context,
                success=True,
                details={
                    "phase_name": phase_name,
                    "execution_time": result.get("execution_time_ms", 0),
                },
            )

            self.performance_monitor.end_operation(tracking_id, success=True)
            logger.info(
                f"✅ Phase '{phase_name}' executed successfully for flow {flow_id}"
            )

            return result

        except Exception as e:
            logger.error(
                f"❌ Phase execution failed: {flow_id} - {phase_name} - {str(e)}"
            )

            # Log execution failure
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.EXECUTE_PHASE.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e),
                details={"phase_name": phase_name},
            )

            if tracking_id:
                self.performance_monitor.end_operation(tracking_id, success=False)

            raise RuntimeError(f"Failed to execute phase '{phase_name}': {str(e)}")

    async def _validate_phase_execution(
        self,
        master_flow,
        phase_name: str,
        validation_overrides: Optional[Dict[str, Any]],
    ) -> None:
        """Validate that the phase can be executed"""
        # Check if flow is in valid state for execution
        if master_flow.flow_status in ["completed", "cancelled"]:
            if not validation_overrides or not validation_overrides.get(
                "force_execution"
            ):
                raise ValueError(
                    f"Cannot execute phase on {master_flow.flow_status} flow"
                )

        # Check if phase is valid for the flow type
        flow_config = self.flow_registry.get_flow_config(master_flow.flow_type)
        if not flow_config.is_phase_valid(phase_name):
            raise ValueError(
                f"Invalid phase '{phase_name}' for flow type '{master_flow.flow_type}'"
            )

        # Check phase dependencies
        if not flow_config.are_dependencies_satisfied(phase_name, master_flow):
            if not validation_overrides or not validation_overrides.get(
                "force_execution"
            ):
                raise ValueError(f"Phase '{phase_name}' dependencies not satisfied")

        logger.info(
            f"✅ Phase validation passed for '{phase_name}' on flow {master_flow.flow_id}"
        )

    async def _update_flow_after_execution(
        self, master_flow, phase_name: str, execution_result: Dict[str, Any]
    ) -> None:
        """Update flow state after successful phase execution"""
        try:
            # Update phase completion status
            if "phase_completion" not in master_flow.flow_persistence_data:
                master_flow.flow_persistence_data["phase_completion"] = {}

            master_flow.flow_persistence_data["phase_completion"][phase_name] = {
                "completed": True,
                "completed_at": execution_result.get("completed_at"),
                "execution_time_ms": execution_result.get("execution_time_ms", 0),
                "result_summary": execution_result.get("summary", ""),
            }

            # Update current phase if execution result indicates progression
            if execution_result.get("next_phase"):
                master_flow.current_phase = execution_result["next_phase"]

            # Update progress percentage
            if execution_result.get("progress_percentage") is not None:
                master_flow.progress_percentage = execution_result[
                    "progress_percentage"
                ]

            # Update status if execution result indicates status change
            if execution_result.get("flow_status"):
                master_flow.flow_status = execution_result["flow_status"]

            # Persist changes
            await self.db.commit()

            logger.info(f"✅ Flow state updated after phase '{phase_name}' execution")

        except Exception as e:
            logger.error(f"❌ Failed to update flow state after execution: {e}")
            # Re-raise to ensure execution failure is properly handled
            raise
