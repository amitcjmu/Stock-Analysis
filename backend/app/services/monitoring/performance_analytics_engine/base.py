"""
Base types, enums, and dataclasses for Performance Analytics Engine

Contains all the core data structures used throughout the analytics engine.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class TrendDirection(str, Enum):
    """Trend direction indicators"""

    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class BottleneckType(str, Enum):
    """Types of performance bottlenecks"""

    CPU_BOUND = "cpu_bound"
    MEMORY_BOUND = "memory_bound"
    IO_BOUND = "io_bound"
    CACHE_BOUND = "cache_bound"
    AUTH_BOUND = "auth_bound"
    NETWORK_BOUND = "network_bound"
    DATABASE_BOUND = "database_bound"


class ImpactLevel(str, Enum):
    """Impact severity levels"""

    CRITICAL = "critical"  # Severe user experience impact
    HIGH = "high"  # Noticeable user impact
    MEDIUM = "medium"  # Minor user impact
    LOW = "low"  # Minimal user impact
    NONE = "none"  # No user impact


@dataclass
class PerformanceTrend:
    """Performance trend analysis result"""

    metric_name: str
    time_period_hours: int
    direction: TrendDirection
    change_percentage: float
    confidence_score: float  # 0-100
    data_points: int
    trend_details: Dict[str, Any] = field(default_factory=dict)
    predictions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceBottleneck:
    """Identified performance bottleneck"""

    id: str
    type: BottleneckType
    component: str
    metric: str
    current_value: float
    threshold: float
    impact_level: ImpactLevel
    confidence_score: float
    root_causes: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    estimated_improvement: Dict[str, float] = field(default_factory=dict)


@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation"""

    id: str
    title: str
    description: str
    priority: str  # high, medium, low
    impact_level: ImpactLevel
    estimated_improvement_percent: float
    implementation_effort: str  # low, medium, high
    cost_estimate: str  # low, medium, high
    timeline_days: int
    success_probability: float  # 0-100
    dependencies: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


@dataclass
class BusinessImpactAnalysis:
    """Business impact analysis of performance metrics"""

    metric_name: str
    performance_change_percent: float
    estimated_user_impact: Dict[str, float]
    estimated_business_impact: Dict[str, Any]
    confidence_level: float
