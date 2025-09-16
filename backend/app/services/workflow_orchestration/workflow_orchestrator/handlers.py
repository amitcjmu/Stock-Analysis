"""
Workflow Event Handlers - Background tasks and event handling
Team C1 - Task C1.2

Contains workflow execution handlers, background task management,
retry logic, timeout handling, and learning optimizations.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict

from app.core.exceptions import FlowError
from app.core.logging import get_logger

from .base import WorkflowExecution, WorkflowStatus

logger = get_logger(__name__)


class WorkflowHandlers:
    """Handlers for workflow execution and background tasks"""

    def __init__(self, orchestrator):
        """Initialize with reference to main orchestrator"""
        self.orchestrator = orchestrator

    async def _execute_workflow(self, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Execute a workflow using the Collection Phase Engine"""
        workflow.start_time = datetime.utcnow()
        workflow.status = WorkflowStatus.RUNNING

        # Add to active workflows
        self.orchestrator.active_workflows[workflow.workflow_id] = workflow

        try:
            logger.info(f"🚀 Executing workflow: {workflow.workflow_id}")

            # Execute Collection Flow using Phase Engine
            execution_result = (
                await self.orchestrator.phase_engine.execute_collection_flow(
                    flow_id=workflow.flow_id,
                    automation_tier=workflow.configuration.automation_tier.value,
                    client_requirements=workflow.metadata.get("client_requirements"),
                    environment_config=workflow.metadata.get("environment_config"),
                )
            )

            # Update workflow with results
            workflow.end_time = datetime.utcnow()
            workflow.execution_time_ms = int(
                (workflow.end_time - workflow.start_time).total_seconds() * 1000
            )
            workflow.result = execution_result
            workflow.status = WorkflowStatus.COMPLETED

            # Apply learning optimizations
            await self._apply_learning_optimizations(workflow, execution_result)

            logger.info(
                f"✅ Workflow completed: {workflow.workflow_id} ({workflow.execution_time_ms}ms)"
            )

            # Move to history
            del self.orchestrator.active_workflows[workflow.workflow_id]
            self.orchestrator.execution_history.append(workflow)

            return {
                "workflow_id": workflow.workflow_id,
                "status": "completed",
                "execution_time_ms": workflow.execution_time_ms,
                "result": execution_result,
            }

        except Exception as e:
            # Handle workflow failure
            workflow.end_time = datetime.utcnow()
            workflow.execution_time_ms = int(
                (workflow.end_time - workflow.start_time).total_seconds() * 1000
            )
            workflow.error_message = str(e)
            workflow.status = WorkflowStatus.FAILED

            logger.error(f"❌ Workflow failed: {workflow.workflow_id} - {str(e)}")

            # Check if retry is needed
            if await self._should_retry_workflow(workflow):
                await self._schedule_retry(workflow)
            else:
                # Move to history
                del self.orchestrator.active_workflows[workflow.workflow_id]
                self.orchestrator.execution_history.append(workflow)

            raise FlowError(f"Workflow execution failed: {str(e)}")

    async def _continue_workflow_execution(
        self, workflow: WorkflowExecution
    ) -> Dict[str, Any]:
        """Continue execution of a resumed workflow"""
        try:
            # Get current flow status to determine continuation point
            flow_status = await self.orchestrator.master_orchestrator.get_flow_status(
                workflow.flow_id, include_details=True
            )

            # Determine where to continue based on flow state
            current_phase = flow_status.get("current_phase", "platform_detection")

            # Continue execution from current phase
            # This would integrate with the Phase Engine to resume from specific phase
            logger.info(f"🔄 Continuing workflow from phase: {current_phase}")

            # For now, return continuation status
            return {
                "workflow_id": workflow.workflow_id,
                "continuation_status": "resumed",
                "current_phase": current_phase,
                "flow_status": flow_status,
            }

        except Exception as e:
            logger.error(f"❌ Failed to continue workflow execution: {e}")
            raise

    async def _workflow_scheduler(self):
        """Background task to schedule queued workflows"""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                # Process queue if we have capacity
                if (
                    len(self.orchestrator.active_workflows)
                    < self.orchestrator.max_concurrent_workflows
                    and self.orchestrator.workflow_queue
                ):
                    # Sort queue by priority and scheduled time
                    self.orchestrator.workflow_queue.sort(
                        key=lambda w: (
                            w.configuration.priority.value,
                            w.scheduled_time or datetime.utcnow(),
                        )
                    )

                    # Execute next workflow
                    next_workflow = self.orchestrator.workflow_queue.pop(0)

                    # Check if dependencies are met
                    if await self._dependencies_met(next_workflow):
                        asyncio.create_task(self._execute_workflow(next_workflow))
                    else:
                        # Put back in queue
                        self.orchestrator.workflow_queue.append(next_workflow)

            except Exception as e:
                logger.error(f"❌ Scheduler error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _workflow_monitor(self):
        """Background task to monitor active workflows"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                current_time = datetime.utcnow()

                # Check for timed out workflows
                for workflow_id, workflow in list(
                    self.orchestrator.active_workflows.items()
                ):
                    if workflow.start_time:
                        elapsed_minutes = (
                            current_time - workflow.start_time
                        ).total_seconds() / 60
                        if elapsed_minutes > workflow.configuration.timeout_minutes:
                            logger.warning(f"⏰ Workflow timeout: {workflow_id}")
                            await self._handle_workflow_timeout(workflow)

            except Exception as e:
                logger.error(f"❌ Monitor error: {e}")
                await asyncio.sleep(60)

    async def _workflow_cleanup(self):
        """Background task to cleanup old workflow records"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour

                cutoff_time = datetime.utcnow() - timedelta(
                    hours=self.orchestrator.workflow_cleanup_hours
                )

                # Clean up old history
                self.orchestrator.execution_history = [
                    w
                    for w in self.orchestrator.execution_history
                    if w.end_time and w.end_time > cutoff_time
                ]

                logger.info(
                    f"🧹 Cleaned up old workflow records. History count: {len(self.orchestrator.execution_history)}"
                )

            except Exception as e:
                logger.error(f"❌ Cleanup error: {e}")
                await asyncio.sleep(3600)

    async def _dependencies_met(self, workflow: WorkflowExecution) -> bool:
        """Check if workflow dependencies are satisfied"""
        if not workflow.dependencies:
            return True

        # Check if dependent workflows are completed
        for dep_id in workflow.dependencies:
            dep_workflow = self.orchestrator.queries._find_workflow(dep_id)
            if not dep_workflow or dep_workflow.status != WorkflowStatus.COMPLETED:
                return False

        return True

    async def _should_retry_workflow(self, workflow: WorkflowExecution) -> bool:
        """Determine if workflow should be retried"""
        max_retries = workflow.configuration.retry_config.get("max_retries", 3)
        return workflow.retry_count < max_retries

    async def _schedule_retry(self, workflow: WorkflowExecution):
        """Schedule workflow retry with backoff"""
        workflow.retry_count += 1

        # Calculate retry delay
        base_delay = workflow.configuration.retry_config.get("base_delay_minutes", 5)
        backoff_multiplier = workflow.configuration.retry_config.get(
            "backoff_multiplier", 2
        )
        retry_delay = base_delay * (backoff_multiplier ** (workflow.retry_count - 1))

        # Update workflow for retry
        workflow.status = WorkflowStatus.SCHEDULED
        workflow.scheduled_time = datetime.utcnow() + timedelta(minutes=retry_delay)
        workflow.error_message = None
        workflow.start_time = None
        workflow.end_time = None

        # Add back to queue
        self.orchestrator.workflow_queue.append(workflow)

        # Remove from active
        if workflow.workflow_id in self.orchestrator.active_workflows:
            del self.orchestrator.active_workflows[workflow.workflow_id]

        logger.info(
            f"🔄 Scheduled retry {workflow.retry_count}: {workflow.workflow_id} (delay: {retry_delay}min)"
        )

    async def _handle_workflow_timeout(self, workflow: WorkflowExecution):
        """Handle workflow timeout"""
        try:
            # Cancel the workflow
            await self.orchestrator.commands.cancel_workflow(
                workflow.workflow_id,
                reason=f"Timeout after {workflow.configuration.timeout_minutes} minutes",
            )

        except Exception as e:
            logger.error(f"❌ Error handling timeout for {workflow.workflow_id}: {e}")

    async def _apply_learning_optimizations(
        self, workflow: WorkflowExecution, result: Dict[str, Any]
    ):
        """Apply machine learning optimizations based on execution results"""
        try:
            # Extract learning data
            learning_data = {
                "automation_tier": workflow.configuration.automation_tier.value,
                "execution_time_ms": workflow.execution_time_ms,
                "quality_scores": result.get("overall_quality_score", 0.0),
                "phase_results": result.get("phase_results", {}),
                "client_requirements": workflow.metadata.get("client_requirements", {}),
                "environment_config": workflow.metadata.get("environment_config", {}),
            }

            # Apply learning optimizations
            optimizations = (
                await self.orchestrator.learning_optimizer.optimize_workflow_execution(
                    learning_data=learning_data,
                    execution_context=workflow.configuration.__dict__,
                )
            )

            # Store optimizations for future workflows
            workflow.metadata["learning_optimizations"] = optimizations

            logger.info(f"🧠 Applied learning optimizations: {workflow.workflow_id}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to apply learning optimizations: {e}")
