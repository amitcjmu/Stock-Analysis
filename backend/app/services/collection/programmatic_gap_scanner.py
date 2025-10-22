"""
Programmatic Gap Scanner Service (Backward Compatibility Wrapper)

MODULARIZED: This file now imports from gap_scanner/ package.
All existing imports will continue to work without changes.

Example:
    from app.services.collection.programmatic_gap_scanner import ProgrammaticGapScanner
"""

# Backward compatibility - re-export from modularized package
from .gap_scanner import ProgrammaticGapScanner

__all__ = ["ProgrammaticGapScanner"]
