"""
Flow Status Manager

Handles status retrieval, flow information aggregation, and status calculation logic.
Simplified version without over-engineered detection and routing.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.agent_ui_bridge import AgentUIBridge
from app.services.flow_type_registry import FlowTypeRegistry

logger = get_logger(__name__)


class FlowStatusManager:
    """
    Manages flow status retrieval, aggregation, and calculation with comprehensive flow information.
    Simplified version without complex detection and routing.
    """

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
        flow_registry: FlowTypeRegistry,
    ):
        """
        Initialize the Flow Status Manager

        Args:
            db: Database session
            context: Request context
            master_repo: Repository for master flow operations
            flow_registry: Registry for flow type configurations
        """
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry

        logger.info(
            f"✅ Flow Status Manager initialized for client {context.client_account_id}"
        )

    async def get_flow_status(
        self, flow_id: str, include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive flow status

        Args:
            flow_id: Flow identifier
            include_details: Whether to include detailed information

        Returns:
            Flow status information

        Raises:
            ValueError: If flow not found
        """
        try:
            # Get flow
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")

            # Get flow configuration
            flow_config = self.flow_registry.get_flow_config(master_flow.flow_type)
            if not flow_config:
                logger.warning(
                    f"No configuration found for flow type: {master_flow.flow_type}"
                )

            # Build status response
            status = {
                "flow_id": flow_id,
                "flow_type": master_flow.flow_type,
                "flow_status": master_flow.flow_status,
                "created_at": master_flow.created_at.isoformat(),
                "updated_at": master_flow.updated_at.isoformat(),
                "user_id": master_flow.user_id,
                "flow_name": master_flow.flow_name,
                "flow_configuration": master_flow.flow_configuration or {},
            }

            # Add details if requested
            if include_details:
                # Get child flow status
                child_status = await self._get_child_flow_status(
                    flow_id, master_flow.flow_type
                )
                if child_status:
                    status["child_flow_status"] = child_status

                # Get agent insights
                agent_bridge = AgentUIBridge(self.db, self.context)
                insights = await agent_bridge.get_agent_insights(flow_id, limit=5)
                status["recent_insights"] = insights

                # Calculate progress
                progress = await self._calculate_flow_progress(
                    flow_id, master_flow.flow_type, child_status
                )
                status["progress"] = progress

            return status

        except Exception as e:
            logger.error(f"Failed to get flow status for {flow_id}: {e}")
            raise

    async def _get_child_flow_status(
        self, flow_id: str, flow_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get status from child flow table

        Args:
            flow_id: Flow identifier
            flow_type: Type of flow

        Returns:
            Child flow status or None
        """
        flow_config = self.flow_registry.get_flow_config(flow_type)
        if not flow_config or not flow_config.repository_class:
            return None

        try:
            # Get repository
            repo = flow_config.repository_class(self.db, self.context)

            # Get child flow
            child_flow = await repo.get_by_flow_id(flow_id)
            if not child_flow:
                return None

            # Build child status
            return {
                "status": getattr(child_flow, "status", None),
                "current_phase": getattr(child_flow, "current_phase", None),
                "progress_percentage": getattr(child_flow, "progress_percentage", 0.0),
                "metadata": getattr(child_flow, "metadata", {}),
            }

        except Exception as e:
            logger.warning(f"Failed to get child flow status: {e}")
            return None

    async def _calculate_flow_progress(
        self,
        flow_id: str,
        flow_type: str,
        child_status: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate flow progress

        Args:
            flow_id: Flow identifier
            flow_type: Type of flow
            child_status: Child flow status

        Returns:
            Progress information
        """
        progress = {
            "percentage": 0.0,
            "phase": "unknown",
            "phases_completed": [],
            "estimated_completion": None,
        }

        if child_status:
            progress["percentage"] = child_status.get("progress_percentage", 0.0)
            progress["phase"] = child_status.get("current_phase", "unknown")

            # Get phase information from flow config
            flow_config = self.flow_registry.get_flow_config(flow_type)
            if flow_config and hasattr(flow_config, "phases"):
                # total_phases = len(flow_config.phases)  # Not needed for now
                current_phase_index = next(
                    (
                        i
                        for i, p in enumerate(flow_config.phases)
                        if p == progress["phase"]
                    ),
                    0,
                )
                progress["phases_completed"] = flow_config.phases[:current_phase_index]

        return progress

    async def get_all_flows(
        self, status_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all flows for the current context

        Args:
            status_filter: Optional list of statuses to filter

        Returns:
            List of flow summaries
        """
        try:
            # Get all master flows
            filters = {}
            if status_filter:
                filters["flow_status__in"] = status_filter

            master_flows = await self.master_repo.get_all(**filters)

            # Build summaries
            summaries = []
            for flow in master_flows:
                summary = {
                    "flow_id": str(flow.flow_id),
                    "flow_type": flow.flow_type,
                    "flow_status": flow.flow_status,
                    "flow_name": flow.flow_name,
                    "created_at": flow.created_at.isoformat(),
                    "updated_at": flow.updated_at.isoformat(),
                }
                summaries.append(summary)

            return summaries

        except Exception as e:
            logger.error(f"Failed to get all flows: {e}")
            return []

    async def update_flow_status(
        self, flow_id: str, status: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update flow status

        Args:
            flow_id: Flow identifier
            status: New status
            metadata: Optional metadata

        Returns:
            Success flag
        """
        try:
            # Update master flow
            await self.master_repo.update_flow_status(
                flow_id=flow_id, status=status, metadata=metadata
            )

            return True

        except Exception as e:
            logger.error(f"Failed to update flow status for {flow_id}: {e}")
            return False
