"""
Smart Workflow Recommendation System
Team C1 - Task C1.5

Intelligent recommendation system that analyzes historical workflow executions, environment patterns,
and business requirements to recommend optimal workflow configurations, automation tiers, and
execution strategies for Collection Flow optimization.

Integrates machine learning insights with business rules and provides adaptive recommendations
based on success patterns, quality outcomes, and performance metrics.

Note: This file has been modularized. The original implementation has been split into:
- recommendation_engine/enums.py - Enum definitions
- recommendation_engine/models.py - Data models
- recommendation_engine/analyzers.py - Analysis methods
- recommendation_engine/evaluators.py - Evaluation and learning
- recommendation_engine/optimizers.py - Optimization logic
- recommendation_engine/engine.py - Main orchestration engine
- recommendation_engine/generators/ - Specific recommendation generators

This file now re-exports all public interfaces for backward compatibility.
"""

# Re-export all public interfaces from the modularized structure
from .recommendation_engine import (
    ConfigRecommendationGenerator,
    LearningPattern,
    PerformanceRecommendationGenerator,
    PhaseRecommendationGenerator,
    QualityRecommendationGenerator,
    # Core components (for advanced usage)
    RecommendationAnalyzers,
    RecommendationConfidence,
    RecommendationEvaluator,
    # Models
    RecommendationInsight,
    RecommendationOptimizer,
    RecommendationPackage,
    RecommendationSource,
    # Enums
    RecommendationType,
    # Main engine
    SmartWorkflowRecommendationEngine,
    # Generators (for advanced usage)
    TierRecommendationGenerator,
    WorkflowRecommendation,
)

# Maintain backward compatibility by exporting all symbols
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