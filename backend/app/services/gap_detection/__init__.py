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

from .schemas import (
    DataRequirements,
    ColumnGapReport,
    EnrichmentGapReport,
)

__all__ = [
    "DataRequirements",
    "ColumnGapReport",
    "EnrichmentGapReport",
]
