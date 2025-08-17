"""
Learning and adaptation patterns for Agent Intelligence Architecture

This module implements learning patterns that enable agents to discover new reasoning
patterns, adapt to new environments, and improve their analysis over time through
continuous learning from user feedback and validation.

This file has been modularized. All functionality is now available through
the learning submodule while maintaining backward compatibility.
"""

# Import all classes from the modularized learning module
from .learning import *  # noqa: F403,F401

# Re-export for complete backward compatibility
from .learning import (
    PatternDiscoveryEngine,
    AdaptiveReasoningEngine,
    ContinuousLearningManager,
)

# Export all for backward compatibility
__all__ = [
    "PatternDiscoveryEngine",
    "AdaptiveReasoningEngine",
    "ContinuousLearningManager",
]
