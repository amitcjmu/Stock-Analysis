"""
Learning Optimizer Models
Contains data models for learning events, optimization recommendations, and insights.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .enums import LearningPattern, OptimizationStrategy


@dataclass
class LearningEvent:
    """Individual learning event for pattern analysis"""

    event_id: str
    event_type: LearningPattern
    timestamp: datetime
    collection_flow_id: str
    questionnaire_id: str
    stakeholder_role: str
    business_context: Dict[str, Any]
    event_data: Dict[str, Any]
    success_metrics: Dict[str, float]
    feedback_data: Optional[Dict[str, Any]] = None


@dataclass
class OptimizationRecommendation:
    """Optimization recommendation based on learning patterns"""

    strategy: OptimizationStrategy
    confidence: float  # 0.0 to 1.0
    expected_improvement: float  # percentage improvement expected
    implementation_complexity: str  # low, medium, high
    evidence: Dict[str, Any]
    specific_actions: List[str]
    success_metrics: List[str]


@dataclass
class LearningInsight:
    """Insight derived from learning pattern analysis"""

    insight_id: str
    pattern_type: LearningPattern
    description: str
    supporting_evidence: Dict[str, Any]
    business_impact: str  # low, medium, high
    actionability: str  # immediate, short_term, long_term
    recommendations: List[OptimizationRecommendation]
