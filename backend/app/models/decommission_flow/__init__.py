"""
Decommission Flow Models Package

This package provides a complete set of models for the decommission flow system,
organized by functionality for better maintainability and code organization.

Modules:
- core_models: Primary database models (DecommissionFlow, DecommissionPlan)
- policy_models: Data retention and archive models
- audit_models: Execution logging and validation models

Reference: /docs/planning/DECOMMISSION_FLOW_SOLUTION.md
Pattern: backend/app/models/assessment_flow/__init__.py
"""

# Import core database models
from .core_models import (
    DecommissionFlow,
    DecommissionPlan,
)

# Import policy and archive models
from .policy_models import (
    DataRetentionPolicy,
    ArchiveJob,
)

# Import audit and validation models
from .audit_models import (
    DecommissionExecutionLog,
    DecommissionValidationCheck,
)

# Export all classes for easy import
__all__ = [
    # Core database models
    "DecommissionFlow",
    "DecommissionPlan",
    # Policy and archive models
    "DataRetentionPolicy",
    "ArchiveJob",
    # Audit and validation models
    "DecommissionExecutionLog",
    "DecommissionValidationCheck",
]
