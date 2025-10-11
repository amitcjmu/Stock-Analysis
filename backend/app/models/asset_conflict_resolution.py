"""
SQLAlchemy model for asset conflict resolution tracking.

CC: Stores detected asset conflicts for user resolution
"""

import uuid
from typing import Dict, Any

from sqlalchemy import Column, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class AssetConflictResolution(Base, TimestampMixin):
    """
    Tracks asset conflicts detected during import for user resolution.

    Workflow:
    1. Executor detects conflict via bulk_prepare_conflicts()
    2. Creates record with resolution_status='pending'
    3. Frontend displays conflict modal
    4. User chooses action (keep_existing/replace_with_new/merge)
    5. API updates record with resolution_status='resolved'
    6. Executor resumes and processes resolution
    """

    __tablename__ = "asset_conflict_resolutions"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenant context
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.client_accounts.id"),
        nullable=False,
        index=True,
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.engagements.id"),
        nullable=False,
        index=True,
    )
    data_import_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.data_imports.id"),
        nullable=True,
        index=True,
    )
    # NOTE: master_flow_id is indexed but NOT a FK (per GPT-5 feedback)
    # ADR rule: FKs must reference table PKs, not flow_id columns
    master_flow_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Master flow ID for filtering/auditing (not FK)",
    )

    # Conflict identification
    conflict_type = Column(
        String(50), nullable=False
    )  # 'duplicate_hostname', 'duplicate_ip', 'duplicate_name'
    conflict_key = Column(
        String(255), nullable=False
    )  # The conflicting value (e.g., hostname)

    # Existing asset reference
    existing_asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    existing_asset_snapshot = Column(
        JSONB, nullable=False
    )  # Full asset data for UI comparison

    # New asset data
    new_asset_data = Column(JSONB, nullable=False)  # Proposed new asset data

    # Resolution
    resolution_status = Column(
        String(20), default="pending", nullable=False
    )  # pending, resolved, cancelled
    resolution_action = Column(String(20))  # keep_existing, replace_with_new, merge
    merge_field_selections = Column(
        JSONB
    )  # {"os_version": "new", "memory_gb": "existing"}
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("migration.users.id"))
    resolved_at = Column(DateTime(timezone=True))

    # Relationships
    existing_asset = relationship("Asset", foreign_keys=[existing_asset_id])
    resolver = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self):
        return (
            f"<AssetConflictResolution(id={self.id}, "
            f"type={self.conflict_type}, key={self.conflict_key}, "
            f"status={self.resolution_status})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for API responses"""
        return {
            "id": str(self.id),
            "conflict_type": self.conflict_type,
            "conflict_key": self.conflict_key,
            "existing_asset_id": str(self.existing_asset_id),
            "existing_asset": self.existing_asset_snapshot,
            "new_asset": self.new_asset_data,
            "resolution_status": self.resolution_status,
            "resolution_action": self.resolution_action,
            "merge_field_selections": self.merge_field_selections,
            "resolved_by": str(self.resolved_by) if self.resolved_by else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
