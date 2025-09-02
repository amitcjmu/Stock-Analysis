"""Add vector search capability to agent discovered patterns

Revision ID: 017_add_vector_search_to_agent_patterns
Revises: 016_add_security_constraints
Create Date: 2025-01-24

This migration adds vector embedding support to the agent_discovered_patterns table
for AI-powered similarity search capabilities.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "017_add_vector_search_to_agent_patterns"
down_revision = "016_add_security_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add vector search capability to agent discovered patterns"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Ensure pgvector extension is available
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add vector embedding column for similarity search
    # Check if column already exists

    conn = op.get_bind()

    result = conn.execute(
        sa.text(
            """

        SELECT column_name

        FROM information_schema.columns

        WHERE table_schema = 'migration'

        AND table_name = 'agent_discovered_patterns'

        AND column_name = 'embedding'

    """
        )
    )

    if not result.fetchone():

        op.add_column(
            "agent_discovered_patterns",
            sa.Column(
                "embedding",
                postgresql.ARRAY(
                    sa.Float, dimensions=1536
                ),  # OpenAI embedding dimension
                nullable=True,  # Allow null initially for existing records
                comment="Vector embedding for similarity search",
            ),
            schema="migration",
        )

    # Add insight_type column for structured pattern classification
    # Check if column already exists

    conn = op.get_bind()

    result = conn.execute(
        sa.text(
            """

        SELECT column_name

        FROM information_schema.columns

        WHERE table_schema = 'migration'

        AND table_name = 'agent_discovered_patterns'

        AND column_name = 'insight_type'

    """
        )
    )

    if not result.fetchone():

        op.add_column(
            "agent_discovered_patterns",
            sa.Column(
                "insight_type",
                sa.String(50),
                nullable=True,  # Allow null initially for existing records
                comment="Structured classification of the pattern type",
            ),
            schema="migration",
        )

    # Create check constraint for insight_type values
    op.create_check_constraint(
        "ck_agent_patterns_insight_type",
        "agent_discovered_patterns",
        sa.text(
            """
            insight_type IS NULL OR insight_type IN (
                'field_mapping_suggestion',
                'risk_pattern',
                'optimization_opportunity',
                'anomaly_detection',
                'workflow_improvement',
                'dependency_pattern',
                'performance_pattern',
                'error_pattern'
            )
        """
        ),
        schema="migration",
    )

    # Create vector similarity index using ivfflat
    op.execute(
        """
        DO $$
        BEGIN
            -- Create vector index for similarity search
            -- Using ivfflat index for fast approximate nearest neighbor search
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

    # Create index on insight_type for filtering during similarity search
    # Check if index already exists

    conn = op.get_bind()

    result = conn.execute(
        sa.text(
            """

        SELECT indexname

        FROM pg_indexes

        WHERE schemaname = 'migration'

        AND indexname = 'ix_agent_patterns_insight_type'

    """
        )
    )

    if not result.fetchone():

        op.create_index(
            "ix_agent_patterns_insight_type",
            "agent_discovered_patterns",
            ["insight_type"],
            schema="migration",
        )

    # Create composite index for multi-tenant similarity queries
    # Check if index already exists

    conn = op.get_bind()

    result = conn.execute(
        sa.text(
            """

        SELECT indexname

        FROM pg_indexes

        WHERE schemaname = 'migration'

        AND indexname = 'ix_agent_patterns_client_insight_type'

    """
        )
    )

    if not result.fetchone():

        op.create_index(
            "ix_agent_patterns_client_insight_type",
            "agent_discovered_patterns",
            ["client_account_id", "insight_type"],
            schema="migration",
        )

    print("✅ Vector search capability added to agent_discovered_patterns")


def downgrade() -> None:
    """Remove vector search capability"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Drop indexes
    op.drop_index(
        "ix_agent_patterns_client_insight_type",
        table_name="agent_discovered_patterns",
        schema="migration",
    )
    op.drop_index(
        "ix_agent_patterns_insight_type",
        table_name="agent_discovered_patterns",
        schema="migration",
    )
    op.execute("DROP INDEX IF EXISTS migration.ix_agent_patterns_embedding")

    # Drop check constraint
    op.drop_constraint(
        "ck_agent_patterns_insight_type",
        "agent_discovered_patterns",
        schema="migration",
    )

    # Drop columns
    op.drop_column("agent_discovered_patterns", "insight_type", schema="migration")
    op.drop_column("agent_discovered_patterns", "embedding", schema="migration")

    print("✅ Vector search capability removed from agent_discovered_patterns")
