"""
Database models for analysis queue functionality.
"""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class QueueStatus(str, enum.Enum):
    """Status of an analysis queue."""

    PENDING = "pending"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ItemStatus(str, enum.Enum):
    """Status of an item in the queue."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisQueue(Base):
    """Analysis queue for batch processing applications."""

    __tablename__ = "analysis_queues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default=QueueStatus.PENDING.value, nullable=False)

    # Context fields
    client_id = Column(UUID(as_uuid=True), nullable=False)
    engagement_id = Column(UUID(as_uuid=True), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
        nullable=False,
    )
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    items = relationship(
        "AnalysisQueueItem", back_populates="queue", cascade="all, delete-orphan"
    )

    # __table_args__ = (
    #     CheckConstraint(
    #         status.in_(['pending', 'processing', 'paused', 'completed', 'cancelled', 'failed']),
    #         name='analysis_queues_status_check'
    #     ),
    # )


class AnalysisQueueItem(Base):
    """Individual item in an analysis queue."""

    __tablename__ = "analysis_queue_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    queue_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.analysis_queues.id", ondelete="CASCADE"),
        nullable=False,
    )
    application_id = Column(String(255), nullable=False)
    status = Column(String(50), default=ItemStatus.PENDING.value, nullable=False)

    # Processing details
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
        nullable=False,
    )

    # Relationships
    queue = relationship("AnalysisQueue", back_populates="items")

    # __table_args__ = (
    #     CheckConstraint(
    #         status.in_(['pending', 'processing', 'completed', 'failed', 'cancelled']),
    #         name='analysis_queue_items_status_check'
    #     ),
    # )
