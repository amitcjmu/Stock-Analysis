"""
Decommission Flow Audit and Validation Models

Models for execution logging and post-decommission validation.
Provides audit trail and compliance verification for decommission activities.

Reference: /docs/planning/DECOMMISSION_FLOW_SOLUTION.md Section 3.4
"""

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DecommissionExecutionLog(Base):
    """
    Audit trail for decommission execution actions.

    Logs all execution steps, safety checks, and rollback points during
    system decommissioning for compliance and troubleshooting.
    """

    __tablename__ = "decommission_execution_logs"
    __table_args__ = (
        CheckConstraint(
            "execution_phase IN ('pre_validation', 'service_shutdown', "
            "'data_migration', 'infrastructure_removal', 'verification')",
            name="valid_execution_phase",
        ),
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', "
            "'failed', 'rolled_back')",
            name="valid_execution_log_status",
        ),
        {"schema": "migration"},
    )

    # Primary identifiers
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.decommission_flows.flow_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.decommission_plans.plan_id"),
        nullable=False,
        index=True,
    )

    # Multi-tenant scoping
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # System identification
    system_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id"),
        nullable=False,
    )

    # Execution details
    execution_phase = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, index=True)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Executor
    executed_by = Column(String(255), nullable=True, comment="Agent or user ID")

    # Safety checks
    safety_checks_passed = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of passed safety checks",
    )
    safety_checks_failed = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of failed safety checks",
    )
    rollback_available = Column(Boolean, default=True)

    # Logging
    execution_log = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of execution events: [{timestamp, action, result}]",
    )

    # Error handling
    error_details = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    flow = relationship("DecommissionFlow", back_populates="execution_logs")
    plan = relationship("DecommissionPlan")
    system = relationship("Asset", foreign_keys=[system_id])

    def __repr__(self) -> str:
        return (
            f"<DecommissionExecutionLog(log_id={self.log_id}, "
            f"phase='{self.execution_phase}', status='{self.status}')>"
        )


class DecommissionValidationCheck(Base):
    """
    Post-decommission validation checks.

    Verifies data integrity, access removal, service termination,
    and compliance after system decommission.
    """

    __tablename__ = "decommission_validation_checks"
    __table_args__ = (
        CheckConstraint(
            "validation_category IN ('data_integrity', 'access_removal', "
            "'service_termination', 'dependency_verification', 'compliance')",
            name="valid_validation_category",
        ),
        CheckConstraint(
            "status IN ('pending', 'passed', 'warning', 'failed')",
            name="valid_validation_check_status",
        ),
        {"schema": "migration"},
    )

    # Primary identifiers
    check_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.decommission_flows.flow_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    system_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id"),
        nullable=False,
        index=True,
    )

    # Multi-tenant scoping
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Check details
    validation_category = Column(String(100), nullable=False)
    check_name = Column(String(255), nullable=False)
    check_description = Column(Text, nullable=True)
    is_critical = Column(Boolean, default=False)

    # Results
    status = Column(String(50), nullable=False, default="pending", index=True)
    result_details = Column(JSONB, nullable=True)
    issues_found = Column(Integer, default=0)

    # Validation metadata
    validated_by = Column(String(255), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    flow = relationship("DecommissionFlow", back_populates="validation_checks")
    system = relationship("Asset", foreign_keys=[system_id])

    def __repr__(self) -> str:
        return (
            f"<DecommissionValidationCheck(check_id={self.check_id}, "
            f"category='{self.validation_category}', "
            f"check='{self.check_name}', "
            f"status='{self.status}', critical={self.is_critical})>"
        )
