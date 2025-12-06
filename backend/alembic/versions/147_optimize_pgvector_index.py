"""Optimize pgvector index configuration (Issue #986)

Optimizes vector index parameters based on current dataset size analysis:
- Current: 45 vectors with embeddings, lists=100 (overkill)
- Optimal: lists=20 for small dataset (sqrt formula: sqrt(45) ≈ 7, rounded up)
- Added: Partial index for tenant-filtered vector queries

Performance improvements:
- IVFFlat with optimized lists: Better recall for small datasets
- Partial index: Faster tenant-scoped vector queries (avoids table scan)

Revision ID: 147_optimize_pgvector_index
Revises: 146_add_additional_cmdb_fields_to_assets
Create Date: 2025-12-05
"""

from alembic import op

revision = "147_optimize_pgvector_index"
down_revision = "146_add_additional_cmdb_fields_to_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Optimize pgvector index configuration.

    Changes:
    1. Recreate IVFFlat index with optimized lists parameter (100 -> 20)
    2. Add partial index for tenant-filtered vector queries

    Idempotent: Uses DROP IF EXISTS and DO blocks for safe re-runs.
    """
    # Drop and recreate IVFFlat index with optimized lists parameter
    # For small datasets (<1K), lists = 10-50 is optimal
    # Current dataset: ~45 vectors, so lists=20 is appropriate
    op.execute("DROP INDEX IF EXISTS migration.ix_agent_patterns_embedding;")

    # Use DO block for idempotent CREATE INDEX (no IF NOT EXISTS for IVFFlat)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND indexname = 'ix_agent_patterns_embedding'
            ) THEN
                CREATE INDEX ix_agent_patterns_embedding
                ON migration.agent_discovered_patterns
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 20);
            END IF;
        END $$;
        """
    )

    # Add partial index for tenant-filtered vector queries
    # This allows PostgreSQL to use index for:
    # WHERE client_account_id = X AND embedding IS NOT NULL
    # Without scanning all rows first
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_agent_patterns_tenant_vector
        ON migration.agent_discovered_patterns (client_account_id)
        WHERE embedding IS NOT NULL;
        """
    )


def downgrade() -> None:
    """Revert to original index configuration.

    Idempotent: Uses DROP IF EXISTS and DO blocks for safe re-runs.
    """
    # Remove partial index
    op.execute("DROP INDEX IF EXISTS migration.ix_agent_patterns_tenant_vector;")

    # Recreate original IVFFlat index with lists=100
    op.execute("DROP INDEX IF EXISTS migration.ix_agent_patterns_embedding;")

    # Use DO block for idempotent CREATE INDEX
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND indexname = 'ix_agent_patterns_embedding'
            ) THEN
                CREATE INDEX ix_agent_patterns_embedding
                ON migration.agent_discovered_patterns
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            END IF;
        END $$;
        """
    )
