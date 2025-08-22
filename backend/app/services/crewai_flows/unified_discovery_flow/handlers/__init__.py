"""
Phase handlers package for the unified discovery flow.

This package contains modularized phase handlers for better maintainability:
- data_validation_handler: Handles data validation phase
- data_processing_handler: Handles data cleansing and asset creation
- analysis_handler: Handles parallel analysis phases
- communication_utils: Agent communication utilities
- state_utils: State management and tracking utilities
"""

from .phase_handlers import PhaseHandlers

__all__ = ["PhaseHandlers"]
