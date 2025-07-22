"""
Automated Collection Workflow Orchestrator
Team C1 - Task C1.2

Main orchestrator service that coordinates all Collection Flow workflows, manages flow lifecycle,
and provides unified orchestration for the complete ADCS (Adaptive Data Collection System).

Integrates with Master Flow Orchestrator patterns and provides automated workflow management
for Collection Flows with intelligent routing, scheduling, and execution coordination.
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import FlowError, InvalidFlowStateError
from app.core.logging import get_logger
from app.services.ai_analysis import BusinessContextAnalyzer, GapAnalysisAgent, LearningOptimizer

# Import Phase 1 & 2 components
from app.services.collection_flow import CollectionFlowStateService, TierDetectionService

# Import flow registry components
from app.services.flow_type_registry import flow_type_registry
from app.services.handler_registry import handler_registry

# Import Master Flow Orchestrator for integration
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.services.validator_registry import validator_registry

# Import Collection Phase Engine
from .collection_phase_engine import AutomationTier, CollectionPhaseExecutionEngine

logger = get_logger(__name__)


class WorkflowStatus(Enum):
    """Status of workflow execution"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowPriority(Enum):
    """Priority levels for workflow execution"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WorkflowConfiguration:
    """Configuration for workflow execution"""
    automation_tier: AutomationTier
    priority: WorkflowPriority
    timeout_minutes: int
    quality_thresholds: Dict[str, float]
    retry_config: Dict[str, Any]
    scheduling_config: Dict[str, Any]
    notification_config: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class WorkflowExecution:
    """Tracking information for workflow execution"""
    workflow_id: str
    flow_id: str
    flow_type: str
    status: WorkflowStatus
    configuration: WorkflowConfiguration
    scheduled_time: Optional[datetime]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    execution_time_ms: Optional[int]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    retry_count: int
    dependencies: List[str]
    metadata: Dict[str, Any]


class WorkflowOrchestrator:
    """
    Automated Collection Workflow Orchestrator
    
    Provides unified orchestration for Collection Flow workflows with:
    - Automated workflow scheduling and execution
    - Integration with Master Flow Orchestrator
    - Dependency management and sequencing
    - Intelligent retry and error handling
    - Performance optimization and load balancing
    - Multi-tenant workflow isolation
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize the Workflow Orchestrator"""
        self.db = db
        self.context = context
        
        # Initialize Master Flow Orchestrator for integration
        self.master_orchestrator = MasterFlowOrchestrator(db, context)
        
        # Initialize Collection Phase Engine
        self.phase_engine = CollectionPhaseExecutionEngine(db, context)
        
        # Initialize core services
        self.state_service = CollectionFlowStateService(db, context)
        self.tier_detection = TierDetectionService(db, context)
        self.business_analyzer = BusinessContextAnalyzer()
        self.gap_analysis_agent = GapAnalysisAgent()
        self.learning_optimizer = LearningOptimizer()
        
        # Initialize registries
        self.flow_registry = flow_type_registry
        self.validator_registry = validator_registry
        self.handler_registry = handler_registry
        
        # Workflow execution tracking
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.workflow_queue: List[WorkflowExecution] = []
        self.execution_history: List[WorkflowExecution] = []
        
        # Configuration
        self.max_concurrent_workflows = 5
        self.default_timeout_minutes = 120
        self.workflow_cleanup_hours = 24
        
        # Background task management
        self._scheduler_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("✅ Workflow Orchestrator initialized")
    
    async def start_orchestrator(self):
        """Start the orchestrator background services"""
        try:
            # Start scheduler for queued workflows
            self._scheduler_task = asyncio.create_task(self._workflow_scheduler())
            
            # Start monitoring for active workflows
            self._monitoring_task = asyncio.create_task(self._workflow_monitor())
            
            # Start cleanup task for completed workflows
            self._cleanup_task = asyncio.create_task(self._workflow_cleanup())
            
            logger.info("🚀 Workflow Orchestrator services started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start orchestrator services: {e}")
            raise
    
    async def stop_orchestrator(self):
        """Stop the orchestrator background services"""
        try:
            # Cancel background tasks
            for task in [self._scheduler_task, self._monitoring_task, self._cleanup_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            logger.info("🛑 Workflow Orchestrator services stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping orchestrator services: {e}")
    
    async def create_collection_workflow(
        self,
        automation_tier: str = "tier_2",
        priority: str = "normal",
        client_requirements: Optional[Dict[str, Any]] = None,
        environment_config: Optional[Dict[str, Any]] = None,
        scheduling_config: Optional[Dict[str, Any]] = None,
        execute_immediately: bool = True
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
            flow_id, flow_data = await self.master_orchestrator.create_flow(
                flow_type="collection",
                flow_name=f"Collection Flow - {automation_tier}",
                configuration={
                    "automation_tier": automation_tier,
                    "client_requirements": client_requirements or {},
                    "environment_config": environment_config or {},
                    "workflow_id": workflow_id
                },
                initial_state={
                    "workflow_status": WorkflowStatus.PENDING.value,
                    "automation_tier": automation_tier,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            # Create workflow configuration
            config = WorkflowConfiguration(
                automation_tier=AutomationTier(automation_tier),
                priority=WorkflowPriority(priority),
                timeout_minutes=scheduling_config.get("timeout_minutes", self.default_timeout_minutes) if scheduling_config else self.default_timeout_minutes,
                quality_thresholds=self._get_quality_thresholds(automation_tier),
                retry_config=self._get_retry_config(automation_tier),
                scheduling_config=scheduling_config or {},
                notification_config=client_requirements.get("notifications", {}) if client_requirements else {},
                metadata={
                    "created_by": self.context.user_id,
                    "tenant": self.context.client_account_id,
                    "engagement": self.context.engagement_id
                }
            )
            
            # Create workflow execution record
            workflow_execution = WorkflowExecution(
                workflow_id=workflow_id,
                flow_id=str(flow_id),
                flow_type="collection",
                status=WorkflowStatus.PENDING,
                configuration=config,
                scheduled_time=self._calculate_scheduled_time(scheduling_config),
                start_time=None,
                end_time=None,
                execution_time_ms=None,
                result=None,
                error_message=None,
                retry_count=0,
                dependencies=scheduling_config.get("dependencies", []) if scheduling_config else [],
                metadata={
                    "client_requirements": client_requirements,
                    "environment_config": environment_config,
                    "creation_time": datetime.utcnow().isoformat()
                }
            )
            
            # Add to queue or execute immediately
            if execute_immediately and self._can_execute_immediately():
                await self._execute_workflow(workflow_execution)
            else:
                self.workflow_queue.append(workflow_execution)
                workflow_execution.status = WorkflowStatus.SCHEDULED
                logger.info(f"📋 Workflow queued: {workflow_id} (position: {len(self.workflow_queue)})")
            
            logger.info(f"✅ Collection workflow created: {workflow_id} -> {flow_id}")
            return workflow_id, str(flow_id)
            
        except Exception as e:
            logger.error(f"❌ Failed to create collection workflow: {e}")
            raise FlowError(f"Failed to create collection workflow: {str(e)}")
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a specific workflow by ID"""
        try:
            # Find workflow
            workflow = self._find_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            # Check if already running
            if workflow.status == WorkflowStatus.RUNNING:
                raise InvalidFlowStateError(f"Workflow already running: {workflow_id}")
            
            # Execute workflow
            return await self._execute_workflow(workflow)
            
        except Exception as e:
            logger.error(f"❌ Failed to execute workflow {workflow_id}: {e}")
            raise
    
    async def pause_workflow(self, workflow_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Pause a running workflow"""
        try:
            workflow = self._find_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            if workflow.status != WorkflowStatus.RUNNING:
                raise InvalidFlowStateError(f"Cannot pause workflow in status: {workflow.status.value}")
            
            # Pause the master flow
            pause_result = await self.master_orchestrator.pause_flow(workflow.flow_id, reason)
            
            # Update workflow status
            workflow.status = WorkflowStatus.PAUSED
            workflow.metadata["pause_reason"] = reason
            workflow.metadata["paused_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"⏸️ Workflow paused: {workflow_id}")
            return {
                "workflow_id": workflow_id,
                "status": "paused",
                "reason": reason,
                "master_flow_result": pause_result
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to pause workflow {workflow_id}: {e}")
            raise
    
    async def resume_workflow(self, workflow_id: str, resume_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resume a paused workflow"""
        try:
            workflow = self._find_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            if workflow.status != WorkflowStatus.PAUSED:
                raise InvalidFlowStateError(f"Cannot resume workflow in status: {workflow.status.value}")
            
            # Resume the master flow
            resume_result = await self.master_orchestrator.resume_flow(workflow.flow_id, resume_context)
            
            # Update workflow status
            workflow.status = WorkflowStatus.RUNNING
            workflow.metadata["resumed_at"] = datetime.utcnow().isoformat()
            if resume_context:
                workflow.metadata["resume_context"] = resume_context
            
            # Continue workflow execution
            execution_result = await self._continue_workflow_execution(workflow)
            
            logger.info(f"▶️ Workflow resumed: {workflow_id}")
            return {
                "workflow_id": workflow_id,
                "status": "resumed",
                "master_flow_result": resume_result,
                "execution_result": execution_result
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to resume workflow {workflow_id}: {e}")
            raise
    
    async def cancel_workflow(self, workflow_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Cancel a workflow"""
        try:
            workflow = self._find_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            # Remove from queue if scheduled
            if workflow.status == WorkflowStatus.SCHEDULED:
                self.workflow_queue = [w for w in self.workflow_queue if w.workflow_id != workflow_id]
            
            # Delete master flow if created
            if workflow.flow_id:
                await self.master_orchestrator.delete_flow(
                    workflow.flow_id,
                    soft_delete=True,
                    reason=reason or "Workflow cancelled"
                )
            
            # Update workflow status
            workflow.status = WorkflowStatus.CANCELLED
            workflow.end_time = datetime.utcnow()
            workflow.metadata["cancel_reason"] = reason
            workflow.metadata["cancelled_at"] = datetime.utcnow().isoformat()
            
            # Move to history
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            self.execution_history.append(workflow)
            
            logger.info(f"❌ Workflow cancelled: {workflow_id}")
            return {
                "workflow_id": workflow_id,
                "status": "cancelled",
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel workflow {workflow_id}: {e}")
            raise
    
    async def get_workflow_status(self, workflow_id: str, include_details: bool = True) -> Dict[str, Any]:
        """Get comprehensive workflow status"""
        try:
            workflow = self._find_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            # Get master flow status
            flow_status = None
            if workflow.flow_id:
                try:
                    flow_status = await self.master_orchestrator.get_flow_status(
                        workflow.flow_id,
                        include_details=include_details
                    )
                except Exception as e:
                    logger.warning(f"Failed to get flow status for {workflow.flow_id}: {e}")
            
            # Build comprehensive status
            status = {
                "workflow_id": workflow_id,
                "flow_id": workflow.flow_id,
                "status": workflow.status.value,
                "automation_tier": workflow.configuration.automation_tier.value,
                "priority": workflow.configuration.priority.value,
                "scheduled_time": workflow.scheduled_time.isoformat() if workflow.scheduled_time else None,
                "start_time": workflow.start_time.isoformat() if workflow.start_time else None,
                "end_time": workflow.end_time.isoformat() if workflow.end_time else None,
                "execution_time_ms": workflow.execution_time_ms,
                "retry_count": workflow.retry_count,
                "error_message": workflow.error_message,
                "metadata": workflow.metadata
            }
            
            if include_details:
                status.update({
                    "configuration": workflow.configuration.__dict__,
                    "dependencies": workflow.dependencies,
                    "flow_status": flow_status,
                    "result": workflow.result
                })
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Failed to get workflow status {workflow_id}: {e}")
            raise
    
    async def list_workflows(
        self,
        status_filter: Optional[str] = None,
        automation_tier_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List workflows with optional filtering"""
        try:
            # Combine all workflows
            all_workflows = []
            all_workflows.extend(self.workflow_queue)
            all_workflows.extend(self.active_workflows.values())
            all_workflows.extend(self.execution_history[-100:])  # Last 100 from history
            
            # Apply filters
            filtered_workflows = all_workflows
            
            if status_filter:
                filtered_workflows = [w for w in filtered_workflows 
                                    if w.status.value == status_filter]
            
            if automation_tier_filter:
                filtered_workflows = [w for w in filtered_workflows 
                                    if w.configuration.automation_tier.value == automation_tier_filter]
            
            # Sort by creation time (newest first)
            filtered_workflows.sort(
                key=lambda w: w.metadata.get("creation_time", ""),
                reverse=True
            )
            
            # Limit results
            limited_workflows = filtered_workflows[:limit]
            
            # Build response
            workflow_list = []
            for workflow in limited_workflows:
                workflow_list.append({
                    "workflow_id": workflow.workflow_id,
                    "flow_id": workflow.flow_id,
                    "status": workflow.status.value,
                    "automation_tier": workflow.configuration.automation_tier.value,
                    "priority": workflow.configuration.priority.value,
                    "scheduled_time": workflow.scheduled_time.isoformat() if workflow.scheduled_time else None,
                    "start_time": workflow.start_time.isoformat() if workflow.start_time else None,
                    "end_time": workflow.end_time.isoformat() if workflow.end_time else None,
                    "execution_time_ms": workflow.execution_time_ms,
                    "retry_count": workflow.retry_count,
                    "created_by": workflow.configuration.metadata.get("created_by"),
                    "tenant": workflow.configuration.metadata.get("tenant")
                })
            
            return workflow_list
            
        except Exception as e:
            logger.error(f"❌ Failed to list workflows: {e}")
            raise
    
    async def get_orchestrator_metrics(self) -> Dict[str, Any]:
        """Get orchestrator performance and health metrics"""
        try:
            # Calculate metrics
            total_workflows = len(self.workflow_queue) + len(self.active_workflows) + len(self.execution_history)
            
            status_counts = {}
            for status in WorkflowStatus:
                status_counts[status.value] = 0
            
            # Count current statuses
            for workflow in self.workflow_queue:
                status_counts[workflow.status.value] += 1
            for workflow in self.active_workflows.values():
                status_counts[workflow.status.value] += 1
            for workflow in self.execution_history[-100:]:  # Recent history
                status_counts[workflow.status.value] += 1
            
            # Calculate success rate (last 100 workflows)
            recent_completed = len([w for w in self.execution_history[-100:] 
                                 if w.status == WorkflowStatus.COMPLETED])
            recent_total = min(100, len(self.execution_history))
            success_rate = recent_completed / recent_total if recent_total > 0 else 0.0
            
            # Calculate average execution time
            completed_workflows = [w for w in self.execution_history[-100:] 
                                 if w.status == WorkflowStatus.COMPLETED and w.execution_time_ms]
            avg_execution_time = (
                sum(w.execution_time_ms for w in completed_workflows) / len(completed_workflows)
                if completed_workflows else 0
            )
            
            return {
                "orchestrator_status": "healthy",
                "total_workflows": total_workflows,
                "active_workflows": len(self.active_workflows),
                "queued_workflows": len(self.workflow_queue),
                "max_concurrent": self.max_concurrent_workflows,
                "status_distribution": status_counts,
                "success_rate": success_rate,
                "average_execution_time_ms": avg_execution_time,
                "background_services": {
                    "scheduler_running": self._scheduler_task and not self._scheduler_task.done(),
                    "monitor_running": self._monitoring_task and not self._monitoring_task.done(),
                    "cleanup_running": self._cleanup_task and not self._cleanup_task.done()
                },
                "tenant_info": {
                    "client_account_id": self.context.client_account_id,
                    "engagement_id": self.context.engagement_id
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get orchestrator metrics: {e}")
            raise
    
    # Private methods
    
    async def _execute_workflow(self, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Execute a workflow using the Collection Phase Engine"""
        workflow.start_time = datetime.utcnow()
        workflow.status = WorkflowStatus.RUNNING
        
        # Add to active workflows
        self.active_workflows[workflow.workflow_id] = workflow
        
        try:
            logger.info(f"🚀 Executing workflow: {workflow.workflow_id}")
            
            # Execute Collection Flow using Phase Engine
            execution_result = await self.phase_engine.execute_collection_flow(
                flow_id=workflow.flow_id,
                automation_tier=workflow.configuration.automation_tier.value,
                client_requirements=workflow.metadata.get("client_requirements"),
                environment_config=workflow.metadata.get("environment_config")
            )
            
            # Update workflow with results
            workflow.end_time = datetime.utcnow()
            workflow.execution_time_ms = int((workflow.end_time - workflow.start_time).total_seconds() * 1000)
            workflow.result = execution_result
            workflow.status = WorkflowStatus.COMPLETED
            
            # Apply learning optimizations
            await self._apply_learning_optimizations(workflow, execution_result)
            
            logger.info(f"✅ Workflow completed: {workflow.workflow_id} ({workflow.execution_time_ms}ms)")
            
            # Move to history
            del self.active_workflows[workflow.workflow_id]
            self.execution_history.append(workflow)
            
            return {
                "workflow_id": workflow.workflow_id,
                "status": "completed",
                "execution_time_ms": workflow.execution_time_ms,
                "result": execution_result
            }
            
        except Exception as e:
            # Handle workflow failure
            workflow.end_time = datetime.utcnow()
            workflow.execution_time_ms = int((workflow.end_time - workflow.start_time).total_seconds() * 1000)
            workflow.error_message = str(e)
            workflow.status = WorkflowStatus.FAILED
            
            logger.error(f"❌ Workflow failed: {workflow.workflow_id} - {str(e)}")
            
            # Check if retry is needed
            if await self._should_retry_workflow(workflow):
                await self._schedule_retry(workflow)
            else:
                # Move to history
                del self.active_workflows[workflow.workflow_id]
                self.execution_history.append(workflow)
            
            raise FlowError(f"Workflow execution failed: {str(e)}")
    
    async def _continue_workflow_execution(self, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Continue execution of a resumed workflow"""
        try:
            # Get current flow status to determine continuation point
            flow_status = await self.master_orchestrator.get_flow_status(workflow.flow_id, include_details=True)
            
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
                "flow_status": flow_status
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
                if len(self.active_workflows) < self.max_concurrent_workflows and self.workflow_queue:
                    # Sort queue by priority and scheduled time
                    self.workflow_queue.sort(
                        key=lambda w: (
                            w.configuration.priority.value,
                            w.scheduled_time or datetime.utcnow()
                        )
                    )
                    
                    # Execute next workflow
                    next_workflow = self.workflow_queue.pop(0)
                    
                    # Check if dependencies are met
                    if await self._dependencies_met(next_workflow):
                        asyncio.create_task(self._execute_workflow(next_workflow))
                    else:
                        # Put back in queue
                        self.workflow_queue.append(next_workflow)
                
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
                for workflow_id, workflow in list(self.active_workflows.items()):
                    if workflow.start_time:
                        elapsed_minutes = (current_time - workflow.start_time).total_seconds() / 60
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
                
                cutoff_time = datetime.utcnow() - timedelta(hours=self.workflow_cleanup_hours)
                
                # Clean up old history
                self.execution_history = [
                    w for w in self.execution_history
                    if w.end_time and w.end_time > cutoff_time
                ]
                
                logger.info(f"🧹 Cleaned up old workflow records. History count: {len(self.execution_history)}")
                
            except Exception as e:
                logger.error(f"❌ Cleanup error: {e}")
                await asyncio.sleep(3600)
    
    def _find_workflow(self, workflow_id: str) -> Optional[WorkflowExecution]:
        """Find a workflow by ID in queue, active, or history"""
        # Check active workflows
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        
        # Check queue
        for workflow in self.workflow_queue:
            if workflow.workflow_id == workflow_id:
                return workflow
        
        # Check history
        for workflow in self.execution_history:
            if workflow.workflow_id == workflow_id:
                return workflow
        
        return None
    
    def _can_execute_immediately(self) -> bool:
        """Check if workflow can be executed immediately"""
        return len(self.active_workflows) < self.max_concurrent_workflows
    
    def _calculate_scheduled_time(self, scheduling_config: Optional[Dict[str, Any]]) -> Optional[datetime]:
        """Calculate when workflow should be scheduled"""
        if not scheduling_config:
            return None
        
        if scheduling_config.get("execute_immediately", True):
            return None
        
        # Handle scheduled execution
        delay_minutes = scheduling_config.get("delay_minutes", 0)
        return datetime.utcnow() + timedelta(minutes=delay_minutes)
    
    async def _dependencies_met(self, workflow: WorkflowExecution) -> bool:
        """Check if workflow dependencies are satisfied"""
        if not workflow.dependencies:
            return True
        
        # Check if dependent workflows are completed
        for dep_id in workflow.dependencies:
            dep_workflow = self._find_workflow(dep_id)
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
        backoff_multiplier = workflow.configuration.retry_config.get("backoff_multiplier", 2)
        retry_delay = base_delay * (backoff_multiplier ** (workflow.retry_count - 1))
        
        # Update workflow for retry
        workflow.status = WorkflowStatus.SCHEDULED
        workflow.scheduled_time = datetime.utcnow() + timedelta(minutes=retry_delay)
        workflow.error_message = None
        workflow.start_time = None
        workflow.end_time = None
        
        # Add back to queue
        self.workflow_queue.append(workflow)
        
        # Remove from active
        if workflow.workflow_id in self.active_workflows:
            del self.active_workflows[workflow.workflow_id]
        
        logger.info(f"🔄 Scheduled retry {workflow.retry_count}: {workflow.workflow_id} (delay: {retry_delay}min)")
    
    async def _handle_workflow_timeout(self, workflow: WorkflowExecution):
        """Handle workflow timeout"""
        try:
            # Cancel the workflow
            await self.cancel_workflow(
                workflow.workflow_id,
                reason=f"Timeout after {workflow.configuration.timeout_minutes} minutes"
            )
            
        except Exception as e:
            logger.error(f"❌ Error handling timeout for {workflow.workflow_id}: {e}")
    
    async def _apply_learning_optimizations(self, workflow: WorkflowExecution, result: Dict[str, Any]):
        """Apply machine learning optimizations based on execution results"""
        try:
            # Extract learning data
            learning_data = {
                "automation_tier": workflow.configuration.automation_tier.value,
                "execution_time_ms": workflow.execution_time_ms,
                "quality_scores": result.get("overall_quality_score", 0.0),
                "phase_results": result.get("phase_results", {}),
                "client_requirements": workflow.metadata.get("client_requirements", {}),
                "environment_config": workflow.metadata.get("environment_config", {})
            }
            
            # Apply learning optimizations
            optimizations = await self.learning_optimizer.optimize_workflow_execution(
                learning_data=learning_data,
                execution_context=workflow.configuration.__dict__
            )
            
            # Store optimizations for future workflows
            workflow.metadata["learning_optimizations"] = optimizations
            
            logger.info(f"🧠 Applied learning optimizations: {workflow.workflow_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to apply learning optimizations: {e}")
    
    def _get_quality_thresholds(self, automation_tier: str) -> Dict[str, float]:
        """Get quality thresholds based on automation tier"""
        thresholds = {
            "tier_1": {"overall": 0.95, "platform_detection": 0.95, "collection": 0.95, "synthesis": 0.95},
            "tier_2": {"overall": 0.85, "platform_detection": 0.85, "collection": 0.85, "synthesis": 0.85},
            "tier_3": {"overall": 0.75, "platform_detection": 0.75, "collection": 0.75, "synthesis": 0.75},
            "tier_4": {"overall": 0.60, "platform_detection": 0.60, "collection": 0.60, "synthesis": 0.60}
        }
        return thresholds.get(automation_tier, thresholds["tier_2"])
    
    def _get_retry_config(self, automation_tier: str) -> Dict[str, Any]:
        """Get retry configuration based on automation tier"""
        return {
            "max_retries": 3,
            "base_delay_minutes": 5,
            "backoff_multiplier": 2,
            "max_delay_minutes": 30
        }