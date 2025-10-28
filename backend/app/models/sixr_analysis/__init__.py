"""
6R Analysis models - Modularized for maintainability.

This module provides backward compatibility by re-exporting all classes
from the modular structure. All imports from app.models.sixr_analysis
continue to work as before.

Modularization: October 2025 - Split 441-line file into <400 line modules
"""

# Import all models from submodules
from app.models.sixr_analysis.analysis import SixRAnalysis, SixRIteration
from app.models.sixr_analysis.base import (
    AnalysisStatus,
    ApplicationType,
    QuestionType,
    SQLALCHEMY_AVAILABLE,
)
from app.models.sixr_analysis.parameters import SixRAnalysisParameters, SixRParameter
from app.models.sixr_analysis.questions import SixRQuestion, SixRQuestionResponse
from app.models.sixr_analysis.recommendations import SixRRecommendation

# Export all classes for backward compatibility
__all__ = [
    # Core analysis models
    "SixRAnalysis",
    "SixRIteration",
    # Recommendation models
    "SixRRecommendation",
    # Question models
    "SixRQuestion",
    "SixRQuestionResponse",
    # Parameter models
    "SixRAnalysisParameters",
    "SixRParameter",
    # Enums (re-exported from schemas or defined in base)
    "AnalysisStatus",
    "ApplicationType",
    "QuestionType",
    # Utility flag
    "SQLALCHEMY_AVAILABLE",
]

# Note about Migration model relationship:
# The Migration model in backend/app/models/migration.py should have:
# sixr_analyses = relationship("SixRAnalysis", back_populates="migration")
