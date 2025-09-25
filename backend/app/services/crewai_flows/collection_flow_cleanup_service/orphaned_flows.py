"""
Orphaned flows cleanup operations
"""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow, CollectionFlowStatus
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)


class OrphanedFlowsCleanupService:
    """Service for cleaning up orphaned Collection flows"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def cleanup_orphaned_flows(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up flows that have lost their CrewAI state but still exist in PostgreSQL
        """
        try:
            # Find flows with master_flow_id but no corresponding CrewAI state
            query = select(CollectionFlow).where(
                and_(
                    CollectionFlow.engagement_id == self.context.engagement_id,
                    CollectionFlow.master_flow_id.isnot(None),
                    ~CollectionFlow.master_flow_id.in_(
                        select(CrewAIFlowStateExtensions.flow_id)
                    ),
                )
            )

            result = await self.db.execute(query)
            orphaned_flows = result.scalars().all()

            cleanup_summary = {
                "orphaned_flows_found": len(orphaned_flows),
                "flows_cleaned": 0,
                "dry_run": dry_run,
                "cleanup_details": [],
            }

            for flow in orphaned_flows:
                cleanup_detail = {
                    "flow_id": str(flow.id),
                    "flow_name": flow.flow_name,
                    "status": flow.status,
                    "master_flow_id": str(flow.master_flow_id),
                    "age_hours": (datetime.utcnow() - flow.updated_at).total_seconds()
                    / 3600,
                }

                if not dry_run:
                    # Reset master_flow_id or delete based on status
                    if flow.status in [
                        CollectionFlowStatus.COMPLETED.value,
                        CollectionFlowStatus.CANCELLED.value,
                    ]:
                        # Keep completed/cancelled flows but clear the orphaned reference
                        flow.master_flow_id = None
                        cleanup_detail["action"] = (
                            "Cleared orphaned master_flow_id reference"
                        )
                    else:
                        # Delete incomplete orphaned flows
                        await self.db.delete(flow)
                        cleanup_detail["action"] = "Deleted orphaned incomplete flow"
                        cleanup_summary["flows_cleaned"] += 1
                else:
                    cleanup_detail["action"] = "Would clear reference or delete flow"

                cleanup_summary["cleanup_details"].append(cleanup_detail)

            if not dry_run and orphaned_flows:
                await self.db.commit()
                logger.info(
                    f"Cleaned up {len(orphaned_flows)} orphaned Collection flows"
                )

            return cleanup_summary

        except Exception as e:
            logger.error(f"Orphaned flow cleanup failed: {e}")
            await self.db.rollback()
            raise
