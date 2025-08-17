"""
Logical reasoning patterns for Agent Intelligence Architecture

This module contains the core logical reasoning patterns that agents use to analyze
assets and discover business value, risk factors, and modernization opportunities.
These patterns represent structured business logic and technical analysis rules.

This file has been modularized. All functionality is now available through
the logical submodule while maintaining backward compatibility.
"""

# Import all classes from the modularized logical module
from .logical import *  # noqa: F403,F401

# Re-export for complete backward compatibility
from .logical import (
    AssetReasoningPatterns,
    BusinessValueReasoningPattern,
    RiskAssessmentReasoningPattern,
    ModernizationReasoningPattern,
)

# Ensure all original exports are available
__all__ = [
    "AssetReasoningPatterns",
    "BusinessValueReasoningPattern",
    "RiskAssessmentReasoningPattern",
    "ModernizationReasoningPattern",
]
