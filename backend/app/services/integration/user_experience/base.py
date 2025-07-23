"""
User Experience Base Types and Classes

Core types and data structures for UX optimization.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
from uuid import UUID


class UXOptimizationArea(Enum):
    """Areas of user experience optimization"""

    WORKFLOW_NAVIGATION = "workflow_navigation"
    PROGRESS_TRACKING = "progress_tracking"
    ERROR_COMMUNICATION = "error_communication"
    DATA_VISUALIZATION = "data_visualization"
    AUTOMATION_TRANSPARENCY = "automation_transparency"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


class UXMetricType(Enum):
    """Types of UX metrics"""

    TIME_TO_COMPLETION = "time_to_completion"
    USER_SATISFACTION = "user_satisfaction"
    ERROR_RATE = "error_rate"
    ABANDONMENT_RATE = "abandonment_rate"
    TASK_SUCCESS_RATE = "task_success_rate"
    COGNITIVE_LOAD = "cognitive_load"


@dataclass
class UXRecommendation:
    """User experience improvement recommendation"""

    id: str
    area: UXOptimizationArea
    title: str
    description: str
    impact: str  # high, medium, low
    effort: str  # high, medium, low
    priority_score: float
    implementation_guidance: List[str]
    expected_improvement: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserJourneyAnalytics:
    """Analytics for user journey through ADCS workflow"""

    engagement_id: UUID
    user_id: UUID
    journey_start: datetime
    current_phase: str
    phases_completed: List[str]
    time_per_phase: Dict[str, float]
    errors_encountered: int
    manual_interventions: int
    automation_efficiency: float
    user_actions: List[Dict[str, Any]]
    satisfaction_indicators: Dict[str, float]


@dataclass
class OptimizationContext:
    """Context for UX optimization"""

    engagement_id: UUID
    user_id: UUID
    flows_data: Dict[str, Any]
    user_behavior: Dict[str, Any]
    performance_metrics: Dict[str, float]
    historical_data: Dict[str, Any]
