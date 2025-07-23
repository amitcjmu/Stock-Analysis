"""
Quality Scoring Data Models

This module contains data models for quality and confidence scoring results.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .enums import ConfidenceLevel, QualityDimension


@dataclass
class QualityScore:
    """Data quality score result"""

    overall_score: float
    dimension_scores: Dict[QualityDimension, float]
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfidenceScore:
    """Confidence assessment result"""

    overall_confidence: float
    confidence_level: ConfidenceLevel
    confidence_factors: Dict[str, float]
    risk_factors: List[Dict[str, Any]]
    improvement_suggestions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
