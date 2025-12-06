"""
CollectionBackgroundTasks SQLAlchemy Model

Persists background task state for resume/retry and status polling.
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class CollectionBackgroundTasks(Base):
    """
    Background task state for async operations.

    Persists long-running task state (bulk import, gap analysis) with
    cancellation support and idempotency guarantees.
    """

    __tablename__ = "collection_background_tasks"
    __table_args__ = {"schema": "migration"}

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenant isolation
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Flow association
    child_flow_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Task identification
    task_type = Column(
        String(50), nullable=False
    )  # "bulk_import", "gap_analysis", "bulk_answer"
    status = Column(
        String(50), nullable=False
    )  # "pending", "running", "completed", "failed", "cancelled"

    # Progress tracking
    progress_percent = Column(Integer, default=0)
    current_stage = Column(String(100))  # "Validating CSV", "Mapping Fields"
    rows_processed = Column(Integer, default=0)
    total_rows = Column(Integer)

    # Task data
    input_params = Column(JSONB, nullable=False)  # Task-specific parameters
    result_data = Column(JSONB)  # Task results on completion
    error_message = Column(Text)

    # Cancellation support
    is_cancellable = Column(Boolean, default=False)
    cancelled_at = Column(DateTime(timezone=True))
    cancelled_by = Column(String(255))

    # Idempotency and retry
    idempotency_key = Column(String(255))  # For duplicate prevention
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses."""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "child_flow_id": str(self.child_flow_id),
            "task_type": self.task_type,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "current_stage": self.current_stage,
            "rows_processed": self.rows_processed,
            "total_rows": self.total_rows,
            "input_params": self.input_params,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "is_cancellable": self.is_cancellable,
            "cancelled_at": (
                self.cancelled_at.isoformat() if self.cancelled_at else None
            ),
            "cancelled_by": self.cancelled_by,
            "idempotency_key": self.idempotency_key,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
