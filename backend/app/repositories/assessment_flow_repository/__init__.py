"""
Assessment Flow Repository Package

Modularized repository split into:
- base_repository.py: Main repository class with delegation to specialized modules
- commands/: Write operations (CRUD) for flows, architecture, components, decisions, feedback
- queries/: Read operations for fetching flows, analytics, and state construction
- specifications/: Utility methods and query specifications

Re-exports main repository for backward compatibility with existing imports.
"""

# Re-export main repository for backward compatibility
from .base_repository import AssessmentFlowRepository

__all__ = ['AssessmentFlowRepository']