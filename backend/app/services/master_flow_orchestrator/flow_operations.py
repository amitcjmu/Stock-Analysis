"""
Flow Operations Module

Main orchestrator that delegates to specialized operation modules using composition pattern.
Reduced from 690+ LOC to under 200 LOC through modularization.
"""

import uuid
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.flow_orchestration import (
    FlowAuditLogger,
    FlowErrorHandler,
    FlowExecutionEngine,
    FlowLifecycleManager,
)

from .enums import FlowOperationType
from .mock_monitor import MockFlowPerformanceMonitor
from .operations import (
    FlowCacheManager,
    FlowCreationOperations,
    FlowExecutionOperations,
    FlowLifecycleOperations,
)

logger = get_logger(__name__)


class FlowOperations:
    """
    Main flow operations orchestrator using composition pattern.
    
    Delegates to specialized operation modules for clean separation of concerns:
    - FlowCreationOperations: Complex flow creation with Redis cleanup
    - FlowExecutionOperations: Phase execution operations  
    - FlowLifecycleOperations: Pause, resume, and delete operations
    - FlowCacheManager: Comprehensive cache invalidation
    """

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
        flow_registry,
        handler_registry,
        validator_registry,
        lifecycle_manager: FlowLifecycleManager,
        execution_engine: FlowExecutionEngine,
        error_handler: FlowErrorHandler,
        performance_monitor: MockFlowPerformanceMonitor,
        audit_logger: FlowAuditLogger,
    ):
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        self.handler_registry = handler_registry
        self.validator_registry = validator_registry
        self.lifecycle_manager = lifecycle_manager
        self.execution_engine = execution_engine
        self.error_handler = error_handler
        self.performance_monitor = performance_monitor
        self.audit_logger = audit_logger
        
        # Initialize specialized operation modules
        self.cache_manager = FlowCacheManager(db, context)
        
        self.creation_ops = FlowCreationOperations(
            db, context, master_repo, flow_registry,
            performance_monitor, audit_logger, self.cache_manager
        )
        
        self.execution_ops = FlowExecutionOperations(
            db, context, master_repo, flow_registry,
            performance_monitor, audit_logger, execution_engine
        )
        
        self.lifecycle_ops = FlowLifecycleOperations(
            db, context, master_repo, flow_registry,
            performance_monitor, audit_logger, self.cache_manager
        )

    async def create_flow(
        self,
        flow_type: str,
        flow_name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        _retry_count: int = 0,
        atomic: bool = False,
    ) -> Tuple[str, Dict[str, Any]]:
        """Delegate flow creation to specialized creation operations module"""
        return await self.creation_ops.create_flow(
            flow_type, flow_name, configuration, initial_state
        )

    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Optional[Dict[str, Any]] = None,
        validation_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Delegate phase execution to specialized execution operations module"""
        return await self.execution_ops.execute_phase(
            flow_id, phase_name, phase_input, validation_overrides
        )

    async def pause_flow(
        self, flow_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delegate flow pausing to specialized lifecycle operations module"""
        return await self.lifecycle_ops.pause_flow(flow_id)

    async def resume_flow(
        self, flow_id: str, resume_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Delegate flow resuming to specialized lifecycle operations module"""
        return await self.lifecycle_ops.resume_flow(flow_id, resume_context)

    async def delete_flow(
        self, flow_id: str, soft_delete: bool = True, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delegate flow deletion to specialized lifecycle operations module"""
        return await self.lifecycle_ops.delete_flow(flow_id)

    async def get_flow_db_id(self, flow_id: str) -> Optional[uuid.UUID]:
        """Get the database ID for a given flow_id"""
        try:
            query = select(CrewAIFlowStateExtensions.id).where(
                CrewAIFlowStateExtensions.flow_id == flow_id
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"Failed to get database ID for flow_id {flow_id}: {e}")
            return None
