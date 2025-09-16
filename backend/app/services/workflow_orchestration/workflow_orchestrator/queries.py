"""
Workflow Query Operations - Read operations
Team C1 - Task C1.2

Contains all read operations for workflow management including:
- Workflow status retrieval
- Workflow listing and filtering
- Metrics and performance data
- Workflow discovery and search
"""

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

from .base import WorkflowExecution, WorkflowStatus

logger = get_logger(__name__)


class WorkflowQueries:
    """Queries for workflow read operations"""

    def __init__(self, orchestrator):
        """Initialize with reference to main orchestrator"""
        self.orchestrator = orchestrator

    async def get_workflow_status(
        self, workflow_id: str, include_details: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive workflow status"""
        try:
            workflow = self._find_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")

            # Get master flow status
            flow_status = None
            if workflow.flow_id:
                try:
                    flow_status = (
                        await self.orchestrator.master_orchestrator.get_flow_status(
                            workflow.flow_id, include_details=include_details
                        )
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to get flow status for {workflow.flow_id}: {e}"
                    )

            # Build comprehensive status
            status = {
                "workflow_id": workflow_id,
                "flow_id": workflow.flow_id,
                "status": workflow.status.value,
                "automation_tier": workflow.configuration.automation_tier.value,
                "priority": workflow.configuration.priority.value,
                "scheduled_time": (
                    workflow.scheduled_time.isoformat()
                    if workflow.scheduled_time
                    else None
                ),
                "start_time": (
                    workflow.start_time.isoformat() if workflow.start_time else None
                ),
                "end_time": (
                    workflow.end_time.isoformat() if workflow.end_time else None
                ),
                "execution_time_ms": workflow.execution_time_ms,
                "retry_count": workflow.retry_count,
                "error_message": workflow.error_message,
                "metadata": workflow.metadata,
            }

            if include_details:
                status.update(
                    {
                        "configuration": workflow.configuration.__dict__,
                        "dependencies": workflow.dependencies,
                        "flow_status": flow_status,
                        "result": workflow.result,
                    }
                )

            return status

        except Exception as e:
            logger.error(f"❌ Failed to get workflow status {workflow_id}: {e}")
            raise

    async def list_workflows(
        self,
        status_filter: Optional[str] = None,
        automation_tier_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List workflows with optional filtering"""
        try:
            # Combine all workflows
            all_workflows = []
            all_workflows.extend(self.orchestrator.workflow_queue)
            all_workflows.extend(self.orchestrator.active_workflows.values())
            all_workflows.extend(
                self.orchestrator.execution_history[-100:]
            )  # Last 100 from history

            # Apply filters
            filtered_workflows = all_workflows

            if status_filter:
                filtered_workflows = [
                    w for w in filtered_workflows if w.status.value == status_filter
                ]

            if automation_tier_filter:
                filtered_workflows = [
                    w
                    for w in filtered_workflows
                    if w.configuration.automation_tier.value == automation_tier_filter
                ]

            # Sort by creation time (newest first)
            filtered_workflows.sort(
                key=lambda w: w.metadata.get("creation_time", ""), reverse=True
            )

            # Limit results
            limited_workflows = filtered_workflows[:limit]

            # Build response
            workflow_list = []
            for workflow in limited_workflows:
                workflow_list.append(
                    {
                        "workflow_id": workflow.workflow_id,
                        "flow_id": workflow.flow_id,
                        "status": workflow.status.value,
                        "automation_tier": workflow.configuration.automation_tier.value,
                        "priority": workflow.configuration.priority.value,
                        "scheduled_time": (
                            workflow.scheduled_time.isoformat()
                            if workflow.scheduled_time
                            else None
                        ),
                        "start_time": (
                            workflow.start_time.isoformat()
                            if workflow.start_time
                            else None
                        ),
                        "end_time": (
                            workflow.end_time.isoformat() if workflow.end_time else None
                        ),
                        "execution_time_ms": workflow.execution_time_ms,
                        "retry_count": workflow.retry_count,
                        "created_by": workflow.configuration.metadata.get("created_by"),
                        "tenant": workflow.configuration.metadata.get("tenant"),
                    }
                )

            return workflow_list

        except Exception as e:
            logger.error(f"❌ Failed to list workflows: {e}")
            raise

    async def get_orchestrator_metrics(self) -> Dict[str, Any]:
        """Get orchestrator performance and health metrics"""
        try:
            # Calculate metrics
            total_workflows = (
                len(self.orchestrator.workflow_queue)
                + len(self.orchestrator.active_workflows)
                + len(self.orchestrator.execution_history)
            )

            status_counts = {}
            for status in WorkflowStatus:
                status_counts[status.value] = 0

            # Count current statuses
            for workflow in self.orchestrator.workflow_queue:
                status_counts[workflow.status.value] += 1
            for workflow in self.orchestrator.active_workflows.values():
                status_counts[workflow.status.value] += 1
            for workflow in self.orchestrator.execution_history[
                -100:
            ]:  # Recent history
                status_counts[workflow.status.value] += 1

            # Calculate success rate (last 100 workflows)
            recent_completed = len(
                [
                    w
                    for w in self.orchestrator.execution_history[-100:]
                    if w.status == WorkflowStatus.COMPLETED
                ]
            )
            recent_total = min(100, len(self.orchestrator.execution_history))
            success_rate = recent_completed / recent_total if recent_total > 0 else 0.0

            # Calculate average execution time
            completed_workflows = [
                w
                for w in self.orchestrator.execution_history[-100:]
                if w.status == WorkflowStatus.COMPLETED and w.execution_time_ms
            ]
            avg_execution_time = (
                sum(w.execution_time_ms for w in completed_workflows)
                / len(completed_workflows)
                if completed_workflows
                else 0
            )

            return {
                "orchestrator_status": "healthy",
                "total_workflows": total_workflows,
                "active_workflows": len(self.orchestrator.active_workflows),
                "queued_workflows": len(self.orchestrator.workflow_queue),
                "max_concurrent": self.orchestrator.max_concurrent_workflows,
                "status_distribution": status_counts,
                "success_rate": success_rate,
                "average_execution_time_ms": avg_execution_time,
                "background_services": {
                    "scheduler_running": self.orchestrator._scheduler_task
                    and not self.orchestrator._scheduler_task.done(),
                    "monitor_running": self.orchestrator._monitoring_task
                    and not self.orchestrator._monitoring_task.done(),
                    "cleanup_running": self.orchestrator._cleanup_task
                    and not self.orchestrator._cleanup_task.done(),
                },
                "tenant_info": {
                    "client_account_id": self.orchestrator.context.client_account_id,
                    "engagement_id": self.orchestrator.context.engagement_id,
                },
            }

        except Exception as e:
            logger.error(f"❌ Failed to get orchestrator metrics: {e}")
            raise

    def _find_workflow(self, workflow_id: str) -> Optional[WorkflowExecution]:
        """Find a workflow by ID in queue, active, or history"""
        # Check active workflows
        if workflow_id in self.orchestrator.active_workflows:
            return self.orchestrator.active_workflows[workflow_id]

        # Check queue
        for workflow in self.orchestrator.workflow_queue:
            if workflow.workflow_id == workflow_id:
                return workflow

        # Check history
        for workflow in self.orchestrator.execution_history:
            if workflow.workflow_id == workflow_id:
                return workflow

        return None
