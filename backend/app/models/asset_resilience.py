"""
SQLAlchemy models for asset resilience and compliance.

This module defines models for tracking asset resilience metrics,
compliance flags, and vulnerability information.
"""

import uuid
from typing import Any, Dict

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class AssetResilience(Base, TimestampMixin):
    """
    Asset resilience metrics.

    This table stores business continuity and resilience metrics for assets
    including RTO, RPO, and SLA information.
    """

    __tablename__ = "asset_resilience"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Asset reference
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,  # One resilience record per asset
    )

    # Resilience metrics
    rto_minutes = Column(Integer, nullable=True)  # Recovery Time Objective
    rpo_minutes = Column(Integer, nullable=True)  # Recovery Point Objective
    sla_json = Column(JSONB, nullable=False, default=dict)  # SLA details and targets

    # Relationships
    asset = relationship("Asset")

    def __repr__(self):
        return (
            f"<AssetResilience(id={self.id}, asset_id={self.asset_id}, "
            f"rto={self.rto_minutes}, rpo={self.rpo_minutes})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "rto_minutes": self.rto_minutes,
            "rpo_minutes": self.rpo_minutes,
            "sla_json": self.sla_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AssetComplianceFlags(Base, TimestampMixin):
    """
    Asset compliance and regulatory flags.

    This table tracks compliance requirements, data classification,
    and residency requirements for assets.
    """

    __tablename__ = "asset_compliance_flags"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Asset reference
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,  # One compliance record per asset
    )

    # Compliance information
    compliance_scopes = Column(
        ARRAY(Text), nullable=False, default=list
    )  # GDPR, HIPAA, SOX, etc.
    data_classification = Column(
        String(50), nullable=True
    )  # public, internal, confidential, restricted
    residency = Column(String(50), nullable=True)  # Data residency requirements
    evidence_refs = Column(
        JSONB, nullable=False, default=list
    )  # Evidence/document references

    # Relationships
    asset = relationship("Asset")

    def __repr__(self):
        return (
            f"<AssetComplianceFlags(id={self.id}, asset_id={self.asset_id}, "
            f"classification='{self.data_classification}')>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "compliance_scopes": self.compliance_scopes or [],
            "data_classification": self.data_classification,
            "residency": self.residency,
            "evidence_refs": self.evidence_refs or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AssetVulnerabilities(Base, TimestampMixin):
    """
    Asset vulnerability tracking.

    This table stores vulnerability information for assets including
    CVE details, severity levels, and detection metadata.
    """

    __tablename__ = "asset_vulnerabilities"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Asset reference
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Vulnerability information
    cve_id = Column(String(50), nullable=True)  # CVE identifier if applicable
    severity = Column(String(10), nullable=True)  # low, medium, high, critical
    detected_at = Column(DateTime(timezone=True), nullable=True)
    source = Column(String(255), nullable=True)  # Where vulnerability was detected
    details = Column(
        JSONB, nullable=False, default=dict
    )  # Additional vulnerability details

    # Relationships
    asset = relationship("Asset")

    def __repr__(self):
        return (
            f"<AssetVulnerabilities(id={self.id}, asset_id={self.asset_id}, "
            f"cve='{self.cve_id}', severity='{self.severity}')>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "cve_id": self.cve_id,
            "severity": self.severity,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "source": self.source,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AssetLicenses(Base, TimestampMixin):
    """
    Asset licensing information.

    This table tracks software licenses, support contracts,
    and renewal dates for assets.
    """

    __tablename__ = "asset_licenses"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Asset reference
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # License information
    license_type = Column(
        String(100), nullable=True
    )  # Commercial, Open Source, Enterprise, etc.
    renewal_date = Column(Date, nullable=True)
    contract_reference = Column(
        String(255), nullable=True
    )  # Contract number or reference
    support_tier = Column(String(50), nullable=True)  # Basic, Premium, Enterprise, etc.

    # Relationships
    asset = relationship("Asset")

    def __repr__(self):
        return f"<AssetLicenses(id={self.id}, asset_id={self.asset_id}, type='{self.license_type}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "license_type": self.license_type,
            "renewal_date": (
                self.renewal_date.isoformat() if self.renewal_date else None
            ),
            "contract_reference": self.contract_reference,
            "support_tier": self.support_tier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
