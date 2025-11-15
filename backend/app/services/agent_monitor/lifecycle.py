"""
Task lifecycle management for Agent Monitoring Service.
Handles task creation, updates, completion, and state transitions.
"""

import logging
from datetime import datetime
from typing import Optional

from .base import TaskExecution, TaskStatus

logger = logging.getLogger(__name__)


class TaskLifecycleMixin:
    """Mixin for task lifecycle management operations."""

    def start_task(
        self, task_id: str, agent_name: str, description: str
    ) -> TaskExecution:
        """Register a new task execution."""
        with self._lock:
            task_exec = TaskExecution(
                task_id=task_id,
                agent_name=agent_name,
                description=(
                    description[:100] + "..." if len(description) > 100 else description
                ),
                status=TaskStatus.STARTING,
                start_time=datetime.utcnow(),
                last_activity=datetime.utcnow(),
            )
            self.active_tasks[task_id] = task_exec

        logger.info(f"🚀 Task started: {agent_name} - {task_id}")
        self._print_status_update(task_exec, "STARTED")
        return task_exec

    def update_task_status(
        self, task_id: str, status: TaskStatus, details: Optional[str] = None
    ):
        """Update task status."""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                old_status = task.status
                task.status = status
                task.last_activity = datetime.utcnow()

                if status == TaskStatus.COMPLETED or status == TaskStatus.FAILED:
                    task.end_time = datetime.utcnow()
                    task.duration = task.elapsed_time

                if details:
                    if status == TaskStatus.FAILED:
                        task.error = details
                    elif status == TaskStatus.COMPLETED:
                        task.result_preview = (
                            details[:200] + "..." if len(details) > 200 else details
                        )

                self._print_status_update(
                    task, f"{old_status.value.upper()} → {status.value.upper()}"
                )

    def record_thinking_phase(self, task_id: str, phase_description: str):
        """Record a thinking phase for detailed analysis."""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.THINKING
                task.last_activity = datetime.utcnow()

                thinking_phase = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "description": phase_description,
                    "elapsed_time": task.elapsed_time,
                }
                task.thinking_phases.append(thinking_phase)

                self._print_status_update(task, f"THINKING: {phase_description}")

    def complete_task(self, task_id: str, result: Optional[str] = None):
        """Mark task as completed."""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.COMPLETED
                task.end_time = datetime.utcnow()
                task.duration = task.elapsed_time

                if result:
                    task.result_preview = (
                        result[:200] + "..." if len(result) > 200 else result
                    )

                # Move to completed tasks
                self.completed_tasks.append(task)
                del self.active_tasks[task_id]

                self._print_status_update(task, f"COMPLETED in {task.duration:.2f}s")

    def fail_task(self, task_id: str, error: str):
        """Mark task as failed."""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.FAILED
                task.end_time = datetime.utcnow()
                task.duration = task.elapsed_time
                task.error = error

                # Move to completed tasks
                self.completed_tasks.append(task)
                del self.active_tasks[task_id]

                self._print_status_update(
                    task, f"FAILED after {task.duration:.2f}s: {error}"
                )
