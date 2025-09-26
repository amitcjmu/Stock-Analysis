"""
AssetFieldConflict model for tracking and resolving field-level conflicts
during asset-agnostic collection across multiple data sources.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import TimestampMixin, Base


class AssetFieldConflict(Base, TimestampMixin):
    """
    Tracks field-level conflicts across multiple data sources for assets.

    This model stores conflicts when the same field has different values
    from different sources (custom_attributes, technical_details, imports).
    """

    __tablename__ = "asset_field_conflicts"
    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "field_name",
            "client_account_id",
            "engagement_id",
            name="uq_conflict_asset_field_tenant",
        ),
        Index("idx_conflicts_asset_field", "asset_id", "field_name"),
        Index("idx_conflicts_tenant", "client_account_id", "engagement_id"),
        Index("idx_conflicts_status", "resolution_status"),
        {"schema": "migration"},
    )

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Asset reference
    asset_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to the asset with conflicting field data",
    )

    # Multi-tenant isolation (UUID types confirmed in governance.py)
    client_account_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=False,
        doc="Client account UUID for tenant isolation",
    )
    engagement_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=False,
        doc="Engagement UUID for project isolation",
    )

    # Conflict details
    field_name = Column(
        String(255), nullable=False, doc="Name of the field that has conflicting values"
    )

    conflicting_values = Column(
        JSONB,
        nullable=False,
        doc="Array of conflicting values with metadata: [{value, source, timestamp, confidence}]",
    )

    # Resolution tracking
    resolution_status = Column(
        String(20),
        nullable=False,
        default="pending",
        doc="Current status of conflict resolution",
    )

    resolved_value = Column(
        Text, nullable=True, doc="The final resolved value chosen for this field"
    )

    resolved_by = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        doc="UUID of the user who resolved the conflict (null for auto-resolution)",
    )

    resolution_rationale = Column(
        Text, nullable=True, doc="Explanation of why this resolution was chosen"
    )

    # Relationships
    asset = relationship("Asset")  # One-way relationship only

    def __init__(self, **kwargs):
        """Initialize with default resolution_status if not provided."""
        if "resolution_status" not in kwargs:
            kwargs["resolution_status"] = "pending"
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return (
            f"<AssetFieldConflict(id={self.id}, asset_id={self.asset_id}, "
            f"field_name='{self.field_name}', status='{self.resolution_status}')>"
        )

    @property
    def is_resolved(self) -> bool:
        """Check if this conflict has been resolved."""
        return self.resolution_status in ("auto_resolved", "manual_resolved")

    @property
    def source_count(self) -> int:
        """Get the number of conflicting sources."""
        if not self.conflicting_values:
            return 0
        return len(self.conflicting_values)

    def get_highest_confidence_value(self) -> Optional[Dict[str, Any]]:
        """Get the conflicting value with the highest confidence score."""
        if not self.conflicting_values:
            return None

        return max(self.conflicting_values, key=lambda x: x.get("confidence", 0.0))

    def get_sources(self) -> List[str]:
        """Get list of all sources that contributed conflicting values."""
        if not self.conflicting_values:
            return []

        return [value.get("source", "unknown") for value in self.conflicting_values]

    def add_conflicting_value(
        self,
        value: Any,
        source: str,
        timestamp: Optional[datetime] = None,
        confidence: float = 0.5,
    ) -> None:
        """Add a new conflicting value to this conflict."""
        if not self.conflicting_values:
            self.conflicting_values = []

        new_value = {
            "value": value,
            "source": source,
            "timestamp": (timestamp or datetime.utcnow()).isoformat(),
            "confidence": confidence,
        }

        # Check if this source already exists, update if so
        for i, existing in enumerate(self.conflicting_values):
            if existing.get("source") == source:
                self.conflicting_values[i] = new_value
                return

        # Add as new conflicting value
        self.conflicting_values.append(new_value)

    def resolve_conflict(
        self,
        resolved_value: str,
        resolved_by: Optional[UUID] = None,
        rationale: Optional[str] = None,
        auto_resolved: bool = False,
    ) -> None:
        """Mark this conflict as resolved with the given value."""
        self.resolved_value = resolved_value
        self.resolved_by = resolved_by
        self.resolution_rationale = rationale
        self.resolution_status = "auto_resolved" if auto_resolved else "manual_resolved"
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "field_name": self.field_name,
            "conflicting_values": self.conflicting_values,
            "resolution_status": self.resolution_status,
            "resolved_value": self.resolved_value,
            "resolved_by": str(self.resolved_by) if self.resolved_by else None,
            "resolution_rationale": self.resolution_rationale,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_resolved": self.is_resolved,
            "source_count": self.source_count,
            "sources": self.get_sources(),
        }
