"""
Collection Flow Cleanup Service

Smart cleanup implementation for Collection flows with enhanced persistence management.
Handles expired flows, orphaned state, and flow lifecycle management.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow, CollectionFlowStatus
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)


class CollectionFlowCleanupService:
    """
    Enhanced cleanup service for Collection flows with smart detection
    and multi-layer persistence cleanup.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

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
                        CollectionFlowStatus.PLATFORM_DETECTION.value,
                        CollectionFlowStatus.AUTOMATED_COLLECTION.value,
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
                    flow_cleanup = await self._cleanup_single_flow(flow, dry_run)
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

    async def _cleanup_single_flow(
        self, flow: CollectionFlow, dry_run: bool
    ) -> Dict[str, Any]:
        """Clean up a single Collection flow and calculate impact"""

        # Calculate estimated size
        estimated_size = self._calculate_flow_size(flow)

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

        else:
            # Dry run - just record what would be done
            cleanup_detail["cleanup_actions"] = [
                "Would remove main flow record",
                f"Would remove {cleanup_detail['related_records']['gap_analyses']} gap analyses",
                f"Would remove {cleanup_detail['related_records']['questionnaire_responses']} questionnaire responses",
            ]

            if flow.master_flow_id:
                cleanup_detail["cleanup_actions"].append(
                    "Would remove CrewAI flow state"
                )

        return cleanup_detail

    def _calculate_flow_size(self, flow: CollectionFlow) -> int:
        """Calculate estimated size of flow data in bytes"""
        size = 0

        # Base flow data
        size += len(str(flow.flow_metadata)) if flow.flow_metadata else 0
        size += len(str(flow.collection_config)) if flow.collection_config else 0
        size += len(str(flow.phase_state)) if flow.phase_state else 0
        size += len(str(flow.user_inputs)) if flow.user_inputs else 0
        size += len(str(flow.phase_results)) if flow.phase_results else 0
        size += len(str(flow.agent_insights)) if flow.agent_insights else 0
        size += len(str(flow.collected_platforms)) if flow.collected_platforms else 0
        size += len(str(flow.collection_results)) if flow.collection_results else 0
        size += len(str(flow.gap_analysis_results)) if flow.gap_analysis_results else 0
        size += len(str(flow.error_details)) if flow.error_details else 0

        # Text fields
        size += len(flow.flow_name) if flow.flow_name else 0
        size += len(flow.error_message) if flow.error_message else 0

        # Related records (estimated)
        if hasattr(flow, "data_gaps") and flow.data_gaps:
            size += len(flow.data_gaps) * 500  # Estimate 500 bytes per gap analysis

        if hasattr(flow, "questionnaire_responses") and flow.questionnaire_responses:
            size += (
                len(flow.questionnaire_responses) * 1000
            )  # Estimate 1KB per response

        return size

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
                        cleanup_detail[
                            "action"
                        ] = "Cleared orphaned master_flow_id reference"
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
                if self._is_cleanup_candidate(flow, now):
                    recommendations["cleanup_candidates"].append(
                        {
                            "flow_id": str(flow.id),
                            "flow_name": flow.flow_name,
                            "status": flow.status,
                            "age_days": age_days,
                            "reason": self._get_cleanup_reason(flow, now),
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
                    f"Review {recommendations['status_breakdown'][CollectionFlowStatus.FAILED.value]} failed flows for cleanup"
                )

            if recommendations["age_analysis"]["older_than_90_days"] > 0:
                recommendations["recommendations"].append(
                    f"Consider archiving {recommendations['age_analysis']['older_than_90_days']} flows older than 90 days"
                )

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate cleanup recommendations: {e}")
            raise

    def _is_cleanup_candidate(
        self, flow: CollectionFlow, current_time: datetime
    ) -> bool:
        """Determine if a flow is a candidate for cleanup"""
        age_days = (current_time - flow.updated_at).days

        # Failed flows older than 7 days
        if flow.status == CollectionFlowStatus.FAILED.value and age_days > 7:
            return True

        # Cancelled flows older than 30 days
        if flow.status == CollectionFlowStatus.CANCELLED.value and age_days > 30:
            return True

        # Completed flows older than 90 days
        if flow.status == CollectionFlowStatus.COMPLETED.value and age_days > 90:
            return True

        # Stale incomplete flows (no update in 7+ days)
        if (
            flow.status
            in [
                CollectionFlowStatus.INITIALIZED.value,
                CollectionFlowStatus.PLATFORM_DETECTION.value,
                CollectionFlowStatus.AUTOMATED_COLLECTION.value,
                CollectionFlowStatus.GAP_ANALYSIS.value,
                CollectionFlowStatus.MANUAL_COLLECTION.value,
            ]
            and age_days > 7
        ):
            return True

        return False

    def _get_cleanup_reason(self, flow: CollectionFlow, current_time: datetime) -> str:
        """Get the reason why a flow is recommended for cleanup"""
        age_days = (current_time - flow.updated_at).days

        if flow.status == CollectionFlowStatus.FAILED.value:
            return f"Failed flow, {age_days} days old"
        elif flow.status == CollectionFlowStatus.CANCELLED.value:
            return f"Cancelled flow, {age_days} days old"
        elif flow.status == CollectionFlowStatus.COMPLETED.value:
            return f"Completed flow, {age_days} days old"
        else:
            return f"Stale incomplete flow, no activity for {age_days} days"

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
                    flow.error_message = f"Flow cancelled due to initialization timeout (stuck for {round(age_minutes, 1)} minutes)"
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
