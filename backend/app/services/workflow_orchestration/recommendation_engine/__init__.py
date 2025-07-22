"""
Recommendation Engine Package
Team C1 - Task C1.5

Smart Workflow Recommendation System that provides intelligent recommendations
for workflow configurations, automation tiers, and execution strategies.
"""

# Export main engine
# Export core components
from .analyzers import RecommendationAnalyzers
from .engine import SmartWorkflowRecommendationEngine

# Export enums
from .enums import RecommendationConfidence, RecommendationSource, RecommendationType
from .evaluators import RecommendationEvaluator
from .generators.config_recommendations import ConfigRecommendationGenerator
from .generators.performance_recommendations import PerformanceRecommendationGenerator
from .generators.phase_recommendations import PhaseRecommendationGenerator
from .generators.quality_recommendations import QualityRecommendationGenerator

# Export generators
from .generators.tier_recommendations import TierRecommendationGenerator

# Export models
from .models import LearningPattern, RecommendationInsight, RecommendationPackage, WorkflowRecommendation
from .optimizers import RecommendationOptimizer

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