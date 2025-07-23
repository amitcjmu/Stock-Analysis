"""
Recommendation Generators Package
Team C1 - Task C1.5

Collection of specialized recommendation generators for different optimization areas.
"""

from .config_recommendations import ConfigRecommendationGenerator
from .performance_recommendations import PerformanceRecommendationGenerator
from .phase_recommendations import PhaseRecommendationGenerator
from .quality_recommendations import QualityRecommendationGenerator
from .tier_recommendations import TierRecommendationGenerator

__all__ = [
    "TierRecommendationGenerator",
    "ConfigRecommendationGenerator",
    "PhaseRecommendationGenerator",
    "QualityRecommendationGenerator",
    "PerformanceRecommendationGenerator",
]
