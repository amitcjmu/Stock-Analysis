"""
Assessment Flow Component Models
Models for application components, architecture overrides, and component treatments.
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ApplicationArchitectureOverride(Base):
    """
    Overrides to default architecture standards for specific applications.

    Allows customization of architecture requirements on a per-application basis
    within the assessment flow context.
    """

    __tablename__ = "application_architecture_overrides"

    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(
        UUID(as_uuid=True), ForeignKey("assessment_flows.id"), nullable=False
    )
    application_id = Column(
        UUID(as_uuid=True), nullable=False
    )  # Reference to application

    # Override definition
    requirement_type = Column(String(100), nullable=False)
    original_value = Column(JSONB, default=lambda: {}, nullable=False)
    override_value = Column(JSONB, default=lambda: {}, nullable=False)

    # Justification and context
    reason = Column(Text, nullable=True)
    business_justification = Column(Text, nullable=True)
    technical_justification = Column(Text, nullable=True)

    # Approval and validation
    approved = Column(Boolean, default=False, nullable=False)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Impact assessment
    impact_assessment = Column(JSONB, default=lambda: {}, nullable=False)
    risk_level = Column(String(50), default="medium", nullable=False)

    # Metadata
    override_metadata = Column(JSONB, default=lambda: {}, nullable=False)

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

    # Relationships
    assessment_flow = relationship(
        "AssessmentFlow", back_populates="application_overrides"
    )

    def __repr__(self):
        return (
            f"<ApplicationArchitectureOverride(id='{self.id}', "
            f"assessment_flow_id='{self.assessment_flow_id}', "
            f"application_id='{self.application_id}', type='{self.requirement_type}')>"
        )


class ApplicationComponent(Base):
    """
    Components discovered or defined within applications during assessment.

    Represents infrastructure, middleware, and application components that need
    to be considered in the migration assessment.
    """

    __tablename__ = "application_components"

    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(
        UUID(as_uuid=True), ForeignKey("assessment_flows.id"), nullable=False
    )
    application_id = Column(
        UUID(as_uuid=True), nullable=False
    )  # Reference to application

    # Component identification
    component_name = Column(String(255), nullable=False)
    component_type = Column(
        String(100), nullable=False
    )  # Uses ComponentType enum values
    description = Column(Text, nullable=True)

    # Technical details
    current_technology = Column(String(255), nullable=True)
    version = Column(String(100), nullable=True)
    configuration = Column(JSONB, default=lambda: {}, nullable=False)
    dependencies = Column(JSONB, default=lambda: [], nullable=False)

    # Assessment metrics
    complexity_score = Column(Float, nullable=True)
    business_criticality = Column(String(50), default="medium", nullable=False)
    technical_debt_score = Column(Float, nullable=True)

    # Migration considerations
    migration_readiness = Column(String(50), nullable=True)
    recommended_approach = Column(Text, nullable=True)
    estimated_effort = Column(String(100), nullable=True)

    # Status and progress
    assessment_status = Column(String(50), default="not_started", nullable=False)
    assessment_progress = Column(Float, default=0.0, nullable=False)

    # Metadata and discovery info
    discovered_by = Column(String(100), nullable=True)  # automated, manual, etc.
    discovery_metadata = Column(JSONB, default=lambda: {}, nullable=False)
    component_metadata = Column(JSONB, default=lambda: {}, nullable=False)

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

    # Relationships
    assessment_flow = relationship(
        "AssessmentFlow", back_populates="application_components"
    )

    # Component treatments (6R decisions, etc.)
    treatments = relationship(
        "ComponentTreatment",
        back_populates="component",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<ApplicationComponent(id='{self.id}', "
            f"assessment_flow_id='{self.assessment_flow_id}', "
            f"name='{self.component_name}', type='{self.component_type}')>"
        )


class ComponentTreatment(Base):
    """
    Treatment plans for individual components (6R strategies, modernization plans).

    Defines the recommended migration strategy and specific treatment plans
    for each component identified in the assessment.
    """

    __tablename__ = "component_treatments"

    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(
        UUID(as_uuid=True), ForeignKey("assessment_flows.id"), nullable=False
    )
    component_id = Column(
        UUID(as_uuid=True), ForeignKey("application_components.id"), nullable=False
    )

    # Treatment strategy
    treatment_type = Column(
        String(100), nullable=False
    )  # 6r_strategy, modernization, etc.
    strategy = Column(String(100), nullable=False)  # rehost, refactor, etc.
    approach = Column(String(255), nullable=True)

    # Analysis and reasoning
    analysis = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    assumptions = Column(JSONB, default=lambda: [], nullable=False)

    # Confidence and risk
    confidence_score = Column(Float, nullable=True)
    risk_assessment = Column(JSONB, default=lambda: {}, nullable=False)
    risk_level = Column(String(50), default="medium", nullable=False)

    # Implementation details
    implementation_plan = Column(JSONB, default=lambda: {}, nullable=False)
    prerequisites = Column(JSONB, default=lambda: [], nullable=False)
    success_criteria = Column(JSONB, default=lambda: [], nullable=False)

    # Effort and timeline
    estimated_effort = Column(String(100), nullable=True)
    estimated_duration = Column(String(100), nullable=True)
    complexity_factors = Column(JSONB, default=lambda: [], nullable=False)

    # Dependencies and ordering
    dependencies = Column(JSONB, default=lambda: [], nullable=False)
    execution_order = Column(Integer, nullable=True)
    parallel_execution = Column(Boolean, default=True, nullable=False)

    # Status and progress
    status = Column(String(50), default="planned", nullable=False)
    progress = Column(Float, default=0.0, nullable=False)

    # Metadata
    task_metadata = Column(JSONB, default=lambda: {}, nullable=False)

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

    # Relationships
    assessment_flow = relationship(
        "AssessmentFlow", back_populates="component_treatments"
    )
    component = relationship("ApplicationComponent", back_populates="treatments")

    def __repr__(self):
        return (
            f"<ComponentTreatment(id='{self.id}', "
            f"component_id='{self.component_id}', "
            f"strategy='{self.strategy}', status='{self.status}')>"
        )
