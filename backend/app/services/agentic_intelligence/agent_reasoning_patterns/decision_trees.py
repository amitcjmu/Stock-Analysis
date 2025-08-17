"""
Decision tree patterns and main reasoning engine for Agent Intelligence Architecture

This module contains the main AgentReasoningEngine and decision tree logic that
orchestrates all reasoning patterns to analyze assets and generate comprehensive
intelligence assessments.

This file has been modularized. All functionality is now available through
the decision_tree submodule while maintaining backward compatibility.
"""

# Import all classes from the modularized decision_tree module
from .decision_tree import *  # noqa: F403,F401

# Re-export for complete backward compatibility
from .decision_tree import (
    AgentReasoningEngine,
    BusinessValueAnalyzer,
    RiskAnalyzer,
    ModernizationAnalyzer,
    EvidenceAnalyzers,
    ReasoningUtilities,
)

# Export all for backward compatibility
__all__ = [
    "AgentReasoningEngine",
    "BusinessValueAnalyzer",
    "RiskAnalyzer",
    "ModernizationAnalyzer",
    "EvidenceAnalyzers",
    "ReasoningUtilities",
]
