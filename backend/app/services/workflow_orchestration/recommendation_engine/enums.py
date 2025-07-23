"""
Recommendation Engine Enums
Team C1 - Task C1.5

Enum definitions for the smart workflow recommendation system.
"""

from enum import Enum


class RecommendationType(Enum):
    """Types of recommendations"""

    AUTOMATION_TIER = "automation_tier"
    WORKFLOW_CONFIG = "workflow_config"
    PHASE_OPTIMIZATION = "phase_optimization"
    QUALITY_IMPROVEMENT = "quality_improvement"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    COST_OPTIMIZATION = "cost_optimization"
    RISK_MITIGATION = "risk_mitigation"


class RecommendationConfidence(Enum):
    """Confidence levels for recommendations"""

    LOW = "low"  # 0.0 - 0.4
    MEDIUM = "medium"  # 0.4 - 0.7
    HIGH = "high"  # 0.7 - 0.9
    VERY_HIGH = "very_high"  # 0.9 - 1.0


class RecommendationSource(Enum):
    """Sources of recommendation insights"""

    HISTORICAL_ANALYSIS = "historical_analysis"
    PATTERN_RECOGNITION = "pattern_recognition"
    MACHINE_LEARNING = "machine_learning"
    BUSINESS_RULES = "business_rules"
    ENVIRONMENT_ANALYSIS = "environment_analysis"
    EXPERT_KNOWLEDGE = "expert_knowledge"
