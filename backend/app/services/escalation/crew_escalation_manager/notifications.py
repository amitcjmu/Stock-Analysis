"""
Notification and alert systems for escalation progress tracking and error handling.
"""

from datetime import datetime
from typing import Dict, Any, Optional

from .base import logger
from .exceptions import ProgressTrackingError, EscalationNotFoundError


class EscalationNotificationManager:
    """
    Manages progress tracking, status updates, and error notifications for escalations.
    """

    def __init__(self, active_escalations: Dict[str, Dict[str, Any]]):
        """Initialize with reference to active escalations."""
        self.active_escalations = active_escalations

    async def update_escalation_progress(
        self, escalation_id: str, progress: int, phase: str, description: str
    ) -> None:
        """Update escalation progress and status."""
        if escalation_id not in self.active_escalations:
            raise EscalationNotFoundError(f"Escalation {escalation_id} not found")

        try:
            escalation = self.active_escalations[escalation_id]
            escalation["progress"] = progress
            escalation["current_phase"] = phase
            escalation["phase_description"] = description
            escalation["updated_at"] = datetime.utcnow().isoformat()

            if progress > 0 and escalation["status"] == "initializing":
                escalation["status"] = (
                    "thinking"
                    if escalation.get("escalation_type") == "think"
                    else "pondering"
                )

            logger.debug(f"Updated escalation {escalation_id}: {progress}% - {phase}")

        except Exception as e:
            logger.error(
                f"Failed to update escalation progress for {escalation_id}: {e}"
            )
            raise ProgressTrackingError(
                f"Failed to update progress for escalation {escalation_id}",
                escalation_id=escalation_id,
            )

    async def handle_escalation_error(
        self,
        escalation_id: str,
        error_message: str,
        error_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Handle escalation errors and update status."""
        if escalation_id not in self.active_escalations:
            logger.warning(
                f"Attempted to handle error for non-existent escalation {escalation_id}"
            )
            return

        try:
            escalation = self.active_escalations[escalation_id]
            escalation["status"] = "failed"
            escalation["error"] = error_message
            escalation["error_context"] = error_context or {}
            escalation["failed_at"] = datetime.utcnow().isoformat()
            escalation["updated_at"] = datetime.utcnow().isoformat()

            # Add error to crew activity log
            escalation.setdefault("crew_activity", []).append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "activity": f"Escalation failed: {error_message}",
                    "phase": "error_handling",
                    "error": True,
                    "error_context": error_context or {},
                }
            )

            logger.error(f"Escalation {escalation_id} failed: {error_message}")

        except Exception as e:
            logger.error(f"Failed to handle escalation error for {escalation_id}: {e}")

    def log_crew_activity(
        self,
        escalation_id: str,
        activity: str,
        phase: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log crew activity for an escalation."""
        if escalation_id not in self.active_escalations:
            logger.warning(
                f"Attempted to log activity for non-existent escalation {escalation_id}"
            )
            return

        try:
            escalation = self.active_escalations[escalation_id]
            activity_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "activity": activity,
                "phase": phase,
            }

            if additional_data:
                activity_entry.update(additional_data)

            escalation.setdefault("crew_activity", []).append(activity_entry)

            logger.debug(f"Logged activity for {escalation_id}: {activity}")

        except Exception as e:
            logger.error(f"Failed to log crew activity for {escalation_id}: {e}")

    def update_crew_collaboration_details(
        self, escalation_id: str, collaboration_details: Dict[str, Any]
    ) -> None:
        """Update collaboration details for an escalation."""
        if escalation_id not in self.active_escalations:
            logger.warning(
                f"Attempted to update collaboration details for non-existent escalation {escalation_id}"
            )
            return

        try:
            escalation = self.active_escalations[escalation_id]
            if "collaboration_details" not in escalation:
                escalation["collaboration_details"] = {}

            escalation["collaboration_details"].update(collaboration_details)
            escalation["updated_at"] = datetime.utcnow().isoformat()

            logger.debug(f"Updated collaboration details for {escalation_id}")

        except Exception as e:
            logger.error(
                f"Failed to update collaboration details for {escalation_id}: {e}"
            )

    def add_preliminary_insights(self, escalation_id: str, insights: list) -> None:
        """Add preliminary insights to an escalation."""
        if escalation_id not in self.active_escalations:
            logger.warning(
                f"Attempted to add insights for non-existent escalation {escalation_id}"
            )
            return

        try:
            escalation = self.active_escalations[escalation_id]
            if "preliminary_insights" not in escalation:
                escalation["preliminary_insights"] = []

            escalation["preliminary_insights"].extend(insights)
            escalation["updated_at"] = datetime.utcnow().isoformat()

            logger.debug(
                f"Added {len(insights)} insights to escalation {escalation_id}"
            )

        except Exception as e:
            logger.error(f"Failed to add insights for {escalation_id}: {e}")

    def complete_escalation(self, escalation_id: str, results: Dict[str, Any]) -> None:
        """Mark an escalation as completed with results."""
        if escalation_id not in self.active_escalations:
            logger.warning(
                f"Attempted to complete non-existent escalation {escalation_id}"
            )
            return

        try:
            escalation = self.active_escalations[escalation_id]
            escalation["status"] = "completed"
            escalation["progress"] = 100
            escalation["current_phase"] = "completed"
            escalation["results"] = results
            escalation["completed_at"] = datetime.utcnow().isoformat()
            escalation["updated_at"] = datetime.utcnow().isoformat()

            # Add completion activity
            self.log_crew_activity(
                escalation_id,
                "Escalation completed successfully",
                "completed",
                {"results_available": True, "result_keys": list(results.keys())},
            )

            logger.info(f"✅ Escalation {escalation_id} completed successfully")

        except Exception as e:
            logger.error(f"Failed to complete escalation {escalation_id}: {e}")
            # Handle error synchronously since this is not an async method
            if escalation_id in self.active_escalations:
                escalation = self.active_escalations[escalation_id]
                escalation["status"] = "failed"
                escalation["error"] = f"Failed to complete escalation: {e}"
                escalation["failed_at"] = datetime.utcnow().isoformat()
                escalation["updated_at"] = datetime.utcnow().isoformat()

    def get_escalation_status_summary(
        self, escalation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a summary of escalation status for monitoring."""
        if escalation_id not in self.active_escalations:
            return None

        escalation = self.active_escalations[escalation_id]

        return {
            "escalation_id": escalation_id,
            "status": escalation.get("status"),
            "progress": escalation.get("progress", 0),
            "current_phase": escalation.get("current_phase"),
            "phase_description": escalation.get("phase_description"),
            "escalation_type": escalation.get("escalation_type"),
            "started_at": escalation.get("started_at"),
            "updated_at": escalation.get("updated_at"),
            "estimated_completion": escalation.get("estimated_completion"),
            "activity_count": len(escalation.get("crew_activity", [])),
            "insights_count": len(escalation.get("preliminary_insights", [])),
            "has_error": "error" in escalation,
        }


# Export for use in other modules
__all__ = ["EscalationNotificationManager"]
