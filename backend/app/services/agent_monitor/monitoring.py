"""
Real-time monitoring and status reporting for Agent Monitoring Service.
Handles monitoring loop, status reports, and console output.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict

from .base import TaskExecution, TaskStatus

logger = logging.getLogger(__name__)


class MonitoringMixin:
    """Mixin for monitoring and status reporting operations."""

    def start_monitoring(self):
        """Start the real-time monitoring thread."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop, daemon=True
            )
            self.monitor_thread.start()
            logger.info("Agent monitoring started")

    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

        # Stop database writer thread
        self._stop_db_writer()
        logger.info("Agent monitoring stopped")

    def get_status_report(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        with self._lock:
            hanging_tasks = [
                task for task in self.active_tasks.values() if task.is_hanging
            ]

            return {
                "monitoring_active": self.monitoring_active,
                "active_tasks": len(self.active_tasks),
                "completed_tasks": len(self.completed_tasks),
                "hanging_tasks": len(hanging_tasks),
                "active_task_details": [
                    {
                        "task_id": task.task_id,
                        "agent": task.agent_name,
                        "status": task.status.value,
                        "elapsed": f"{task.elapsed_time:.1f}s",
                        "since_activity": f"{task.time_since_activity:.1f}s",
                        "description": task.description,
                        "is_hanging": task.is_hanging,
                        "hanging_reason": task.hanging_reason,
                        "llm_calls": len(task.llm_calls),
                        "thinking_phases": len(task.thinking_phases),
                    }
                    for task in self.active_tasks.values()
                ],
                "hanging_task_details": [
                    {
                        "task_id": task.task_id,
                        "agent": task.agent_name,
                        "elapsed": f"{task.elapsed_time:.1f}s",
                        "since_activity": f"{task.time_since_activity:.1f}s",
                        "description": task.description,
                        "hanging_reason": task.hanging_reason,
                        "llm_calls": len(task.llm_calls),
                        "last_llm_call": (
                            task.llm_calls[-1].action if task.llm_calls else "None"
                        ),
                        "thinking_phases": len(task.thinking_phases),
                        "last_thinking": (
                            task.thinking_phases[-1]["description"]
                            if task.thinking_phases
                            else "None"
                        ),
                    }
                    for task in hanging_tasks
                ],
            }

    def _print_status_update(self, task: TaskExecution, action: str):
        """Print a formatted status update."""
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        elapsed = f"{task.elapsed_time:.1f}s" if task.start_time else "0.0s"

        print(
            f"[{timestamp}] 🤖 {task.agent_name} | {action} | {elapsed} | {task.description}"
        )

        # Print warning for long-running tasks
        if task.elapsed_time > 15:
            print(f"⚠️  Task running for {elapsed} - {task.hanging_reason}")

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                with self._lock:
                    datetime.utcnow()

                    # Check for hanging tasks
                    for task in self.active_tasks.values():
                        if task.is_hanging and task.status != TaskStatus.TIMEOUT:
                            task.status = TaskStatus.TIMEOUT
                            print(
                                f"🚨 HANGING DETECTED: {task.agent_name} task {task.task_id}"
                            )
                            print(f"   Reason: {task.hanging_reason}")
                            print(f"   Description: {task.description}")
                            print(f"   LLM calls made: {len(task.llm_calls)}")
                            print(f"   Thinking phases: {len(task.thinking_phases)}")

                            if task.llm_calls:
                                last_call = task.llm_calls[-1]
                                print(
                                    f"   Last LLM call: {last_call.action} ({last_call.status})"
                                )

                            if task.thinking_phases:
                                last_thinking = task.thinking_phases[-1]
                                print(
                                    f"   Last thinking: {last_thinking['description']}"
                                )

                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)

    def print_summary(self):
        """Print a summary of all task executions."""
        print("\n" + "=" * 80)
        print("AGENT MONITORING SUMMARY")
        print("=" * 80)

        with self._lock:
            if self.active_tasks:
                print(f"\n🔄 ACTIVE TASKS ({len(self.active_tasks)}):")
                for task in self.active_tasks.values():
                    status_icon = "🚨" if task.is_hanging else "⏳"
                    print(f"  {status_icon} {task.agent_name}: {task.description}")
                    print(
                        f"     Status: {task.status.value} | Elapsed: {task.elapsed_time:.1f}s | "
                        f"Since Activity: {task.time_since_activity:.1f}s"
                    )
                    if task.is_hanging:
                        print(f"     🚨 HANGING: {task.hanging_reason}")
                    print(
                        f"     LLM Calls: {len(task.llm_calls)} | Thinking Phases: {len(task.thinking_phases)}"
                    )

            if self.completed_tasks:
                print(f"\n✅ COMPLETED TASKS ({len(self.completed_tasks)}):")
                for task in self.completed_tasks[-5:]:  # Show last 5
                    status_icon = "✅" if task.status == TaskStatus.COMPLETED else "❌"
                    print(
                        f"  {status_icon} {task.agent_name}: {task.description} "
                        f"({task.duration:.1f}s)"
                    )

        print("=" * 80)
