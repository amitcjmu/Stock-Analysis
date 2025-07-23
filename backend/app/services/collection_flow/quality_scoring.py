"""
Quality Scoring and Confidence Assessment Services - Backward Compatibility Module

This module provides backward compatibility for imports from quality_scoring.py.
All functionality has been modularized into the quality_scoring/ subdirectory.

DEPRECATED: This file exists only for backward compatibility.
Please update imports to use the modular structure:
    from app.services.collection_flow.quality_scoring import QualityAssessmentService
"""

# Re-export all public interfaces for backward compatibility
from .quality_scoring import (  # Note: Constants and validators are not re-exported here as they were; previously private to the module. If needed, they can be imported from; the quality_scoring package directly.; Services; Enums; Models
    ConfidenceAssessmentService,
    ConfidenceLevel,
    ConfidenceScore,
    QualityAssessmentService,
    QualityDimension,
    QualityScore,
)

__all__ = [
    "QualityDimension",
    "ConfidenceLevel",
    "QualityScore",
    "ConfidenceScore",
    "QualityAssessmentService",
    "ConfidenceAssessmentService",
]
