"""
Cleanup recommendations and analysis operations
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow, CollectionFlowStatus

from .base import CleanupUtils

logger = logging.getLogger(__name__)


class CleanupRecommendationsService:
    """Service for analyzing flows and providing cleanup recommendations"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def get_cleanup_recommendations(self) -> Dict[str, Any]:
        """
        Analyze Collection flows and provide cleanup recommendations
        """
        try:
            # Get flow statistics
            all_flows_result = await self.db.execute(
                select(CollectionFlow)
                .where(CollectionFlow.engagement_id == self.context.engagement_id)
                .order_by(CollectionFlow.updated_at.desc())
            )
            all_flows = all_flows_result.scalars().all()

            now = datetime.utcnow()
            recommendations = {
                "total_flows": len(all_flows),
                "status_breakdown": {},
                "age_analysis": {
                    "older_than_7_days": 0,
                    "older_than_30_days": 0,
                    "older_than_90_days": 0,
                },
                "cleanup_candidates": [],
                "recommendations": [],
            }

            # Analyze flows
            for flow in all_flows:
                # Status breakdown
                status = flow.status
                recommendations["status_breakdown"][status] = (
                    recommendations["status_breakdown"].get(status, 0) + 1
                )

                # Age analysis
                age_days = (now - flow.updated_at).days
                if age_days > 7:
                    recommendations["age_analysis"]["older_than_7_days"] += 1
                if age_days > 30:
                    recommendations["age_analysis"]["older_than_30_days"] += 1
                if age_days > 90:
                    recommendations["age_analysis"]["older_than_90_days"] += 1

                # Cleanup candidates
                if CleanupUtils.is_cleanup_candidate(flow, now):
                    recommendations["cleanup_candidates"].append(
                        {
                            "flow_id": str(flow.id),
                            "flow_name": flow.flow_name,
                            "status": flow.status,
                            "age_days": age_days,
                            "reason": CleanupUtils.get_cleanup_reason(flow, now),
                        }
                    )

            # Generate recommendations
            if recommendations["cleanup_candidates"]:
                recommendations["recommendations"].append(
                    f"Consider cleaning up {len(recommendations['cleanup_candidates'])} old or failed flows"
                )

            if (
                recommendations["status_breakdown"].get(
                    CollectionFlowStatus.FAILED.value, 0
                )
                > 0
            ):
                recommendations["recommendations"].append(
                    f"Review {recommendations['status_breakdown'][CollectionFlowStatus.FAILED.value]} "
                    f"failed flows for cleanup"
                )

            if recommendations["age_analysis"]["older_than_90_days"] > 0:
                recommendations["recommendations"].append(
                    f"Consider archiving {recommendations['age_analysis']['older_than_90_days']} "
                    f"flows older than 90 days"
                )

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate cleanup recommendations: {e}")
            raise

    async def cleanup_stuck_initialized_flows(
        self, timeout_minutes: int = 5, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Clean up flows stuck in INITIALIZED state

        Args:
            timeout_minutes: Minutes after which INITIALIZED flows are considered stuck
            dry_run: Preview cleanup without actually performing it
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)

            # Find stuck INITIALIZED flows
            query = select(CollectionFlow).where(
                and_(
                    CollectionFlow.engagement_id == self.context.engagement_id,
                    CollectionFlow.status == CollectionFlowStatus.INITIALIZED.value,
                    CollectionFlow.created_at < cutoff_time,
                )
            )

            result = await self.db.execute(query)
            stuck_flows = result.scalars().all()

            cleanup_summary = {
                "stuck_flows_found": len(stuck_flows),
                "flows_cleaned": 0,
                "dry_run": dry_run,
                "cleanup_details": [],
            }

            for flow in stuck_flows:
                age_minutes = (datetime.utcnow() - flow.created_at).total_seconds() / 60

                cleanup_detail = {
                    "flow_id": str(flow.id),
                    "flow_name": flow.flow_name,
                    "age_minutes": round(age_minutes, 2),
                    "created_at": flow.created_at.isoformat(),
                }

                if not dry_run:
                    # Cancel the stuck flow
                    flow.status = CollectionFlowStatus.CANCELLED.value
                    flow.completed_at = datetime.utcnow()
                    flow.error_message = (
                        f"Flow cancelled due to initialization timeout "
                        f"(stuck for {round(age_minutes, 1)} minutes)"
                    )
                    flow.error_details = {
                        "timeout_minutes": timeout_minutes,
                        "age_minutes": age_minutes,
                        "auto_cancelled_at": datetime.utcnow().isoformat(),
                    }
                    cleanup_detail["action"] = "Cancelled stuck flow"
                    cleanup_summary["flows_cleaned"] += 1
                else:
                    cleanup_detail["action"] = "Would cancel stuck flow"

                cleanup_summary["cleanup_details"].append(cleanup_detail)

            if not dry_run and stuck_flows:
                await self.db.commit()
                logger.info(f"Cleaned up {len(stuck_flows)} stuck INITIALIZED flows")

            return cleanup_summary

        except Exception as e:
            logger.error(f"Failed to cleanup stuck initialized flows: {e}")
            await self.db.rollback()
            raise
