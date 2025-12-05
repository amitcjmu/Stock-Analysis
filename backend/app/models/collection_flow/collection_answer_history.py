"""
CollectionAnswerHistory SQLAlchemy Model

Tracks answer changes for audit trail and re-emergence logic.
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    UUID,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class CollectionAnswerHistory(Base):
    """
    Answer history for audit trail and re-emergence tracking.

    Records all answer changes with source tracking and re-emergence support
    for dependency-driven question reopening.
    """

    __tablename__ = "collection_answer_history"
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

    # Reference to questionnaire and asset
    questionnaire_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.adaptive_questionnaires.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    question_id = Column(String(255), nullable=False)

    # Answer data
    answer_value = Column(Text)
    answer_source = Column(
        String(50), nullable=False
    )  # "user_input", "bulk_import", "agent_generated", "bulk_answer_modal"
    confidence_score = Column(Numeric(5, 2))  # 0.00 to 100.00

    # Change tracking
    previous_value = Column(Text)
    changed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    changed_by = Column(String(255))

    # Re-emergence tracking
    reopened_at = Column(DateTime(timezone=True))
    reopened_reason = Column(Text)
    reopened_by = Column(
        String(50)
    )  # "user_manual", "agent_dependency_change", "critical_field_change"

    # Metadata (renamed to avoid SQLAlchemy reserved word)
    additional_metadata = Column(
        JSONB
    )  # Additional context (bulk operation ID, import file name, etc.)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses."""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "questionnaire_id": str(self.questionnaire_id),
            "asset_id": str(self.asset_id),
            "question_id": self.question_id,
            "answer_value": self.answer_value,
            "answer_source": self.answer_source,
            "confidence_score": (
                float(self.confidence_score) if self.confidence_score else None
            ),
            "previous_value": self.previous_value,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
            "changed_by": self.changed_by,
            "reopened_at": self.reopened_at.isoformat() if self.reopened_at else None,
            "reopened_reason": self.reopened_reason,
            "reopened_by": self.reopened_by,
            "metadata": self.additional_metadata,
        }
