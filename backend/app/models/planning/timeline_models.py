"""Timeline-related models for planning flow."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
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
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    engagement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

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
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    engagement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

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
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    engagement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

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

    # Milestone Identity
    milestone_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Milestone Type (matches DB constraint: phase_completion, deliverable, gate_review, dependency, custom)
    milestone_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="custom"
    )

    # Dates (DB column is 'target_date' not 'planned_date')
    target_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    actual_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    baseline_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Status (matches DB constraint: pending, at_risk, achieved, missed)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    is_critical: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))

    # Deliverables
    deliverables: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )

    # Dependencies (DB column is 'depends_on_milestone_ids' not 'predecessor_milestone_ids')
    depends_on_milestone_ids: Mapped[List[uuid.UUID]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )

    # Notifications (DB column is 'notify_days_before' not 'notification_days_before')
    notify_days_before: Mapped[int] = mapped_column(Integer, server_default=text("7"))
    notification_sent: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false")
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
            f"<TimelineMilestone(id={self.id}, "
            f"milestone_name='{self.milestone_name}', status='{self.status}')>"
        )
