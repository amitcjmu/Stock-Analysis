"""
Utility functions for maintenance windows API.

Provides helper functions for activity status determination and data transformation.
"""

from datetime import datetime
from typing import List

from app.models.api.collection_gaps import MaintenanceWindowResponse


def is_window_active(start_time: datetime, end_time: datetime) -> bool:
    """
    Determine if a maintenance window is currently active.

    Args:
        start_time: Window start time
        end_time: Window end time

    Returns:
        True if window is currently active, False otherwise
    """
    if not start_time or not end_time:
        return False

    current_time = datetime.utcnow()
    return start_time <= current_time <= end_time


def convert_to_response(
    window, current_time: datetime = None
) -> MaintenanceWindowResponse:
    """
    Convert a maintenance window model to response format.

    Args:
        window: MaintenanceWindow model instance
        current_time: Current time for activity calculation (defaults to utcnow)

    Returns:
        MaintenanceWindowResponse object
    """
    if current_time is None:
        current_time = datetime.utcnow()

    # Determine if window is currently active
    is_active = is_window_active(window.start_time, window.end_time)

    return MaintenanceWindowResponse(
        id=str(window.id),
        name=window.name,
        start_time=window.start_time,
        end_time=window.end_time,
        scope_type=window.scope_type,
        is_active=is_active,
    )


def convert_windows_to_responses(
    windows: List, current_time: datetime = None
) -> List[MaintenanceWindowResponse]:
    """
    Convert a list of maintenance window models to response format.

    Args:
        windows: List of MaintenanceWindow model instances
        current_time: Current time for activity calculation (defaults to utcnow)

    Returns:
        List of MaintenanceWindowResponse objects
    """
    if current_time is None:
        current_time = datetime.utcnow()

    return [convert_to_response(window, current_time) for window in windows]
