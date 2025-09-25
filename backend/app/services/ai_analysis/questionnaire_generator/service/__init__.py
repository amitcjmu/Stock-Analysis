"""
Questionnaire Generator Service Module

This module has been modularized to improve maintainability while preserving
backward compatibility. All public APIs remain the same.
"""

# Import core service classes to maintain backward compatibility
from .core import QuestionnaireGeneratorService
from .processors import QuestionnaireProcessor
from .handlers import QuestionnaireService

# Maintain backward compatibility - export all public classes
__all__ = [
    "QuestionnaireGeneratorService",
    "QuestionnaireProcessor",
    "QuestionnaireService",
]
