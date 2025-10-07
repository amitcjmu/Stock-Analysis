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
        """Create a new collection flow with Master Flow Orchestrator (MFO) integration."""
        from app.core.context import RequestContext
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator

        # Generate flow_id if not provided
        flow_id = kwargs.get("flow_id") or str(uuid.uuid4())

        # Prepare context for MFO
        context = RequestContext(
            client_account_id=self.client_account_id,
            engagement_id=self.engagement_id,
            user_id=kwargs.get("user_id", "system"),
        )

        # Prepare master flow configuration
        master_flow_config = {
            "flow_name": flow_name,
            "automation_tier": automation_tier,
            "metadata": flow_metadata or {},
            "collection_config": collection_config or {},
        }

        # Prepare master flow initial state
        initial_state = {
            "current_phase": "initialization",
            "progress_percentage": 0.0,
            "collection_config": collection_config or {},
            "flow_metadata": flow_metadata or {},
        }

        # Use existing transaction to create both master and child flows atomically
        # Step 1: Register flow with Master Flow Orchestrator (ADR-006 pattern)
        mfo = MasterFlowOrchestrator(self.db, context)
        master_flow_id, master_flow_data = await mfo.create_flow(
            flow_type="collection",
            flow_name=flow_name,
            configuration=master_flow_config,
            initial_state=initial_state,
            atomic=True,  # Prevents internal commits
        )

        # Step 2: Flush to make master flow ID available for FK relationship
        await self.db.flush()

        # Step 3: Create child collection flow with master_flow_id linkage
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

        # Transaction will be automatically committed by get_db() context manager
        logger.info(
            f"✅ Collection flow created with MFO integration: "
            f"flow_id={flow_id}, master_flow_id={master_flow_id}"
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
