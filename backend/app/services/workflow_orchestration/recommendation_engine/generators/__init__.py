"""
Recommendation Generators Package
Team C1 - Task C1.5

Collection of specialized recommendation generators for different optimization areas.
"""

from .tier_recommendations import TierRecommendationGenerator
from .config_recommendations import ConfigRecommendationGenerator
from .phase_recommendations import PhaseRecommendationGenerator
from .quality_recommendations import QualityRecommendationGenerator
from .performance_recommendations import PerformanceRecommendationGenerator

__all__ = [
    'TierRecommendationGenerator',
    'ConfigRecommendationGenerator',
    'PhaseRecommendationGenerator',
    'QualityRecommendationGenerator',
    'PerformanceRecommendationGenerator',
]