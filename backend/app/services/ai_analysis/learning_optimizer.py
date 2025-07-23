"""
Learning Patterns for Questionnaire Optimization - B2.5
ADCS AI Analysis & Intelligence Service

This service implements machine learning and pattern recognition to continuously
optimize questionnaire generation, targeting, and effectiveness based on
historical data and user feedback.

Built by: Agent Team B2 (AI Analysis & Intelligence)

NOTE: This file has been modularized. The implementation is now split into:
- learning_optimizer/enums.py - Enumeration types
- learning_optimizer/models.py - Data models
- learning_optimizer/analyzers.py - Pattern analysis functions
- learning_optimizer/insights.py - Insight generation functions
- learning_optimizer/calculations.py - Helper calculations
- learning_optimizer/core.py - Main LearningOptimizer class

This file re-exports all public interfaces for backward compatibility.
"""

# Re-export all public interfaces from the modularized structure
from .learning_optimizer import (  # Models; Main class and function; Enums
    LearningEvent, LearningInsight, LearningOptimizer, LearningPattern,
    OptimizationRecommendation, OptimizationStrategy,
    optimize_questionnaire_learning)

# Maintain backward compatibility
__all__ = [
    "LearningPattern",
    "OptimizationStrategy",
    "LearningEvent",
    "OptimizationRecommendation",
    "LearningInsight",
    "LearningOptimizer",
    "optimize_questionnaire_learning",
]
