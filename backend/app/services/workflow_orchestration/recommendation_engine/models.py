"""
Recommendation Engine Data Models
Team C1 - Task C1.5

Data models and structures for the smart workflow recommendation system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from .enums import RecommendationConfidence, RecommendationSource, RecommendationType


@dataclass
class RecommendationInsight:
    """Individual insight supporting a recommendation"""

    insight_type: str
    description: str
    confidence: float
    supporting_data: Dict[str, Any]
    weight: float
    source: RecommendationSource


@dataclass
class WorkflowRecommendation:
    """Individual workflow recommendation"""

    recommendation_id: str
    recommendation_type: RecommendationType
    title: str
    description: str
    recommended_action: Dict[str, Any]
    confidence: RecommendationConfidence
    confidence_score: float
    expected_impact: Dict[str, Any]
    implementation_effort: str  # low, medium, high
    priority: int  # 1-10 scale
    supporting_insights: List[RecommendationInsight]
    cost_benefit_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    alternatives: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class RecommendationPackage:
    """Complete package of recommendations for a workflow"""

    package_id: str
    target_environment: Dict[str, Any]
    target_requirements: Dict[str, Any]
    analysis_timestamp: datetime
    recommendations: List[WorkflowRecommendation]
    overall_confidence: float
    recommended_execution_order: List[str]
    estimated_improvement: Dict[str, Any]
    adaptation_notes: List[str]
    metadata: Dict[str, Any]


@dataclass
class LearningPattern:
    """Pattern identified from historical executions"""

    pattern_id: str
    pattern_type: str
    description: str
    conditions: Dict[str, Any]
    outcomes: Dict[str, Any]
    confidence: float
    occurrence_count: int
    success_rate: float
    average_improvement: Dict[str, Any]
    applicable_scenarios: List[str]
