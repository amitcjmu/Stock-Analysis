"""
Agent Learning System with Context Isolation and Performance Integration

Provides context-scoped learning for CrewAI agents with multi-tenant isolation.
Enhanced with performance monitoring integration.

Key Components:
- LearningContext: Context information for scoped learning
- LearningPattern: Represents a learned pattern with context isolation
- PerformanceLearningPattern: Performance-based learning pattern for optimization
- ContextScopedAgentLearning: Main learning system with context isolation
"""

from .models.learning_context import LearningContext
from .models.learning_pattern import LearningPattern, PerformanceLearningPattern
from .core.context_scoped_learning import ContextScopedAgentLearning

# Compatibility imports for backward compatibility
AgentLearningSystem = ContextScopedAgentLearning

__all__ = [
    'LearningContext',
    'LearningPattern',
    'PerformanceLearningPattern',
    'ContextScopedAgentLearning',
    'AgentLearningSystem'  # For backward compatibility
]