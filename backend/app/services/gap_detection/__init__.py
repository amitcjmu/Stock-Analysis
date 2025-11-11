"""
Gap Detection Service Module

This module provides intelligent multi-layer gap detection for assets across:
- SQLAlchemy columns
- Enrichment tables (7 types)
- JSONB fields
- CanonicalApplication metadata
- Architecture standards

Part of Issue #980: Intelligent Multi-Layer Gap Detection System
All 8 GPT-5 recommendations incorporated.
"""

from .gap_analyzer import GapAnalyzer
from .schemas import (
    ApplicationGapReport,
    ColumnGapReport,
    ComprehensiveGapReport,
    DataRequirements,
    EnrichmentGapReport,
    JSONBGapReport,
    StandardsGapReport,
    StandardViolation,
)

__all__ = [
    # Main orchestrator
    "GapAnalyzer",
    # Schema models
    "DataRequirements",
    "ColumnGapReport",
    "EnrichmentGapReport",
    "JSONBGapReport",
    "ApplicationGapReport",
    "StandardsGapReport",
    "StandardViolation",
    "ComprehensiveGapReport",
]
