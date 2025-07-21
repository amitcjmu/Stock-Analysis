"""
Recommendation Engine Package
Team C1 - Task C1.5

Smart Workflow Recommendation System that provides intelligent recommendations
for workflow configurations, automation tiers, and execution strategies.
"""

# Export main engine
from .engine import SmartWorkflowRecommendationEngine

# Export enums
from .enums import (
    RecommendationType,
    RecommendationConfidence,
    RecommendationSource
)

# Export models
from .models import (
    RecommendationInsight,
    WorkflowRecommendation,
    RecommendationPackage,
    LearningPattern
)

# Export core components
from .analyzers import RecommendationAnalyzers
from .evaluators import RecommendationEvaluator
from .optimizers import RecommendationOptimizer

# Export generators
from .generators.tier_recommendations import TierRecommendationGenerator
from .generators.config_recommendations import ConfigRecommendationGenerator
from .generators.phase_recommendations import PhaseRecommendationGenerator
from .generators.quality_recommendations import QualityRecommendationGenerator
from .generators.performance_recommendations import PerformanceRecommendationGenerator

__all__ = [
    # Main engine
    'SmartWorkflowRecommendationEngine',
    
    # Enums
    'RecommendationType',
    'RecommendationConfidence',
    'RecommendationSource',
    
    # Models
    'RecommendationInsight',
    'WorkflowRecommendation',
    'RecommendationPackage',
    'LearningPattern',
    
    # Core components
    'RecommendationAnalyzers',
    'RecommendationEvaluator',
    'RecommendationOptimizer',
    
    # Generators
    'TierRecommendationGenerator',
    'ConfigRecommendationGenerator',
    'PhaseRecommendationGenerator',
    'QualityRecommendationGenerator',
    'PerformanceRecommendationGenerator',
]