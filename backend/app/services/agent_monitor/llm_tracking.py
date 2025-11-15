"""
LLM call tracking for Agent Monitoring Service.
Tracks LLM interactions including timing, token counts, and errors.
"""

from datetime import datetime
from typing import Dict, Optional

from .base import LLMCall, TaskExecution, TaskStatus


class LLMTrackingMixin:
    """Mixin for LLM call tracking operations."""

    def start_llm_call(self, task_id: str, action: str, prompt_length: int = 0) -> str:
        """Start tracking an LLM call."""
        call_id = f"{task_id}_call_{len(self.active_tasks.get(task_id, TaskExecution('', '', '')).llm_calls)}"

        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.WAITING_LLM
                task.last_activity = datetime.utcnow()

                llm_call = LLMCall(
                    timestamp=datetime.utcnow(),
                    action=action,
                    prompt_length=prompt_length,
                    status="pending",
                )
                task.llm_calls.append(llm_call)

                self._print_status_update(
                    task, f"LLM CALL: {action} (prompt: {prompt_length} chars)"
                )

        return call_id

    def complete_llm_call(
        self, task_id: str, response_length: int = 0, error: Optional[str] = None
    ):
        """Complete tracking an LLM call."""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.last_activity = datetime.utcnow()

                if task.llm_calls:
                    last_call = task.llm_calls[-1]
                    last_call.duration = (
                        datetime.utcnow() - last_call.timestamp
                    ).total_seconds()
                    last_call.response_length = response_length
                    last_call.status = "failed" if error else "completed"
                    last_call.error = error

                    if error:
                        task.status = TaskStatus.FAILED
                        self._print_status_update(task, f"LLM CALL FAILED: {error}")
                    else:
                        task.status = TaskStatus.PROCESSING_RESPONSE
                        self._print_status_update(
                            task,
                            f"LLM RESPONSE: {response_length} chars in {last_call.duration:.1f}s",
                        )

    def add_llm_call(self, task_id: str, llm_call_info: Dict):
        """Record an LLM call for a task (legacy method for compatibility)."""
        action = llm_call_info.get("action", "unknown")
        prompt_length = len(str(llm_call_info.get("prompt", "")))
        self.start_llm_call(task_id, action, prompt_length)
