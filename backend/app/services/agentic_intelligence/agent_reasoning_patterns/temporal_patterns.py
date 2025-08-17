"""
Temporal reasoning patterns for Agent Intelligence Architecture

This module implements temporal reasoning patterns that help agents understand
time-based relationships in asset analysis. These patterns enable agents to
reason about trends, lifecycle stages, aging factors, and time-sensitive risks.

This file has been modularized. All functionality is now available through
the temporal submodule while maintaining backward compatibility.
"""

# Import all classes from the modularized temporal module
from .temporal import *  # noqa: F403,F401

# Re-export for complete backward compatibility
from .temporal import (
    TemporalPoint,
    TemporalTrend,
    AssetLifecyclePattern,
    PerformanceTrendPattern,
    TechnicalDebtAccumulationPattern,
)

# Export all for backward compatibility
__all__ = [
    "TemporalPoint",
    "TemporalTrend",
    "AssetLifecyclePattern",
    "PerformanceTrendPattern",
    "TechnicalDebtAccumulationPattern",
]
