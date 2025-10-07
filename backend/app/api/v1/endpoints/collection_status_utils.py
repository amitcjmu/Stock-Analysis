"""
Collection Status Utilities
Status and phase management utilities for collection flows including
status determination, progress calculations, and flow state validation.
"""

from datetime import timedelta

from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
)
from app.api.v1.endpoints.collection_time_utils import calculate_time_since_creation


def is_flow_stuck_in_initialization(
    flow: CollectionFlow, timeout_minutes: int = 5
) -> bool:
    """Check if a flow is stuck in INITIALIZED state beyond timeout.

    Args:
        flow: Collection flow to check
        timeout_minutes: Timeout in minutes (default 5)

    Returns:
        True if flow is stuck, False otherwise
    """
    if flow.status != CollectionFlowStatus.INITIALIZED.value:
        return False

    time_since_creation = calculate_time_since_creation(flow.created_at)
    return time_since_creation > timedelta(minutes=timeout_minutes)


def determine_next_phase_status(next_phase: str, current_status: str = None) -> str:
    """Determine the appropriate flow status based on next phase.

    Per ADR-012: Status reflects lifecycle, not phase.

    Args:
        next_phase: The next phase name
        current_status: Current flow status

    Returns:
        Appropriate collection flow status
    """
    # If already running, stay running unless at finalization
    if next_phase == "finalization":
        return CollectionFlowStatus.COMPLETED.value

    # If initialized and moving to first active phase
    if current_status == CollectionFlowStatus.INITIALIZED.value:
        # Check if phase requires user input
        if next_phase in ["asset_selection"]:
            return CollectionFlowStatus.PAUSED.value
        return CollectionFlowStatus.RUNNING.value

    # Otherwise preserve current status (RUNNING/PAUSED)
    return current_status or CollectionFlowStatus.RUNNING.value


def calculate_progress_percentage(
    milestones_completed: int, total_milestones: int
) -> float:
    """Calculate progress percentage from completed milestones.

    Args:
        milestones_completed: Number of completed milestones
        total_milestones: Total number of milestones

    Returns:
        Progress percentage (0.0 to 100.0)
    """
    if total_milestones <= 0:
        return 0.0

    percentage = (milestones_completed / total_milestones) * 100
    return min(100.0, max(0.0, percentage))  # Clamp between 0 and 100
