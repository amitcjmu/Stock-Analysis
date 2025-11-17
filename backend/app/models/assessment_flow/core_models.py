"""
Assessment Flow Core Database Models
Primary SQLAlchemy models for the assessment flow system.
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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from .enums_and_exceptions import AssessmentFlowStatus, AssessmentPhase


class AssessmentFlow(Base):
    """
    Main assessment flow model representing a complete assessment workflow.

    This model tracks the high-level state and progress of an assessment flow,
    coordinating with other assessment-related models for detailed data storage.
    """

    __tablename__ = "assessment_flows"
    __table_args__ = (
        CheckConstraint("progress >= 0 AND progress <= 100", name="valid_progress"),
    )

    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engagement_id = Column(
        UUID(as_uuid=True), ForeignKey("engagements.id"), nullable=False
    )
    client_account_id = Column(
        UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False
    )

    # MFO Integration - Links to master flow orchestrator
    master_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crewai_flow_state_extensions.flow_id"),
        nullable=True,
        comment="Reference to master flow orchestrator for cross-phase coordination",
    )

    # Flow identification and metadata
    flow_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Status and phase tracking
    status = Column(
        String(50), default=AssessmentFlowStatus.INITIALIZED.value, nullable=False
    )
    current_phase = Column(
        String(100), default=AssessmentPhase.INITIALIZATION.value, nullable=False
    )

    # Progress tracking
    progress = Column(Integer, default=0, nullable=False)
    phase_progress = Column(JSONB, default=lambda: {}, nullable=False)

    # Configuration and runtime data
    configuration = Column(JSONB, default=lambda: {}, nullable=False)
    runtime_state = Column(JSONB, default=lambda: {}, nullable=False)
    flow_metadata = Column(JSONB, default=lambda: {}, nullable=False)

    # Selected applications for assessment (separate from configuration for DB constraint)
    # DEPRECATED: Keep for backward compatibility (semantic mismatch from pre-October 2025)
    selected_application_ids = Column(
        JSONB,
        nullable=False,
        default=lambda: [],
        comment=(
            "DEPRECATED: Use selected_asset_ids instead. "
            "This column actually stores asset UUIDs, not application UUIDs "
            "(semantic mismatch from pre-October 2025)."
        ),
    )

    # NEW: Proper semantic fields (October 2025 refactor)
    selected_asset_ids = Column(
        JSONB,
        default=lambda: [],
        nullable=True,
        comment="Array of asset UUIDs selected for assessment",
    )

    selected_canonical_application_ids = Column(
        JSONB,
        default=lambda: [],
        nullable=True,
        comment="Array of canonical application UUIDs (resolved from collection_flow_applications junction table)",
    )

    application_asset_groups = Column(
        JSONB,
        default=lambda: [],
        nullable=True,
        comment="""Array of application groups with their assets. Structure: [
      {
        "canonical_application_id": "uuid",
        "canonical_application_name": "CRM System",
        "asset_ids": ["uuid1", "uuid2"],
        "asset_count": 2,
        "asset_types": ["server", "database"],
        "readiness_summary": {"ready": 1, "not_ready": 1}
      }
    ]""",
    )

    enrichment_status = Column(
        JSONB,
        default=lambda: {},
        nullable=True,
        comment="""Summary of enrichment table population. Structure: {
      "compliance_flags": 2,
      "licenses": 0,
      "vulnerabilities": 3,
      "resilience": 1,
      "dependencies": 4,
      "product_links": 0,
      "field_conflicts": 0
    }""",
    )

    readiness_summary = Column(
        JSONB,
        default=lambda: {},
        nullable=True,
        comment="""Assessment readiness summary. Structure: {
      "total_assets": 5,
      "ready": 2,
      "not_ready": 3,
      "in_progress": 0,
      "avg_completeness_score": 0.64
    }""",
    )

    # Assessment state fields
    architecture_captured = Column(Boolean, default=False, nullable=False)
    selected_template = Column(
        String(100),
        nullable=True,
        comment=(
            "Architecture template ID selected by user "
            "(enterprise-standard, cloud-native, security-first, performance-optimized, custom, or NULL)"
        ),
    )
    user_inputs = Column(JSONB, default=lambda: {}, nullable=False)
    phase_results = Column(JSONB, default=lambda: {}, nullable=False)
    agent_insights = Column(JSONB, default=lambda: [], nullable=False)
    apps_ready_for_planning = Column(JSONB, default=lambda: [], nullable=False)
    pause_points = Column(JSONB, default=lambda: {}, nullable=False)
    last_user_interaction = Column(DateTime(timezone=True), nullable=True)

    # Error handling and logging
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Master flow relationship
    master_flow = relationship(
        "CrewAIFlowStateExtensions",
        foreign_keys=[master_flow_id],
        primaryjoin="AssessmentFlow.master_flow_id == CrewAIFlowStateExtensions.flow_id",
        back_populates="assessment_flows",
    )

    # Child relationships
    application_overrides = relationship(
        "ApplicationArchitectureOverride",
        back_populates="assessment_flow",
        cascade="all, delete-orphan",
    )
    application_components = relationship(
        "ApplicationComponent",
        back_populates="assessment_flow",
        cascade="all, delete-orphan",
    )
    tech_debt_analyses = relationship(
        "TechDebtAnalysis",
        back_populates="assessment_flow",
        cascade="all, delete-orphan",
    )
    component_treatments = relationship(
        "ComponentTreatment",
        back_populates="assessment_flow",
        cascade="all, delete-orphan",
    )
    sixr_decisions = relationship(
        "SixRDecision",
        back_populates="assessment_flow",
        cascade="all, delete-orphan",
    )
    learning_feedback = relationship(
        "AssessmentLearningFeedback",
        back_populates="assessment_flow",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<AssessmentFlow(id='{self.id}', engagement_id='{self.engagement_id}', "
            f"status='{self.status}', phase='{self.current_phase}')>"
        )


class EngagementArchitectureStandard(Base):
    """
    Architecture standards and requirements for an engagement.

    These standards guide the assessment process and define the target
    architecture patterns and requirements for the migration.
    """

    __tablename__ = "engagement_architecture_standards"
    __table_args__ = (
        UniqueConstraint(
            "engagement_id",
            "requirement_type",
            "standard_name",
            name="unique_engagement_standard",
        ),
    )

    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engagement_id = Column(
        UUID(as_uuid=True), ForeignKey("engagements.id"), nullable=False
    )
    client_account_id = Column(
        UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False
    )

    # Standard definition
    requirement_type = Column(
        String(100), nullable=False
    )  # security, performance, etc.
    standard_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Requirements and constraints
    minimum_requirements = Column(JSONB, default=lambda: {}, nullable=False)
    preferred_patterns = Column(JSONB, default=lambda: {}, nullable=False)
    constraints = Column(JSONB, default=lambda: {}, nullable=False)
    supported_versions = Column(JSONB, nullable=True)  # Migration 092
    requirement_details = Column(JSONB, nullable=True)  # Migration 092

    # Validation and compliance
    is_mandatory = Column(Boolean, default=False, nullable=False)
    compliance_level = Column(String(50), default="standard", nullable=False)

    # Priority and impact
    priority = Column(Integer, default=5, nullable=False)  # 1-10 scale
    business_impact = Column(String(50), default="medium", nullable=False)

    # Metadata
    source = Column(String(255), nullable=True)  # Where this standard came from
    version = Column(String(50), nullable=True)
    score_metadata = Column(JSONB, default=lambda: {}, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<EngagementArchitectureStandard(id='{self.id}', "
            f"engagement_id='{self.engagement_id}', type='{self.requirement_type}', "
            f"name='{self.standard_name}')>"
        )
