"""
Assessment Data Repository Package

Backward compatible public API exports.
Per CLAUDE.md modularization pattern: Preserve all public imports.
"""

from .base import AssessmentDataRepository

__all__ = ["AssessmentDataRepository"]
