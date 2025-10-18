"""
CollectionFlow SQLAlchemy Model
Main collection flow model for tracking data collection processes.
"""

import uuid
from typing import Any, Dict, Optional

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

from app.models.base import Base, TimestampMixin
from .schemas import (
    AutomationTier,
    CollectionFlowStatus,
    CollectionPhase,
)


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
    # phase_state removed per ADR-028: Master flow is single source of truth for phase tracking

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
        "CrewAIFlowStateExtensions",
        foreign_keys=[master_flow_id],
        back_populates="collection_flow",
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
    gap_analyses = relationship(
        "CollectionGapAnalysis",
        back_populates="collection_flow",
        cascade="all, delete-orphan",
    )
    adaptive_questionnaires = relationship(
        "AdaptiveQuestionnaire",
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
            CollectionPhase.ASSET_SELECTION.value: 15,
            CollectionPhase.GAP_ANALYSIS.value: 40,
            CollectionPhase.QUESTIONNAIRE_GENERATION.value: 60,
            CollectionPhase.MANUAL_COLLECTION.value: 80,
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
            CollectionPhase.ASSET_SELECTION,
            CollectionPhase.GAP_ANALYSIS,
            CollectionPhase.QUESTIONNAIRE_GENERATION,
            CollectionPhase.MANUAL_COLLECTION,
            CollectionPhase.DATA_VALIDATION,
            CollectionPhase.FINALIZATION,
        ]

        if not self.current_phase:
            return CollectionPhase.INITIALIZATION.value

        try:
            current_phase_enum = CollectionPhase(self.current_phase)
            current_index = phase_order.index(current_phase_enum)
            if current_index < len(phase_order) - 1:
                return phase_order[current_index + 1].value
        except (ValueError, IndexError):
            pass

        return None

    def is_complete(self) -> bool:
        """Check if the collection flow is complete"""
        return self.status == CollectionFlowStatus.COMPLETED

    def prepare_assessment_package(self) -> Dict[str, Any]:
        """Prepare data package for assessment flow handoff"""
        return {
            "collection_flow_id": str(self.id),
            "flow_metadata": {
                "automation_tier": (
                    self.automation_tier.value if self.automation_tier else "tier_1"
                ),
                "quality_score": self.collection_quality_score,
                "confidence_score": self.confidence_score,
                "platforms": self.collected_platforms,
                "phases_completed": [
                    phase
                    for phase, result in self.phase_results.items()
                    if result.get("status") == "completed"
                ],
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
                if hasattr(self.automation_tier, "value")
                else self.automation_tier
            ),
            "status": (
                self.status.value if hasattr(self.status, "value") else self.status
            ),
            "current_phase": self.current_phase,
            "next_phase": self.next_phase,
            "progress_percentage": self.progress_percentage,
            "collection_quality_score": self.collection_quality_score,
            "confidence_score": self.confidence_score,
            "metadata": self.flow_metadata,
            "collection_config": self.collection_config,
            # phase_state removed per ADR-028 - use master flow's phase_transitions
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
