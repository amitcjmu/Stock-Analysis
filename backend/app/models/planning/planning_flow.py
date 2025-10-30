"""PlanningFlow model - Child flow operational state."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, ForeignKey, String, text
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
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    engagement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

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
