"""
Governance API module for Collection Gaps Phase 2.

This module preserves backward compatibility while providing modularized governance
functionality for approval workflows and migration exceptions.
"""

# Import handlers to preserve public API
from .handlers import (
    create_governance_requirement,
    create_migration_exception,
    list_governance_requirements,
    list_migration_exceptions,
)

# Import router for FastAPI integration
from .handlers import router

__all__ = [
    "router",
    "create_governance_requirement",
    "create_migration_exception",
    "list_governance_requirements",
    "list_migration_exceptions",
]
