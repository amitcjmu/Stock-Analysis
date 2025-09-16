"""
Modular Workflow Orchestrator Package
Team C1 - Task C1.2

Modularized workflow orchestrator with focused responsibilities.
Maintains 100% backward compatibility with the original unified file.

This module preserves all public API exports while organizing code into
focused modules for better maintainability and testing.
"""

from .base import (
    WorkflowConfiguration,
    WorkflowExecution,
    WorkflowPriority,
    WorkflowStatus,
)
from .commands import WorkflowCommands
from .handlers import WorkflowHandlers
from .orchestrator import WorkflowOrchestrator as BaseWorkflowOrchestrator
from .queries import WorkflowQueries
from .utils import WorkflowUtils


class WorkflowOrchestrator(BaseWorkflowOrchestrator):
    """
    Enhanced Workflow Orchestrator with modular components

    Extends the base orchestrator to include all command, query, handler,
    and utility functionality while maintaining the same public API.
    """

    def __init__(self, db, context):
        """Initialize the modular workflow orchestrator"""
        super().__init__(db, context)

        # Initialize modular components
        self.commands = WorkflowCommands(self)
        self.queries = WorkflowQueries(self)
        self.handlers = WorkflowHandlers(self)
        self.utils = WorkflowUtils(self)

    # Expose command methods directly for backward compatibility
    async def create_collection_workflow(self, *args, **kwargs):
        """Create a new Collection Flow workflow"""
        return await self.commands.create_collection_workflow(*args, **kwargs)

    async def execute_workflow(self, *args, **kwargs):
        """Execute a specific workflow by ID"""
        return await self.commands.execute_workflow(*args, **kwargs)

    async def pause_workflow(self, *args, **kwargs):
        """Pause a running workflow"""
        return await self.commands.pause_workflow(*args, **kwargs)

    async def resume_workflow(self, *args, **kwargs):
        """Resume a paused workflow"""
        return await self.commands.resume_workflow(*args, **kwargs)

    async def cancel_workflow(self, *args, **kwargs):
        """Cancel a workflow"""
        return await self.commands.cancel_workflow(*args, **kwargs)

    # Expose query methods directly for backward compatibility
    async def get_workflow_status(self, *args, **kwargs):
        """Get comprehensive workflow status"""
        return await self.queries.get_workflow_status(*args, **kwargs)

    async def list_workflows(self, *args, **kwargs):
        """List workflows with optional filtering"""
        return await self.queries.list_workflows(*args, **kwargs)

    async def get_orchestrator_metrics(self, *args, **kwargs):
        """Get orchestrator performance and health metrics"""
        return await self.queries.get_orchestrator_metrics(*args, **kwargs)

    # Expose utility methods directly for backward compatibility
    def _find_workflow(self, *args, **kwargs):
        """Find a workflow by ID in queue, active, or history"""
        return self.queries._find_workflow(*args, **kwargs)

    def _can_execute_immediately(self, *args, **kwargs):
        """Check if workflow can be executed immediately"""
        return self.utils._can_execute_immediately(*args, **kwargs)

    def _calculate_scheduled_time(self, *args, **kwargs):
        """Calculate when workflow should be scheduled"""
        return self.utils._calculate_scheduled_time(*args, **kwargs)

    def _get_quality_thresholds(self, *args, **kwargs):
        """Get quality thresholds based on automation tier"""
        return self.utils._get_quality_thresholds(*args, **kwargs)

    def _get_retry_config(self, *args, **kwargs):
        """Get retry configuration based on automation tier"""
        return self.utils._get_retry_config(*args, **kwargs)

    # Expose handler methods directly for backward compatibility
    async def _execute_workflow(self, *args, **kwargs):
        """Execute a workflow using the Collection Phase Engine"""
        return await self.handlers._execute_workflow(*args, **kwargs)

    async def _continue_workflow_execution(self, *args, **kwargs):
        """Continue execution of a resumed workflow"""
        return await self.handlers._continue_workflow_execution(*args, **kwargs)

    async def _workflow_scheduler(self, *args, **kwargs):
        """Background task to schedule queued workflows"""
        return await self.handlers._workflow_scheduler(*args, **kwargs)

    async def _workflow_monitor(self, *args, **kwargs):
        """Background task to monitor active workflows"""
        return await self.handlers._workflow_monitor(*args, **kwargs)

    async def _workflow_cleanup(self, *args, **kwargs):
        """Background task to cleanup old workflow records"""
        return await self.handlers._workflow_cleanup(*args, **kwargs)

    async def _dependencies_met(self, *args, **kwargs):
        """Check if workflow dependencies are satisfied"""
        return await self.handlers._dependencies_met(*args, **kwargs)

    async def _should_retry_workflow(self, *args, **kwargs):
        """Determine if workflow should be retried"""
        return await self.handlers._should_retry_workflow(*args, **kwargs)

    async def _schedule_retry(self, *args, **kwargs):
        """Schedule workflow retry with backoff"""
        return await self.handlers._schedule_retry(*args, **kwargs)

    async def _handle_workflow_timeout(self, *args, **kwargs):
        """Handle workflow timeout"""
        return await self.handlers._handle_workflow_timeout(*args, **kwargs)

    async def _apply_learning_optimizations(self, *args, **kwargs):
        """Apply machine learning optimizations based on execution results"""
        return await self.handlers._apply_learning_optimizations(*args, **kwargs)


# Export all public classes and types for backward compatibility
__all__ = [
    "WorkflowOrchestrator",
    "WorkflowStatus",
    "WorkflowPriority",
    "WorkflowConfiguration",
    "WorkflowExecution",
    # Export modular components for advanced usage
    "WorkflowCommands",
    "WorkflowQueries",
    "WorkflowHandlers",
    "WorkflowUtils",
]
