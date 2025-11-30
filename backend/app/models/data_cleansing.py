"""
Data Cleansing Models - Database persistence for recommendations
Stores recommendations with stable primary keys instead of deterministic IDs
"""

import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class DataCleansingRecommendation(Base, TimestampMixin):
    """
    Data cleansing recommendation stored in database with stable primary keys.

    This replaces the previous deterministic ID approach where IDs were generated
    from category and title, which broke when recommendation content changed.
    Now uses UUID primary keys that remain stable even when content is updated.
    """

    __tablename__ = "data_cleansing_recommendations"

    # Primary key - stable UUID that doesn't change when content changes
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to discovery flow
    flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.discovery_flows.flow_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Recommendation content
    category = Column(
        String(100), nullable=False
    )  # 'standardization', 'validation', 'enrichment', 'deduplication'
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False)  # 'low', 'medium', 'high'
    impact = Column(Text, nullable=True)
    effort_estimate = Column(String(100), nullable=True)
    fields_affected = Column(JSON, nullable=True)  # List of field names

    # Action tracking
    status = Column(
        String(20), nullable=False, default="pending"
    )  # 'pending', 'applied', 'rejected'
    action_notes = Column(Text, nullable=True)
    applied_by_user_id = Column(String(255), nullable=True)
    applied_at = Column(
        DateTime(timezone=True), nullable=True
    )  # Timestamp with timezone

    # Multi-tenant isolation (for audit and filtering)
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Relationship to discovery flow
    discovery_flow = relationship(
        "DiscoveryFlow",
        primaryjoin="DataCleansingRecommendation.flow_id == DiscoveryFlow.flow_id",
        back_populates="recommendations",
    )

    def __repr__(self):
        return f"<DataCleansingRecommendation(id={self.id}, title={self.title}, status={self.status})>"


# Update DiscoveryFlow model to add relationship
# This will be done via migration and adding relationship in discovery_flow.py
