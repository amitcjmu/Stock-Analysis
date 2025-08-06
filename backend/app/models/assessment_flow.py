"""
Assessment Flow Models - Database Foundation
Complete SQLAlchemy models for assessment flow architecture with multi-tenant support

Includes both database models and in-memory state models for CrewAI flow compatibility.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

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

    __tablename__ = "assessment_flows"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Multi-tenant isolation
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Flow configuration - using fields that exist in the database table
    flow_name = Column(String(255), nullable=False)
    flow_status = Column(String(50), nullable=False, default="initialized", index=True)
    flow_configuration = Column(JSONB, nullable=True)  # Store all flow data here as JSON

    # Timestamps - using fields that exist in the database table
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Properties to provide backward compatibility with the expected interface
    @property
    def selected_application_ids(self):
        return self.flow_configuration.get('selected_application_ids', []) if self.flow_configuration else []
    
    @property
    def architecture_captured(self):
        return self.flow_configuration.get('architecture_captured', False) if self.flow_configuration else False
    
    @property
    def status(self):
        return self.flow_status
    
    @property
    def progress(self):
        return self.flow_configuration.get('progress', 0) if self.flow_configuration else 0
    
    @property
    def current_phase(self):
        return self.flow_configuration.get('current_phase') if self.flow_configuration else None
    
    @property
    def next_phase(self):
        return self.flow_configuration.get('next_phase') if self.flow_configuration else None
    
    @property
    def pause_points(self):
        return self.flow_configuration.get('pause_points', []) if self.flow_configuration else []
    
    @property
    def user_inputs(self):
        return self.flow_configuration.get('user_inputs', {}) if self.flow_configuration else {}
    
    @property
    def phase_results(self):
        return self.flow_configuration.get('phase_results', {}) if self.flow_configuration else {}
    
    @property
    def agent_insights(self):
        return self.flow_configuration.get('agent_insights', []) if self.flow_configuration else []
    
    @property
    def apps_ready_for_planning(self):
        return self.flow_configuration.get('apps_ready_for_planning', []) if self.flow_configuration else []
    
    @property
    def last_user_interaction(self):
        last_interaction = self.flow_configuration.get('last_user_interaction') if self.flow_configuration else None
        if last_interaction:
            from datetime import datetime
            return datetime.fromisoformat(last_interaction)
        return None
    
    @property
    def completed_at(self):
        completed = self.flow_configuration.get('completed_at') if self.flow_configuration else None
        if completed:
            from datetime import datetime
            return datetime.fromisoformat(completed)
        return None

    # Constraints - removed progress constraint since it's now in JSON
    __table_args__ = tuple()

    # Relationships (using string references to avoid forward reference issues)
    # Note: architecture_standards are linked via engagement_id, not directly
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
    tech_debt_analysis = relationship(
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
        "SixRDecision", back_populates="assessment_flow", cascade="all, delete-orphan"
    )
    learning_feedback = relationship(
        "AssessmentLearningFeedback",
        back_populates="assessment_flow",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<AssessmentFlow(id={self.id}, status='{self.status}', progress={self.progress})>"


class EngagementArchitectureStandard(Base):
    """
    Engagement-level architecture standards with version management.
    Defines minimum requirements and supported technology versions.
    """

    __tablename__ = "engagement_architecture_standards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Standard definition
    requirement_type = Column(
        String(100), nullable=False
    )  # e.g., 'java_versions', 'security_standards'
    description = Column(Text, nullable=True)
    mandatory = Column(Boolean, default=True, nullable=False)

    # Version and requirement details
    supported_versions = Column(
        JSONB, nullable=True
    )  # {"java": "11+", "spring": "2.5+"}
    requirement_details = Column(
        JSONB, nullable=True
    )  # Additional requirement specifications

    # Audit trail
    created_by = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "engagement_id", "requirement_type", name="unique_engagement_requirement"
        ),
    )

    # Relationships
    # Note: Related to AssessmentFlow via engagement_id, not direct foreign key
    application_overrides = relationship(
        "ApplicationArchitectureOverride", back_populates="standard"
    )

    def __repr__(self):
        return f"<EngagementArchitectureStandard(engagement_id={self.engagement_id}, type='{self.requirement_type}')>"


class ApplicationArchitectureOverride(Base):
    """
    Application-specific architecture overrides with business rationale.
    Allows exceptions to engagement-level standards with proper approval.
    """

    __tablename__ = "application_architecture_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assessment_flows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    standard_id = Column(
        UUID(as_uuid=True),
        ForeignKey("engagement_architecture_standards.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Override details
    override_type = Column(
        String(100), nullable=False
    )  # exception, modification, addition
    override_details = Column(JSONB, nullable=True)
    rationale = Column(Text, nullable=True)
    approved_by = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "override_type IN ('exception', 'modification', 'addition')",
            name="valid_override_type",
        ),
    )

    # Relationships
    assessment_flow = relationship(
        "AssessmentFlow", back_populates="application_overrides"
    )
    standard = relationship(
        "EngagementArchitectureStandard", back_populates="application_overrides"
    )

    def __repr__(self):
        return f"<ApplicationArchitectureOverride(app_id={self.application_id}, type='{self.override_type}')>"


class ApplicationComponent(Base):
    """
    Flexible component identification beyond 3-tier architecture.
    Supports discovery of various component types with technology stacks.
    """

    __tablename__ = "application_components"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assessment_flows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Component identification
    component_name = Column(String(255), nullable=False)
    component_type = Column(
        String(100), nullable=False
    )  # frontend, middleware, backend, service, etc.

    # Technical details
    technology_stack = Column(JSONB, nullable=True)  # Technology details and versions
    dependencies = Column(JSONB, nullable=True)  # Other components this depends on

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "assessment_flow_id",
            "application_id",
            "component_name",
            name="unique_app_component",
        ),
    )

    # Relationships
    assessment_flow = relationship(
        "AssessmentFlow", back_populates="application_components"
    )
    tech_debt_items = relationship("TechDebtAnalysis", back_populates="component")
    treatments = relationship("ComponentTreatment", back_populates="component")

    def __repr__(self):
        return f"<ApplicationComponent(name='{self.component_name}', type='{self.component_type}')>"


class TechDebtAnalysis(Base):
    """
    Component-aware tech debt analysis with severity and remediation tracking.
    Enables component-level debt assessment for migration planning.
    """

    __tablename__ = "tech_debt_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assessment_flows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    component_id = Column(
        UUID(as_uuid=True),
        ForeignKey("application_components.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Debt classification
    debt_category = Column(
        String(100), nullable=False
    )  # e.g., 'security', 'performance', 'maintainability'
    severity = Column(
        String(20), nullable=False, index=True
    )  # critical, high, medium, low
    description = Column(Text, nullable=False)

    # Impact assessment
    remediation_effort_hours = Column(Integer, nullable=True)
    impact_on_migration = Column(Text, nullable=True)
    tech_debt_score = Column(
        Float, nullable=True
    )  # Quantified score for prioritization

    # Agent tracking
    detected_by_agent = Column(String(100), nullable=True)
    agent_confidence = Column(Float, nullable=True)  # 0.0 to 1.0

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "severity IN ('critical', 'high', 'medium', 'low')", name="valid_severity"
        ),
        CheckConstraint(
            "agent_confidence >= 0 AND agent_confidence <= 1",
            name="valid_agent_confidence",
        ),
    )

    # Relationships
    assessment_flow = relationship(
        "AssessmentFlow", back_populates="tech_debt_analysis"
    )
    component = relationship("ApplicationComponent", back_populates="tech_debt_items")

    def __repr__(self):
        return f"<TechDebtAnalysis(category='{self.debt_category}', severity='{self.severity}')>"


class ComponentTreatment(Base):
    """
    Individual component 6R decisions with compatibility validation.
    Enables component-level strategy selection within applications.
    """

    __tablename__ = "component_treatments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assessment_flows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    component_id = Column(
        UUID(as_uuid=True),
        ForeignKey("application_components.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Strategy decision
    recommended_strategy = Column(String(20), nullable=False, index=True)  # 6R strategy
    rationale = Column(Text, nullable=True)

    # Compatibility validation
    compatibility_validated = Column(Boolean, default=False, nullable=False)
    compatibility_issues = Column(
        JSONB, nullable=True
    )  # List of compatibility concerns

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "recommended_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')",
            name="valid_recommended_strategy",
        ),
        UniqueConstraint(
            "assessment_flow_id", "component_id", name="unique_component_treatment"
        ),
    )

    # Relationships
    assessment_flow = relationship(
        "AssessmentFlow", back_populates="component_treatments"
    )
    component = relationship("ApplicationComponent", back_populates="treatments")

    def __repr__(self):
        return f"<ComponentTreatment(strategy='{self.recommended_strategy}', validated={self.compatibility_validated})>"


class SixRDecision(Base):
    """
    Application-level 6R decisions with component rollup and app-on-page data.
    Consolidates component treatments into overall application strategy.
    """

    __tablename__ = "sixr_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assessment_flows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    application_name = Column(String(255), nullable=False)

    # Strategy decision
    overall_strategy = Column(String(20), nullable=False, index=True)  # 6R strategy
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    rationale = Column(Text, nullable=True)

    # Architecture and risk factors
    architecture_exceptions = Column(
        JSONB, default=list, nullable=False
    )  # List of architecture exceptions
    tech_debt_score = Column(Float, nullable=True)
    risk_factors = Column(JSONB, default=list, nullable=False)  # List of risk factors

    # Migration planning hints
    move_group_hints = Column(
        JSONB, default=list, nullable=False
    )  # Technology proximity, dependencies
    estimated_effort_hours = Column(Integer, nullable=True)
    estimated_cost = Column(Numeric(12, 2), nullable=True)

    # User modifications
    user_modifications = Column(JSONB, nullable=True)
    modified_by = Column(String(100), nullable=True)
    modified_at = Column(DateTime(timezone=True), nullable=True)

    # Complete consolidated view
    app_on_page_data = Column(
        JSONB, nullable=True
    )  # Complete app-on-page representation
    decision_factors = Column(
        JSONB, nullable=True
    )  # Factors that influenced the decision

    # Planning readiness
    ready_for_planning = Column(Boolean, default=False, nullable=False, index=True)

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

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "overall_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')",
            name="valid_overall_strategy",
        ),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="valid_confidence_score",
        ),
        UniqueConstraint(
            "assessment_flow_id", "application_id", name="unique_app_decision"
        ),
    )

    # Relationships
    assessment_flow = relationship("AssessmentFlow", back_populates="sixr_decisions")
    learning_feedback = relationship(
        "AssessmentLearningFeedback", back_populates="decision"
    )

    def __repr__(self):
        return f"<SixRDecision(app='{self.application_name}', strategy='{self.overall_strategy}', confidence={self.confidence_score})>"


class AssessmentLearningFeedback(Base):
    """
    Learning feedback for agent improvement from user modifications and overrides.
    Enables continuous agent learning from user decisions.
    """

    __tablename__ = "assessment_learning_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assessment_flows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sixr_decisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Learning data
    original_strategy = Column(
        String(20), nullable=False
    )  # Agent's original recommendation
    override_strategy = Column(String(20), nullable=False)  # User's override decision
    feedback_reason = Column(Text, nullable=True)  # User's rationale for change

    # Agent learning
    agent_id = Column(
        String(100), nullable=True
    )  # Which agent made the original decision
    learned_pattern = Column(
        JSONB, nullable=True
    )  # Pattern extracted for future learning

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "original_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')",
            name="valid_original_strategy",
        ),
        CheckConstraint(
            "override_strategy IN ('rewrite', 'rearchitect', 'refactor', 'replatform', 'rehost', 'repurchase', 'retire', 'retain')",
            name="valid_override_strategy",
        ),
    )

    # Relationships
    assessment_flow = relationship("AssessmentFlow", back_populates="learning_feedback")
    decision = relationship("SixRDecision", back_populates="learning_feedback")

    def __repr__(self):
        return f"<AssessmentLearningFeedback(original='{self.original_strategy}', override='{self.override_strategy}')>"


# ========================================
# IN-MEMORY STATE MODELS FOR CREWAI FLOW
# ========================================


class AssessmentStatus(str, Enum):
    """Assessment flow status for in-memory state management"""

    INITIALIZING = "initializing"
    PROCESSING = "processing"
    PAUSED_FOR_USER_INPUT = "paused_for_user_input"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"


class InMemorySixRDecision:
    """In-memory model for 6R decisions"""

    def __init__(
        self,
        application_id: str,
        application_name: str,
        component_treatments: List[Dict[str, Any]] = None,
        overall_strategy: str = None,
        confidence_score: float = 0.0,
        rationale: str = "",
        move_group_hints: List[str] = None,
        tech_debt_score: float = 0.0,
        architecture_exceptions: List[Dict[str, Any]] = None,
        risk_factors: List[str] = None,
        app_on_page_data: Dict[str, Any] = None,
    ):
        self.application_id = application_id
        self.application_name = application_name
        self.component_treatments = component_treatments or []
        self.overall_strategy = overall_strategy
        self.confidence_score = confidence_score
        self.rationale = rationale
        self.move_group_hints = move_group_hints or []
        self.tech_debt_score = tech_debt_score
        self.architecture_exceptions = architecture_exceptions or []
        self.risk_factors = risk_factors or []
        self.app_on_page_data = app_on_page_data or {}


class ArchitectureRequirementType(str, Enum):
    """Types of architecture requirements"""

    TECHNOLOGY_VERSION = "technology_version"
    SECURITY_STANDARD = "security_standard"
    COMPLIANCE_REQUIREMENT = "compliance_requirement"
    PERFORMANCE_STANDARD = "performance_standard"
    INTEGRATION_PATTERN = "integration_pattern"


class ComponentType(str, Enum):
    """Types of application components"""

    WEB_FRONTEND = "web_frontend"
    API_GATEWAY = "api_gateway"
    MICROSERVICE = "microservice"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    CACHE = "cache"
    FILE_STORAGE = "file_storage"
    BATCH_PROCESSOR = "batch_processor"
    INTEGRATION_LAYER = "integration_layer"
    MONITORING = "monitoring"
    REST_API = "rest_api"
    RELATIONAL_DATABASE = "relational_database"
    CUSTOM = "custom"


class TechDebtSeverity(str, Enum):
    """Severity levels for technical debt"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AssessmentFlowError(Exception):
    """Custom exception for assessment flow errors"""

    pass


class CrewExecutionError(Exception):
    """Custom exception for crew execution errors"""

    pass


class AssessmentFlowState:
    """In-memory state model for assessment flow execution"""

    def __init__(
        self,
        flow_id: str,
        client_account_id: str,
        engagement_id: str,
        user_id: Optional[str] = None,
        current_phase: AssessmentPhase = AssessmentPhase.INITIALIZATION,
        next_phase: AssessmentPhase = None,
        status: AssessmentStatus = AssessmentStatus.INITIALIZING,
        progress: float = 0.0,
        selected_application_ids: List[str] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.flow_id = flow_id
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.user_id = user_id
        self.current_phase = current_phase
        self.next_phase = next_phase
        self.status = status
        self.progress = progress
        self.selected_application_ids = selected_application_ids or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.completed_at: Optional[datetime] = None

        # Phase-specific data
        self.phase_results: Dict[str, Any] = {}
        self.user_inputs: Dict[str, Any] = {}
        self.pause_points: List[str] = []

        # Assessment-specific data
        self.engagement_architecture_standards: List[Dict[str, Any]] = []
        self.application_components: Dict[str, List[Dict[str, Any]]] = {}
        self.tech_debt_analysis: Dict[str, List[Dict[str, Any]]] = {}
        self.component_tech_debt: Dict[str, Dict[str, float]] = {}
        self.sixr_decisions: Dict[str, InMemorySixRDecision] = {}
        self.apps_ready_for_planning: List[str] = []

        # Interaction tracking
        self.last_user_interaction: Optional[datetime] = None
        self.errors: List[Dict[str, Any]] = []

    def add_error(self, phase: str, error_message: str):
        """Add an error to the flow state"""
        self.errors.append(
            {
                "phase": phase,
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        self.status = AssessmentStatus.ERROR
        self.updated_at = datetime.utcnow()

    def validate_component_compatibility(self, application_id: str) -> List[str]:
        """Validate component compatibility for an application"""
        # Placeholder implementation
        issues = []

        components = self.application_components.get(application_id, [])
        if len(components) > 10:
            issues.append("High component count may indicate complexity")

        return issues

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            "flow_id": self.flow_id,
            "client_account_id": self.client_account_id,
            "engagement_id": self.engagement_id,
            "user_id": self.user_id,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "next_phase": self.next_phase.value if self.next_phase else None,
            "status": self.status.value if self.status else None,
            "progress": self.progress,
            "selected_application_ids": self.selected_application_ids,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "phase_results": self.phase_results,
            "user_inputs": self.user_inputs,
            "pause_points": self.pause_points,
            "engagement_architecture_standards": self.engagement_architecture_standards,
            "application_components": self.application_components,
            "tech_debt_analysis": self.tech_debt_analysis,
            "component_tech_debt": self.component_tech_debt,
            "sixr_decisions": {
                app_id: {
                    "application_id": decision.application_id,
                    "application_name": decision.application_name,
                    "component_treatments": decision.component_treatments,
                    "overall_strategy": decision.overall_strategy,
                    "confidence_score": decision.confidence_score,
                    "rationale": decision.rationale,
                    "move_group_hints": decision.move_group_hints,
                    "tech_debt_score": decision.tech_debt_score,
                    "architecture_exceptions": decision.architecture_exceptions,
                    "risk_factors": decision.risk_factors,
                    "app_on_page_data": decision.app_on_page_data,
                }
                for app_id, decision in self.sixr_decisions.items()
            },
            "apps_ready_for_planning": self.apps_ready_for_planning,
            "last_user_interaction": (
                self.last_user_interaction.isoformat()
                if self.last_user_interaction
                else None
            ),
            "errors": self.errors,
        }
