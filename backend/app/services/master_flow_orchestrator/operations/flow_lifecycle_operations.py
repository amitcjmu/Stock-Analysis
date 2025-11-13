"""
Flow Lifecycle Operations - Facade for modular lifecycle management

This module provides a backward-compatible API that delegates to specialized modules.
All lifecycle operations are now split into focused components for better maintainability.
"""

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.flow_contracts import FlowAuditLogger

from .flow_cache_manager import FlowCacheManager
from .mock_monitor import MockFlowPerformanceMonitor
from .lifecycle_commands import FlowLifecycleCommands


class FlowLifecycleOperations:
    """
    Facade for flow lifecycle operations

    Delegates to specialized modules while maintaining backward compatibility.
    This keeps the public API stable while allowing internal modularization.
    """

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
        flow_registry,
        performance_monitor: MockFlowPerformanceMonitor,
        audit_logger: FlowAuditLogger,
        cache_manager: FlowCacheManager,
    ):
        """
        Initialize the lifecycle operations facade

        Args:
            db: Database session
            context: Request context with tenant information
            master_repo: Repository for master flow operations
            flow_registry: Registry of flow types and configurations
            performance_monitor: Performance tracking service
            audit_logger: Audit logging service
            cache_manager: Cache management service
        """
        # Initialize the commands module that handles all write operations
        self._commands = FlowLifecycleCommands(
            db=db,
            context=context,
            master_repo=master_repo,
            flow_registry=flow_registry,
            performance_monitor=performance_monitor,
            audit_logger=audit_logger,
            cache_manager=cache_manager,
        )

    async def pause_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Pause a running flow with state preservation

        Args:
            flow_id: Flow identifier

        Returns:
            Pause operation result
        """
        return await self._commands.pause_flow(flow_id)

    async def resume_flow(
        self, flow_id: str, resume_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resume a paused flow from its last saved state

        Args:
            flow_id: Flow identifier
            resume_context: Additional context for resume operation

        Returns:
            Resume operation result
        """
        return await self._commands.resume_flow(flow_id, resume_context)

    async def delete_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Soft delete a flow with comprehensive cleanup

        Args:
            flow_id: Flow identifier

        Returns:
            Delete operation result
        """
        return await self._commands.delete_flow(flow_id)
