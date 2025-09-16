"""
Main WorkflowOrchestrator class - Core orchestration logic
Team C1 - Task C1.2

Contains the main WorkflowOrchestrator class with initialization,
background service management, and core workflow coordination.
"""

import asyncio
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.services.ai_analysis import (
    BusinessContextAnalyzer,
    GapAnalysisAgent,
    LearningOptimizer,
)
from app.services.collection_flow import (
    CollectionFlowStateService,
    TierDetectionService,
)
from app.services.flow_type_registry import flow_type_registry
from app.services.handler_registry import handler_registry
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.services.validator_registry import validator_registry

from ..collection_phase_engine import CollectionPhaseExecutionEngine
from .base import WorkflowExecution

logger = get_logger(__name__)


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
        # Pass required context parameters to GapAnalysisAgent
        self.gap_analysis_agent = GapAnalysisAgent(
            client_account_id=context.client_account_id or "",
            engagement_id=context.engagement_id or "",
        )
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
            for task in [
                self._scheduler_task,
                self._monitoring_task,
                self._cleanup_task,
            ]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            logger.info("🛑 Workflow Orchestrator services stopped")

        except Exception as e:
            logger.error(f"❌ Error stopping orchestrator services: {e}")
