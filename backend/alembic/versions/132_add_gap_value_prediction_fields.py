"""Add gap value prediction fields

Revision ID: 132
Revises: 131
Create Date: 2025-11-15

"""

from typing import Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "132_gap_value_prediction"
down_revision: Union[str, None] = "131_ai_gap_tracking"
branch_labels = None
depends_on = None


def upgrade():
    """
    Add AI value prediction fields to collection_data_gaps table.

    These fields support Phase 3 (Agentic Gap Resolution) where AI
    predicts actual VALUES for gaps, not just suggestions.
    """
    # Use PostgreSQL DO block for idempotent migration
    op.execute(
        """
        DO $$
        BEGIN
            -- Add predicted_value column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'collection_data_gaps'
                AND column_name = 'predicted_value'
            ) THEN
                ALTER TABLE migration.collection_data_gaps
                ADD COLUMN predicted_value TEXT NULL;
            END IF;

            -- Add prediction_confidence column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'collection_data_gaps'
                AND column_name = 'prediction_confidence'
            ) THEN
                ALTER TABLE migration.collection_data_gaps
                ADD COLUMN prediction_confidence FLOAT NULL;
            END IF;

            -- Add prediction_reasoning column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'collection_data_gaps'
                AND column_name = 'prediction_reasoning'
            ) THEN
                ALTER TABLE migration.collection_data_gaps
                ADD COLUMN prediction_reasoning TEXT NULL;
            END IF;
        END $$;
    """
    )


def downgrade():
    """Remove AI value prediction fields."""
    op.execute(
        """
        DO $$
        BEGIN
            ALTER TABLE migration.collection_data_gaps
            DROP COLUMN IF EXISTS predicted_value,
            DROP COLUMN IF EXISTS prediction_confidence,
            DROP COLUMN IF EXISTS prediction_reasoning;
        END $$;
    """
    )
