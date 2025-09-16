"""
Base classes, types, and exceptions for Workflow Orchestration
Team C1 - Task C1.2

Contains core data structures, enums, and base classes used throughout
the workflow orchestration system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..collection_phase_engine import AutomationTier


class WorkflowStatus(Enum):
    """Status of workflow execution"""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowPriority(Enum):
    """Priority levels for workflow execution"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WorkflowConfiguration:
    """Configuration for workflow execution"""

    automation_tier: AutomationTier
    priority: WorkflowPriority
    timeout_minutes: int
    quality_thresholds: Dict[str, float]
    retry_config: Dict[str, Any]
    scheduling_config: Dict[str, Any]
    notification_config: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class WorkflowExecution:
    """Tracking information for workflow execution"""

    workflow_id: str
    flow_id: str
    flow_type: str
    status: WorkflowStatus
    configuration: WorkflowConfiguration
    scheduled_time: Optional[datetime]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    execution_time_ms: Optional[int]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    retry_count: int
    dependencies: List[str]
    metadata: Dict[str, Any]
