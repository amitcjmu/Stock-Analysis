"""
Data models and enums for confidence scoring system.

Defines the core data structures used throughout the confidence scoring algorithms.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class ConfidenceFactorType(str, Enum):
    """Types of factors that influence confidence scoring"""

    DATA_COMPLETENESS = "data_completeness"
    DATA_QUALITY = "data_quality"
    SOURCE_RELIABILITY = "source_reliability"
    VALIDATION_STATUS = "validation_status"
    BUSINESS_CONTEXT = "business_context"
    TEMPORAL_FRESHNESS = "temporal_freshness"
    CROSS_VALIDATION = "cross_validation"
    EXPERT_VALIDATION = "expert_validation"


class SixRStrategy(str, Enum):
    """5R cloud migration strategy framework"""

    # Migration Lift and Shift
    REHOST = "rehost"

    # Legacy Modernization Treatments
    REPLATFORM = "replatform"
    REFACTOR = "refactor"
    REARCHITECT = "rearchitect"

    # Cloud Native
    REPLACE = "replace"
    REWRITE = "rewrite"


@dataclass
class ConfidenceFactor:
    """Individual factor contributing to overall confidence score"""

    factor_type: ConfidenceFactorType
    weight: float  # 0.0 to 1.0
    score: float  # 0.0 to 100.0
    evidence: Dict[str, Any]
    description: str


@dataclass
class ConfidenceAssessment:
    """Complete confidence assessment for an asset or collection"""

    overall_score: float  # 0.0 to 100.0
    strategy_scores: Dict[SixRStrategy, float]
    contributing_factors: List[ConfidenceFactor]
    critical_gaps: List[str]
    recommendations: List[str]
    last_updated: datetime
    assessment_metadata: Dict[str, Any]
