"""
Simple Blocking Check

Lightweight service to check if flows are blocking data import.
Only considers flows in early phases where asset collection is incomplete.
"""

from typing import List, Dict, Any
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.models.discovery_flow import DiscoveryFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)

# Phases that block data import (asset collection not complete)
BLOCKING_PHASES = {
    "initialization",
    "data_import",
    "field_mapping",
    "attribute_mapping",
    "data_cleansing",
    "asset_inventory",
}

# Phases that DON'T block (assets already collected)
NON_BLOCKING_PHASES = {
    "dependency_analysis",  # Assets already in inventory
    "tech_debt_analysis",  # Assets already in inventory
    "finalization",  # Almost done
    "completed",  # Done
}


class SimpleBlockingCheck:
    """
    Simple service to check for blocking flows.
    Much simpler than the over-engineered flow recovery system.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def get_blocking_flows(self) -> List[Dict[str, Any]]:
        """
        Get flows that are actually blocking data import.

        Returns:
            List of blocking flow info
        """
        blocking_flows = []

        try:
            # Query discovery flows in blocking phases only
            query = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.client_account_id == self.context.client_account_id,
                    DiscoveryFlow.engagement_id == self.context.engagement_id,
                    # Not completed/failed/cancelled
                    DiscoveryFlow.status.notin_(["completed", "failed", "cancelled"]),
                    # In a blocking phase (early phases where assets aren't collected yet)
                    DiscoveryFlow.current_phase.in_(BLOCKING_PHASES),
                )
            )

            result = await self.db.execute(query)
            discovery_flows = result.scalars().all()

            for flow in discovery_flows:
                blocking_flows.append(
                    {
                        "flow_id": str(flow.flow_id),
                        "phase": flow.current_phase,
                        "status": flow.status,
                        "progress": flow.progress_percentage,
                        "created_at": (
                            flow.created_at.isoformat() if flow.created_at else None
                        ),
                        "is_blocking": True,
                        "reason": f"Flow in {flow.current_phase} phase - asset collection incomplete",
                    }
                )

            logger.info(f"Found {len(blocking_flows)} blocking flows")

        except Exception as e:
            logger.error(f"Error checking blocking flows: {e}")

        return blocking_flows

    async def is_phase_blocking(self, phase: str) -> bool:
        """
        Check if a specific phase blocks data import.

        Args:
            phase: Phase name to check

        Returns:
            True if phase blocks data import
        """
        return phase in BLOCKING_PHASES

    async def can_import_data(self) -> bool:
        """
        Check if data import is allowed (no blocking flows).

        Returns:
            True if data import is allowed
        """
        blocking_flows = await self.get_blocking_flows()
        return len(blocking_flows) == 0

    async def mark_flow_cancelled(self, flow_id: str) -> bool:
        """
        Simple flow cancellation - just mark as cancelled.

        Args:
            flow_id: Flow to cancel

        Returns:
            Success flag
        """
        try:
            # Update discovery flow
            await self.db.execute(
                DiscoveryFlow.__table__.update()
                .where(
                    and_(
                        DiscoveryFlow.flow_id == flow_id,
                        DiscoveryFlow.client_account_id
                        == self.context.client_account_id,
                        DiscoveryFlow.engagement_id == self.context.engagement_id,
                    )
                )
                .values(status="cancelled")
            )

            # Update master flow
            await self.db.execute(
                CrewAIFlowStateExtensions.__table__.update()
                .where(
                    and_(
                        CrewAIFlowStateExtensions.flow_id == flow_id,
                        CrewAIFlowStateExtensions.client_account_id
                        == self.context.client_account_id,
                        CrewAIFlowStateExtensions.engagement_id
                        == self.context.engagement_id,
                    )
                )
                .values(flow_status="cancelled")
            )

            await self.db.commit()
            logger.info(f"Flow {flow_id} cancelled successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel flow {flow_id}: {e}")
            await self.db.rollback()
            return False
