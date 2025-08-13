"""
Auto-Complete Monitor

Monitors flows and automatically marks them as completed when they reach 100% progress
or have completed phase, preventing them from incorrectly blocking uploads.
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


class AutoCompleteMonitor:
    """
    Monitors and auto-completes flows that have finished but aren't marked as completed
    """

    def __init__(self, db: AsyncSession, context: Optional[RequestContext] = None):
        """
        Initialize the auto-complete monitor

        Args:
            db: Database session
            context: Optional request context for filtering
        """
        self.db = db
        self.context = context

    async def check_and_complete_flows(self) -> List[str]:
        """
        Check for flows that should be marked as completed and update them

        Returns:
            List of flow IDs that were auto-completed
        """
        completed_flow_ids = []

        try:
            # Find discovery flows that should be completed
            discovery_flows = await self._find_completable_discovery_flows()

            for flow in discovery_flows:
                if await self._mark_flow_completed(flow):
                    completed_flow_ids.append(str(flow.flow_id))
                    logger.info(
                        f"✅ Auto-completed flow {flow.flow_id}: "
                        f"phase={flow.current_phase}, progress={flow.progress_percentage}%"
                    )

            # Also check master flow records
            master_flows = await self._find_completable_master_flows()

            for master_flow in master_flows:
                if await self._mark_master_flow_completed(master_flow):
                    if str(master_flow.flow_id) not in completed_flow_ids:
                        completed_flow_ids.append(str(master_flow.flow_id))
                    logger.info(
                        f"✅ Auto-completed master flow record: {master_flow.flow_id}"
                    )

            if completed_flow_ids:
                await self.db.commit()
                logger.info(f"✅ Auto-completed {len(completed_flow_ids)} flows total")

        except Exception as e:
            logger.error(f"Error in auto-complete monitor: {e}")
            await self.db.rollback()

        return completed_flow_ids

    async def _find_completable_discovery_flows(self) -> List[DiscoveryFlow]:
        """
        Find discovery flows that should be marked as completed

        Returns:
            List of discovery flows that need completion
        """
        query = select(DiscoveryFlow).where(
            and_(
                # Status is not already completed
                DiscoveryFlow.status.notin_(["completed", "failed", "cancelled"]),
                # But either phase is completed OR progress is 100%
                (
                    (DiscoveryFlow.current_phase == "completed")
                    | (DiscoveryFlow.progress_percentage >= 100.0)
                    | (DiscoveryFlow.current_phase == "finalization")
                ),
            )
        )

        # Apply context filtering if available
        if self.context:
            query = query.where(
                and_(
                    DiscoveryFlow.client_account_id == self.context.client_account_id,
                    DiscoveryFlow.engagement_id == self.context.engagement_id,
                )
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _find_completable_master_flows(self) -> List[CrewAIFlowStateExtensions]:
        """
        Find master flows that should be marked as completed

        Returns:
            List of master flow records that need completion
        """
        query = select(CrewAIFlowStateExtensions).where(
            and_(
                CrewAIFlowStateExtensions.flow_status.notin_(
                    ["completed", "failed", "cancelled"]
                ),
                CrewAIFlowStateExtensions.flow_type == "discovery",
            )
        )

        # Apply context filtering if available
        if self.context:
            query = query.where(
                and_(
                    CrewAIFlowStateExtensions.client_account_id
                    == self.context.client_account_id,
                    CrewAIFlowStateExtensions.engagement_id
                    == self.context.engagement_id,
                )
            )

        result = await self.db.execute(query)
        master_flows = list(result.scalars().all())

        # Check each master flow to see if its child is completed
        completable_flows = []
        for master_flow in master_flows:
            # Check corresponding discovery flow
            discovery_query = select(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == master_flow.flow_id
            )
            discovery_result = await self.db.execute(discovery_query)
            discovery_flow = discovery_result.scalar_one_or_none()

            if discovery_flow and (
                discovery_flow.status == "completed"
                or discovery_flow.current_phase == "completed"
                or discovery_flow.progress_percentage >= 100.0
            ):
                completable_flows.append(master_flow)

        return completable_flows

    async def _mark_flow_completed(self, flow: DiscoveryFlow) -> bool:
        """
        Mark a discovery flow as completed

        Args:
            flow: The discovery flow to complete

        Returns:
            True if successfully marked as completed
        """
        try:
            # Update discovery flow
            await self.db.execute(
                update(DiscoveryFlow)
                .where(DiscoveryFlow.flow_id == flow.flow_id)
                .values(
                    status="completed",
                    progress_percentage=100.0,
                    completed_at=flow.completed_at or datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

            # Also update master flow
            await self.db.execute(
                update(CrewAIFlowStateExtensions)
                .where(CrewAIFlowStateExtensions.flow_id == flow.flow_id)
                .values(flow_status="completed", updated_at=datetime.utcnow())
            )

            return True

        except Exception as e:
            logger.error(f"Failed to mark flow {flow.flow_id} as completed: {e}")
            return False

    async def _mark_master_flow_completed(
        self, master_flow: CrewAIFlowStateExtensions
    ) -> bool:
        """
        Mark a master flow record as completed

        Args:
            master_flow: The master flow to complete

        Returns:
            True if successfully marked as completed
        """
        try:
            await self.db.execute(
                update(CrewAIFlowStateExtensions)
                .where(CrewAIFlowStateExtensions.flow_id == master_flow.flow_id)
                .values(flow_status="completed", updated_at=datetime.utcnow())
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to mark master flow {master_flow.flow_id} as completed: {e}"
            )
            return False

    async def is_flow_truly_incomplete(self, flow_id: str) -> bool:
        """
        Check if a flow is truly incomplete (not just miscategorized)

        Args:
            flow_id: The flow ID to check

        Returns:
            True if the flow is genuinely incomplete, False if it should be completed
        """
        try:
            # Check discovery flow
            discovery_query = select(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == flow_id
            )
            discovery_result = await self.db.execute(discovery_query)
            discovery_flow = discovery_result.scalar_one_or_none()

            if not discovery_flow:
                return True  # Can't find flow, consider it incomplete

            # Check if it should actually be completed
            should_be_completed = (
                discovery_flow.current_phase == "completed"
                or discovery_flow.progress_percentage >= 100.0
                or discovery_flow.status == "completed"
            )

            if should_be_completed:
                # Auto-fix it if needed
                if discovery_flow.status != "completed":
                    logger.info(f"Auto-fixing miscategorized flow {flow_id}")
                    await self._mark_flow_completed(discovery_flow)
                    await self.db.commit()
                return False  # Not truly incomplete

            # It's genuinely incomplete
            return True

        except Exception as e:
            logger.error(f"Error checking flow incompleteness for {flow_id}: {e}")
            return True  # Assume incomplete on error
