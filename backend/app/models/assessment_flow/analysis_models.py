"""
Assessment Flow Analysis Models
Models for technical debt analysis, 6R decisions, and learning feedback.
"""

import uuid

from sqlalchemy import (
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
from .enums_and_exceptions import TechDebtSeverity


class TechDebtAnalysis(Base):
    """
    Technical debt analysis results for applications and components.

    Stores detailed analysis of technical debt, including severity assessments,
    impact analysis, and remediation recommendations.
    """

    __tablename__ = "tech_debt_analysis"

    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(
        UUID(as_uuid=True), ForeignKey("migration.assessment_flows.id"), nullable=False
    )
    application_id = Column(
        UUID(as_uuid=True), nullable=False
    )  # Reference to application
    component_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # Optional component reference

    # Debt classification
    debt_type = Column(String(100), nullable=False)  # code, architecture, data, etc.
    debt_category = Column(
        String(100), nullable=False
    )  # maintainability, security, etc.
    severity = Column(String(50), default=TechDebtSeverity.MEDIUM.value, nullable=False)

    # Analysis details
    description = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    impact_analysis = Column(JSONB, default=lambda: {}, nullable=False)

    # Metrics and scoring
    debt_score = Column(Float, nullable=True)  # 0-100 scale
    impact_score = Column(Float, nullable=True)  # Business impact
    effort_score = Column(Float, nullable=True)  # Remediation effort
    priority_score = Column(Float, nullable=True)  # Overall priority

    # Remediation planning
    remediation_strategy = Column(Text, nullable=True)
    estimated_effort = Column(String(100), nullable=True)
    recommended_timeline = Column(String(100), nullable=True)
    prerequisites = Column(JSONB, default=lambda: [], nullable=False)

    # Risk and dependencies
    risk_factors = Column(JSONB, default=lambda: [], nullable=False)
    dependencies = Column(JSONB, default=lambda: [], nullable=False)
    affected_components = Column(JSONB, default=lambda: [], nullable=False)

    # Analysis metadata
    analysis_method = Column(String(100), nullable=True)  # automated, manual, hybrid
    confidence_level = Column(Float, nullable=True)  # 0-1 scale
    evidence = Column(JSONB, default=lambda: [], nullable=False)

    # Status tracking
    status = Column(String(50), default="identified", nullable=False)
    resolution_status = Column(String(50), nullable=True)

    # Metadata
    risk_metadata = Column(JSONB, default=lambda: {}, nullable=False)

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
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    assessment_flow = relationship(
        "AssessmentFlow", back_populates="tech_debt_analyses"
    )

    def __repr__(self):
        return (
            f"<TechDebtAnalysis(id='{self.id}', "
            f"assessment_flow_id='{self.assessment_flow_id}', "
            f"type='{self.debt_type}', severity='{self.severity}')>"
        )


class SixRDecision(Base):
    """
    6R migration strategy decisions for applications and components.

    Stores the recommended 6R strategy (Rehost, Refactor, Rearchitect, Rebuild,
    Replace, Retain) along with detailed analysis and reasoning.
    """

    __tablename__ = "sixr_decisions"

    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(
        UUID(as_uuid=True), ForeignKey("migration.assessment_flows.id"), nullable=False
    )
    application_id = Column(
        UUID(as_uuid=True), nullable=False
    )  # Reference to application
    component_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # Optional component reference

    # Decision core
    sixr_strategy = Column(String(50), nullable=False)  # rehost, refactor, etc.
    decision_rationale = Column(Text, nullable=True)
    alternative_strategies = Column(JSONB, default=lambda: [], nullable=False)

    # Analysis and confidence
    analysis_details = Column(JSONB, default=lambda: {}, nullable=False)
    confidence_score = Column(Float, nullable=True)  # 0-1 scale
    risk_assessment = Column(JSONB, default=lambda: {}, nullable=False)

    # Implementation planning
    implementation_approach = Column(Text, nullable=True)
    estimated_effort = Column(String(100), nullable=True)
    estimated_duration = Column(String(100), nullable=True)
    estimated_cost = Column(Float, nullable=True)

    # Dependencies and constraints
    dependencies = Column(JSONB, default=lambda: [], nullable=False)
    constraints = Column(JSONB, default=lambda: [], nullable=False)
    assumptions = Column(JSONB, default=lambda: [], nullable=False)

    # Success criteria and validation
    success_criteria = Column(JSONB, default=lambda: [], nullable=False)
    validation_plan = Column(JSONB, default=lambda: {}, nullable=False)
    rollback_plan = Column(Text, nullable=True)

    # Business alignment
    business_value = Column(Text, nullable=True)
    business_priority = Column(Integer, nullable=True)  # 1-10 scale
    stakeholder_alignment = Column(JSONB, default=lambda: {}, nullable=False)

    # Status and execution
    decision_status = Column(String(50), default="recommended", nullable=False)
    implementation_status = Column(String(50), default="not_started", nullable=False)
    approval_status = Column(String(50), default="pending", nullable=False)

    # Decision tracking
    decision_date = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    decided_by = Column(String(255), nullable=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    decision_metadata = Column(JSONB, default=lambda: {}, nullable=False)

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
    assessment_flow = relationship("AssessmentFlow", back_populates="sixr_decisions")

    def __repr__(self):
        return (
            f"<SixRDecision(id='{self.id}', "
            f"assessment_flow_id='{self.assessment_flow_id}', "
            f"strategy='{self.sixr_strategy}', status='{self.decision_status}')>"
        )


class AssessmentLearningFeedback(Base):
    """
    Learning feedback and insights captured during assessment processes.

    Stores feedback, lessons learned, and insights that can improve future
    assessment workflows and decision-making processes.
    """

    __tablename__ = "assessment_learning_feedback"

    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(
        UUID(as_uuid=True), ForeignKey("migration.assessment_flows.id"), nullable=False
    )

    # Feedback classification
    feedback_type = Column(String(100), nullable=False)  # process, decision, tool, etc.
    category = Column(
        String(100), nullable=False
    )  # accuracy, efficiency, quality, etc.
    source = Column(String(100), nullable=True)  # human, automated, hybrid

    # Feedback content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    insights = Column(JSONB, default=lambda: [], nullable=False)
    recommendations = Column(JSONB, default=lambda: [], nullable=False)

    # Context and scope
    context_data = Column(JSONB, default=lambda: {}, nullable=False)
    affected_components = Column(JSONB, default=lambda: [], nullable=False)
    scope = Column(String(100), nullable=True)  # component, application, engagement

    # Quality and impact metrics
    quality_score = Column(Float, nullable=True)  # 0-10 scale
    impact_level = Column(String(50), default="medium", nullable=False)
    actionability_score = Column(
        Float, nullable=True
    )  # How actionable is this feedback

    # Processing and status
    processing_status = Column(String(50), default="new", nullable=False)
    review_status = Column(String(50), default="pending", nullable=False)
    implementation_status = Column(String(50), default="not_applicable", nullable=False)

    # Metadata and tracking
    recommendation_metadata = Column(JSONB, default=lambda: {}, nullable=False)
    tags = Column(JSONB, default=lambda: [], nullable=False)

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
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    assessment_flow = relationship("AssessmentFlow", back_populates="learning_feedback")

    def __repr__(self):
        return (
            f"<AssessmentLearningFeedback(id='{self.id}', "
            f"assessment_flow_id='{self.assessment_flow_id}', "
            f"type='{self.feedback_type}', title='{self.title[:50]}...')>"
        )
