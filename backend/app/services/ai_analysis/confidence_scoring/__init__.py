"""
Confidence Scoring Algorithms - B2.3
ADCS AI Analysis & Intelligence Service

This service implements sophisticated confidence scoring algorithms that assess
the reliability and completeness of collected data for 6R migration recommendations.

The service is modularized into:
- models: Core data structures and enums
- config: Configuration and initialization settings
- factors: Individual confidence factor calculations
- strategies: Strategy-specific confidence assessments
- core: Main ConfidenceScorer orchestration
- utils: Utility functions and convenience methods

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

from .core import ConfidenceScorer
from .models import (
    ConfidenceAssessment,
    ConfidenceFactor,
    ConfidenceFactorType,
    SixRStrategy,
)
from .utils import calculate_collection_confidence

# Public API - maintain backward compatibility
__all__ = [
    "ConfidenceScorer",
    "ConfidenceAssessment",
    "ConfidenceFactor",
    "ConfidenceFactorType",
    "SixRStrategy",
    "calculate_collection_confidence",
]
