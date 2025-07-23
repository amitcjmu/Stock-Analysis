"""
Tags and vector embeddings models for auto-tagging and AI-driven asset classification.
"""

try:
    from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey,
                            Integer, String, Text)
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = String = Text = DateTime = ForeignKey = Float = Integer = Boolean = object

    def relationship(*args, **kwargs):
        return None

    class func:
        @staticmethod
        def now():
            return None

    class PostgresUUID:
        def __init__(self, *args, **kwargs):
            pass


try:
    from pgvector.sqlalchemy import Vector

    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = Text

import uuid

try:
    from app.core.database import Base
except ImportError:
    Base = object


class Tag(Base):
    """Tag model for asset auto-tagging based on Azure Migrate metadata categories."""

    __tablename__ = "tags"

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    client_account_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(
        String(50), nullable=False, index=True
    )  # Technology, Business, Infrastructure, etc.
    description = Column(Text)

    # Reference embedding for similarity matching
    reference_embedding = Column(Vector(1536)) if PGVECTOR_AVAILABLE else Column(Text)

    # Tag metadata
    confidence_threshold = Column(
        Float, default=0.7
    )  # Minimum similarity score for auto-assignment
    is_active = Column(Boolean, default=True, index=True)

    # Usage statistics
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', category='{self.category}')>"


class AssetEmbedding(Base):
    """Vector embeddings for assets to enable AI-driven similarity search and auto-tagging."""

    __tablename__ = "asset_embeddings"

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    asset_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Multi-tenant isolation (inherited from asset, but explicit for vector queries)
    client_account_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engagement_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Vector embedding (1536 dimensions for text-embedding-ada-002 from DeepInfra)
    embedding = Column(Vector(1536)) if PGVECTOR_AVAILABLE else Column(Text)

    # Source text used to generate embedding
    source_text = Column(Text)  # Concatenated asset description, name, tech stack, etc.
    embedding_model = Column(String(100), default="text-embedding-ada-002")

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    asset = relationship("Asset")

    def __repr__(self):
        return f"<AssetEmbedding(id={self.id}, asset_id={self.asset_id})>"


class AssetTag(Base):
    """Association table between CMDB assets and tags with confidence scores."""

    __tablename__ = "asset_tags"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Auto-tagging metadata
    confidence_score = Column(Float)  # 0-1 similarity score
    assigned_method = Column(String(50))  # 'auto', 'manual', 'ai_agent'
    assigned_by = Column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Validation
    is_validated = Column(Boolean, default=False)
    validated_by = Column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    validated_at = Column(DateTime(timezone=True))

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    asset = relationship("Asset")
    tag = relationship("Tag")

    def __repr__(self):
        return f"<AssetTag(asset_id={self.asset_id}, tag_id={self.tag_id}, confidence={self.confidence_score})>"
