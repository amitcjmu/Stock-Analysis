"""
Collection Flow Execution Module
Modularized collection flow execution operations with backward compatibility.

This module preserves the public API of the original collection_crud_execution.py file
while organizing the code into logical modules for better maintainability.
"""

# Import all public functions to maintain backward compatibility
from .base import sanitize_mfo_result
from .queries import ensure_collection_flow

# Import from new modular files
from .creation import create_master_flow_for_orphan
from .execution import execute_collection_flow
from .management import continue_flow
from .analysis import rerun_gap_analysis

# Define public API for export
__all__ = [
    "sanitize_mfo_result",
    "ensure_collection_flow",
    "create_master_flow_for_orphan",
    "execute_collection_flow",
    "continue_flow",
    "rerun_gap_analysis",
]
