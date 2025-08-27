"""
Collection Questionnaire Response Model

This model represents questionnaire responses for filling data gaps.
"""

import uuid

from sqlalchemy import UUID, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class CollectionQuestionnaireResponse(Base, TimestampMixin):
    """
    Model for tracking questionnaire responses in Collection Flows.
    """

    __tablename__ = "collection_questionnaire_responses"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    collection_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_flows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gap_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_data_gaps.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    responded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Asset relationship - CRITICAL: Links responses to specific assets
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=True,  # Allow null for legacy responses
        index=True,
        comment="Foreign key to the asset this questionnaire response is about"
    )

    # Question details
    questionnaire_type = Column(String(50), nullable=False, index=True)
    question_category = Column(String(50), nullable=False, index=True)
    question_id = Column(String(100), nullable=False)
    question_text = Column(Text, nullable=False)

    # Response
    response_type = Column(String(50), nullable=False)
    response_value = Column(JSONB, nullable=True)
    confidence_score = Column(Float, nullable=True)
    validation_status = Column(
        String(20),
        nullable=True,
        default="pending",
        server_default="pending",
        index=True,
    )

    # Timestamps
    responded_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    response_metadata = Column(
        "metadata", JSONB, nullable=False, default={}, server_default="{}"
    )

    # Relationships
    collection_flow = relationship(
        "CollectionFlow", back_populates="questionnaire_responses"
    )
    gap = relationship("CollectionDataGap", back_populates="questionnaire_responses")
    user = relationship("User", back_populates="questionnaire_responses")
    asset = relationship("Asset", back_populates="questionnaire_responses")

    def __repr__(self):
        return f"<CollectionQuestionnaireResponse(id={self.id}, question_id='{self.question_id}')>"
