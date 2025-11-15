"""
Base data structures for Agent Monitoring Service.
Contains enums, dataclasses, and core types used across all monitoring modules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class TaskStatus(Enum):
    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    THINKING = "thinking"
    WAITING_LLM = "waiting_llm"
    PROCESSING_RESPONSE = "processing_response"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class LLMCall:
    timestamp: datetime
    action: str
    prompt_length: int = 0
    response_length: int = 0
    duration: Optional[float] = None
    status: str = "pending"
    error: Optional[str] = None


@dataclass
class TaskExecution:
    task_id: str
    agent_name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    llm_calls: List[LLMCall] = field(default_factory=list)
    error: Optional[str] = None
    result_preview: Optional[str] = None
    last_activity: Optional[datetime] = None
    thinking_phases: List[Dict] = field(default_factory=list)

    @property
    def elapsed_time(self) -> float:
        if self.start_time:
            end = self.end_time or datetime.utcnow()
            return (end - self.start_time).total_seconds()
        return 0.0

    @property
    def time_since_activity(self) -> float:
        """Time since last recorded activity."""
        if self.last_activity:
            return (datetime.utcnow() - self.last_activity).total_seconds()
        return self.elapsed_time

    @property
    def is_hanging(self) -> bool:
        """Check if task appears to be hanging (no activity > 30 seconds)."""
        return self.time_since_activity > 30 and self.status in [
            TaskStatus.RUNNING,
            TaskStatus.THINKING,
            TaskStatus.WAITING_LLM,
        ]

    @property
    def hanging_reason(self) -> str:
        """Determine why the task might be hanging."""
        if not self.is_hanging:
            return "Not hanging"

        if self.status == TaskStatus.THINKING:
            return f"Stuck in thinking phase for {self.time_since_activity:.1f}s"
        elif self.status == TaskStatus.WAITING_LLM:
            return f"Waiting for LLM response for {self.time_since_activity:.1f}s"
        elif len(self.llm_calls) == 0:
            return f"No LLM calls made in {self.elapsed_time:.1f}s"
        else:
            last_call = self.llm_calls[-1]
            if last_call.status == "pending":
                return f"LLM call pending for {self.time_since_activity:.1f}s"
            else:
                return f"No activity after last LLM call for {self.time_since_activity:.1f}s"
