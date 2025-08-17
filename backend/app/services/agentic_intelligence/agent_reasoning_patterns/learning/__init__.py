"""
Learning Patterns Module

This module contains all learning and adaptation functionality for the
Agent Intelligence Architecture.
"""

# Import all learning pattern classes
from .discovery_engine import PatternDiscoveryEngine
from .adaptive_engine import AdaptiveReasoningEngine
from .learning_manager import ContinuousLearningManager

# Export all classes for backward compatibility
__all__ = [
    "PatternDiscoveryEngine",
    "AdaptiveReasoningEngine",
    "ContinuousLearningManager",
]
