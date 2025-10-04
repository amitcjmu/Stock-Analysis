"""add_two_phase_gap_analysis_columns

Revision ID: 080_add_two_phase_gap_analysis_columns
Revises: 079_create_llm_usage_logs
Create Date: 2025-10-04

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "080_add_two_phase_gap_analysis_columns"
down_revision = "079_create_llm_usage_logs"
branch_labels = None
depends_on = None


def upgrade():
    """
    Add columns for two-phase gap analysis implementation.

    New columns:
    - asset_id: Links gap to specific asset (NOT NULL for deduplication)
    - resolved_value: User-entered or AI-suggested value
    - confidence_score: AI confidence (0.0-1.0, NULL if no AI analysis)
    - ai_suggestions: JSONB array of AI suggestions
    - resolution_method: How gap was resolved (manual_entry, ai_suggestion, hybrid)
    """

    # Check if asset_id column exists
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'collection_data_gaps'
        AND column_name = 'asset_id'
    """
        )
    )
    asset_id_exists = result.fetchone() is not None

    if not asset_id_exists:
        # Add asset_id column as nullable first
        op.add_column(
            "collection_data_gaps",
            sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=True),
            schema="migration",
        )

        # CRITICAL: For existing rows, we need to handle NULL asset_ids
        # Option 1: Delete orphaned gaps without assets (recommended for fresh deployment)
        # Option 2: Set to placeholder UUID (if data preservation needed)
        # Using Option 1 as per plan - clean slate for two-phase approach
        conn.execute(
            sa.text(
                """
            DELETE FROM migration.collection_data_gaps WHERE asset_id IS NULL
        """
            )
        )

        # Now make it NOT NULL
        op.alter_column(
            "collection_data_gaps",
            "asset_id",
            existing_type=postgresql.UUID(),
            nullable=False,
            schema="migration",
        )

    # Check and add resolved_value
    result = conn.execute(
        sa.text(
            """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'collection_data_gaps'
        AND column_name = 'resolved_value'
    """
        )
    )
    if result.fetchone() is None:
        op.add_column(
            "collection_data_gaps",
            sa.Column("resolved_value", sa.Text(), nullable=True),
            schema="migration",
        )

    # Check and add confidence_score
    result = conn.execute(
        sa.text(
            """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'collection_data_gaps'
        AND column_name = 'confidence_score'
    """
        )
    )
    if result.fetchone() is None:
        op.add_column(
            "collection_data_gaps",
            sa.Column("confidence_score", sa.Float(), nullable=True),
            schema="migration",
        )

    # Check and add ai_suggestions
    result = conn.execute(
        sa.text(
            """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'collection_data_gaps'
        AND column_name = 'ai_suggestions'
    """
        )
    )
    if result.fetchone() is None:
        op.add_column(
            "collection_data_gaps",
            sa.Column(
                "ai_suggestions", postgresql.JSONB(astext_type=sa.Text()), nullable=True
            ),
            schema="migration",
        )

    # Check and add resolution_method
    result = conn.execute(
        sa.text(
            """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'collection_data_gaps'
        AND column_name = 'resolution_method'
    """
        )
    )
    if result.fetchone() is None:
        op.add_column(
            "collection_data_gaps",
            sa.Column("resolution_method", sa.String(length=50), nullable=True),
            schema="migration",
        )

        # Add CHECK constraint for resolution_method
        conn.execute(
            sa.text(
                """
            ALTER TABLE migration.collection_data_gaps
            ADD CONSTRAINT ck_resolution_method
            CHECK (resolution_method IN ('manual_entry', 'ai_suggestion', 'hybrid') OR resolution_method IS NULL)
        """
            )
        )

    # Create performance indexes if they don't exist

    # Index for flow queries
    result = conn.execute(
        sa.text(
            """
        SELECT indexname FROM pg_indexes
        WHERE schemaname = 'migration'
        AND tablename = 'collection_data_gaps'
        AND indexname = 'idx_collection_data_gaps_flow'
    """
        )
    )
    if result.fetchone() is None:
        op.create_index(
            "idx_collection_data_gaps_flow",
            "collection_data_gaps",
            ["collection_flow_id"],
            schema="migration",
        )

    # Composite unique constraint for deduplication
    result = conn.execute(
        sa.text(
            """
        SELECT constraint_name FROM information_schema.table_constraints
        WHERE table_schema = 'migration'
        AND table_name = 'collection_data_gaps'
        AND constraint_name = 'uq_gaps_dedup'
    """
        )
    )
    if result.fetchone() is None:
        op.create_unique_constraint(
            "uq_gaps_dedup",
            "collection_data_gaps",
            ["collection_flow_id", "field_name", "gap_type", "asset_id"],
            schema="migration",
        )


def downgrade():
    """
    Rollback two-phase gap analysis columns.

    CRITICAL: This will drop data (resolved_value, confidence_score, ai_suggestions).
    Only run if absolutely necessary.
    """
    conn = op.get_bind()

    # Drop unique constraint
    result = conn.execute(
        sa.text(
            """
        SELECT constraint_name FROM information_schema.table_constraints
        WHERE table_schema = 'migration'
        AND table_name = 'collection_data_gaps'
        AND constraint_name = 'uq_gaps_dedup'
    """
        )
    )
    if result.fetchone() is not None:
        op.drop_constraint(
            "uq_gaps_dedup", "collection_data_gaps", schema="migration", type_="unique"
        )

    # Drop index
    result = conn.execute(
        sa.text(
            """
        SELECT indexname FROM pg_indexes
        WHERE schemaname = 'migration'
        AND tablename = 'collection_data_gaps'
        AND indexname = 'idx_collection_data_gaps_flow'
    """
        )
    )
    if result.fetchone() is not None:
        op.drop_index(
            "idx_collection_data_gaps_flow",
            table_name="collection_data_gaps",
            schema="migration",
        )

    # Drop CHECK constraint
    result = conn.execute(
        sa.text(
            """
        SELECT constraint_name FROM information_schema.table_constraints
        WHERE table_schema = 'migration'
        AND table_name = 'collection_data_gaps'
        AND constraint_name = 'ck_resolution_method'
    """
        )
    )
    if result.fetchone() is not None:
        op.drop_constraint(
            "ck_resolution_method",
            "collection_data_gaps",
            schema="migration",
            type_="check",
        )

    # Drop columns if they exist
    result = conn.execute(
        sa.text(
            """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'collection_data_gaps'
        AND column_name = 'resolution_method'
    """
        )
    )
    if result.fetchone() is not None:
        op.drop_column("collection_data_gaps", "resolution_method", schema="migration")

    result = conn.execute(
        sa.text(
            """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'collection_data_gaps'
        AND column_name = 'ai_suggestions'
    """
        )
    )
    if result.fetchone() is not None:
        op.drop_column("collection_data_gaps", "ai_suggestions", schema="migration")

    result = conn.execute(
        sa.text(
            """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'collection_data_gaps'
        AND column_name = 'confidence_score'
    """
        )
    )
    if result.fetchone() is not None:
        op.drop_column("collection_data_gaps", "confidence_score", schema="migration")

    result = conn.execute(
        sa.text(
            """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'collection_data_gaps'
        AND column_name = 'resolved_value'
    """
        )
    )
    if result.fetchone() is not None:
        op.drop_column("collection_data_gaps", "resolved_value", schema="migration")

    result = conn.execute(
        sa.text(
            """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'collection_data_gaps'
        AND column_name = 'asset_id'
    """
        )
    )
    if result.fetchone() is not None:
        op.drop_column("collection_data_gaps", "asset_id", schema="migration")
