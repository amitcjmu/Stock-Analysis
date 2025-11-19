"""Command operations for collection questionnaires (writes, background tasks).

This module has been modularized to meet pre-commit file length limits (<400 lines).
All public APIs are preserved for backward compatibility.

Modularization completed: 2025-11-19 (Bug #10 deduplication fix pushed file over limit)
"""

# Import from modular structure
from .shared import _background_tasks
from .start_generation import _start_agent_generation
from .background_task import _background_generate

# Export public API (preserves backward compatibility)
__all__ = [
    "_start_agent_generation",
    "_background_generate",
    "_background_tasks",
]
