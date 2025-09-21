"""
SQLAlchemy models for governance and approval workflows.

This module defines models for tracking approval requests and
migration exceptions in the governance process.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base, TimestampMixin


class ApprovalRequests(Base, TimestampMixin):
    """
    Approval requests for governance workflow.

    This table tracks requests for approvals of various migration
    activities including strategy changes, wave planning, and exceptions.
    """

    __tablename__ = "approval_requests"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenant scoping
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

    # Entity being approved
    entity_type = Column(
        String(30), nullable=False
    )  # strategy, wave, schedule, exception
    entity_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # ID of the entity being approved

    # Approval status and details
    status = Column(
        String(20), nullable=False, default="PENDING"
    )  # PENDING, APPROVED, REJECTED
    approver_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # User who approved/rejected
    notes = Column(Text, nullable=True)  # Approval/rejection notes

    # Timestamps
    requested_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    decided_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")
    migration_exceptions = relationship(
        "MigrationExceptions",
        back_populates="approval_request",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<ApprovalRequests(id={self.id}, entity_type='{self.entity_type}', status='{self.status}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id) if self.entity_id else None,
            "status": self.status,
            "approver_id": str(self.approver_id) if self.approver_id else None,
            "notes": self.notes,
            "requested_at": (
                self.requested_at.isoformat() if self.requested_at else None
            ),
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def approve(self, approver_id: str, notes: Optional[str] = None):
        """Approve the request."""
        self.status = "APPROVED"
        self.approver_id = approver_id
        if notes:
            self.notes = notes
        self.decided_at = datetime.utcnow()

    def reject(self, approver_id: str, notes: Optional[str] = None):
        """Reject the request."""
        self.status = "REJECTED"
        self.approver_id = approver_id
        if notes:
            self.notes = notes
        self.decided_at = datetime.utcnow()

    def is_pending(self) -> bool:
        """Check if request is still pending."""
        return self.status == "PENDING"

    def is_approved(self) -> bool:
        """Check if request is approved."""
        return self.status == "APPROVED"

    def is_rejected(self) -> bool:
        """Check if request is rejected."""
        return self.status == "REJECTED"


class MigrationExceptions(Base, TimestampMixin):
    """
    Migration exceptions and deviations.

    This table tracks exceptions to standard migration practices,
    including rationale, risk assessment, and approval status.
    """

    __tablename__ = "migration_exceptions"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenant scoping
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

    # Scope of exception
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.canonical_applications.id", ondelete="CASCADE"),
        nullable=True,
    )
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Exception details
    exception_type = Column(
        String(50), nullable=True
    )  # skip_migration, custom_approach, delay, etc.
    rationale = Column(Text, nullable=True)  # Business/technical justification
    risk_level = Column(String(10), nullable=True)  # low, medium, high, critical

    # Approval tracking
    approval_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.approval_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    status = Column(String(20), nullable=False, default="OPEN")  # OPEN, CLOSED

    # Relationships
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")
    application = relationship("CanonicalApplication")
    asset = relationship("Asset")
    approval_request = relationship(
        "ApprovalRequests", back_populates="migration_exceptions"
    )

    def __repr__(self):
        return f"<MigrationExceptions(id={self.id}, type='{self.exception_type}', risk='{self.risk_level}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "application_id": str(self.application_id) if self.application_id else None,
            "asset_id": str(self.asset_id) if self.asset_id else None,
            "exception_type": self.exception_type,
            "rationale": self.rationale,
            "risk_level": self.risk_level,
            "approval_request_id": (
                str(self.approval_request_id) if self.approval_request_id else None
            ),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def close(self):
        """Close the exception."""
        self.status = "CLOSED"

    def reopen(self):
        """Reopen the exception."""
        self.status = "OPEN"

    def is_open(self) -> bool:
        """Check if exception is open."""
        return self.status == "OPEN"

    def is_closed(self) -> bool:
        """Check if exception is closed."""
        return self.status == "CLOSED"

    def requires_approval(self) -> bool:
        """Check if exception requires approval based on risk level."""
        high_risk_types = ["custom_approach", "skip_migration"]
        return self.exception_type in high_risk_types or self.risk_level in [
            "high",
            "critical",
        ]
