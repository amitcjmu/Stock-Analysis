"""
Collection Flow Execution Operations
Flow lifecycle operations including ensuring flow existence, execution,
and continuation/resumption of collection flows.

IMPORTANT: This file has been modularized to improve maintainability.
The implementation is now split across multiple modules in the collection_crud_execution/ directory:

- base.py: Common utilities and shared functions (sanitize_mfo_result)
- queries.py: Read operations (ensure_collection_flow)
- commands.py: Write operations (execute_collection_flow, continue_flow, rerun_gap_analysis)

All public functions are re-exported from the collection_crud_execution module
to maintain backward compatibility with existing imports.
"""

# Import all functions from the modularized structure to maintain backward compatibility
from .collection_crud_execution import (
    sanitize_mfo_result,
    ensure_collection_flow,
    execute_collection_flow,
    continue_flow,
    rerun_gap_analysis,
)

# Preserve the original API surface for any external imports
__all__ = [
    "sanitize_mfo_result",
    "ensure_collection_flow",
    "execute_collection_flow",
    "continue_flow",
    "rerun_gap_analysis",
]
