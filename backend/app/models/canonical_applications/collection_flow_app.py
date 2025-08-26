"""
CollectionFlowApplication model - Enhanced collection flow application with canonical support
"""

from typing import Any, Dict

from .base import (
    Base,
    TimestampMixin,
    Column,
    String,
    Float,
    ForeignKey,
    UUID,
    JSONB,
    relationship,
    uuid,
)
from .enums import MatchMethod


class CollectionFlowApplication(Base, TimestampMixin):
    """
    Enhanced collection flow application model with canonical application support.

    This model now supports both the legacy application_name field and the new
    canonical application references for proper deduplication and data integrity.
    """

    __tablename__ = "collection_flow_applications"
    __table_args__ = {"schema": "migration"}

    # Existing fields (preserved for backward compatibility)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_flow_id = Column(UUID(as_uuid=True), nullable=False)
    asset_id = Column(UUID(as_uuid=True), nullable=True)
    application_name = Column(String(255), nullable=False)  # Legacy field

    # New canonical application integration
    canonical_application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.canonical_applications.id", ondelete="SET NULL"),
        nullable=True,
    )
    name_variant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.application_name_variants.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Multi-tenant fields (added in migration)
    client_account_id = Column(UUID(as_uuid=True), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=True)

    # Deduplication metadata
    deduplication_method = Column(String(50), nullable=True)
    match_confidence = Column(Float, nullable=True)

    # Existing fields
    discovery_data_snapshot = Column(JSONB, nullable=True)
    gap_analysis_result = Column(JSONB, nullable=True)
    collection_status = Column(String(50), nullable=False, default="pending")

    # Relationships
    canonical_application = relationship(
        "CanonicalApplication", back_populates="collection_flow_applications"
    )
    name_variant = relationship(
        "ApplicationNameVariant", back_populates="collection_flow_applications"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "collection_flow_id": str(self.collection_flow_id),
            "application_name": self.application_name,
            "canonical_application_id": (
                str(self.canonical_application_id)
                if self.canonical_application_id
                else None
            ),
            "canonical_name": (
                self.canonical_application.canonical_name
                if self.canonical_application
                else None
            ),
            "deduplication_method": self.deduplication_method,
            "match_confidence": self.match_confidence,
            "collection_status": self.collection_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
