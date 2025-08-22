"""
Collection Flow Analysis Service
Provides analysis functionality for collection flows including completion detection,
health assessment, and user option generation.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
    CollectionPhase,
)

logger = logging.getLogger(__name__)


class CollectionFlowAnalyzer:
    """Service for analyzing collection flow states and generating recommendations."""

    def _ensure_timezone_aware(self, dt: datetime) -> datetime:
        """Ensure a datetime is timezone-aware, assuming UTC if naive."""
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    async def analyze_single_flow(
        self, flow: CollectionFlow, now: datetime
    ) -> Dict[str, Any]:
        """Analyze a single flow to determine its state and options."""

        # Calculate age and activity metrics
        # Use updated_at for activity, fallback to created_at for both if updated_at is null
        last_activity = self._ensure_timezone_aware(flow.updated_at or flow.created_at)
        creation_time = self._ensure_timezone_aware(flow.created_at)

        age_hours = (
            (now - last_activity).total_seconds() / 3600 if last_activity else 0.0
        )
        creation_age_hours = (
            (now - creation_time).total_seconds() / 3600 if creation_time else 0.0
        )

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
        completion_indicators = await self.check_completion_indicators(flow)

        # Determine flow health
        health_status = self.determine_flow_health(
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
            "last_activity": last_activity.isoformat() if last_activity else None,
            "created_at": creation_time.isoformat() if creation_time else None,
        }

    async def check_completion_indicators(self, flow: CollectionFlow) -> Dict[str, Any]:
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

    def determine_flow_health(
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

    def determine_recommended_action(
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

    def generate_user_options(
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
