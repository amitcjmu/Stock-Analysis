"""
Causal reasoning patterns for Agent Intelligence Architecture

This module implements causal reasoning patterns that help agents understand
cause-and-effect relationships in asset analysis. These patterns enable agents
to reason about why certain conditions lead to specific outcomes and how
changes might impact the system.

This file has been modularized. All functionality is now available through
the causal submodule while maintaining backward compatibility.
"""

# Import all classes from the modularized causal module
from .causal import *  # noqa: F403,F401

# Re-export for complete backward compatibility
from .causal import (
    BusinessValueCausalPattern,
    CausalChainAnalyzer,
    CausalRelationship,
    ModernizationCausalPattern,
    RiskCausalPattern,
)

# Export all for backward compatibility
__all__ = [
    "CausalRelationship",
    "BusinessValueCausalPattern",
    "RiskCausalPattern",
    "ModernizationCausalPattern",
    "CausalChainAnalyzer",
]
