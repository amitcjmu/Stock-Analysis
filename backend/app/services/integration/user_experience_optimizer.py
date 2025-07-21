"""
User Experience Optimizer for ADCS End-to-End Integration

This service optimizes user experience across the Collection → Discovery → Assessment workflow,
providing intelligent recommendations, progress optimization, and seamless flow transitions.

MODULAR STRUCTURE:
- Base types and classes: ./user_experience/base.py
- UX analysis: ./user_experience/analyzer.py
- Recommendations engine: ./user_experience/recommendations.py
- Optimization management: ./user_experience/optimization_manager.py
- Main optimizer: ./user_experience/optimizer.py

Generated with CC for modular backend architecture.
"""

import logging
from typing import Dict, List, Any, Tuple
from uuid import UUID

# Import modular components
from .user_experience import (
    UXOptimizationArea,
    UXMetricType,
    UXRecommendation,
    UserJourneyAnalytics,
    OptimizationContext,
    UserExperienceOptimizer as ModularUserExperienceOptimizer
)

# For backward compatibility - re-export all classes
from app.core.logging import get_logger
from app.monitoring.metrics import track_performance

logger = get_logger(__name__)


# Backward compatibility: Delegate to modular implementation
class UserExperienceOptimizer(ModularUserExperienceOptimizer):
    """
    User experience optimizer - delegates to modular implementation.
    Optimizes user experience across the complete ADCS workflow.
    """
    pass


# Export all types and classes for backward compatibility
__all__ = [
    'UXOptimizationArea',
    'UXMetricType', 
    'UXRecommendation',
    'UserJourneyAnalytics',
    'OptimizationContext',
    'UserExperienceOptimizer'
]