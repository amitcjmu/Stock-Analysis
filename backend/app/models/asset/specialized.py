"""
Specialized CMDB tables for normalized data structures.

These tables support end-of-life assessments and contact management.
"""

import uuid
from typing import Any, Dict

from sqlalchemy import Column, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class AssetEOLAssessment(Base, TimestampMixin):
    """
    End-of-life technology assessments for assets.

    Tracks EOL dates, risk levels, and remediation options for
    technology components.
    """

    __tablename__ = "asset_eol_assessments"
    __table_args__ = {"schema": "migration"}

    # Primary key
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

    # Asset reference
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # EOL Assessment Data
    technology_component = Column(String(255), nullable=False)
    eol_date = Column(Date, nullable=True, index=True)
    eol_risk_level = Column(
        String(20), nullable=True, comment="low, medium, high, critical"
    )
    assessment_notes = Column(Text, nullable=True)
    remediation_options = Column(JSONB, default=list, nullable=False)

    # Relationships
    asset = relationship("Asset", back_populates="eol_assessments")
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")

    def __repr__(self):
        return (
            f"<AssetEOLAssessment(id={self.id}, asset_id={self.asset_id}, "
            f"component='{self.technology_component}', eol_date={self.eol_date})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "technology_component": self.technology_component,
            "eol_date": self.eol_date.isoformat() if self.eol_date else None,
            "eol_risk_level": self.eol_risk_level,
            "assessment_notes": self.assessment_notes,
            "remediation_options": self.remediation_options or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AssetContact(Base, TimestampMixin):
    """
    Normalized contact information for assets.

    Supports multiple contact types (business owner, technical owner, etc.)
    with optional platform user linkage.
    """

    __tablename__ = "asset_contacts"
    __table_args__ = {"schema": "migration"}

    # Primary key
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

    # Asset reference
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Contact Data
    contact_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="business_owner, technical_owner, architect, etc.",
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="If contact is platform user",
    )
    email = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Relationships
    asset = relationship("Asset", back_populates="contacts")
    user = relationship("User")
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")

    def __repr__(self):
        return (
            f"<AssetContact(id={self.id}, asset_id={self.asset_id}, "
            f"type='{self.contact_type}', email='{self.email}')>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "contact_type": self.contact_type,
            "user_id": str(self.user_id) if self.user_id else None,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
