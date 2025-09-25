"""
Expired flows cleanup operations
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow, CollectionFlowStatus

from .single_flow import SingleFlowCleanupService

logger = logging.getLogger(__name__)


class ExpiredFlowsCleanupService:
    """Service for cleaning up expired Collection flows"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self._single_flow_service = SingleFlowCleanupService(db, context)

    async def cleanup_expired_flows(
        self,
        expiration_hours: int = 72,
        dry_run: bool = True,
        include_failed: bool = True,
        include_cancelled: bool = True,
        force_cleanup_active: bool = False,
    ) -> Dict[str, Any]:
        """
        Clean up expired Collection flows with smart filtering

        Args:
            expiration_hours: Hours after which flows are considered expired
            dry_run: Preview cleanup without actually deleting
            include_failed: Include failed flows in cleanup
            include_cancelled: Include cancelled flows in cleanup
            force_cleanup_active: Force cleanup of active flows (dangerous)
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=expiration_hours)

            # Build status filter
            status_filters = []
            if include_cancelled:
                status_filters.append(CollectionFlowStatus.CANCELLED.value)
            if include_failed:
                status_filters.append(CollectionFlowStatus.FAILED.value)
            if force_cleanup_active:
                status_filters.extend(
                    [
                        CollectionFlowStatus.INITIALIZED.value,
                        CollectionFlowStatus.ASSET_SELECTION.value,
                        CollectionFlowStatus.GAP_ANALYSIS.value,
                        CollectionFlowStatus.MANUAL_COLLECTION.value,
                    ]
                )

            if not status_filters:
                return {
                    "flows_cleaned": 0,
                    "space_recovered": "0 KB",
                    "dry_run": dry_run,
                    "message": "No cleanup criteria specified",
                }

            # Query for expired flows
            query = (
                select(CollectionFlow)
                .options(
                    selectinload(CollectionFlow.data_gaps),
                    selectinload(CollectionFlow.questionnaire_responses),
                )
                .where(
                    and_(
                        CollectionFlow.engagement_id == self.context.engagement_id,
                        CollectionFlow.updated_at < cutoff_time,
                        CollectionFlow.status.in_(status_filters),
                    )
                )
                .order_by(CollectionFlow.updated_at.asc())
            )

            result = await self.db.execute(query)
            expired_flows = result.scalars().all()

            cleanup_summary = {
                "flows_found": len(expired_flows),
                "flows_cleaned": 0,
                "total_size_bytes": 0,
                "space_recovered": "0 KB",
                "dry_run": dry_run,
                "cleanup_details": [],
                "errors": [],
            }

            for flow in expired_flows:
                try:
                    flow_cleanup = await self._single_flow_service.cleanup_single_flow(
                        flow, dry_run
                    )
                    cleanup_summary["cleanup_details"].append(flow_cleanup)
                    cleanup_summary["total_size_bytes"] += flow_cleanup[
                        "estimated_size_bytes"
                    ]

                    if not dry_run:
                        cleanup_summary["flows_cleaned"] += 1

                except Exception as e:
                    error_detail = {
                        "flow_id": str(flow.id),
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    cleanup_summary["errors"].append(error_detail)
                    logger.error(f"Failed to cleanup flow {flow.id}: {e}")

            # Calculate space recovered
            if cleanup_summary["total_size_bytes"] > 0:
                kb_recovered = cleanup_summary["total_size_bytes"] / 1024
                if kb_recovered > 1024:
                    cleanup_summary["space_recovered"] = f"{kb_recovered / 1024:.1f} MB"
                else:
                    cleanup_summary["space_recovered"] = f"{kb_recovered:.1f} KB"

            if not dry_run and cleanup_summary["flows_cleaned"] > 0:
                await self.db.commit()
                logger.info(
                    f"Cleaned up {cleanup_summary['flows_cleaned']} Collection flows"
                )

            return cleanup_summary

        except Exception as e:
            logger.error(f"Collection flow cleanup failed: {e}")
            await self.db.rollback()
            raise
