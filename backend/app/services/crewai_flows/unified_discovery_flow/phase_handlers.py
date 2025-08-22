"""
Phase Handlers Module

This module contains all the phase handling methods extracted from the base_flow.py
to improve maintainability and code organization.

This module re-exports the PhaseHandlers class from the handlers package for backward compatibility.
"""

# Re-export from handlers package for backward compatibility
from .handlers import PhaseHandlers

__all__ = ["PhaseHandlers"]
