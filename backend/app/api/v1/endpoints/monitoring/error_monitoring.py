"""
Error monitoring endpoints.

Provides monitoring for background tasks and error tracking including active tasks,
failed tasks, and error summaries.
"""

import os
from datetime import datetime
from typing import Any, Dict

from app.core.logging import get_logger as enhanced_get_logger
from app.middleware.error_tracking import background_task_tracker
from app.services.agent_monitor import agent_monitor
from fastapi import APIRouter, Depends, HTTPException, Query

from .base import get_monitoring_context

logger = enhanced_get_logger(__name__)

router = APIRouter()


@router.get("/errors/background-tasks/active")
async def get_active_background_tasks(
    context=Depends(get_monitoring_context),
) -> Dict[str, Any]:
    """
    Get all active background tasks

    Returns:
        Active background tasks with their status
    """
    try:
        active_tasks = background_task_tracker.get_active_tasks()

        logger.info(
            f"Retrieved {len(active_tasks)} active background tasks",
            extra={
                "user_id": context.user_id if context else None,
                "task_count": len(active_tasks),
            },
        )

        return {
            "status": "success",
            "task_count": len(active_tasks),
            "tasks": list(active_tasks.values()),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(
            f"Failed to retrieve active tasks: {str(e)}",
            extra={"user_id": context.user_id if context else None},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve active background tasks"
        )


@router.get("/errors/background-tasks/failed")
async def get_failed_background_tasks(
    limit: int = Query(default=100, ge=1, le=1000),
    context=Depends(get_monitoring_context),
) -> Dict[str, Any]:
    """
    Get recent failed background tasks

    Args:
        limit: Maximum number of failed tasks to return (1-1000)

    Returns:
        Failed background tasks with error details
    """
    try:
        failed_tasks = background_task_tracker.get_failed_tasks(limit=limit)

        logger.info(
            f"Retrieved {len(failed_tasks)} failed background tasks",
            extra={
                "user_id": context.user_id if context else None,
                "task_count": len(failed_tasks),
                "limit": limit,
            },
        )

        return {
            "status": "success",
            "task_count": len(failed_tasks),
            "tasks": list(failed_tasks.values()),
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(
            f"Failed to retrieve failed tasks: {str(e)}",
            extra={"user_id": context.user_id if context else None},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve failed background tasks"
        )


@router.get("/errors/background-tasks/{task_id}")
async def get_background_task_status(
    task_id: str, context=Depends(get_monitoring_context)
) -> Dict[str, Any]:
    """
    Get status of a specific background task

    Args:
        task_id: ID of the task to check

    Returns:
        Task status and details
    """
    try:
        task_status = background_task_tracker.get_task_status(task_id)

        if not task_status:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        logger.info(
            f"Retrieved status for task {task_id}",
            extra={
                "user_id": context.user_id if context else None,
                "task_id": task_id,
                "task_status": task_status.get("status"),
            },
        )

        return {
            "status": "success",
            "task": task_status,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve task status: {str(e)}",
            extra={"user_id": context.user_id if context else None, "task_id": task_id},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve task status")


@router.get("/errors/summary")
async def get_error_summary(
    hours: int = Query(default=24, ge=1, le=168),
    context=Depends(get_monitoring_context),
) -> Dict[str, Any]:
    """
    Get error summary for the specified time period

    Args:
        hours: Number of hours to look back (1-168)

    Returns:
        Error summary with counts by type and severity
    """
    try:
        # Get failed task summary from background tracker
        failed_tasks = background_task_tracker.get_failed_tasks(limit=1000)

        # Group by error type
        error_types = {}
        for task in failed_tasks.values():
            error_type = task.get("error_type", "Unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # Get monitoring status for additional error insights
        status_report = agent_monitor.get_status_report()
        hanging_tasks = status_report.get("hanging_tasks", 0)

        logger.info(
            f"Generated error summary for last {hours} hours",
            extra={
                "user_id": context.user_id if context else None,
                "hours": hours,
                "total_errors": len(failed_tasks),
            },
        )

        return {
            "status": "success",
            "time_period_hours": hours,
            "total_errors": len(failed_tasks),
            "hanging_tasks": hanging_tasks,
            "error_types": error_types,
            "recent_errors": list(failed_tasks.values())[:10],  # Last 10 errors
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(
            f"Failed to generate error summary: {str(e)}",
            extra={"user_id": context.user_id if context else None},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to generate error summary")


@router.post("/errors/test/{error_type}")
async def trigger_test_error(
    error_type: str, context=Depends(get_monitoring_context)
) -> Dict[str, Any]:
    """
    Trigger a test error for testing error handling (non-production only)

    Args:
        error_type: Type of error to trigger

    Returns:
        Never returns - always raises an error
    """
    # Only allow in development/testing
    if os.getenv("ENVIRONMENT", "production") == "production":
        raise HTTPException(
            status_code=403, detail="Test errors are disabled in production"
        )

    logger.warning(
        f"Test error triggered: {error_type}",
        extra={
            "user_id": context.user_id if context else None,
            "error_type": error_type,
        },
    )

    # Trigger different error types
    if error_type == "validation":
        from app.core.exceptions import ValidationError

        raise ValidationError(
            "Test validation error", field="test_field", value="invalid"
        )
    elif error_type == "auth":
        from app.core.exceptions import AuthenticationError

        raise AuthenticationError("Test authentication error")
    elif error_type == "flow":
        from app.core.exceptions import FlowNotFoundError

        raise FlowNotFoundError("test-flow-123")
    elif error_type == "timeout":
        from app.core.exceptions import NetworkTimeoutError

        raise NetworkTimeoutError("test-operation", timeout_seconds=30)
    elif error_type == "background":
        from app.core.exceptions import BackgroundTaskError

        raise BackgroundTaskError("test-task", task_id="test-123")
    elif error_type == "crewai":
        from app.core.exceptions import CrewAIExecutionError

        raise CrewAIExecutionError(
            "Test CrewAI execution failed", crew_name="test-crew", phase="test-phase"
        )
    else:
        raise ValueError(f"Unknown test error type: {error_type}")
