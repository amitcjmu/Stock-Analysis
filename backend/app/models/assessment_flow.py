"""
Assessment Flow models for the Assessment Flow feature.
Supports flow-based assessment with multi-tenant architecture.
"""

try:
    from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum, Boolean, ForeignKey, Float
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Create dummy classes for type hints
    Column = Integer = String = DateTime = Text = JSON = Enum = Boolean = ForeignKey = Float = object
    def relationship(*args, **kwargs):
        return None
    class func:
        @staticmethod
        def now():
            return None

import enum
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from app.core.database import Base
except ImportError:
    Base = object


class AssessmentPhase(str, enum.Enum):
    """Assessment Flow phases enumeration."""
    INITIALIZATION = "initialization"
    ARCHITECTURE_MINIMUMS = "architecture_minimums"
    TECH_DEBT_ANALYSIS = "tech_debt_analysis" 
    COMPONENT_SIXR_STRATEGIES = "component_sixr_strategies"
    APP_ON_PAGE_GENERATION = "app_on_page_generation"
    FINALIZATION = "finalization"


class AssessmentFlowStatus(str, enum.Enum):
    """Assessment Flow status enumeration."""
    INITIALIZED = "initialized"
    PROCESSING = "processing"
    PAUSED_FOR_USER_INPUT = "paused_for_user_input"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class AssessmentFlowState(Base):
    """Assessment Flow state management model."""
    
    __tablename__ = "assessment_flow_states"
    
    # Primary identifier
    flow_id = Column(String(255), primary_key=True, index=True)
    
    # Multi-tenant isolation
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Flow status and progress
    status = Column(Enum(AssessmentFlowStatus), default=AssessmentFlowStatus.INITIALIZED, nullable=False)
    current_phase = Column(Enum(AssessmentPhase), default=AssessmentPhase.INITIALIZATION, nullable=False)
    next_phase = Column(Enum(AssessmentPhase), nullable=True)
    progress = Column(Integer, default=0)  # 0-100 percentage
    
    # Flow configuration
    selected_application_ids = Column(JSON, nullable=False)  # List of application IDs for assessment
    pause_points = Column(JSON, default=list)  # List of phases where user input is required
    
    # User interaction tracking
    user_inputs = Column(JSON, default=dict)  # User inputs collected during flow
    last_user_interaction = Column(DateTime(timezone=True))
    
    # Phase results storage
    phase_results = Column(JSON, default=dict)  # Results from each completed phase
    
    # Architecture standards capture
    architecture_captured = Column(Boolean, default=False)
    engagement_standards = Column(JSON, default=dict)  # Engagement-level architecture standards
    application_overrides = Column(JSON, default=dict)  # Application-specific overrides
    
    # Component analysis results
    identified_components = Column(JSON, default=dict)  # Component identification per application
    tech_debt_analysis = Column(JSON, default=dict)  # Tech debt analysis per application
    
    # 6R decision results
    sixr_decisions = Column(JSON, default=dict)  # 6R decisions per application/component
    app_on_page_data = Column(JSON, default=dict)  # Generated app-on-page data
    
    # Finalization and handoff
    apps_ready_for_planning = Column(JSON, default=list)  # Applications ready for Planning Flow
    finalized_at = Column(DateTime(timezone=True))
    
    # Error handling
    error_details = Column(JSON)
    retry_count = Column(Integer, default=0)
    
    # Audit fields
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")
    
    def __repr__(self):
        return f"<AssessmentFlowState(flow_id='{self.flow_id}', status='{self.status}', phase='{self.current_phase}')>"
    
    @property
    def is_paused(self) -> bool:
        """Check if flow is paused for user input."""
        return self.status == AssessmentFlowStatus.PAUSED_FOR_USER_INPUT
    
    @property
    def is_completed(self) -> bool:
        """Check if flow is completed."""
        return self.status == AssessmentFlowStatus.COMPLETED
    
    @property
    def is_active(self) -> bool:
        """Check if flow is actively processing."""
        return self.status in [AssessmentFlowStatus.PROCESSING, AssessmentFlowStatus.PAUSED_FOR_USER_INPUT]
    
    def get_phase_results(self, phase: AssessmentPhase) -> Dict[str, Any]:
        """Get results for specific phase."""
        return self.phase_results.get(phase.value, {})
    
    def set_phase_results(self, phase: AssessmentPhase, results: Dict[str, Any]):
        """Set results for specific phase."""
        if not self.phase_results:
            self.phase_results = {}
        self.phase_results[phase.value] = results
    
    def add_user_input(self, phase: AssessmentPhase, input_data: Dict[str, Any]):
        """Add user input for specific phase."""
        if not self.user_inputs:
            self.user_inputs = {}
        self.user_inputs[phase.value] = input_data
        self.last_user_interaction = datetime.utcnow()
    
    def get_application_components(self, app_id: str) -> Dict[str, Any]:
        """Get identified components for specific application."""
        return self.identified_components.get(app_id, {})
    
    def set_application_components(self, app_id: str, components: Dict[str, Any]):
        """Set identified components for specific application."""
        if not self.identified_components:
            self.identified_components = {}
        self.identified_components[app_id] = components
    
    def get_tech_debt_analysis(self, app_id: str) -> Dict[str, Any]:
        """Get tech debt analysis for specific application."""
        return self.tech_debt_analysis.get(app_id, {})
    
    def set_tech_debt_analysis(self, app_id: str, analysis: Dict[str, Any]):
        """Set tech debt analysis for specific application."""
        if not self.tech_debt_analysis:
            self.tech_debt_analysis = {}
        self.tech_debt_analysis[app_id] = analysis
    
    def get_sixr_decision(self, app_id: str) -> Dict[str, Any]:
        """Get 6R decision for specific application."""
        return self.sixr_decisions.get(app_id, {})
    
    def set_sixr_decision(self, app_id: str, decision: Dict[str, Any]):
        """Set 6R decision for specific application."""
        if not self.sixr_decisions:
            self.sixr_decisions = {}
        self.sixr_decisions[app_id] = decision
    
    def mark_app_ready_for_planning(self, app_id: str):
        """Mark application as ready for Planning Flow."""
        if not self.apps_ready_for_planning:
            self.apps_ready_for_planning = []
        if app_id not in self.apps_ready_for_planning:
            self.apps_ready_for_planning.append(app_id)


class AssessmentArchitectureStandard(Base):
    """Architecture standards for assessment flows."""
    
    __tablename__ = "assessment_architecture_standards"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Multi-tenant isolation
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Standards metadata
    standard_type = Column(String(100), nullable=False)  # e.g., "cloud_provider", "framework", "security"
    domain = Column(String(100))  # e.g., "infrastructure", "application", "data"
    
    # Standards content
    standard_definition = Column(JSON, nullable=False)  # The actual standard definition
    enforcement_level = Column(String(50), default="recommended")  # required, recommended, optional
    
    # Template and customization
    is_template = Column(Boolean, default=False)  # Whether this is a reusable template
    customizable_fields = Column(JSON, default=list)  # Fields that can be customized per application
    
    # Metadata
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")
    
    def __repr__(self):
        return f"<AssessmentArchitectureStandard(id={self.id}, type='{self.standard_type}', domain='{self.domain}')>"


class AssessmentApplicationOverride(Base):
    """Application-specific overrides for architecture standards."""
    
    __tablename__ = "assessment_application_overrides"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Multi-tenant isolation
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    flow_id = Column(String(255), ForeignKey('assessment_flow_states.flow_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Application context
    application_id = Column(String(255), nullable=False)  # Reference to application being assessed
    
    # Override details
    standard_id = Column(PostgresUUID(as_uuid=True), ForeignKey('assessment_architecture_standards.id'), nullable=False)
    override_data = Column(JSON, nullable=False)  # Override values
    override_reason = Column(Text)  # Justification for override
    
    # Approval tracking
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(String(255))
    approved_at = Column(DateTime(timezone=True))
    approval_comments = Column(Text)
    
    # Metadata
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client_account = relationship("ClientAccount")
    flow_state = relationship("AssessmentFlowState")
    standard = relationship("AssessmentArchitectureStandard")
    
    def __repr__(self):
        return f"<AssessmentApplicationOverride(id={self.id}, app_id='{self.application_id}', standard_id={self.standard_id})>"