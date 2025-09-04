"""
Collection Flow Model

This model represents the Collection Flow entity for the Adaptive Data Collection System.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base, TimestampMixin


class AutomationTier(str, Enum):
    """Automation tier levels"""

    TIER_1 = "tier_1"  # Manual/Template-based
    TIER_2 = "tier_2"  # Script-Assisted
    TIER_3 = "tier_3"  # API-Integrated
    TIER_4 = "tier_4"  # Fully Automated


class CollectionFlowStatus(str, Enum):
    """Collection Flow status values"""

    INITIALIZED = "initialized"
    PLATFORM_DETECTION = "platform_detection"
    AUTOMATED_COLLECTION = "automated_collection"
    GAP_ANALYSIS = "gap_analysis"
    MANUAL_COLLECTION = "manual_collection"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CollectionPhase(str, Enum):
    """Collection flow phases"""

    INITIALIZATION = "initialization"
    PLATFORM_DETECTION = "platform_detection"
    AUTOMATED_COLLECTION = "automated_collection"
    GAP_ANALYSIS = "gap_analysis"
    QUESTIONNAIRE_GENERATION = "questionnaire_generation"
    MANUAL_COLLECTION = "manual_collection"
    DATA_VALIDATION = "data_validation"
    FINALIZATION = "finalization"


class CollectionFlow(Base, TimestampMixin):
    """
    Collection Flow model for tracking data collection processes.

    This model tracks the lifecycle of data collection flows, including
    automation tier, current status, quality scores, and relationships
    to other flow types.
    """

    __tablename__ = "collection_flows"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Flow identifiers
    flow_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    flow_name = Column(String(255), nullable=False)

    # Multi-tenant fields
    client_account_id = Column(
        UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True
    )
    engagement_id = Column(
        UUID(as_uuid=True), ForeignKey("engagements.id"), nullable=False, index=True
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)  # User who created the flow

    # Flow relationships
    master_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crewai_flow_state_extensions.flow_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    discovery_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("discovery_flows.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Flow configuration
    automation_tier = Column(
        SQLEnum(
            AutomationTier,
            values_callable=lambda obj: [e.value for e in obj],
            create_type=False,
        ),
        nullable=False,
        index=True,
    )
    status = Column(
        SQLEnum(
            CollectionFlowStatus,
            values_callable=lambda obj: [e.value for e in obj],
            create_type=False,
        ),
        nullable=False,
        default=CollectionFlowStatus.INITIALIZED,
        server_default="initialized",
        index=True,
    )

    # Progress tracking
    current_phase = Column(String(100), nullable=True)
    next_phase = Column(String(100), nullable=True)
    progress_percentage = Column(
        Float, nullable=False, default=0.0, server_default="0.0"
    )

    # Quality metrics
    collection_quality_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Configuration and state
    flow_metadata = Column(
        "metadata", JSONB, nullable=False, default={}, server_default="{}"
    )
    collection_config = Column(JSONB, nullable=False, default={}, server_default="{}")
    phase_state = Column(JSONB, nullable=False, default={}, server_default="{}")

    # User interaction tracking
    pause_points = Column(
        JSONB, default=list, nullable=False
    )  # List of pause point identifiers
    user_inputs = Column(
        JSONB, default=dict, nullable=False
    )  # Phase-specific user inputs
    phase_results = Column(
        JSONB, default=dict, nullable=False
    )  # Phase completion results
    agent_insights = Column(
        JSONB, default=list, nullable=False
    )  # Agent-generated insights

    # Collection results
    collected_platforms = Column(
        JSONB, default=list, nullable=False
    )  # Detected platforms
    collection_results = Column(
        JSONB, default=dict, nullable=False
    )  # Collection phase results
    gap_analysis_results = Column(
        JSONB, default=dict, nullable=False
    )  # Gap analysis summary

    # Assessment readiness
    assessment_ready = Column(
        Boolean, default=False, nullable=False
    )  # Ready for assessment handoff
    apps_ready_for_assessment = Column(
        Integer, default=0, nullable=False
    )  # Number of apps ready for assessment

    # Assessment transition tracking (Phase 4)
    assessment_flow_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # Linked assessment flow ID
    assessment_transition_date = Column(
        DateTime(timezone=True), nullable=True
    )  # When transition to assessment occurred

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)

    # User interaction timestamp
    last_user_interaction = Column(DateTime(timezone=True), nullable=True)

    # Completion timestamp
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    client_account = relationship("ClientAccount", back_populates="collection_flows")
    engagement = relationship("Engagement", back_populates="collection_flows")
    user = relationship("User", back_populates="collection_flows")
    master_flow = relationship(
        "CrewAIFlowStateExtensions", back_populates="collection_flow"
    )
    discovery_flow = relationship("DiscoveryFlow", back_populates="collection_flows")

    # Related entities
    collected_data = relationship(
        "CollectedDataInventory",
        back_populates="collection_flow",
        cascade="all, delete-orphan",
    )
    data_gaps = relationship(
        "CollectionDataGap",
        back_populates="collection_flow",
        cascade="all, delete-orphan",
    )
    questionnaire_responses = relationship(
        "CollectionQuestionnaireResponse",
        back_populates="collection_flow",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<CollectionFlow(id={self.id}, flow_name='{self.flow_name}', status={self.status})>"

    def calculate_progress(self) -> float:
        """Calculate progress percentage based on current phase"""
        phase_weights = {
            CollectionPhase.INITIALIZATION.value: 0,
            CollectionPhase.PLATFORM_DETECTION.value: 15,
            CollectionPhase.AUTOMATED_COLLECTION.value: 40,
            CollectionPhase.GAP_ANALYSIS.value: 55,
            CollectionPhase.QUESTIONNAIRE_GENERATION.value: 70,
            CollectionPhase.MANUAL_COLLECTION.value: 85,
            CollectionPhase.DATA_VALIDATION.value: 95,
            CollectionPhase.FINALIZATION.value: 100,
        }

        if self.current_phase and self.current_phase in phase_weights:
            return phase_weights[self.current_phase]
        return 0.0

    def update_progress(self):
        """Update progress percentage based on current phase"""
        self.progress_percentage = self.calculate_progress()

    def get_next_phase(self) -> Optional[str]:
        """Get the next phase in the collection flow"""
        phase_order = [
            CollectionPhase.INITIALIZATION,
            CollectionPhase.PLATFORM_DETECTION,
            CollectionPhase.AUTOMATED_COLLECTION,
            CollectionPhase.GAP_ANALYSIS,
            CollectionPhase.QUESTIONNAIRE_GENERATION,
            CollectionPhase.MANUAL_COLLECTION,
            CollectionPhase.DATA_VALIDATION,
            CollectionPhase.FINALIZATION,
        ]

        if not self.current_phase:
            return CollectionPhase.INITIALIZATION.value

        try:
            current_index = next(
                i
                for i, phase in enumerate(phase_order)
                if phase.value == self.current_phase
            )
            if current_index < len(phase_order) - 1:
                return phase_order[current_index + 1].value
        except StopIteration:
            pass

        return None

    def is_complete(self) -> bool:
        """Check if the collection flow is complete"""
        return self.status == CollectionFlowStatus.COMPLETED

    def prepare_assessment_package(self) -> Dict[str, Any]:
        """Prepare data package for assessment flow handoff"""
        return {
            "flow_id": str(self.flow_id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "collection_summary": {
                "automation_tier": (
                    self.automation_tier.value
                    if isinstance(self.automation_tier, Enum)
                    else self.automation_tier
                ),
                "collection_quality_score": self.collection_quality_score,
                "confidence_score": self.confidence_score,
                "platforms_collected": len(self.collected_platforms),
                "gap_analysis_complete": bool(self.gap_analysis_results),
            },
            "collected_data": self.collection_results,
            "gap_analysis": self.gap_analysis_results,
            "apps_ready": self.apps_ready_for_assessment,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary representation."""
        return {
            "id": str(self.id),
            "flow_id": str(self.flow_id),
            "flow_name": self.flow_name,
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "user_id": str(self.user_id),
            "master_flow_id": str(self.master_flow_id) if self.master_flow_id else None,
            "discovery_flow_id": (
                str(self.discovery_flow_id) if self.discovery_flow_id else None
            ),
            "automation_tier": (
                self.automation_tier.value
                if isinstance(self.automation_tier, Enum)
                else self.automation_tier
            ),
            "status": (
                self.status.value if isinstance(self.status, Enum) else self.status
            ),
            "current_phase": self.current_phase,
            "next_phase": self.next_phase,
            "progress_percentage": self.progress_percentage,
            "collection_quality_score": self.collection_quality_score,
            "confidence_score": self.confidence_score,
            "metadata": self.flow_metadata,
            "collection_config": self.collection_config,
            "phase_state": self.phase_state,
            "pause_points": self.pause_points,
            "user_inputs": self.user_inputs,
            "phase_results": self.phase_results,
            "agent_insights": self.agent_insights,
            "collected_platforms": self.collected_platforms,
            "collection_results": self.collection_results,
            "gap_analysis_results": self.gap_analysis_results,
            "assessment_ready": self.assessment_ready,
            "apps_ready_for_assessment": self.apps_ready_for_assessment,
            "last_user_interaction": (
                self.last_user_interaction.isoformat()
                if self.last_user_interaction
                else None
            ),
            "error_message": self.error_message,
            "error_details": self.error_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "is_complete": self.is_complete(),
        }


class CollectionGapAnalysis(Base):
    """
    Gap analysis results for collection flows.
    Tracks data completeness and quality assessment results.
    """

    __tablename__ = "collection_gap_analysis"
    __table_args__ = {"schema": "migration"}

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

    # Flow relationship
    collection_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_flows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Analysis results
    total_fields_required = Column(Integer, nullable=False, default=0)
    fields_collected = Column(Integer, nullable=False, default=0)
    fields_missing = Column(Integer, nullable=False, default=0)
    completeness_percentage = Column(Float, nullable=False, default=0.0)

    # Quality metrics
    data_quality_score = Column(Float, nullable=True)  # 0.0 to 1.0
    confidence_level = Column(Float, nullable=True)  # 0.0 to 1.0
    automation_coverage = Column(Float, nullable=True)  # 0.0 to 1.0

    # Gap details
    critical_gaps = Column(
        JSONB, default=list, nullable=False
    )  # List of critical missing data
    optional_gaps = Column(
        JSONB, default=list, nullable=False
    )  # List of optional missing data
    gap_categories = Column(JSONB, default=dict, nullable=False)  # Categorized gaps

    # Recommendations
    recommended_actions = Column(
        JSONB, default=list, nullable=False
    )  # Agent recommendations
    questionnaire_requirements = Column(
        JSONB, default=dict, nullable=False
    )  # Required questionnaires

    # Timestamps
    analyzed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    collection_flow = relationship("CollectionFlow", backref="gap_analysis")

    def __repr__(self):
        return f"<CollectionGapAnalysis(id={self.id}, completeness={self.completeness_percentage}%)>"

    def calculate_completeness(self) -> float:
        """Calculate completeness percentage"""
        if self.total_fields_required == 0:
            return 100.0
        return round((self.fields_collected / self.total_fields_required) * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "collection_flow_id": str(self.collection_flow_id),
            "total_fields_required": self.total_fields_required,
            "fields_collected": self.fields_collected,
            "fields_missing": self.fields_missing,
            "completeness_percentage": self.completeness_percentage,
            "data_quality_score": self.data_quality_score,
            "confidence_level": self.confidence_level,
            "automation_coverage": self.automation_coverage,
            "critical_gaps": self.critical_gaps,
            "optional_gaps": self.optional_gaps,
            "gap_categories": self.gap_categories,
            "recommended_actions": self.recommended_actions,
            "questionnaire_requirements": self.questionnaire_requirements,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AdaptiveQuestionnaire(Base):
    """
    Adaptive questionnaire templates for gap filling.
    Dynamically generates questions based on identified gaps.
    """

    __tablename__ = "adaptive_questionnaires"
    __table_args__ = {"schema": "migration"}

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

    # Flow relationship
    collection_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_flows.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Questionnaire identification
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    template_name = Column(String(255), nullable=False)
    template_type = Column(
        String(100), nullable=False, index=True
    )  # technical, business, operational
    version = Column(String(20), nullable=False, default="1.0")

    # Automation tier applicability
    applicable_tiers = Column(
        JSONB, default=list, nullable=False
    )  # List of applicable automation tiers

    # Question configuration
    question_set = Column(JSONB, nullable=False)  # Structured question data
    questions = Column(
        JSONB, default=list, nullable=False
    )  # List of questions for this instance
    question_count = Column(Integer, nullable=False, default=0)
    estimated_completion_time = Column(Integer, nullable=True)  # In minutes

    # Targeting
    target_gaps = Column(
        JSONB, default=list, nullable=False
    )  # Specific gaps this questionnaire addresses
    gap_categories = Column(
        JSONB, default=list, nullable=False
    )  # Gap categories this addresses
    platform_types = Column(
        JSONB, default=list, nullable=False
    )  # Applicable platform types
    data_domains = Column(JSONB, default=list, nullable=False)  # Data domains covered

    # Scoring and validation
    scoring_rules = Column(
        JSONB, default=dict, nullable=False
    )  # How to score responses
    validation_rules = Column(
        JSONB, default=dict, nullable=False
    )  # Response validation rules

    # Usage tracking
    usage_count = Column(Integer, nullable=False, default=0)
    success_rate = Column(Float, nullable=True)  # Success rate of gap filling

    # Status and responses
    completion_status = Column(
        String(50), nullable=False, default="pending"
    )  # pending, in_progress, completed
    responses_collected = Column(JSONB, nullable=True)  # Collected responses
    is_active = Column(Boolean, nullable=False, default=True)
    is_template = Column(Boolean, nullable=False, default=True)  # Template vs instance

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
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<AdaptiveQuestionnaire(name='{self.template_name}', type='{self.template_type}')>"

    def is_applicable_for_tier(self, tier: str) -> bool:
        """Check if questionnaire is applicable for a given automation tier"""
        return tier in self.applicable_tiers

    def is_applicable_for_gap(self, gap_category: str) -> bool:
        """Check if questionnaire addresses a specific gap category"""
        return gap_category in self.gap_categories

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "collection_flow_id": (
                str(self.collection_flow_id) if self.collection_flow_id else None
            ),
            "title": self.title,
            "description": self.description,
            "template_name": self.template_name,
            "template_type": self.template_type,
            "version": self.version,
            "applicable_tiers": self.applicable_tiers,
            "question_set": self.question_set,
            "questions": self.questions,
            "question_count": self.question_count,
            "estimated_completion_time": self.estimated_completion_time,
            "target_gaps": self.target_gaps,
            "gap_categories": self.gap_categories,
            "platform_types": self.platform_types,
            "data_domains": self.data_domains,
            "scoring_rules": self.scoring_rules,
            "validation_rules": self.validation_rules,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "completion_status": self.completion_status,
            "responses_collected": self.responses_collected,
            "is_active": self.is_active,
            "is_template": self.is_template,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }


# ========================================
# IN-MEMORY STATE MODELS FOR CREWAI FLOW
# ========================================


class CollectionStatus(str, Enum):
    """Collection flow status for in-memory state management"""

    INITIALIZING = "initializing"
    DETECTING_PLATFORMS = "detecting_platforms"
    COLLECTING_DATA = "collecting_data"
    ANALYZING_GAPS = "analyzing_gaps"
    GENERATING_QUESTIONNAIRES = "generating_questionnaires"
    MANUAL_COLLECTION = "manual_collection"
    VALIDATING_DATA = "validating_data"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"


class PlatformType(str, Enum):
    """Supported platform types for collection"""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ON_PREMISE = "on_premise"
    KUBERNETES = "kubernetes"
    VMWARE = "vmware"
    OPENSHIFT = "openshift"
    CUSTOM = "custom"


class DataDomain(str, Enum):
    """Data domains for collection"""

    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    DATABASE = "database"
    NETWORK = "network"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    COST = "cost"


class CollectionFlowError(Exception):
    """Custom exception for collection flow errors"""

    pass


class CollectionFlowState:
    """In-memory state model for collection flow execution"""

    def __init__(
        self,
        flow_id: str,
        client_account_id: str,
        engagement_id: str,
        user_id: Optional[str] = None,
        discovery_flow_id: Optional[str] = None,
        automation_tier: AutomationTier = AutomationTier.TIER_1,
        current_phase: CollectionPhase = CollectionPhase.INITIALIZATION,
        next_phase: CollectionPhase = None,
        status: CollectionStatus = CollectionStatus.INITIALIZING,
        progress: float = 0.0,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.flow_id = flow_id
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.user_id = user_id
        self.discovery_flow_id = discovery_flow_id
        self.automation_tier = automation_tier
        self.current_phase = current_phase
        self.next_phase = next_phase
        self.status = status
        self.progress = progress
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.completed_at: Optional[datetime] = None

        # Phase-specific data
        self.phase_results: Dict[str, Any] = {}
        self.user_inputs: Dict[str, Any] = {}
        self.pause_points: List[str] = []

        # Collection-specific data
        self.detected_platforms: List[Dict[str, Any]] = []
        self.collection_config: Dict[str, Any] = {}
        self.collected_data: Dict[str, Any] = {}
        self.gap_analysis_results: Dict[str, Any] = {}
        self.questionnaires: List[Dict[str, Any]] = []
        self.manual_responses: Dict[str, Any] = {}
        self.validation_results: Dict[str, Any] = {}

        # Quality metrics
        self.collection_quality_score: float = 0.0
        self.confidence_score: float = 0.0
        self.automation_coverage: float = 0.0

        # Assessment readiness
        self.assessment_ready: bool = False
        self.apps_ready_for_assessment: List[str] = []

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
        self.status = CollectionStatus.ERROR
        self.updated_at = datetime.utcnow()

    def detect_platform(self, platform_info: Dict[str, Any]):
        """Add a detected platform"""
        self.detected_platforms.append(platform_info)
        self.updated_at = datetime.utcnow()

    def update_gap_analysis(self, gap_results: Dict[str, Any]):
        """Update gap analysis results"""
        self.gap_analysis_results = gap_results
        self.updated_at = datetime.utcnow()

    def calculate_quality_score(self) -> float:
        """Calculate overall collection quality score"""
        if not self.collected_data:
            return 0.0

        # Placeholder calculation - would be more sophisticated in practice
        total_fields = self.gap_analysis_results.get("total_fields_required", 1)
        collected_fields = self.gap_analysis_results.get("fields_collected", 0)

        return round((collected_fields / total_fields) * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            "flow_id": self.flow_id,
            "client_account_id": self.client_account_id,
            "engagement_id": self.engagement_id,
            "user_id": self.user_id,
            "discovery_flow_id": self.discovery_flow_id,
            "automation_tier": (
                self.automation_tier.value if self.automation_tier else None
            ),
            "current_phase": self.current_phase.value if self.current_phase else None,
            "next_phase": self.next_phase.value if self.next_phase else None,
            "status": self.status.value if self.status else None,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "phase_results": self.phase_results,
            "user_inputs": self.user_inputs,
            "pause_points": self.pause_points,
            "detected_platforms": self.detected_platforms,
            "collection_config": self.collection_config,
            "collected_data": self.collected_data,
            "gap_analysis_results": self.gap_analysis_results,
            "questionnaires": self.questionnaires,
            "manual_responses": self.manual_responses,
            "validation_results": self.validation_results,
            "collection_quality_score": self.collection_quality_score,
            "confidence_score": self.confidence_score,
            "automation_coverage": self.automation_coverage,
            "assessment_ready": self.assessment_ready,
            "apps_ready_for_assessment": self.apps_ready_for_assessment,
            "last_user_interaction": (
                self.last_user_interaction.isoformat()
                if self.last_user_interaction
                else None
            ),
            "errors": self.errors,
        }
