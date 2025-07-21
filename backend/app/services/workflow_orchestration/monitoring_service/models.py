"""
Monitoring Service Data Models
Team C1 - Task C1.6

Data models and dataclasses used throughout the workflow monitoring system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from .types import MetricType, AlertSeverity, MonitoringLevel


@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: datetime
    metric_name: str
    metric_type: MetricType
    value: Union[int, float, str, bool]
    unit: Optional[str]
    tags: Dict[str, str]
    context: Dict[str, Any]


@dataclass
class ProgressMilestone:
    """Progress milestone definition"""
    milestone_id: str
    name: str
    description: str
    phase: Optional[str]
    completion_criteria: Dict[str, Any]
    weight: float  # Contribution to overall progress
    dependencies: List[str]
    estimated_duration_ms: Optional[int]
    metadata: Dict[str, Any]


@dataclass
class WorkflowProgress:
    """Comprehensive workflow progress tracking"""
    workflow_id: str
    overall_progress: float  # 0.0 to 1.0
    phase_progress: Dict[str, float]
    completed_milestones: List[str]
    current_milestone: Optional[str]
    estimated_completion: Optional[datetime]
    time_remaining_ms: Optional[int]
    velocity_metrics: Dict[str, float]
    bottlenecks: List[Dict[str, Any]]
    quality_gates_status: Dict[str, str]
    last_updated: datetime


@dataclass
class PerformanceMetrics:
    """Performance metrics for workflows"""
    workflow_id: str
    execution_time_ms: Optional[int]
    throughput: float  # Items processed per minute
    resource_utilization: Dict[str, float]
    queue_metrics: Dict[str, Any]
    error_rate: float
    success_rate: float
    quality_scores: Dict[str, float]
    efficiency_score: float
    sla_compliance: Dict[str, bool]


@dataclass
class AlertDefinition:
    """Alert rule definition"""
    alert_id: str
    name: str
    description: str
    severity: AlertSeverity
    condition: str  # Alert condition expression
    threshold: Union[int, float]
    evaluation_window_ms: int
    cooldown_ms: int
    enabled: bool
    notification_channels: List[str]
    metadata: Dict[str, Any]


@dataclass
class Alert:
    """Active alert instance"""
    alert_id: str
    alert_definition_id: str
    workflow_id: Optional[str]
    severity: AlertSeverity
    title: str
    message: str
    triggered_at: datetime
    resolved_at: Optional[datetime]
    current_value: Union[int, float, str]
    threshold_value: Union[int, float]
    context: Dict[str, Any]
    acknowledgments: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class MonitoringSession:
    """Monitoring session for a workflow"""
    session_id: str
    workflow_id: str
    monitoring_level: MonitoringLevel
    start_time: datetime
    end_time: Optional[datetime]
    metrics_collected: int
    alerts_triggered: int
    health_checks_performed: int
    configuration: Dict[str, Any]
    metadata: Dict[str, Any]