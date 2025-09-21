"""
Collection Flow repository with context-aware multi-tenant data access.
Provides collection flow-specific query methods with automatic client account scoping.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
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
        """Get collection flow by flow_id with context filtering."""
        return await self.get_by_filters(flow_id=flow_id)

    async def get_by_status(self, status: CollectionFlowStatus) -> List[CollectionFlow]:
        """Get collection flows by status with context filtering."""
        return await self.get_by_filters(status=status)

    async def get_active_flows(self) -> List[CollectionFlow]:
        """Get all active (non-completed/failed/cancelled) flows."""
        # Use the base class method to get all flows, then filter by status
        all_flows = await self.get_by_filters()
        active_statuses = [
            CollectionFlowStatus.INITIALIZED,
            CollectionFlowStatus.PLATFORM_DETECTION,
            CollectionFlowStatus.AUTOMATED_COLLECTION,
            CollectionFlowStatus.GAP_ANALYSIS,
            CollectionFlowStatus.MANUAL_COLLECTION,
        ]
        return [flow for flow in all_flows if flow.status in active_statuses]

    async def create(
        self,
        flow_name: str,
        automation_tier: str,
        flow_metadata: Optional[Dict[str, Any]] = None,
        collection_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> CollectionFlow:
        """Create a new collection flow with context."""

        # Generate flow_id if not provided
        flow_id = kwargs.get("flow_id") or str(UUID.uuid4())

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
            **kwargs,
        }

        return await self.create_record(**flow_data)

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
        return await self.get_by_filters(status=CollectionFlowStatus.GAP_ANALYSIS)

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
