"""
Governance API endpoints for Collection Gaps Phase 2.

This module provides endpoints for managing governance requirements and migration exceptions,
including approval workflows and compliance tracking.

This is a compatibility module that imports from the modularized governance package.
"""

# Import all public functions to maintain backward compatibility
from .governance import (
    create_governance_requirement,
    create_migration_exception,
    list_governance_requirements,
    list_migration_exceptions,
    router,
)

# Export all public symbols
__all__ = [
    "router",
    "create_governance_requirement",
    "create_migration_exception",
    "list_governance_requirements",
    "list_migration_exceptions",
]
