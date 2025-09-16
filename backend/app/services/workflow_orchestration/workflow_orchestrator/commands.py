"""
Workflow Command Operations - Write/Mutation operations
Team C1 - Task C1.2

Contains all write operations for workflow management including:
- Workflow creation and modification
- Flow lifecycle operations (pause, resume, cancel)
- Retry scheduling and error handling
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from app.core.exceptions import FlowError, InvalidFlowStateError
from app.core.logging import get_logger

from .base import (
    WorkflowExecution,
    WorkflowStatus,
)

logger = get_logger(__name__)


class WorkflowCommands:
    """Commands for workflow write operations"""

    def __init__(self, orchestrator):
        """Initialize with reference to main orchestrator"""
        self.orchestrator = orchestrator

    async def create_collection_workflow(
        self,
        automation_tier: str = "tier_2",
        priority: str = "normal",
        client_requirements: Optional[Dict[str, Any]] = None,
        environment_config: Optional[Dict[str, Any]] = None,
        scheduling_config: Optional[Dict[str, Any]] = None,
        execute_immediately: bool = True,
    ) -> Tuple[str, str]:
        """
        Create a new Collection Flow workflow

        Args:
            automation_tier: Level of automation (tier_1 to tier_4)
            priority: Workflow priority (low, normal, high, critical)
            client_requirements: Client-specific requirements
            environment_config: Environment configuration
            scheduling_config: Scheduling preferences
            execute_immediately: Whether to execute immediately or queue

        Returns:
            Tuple of (workflow_id, flow_id)
        """
        try:
            # Generate unique identifiers
            workflow_id = f"workflow-{uuid.uuid4()}"

            # Create master flow record using Master Flow Orchestrator
            flow_id, flow_data = (
                await self.orchestrator.master_orchestrator.create_flow(
                    flow_type="collection",
                    flow_name=f"Collection Flow - {automation_tier}",
                    configuration={
                        "automation_tier": automation_tier,
                        "client_requirements": client_requirements or {},
                        "environment_config": environment_config or {},
                        "workflow_id": workflow_id,
                    },
                    initial_state={
                        "workflow_status": WorkflowStatus.PENDING.value,
                        "automation_tier": automation_tier,
                        "created_at": datetime.utcnow().isoformat(),
                    },
                )
            )

            # Create workflow configuration using utility method
            config = self.orchestrator.utils._create_workflow_configuration(
                automation_tier, priority, scheduling_config, client_requirements
            )

            # Create workflow execution record
            workflow_execution = WorkflowExecution(
                workflow_id=workflow_id,
                flow_id=str(flow_id),
                flow_type="collection",
                status=WorkflowStatus.PENDING,
                configuration=config,
                scheduled_time=self.orchestrator.utils._calculate_scheduled_time(
                    scheduling_config
                ),
                start_time=None,
                end_time=None,
                execution_time_ms=None,
                result=None,
                error_message=None,
                retry_count=0,
                dependencies=(
                    scheduling_config.get("dependencies", [])
                    if scheduling_config
                    else []
                ),
                metadata={
                    "client_requirements": client_requirements,
                    "environment_config": environment_config,
                    "creation_time": datetime.utcnow().isoformat(),
                },
            )

            # Add to queue or execute immediately
            if (
                execute_immediately
                and self.orchestrator.utils._can_execute_immediately()
            ):
                await self.orchestrator.handlers._execute_workflow(workflow_execution)
            else:
                self.orchestrator.workflow_queue.append(workflow_execution)
                workflow_execution.status = WorkflowStatus.SCHEDULED
                logger.info(
                    f"📋 Workflow queued: {workflow_id} (position: {len(self.orchestrator.workflow_queue)})"
                )

            logger.info(f"✅ Collection workflow created: {workflow_id} -> {flow_id}")
            return workflow_id, str(flow_id)

        except Exception as e:
            logger.error(f"❌ Failed to create collection workflow: {e}")
            raise FlowError(f"Failed to create collection workflow: {str(e)}")

    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a specific workflow by ID"""
        try:
            # Find workflow
            workflow = self.orchestrator.queries._find_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")

            # Check if already running
            if workflow.status == WorkflowStatus.RUNNING:
                raise InvalidFlowStateError(f"Workflow already running: {workflow_id}")

            # Execute workflow
            return await self.orchestrator.handlers._execute_workflow(workflow)

        except Exception as e:
            logger.error(f"❌ Failed to execute workflow {workflow_id}: {e}")
            raise

    async def pause_workflow(
        self, workflow_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Pause a running workflow"""
        try:
            workflow = self.orchestrator.queries._find_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")

            if workflow.status != WorkflowStatus.RUNNING:
                raise InvalidFlowStateError(
                    f"Cannot pause workflow in status: {workflow.status.value}"
                )

            # Pause the master flow
            pause_result = await self.orchestrator.master_orchestrator.pause_flow(
                workflow.flow_id, reason
            )

            # Update workflow status
            workflow.status = WorkflowStatus.PAUSED
            workflow.metadata["pause_reason"] = reason
            workflow.metadata["paused_at"] = datetime.utcnow().isoformat()

            logger.info(f"⏸️ Workflow paused: {workflow_id}")
            return {
                "workflow_id": workflow_id,
                "status": "paused",
                "reason": reason,
                "master_flow_result": pause_result,
            }

        except Exception as e:
            logger.error(f"❌ Failed to pause workflow {workflow_id}: {e}")
            raise

    async def resume_workflow(
        self, workflow_id: str, resume_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Resume a paused workflow"""
        try:
            workflow = self.orchestrator.queries._find_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")

            if workflow.status != WorkflowStatus.PAUSED:
                raise InvalidFlowStateError(
                    f"Cannot resume workflow in status: {workflow.status.value}"
                )

            # Resume the master flow
            resume_result = await self.orchestrator.master_orchestrator.resume_flow(
                workflow.flow_id, resume_context
            )

            # Update workflow status
            workflow.status = WorkflowStatus.RUNNING
            workflow.metadata["resumed_at"] = datetime.utcnow().isoformat()
            if resume_context:
                workflow.metadata["resume_context"] = resume_context

            # Continue workflow execution
            execution_result = (
                await self.orchestrator.handlers._continue_workflow_execution(workflow)
            )

            logger.info(f"▶️ Workflow resumed: {workflow_id}")
            return {
                "workflow_id": workflow_id,
                "status": "resumed",
                "master_flow_result": resume_result,
                "execution_result": execution_result,
            }

        except Exception as e:
            logger.error(f"❌ Failed to resume workflow {workflow_id}: {e}")
            raise

    async def cancel_workflow(
        self, workflow_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel a workflow"""
        try:
            workflow = self.orchestrator.queries._find_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")

            # Remove from queue if scheduled
            if workflow.status == WorkflowStatus.SCHEDULED:
                self.orchestrator.workflow_queue = [
                    w
                    for w in self.orchestrator.workflow_queue
                    if w.workflow_id != workflow_id
                ]

            # Delete master flow if created
            if workflow.flow_id:
                await self.orchestrator.master_orchestrator.delete_flow(
                    workflow.flow_id,
                    soft_delete=True,
                    reason=reason or "Workflow cancelled",
                )

            # Update workflow status
            workflow.status = WorkflowStatus.CANCELLED
            workflow.end_time = datetime.utcnow()
            workflow.metadata["cancel_reason"] = reason
            workflow.metadata["cancelled_at"] = datetime.utcnow().isoformat()

            # Move to history
            if workflow_id in self.orchestrator.active_workflows:
                del self.orchestrator.active_workflows[workflow_id]
            self.orchestrator.execution_history.append(workflow)

            logger.info(f"❌ Workflow cancelled: {workflow_id}")
            return {"workflow_id": workflow_id, "status": "cancelled", "reason": reason}

        except Exception as e:
            logger.error(f"❌ Failed to cancel workflow {workflow_id}: {e}")
            raise
