"""
Collection Data Gap Model

This model represents identified data gaps in Collection Flows.
"""

import uuid

from sqlalchemy import (UUID, Column, DateTime, ForeignKey, Integer, String,
                        Text)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class CollectionDataGap(Base, TimestampMixin):
    """
    Model for tracking data gaps identified during collection.
    """

    __tablename__ = "collection_data_gaps"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    collection_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_flows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Gap identification
    gap_type = Column(String(100), nullable=False, index=True)
    gap_category = Column(String(50), nullable=False, index=True)
    field_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Impact assessment
    impact_on_sixr = Column(String(20), nullable=False)
    priority = Column(
        Integer, nullable=False, default=0, server_default="0", index=True
    )

    # Resolution
    suggested_resolution = Column(Text, nullable=True)
    resolution_status = Column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(50), nullable=True)

    # Metadata
    gap_metadata = Column(
        "metadata", JSONB, nullable=False, default={}, server_default="{}"
    )

    # Relationships
    collection_flow = relationship("CollectionFlow", back_populates="data_gaps")
    questionnaire_responses = relationship(
        "CollectionQuestionnaireResponse",
        back_populates="gap",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<CollectionDataGap(id={self.id}, type='{self.gap_type}', field='{self.field_name}')>"
