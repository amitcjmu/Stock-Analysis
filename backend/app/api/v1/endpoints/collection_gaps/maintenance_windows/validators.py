"""
Validation utilities for maintenance windows API.

Provides validation functions for time ranges, UUIDs, and business logic constraints.
"""

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status


def validate_uuid(uuid_string: str, field_name: str = "ID") -> UUID:
    """
    Validate UUID format and return UUID object.

    Args:
        uuid_string: String to validate as UUID
        field_name: Name of the field for error messages

    Returns:
        UUID object if valid

    Raises:
        HTTPException: If UUID format is invalid
    """
    try:
        return UUID(uuid_string)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "invalid_uuid",
                "message": f"Invalid {field_name.lower()} format",
                "details": {field_name.lower(): uuid_string},
            },
        )


def validate_time_range(start_time: datetime, end_time: datetime) -> None:
    """
    Validate that start time is before end time.

    Args:
        start_time: Start datetime
        end_time: End datetime

    Raises:
        HTTPException: If time range is invalid
    """
    if start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "invalid_time_range",
                "message": "Start time must be before end time",
                "details": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                },
            },
        )


def check_schedule_conflicts(conflicts, operation: str = "creation") -> None:
    """
    Check for schedule conflicts and raise exception if found.

    Args:
        conflicts: List of conflicting maintenance windows
        operation: Type of operation (creation, update)

    Raises:
        HTTPException: If conflicts are found
    """
    if conflicts:
        conflict_details = [
            {
                "id": str(window.id),
                "name": window.name,
                "start_time": window.start_time.isoformat(),
                "end_time": window.end_time.isoformat(),
            }
            for window in conflicts
        ]

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "error": "schedule_conflict",
                "message": f"Found {len(conflicts)} conflicting maintenance windows",
                "details": {"conflicts": conflict_details},
            },
        )


def validate_window_exists(window, window_id: str) -> None:
    """
    Validate that maintenance window exists.

    Args:
        window: Window object from repository or None
        window_id: ID of the window for error messages

    Raises:
        HTTPException: If window doesn't exist
    """
    if not window:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "window_not_found",
                "message": "Maintenance window not found",
                "details": {"window_id": window_id},
            },
        )
