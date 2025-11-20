"""
Asset Repository Package

Modularized repository split into:
- base.py: Main repository classes (AssetRepository, AssetDependencyRepository, WorkflowProgressRepository)
- commands.py: Write operations (updates, phase progression, 6R strategy updates)
- queries.py: Read operations (searches, filters, analytics)

Re-exports main repositories for backward compatibility with existing imports.
"""

# Re-export main repositories for backward compatibility
from .base import (
    AssetDependencyRepository,
    AssetRepository,
    WorkflowProgressRepository,
)

__all__ = [
    "AssetRepository",
    "AssetDependencyRepository",
    "WorkflowProgressRepository",
]
