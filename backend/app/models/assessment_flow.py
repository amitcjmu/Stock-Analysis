"""
Assessment Flow Models - Database Foundation
Complete SQLAlchemy models for assessment flow architecture with multi-tenant support
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, Float, ForeignKey, CheckConstraint, UniqueConstraint, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AssessmentFlowStatus(str, Enum):
    """Assessment flow status states."""
    INITIALIZED = "initialized"
    PROCESSING = "processing"
    PAUSED_FOR_USER_INPUT = "paused_for_user_input"
    COMPLETED = "completed"
    ERROR = "error"


class AssessmentPhase(str, Enum):
    """Assessment flow phases."""
    INITIALIZATION = "initialization"
    ARCHITECTURE_MINIMUMS = "architecture_minimums"
    TECH_DEBT_ANALYSIS = "tech_debt_analysis"
    COMPONENT_SIXR_STRATEGIES = "component_sixr_strategies"
    APP_ON_PAGE_GENERATION = "app_on_page_generation"
    FINALIZATION = "finalization"

class AssessmentFlow(Base):
    """
    Main assessment flow tracking with pause points and navigation state.
    Supports component-level 6R treatments with flexible architecture.
    """
    __tablename__ = 'assessment_flows'

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Multi-tenant isolation
    client_account_id = Column(UUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Flow configuration
    selected_application_ids = Column(JSONB, nullable=False)  # List of application UUIDs
    architecture_captured = Column(Boolean, default=False, nullable=False)
    
    # Flow state management
    status = Column(String(50), nullable=False, default='initialized', index=True)
    progress = Column(Integer, default=0, nullable=False)
    current_phase = Column(String(100), nullable=True, index=True)
    next_phase = Column(String(100), nullable=True, index=True)
    
    # User interaction tracking
    pause_points = Column(JSONB, default=list, nullable=False)  # List of pause point identifiers
    user_inputs = Column(JSONB, default=dict, nullable=False)  # Phase-specific user inputs
    phase_results = Column(JSONB, default=dict, nullable=False)  # Phase completion results
    agent_insights = Column(JSONB, default=list, nullable=False)  # Agent-generated insights
    
    # Planning readiness
    apps_ready_for_planning = Column(JSONB, default=list, nullable=False)  # Apps ready for planning flow
    
    # Timestamps
    last_user_interaction = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('progress >= 0 AND progress <= 100', name='valid_progress'),
    )
    
    # Relationships
    # Note: architecture_standards are linked via engagement_id, not directly
    application_overrides = relationship("ApplicationArchitectureOverride", back_populates="assessment_flow", cascade="all, delete-orphan")
    application_components = relationship("ApplicationComponent", back_populates="assessment_flow", cascade="all, delete-orphan")
    tech_debt_analysis = relationship("TechDebtAnalysis", back_populates="assessment_flow", cascade="all, delete-orphan")
    component_treatments = relationship("ComponentTreatment", back_populates="assessment_flow", cascade="all, delete-orphan")
    sixr_decisions = relationship("SixRDecision", back_populates="assessment_flow", cascade="all, delete-orphan")
    learning_feedback = relationship("AssessmentLearningFeedback", back_populates="assessment_flow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AssessmentFlow(id={self.id}, status='{self.status}', progress={self.progress})>"


class EngagementArchitectureStandard(Base):
    """
    Engagement-level architecture standards with version management.
    Defines minimum requirements and supported technology versions.
    """
    __tablename__ = 'engagement_architecture_standards'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Standard definition
    requirement_type = Column(String(100), nullable=False)  # e.g., 'java_versions', 'security_standards'
    description = Column(Text, nullable=True)
    mandatory = Column(Boolean, default=True, nullable=False)
    
    # Version and requirement details
    supported_versions = Column(JSONB, nullable=True)  # {"java": "11+", "spring": "2.5+"}
    requirement_details = Column(JSONB, nullable=True)  # Additional requirement specifications
    
    # Audit trail
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('engagement_id', 'requirement_type', name='unique_engagement_requirement'),
    )
    
    # Relationships
    # Note: Related to AssessmentFlow via engagement_id, not direct foreign key
    application_overrides = relationship("ApplicationArchitectureOverride", back_populates="standard")

    def __repr__(self):
        return f"<EngagementArchitectureStandard(engagement_id={self.engagement_id}, type='{self.requirement_type}')>"


class ApplicationArchitectureOverride(Base):
    """
    Application-specific architecture overrides with business rationale.
    Allows exceptions to engagement-level standards with proper approval.
    """
    __tablename__ = 'application_architecture_overrides'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(UUID(as_uuid=True), ForeignKey('assessment_flows.id', ondelete='CASCADE'), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    standard_id = Column(UUID(as_uuid=True), ForeignKey('engagement_architecture_standards.id', ondelete='SET NULL'), nullable=True)
    
    # Override details
    override_type = Column(String(100), nullable=False)  # exception, modification, addition
    override_details = Column(JSONB, nullable=True)
    rationale = Column(Text, nullable=True)
    approved_by = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("override_type IN ('exception', 'modification', 'addition')", name='valid_override_type'),
    )
    
    # Relationships
    assessment_flow = relationship("AssessmentFlow", back_populates="application_overrides")
    standard = relationship("EngagementArchitectureStandard", back_populates="application_overrides")

    def __repr__(self):
        return f"<ApplicationArchitectureOverride(app_id={self.application_id}, type='{self.override_type}')>"


class ApplicationComponent(Base):
    """
    Flexible component identification beyond 3-tier architecture.
    Supports discovery of various component types with technology stacks.
    """
    __tablename__ = 'application_components'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(UUID(as_uuid=True), ForeignKey('assessment_flows.id', ondelete='CASCADE'), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Component identification
    component_name = Column(String(255), nullable=False)
    component_type = Column(String(100), nullable=False)  # frontend, middleware, backend, service, etc.
    
    # Technical details
    technology_stack = Column(JSONB, nullable=True)  # Technology details and versions
    dependencies = Column(JSONB, nullable=True)  # Other components this depends on
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('assessment_flow_id', 'application_id', 'component_name', name='unique_app_component'),
    )
    
    # Relationships
    assessment_flow = relationship("AssessmentFlow", back_populates="application_components")
    tech_debt_items = relationship("TechDebtAnalysis", back_populates="component")
    treatments = relationship("ComponentTreatment", back_populates="component")

    def __repr__(self):
        return f"<ApplicationComponent(name='{self.component_name}', type='{self.component_type}')>"


class TechDebtAnalysis(Base):
    """
    Component-aware tech debt analysis with severity and remediation tracking.
    Enables component-level debt assessment for migration planning.
    """
    __tablename__ = 'tech_debt_analysis'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(UUID(as_uuid=True), ForeignKey('assessment_flows.id', ondelete='CASCADE'), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    component_id = Column(UUID(as_uuid=True), ForeignKey('application_components.id', ondelete='SET NULL'), nullable=True)
    
    # Debt classification
    debt_category = Column(String(100), nullable=False)  # e.g., 'security', 'performance', 'maintainability'
    severity = Column(String(20), nullable=False, index=True)  # critical, high, medium, low
    description = Column(Text, nullable=False)
    
    # Impact assessment
    remediation_effort_hours = Column(Integer, nullable=True)
    impact_on_migration = Column(Text, nullable=True)
    tech_debt_score = Column(Float, nullable=True)  # Quantified score for prioritization
    
    # Agent tracking
    detected_by_agent = Column(String(100), nullable=True)
    agent_confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("severity IN ('critical', 'high', 'medium', 'low')", name='valid_severity'),
        CheckConstraint('agent_confidence >= 0 AND agent_confidence <= 1', name='valid_agent_confidence'),
    )
    
    # Relationships
    assessment_flow = relationship("AssessmentFlow", back_populates="tech_debt_analysis")
    component = relationship("ApplicationComponent", back_populates="tech_debt_items")

    def __repr__(self):
        return f"<TechDebtAnalysis(category='{self.debt_category}', severity='{self.severity}')>"


class ComponentTreatment(Base):
    """
    Individual component 6R decisions with compatibility validation.
    Enables component-level strategy selection within applications.
    """
    __tablename__ = 'component_treatments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(UUID(as_uuid=True), ForeignKey('assessment_flows.id', ondelete='CASCADE'), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    component_id = Column(UUID(as_uuid=True), ForeignKey('application_components.id', ondelete='CASCADE'), nullable=True)
    
    # Strategy decision
    recommended_strategy = Column(String(20), nullable=False, index=True)  # 6R strategy
    rationale = Column(Text, nullable=True)
    
    # Compatibility validation
    compatibility_validated = Column(Boolean, default=False, nullable=False)
    compatibility_issues = Column(JSONB, nullable=True)  # List of compatibility concerns
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("recommended_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')", name='valid_recommended_strategy'),
        UniqueConstraint('assessment_flow_id', 'component_id', name='unique_component_treatment'),
    )
    
    # Relationships
    assessment_flow = relationship("AssessmentFlow", back_populates="component_treatments")
    component = relationship("ApplicationComponent", back_populates="treatments")

    def __repr__(self):
        return f"<ComponentTreatment(strategy='{self.recommended_strategy}', validated={self.compatibility_validated})>"


class SixRDecision(Base):
    """
    Application-level 6R decisions with component rollup and app-on-page data.
    Consolidates component treatments into overall application strategy.
    """
    __tablename__ = 'sixr_decisions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(UUID(as_uuid=True), ForeignKey('assessment_flows.id', ondelete='CASCADE'), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    application_name = Column(String(255), nullable=False)
    
    # Strategy decision
    overall_strategy = Column(String(20), nullable=False, index=True)  # 6R strategy
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    rationale = Column(Text, nullable=True)
    
    # Architecture and risk factors
    architecture_exceptions = Column(JSONB, default=list, nullable=False)  # List of architecture exceptions
    tech_debt_score = Column(Float, nullable=True)
    risk_factors = Column(JSONB, default=list, nullable=False)  # List of risk factors
    
    # Migration planning hints
    move_group_hints = Column(JSONB, default=list, nullable=False)  # Technology proximity, dependencies
    estimated_effort_hours = Column(Integer, nullable=True)
    estimated_cost = Column(Numeric(12, 2), nullable=True)
    
    # User modifications
    user_modifications = Column(JSONB, nullable=True)
    modified_by = Column(String(100), nullable=True)
    modified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Complete consolidated view
    app_on_page_data = Column(JSONB, nullable=True)  # Complete app-on-page representation
    decision_factors = Column(JSONB, nullable=True)  # Factors that influenced the decision
    
    # Planning readiness
    ready_for_planning = Column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("overall_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')", name='valid_overall_strategy'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='valid_confidence_score'),
        UniqueConstraint('assessment_flow_id', 'application_id', name='unique_app_decision'),
    )
    
    # Relationships
    assessment_flow = relationship("AssessmentFlow", back_populates="sixr_decisions")
    learning_feedback = relationship("AssessmentLearningFeedback", back_populates="decision")

    def __repr__(self):
        return f"<SixRDecision(app='{self.application_name}', strategy='{self.overall_strategy}', confidence={self.confidence_score})>"


class AssessmentLearningFeedback(Base):
    """
    Learning feedback for agent improvement from user modifications and overrides.
    Enables continuous agent learning from user decisions.
    """
    __tablename__ = 'assessment_learning_feedback'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(UUID(as_uuid=True), ForeignKey('assessment_flows.id', ondelete='CASCADE'), nullable=False, index=True)
    decision_id = Column(UUID(as_uuid=True), ForeignKey('sixr_decisions.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Learning data
    original_strategy = Column(String(20), nullable=False)  # Agent's original recommendation
    override_strategy = Column(String(20), nullable=False)  # User's override decision
    feedback_reason = Column(Text, nullable=True)  # User's rationale for change
    
    # Agent learning
    agent_id = Column(String(100), nullable=True)  # Which agent made the original decision
    learned_pattern = Column(JSONB, nullable=True)  # Pattern extracted for future learning
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("original_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')", name='valid_original_strategy'),
        CheckConstraint("override_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')", name='valid_override_strategy'),
    )
    
    # Relationships
    assessment_flow = relationship("AssessmentFlow", back_populates="learning_feedback")
    decision = relationship("SixRDecision", back_populates="learning_feedback")

    def __repr__(self):
        return f"<AssessmentLearningFeedback(original='{self.original_strategy}', override='{self.override_strategy}')>"