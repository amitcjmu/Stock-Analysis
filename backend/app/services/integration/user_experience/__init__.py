"""
User Experience Optimizer - Modular Structure

This package provides modular user experience optimization functionality
for ADCS end-to-end integration workflows.

Generated with CC for modular backend architecture.
"""

# Core types and enums
# Analysis and recommendations
from .analyzer import UXAnalyzer
from .base import (
    OptimizationContext,
    UserJourneyAnalytics,
    UXMetricType,
    UXOptimizationArea,
    UXRecommendation,
)
from .optimization_manager import OptimizationManager

# Main optimizer class
from .optimizer import UserExperienceOptimizer
from .recommendations import UXRecommendationEngine

__all__ = [
    "UXOptimizationArea",
    "UXMetricType",
    "UXRecommendation",
    "UserJourneyAnalytics",
    "OptimizationContext",
    "UXAnalyzer",
    "UXRecommendationEngine",
    "OptimizationManager",
    "UserExperienceOptimizer",
]
