"""Create help_documents table for contextual AI chat RAG

Revision ID: 145_create_help_documents_table
Revises: 144_add_feedback_user_tracking
Create Date: 2025-12-04

Issue: #1218 - [Feature] Contextual AI Chat Assistant
Milestone: Contextual AI Chat Assistant
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "145_create_help_documents_table"
down_revision = "144_add_feedback_user_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create help_documents table for RAG-based contextual chat."""
    # Ensure pgvector extension is available (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create help_documents table if not exists (idempotent)
    op.execute(
        """
        DO $$
        BEGIN
            -- Create help_documents table if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'help_documents'
            ) THEN
                CREATE TABLE migration.help_documents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                    -- Document identification
                    title VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) NOT NULL,

                    -- Content
                    content TEXT NOT NULL,
                    summary TEXT,

                    -- Categorization
                    category VARCHAR(50) NOT NULL DEFAULT 'general',
                    flow_type VARCHAR(50),
                    route VARCHAR(255),

                    -- Metadata as JSONB
                    tags JSONB DEFAULT '[]'::jsonb,
                    related_pages JSONB DEFAULT '[]'::jsonb,
                    faq_questions JSONB DEFAULT '[]'::jsonb,

                    -- Vector embedding for semantic search (1024 dimensions for thenlper/gte-large)
                    embedding vector(1024),

                    -- Source and versioning
                    source VARCHAR(100) DEFAULT 'manual',
                    version VARCHAR(50) DEFAULT '1.0',
                    is_active VARCHAR(10) DEFAULT 'true',

                    -- Timestamps
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ,

                    -- Unique constraint on slug within schema
                    CONSTRAINT uq_help_documents_slug UNIQUE (slug)
                );

                RAISE NOTICE 'Created help_documents table';
            ELSE
                RAISE NOTICE 'help_documents table already exists - skipping';
            END IF;
        END $$;
        """
    )

    # Create indexes idempotently (IF NOT EXISTS)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_help_documents_slug
            ON migration.help_documents(slug);
        CREATE INDEX IF NOT EXISTS ix_help_documents_category
            ON migration.help_documents(category);
        CREATE INDEX IF NOT EXISTS ix_help_documents_flow_type
            ON migration.help_documents(flow_type);
        CREATE INDEX IF NOT EXISTS ix_help_documents_route
            ON migration.help_documents(route);
        """
    )

    # Create vector similarity index for efficient semantic search (idempotent)
    # Only create if table has rows (ivfflat requires data to build index)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND indexname = 'ix_help_documents_embedding'
            ) THEN
                -- Use HNSW index which doesn't require pre-populated data
                CREATE INDEX ix_help_documents_embedding
                    ON migration.help_documents
                    USING hnsw (embedding vector_cosine_ops);
                RAISE NOTICE 'Created vector embedding index';
            ELSE
                RAISE NOTICE 'Vector embedding index already exists - skipping';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Drop help_documents table (idempotent)."""
    # Drop indexes first (IF EXISTS for idempotency)
    op.execute(
        """
        DROP INDEX IF EXISTS migration.ix_help_documents_embedding;
        DROP INDEX IF EXISTS migration.ix_help_documents_slug;
        DROP INDEX IF EXISTS migration.ix_help_documents_category;
        DROP INDEX IF EXISTS migration.ix_help_documents_flow_type;
        DROP INDEX IF EXISTS migration.ix_help_documents_route;
        """
    )

    # Drop table (IF EXISTS for idempotency)
    op.execute("DROP TABLE IF EXISTS migration.help_documents CASCADE;")
