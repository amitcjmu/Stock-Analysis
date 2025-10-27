"""
Field Dependency Rule Model

Database table for storing data-driven field-to-question dependency rules.
Per GPT5 review: Enables tenant-scoped, agent-learnable dependency configuration
instead of hard-coded fallback rules.
"""

from datetime import datetime
from typing import List
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Float, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.core.database import Base


class FieldDependencyRule(Base):
    """
    Field dependency rules for question reopening logic.

    Defines which questions should be reopened when a critical field changes.
    Supports multi-tenant scoping and agent learning.
    """

    __tablename__ = "field_dependency_rules"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Multi-tenant scoping
    client_account_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )  # NULL = client-level

    # Dependency mapping
    source_field = Column(
        String(100), nullable=False, index=True
    )  # Field that triggers dependency
    affected_questions = Column(
        JSONB, nullable=False, default=[]
    )  # List of question IDs to reopen

    # Rule metadata
    rule_type = Column(
        String(50), nullable=False, default="fallback"
    )  # 'fallback', 'learned', 'explicit'
    confidence_score = Column(Float, default=0.8)  # Agent learning confidence
    learned_by = Column(String(50), default="manual")  # 'manual', 'agent', 'analytics'

    # Audit trail
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)

    def get_affected_questions(self) -> List[str]:
        """
        Get affected questions as Python list.

        Returns:
            List of question IDs to reopen when source_field changes
        """
        if not self.affected_questions:
            return []
        return (
            self.affected_questions if isinstance(self.affected_questions, list) else []
        )

    def __repr__(self) -> str:
        return (
            f"<FieldDependencyRule(id={self.id}, "
            f"source_field='{self.source_field}', "
            f"rule_type='{self.rule_type}', "
            f"confidence={self.confidence_score})>"
        )
