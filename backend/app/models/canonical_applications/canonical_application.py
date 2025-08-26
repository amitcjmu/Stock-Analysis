"""
CanonicalApplication model - Master registry of application identities
"""

from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .application_variant import ApplicationNameVariant
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import (
    Base,
    TimestampMixin,
    Column,
    String,
    Text,
    Boolean,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    UUID,
    JSONB,
    Vector,
    relationship,
    validates,
    PGVECTOR_AVAILABLE,
    normalize_name,
    generate_name_hash,
    calculate_text_similarity,
    uuid,
)
from .enums import MatchMethod, VerificationSource


class CanonicalApplication(Base, TimestampMixin):
    """
    Master registry of canonical application identities.

    This model serves as the single source of truth for application names
    within a client engagement, preventing duplicates and enabling
    consistent references across collection flows.

    Key Features:
    - Multi-tenant isolation (client_account_id + engagement_id)
    - Vector embeddings for fuzzy similarity matching
    - Audit trail for all changes
    - Performance optimized with strategic indexes
    """

    __tablename__ = "canonical_applications"
    __table_args__ = (
        # CRITICAL: Enforce uniqueness within tenant scope
        UniqueConstraint(
            "client_account_id",
            "engagement_id",
            "normalized_name",
            name="uq_canonical_apps_tenant_name",
        ),
        Index(
            "idx_canonical_apps_hash_tenant",
            "name_hash",
            "client_account_id",
            "engagement_id",
        ),
        Index("idx_canonical_apps_usage_stats", "usage_count", "last_used_at"),
        {"schema": "migration"},
    )

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Application name management
    canonical_name = Column(String(255), nullable=False, index=True)
    normalized_name = Column(String(255), nullable=False, index=True)
    name_hash = Column(
        String(64), nullable=False, index=True
    )  # SHA-256 for fast exact lookups

    # Multi-tenant isolation - CRITICAL for security
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

    # Vector embedding for fuzzy matching (sentence-transformers all-MiniLM-L6-v2: 384 dimensions)
    name_embedding = Column(
        Vector(384) if PGVECTOR_AVAILABLE else list,
        nullable=True,
        comment="Vector embedding for semantic similarity search",
    )

    # Application metadata
    description = Column(Text, nullable=True)
    application_type = Column(String(100), nullable=True)
    business_criticality = Column(String(50), nullable=True)
    technology_stack = Column(JSONB, nullable=True)

    # Confidence and quality metrics
    confidence_score = Column(Float, nullable=False, default=1.0)
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_source = Column(String(100), nullable=True)

    # Usage tracking for optimization
    usage_count = Column(Integer, nullable=False, default=1)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Audit trail
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    client_account = relationship(
        "ClientAccount", back_populates="canonical_applications"
    )
    engagement = relationship("Engagement", back_populates="canonical_applications")
    name_variants = relationship(
        "ApplicationNameVariant",
        back_populates="canonical_application",
        cascade="all, delete-orphan",
    )
    collection_flow_applications = relationship(
        "CollectionFlowApplication", back_populates="canonical_application"
    )

    @validates("canonical_name")
    def validate_canonical_name(self, key, name):
        """Validate canonical name format"""
        if not name or not name.strip():
            raise ValueError("Canonical name cannot be empty")
        if len(name.strip()) > 255:
            raise ValueError("Canonical name cannot exceed 255 characters")
        return name.strip()

    @validates("confidence_score")
    def validate_confidence_score(self, key, score):
        """Validate confidence score range"""
        if score is not None and not (0.0 <= score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return score

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.canonical_name:
            self.normalized_name = normalize_name(self.canonical_name)
            self.name_hash = generate_name_hash(self.normalized_name)

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize application name for consistent matching."""
        return normalize_name(name)

    @staticmethod
    def generate_name_hash(normalized_name: str) -> str:
        """Generate SHA-256 hash of normalized name for fast exact matching"""
        return generate_name_hash(normalized_name)

    def update_usage_stats(self):
        """Update usage statistics when application is referenced"""
        self.usage_count = (self.usage_count or 0) + 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @classmethod
    async def find_or_create_canonical(
        cls,
        db: AsyncSession,
        application_name: str,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        similarity_threshold: float = 0.85,
        **metadata
    ) -> Tuple["CanonicalApplication", bool, Optional["ApplicationNameVariant"]]:
        """
        Find existing canonical application or create new one with deduplication.

        Returns:
            Tuple of (canonical_app, is_new, variant)
            - canonical_app: The canonical application record
            - is_new: True if a new canonical application was created
            - variant: The name variant record (None if exact match to canonical name)
        """
        # Import here to avoid circular imports
        from .application_variant import ApplicationNameVariant

        if not application_name or not application_name.strip():
            raise ValueError("Application name cannot be empty")

        normalized_name = cls.normalize_name(application_name)
        name_hash = cls.generate_name_hash(normalized_name)

        # Step 1: Try exact hash match first (fastest)
        exact_match_query = select(cls).where(
            cls.client_account_id == client_account_id,
            cls.engagement_id == engagement_id,
            cls.name_hash == name_hash,
        )
        result = await db.execute(exact_match_query)
        existing_canonical = result.scalar_one_or_none()

        if existing_canonical:
            existing_canonical.update_usage_stats()
            await db.commit()

            # Check if we need to create a variant record
            if existing_canonical.canonical_name != application_name.strip():
                variant = await ApplicationNameVariant.create_variant(
                    db, existing_canonical, application_name, MatchMethod.EXACT, 1.0
                )
                return existing_canonical, False, variant

            return existing_canonical, False, None

        # Create new canonical application
        new_canonical = cls(
            canonical_name=application_name.strip(),
            normalized_name=normalized_name,
            name_hash=name_hash,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            created_by=user_id,
            verification_source=VerificationSource.USER_INPUT.value,
            **metadata
        )

        db.add(new_canonical)
        await db.commit()
        await db.refresh(new_canonical)

        return new_canonical, True, None

    @staticmethod
    def _calculate_text_similarity(str1: str, str2: str) -> float:
        """Calculate text similarity using Levenshtein distance."""
        return calculate_text_similarity(str1, str2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "canonical_name": self.canonical_name,
            "normalized_name": self.normalized_name,
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "description": self.description,
            "application_type": self.application_type,
            "business_criticality": self.business_criticality,
            "technology_stack": self.technology_stack,
            "confidence_score": self.confidence_score,
            "is_verified": self.is_verified,
            "verification_source": self.verification_source,
            "usage_count": self.usage_count,
            "last_used_at": (
                self.last_used_at.isoformat() if self.last_used_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
