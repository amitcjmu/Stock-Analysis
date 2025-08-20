"""
Collection Time Utilities
Time-related helper functions for collection flows including timezone handling,
duration calculations, and completion time estimates.
"""

from datetime import datetime, timezone, timedelta


def ensure_timezone_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware, assuming UTC if naive.

    Args:
        dt: Datetime object that may or may not be timezone-aware

    Returns:
        Timezone-aware datetime object
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def calculate_time_since_creation(created_at: datetime) -> timedelta:
    """Calculate time elapsed since creation with proper timezone handling.

    Args:
        created_at: Creation timestamp

    Returns:
        Timedelta representing elapsed time
    """
    now = datetime.now(timezone.utc)
    created_at_aware = ensure_timezone_aware(created_at)
    return now - created_at_aware


def estimate_completion_time(phase: str, application_count: int = 1) -> int:
    """Estimate completion time for a phase based on complexity.

    Args:
        phase: Phase name
        application_count: Number of applications being processed

    Returns:
        Estimated completion time in minutes
    """
    # Base time estimates per phase (in minutes)
    base_estimates = {
        "initialization": 2,
        "platform_detection": 5,
        "automated_collection": 15,
        "gap_analysis": 10,
        "manual_collection": 30,
        "finalization": 5,
    }

    base_time = base_estimates.get(phase, 10)  # Default 10 minutes

    # Scale based on application count (non-linear scaling)
    if application_count <= 1:
        scaling_factor = 1.0
    elif application_count <= 5:
        scaling_factor = 1.5
    elif application_count <= 10:
        scaling_factor = 2.0
    else:
        scaling_factor = 2.5

    return int(base_time * scaling_factor)
