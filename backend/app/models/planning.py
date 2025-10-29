"""
Planning Flow Models

SQLAlchemy ORM models for planning flow tables created in migrations 112-114.
Implements Two-Table Pattern (ADR-012) for wave planning, resource allocation,
and timeline management.

Tables:
1. planning_flows - Child flow operational state (migration 112)
2. project_timelines - Master timeline for Gantt charts (migration 113)
3. timeline_phases - Migration phases within timeline (migration 113)
4. timeline_milestones - Key milestones and deliverables (migration 113)
5. resource_pools - Role-based resource capacity (migration 114)
6. resource_allocations - Resource assignments to waves (migration 114)
7. resource_skills - Skill requirements and gaps (migration 114)

Related Issues:
- #698 (Wave Planning Flow - Database Schema)
- #701 (Timeline Planning Integration)
- #704 (Resource Planning Database Schema)
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PlanningFlow(Base):
    """
    Child flow table for planning flow operational state (ADR-012).

    Tracks operational decisions, phase status, and UI state for wave planning flows.
    Master flow lifecycle managed in crewai_flow_state_extensions table.
    """

    __tablename__ = "planning_flows"
    __table_args__ = {"schema": "migration"}

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Multi-Tenant Scoping (MANDATORY per ADR-012)
    client_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Master Flow Reference
    master_flow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "migration.crewai_flow_state_extensions.flow_id", ondelete="CASCADE"
        ),
        nullable=False,
    )

    # Planning Flow Identity
    planning_flow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True
    )

    # Current Phase (operational decisions)
    current_phase: Mapped[str] = mapped_column(String(50), nullable=False)
    phase_status: Mapped[str] = mapped_column(String(20), nullable=False)

    # JSONB Data Columns
    planning_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    wave_plan_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    resource_allocation_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    timeline_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    cost_estimation_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    agent_execution_log: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )
    ui_state: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    validation_errors: Mapped[List[str]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )
    warnings: Mapped[List[str]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )
    selected_applications: Mapped[List[uuid.UUID]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )

    # Timestamps
    planning_ready_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    planning_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    planning_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Relationships
    master_flow = relationship(
        "CrewAIFlowStateExtensions", back_populates="planning_flows"
    )
    timelines = relationship(
        "ProjectTimeline", back_populates="planning_flow", cascade="all, delete-orphan"
    )
    resource_allocations = relationship(
        "ResourceAllocation",
        back_populates="planning_flow",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<PlanningFlow(planning_flow_id={self.planning_flow_id}, "
            f"current_phase='{self.current_phase}', "
            f"phase_status='{self.phase_status}')>"
        )


class ProjectTimeline(Base):
    """
    Master timeline for planning flow (Gantt chart support).

    Provides structured timeline data with critical path analysis, progress tracking,
    and AI-generated optimization recommendations.
    """

    __tablename__ = "project_timelines"
    __table_args__ = {"schema": "migration"}

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Multi-Tenant Scoping
    client_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Planning Flow Reference
    planning_flow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("migration.planning_flows.planning_flow_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Timeline Metadata
    timeline_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Timeline Dates
    overall_start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    overall_end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    baseline_start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    baseline_end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Critical Path Analysis
    critical_path_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )

    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    progress_percentage: Mapped[float] = mapped_column(
        Numeric(5, 2), server_default=text("0.00")
    )

    # AI-Generated Insights
    ai_recommendations: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    optimization_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))

    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Relationships
    planning_flow = relationship("PlanningFlow", back_populates="timelines")
    phases = relationship(
        "TimelinePhase", back_populates="timeline", cascade="all, delete-orphan"
    )
    milestones = relationship(
        "TimelineMilestone", back_populates="timeline", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<ProjectTimeline(timeline_name='{self.timeline_name}', "
            f"status='{self.status}')>"
        )


class TimelinePhase(Base):
    """
    Migration phases within timeline for detailed Gantt visualization.

    Tracks phase dependencies, effort, cost, and critical path status.
    Supports finish-to-start, start-to-start, finish-to-finish, and
    start-to-finish dependency types.
    """

    __tablename__ = "timeline_phases"
    __table_args__ = {"schema": "migration"}

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Multi-Tenant Scoping
    client_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timeline Reference
    timeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("migration.project_timelines.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Wave Reference (optional - phase may span multiple waves)
    wave_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Phase Identity
    phase_number: Mapped[int] = mapped_column(Integer, nullable=False)
    phase_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Phase Dates
    planned_start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    planned_end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    actual_start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    actual_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Dependencies
    predecessor_phase_ids: Mapped[List[uuid.UUID]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )
    dependency_type: Mapped[str] = mapped_column(
        String(20), server_default=text("'finish_to_start'")
    )
    lag_days: Mapped[int] = mapped_column(Integer, server_default=text("0"))

    # Phase Details
    effort_hours: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    estimated_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    assigned_resources: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )

    # Status Tracking
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="not_started"
    )
    progress_percentage: Mapped[float] = mapped_column(
        Numeric(5, 2), server_default=text("0.00")
    )
    is_on_critical_path: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false")
    )

    # Risk & Issues
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    blocking_issues: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )

    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    timeline = relationship("ProjectTimeline", back_populates="phases")

    def __repr__(self) -> str:
        return (
            f"<TimelinePhase(phase_number={self.phase_number}, "
            f"phase_name='{self.phase_name}', status='{self.status}')>"
        )


class TimelineMilestone(Base):
    """
    Key milestones and deliverables within project timeline.

    Tracks milestone dates, status, and associated deliverables with
    notification support for upcoming deadlines.
    """

    __tablename__ = "timeline_milestones"
    __table_args__ = {"schema": "migration"}

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Multi-Tenant Scoping
    client_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timeline Reference
    timeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("migration.project_timelines.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Phase Reference (optional - milestone may be timeline-level)
    phase_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("migration.timeline_phases.id", ondelete="SET NULL"),
    )

    # Wave Reference (optional)
    wave_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Milestone Identity
    milestone_number: Mapped[int] = mapped_column(Integer, nullable=False)
    milestone_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Milestone Type
    milestone_type: Mapped[str] = mapped_column(String(50), default="deliverable")

    # Dates
    planned_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    actual_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    baseline_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="not_started"
    )
    is_critical: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))

    # Deliverables
    deliverables: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )

    # Dependencies
    predecessor_milestone_ids: Mapped[List[uuid.UUID]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )

    # Notifications
    notification_days_before: Mapped[int] = mapped_column(
        Integer, server_default=text("7")
    )
    notification_sent: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false")
    )
    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    timeline = relationship("ProjectTimeline", back_populates="milestones")
    phase = relationship("TimelinePhase")

    def __repr__(self) -> str:
        return (
            f"<TimelineMilestone(milestone_number={self.milestone_number}, "
            f"milestone_name='{self.milestone_name}', status='{self.status}')>"
        )


class ResourcePool(Base):
    """
    Role-based resource capacity and cost tracking.

    Manages resource pools with capacity, skills, cost rates, and utilization
    tracking. Supports individual, role-based, and team resource types.
    """

    __tablename__ = "resource_pools"
    __table_args__ = {"schema": "migration"}

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Multi-Tenant Scoping
    client_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Resource Pool Identity
    pool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Resource Type (from #690: role-based resources)
    resource_type: Mapped[str] = mapped_column(String(50), default="role")
    role_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Capacity Tracking
    total_capacity_hours: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    available_capacity_hours: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    allocated_capacity_hours: Mapped[float] = mapped_column(
        Numeric(10, 2), server_default=text("0.00")
    )

    # Cost Tracking (from #690: hourly rates)
    hourly_rate: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Skills (JSONB array for flexible skill tracking)
    skills: Mapped[List[str]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))

    # Location & Availability
    location: Mapped[Optional[str]] = mapped_column(String(255))
    timezone: Mapped[Optional[str]] = mapped_column(String(50))
    availability_start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    availability_end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Resource Pool Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    utilization_percentage: Mapped[float] = mapped_column(
        Numeric(5, 2), server_default=text("0.00")
    )

    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Relationships
    allocations = relationship(
        "ResourceAllocation",
        back_populates="resource_pool",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<ResourcePool(pool_name='{self.pool_name}', "
            f"role_name='{self.role_name}', utilization={self.utilization_percentage}%)>"
        )


class ResourceAllocation(Base):
    """
    Resource assignments to migration waves with AI suggestions.

    Tracks resource allocations to waves with AI-generated suggestions,
    manual override capability, and cost tracking.
    """

    __tablename__ = "resource_allocations"
    __table_args__ = {"schema": "migration"}

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Multi-Tenant Scoping
    client_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Planning Flow Reference
    planning_flow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("migration.planning_flows.planning_flow_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Wave Reference (FK to migration_waves)
    wave_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Resource Pool Reference
    resource_pool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("migration.resource_pools.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Allocation Details
    allocated_hours: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    allocation_percentage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))

    # Dates
    allocation_start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    allocation_end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Cost Calculation
    estimated_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    actual_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))

    # AI-Generated Allocation (from #690: AI suggestions with manual override)
    is_ai_suggested: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    ai_confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    manual_override: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    override_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="planned")

    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Relationships
    planning_flow = relationship("PlanningFlow", back_populates="resource_allocations")
    resource_pool = relationship("ResourcePool", back_populates="allocations")

    def __repr__(self) -> str:
        return (
            f"<ResourceAllocation(wave_id={self.wave_id}, "
            f"allocated_hours={self.allocated_hours}, status='{self.status}')>"
        )


class ResourceSkill(Base):
    """
    Skill requirements and gap analysis per wave.

    Tracks required skills, proficiency levels, and availability with
    gap analysis warnings (non-blocking per #690).
    """

    __tablename__ = "resource_skills"
    __table_args__ = {"schema": "migration"}

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Multi-Tenant Scoping
    client_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Wave Reference (FK to migration_waves)
    wave_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Skill Requirement
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    skill_category: Mapped[Optional[str]] = mapped_column(String(100))
    proficiency_level: Mapped[str] = mapped_column(String(50), default="intermediate")

    # Requirement Details
    required_hours: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    available_hours: Mapped[float] = mapped_column(
        Numeric(10, 2), server_default=text("0.00")
    )

    # Gap Analysis (from #690: non-blocking warnings)
    has_gap: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    gap_severity: Mapped[str] = mapped_column(String(20), default="low")
    gap_impact_description: Mapped[Optional[str]] = mapped_column(Text)

    # AI Analysis
    ai_recommendations: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )

    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )

    def __repr__(self) -> str:
        return (
            f"<ResourceSkill(skill_name='{self.skill_name}', "
            f"proficiency_level='{self.proficiency_level}', has_gap={self.has_gap})>"
        )
