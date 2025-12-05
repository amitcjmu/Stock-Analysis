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
    op.execute(
        """
        DO $$
        BEGIN
            -- Ensure pgvector extension is available in public schema
            CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;

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
                    slug VARCHAR(255) UNIQUE NOT NULL,

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
                    -- Use public.vector since pgvector extension is in public schema
                    embedding public.vector(1024),

                    -- Source and versioning
                    source VARCHAR(100) DEFAULT 'manual',
                    version VARCHAR(50) DEFAULT '1.0',
                    is_active VARCHAR(10) DEFAULT 'true',

                    -- Timestamps
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ
                );

                RAISE NOTICE 'Created help_documents table';

                -- Create indexes
                CREATE INDEX IF NOT EXISTS ix_help_documents_slug
                    ON migration.help_documents(slug);
                CREATE INDEX IF NOT EXISTS ix_help_documents_category
                    ON migration.help_documents(category);
                CREATE INDEX IF NOT EXISTS ix_help_documents_flow_type
                    ON migration.help_documents(flow_type);
                CREATE INDEX IF NOT EXISTS ix_help_documents_route
                    ON migration.help_documents(route);

                -- Create vector similarity index for efficient semantic search
                -- Use public schema qualified operator class
                CREATE INDEX IF NOT EXISTS ix_help_documents_embedding
                    ON migration.help_documents
                    USING ivfflat (embedding public.vector_cosine_ops)
                    WITH (lists = 100);

                RAISE NOTICE 'Created indexes for help_documents table';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Drop help_documents table."""
    op.execute(
        """
        DROP TABLE IF EXISTS migration.help_documents CASCADE;
        """
    )
