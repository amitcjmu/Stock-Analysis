"""
Decommission Flow SQLAlchemy Models

Database models for the Decommission Flow following ADR-006 two-table pattern.
Implements safe system decommissioning with data preservation.

Models:
- DecommissionFlow: Child flow table (master is crewai_flow_state_extensions)
- DecommissionPlan: Per-system decommission plans with dependencies
- DataRetentionPolicy: Compliance-driven retention policies
- ArchiveJob: Data archival tracking
- DecommissionExecutionLog: Audit trail for decommission actions
- DecommissionValidationCheck: Post-decommission validation

Reference: /docs/planning/DECOMMISSION_FLOW_SOLUTION.md Section 3.2-3.3
Pattern: backend/app/models/assessment_flow/__init__.py

Note: This file maintains backward compatibility by re-exporting all models
from the decommission_flow package. The actual model definitions are now
organized in separate modules within backend/app/models/decommission_flow/
"""

# Re-export all models from the package for backward compatibility
# Fixed per CodeRabbit: Import from submodules to avoid circular import
from app.models.decommission_flow.core_models import (
    DecommissionFlow,
    DecommissionPlan,
)
from app.models.decommission_flow.policy_models import DataRetentionPolicy
from app.models.decommission_flow.audit_models import (
    ArchiveJob,
    DecommissionExecutionLog,
    DecommissionValidationCheck,
)

__all__ = [
    "DecommissionFlow",
    "DecommissionPlan",
    "DataRetentionPolicy",
    "ArchiveJob",
    "DecommissionExecutionLog",
    "DecommissionValidationCheck",
]
