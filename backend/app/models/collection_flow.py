"""
Collection Flow Model

This model represents the Collection Flow entity for the Adaptive Data Collection System.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, UUID, ForeignKey, Enum as SQLEnum, Float, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

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


class CollectionFlow(Base, TimestampMixin):
    """
    Collection Flow model for tracking data collection processes.
    
    This model tracks the lifecycle of data collection flows, including
    automation tier, current status, quality scores, and relationships
    to other flow types.
    """
    
    __tablename__ = "collection_flows"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Flow identifiers
    flow_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    flow_name = Column(String(255), nullable=False)
    
    # Multi-tenant fields
    client_account_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("engagements.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Flow relationships
    master_flow_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("crewai_flow_state_extensions.flow_id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    discovery_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("discovery_flows.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Flow configuration
    automation_tier = Column(
        SQLEnum(AutomationTier, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        index=True
    )
    status = Column(
        SQLEnum(CollectionFlowStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=CollectionFlowStatus.INITIALIZED,
        server_default="initialized",
        index=True
    )
    
    # Progress tracking
    current_phase = Column(String(100), nullable=True)
    progress_percentage = Column(Float, nullable=False, default=0.0, server_default="0.0")
    
    # Quality metrics
    collection_quality_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Configuration and state
    flow_metadata = Column("metadata", JSONB, nullable=False, default={}, server_default="{}")
    collection_config = Column(JSONB, nullable=False, default={}, server_default="{}")
    phase_state = Column(JSONB, nullable=False, default={}, server_default="{}")
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)
    
    # Completion timestamp
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    client_account = relationship("ClientAccount", back_populates="collection_flows")
    engagement = relationship("Engagement", back_populates="collection_flows")
    user = relationship("User", back_populates="collection_flows")
    master_flow = relationship("CrewAIFlowStateExtensions", back_populates="collection_flow")
    discovery_flow = relationship("DiscoveryFlow", back_populates="collection_flows")
    
    # Related entities
    collected_data = relationship("CollectedDataInventory", back_populates="collection_flow", cascade="all, delete-orphan")
    data_gaps = relationship("CollectionDataGap", back_populates="collection_flow", cascade="all, delete-orphan")
    questionnaire_responses = relationship("CollectionQuestionnaireResponse", back_populates="collection_flow", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CollectionFlow(id={self.id}, flow_name='{self.flow_name}', status={self.status})>"
    
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
            "discovery_flow_id": str(self.discovery_flow_id) if self.discovery_flow_id else None,
            "automation_tier": self.automation_tier.value if isinstance(self.automation_tier, Enum) else self.automation_tier,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "current_phase": self.current_phase,
            "progress_percentage": self.progress_percentage,
            "collection_quality_score": self.collection_quality_score,
            "confidence_score": self.confidence_score,
            "metadata": self.flow_metadata,
            "collection_config": self.collection_config,
            "phase_state": self.phase_state,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }