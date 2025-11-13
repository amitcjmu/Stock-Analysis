"""Resource-related models for planning flow."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


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
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    engagement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

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
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    engagement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

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
