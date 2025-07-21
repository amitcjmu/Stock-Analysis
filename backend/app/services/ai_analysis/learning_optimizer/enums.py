"""
Learning Optimizer Enums
Contains enumeration types for learning patterns and optimization strategies.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

from enum import Enum


class LearningPattern(str, Enum):
    """Types of learning patterns supported"""
    RESPONSE_QUALITY = "response_quality"
    STAKEHOLDER_ENGAGEMENT = "stakeholder_engagement"
    QUESTION_EFFECTIVENESS = "question_effectiveness"
    COMPLETION_RATES = "completion_rates"
    GAP_RESOLUTION_SUCCESS = "gap_resolution_success"
    BUSINESS_CONTEXT_CORRELATION = "business_context_correlation"
    TEMPORAL_OPTIMIZATION = "temporal_optimization"
    COMPLEXITY_ADAPTATION = "complexity_adaptation"


class OptimizationStrategy(str, Enum):
    """Optimization strategies for questionnaires"""
    REDUCE_COMPLEXITY = "reduce_complexity"
    IMPROVE_TARGETING = "improve_targeting"
    ENHANCE_ENGAGEMENT = "enhance_engagement"
    OPTIMIZE_SEQUENCING = "optimize_sequencing"
    REFINE_QUESTIONS = "refine_questions"
    ADJUST_TIMING = "adjust_timing"
    PERSONALIZE_APPROACH = "personalize_approach"
    STRENGTHEN_VALIDATION = "strengthen_validation"