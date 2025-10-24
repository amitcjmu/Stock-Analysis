"""
AssetCustomAttributes SQLAlchemy Model

Stores unmapped fields from bulk imports for flexible attribute storage.
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
    String,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class AssetCustomAttributes(Base):
    """
    Custom attributes for assets from bulk imports.

    Stores unmapped CSV/JSON fields that don't match standard enrichment
    table columns, with pattern detection for future agent suggestions.
    """

    __tablename__ = "asset_custom_attributes"
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

    # Asset reference
    asset_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    asset_type = Column(
        String(100), nullable=False
    )  # "Application", "Server", "Database"

    # Custom attribute data (flexible schema)
    attributes = Column(JSONB, nullable=False)  # {"custom_field": "value", ...}

    # Import tracking
    source = Column(String(100))  # "csv_import", "json_import", "api_integration"
    import_batch_id = Column(UUID(as_uuid=True))
    import_timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Pattern analysis (for future agent suggestions)
    pattern_detected = Column(Boolean, default=False)
    suggested_standard_field = Column(String(255))

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses."""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "asset_id": str(self.asset_id),
            "asset_type": self.asset_type,
            "attributes": self.attributes,
            "source": self.source,
            "import_batch_id": (
                str(self.import_batch_id) if self.import_batch_id else None
            ),
            "import_timestamp": (
                self.import_timestamp.isoformat() if self.import_timestamp else None
            ),
            "pattern_detected": self.pattern_detected,
            "suggested_standard_field": self.suggested_standard_field,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
