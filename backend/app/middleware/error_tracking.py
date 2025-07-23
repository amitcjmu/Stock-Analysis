"""
Error Tracking Middleware

Middleware to track and handle errors in background tasks and async operations.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from app.core.exceptions import BackgroundTaskError
from app.core.logging import get_logger, set_request_context

logger = get_logger(__name__)


class BackgroundTaskTracker:
    """Tracks background tasks and their errors"""

    def __init__(self):
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._failed_tasks: Dict[str, Dict[str, Any]] = {}
        self._max_failed_tasks = 1000  # Keep last 1000 failed tasks

    def create_task(
        self, coro, task_name: str, context: Optional[Dict[str, Any]] = None
    ) -> asyncio.Task:
        """
        Create and track a background task

        Args:
            coro: Coroutine to run
            task_name: Name of the task
            context: Optional context information

        Returns:
            Created asyncio.Task
        """
        task_id = str(uuid.uuid4())

        # Create wrapper to track task
        async def task_wrapper():
            start_time = datetime.utcnow()

            # Set context for logging
            if context:
                set_request_context(**context)

            try:
                # Track active task
                self._active_tasks[task_id] = {
                    "task_id": task_id,
                    "task_name": task_name,
                    "start_time": start_time,
                    "context": context,
                }

                logger.info(
                    f"Background task started: {task_name}",
                    extra={
                        "task_id": task_id,
                        "task_name": task_name,
                        "context": context,
                    },
                )

                # Run the actual task
                result = await coro

                # Task completed successfully
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                logger.info(
                    f"Background task completed: {task_name}",
                    extra={
                        "task_id": task_id,
                        "task_name": task_name,
                        "duration_ms": duration_ms,
                        "status": "success",
                    },
                )

                return result

            except Exception as e:
                # Task failed
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Log the error
                logger.error(
                    f"Background task failed: {task_name} - {str(e)}",
                    extra={
                        "task_id": task_id,
                        "task_name": task_name,
                        "duration_ms": duration_ms,
                        "status": "failed",
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )

                # Track failed task
                self._failed_tasks[task_id] = {
                    "task_id": task_id,
                    "task_name": task_name,
                    "start_time": start_time,
                    "end_time": datetime.utcnow(),
                    "duration_ms": duration_ms,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "context": context,
                }

                # Limit failed tasks history
                if len(self._failed_tasks) > self._max_failed_tasks:
                    oldest_task = min(
                        self._failed_tasks.keys(),
                        key=lambda k: self._failed_tasks[k]["end_time"],
                    )
                    del self._failed_tasks[oldest_task]

                # Re-raise as BackgroundTaskError
                raise BackgroundTaskError(
                    task_name=task_name,
                    task_id=task_id,
                    details={
                        "original_error": type(e).__name__,
                        "duration_ms": duration_ms,
                        "context": context,
                    },
                ) from e

            finally:
                # Remove from active tasks
                self._active_tasks.pop(task_id, None)

        # Create the task
        task = asyncio.create_task(task_wrapper())
        task.task_id = task_id  # Attach task ID for reference

        return task

    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all active background tasks"""
        return self._active_tasks.copy()

    def get_failed_tasks(self, limit: int = 100) -> Dict[str, Dict[str, Any]]:
        """Get recent failed tasks"""
        # Return most recent failed tasks
        sorted_tasks = sorted(
            self._failed_tasks.items(), key=lambda x: x[1]["end_time"], reverse=True
        )
        return dict(sorted_tasks[:limit])

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        if task_id in self._active_tasks:
            return {**self._active_tasks[task_id], "status": "active"}
        elif task_id in self._failed_tasks:
            return {**self._failed_tasks[task_id], "status": "failed"}
        return None


# Global background task tracker
background_task_tracker = BackgroundTaskTracker()


def create_background_task(
    coro, task_name: str, context: Optional[Dict[str, Any]] = None
) -> asyncio.Task:
    """
    Create a tracked background task

    Args:
        coro: Coroutine to run
        task_name: Name of the task
        context: Optional context information

    Returns:
        Created asyncio.Task
    """
    return background_task_tracker.create_task(coro, task_name, context)


def track_async_errors(task_name: str):
    """
    Decorator to track errors in async functions

    Args:
        task_name: Name of the task for tracking
    """

    def decorator(func: Callable):
        # Import functools to preserve function signature for FastAPI
        import functools

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            task_id = str(uuid.uuid4())
            start_time = datetime.utcnow()

            logger.info(
                f"Async operation started: {task_name}",
                extra={
                    "task_id": task_id,
                    "task_name": task_name,
                    "function": func.__name__,
                },
            )

            try:
                result = await func(*args, **kwargs)

                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.info(
                    f"Async operation completed: {task_name}",
                    extra={
                        "task_id": task_id,
                        "task_name": task_name,
                        "duration_ms": duration_ms,
                        "status": "success",
                    },
                )

                return result

            except Exception as e:
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                logger.error(
                    f"Async operation failed: {task_name} - {str(e)}",
                    extra={
                        "task_id": task_id,
                        "task_name": task_name,
                        "duration_ms": duration_ms,
                        "status": "failed",
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )

                # Re-raise with context
                if not isinstance(e, BackgroundTaskError):
                    raise BackgroundTaskError(
                        task_name=task_name,
                        task_id=task_id,
                        details={
                            "function": func.__name__,
                            "original_error": type(e).__name__,
                            "duration_ms": duration_ms,
                        },
                    ) from e
                raise

        return wrapper

    return decorator
