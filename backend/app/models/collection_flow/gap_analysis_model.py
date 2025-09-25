"""
CollectionGapAnalysis SQLAlchemy Model
Model for tracking gap analysis results in collection flows.
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    UUID,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


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
    completeness_percentage = Column(Float, nullable=False, default=0.0)

    # Quality metrics
    data_quality_score = Column(Float, nullable=True)
    confidence_level = Column(String(50), nullable=True)  # low, medium, high

    # Gap details
    missing_critical_fields = Column(JSONB, nullable=False, default=list)
    data_quality_issues = Column(JSONB, nullable=False, default=list)
    recommended_actions = Column(JSONB, nullable=False, default=list)

    # Analysis metadata
    analysis_type = Column(String(100), nullable=False, default="automated")
    analysis_version = Column(String(50), nullable=True)
    analysis_config = Column(JSONB, nullable=False, default=dict)

    # Timestamps
    analyzed_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    collection_flow = relationship("CollectionFlow", back_populates="gap_analyses")

    def __repr__(self):
        return f"<CollectionGapAnalysis(id={self.id}, completeness={self.completeness_percentage}%)>"

    def calculate_completeness(self) -> float:
        """Calculate completeness percentage"""
        if self.total_fields_required == 0:
            return 0.0
        return round((self.fields_collected / self.total_fields_required) * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary representation."""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "collection_flow_id": str(self.collection_flow_id),
            "total_fields_required": self.total_fields_required,
            "fields_collected": self.fields_collected,
            "completeness_percentage": self.completeness_percentage,
            "data_quality_score": self.data_quality_score,
            "confidence_level": self.confidence_level,
            "missing_critical_fields": self.missing_critical_fields,
            "data_quality_issues": self.data_quality_issues,
            "recommended_actions": self.recommended_actions,
            "analysis_type": self.analysis_type,
            "analysis_version": self.analysis_version,
            "analysis_config": self.analysis_config,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
