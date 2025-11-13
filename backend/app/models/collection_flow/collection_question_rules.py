"""
CollectionQuestionRules SQLAlchemy Model

Maps questions to asset types and defines inheritance rules for adaptive questionnaires.
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


class CollectionQuestionRules(Base):
    """
    Question rules for asset-type-specific filtering.

    Maps questions to asset types (Application, Server, Database, etc.) with
    inheritance rules and answer options for dropdown enforcement.
    """

    __tablename__ = "collection_question_rules"
    __table_args__ = {"schema": "migration"}

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

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

    # Question identification
    question_id = Column(String(255), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(
        String(50), nullable=False
    )  # "dropdown", "multi_select", "text"

    # Asset type applicability
    asset_type = Column(
        String(100), nullable=False
    )  # "Application", "Server", "Database", etc.
    is_applicable = Column(Boolean, nullable=False, default=True)

    # Inheritance rules
    inherits_from_parent = Column(Boolean, default=True)
    override_parent = Column(Boolean, default=False)

    # Answer options (for dropdowns)
    answer_options = Column(JSONB)  # ["Option 1", "Option 2", "Other"]

    # Display configuration
    display_order = Column(Integer)
    section = Column(String(100))  # "Basic Information", "Technical Details"
    weight = Column(Integer, default=40)  # For progress calculation
    is_required = Column(Boolean, default=False)

    # Agent generation hints
    generation_hint = Column(Text)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = Column(String(255))

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses."""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "question_id": self.question_id,
            "question_text": self.question_text,
            "question_type": self.question_type,
            "asset_type": self.asset_type,
            "is_applicable": self.is_applicable,
            "inherits_from_parent": self.inherits_from_parent,
            "override_parent": self.override_parent,
            "answer_options": self.answer_options,
            "display_order": self.display_order,
            "section": self.section,
            "weight": self.weight,
            "is_required": self.is_required,
            "generation_hint": self.generation_hint,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }
