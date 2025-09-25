"""
AdaptiveQuestionnaire SQLAlchemy Model
Model for dynamic questionnaire generation and management.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class AdaptiveQuestionnaire(Base):
    """
    Adaptive questionnaire model for dynamic data collection.

    Stores questionnaire templates and generated forms for specific
    automation tiers and gap categories.
    """

    __tablename__ = "adaptive_questionnaires"
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

    # Questionnaire identification
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    template_name = Column(String(200), nullable=False, index=True)
    template_type = Column(
        String(100), nullable=False
    )  # basic, detailed, comprehensive
    version = Column(String(50), nullable=False, default="1.0")

    # Applicability
    applicable_tiers = Column(
        JSONB, nullable=False, default=list
    )  # List of automation tiers
    question_set = Column(JSONB, nullable=False, default=dict)
    questions = Column(JSONB, nullable=False, default=list)  # List of question objects

    # Questionnaire configuration
    validation_rules = Column(JSONB, nullable=False, default=dict)
    scoring_rules = Column(JSONB, nullable=False, default=dict)

    # Response tracking
    completion_status = Column(
        String(50), nullable=False, default="pending"
    )  # pending, in_progress, completed, failed
    responses_collected = Column(JSONB, nullable=False, default=dict)

    # Template metadata
    is_active = Column(Boolean, nullable=False, default=True)
    is_template = Column(Boolean, nullable=False, default=False)

    # Usage statistics
    usage_count = Column(Integer, nullable=False, default=0)
    success_rate = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    collection_flow = relationship(
        "CollectionFlow", back_populates="adaptive_questionnaires"
    )

    def __repr__(self):
        return f"<AdaptiveQuestionnaire(name='{self.template_name}', type='{self.template_type}')>"

    def is_applicable_for_tier(self, tier: str) -> bool:
        """Check if questionnaire is applicable for given automation tier"""
        return tier in self.applicable_tiers

    def is_applicable_for_gap(self, gap_category: str) -> bool:
        """Check if questionnaire addresses specific gap category"""
        # Check if any question targets this gap category
        for question in self.questions:
            if isinstance(question, dict):
                question_gaps = question.get("target_gaps", [])
                if gap_category in question_gaps:
                    return True
        return False

    def get_questions_for_gap(self, gap_category: str) -> List[Dict[str, Any]]:
        """Get questions that address specific gap category"""
        relevant_questions = []
        for question in self.questions:
            if isinstance(question, dict):
                question_gaps = question.get("target_gaps", [])
                if gap_category in question_gaps:
                    relevant_questions.append(question)
        return relevant_questions

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary representation."""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "collection_flow_id": str(self.collection_flow_id),
            "title": self.title,
            "description": self.description,
            "template_name": self.template_name,
            "template_type": self.template_type,
            "version": self.version,
            "applicable_tiers": self.applicable_tiers,
            "question_set": self.question_set,
            "questions": self.questions,
            "validation_rules": self.validation_rules,
            "scoring_rules": self.scoring_rules,
            "completion_status": self.completion_status,
            "responses_collected": self.responses_collected,
            "is_active": self.is_active,
            "is_template": self.is_template,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }
