"""
User Experience Optimizer - Modular Structure

This package provides modular user experience optimization functionality
for ADCS end-to-end integration workflows.

Generated with CC for modular backend architecture.
"""

# Core types and enums
from .base import (
    UXOptimizationArea,
    UXMetricType,
    UXRecommendation,
    UserJourneyAnalytics,
    OptimizationContext
)

# Analysis and recommendations
from .analyzer import UXAnalyzer
from .recommendations import UXRecommendationEngine
from .optimization_manager import OptimizationManager

# Main optimizer class
from .optimizer import UserExperienceOptimizer

__all__ = [
    'UXOptimizationArea',
    'UXMetricType',
    'UXRecommendation',
    'UserJourneyAnalytics',
    'OptimizationContext',
    'UXAnalyzer',
    'UXRecommendationEngine',
    'OptimizationManager',
    'UserExperienceOptimizer'
]