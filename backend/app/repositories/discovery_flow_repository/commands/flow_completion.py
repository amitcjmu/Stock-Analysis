"""
Flow completion operations.

Handles flow completion and final status updates.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, update

from app.models.discovery_flow import DiscoveryFlow
from .flow_base import FlowCommandsBase

logger = logging.getLogger(__name__)


class FlowCompletionCommands(FlowCommandsBase):
    """Handles flow completion operations"""

    async def mark_flow_complete(
        self, flow_id: str, readiness_scores: Optional[dict] = None
    ) -> Optional[DiscoveryFlow]:
        """
        Mark flow as complete.

        Args:
            flow_id: The flow ID to mark as complete
            readiness_scores: Optional readiness scores calculated by service layer.
                            If not provided, default scores will be used.

        Returns:
            Updated DiscoveryFlow or None if not found

        Note:
            Readiness score calculation should be performed in the service layer
            and passed to this repository method for data persistence only.
        """

        # Ensure flow_id is UUID
        flow_uuid = self._ensure_uuid(flow_id)

        # Get existing flow to update state data
        existing_flow = await self.flow_queries.get_by_flow_id(flow_id)
        if not existing_flow:
            return None

        # Update state data
        state_data = existing_flow.crewai_state_data or {}
        state_data["status"] = "complete"
        state_data["completed_at"] = datetime.utcnow().isoformat()

        # Use provided readiness scores or defaults
        # Repository layer does NOT calculate business logic - only persists data
        if readiness_scores:
            state_data["readiness_scores"] = readiness_scores
        else:
            # Provide default readiness scores if service layer didn't provide them
            logger.info(
                f"No readiness scores provided by service layer for {flow_id}, using defaults"
            )
            state_data["readiness_scores"] = {
                "overall": 85.0,
                "data_quality": 80.0,
                "mapping_completeness": 90.0,
                "asset_coverage": 85.0,
                "dependency_analysis": 90.0,
                "assessment_ready": True,
            }

        stmt = (
            update(DiscoveryFlow)
            .where(
                and_(
                    DiscoveryFlow.flow_id == flow_uuid,
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                )
            )
            .values(
                status="complete",
                progress_percentage=100.0,
                completed_at=datetime.utcnow(),
                assessment_ready=True,
                crewai_state_data=state_data,
                updated_at=datetime.utcnow(),
            )
        )

        await self.db.execute(stmt)
        # 🔧 CC FIX: Remove duplicate commit - transaction boundary managed by caller
        # This ensures atomicity with the parent flow_phase_management transaction
        # await self.db.commit()  # REMOVED to prevent double commit

        # Invalidate cache after update
        updated_flow = await self.flow_queries.get_by_flow_id(flow_id)
        if updated_flow:
            await self._invalidate_flow_cache(updated_flow)

        return updated_flow

    async def complete_discovery_flow(
        self, flow_id: str, readiness_scores: Optional[dict] = None
    ) -> Optional[DiscoveryFlow]:
        """
        Complete discovery flow and prepare for assessment handoff.

        Args:
            flow_id: The flow ID to complete
            readiness_scores: Optional readiness scores calculated by service layer

        Returns:
            Completed DiscoveryFlow or None if not found

        Note:
            This repository method only handles data persistence.
            Master flow coordination should be performed by the service layer.
        """
        try:
            logger.info(f"🏁 Completing discovery flow: {flow_id}")

            # Use the existing mark_flow_complete method
            completed_flow = await self.mark_flow_complete(flow_id, readiness_scores)

            if not completed_flow:
                logger.error(f"❌ Failed to complete flow {flow_id} - flow not found")
                return None

            logger.info(f"✅ Discovery flow completed successfully: {flow_id}")
            return completed_flow

        except Exception as e:
            logger.error(f"❌ Failed to complete discovery flow {flow_id}: {e}")
            return None
