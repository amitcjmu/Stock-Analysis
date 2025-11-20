"""
Collection Flow repository with context-aware multi-tenant data access.
Provides collection flow-specific query methods with automatic client account scoping.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
    CollectionPhase,
    AutomationTier,
)
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)


class CollectionFlowRepository(ContextAwareRepository[CollectionFlow]):
    """
    Collection flow repository with context-aware operations and flow-specific methods.
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        """Initialize collection flow repository with context."""
        super().__init__(db, CollectionFlow, client_account_id, engagement_id)

    async def get_by_flow_id(self, flow_id: str) -> Optional[CollectionFlow]:
        """Get collection flow by flow_id with context filtering.

        CRITICAL: get_by_filters() returns List, but this method must return single object.
        Per architectural pattern from collection-flow-id-resolver-fix memory.
        """
        flows = await self.get_by_filters(flow_id=flow_id)
        return flows[0] if flows else None

    async def get_by_master_flow_id(
        self, master_flow_id: uuid.UUID
    ) -> Optional[CollectionFlow]:
        """Get collection flow by master flow ID with context filtering.

        CRITICAL: get_by_filters() returns List, but this method must return single object.
        Per architectural pattern from collection-flow-id-resolver-fix memory.
        """
        flows = await self.get_by_filters(master_flow_id=master_flow_id)
        return flows[0] if flows else None

    async def get_by_status(self, status: CollectionFlowStatus) -> List[CollectionFlow]:
        """Get collection flows by status with context filtering."""
        return await self.get_by_filters(status=status)

    async def get_active_flows(self) -> List[CollectionFlow]:
        """Get all active (non-completed/failed/cancelled) flows."""
        # Use the base class method to get all flows, then filter by status
        all_flows = await self.get_by_filters()
        active_statuses = [
            CollectionFlowStatus.INITIALIZED,
            CollectionFlowStatus.RUNNING,
            CollectionFlowStatus.PAUSED,
        ]
        return [flow for flow in all_flows if flow.status in active_statuses]

    async def create(
        self,
        flow_name: str,
        automation_tier: str,
        flow_metadata: Optional[Dict[str, Any]] = None,
        collection_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> CollectionFlow:
        """
        Create a new collection flow (data persistence only).

        DEPRECATED: Use CollectionFlowLifecycleService.create_flow_with_orchestration()
        for new code. This method is retained for backward compatibility with tests.

        This method ONLY handles data persistence. For full flow creation with
        MFO integration, use the lifecycle service.

        Args:
            flow_name: Name of the collection flow
            automation_tier: Automation tier (tier_1, tier_2, tier_3, tier_4)
            flow_metadata: Optional flow metadata
            collection_config: Optional collection configuration
            **kwargs: Additional parameters (flow_id, master_flow_id, etc.)

        Returns:
            Created CollectionFlow instance
        """
        # Generate flow_id if not provided
        flow_id = kwargs.get("flow_id") or str(uuid.uuid4())

        # Prepare flow data (DATA PERSISTENCE ONLY - no orchestration)
        flow_data = {
            "flow_id": flow_id,
            "flow_name": flow_name,
            "automation_tier": AutomationTier(automation_tier),
            "status": CollectionFlowStatus.INITIALIZED,
            "current_phase": "initialization",
            "progress_percentage": 0.0,
            "flow_metadata": flow_metadata or {},
            "collection_config": collection_config or {},
            "client_account_id": self.client_account_id,
            "engagement_id": self.engagement_id,
            # master_flow_id should be provided via kwargs if needed
            **kwargs,
        }

        # Use parent class create method with no commit since we're in existing transaction
        collection_flow = await super().create(commit=False, **flow_data)

        logger.info(
            f"✅ Collection flow created (data only): flow_id={flow_id}, "
            f"master_flow_id={kwargs.get('master_flow_id', 'none')}"
        )

        return collection_flow

    async def create_with_master_flow(
        self,
        flow_id: str,
        flow_name: str,
        automation_tier: str,
        master_flow_id: uuid.UUID,
        flow_metadata: Optional[Dict[str, Any]] = None,
        collection_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> CollectionFlow:
        """
        Create a new collection flow with master flow linkage (data persistence only).

        This method is called by CollectionFlowLifecycleService after MFO registration.
        Repository ONLY handles data persistence, service handles orchestration.

        Args:
            flow_id: Child flow ID (user-facing identifier)
            flow_name: Name of the collection flow
            automation_tier: Automation tier
            master_flow_id: Master flow ID (from MFO)
            flow_metadata: Optional flow metadata
            collection_config: Optional collection configuration
            **kwargs: Additional parameters

        Returns:
            Created CollectionFlow instance
        """
        flow_data = {
            "flow_id": flow_id,
            "flow_name": flow_name,
            "automation_tier": AutomationTier(automation_tier),
            "status": CollectionFlowStatus.INITIALIZED,
            "current_phase": "initialization",
            "progress_percentage": 0.0,
            "flow_metadata": flow_metadata or {},
            "collection_config": collection_config or {},
            "client_account_id": self.client_account_id,
            "engagement_id": self.engagement_id,
            "master_flow_id": master_flow_id,  # Link to master flow
            **kwargs,
        }

        # Use parent class create method with no commit since we're in existing transaction
        collection_flow = await super().create(commit=False, **flow_data)

        logger.info(
            f"✅ Collection flow data persisted: flow_id={flow_id}, "
            f"master_flow_id={master_flow_id}"
        )

        return collection_flow

    async def update_status(
        self,
        flow_id: str,
        status: CollectionFlowStatus,
        current_phase: Optional[str] = None,
        progress_percentage: Optional[float] = None,
    ) -> Optional[CollectionFlow]:
        """Update collection flow status and progress."""

        update_data = {"status": status}
        if current_phase:
            update_data["current_phase"] = current_phase
        if progress_percentage is not None:
            update_data["progress_percentage"] = progress_percentage

        return await self.update_by_filters(update_data, flow_id=flow_id)

    async def get_flows_with_gaps(self) -> List[CollectionFlow]:
        """Get flows that are in gap analysis phase or have pending gaps."""
        # Per ADR-012: Use phase for operational state, not status
        all_flows = await self.get_by_filters()
        return [
            flow
            for flow in all_flows
            if flow.current_phase == CollectionPhase.GAP_ANALYSIS.value
        ]

    async def get_flows_by_automation_tier(
        self, tier: AutomationTier
    ) -> List[CollectionFlow]:
        """Get flows by automation tier."""
        return await self.get_by_filters(automation_tier=tier)

    async def get_flow_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics for collection flows."""
        # Get all flows and calculate metrics in Python for simplicity
        all_flows = await self.get_by_filters()

        # Count flows by status
        status_counts = {}
        total_progress = 0.0

        for flow in all_flows:
            status_key = (
                flow.status.value if hasattr(flow.status, "value") else str(flow.status)
            )
            status_counts[status_key] = status_counts.get(status_key, 0) + 1
            total_progress += flow.progress_percentage or 0.0

        avg_progress = total_progress / len(all_flows) if all_flows else 0.0

        return {
            "status_counts": status_counts,
            "average_progress": float(avg_progress),
            "total_flows": len(all_flows),
        }
