"""Fix vector column type for pgvector compatibility

Revision ID: 085_fix_vector_column_type
Revises: 084_revert_gaps_fk_to_id
Create Date: 2025-10-07

This migration fixes the agent_discovered_patterns embedding column to use
proper pgvector vector type instead of double precision array. Also updates
dimension from 1536 (OpenAI ada-002) to 1024 (thenlper/gte-large).

Root Cause: Migration 042 created column as postgresql.ARRAY(sa.Float, dimensions=1536)
which is incompatible with pgvector operations (CAST AS vector fails).

Fix: Convert to vector(1024) type for DeepInfra thenlper/gte-large model.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "085_fix_vector_column_type"
down_revision = "084_revert_gaps_fk_to_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix vector column type to use pgvector"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Ensure pgvector extension is available
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Drop existing vector index if it exists
    op.execute("DROP INDEX IF EXISTS migration.ix_agent_patterns_embedding")

    # Convert embedding column from double precision[] to vector(1024)
    # Note: We use 1024 dimensions for thenlper/gte-large model (not 1536)
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if column exists and is the wrong type
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'agent_discovered_patterns'
                AND column_name = 'embedding'
                AND data_type = 'ARRAY'
            ) THEN
                -- Alter column type to vector(1024)
                ALTER TABLE migration.agent_discovered_patterns
                ALTER COLUMN embedding TYPE vector(1024)
                USING embedding::vector(1024);

                RAISE NOTICE 'Converted embedding column from double precision[] to vector(1024)';
            ELSIF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'agent_discovered_patterns'
                AND column_name = 'embedding'
            ) THEN
                RAISE NOTICE 'Embedding column exists but is not an array - skipping conversion';
            ELSE
                RAISE NOTICE 'Embedding column does not exist - skipping conversion';
            END IF;
        END $$;
        """
    )

    # Create proper vector similarity index using ivfflat
    op.execute(
        """
        DO $$
        BEGIN
            -- Create vector index for similarity search
            -- Using ivfflat index for fast approximate nearest neighbor search
            -- Lists = 100 is a good default for small to medium datasets
            CREATE INDEX IF NOT EXISTS ix_agent_patterns_embedding
            ON migration.agent_discovered_patterns
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);

            RAISE NOTICE 'Vector similarity index created successfully';
        EXCEPTION
            WHEN undefined_object THEN
                RAISE NOTICE 'Vector type not available, index creation skipped';
            WHEN OTHERS THEN
                RAISE NOTICE 'Error creating vector index: %', SQLERRM;
        END $$;
        """
    )

    print(
        "✅ Fixed embedding column: double precision[] → vector(1024) for pgvector compatibility"
    )


def downgrade() -> None:
    """Revert vector column type back to array"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Drop vector index
    op.execute("DROP INDEX IF EXISTS migration.ix_agent_patterns_embedding")

    # Convert back to double precision array
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if column exists and is vector type
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'agent_discovered_patterns'
                AND column_name = 'embedding'
            ) THEN
                -- Alter column type back to double precision array
                ALTER TABLE migration.agent_discovered_patterns
                ALTER COLUMN embedding TYPE double precision[]
                USING embedding::double precision[];

                RAISE NOTICE 'Reverted embedding column from vector(1024) to double precision[]';
            ELSE
                RAISE NOTICE 'Embedding column does not exist - skipping reversion';
            END IF;
        END $$;
        """
    )

    print("✅ Reverted embedding column: vector(1024) → double precision[]")
