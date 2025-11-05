"""
Decommission Flow Policy and Archive Models

Models for data retention policies and archive job tracking.
Ensures compliance-driven data preservation during decommission.

Reference: /docs/planning/DECOMMISSION_FLOW_SOLUTION.md Section 3.3
"""

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DataRetentionPolicy(Base):
    """
    Compliance-driven data retention policies.

    Defines retention requirements, data classification, and storage locations
    for decommissioned system data.
    """

    __tablename__ = "data_retention_policies"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'under_review')",
            name="valid_retention_policy_status",
        ),
        {"schema": "migration"},
    )

    # Primary identifiers
    policy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenant scoping
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.client_accounts.client_account_id"),
        nullable=False,
        index=True,
    )
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Policy definition
    policy_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Retention requirements
    retention_period_days = Column(Integer, nullable=False)
    compliance_requirements: ARRAY = Column(  # type: ignore[assignment]
        ARRAY(String),
        nullable=False,
        comment="Array of compliance standards: ['GDPR', 'SOX', 'HIPAA']",
    )

    # Data classification
    data_types: ARRAY = Column(  # type: ignore[assignment]
        ARRAY(String),
        nullable=False,
        comment="Array of data types covered by policy",
    )
    storage_location = Column(String(255), nullable=False)
    encryption_required = Column(Boolean, default=True)

    # Status
    status = Column(String(50), default="active")

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    archive_jobs = relationship(
        "ArchiveJob",
        back_populates="policy",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<DataRetentionPolicy(policy_id={self.policy_id}, "
            f"name='{self.policy_name}', "
            f"retention={self.retention_period_days} days, "
            f"status='{self.status}')>"
        )


class ArchiveJob(Base):
    """
    Data archival job tracking for decommissioned systems.

    Tracks archival execution, verification, and integrity checks for
    data preservation during decommission.
    """

    __tablename__ = "archive_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'in_progress', 'completed', "
            "'failed', 'cancelled')",
            name="valid_archive_job_status",
        ),
        CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="valid_progress_percentage",
        ),
        {"schema": "migration"},
    )

    # Primary identifiers
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.decommission_flows.flow_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.data_retention_policies.policy_id"),
        nullable=False,
    )

    # Multi-tenant scoping
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # System identification
    system_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id"),
        nullable=False,
        index=True,
    )
    system_name = Column(String(255), nullable=False)

    # Job details
    data_size_gb = Column(Numeric(15, 2), nullable=True)
    archive_location = Column(String(500), nullable=True)

    # Status tracking
    status = Column(String(50), nullable=False, default="queued", index=True)
    progress_percentage = Column(Integer, default=0)

    # Timing
    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    estimated_completion = Column(DateTime(timezone=True), nullable=True)
    actual_completion = Column(DateTime(timezone=True), nullable=True)

    # Verification
    integrity_verified = Column(Boolean, default=False)
    verification_checksum = Column(String(255), nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    flow = relationship("DecommissionFlow", back_populates="archive_jobs")
    policy = relationship("DataRetentionPolicy", back_populates="archive_jobs")
    system = relationship("Asset", foreign_keys=[system_id])

    def __repr__(self) -> str:
        return (
            f"<ArchiveJob(job_id={self.job_id}, "
            f"system='{self.system_name}', status='{self.status}', "
            f"progress={self.progress_percentage}%)>"
        )
