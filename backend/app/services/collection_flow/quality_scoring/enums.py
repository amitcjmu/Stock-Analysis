"""
Quality Scoring Enumerations

This module contains enumerations used for quality scoring and confidence assessment.
"""

from enum import Enum


class QualityDimension(str, Enum):
    """Dimensions of data quality assessment"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"


class ConfidenceLevel(str, Enum):
    """Confidence levels for assessments"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"