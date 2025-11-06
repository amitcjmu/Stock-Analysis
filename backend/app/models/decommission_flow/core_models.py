"""
Decommission Flow Core Database Models

Primary SQLAlchemy models for the decommission flow system following ADR-006.
Implements safe system decommissioning with data preservation.

Reference: /docs/planning/DECOMMISSION_FLOW_SOLUTION.md Section 3.2
Pattern: backend/app/models/assessment_flow/core_models.py
"""

import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DecommissionFlow(Base):
    """
    Child flow table for decommission workflow (ADR-006 two-table pattern).

    Tracks operational state, phase progress, and runtime decisions for system
    decommissioning. Master flow lifecycle managed in
    crewai_flow_state_extensions.

    Phases (per ADR-027):
    - decommission_planning: Dependency analysis, risk assessment, cost analysis
    - data_migration: Data retention policies, archival jobs
    - system_shutdown: Pre-validation, shutdown, post-validation, cleanup
    """

    __tablename__ = "decommission_flows"
    __table_args__ = (
        CheckConstraint(
            "status IN ('initialized', 'decommission_planning', "
            "'data_migration', 'system_shutdown', 'completed', 'failed', 'paused')",
            name="valid_decommission_flow_status",
        ),
        CheckConstraint(
            "current_phase IN ('decommission_planning', 'data_migration', "
            "'system_shutdown', 'completed')",
            name="valid_decommission_flow_phase",
        ),
        CheckConstraint(
            "compliance_score >= 0 AND compliance_score <= 100",
            name="valid_compliance_score",
        ),
        {"schema": "migration"},
    )

    # Primary identifiers
    flow_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Master Flow Coordination (ADR-006)
    master_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "migration.crewai_flow_state_extensions.flow_id", ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
        comment="Reference to master flow orchestrator for lifecycle management",
    )

    # Multi-tenant scoping (REQUIRED for all queries)
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.client_accounts.id"),
        nullable=False,
        index=True,
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.engagements.id"),
        nullable=False,
        index=True,
    )

    # Flow metadata
    flow_name = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Operational status (child flow - per ADR-012)
    status = Column(String(50), nullable=False, default="initialized", index=True)
    current_phase = Column(String(50), nullable=False, default="decommission_planning")

    # Selected systems for decommission
    selected_system_ids: ARRAY = Column(  # type: ignore[assignment]
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
        comment="Array of Asset IDs selected for decommission",
    )
    system_count = Column(Integer, nullable=False)

    # Phase progress tracking (ALIGNED WITH FlowTypeConfig per ADR-027)
    decommission_planning_status = Column(String(50), default="pending")
    decommission_planning_completed_at = Column(DateTime(timezone=True), nullable=True)

    data_migration_status = Column(String(50), default="pending")
    data_migration_completed_at = Column(DateTime(timezone=True), nullable=True)

    system_shutdown_status = Column(String(50), default="pending")
    system_shutdown_started_at = Column(DateTime(timezone=True), nullable=True)
    system_shutdown_completed_at = Column(DateTime(timezone=True), nullable=True)

    # Configuration and runtime state
    decommission_strategy = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment=(
            "Strategy configuration: priority, execution_mode, "
            "rollback_enabled, stakeholder_approvals"
        ),
    )
    runtime_state = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment=(
            "Runtime execution state: current_agent, phase_metrics, "
            "pending_approvals, warnings, errors"
        ),
    )

    # Aggregated metrics
    total_systems_decommissioned = Column(Integer, default=0)
    estimated_annual_savings = Column(Numeric(15, 2), nullable=True)
    actual_annual_savings = Column(Numeric(15, 2), nullable=True)
    compliance_score = Column(
        Numeric(5, 2), nullable=True, comment="0-100 compliance score"
    )

    # Relationships
    master_flow = relationship(
        "CrewAIFlowStateExtensions",
        foreign_keys=[master_flow_id],
        primaryjoin=(
            "DecommissionFlow.master_flow_id == " "CrewAIFlowStateExtensions.flow_id"
        ),
        back_populates="decommission_flows",
    )

    plans = relationship(
        "DecommissionPlan",
        back_populates="flow",
        cascade="all, delete-orphan",
        lazy="select",
    )

    archive_jobs = relationship(
        "ArchiveJob",
        back_populates="flow",
        cascade="all, delete-orphan",
        lazy="select",
    )

    execution_logs = relationship(
        "DecommissionExecutionLog",
        back_populates="flow",
        cascade="all, delete-orphan",
        lazy="select",
    )

    validation_checks = relationship(
        "DecommissionValidationCheck",
        back_populates="flow",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<DecommissionFlow(flow_id={self.flow_id}, "
            f"status='{self.status}', phase='{self.current_phase}', "
            f"systems={self.system_count})>"
        )


class DecommissionPlan(Base):
    """
    Per-system decommission plan with dependencies, risk assessment, and approvals.

    Each plan represents the decommission strategy for a single system,
    including dependency analysis, scheduling, and required approvals.
    """

    __tablename__ = "decommission_plans"
    __table_args__ = (
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high', 'very_high')",
            name="valid_risk_level",
        ),
        CheckConstraint(
            "priority IN ('high', 'medium', 'low')",
            name="valid_priority",
        ),
        CheckConstraint(
            "approval_status IN ('pending', 'approved', 'rejected', 'cancelled')",
            name="valid_approval_status",
        ),
        {"schema": "migration"},
    )

    # Primary identifiers
    plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.decommission_flows.flow_id", ondelete="CASCADE"),
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
        index=True,
    )
    system_name = Column(String(255), nullable=False)
    system_type = Column(String(100), nullable=True)

    # Dependencies
    dependencies = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of dependent systems: [{system_id, name, impact}]",
    )

    # Risk assessment
    risk_level = Column(String(50), nullable=False)
    risk_factors = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of identified risk factors",
    )
    mitigation_strategies = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of risk mitigation strategies",
    )

    # Scheduling
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    estimated_duration_hours = Column(Integer, nullable=True)
    priority = Column(String(50), nullable=True)

    # Approvals
    requires_approvals = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of required approvers: [{approver, role, status}]",
    )
    approval_status = Column(String(50), default="pending")
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    flow = relationship("DecommissionFlow", back_populates="plans")
    system = relationship("Asset", foreign_keys=[system_id])

    def __repr__(self) -> str:
        return (
            f"<DecommissionPlan(plan_id={self.plan_id}, "
            f"system='{self.system_name}', risk='{self.risk_level}', "
            f"approval='{self.approval_status}')>"
        )
