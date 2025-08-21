"""
Collection Flow Lifecycle Management
Utilities for managing collection flow lifecycle states, completion detection,
and stale flow handling to resolve 409 conflicts.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
    CollectionPhase,
)

logger = logging.getLogger(__name__)


class CollectionFlowLifecycleManager:
    """Manager for collection flow lifecycle operations and state transitions."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def analyze_existing_flows(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze existing flows for the current engagement to provide options
        when a 409 conflict occurs.

        Returns:
            Dictionary with flow analysis and recommended actions
        """
        try:
            # Get all active flows for the engagement
            active_statuses = [
                CollectionFlowStatus.INITIALIZED.value,
                CollectionFlowStatus.PLATFORM_DETECTION.value,
                CollectionFlowStatus.AUTOMATED_COLLECTION.value,
                CollectionFlowStatus.GAP_ANALYSIS.value,
                CollectionFlowStatus.MANUAL_COLLECTION.value,
            ]

            query = (
                select(CollectionFlow)
                .where(
                    CollectionFlow.engagement_id == self.context.engagement_id,
                    CollectionFlow.status.in_(active_statuses),
                )
                .order_by(CollectionFlow.updated_at.desc())
            )

            result = await self.db.execute(query)
            active_flows = result.scalars().all()

            if not active_flows:
                return {
                    "has_active_flows": False,
                    "can_create_new": True,
                    "recommended_action": "create_new",
                    "message": "No active flows found. Safe to create new flow.",
                }

            # Analyze each flow
            flow_analysis = []
            now = datetime.utcnow()
            resumable_flows = []
            stale_flows = []
            recently_active_flows = []

            for flow in active_flows:
                analysis = await self._analyze_single_flow(flow, now)
                flow_analysis.append(analysis)

                if analysis["is_stale"]:
                    stale_flows.append(flow)
                elif analysis["is_resumable"]:
                    resumable_flows.append(flow)
                elif analysis["recently_active"]:
                    recently_active_flows.append(flow)

            # Determine recommended action
            recommended_action, message = self._determine_recommended_action(
                recently_active_flows, resumable_flows, stale_flows
            )

            return {
                "has_active_flows": True,
                "active_flow_count": len(active_flows),
                "flow_analysis": flow_analysis,
                "resumable_flows": len(resumable_flows),
                "stale_flows": len(stale_flows),
                "recently_active_flows": len(recently_active_flows),
                "recommended_action": recommended_action,
                "message": message,
                "can_create_new": recommended_action == "create_new",
                "options": self._generate_user_options(
                    recently_active_flows, resumable_flows, stale_flows
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing existing flows: {e}")
            raise

    async def _analyze_single_flow(
        self, flow: CollectionFlow, now: datetime
    ) -> Dict[str, Any]:
        """Analyze a single flow to determine its state and options."""

        # Calculate age and activity metrics
        age_hours = (now - flow.updated_at).total_seconds() / 3600
        creation_age_hours = (now - flow.created_at).total_seconds() / 3600

        # Determine if flow is stale (no activity in 24+ hours)
        is_stale = age_hours >= 24

        # Determine if flow is recently active (activity within 2 hours)
        recently_active = age_hours < 2

        # Check if flow appears to be stuck in initialization
        is_stuck_init = (
            flow.status == CollectionFlowStatus.INITIALIZED.value
            and creation_age_hours > 0.5  # Stuck if initializing for 30+ minutes
        )

        # Determine if flow is resumable (not stuck, has some progress)
        is_resumable = (
            not is_stuck_init
            and not is_stale
            and flow.status != CollectionFlowStatus.INITIALIZED.value
        )

        # Check for completion indicators
        completion_indicators = await self._check_completion_indicators(flow)

        # Determine flow health
        health_status = self._determine_flow_health(
            flow, is_stale, is_stuck_init, recently_active, completion_indicators
        )

        return {
            "flow_id": str(flow.flow_id),
            "flow_name": flow.flow_name,
            "status": flow.status,
            "current_phase": flow.current_phase,
            "progress_percentage": flow.progress_percentage,
            "age_hours": round(age_hours, 2),
            "creation_age_hours": round(creation_age_hours, 2),
            "is_stale": is_stale,
            "is_stuck_init": is_stuck_init,
            "recently_active": recently_active,
            "is_resumable": is_resumable,
            "health_status": health_status,
            "completion_indicators": completion_indicators,
            "last_activity": flow.updated_at.isoformat(),
            "created_at": flow.created_at.isoformat(),
        }

    async def _check_completion_indicators(
        self, flow: CollectionFlow
    ) -> Dict[str, Any]:
        """Check if a flow has indicators that it should be marked as complete."""

        indicators = {"should_be_complete": False, "reasons": [], "confidence": 0.0}

        # Check progress percentage
        if flow.progress_percentage >= 95:
            indicators["reasons"].append("Progress at 95%+")
            indicators["confidence"] += 0.3

        # Check if in finalization phase
        if flow.current_phase == CollectionPhase.FINALIZATION.value:
            indicators["reasons"].append("In finalization phase")
            indicators["confidence"] += 0.4

        # Check if assessment ready
        if flow.assessment_ready:
            indicators["reasons"].append("Marked as assessment ready")
            indicators["confidence"] += 0.3

        # Check for completion timestamp
        if flow.completed_at:
            indicators["reasons"].append("Has completion timestamp")
            indicators["confidence"] = 1.0

        # Determine if should be complete
        indicators["should_be_complete"] = indicators["confidence"] >= 0.7

        return indicators

    def _determine_flow_health(
        self,
        flow: CollectionFlow,
        is_stale: bool,
        is_stuck_init: bool,
        recently_active: bool,
        completion_indicators: Dict[str, Any],
    ) -> str:
        """Determine the overall health status of a flow."""

        if completion_indicators["should_be_complete"]:
            return "should_be_completed"
        elif is_stuck_init:
            return "stuck_initialization"
        elif is_stale:
            return "stale"
        elif recently_active:
            return "active"
        elif flow.status == CollectionFlowStatus.FAILED.value:
            return "failed"
        elif flow.error_message:
            return "error"
        else:
            return "idle"

    def _determine_recommended_action(
        self,
        recently_active: List[CollectionFlow],
        resumable: List[CollectionFlow],
        stale: List[CollectionFlow],
    ) -> Tuple[str, str]:
        """Determine the recommended action based on flow analysis."""

        if recently_active:
            return "resume_existing", (
                f"Found {len(recently_active)} recently active flow(s). "
                "Recommend resuming existing flow instead of creating new one."
            )

        if resumable and not stale:
            return "resume_existing", (
                f"Found {len(resumable)} resumable flow(s). "
                "Recommend resuming existing flow."
            )

        if stale:
            return "cleanup_and_create", (
                f"Found {len(stale)} stale flow(s). "
                "Recommend cleaning up stale flows and creating new one."
            )

        return "create_new", "No active flows preventing new flow creation."

    def _generate_user_options(
        self,
        recently_active: List[CollectionFlow],
        resumable: List[CollectionFlow],
        stale: List[CollectionFlow],
    ) -> List[Dict[str, Any]]:
        """Generate user-friendly options for handling existing flows."""

        options = []

        if recently_active:
            options.append(
                {
                    "action": "resume_existing",
                    "title": "Resume Active Flow",
                    "description": f"Continue with the recently active flow ({recently_active[0].flow_name})",
                    "flow_id": str(recently_active[0].flow_id),
                    "recommended": True,
                }
            )

        if resumable:
            for flow in resumable[:2]:  # Show max 2 resumable options
                options.append(
                    {
                        "action": "resume_existing",
                        "title": f"Resume Flow: {flow.flow_name}",
                        "description": (
                            f"Continue from {flow.current_phase} phase "
                            f"({flow.progress_percentage:.1f}% complete)"
                        ),
                        "flow_id": str(flow.flow_id),
                        "recommended": len(recently_active) == 0,
                    }
                )

        if stale:
            options.append(
                {
                    "action": "cancel_stale_and_create",
                    "title": "Cancel Stale Flows & Create New",
                    "description": f"Cancel {len(stale)} stale flow(s) and start fresh",
                    "flow_ids": [str(flow.flow_id) for flow in stale],
                    "recommended": len(recently_active) == 0 and len(resumable) == 0,
                }
            )

        # Always offer the option to create with explicit override
        options.append(
            {
                "action": "force_create_new",
                "title": "Force Create New Flow",
                "description": "Create a new flow alongside existing ones (use with caution)",
                "recommended": False,
                "warning": "This may create duplicate flows",
            }
        )

        return options

    async def auto_complete_eligible_flows(self) -> Dict[str, Any]:
        """
        Auto-complete flows that have completion indicators but aren't marked complete.

        Returns:
            Summary of flows that were auto-completed
        """
        try:
            # Find flows that should be completed
            active_statuses = [
                CollectionFlowStatus.INITIALIZED.value,
                CollectionFlowStatus.PLATFORM_DETECTION.value,
                CollectionFlowStatus.AUTOMATED_COLLECTION.value,
                CollectionFlowStatus.GAP_ANALYSIS.value,
                CollectionFlowStatus.MANUAL_COLLECTION.value,
            ]

            query = select(CollectionFlow).where(
                CollectionFlow.engagement_id == self.context.engagement_id,
                CollectionFlow.status.in_(active_statuses),
            )

            result = await self.db.execute(query)
            active_flows = result.scalars().all()

            completed_flows = []

            for flow in active_flows:
                completion_indicators = await self._check_completion_indicators(flow)

                if completion_indicators["should_be_complete"]:
                    # Auto-complete the flow
                    flow.status = CollectionFlowStatus.COMPLETED.value
                    flow.completed_at = datetime.utcnow()
                    flow.progress_percentage = 100.0

                    # Add completion metadata
                    if not flow.flow_metadata:
                        flow.flow_metadata = {}
                    flow.flow_metadata["auto_completed"] = True
                    flow.flow_metadata["auto_completed_at"] = (
                        datetime.utcnow().isoformat()
                    )
                    flow.flow_metadata["completion_reasons"] = completion_indicators[
                        "reasons"
                    ]
                    flow.flow_metadata["completion_confidence"] = completion_indicators[
                        "confidence"
                    ]

                    completed_flows.append(
                        {
                            "flow_id": str(flow.flow_id),
                            "flow_name": flow.flow_name,
                            "reasons": completion_indicators["reasons"],
                            "confidence": completion_indicators["confidence"],
                        }
                    )

            if completed_flows:
                await self.db.commit()
                logger.info(f"Auto-completed {len(completed_flows)} collection flows")

            return {
                "flows_completed": len(completed_flows),
                "completed_flows": completed_flows,
            }

        except Exception as e:
            logger.error(f"Error auto-completing flows: {e}")
            await self.db.rollback()
            raise

    async def cancel_stale_flows(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Cancel flows that have been stale for more than the specified time.

        Args:
            max_age_hours: Maximum age in hours before a flow is considered stale

        Returns:
            Summary of cancelled flows
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

            # Find stale flows
            active_statuses = [
                CollectionFlowStatus.INITIALIZED.value,
                CollectionFlowStatus.PLATFORM_DETECTION.value,
                CollectionFlowStatus.AUTOMATED_COLLECTION.value,
                CollectionFlowStatus.GAP_ANALYSIS.value,
                CollectionFlowStatus.MANUAL_COLLECTION.value,
            ]

            query = select(CollectionFlow).where(
                CollectionFlow.engagement_id == self.context.engagement_id,
                CollectionFlow.status.in_(active_statuses),
                CollectionFlow.updated_at < cutoff_time,
            )

            result = await self.db.execute(query)
            stale_flows = result.scalars().all()

            cancelled_flows = []

            for flow in stale_flows:
                age_hours = (datetime.utcnow() - flow.updated_at).total_seconds() / 3600

                # Cancel the stale flow
                flow.status = CollectionFlowStatus.CANCELLED.value
                flow.completed_at = datetime.utcnow()
                flow.error_message = f"Flow cancelled due to inactivity (stale for {age_hours:.1f} hours)"

                if not flow.flow_metadata:
                    flow.flow_metadata = {}
                flow.flow_metadata["auto_cancelled"] = True
                flow.flow_metadata["auto_cancelled_at"] = datetime.utcnow().isoformat()
                flow.flow_metadata["stale_hours"] = age_hours

                cancelled_flows.append(
                    {
                        "flow_id": str(flow.flow_id),
                        "flow_name": flow.flow_name,
                        "age_hours": round(age_hours, 2),
                        "status": flow.status,
                    }
                )

            if cancelled_flows:
                await self.db.commit()
                logger.info(
                    f"Auto-cancelled {len(cancelled_flows)} stale collection flows"
                )

            return {
                "flows_cancelled": len(cancelled_flows),
                "cancelled_flows": cancelled_flows,
            }

        except Exception as e:
            logger.error(f"Error cancelling stale flows: {e}")
            await self.db.rollback()
            raise
