"""
Single flow cleanup operations
"""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

from .base import CleanupUtils

logger = logging.getLogger(__name__)


class SingleFlowCleanupService:
    """Service for cleaning up a single Collection flow"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def cleanup_single_flow(
        self, flow: CollectionFlow, dry_run: bool
    ) -> Dict[str, Any]:
        """Clean up a single Collection flow and calculate impact"""

        # Calculate estimated size
        estimated_size = CleanupUtils.calculate_flow_size(flow)

        cleanup_detail = {
            "flow_id": str(flow.id),
            "flow_name": flow.flow_name,
            "status": flow.status,
            "current_phase": flow.current_phase,
            "age_hours": (datetime.utcnow() - flow.updated_at).total_seconds() / 3600,
            "estimated_size_bytes": estimated_size,
            "related_records": {
                "gap_analyses": len(flow.data_gaps) if flow.data_gaps else 0,
                "questionnaire_responses": (
                    len(flow.questionnaire_responses)
                    if flow.questionnaire_responses
                    else 0
                ),
            },
            "cleanup_actions": [],
        }

        if not dry_run:
            # Perform actual cleanup
            await self._perform_cleanup(flow, cleanup_detail)
        else:
            # Dry run - just record what would be done
            await self._simulate_cleanup(flow, cleanup_detail)

        return cleanup_detail

    async def _perform_cleanup(
        self, flow: CollectionFlow, cleanup_detail: Dict[str, Any]
    ) -> None:
        """Perform actual cleanup operations"""

        # 1. Clean up from CrewAI flow state if exists
        if flow.master_flow_id:
            try:
                crewai_state_result = await self.db.execute(
                    select(CrewAIFlowStateExtensions).where(
                        CrewAIFlowStateExtensions.flow_id == flow.master_flow_id
                    )
                )
                crewai_state = crewai_state_result.scalar_one_or_none()

                if crewai_state:
                    await self.db.delete(crewai_state)
                    cleanup_detail["cleanup_actions"].append(
                        "Removed CrewAI flow state"
                    )

            except Exception as e:
                logger.warning(
                    f"Failed to cleanup CrewAI state for flow {flow.id}: {e}"
                )
                cleanup_detail["cleanup_actions"].append(
                    f"CrewAI cleanup failed: {str(e)}"
                )

        # 2. Delete related gap analyses (if not handled by cascade)
        if flow.data_gaps:
            for gap in flow.data_gaps:
                await self.db.delete(gap)
            cleanup_detail["cleanup_actions"].append(
                f"Removed {len(flow.data_gaps)} gap analyses"
            )

        # 3. Delete related questionnaire responses (if not handled by cascade)
        if flow.questionnaire_responses:
            for response in flow.questionnaire_responses:
                await self.db.delete(response)
            cleanup_detail["cleanup_actions"].append(
                f"Removed {len(flow.questionnaire_responses)} questionnaire responses"
            )

        # 4. Delete the main flow record
        await self.db.delete(flow)
        cleanup_detail["cleanup_actions"].append("Removed main flow record")

    async def _simulate_cleanup(
        self, flow: CollectionFlow, cleanup_detail: Dict[str, Any]
    ) -> None:
        """Simulate cleanup operations for dry run"""
        cleanup_detail["cleanup_actions"] = [
            "Would remove main flow record",
            f"Would remove {cleanup_detail['related_records']['gap_analyses']} gap analyses",
            f"Would remove {cleanup_detail['related_records']['questionnaire_responses']} questionnaire responses",
        ]

        if flow.master_flow_id:
            cleanup_detail["cleanup_actions"].append("Would remove CrewAI flow state")
