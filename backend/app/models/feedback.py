"""
Feedback Database Models.
Stores user feedback in database instead of files for Vercel compatibility.
"""

import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Feedback(Base):
    """
    User feedback storage model.
    Supports both page feedback and CMDB analysis feedback.
    """

    __tablename__ = "feedback"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Feedback identification
    feedback_type = Column(
        String(50), nullable=False, index=True
    )  # page_feedback, cmdb_analysis

    # Page feedback fields
    page = Column(String(255), index=True)  # Page name where feedback was submitted
    rating = Column(Integer)  # 1-5 star rating
    comment = Column(Text)  # User comment
    category = Column(
        String(50), default="general"
    )  # ui, performance, feature, bug, general
    breadcrumb = Column(String(500))  # Breadcrumb path for context

    # CMDB feedback fields
    filename = Column(String(255))  # CMDB filename for analysis feedback
    original_analysis = Column(JSON)  # Original AI analysis
    user_corrections = Column(JSON)  # User corrections to analysis
    asset_type_override = Column(String(100))  # User's asset type override

    # Status and processing
    status = Column(String(20), default="new")  # new, reviewed, resolved
    processed = Column(
        Boolean, default=False
    )  # Whether feedback has been processed for learning

    # Metadata
    user_agent = Column(String(500))  # Browser user agent
    user_timestamp = Column(String(50))  # Timestamp from client side
    client_ip = Column(String(45))  # Client IP address (IPv4/IPv6)

    # Multi-tenant support (nullable for general feedback)
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=True,
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Learning integration
    learning_patterns_extracted = Column(JSON)  # Patterns extracted for AI learning
    confidence_impact = Column(Float, default=0.0)  # Impact on AI confidence

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))  # When feedback was processed

    # Relationships
    client_account = relationship("ClientAccount", back_populates="feedback")
    engagement = relationship("Engagement", back_populates="feedback")

    def __repr__(self):
        return (
            f"<Feedback(id={self.id}, type='{self.feedback_type}', page='{self.page}')>"
        )

    @property
    def is_page_feedback(self) -> bool:
        """Check if this is page feedback."""
        return self.feedback_type == "page_feedback"

    @property
    def is_cmdb_feedback(self) -> bool:
        """Check if this is CMDB analysis feedback."""
        return self.feedback_type == "cmdb_analysis"


class FeedbackSummary(Base):
    """
    Feedback summary statistics for quick access.
    Updated periodically to avoid real-time calculations.
    """

    __tablename__ = "feedback_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Summary scope
    feedback_type = Column(String(50), nullable=False, index=True)
    page = Column(String(255), index=True)  # Specific page or 'all'
    time_period = Column(
        String(20), default="all_time"
    )  # all_time, last_30_days, last_7_days

    # Summary statistics
    total_feedback = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    status_counts = Column(JSON)  # {"new": 5, "reviewed": 3, "resolved": 2}
    rating_distribution = Column(JSON)  # {"1": 0, "2": 1, "3": 2, "4": 5, "5": 8}
    category_counts = Column(JSON)  # {"ui": 10, "performance": 5, "bug": 3}

    # Trends
    feedback_trend = Column(JSON)  # Daily/weekly feedback counts
    rating_trend = Column(JSON)  # Rating trends over time

    # Multi-tenant support
    client_account_id = Column(
        UUID(as_uuid=True), ForeignKey("client_accounts.id", ondelete="CASCADE")
    )
    engagement_id = Column(
        UUID(as_uuid=True), ForeignKey("engagements.id", ondelete="CASCADE")
    )

    # Metadata
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    calculation_duration_ms = Column(Integer)  # Time taken to calculate summary

    # Relationships
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")

    def __repr__(self):
        return f"<FeedbackSummary(type='{self.feedback_type}', page='{self.page}', total={self.total_feedback})>"
