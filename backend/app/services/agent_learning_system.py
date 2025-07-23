"""
Agent Learning System - Backward Compatibility Wrapper

This module provides backward compatibility for the modularized agent learning system.
All functionality has been moved to the agent_learning package.

For new code, please import from:
- app.services.agent_learning

Migration guide:
- LearningContext -> app.services.agent_learning.models.LearningContext
- LearningPattern -> app.services.agent_learning.models.LearningPattern
- PerformanceLearningPattern -> app.services.agent_learning.models.PerformanceLearningPattern
- ContextScopedAgentLearning -> app.services.agent_learning.core.ContextScopedAgentLearning
"""

# Re-export everything from the modular structure for backward compatibility
from app.services.agent_learning import (AgentLearningSystem,
                                         ContextScopedAgentLearning,
                                         LearningContext, LearningPattern,
                                         PerformanceLearningPattern)

# Create global instance for backward compatibility
agent_learning_system = ContextScopedAgentLearning()

__all__ = [
    "LearningContext",
    "LearningPattern",
    "PerformanceLearningPattern",
    "ContextScopedAgentLearning",
    "AgentLearningSystem",
    "agent_learning_system",
]
