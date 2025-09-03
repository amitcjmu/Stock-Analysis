"""Add canonical application identity management with pgvector deduplication

Revision ID: 050_add_canonical_application_identity
Revises: 049_add_collection_flow_applications_table
Create Date: 2025-09-03 03:36:00.000000

This migration creates a comprehensive application identity management system
that addresses critical data integrity issues in collection flows:
- Prevents duplicate applications within same engagement
- Provides fuzzy matching with pgvector for normalization
- Ensures multi-tenant isolation
- Implements idempotency for updates
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# CC: Import pgvector types with fallback for environments without pgvector
try:
    from pgvector.sqlalchemy import Vector

    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False

# revision identifiers, used by Alembic.
revision = "050_add_canonical_application_identity"
down_revision = "049_add_collection_flow_applications_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create canonical application identity tables with pgvector support"""

    # Ensure pgvector extension is available
    conn = op.get_bind()

    # Check if pgvector extension exists and create if not
    try:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("✅ pgvector extension enabled successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not enable pgvector extension: {e}")
        print("   Continuing without vector similarity search capabilities")

    # 1. Create canonical_applications table - the master application registry
    op.create_table(
        "canonical_applications",
        # Primary identification
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_name", sa.String(255), nullable=False),
        sa.Column("normalized_name", sa.String(255), nullable=False, index=True),
        sa.Column(
            "name_hash", sa.String(64), nullable=False, index=True
        ),  # SHA-256 hash
        # Multi-tenant isolation - CRITICAL for data integrity
        sa.Column(
            "client_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "engagement_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        # Vector embedding for fuzzy matching (384 dimensions for sentence-transformers)
        # Using proper Vector type if pgvector available, fallback to ARRAY(Float)
        sa.Column(
            "name_embedding",
            Vector(384) if PGVECTOR_AVAILABLE else postgresql.ARRAY(sa.Float),
            nullable=True,
        ),
        # Application metadata
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("application_type", sa.String(100), nullable=True),
        sa.Column("business_criticality", sa.String(50), nullable=True),
        sa.Column("technology_stack", postgresql.JSONB, nullable=True),
        # Confidence and quality metrics
        sa.Column("confidence_score", sa.Float, nullable=False, default=1.0),
        sa.Column("is_verified", sa.Boolean, nullable=False, default=False),
        sa.Column("verification_source", sa.String(100), nullable=True),
        # Usage tracking for optimization
        sa.Column("usage_count", sa.Integer, nullable=False, default=1),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        # Audit trail
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ["client_account_id"], ["client_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["engagements.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="migration",
    )

    # 2. Create application_name_variants table - tracks all name variations
    op.create_table(
        "application_name_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "canonical_application_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        # The actual name variation as entered by users
        sa.Column("variant_name", sa.String(255), nullable=False),
        sa.Column("normalized_variant", sa.String(255), nullable=False, index=True),
        sa.Column("variant_hash", sa.String(64), nullable=False, index=True),
        # Multi-tenant isolation
        sa.Column(
            "client_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "engagement_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        # Vector embedding for this variant
        sa.Column(
            "variant_embedding",
            Vector(384) if PGVECTOR_AVAILABLE else postgresql.ARRAY(sa.Float),
            nullable=True,
        ),
        # Similarity scores and matching metadata
        sa.Column(
            "similarity_score", sa.Float, nullable=True
        ),  # Cosine similarity to canonical
        sa.Column(
            "match_method", sa.String(50), nullable=True
        ),  # exact, fuzzy, vector, manual
        sa.Column("match_confidence", sa.Float, nullable=False, default=1.0),
        # Usage tracking
        sa.Column("usage_count", sa.Integer, nullable=False, default=1),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ["canonical_application_id"],
            ["migration.canonical_applications.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["client_account_id"], ["client_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["engagements.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="migration",
    )

    # 3. Update collection_flow_applications to reference canonical applications
    # First, add new columns
    op.add_column(
        "collection_flow_applications",
        sa.Column(
            "canonical_application_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        schema="migration",
    )

    op.add_column(
        "collection_flow_applications",
        sa.Column("name_variant_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="migration",
    )

    op.add_column(
        "collection_flow_applications",
        sa.Column("deduplication_method", sa.String(50), nullable=True),
        schema="migration",
    )

    op.add_column(
        "collection_flow_applications",
        sa.Column("match_confidence", sa.Float, nullable=True),
        schema="migration",
    )

    # Add multi-tenant fields if not present
    try:
        op.add_column(
            "collection_flow_applications",
            sa.Column(
                "client_account_id", postgresql.UUID(as_uuid=True), nullable=True
            ),
            schema="migration",
        )
        op.add_column(
            "collection_flow_applications",
            sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=True),
            schema="migration",
        )
    except Exception:
        # Columns may already exist
        pass

    # Add foreign key constraints
    op.create_foreign_key(
        "fk_collection_flow_apps_canonical",
        "collection_flow_applications",
        "canonical_applications",
        ["canonical_application_id"],
        ["id"],
        ondelete="SET NULL",
        source_schema="migration",
        referent_schema="migration",
    )

    op.create_foreign_key(
        "fk_collection_flow_apps_variant",
        "collection_flow_applications",
        "application_name_variants",
        ["name_variant_id"],
        ["id"],
        ondelete="SET NULL",
        source_schema="migration",
        referent_schema="migration",
    )

    # 4. Create performance indexes

    # Multi-tenant isolation indexes (CRITICAL for security)
    op.create_index(
        "idx_canonical_apps_tenant_isolation",
        "canonical_applications",
        ["client_account_id", "engagement_id", "normalized_name"],
        unique=True,  # Prevent duplicates within same engagement
        schema="migration",
    )

    op.create_index(
        "idx_app_variants_tenant_isolation",
        "application_name_variants",
        ["client_account_id", "engagement_id", "normalized_variant"],
        unique=True,  # Prevent duplicate variants within same engagement
        schema="migration",
    )

    # Performance indexes for lookups
    op.create_index(
        "idx_canonical_apps_hash_lookup",
        "canonical_applications",
        ["name_hash", "client_account_id", "engagement_id"],
        schema="migration",
    )

    op.create_index(
        "idx_app_variants_hash_lookup",
        "application_name_variants",
        ["variant_hash", "client_account_id", "engagement_id"],
        schema="migration",
    )

    # Usage tracking indexes
    op.create_index(
        "idx_canonical_apps_usage",
        "canonical_applications",
        ["usage_count", "last_used_at"],
        schema="migration",
    )

    # Collection flow app indexes
    op.create_index(
        "idx_collection_flow_apps_canonical",
        "collection_flow_applications",
        ["canonical_application_id", "collection_flow_id"],
        schema="migration",
    )

    # 5. Add table and column comments for documentation
    op.execute(
        """
        COMMENT ON TABLE migration.canonical_applications IS
        'Master registry of canonical application names with multi-tenant isolation and deduplication';

        COMMENT ON COLUMN migration.canonical_applications.canonical_name IS
        'The authoritative, human-readable name for this application';

        COMMENT ON COLUMN migration.canonical_applications.normalized_name IS
        'Lowercase, trimmed, special-char-removed version for exact matching';

        COMMENT ON COLUMN migration.canonical_applications.name_hash IS
        'SHA-256 hash of normalized_name for fast lookups';

        COMMENT ON COLUMN migration.canonical_applications.name_embedding IS
        'Vector embedding of canonical_name for fuzzy similarity search (384-dim sentence-transformers)';

        COMMENT ON COLUMN migration.canonical_applications.confidence_score IS
        'Confidence in canonical name accuracy (0.0-1.0, higher = more confident)';

        COMMENT ON TABLE migration.application_name_variants IS
        'All name variations that resolve to canonical applications, with similarity metrics';

        COMMENT ON COLUMN migration.application_name_variants.match_method IS
        'How this variant was matched: exact, fuzzy_text, vector_similarity, manual_verification';

        COMMENT ON COLUMN migration.application_name_variants.similarity_score IS
        'Cosine similarity score to canonical name embedding (0.0-1.0)';
    """
    )


def downgrade() -> None:
    """Remove canonical application identity tables"""

    # Drop foreign key constraints first
    op.drop_constraint(
        "fk_collection_flow_apps_variant",
        "collection_flow_applications",
        schema="migration",
    )
    op.drop_constraint(
        "fk_collection_flow_apps_canonical",
        "collection_flow_applications",
        schema="migration",
    )

    # Remove added columns
    op.drop_column(
        "collection_flow_applications", "match_confidence", schema="migration"
    )
    op.drop_column(
        "collection_flow_applications", "deduplication_method", schema="migration"
    )
    op.drop_column(
        "collection_flow_applications", "name_variant_id", schema="migration"
    )
    op.drop_column(
        "collection_flow_applications", "canonical_application_id", schema="migration"
    )

    # Drop indexes
    op.drop_index(
        "idx_collection_flow_apps_canonical",
        "collection_flow_applications",
        schema="migration",
    )
    op.drop_index(
        "idx_canonical_apps_usage", "canonical_applications", schema="migration"
    )
    op.drop_index(
        "idx_app_variants_hash_lookup", "application_name_variants", schema="migration"
    )
    op.drop_index(
        "idx_canonical_apps_hash_lookup", "canonical_applications", schema="migration"
    )
    op.drop_index(
        "idx_app_variants_tenant_isolation",
        "application_name_variants",
        schema="migration",
    )
    op.drop_index(
        "idx_canonical_apps_tenant_isolation",
        "canonical_applications",
        schema="migration",
    )

    # Drop tables
    op.drop_table("application_name_variants", schema="migration")
    op.drop_table("canonical_applications", schema="migration")
