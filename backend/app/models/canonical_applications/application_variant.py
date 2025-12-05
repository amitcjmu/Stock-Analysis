"""
ApplicationNameVariant model - Tracks name variations for canonical applications
"""

from typing import Any, Dict
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .base import (
    Base,
    TimestampMixin,
    Column,
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    UUID,
    Vector,
    relationship,
    PGVECTOR_AVAILABLE,
    normalize_name,
    generate_name_hash,
    uuid,
)
from sqlalchemy import ARRAY
from .enums import MatchMethod


class ApplicationNameVariant(Base, TimestampMixin):
    """
    Tracks all name variations that resolve to canonical applications.

    This enables users to enter applications with slight variations
    (e.g., "Customer Portal", "customer-portal", "Customer_Portal")
    while maintaining referential integrity to the canonical name.
    """

    __tablename__ = "application_name_variants"
    __table_args__ = (
        UniqueConstraint(
            "client_account_id",
            "engagement_id",
            "normalized_variant",
            name="uq_app_variants_tenant_name",
        ),
        Index(
            "idx_app_variants_hash_tenant",
            "variant_hash",
            "client_account_id",
            "engagement_id",
        ),
        {"schema": "migration"},
    )

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.canonical_applications.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Name variation data
    variant_name = Column(String(255), nullable=False)
    normalized_variant = Column(String(255), nullable=False, index=True)
    variant_hash = Column(String(64), nullable=False, index=True)

    # Multi-tenant isolation
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

    # Vector embedding for this variant
    variant_embedding = Column(
        Vector(384) if PGVECTOR_AVAILABLE else ARRAY(Float), nullable=True
    )

    # Matching metadata
    similarity_score = Column(Float, nullable=True)
    match_method = Column(String(50), nullable=False, default=MatchMethod.EXACT.value)
    match_confidence = Column(Float, nullable=False, default=1.0)

    # Usage tracking
    usage_count = Column(Integer, nullable=False, default=1)
    first_seen_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    last_used_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    canonical_application = relationship(
        "CanonicalApplication", back_populates="name_variants"
    )
    collection_flow_applications = relationship(
        "CollectionFlowApplication", back_populates="name_variant"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.variant_name:
            self.normalized_variant = normalize_name(self.variant_name)
            self.variant_hash = generate_name_hash(self.normalized_variant)

    @classmethod
    async def create_variant(
        cls,
        db: AsyncSession,
        canonical_app,  # Type hint removed to avoid circular import
        variant_name: str,
        match_method: MatchMethod,
        similarity_score: float,
    ) -> "ApplicationNameVariant":
        """Create or update a name variant for a canonical application"""

        normalized_variant = normalize_name(variant_name)
        variant_hash = generate_name_hash(normalized_variant)

        # Check if variant already exists
        existing_query = select(cls).where(
            cls.client_account_id == canonical_app.client_account_id,
            cls.engagement_id == canonical_app.engagement_id,
            cls.variant_hash == variant_hash,
        )
        result = await db.execute(existing_query)
        existing_variant = result.scalar_one_or_none()

        if existing_variant:
            # Update usage stats
            existing_variant.usage_count += 1
            existing_variant.last_used_at = datetime.utcnow()
            await db.commit()
            return existing_variant

        # Create new variant
        new_variant = cls(
            canonical_application_id=canonical_app.id,
            variant_name=variant_name.strip(),
            client_account_id=canonical_app.client_account_id,
            engagement_id=canonical_app.engagement_id,
            similarity_score=similarity_score,
            match_method=match_method.value,
            match_confidence=min(similarity_score, 1.0),
        )

        db.add(new_variant)
        await db.commit()
        await db.refresh(new_variant)

        return new_variant

    def update_usage_stats(self):
        """Update usage statistics when variant is referenced"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "canonical_application_id": str(self.canonical_application_id),
            "variant_name": self.variant_name,
            "normalized_variant": self.normalized_variant,
            "similarity_score": self.similarity_score,
            "match_method": self.match_method,
            "match_confidence": self.match_confidence,
            "usage_count": self.usage_count,
            "first_seen_at": (
                self.first_seen_at.isoformat() if self.first_seen_at else None
            ),
            "last_used_at": (
                self.last_used_at.isoformat() if self.last_used_at else None
            ),
        }
