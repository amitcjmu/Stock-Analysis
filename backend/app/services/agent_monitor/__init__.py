"""
Agent Monitoring Service for CrewAI agents.
Provides real-time observability into agent task execution with database persistence.

This module is modularized for maintainability:
- base.py: Core data structures (TaskStatus, LLMCall, TaskExecution)
- lifecycle.py: Task lifecycle management
- llm_tracking.py: LLM call tracking
- monitoring.py: Real-time monitoring and reporting
- persistence.py: Database operations and async writes

Enhanced for Agent Observability Enhancement Phase 2.
"""

import threading
from typing import Any, Dict, List, Tuple

from .base import LLMCall, TaskExecution, TaskStatus
from .lifecycle import TaskLifecycleMixin
from .llm_tracking import LLMTrackingMixin
from .monitoring import MonitoringMixin
from .persistence import PersistenceMixin


class AgentMonitor(
    TaskLifecycleMixin,
    LLMTrackingMixin,
    MonitoringMixin,
    PersistenceMixin,
):
    """
    Real-time monitoring for CrewAI agent task execution with database persistence.

    Combines functionality from multiple mixins:
    - TaskLifecycleMixin: start_task, complete_task, fail_task, update_task_status
    - LLMTrackingMixin: start_llm_call, complete_llm_call, add_llm_call
    - MonitoringMixin: start_monitoring, stop_monitoring, get_status_report, print_summary
    - PersistenceMixin: start_task_with_context, complete_task_with_metrics, discover_pattern
    """

    def __init__(self):
        self.active_tasks: Dict[str, TaskExecution] = {}
        self.completed_tasks: List[TaskExecution] = []
        self.monitoring_active = False
        self.monitor_thread = None
        self._lock = threading.Lock()
        self._db_write_queue: List[Tuple[str, Dict[str, Any]]] = []
        self._db_write_thread = None
        self._db_write_active = False

        # Start background database writer thread
        self._start_db_writer()


# Global monitor instance
agent_monitor = AgentMonitor()

# Backward compatibility exports
__all__ = [
    "AgentMonitor",
    "agent_monitor",
    "TaskStatus",
    "TaskExecution",
    "LLMCall",
]
