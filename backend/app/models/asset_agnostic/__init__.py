"""
Asset-Agnostic Models for Dynamic Asset Management and Conflict Detection

This module contains SQLAlchemy models for:
- Conflict detection and resolution
"""

from .asset_field_conflicts import AssetFieldConflict

__all__ = [
    "AssetFieldConflict",
]
