"""Add complexity_score column to assets table

Revision ID: 108_add_complexity_score
Revises: 107_add_field_dependency_rules
Create Date: 2025-10-27

Bug #813 fix: Add complexity_score field to Asset model for 6R analysis.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "108_add_complexity_score"
down_revision = "107_add_field_dependency_rules"
branch_labels = None
depends_on = None


def upgrade():
    """Add complexity_score column for Bug #813 fix."""
    # Use PostgreSQL DO block for idempotent migration
    op.execute(
        """
        DO $$
        BEGIN
            -- Add complexity_score column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'complexity_score'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN complexity_score DOUBLE PRECISION;

                COMMENT ON COLUMN migration.assets.complexity_score IS
                    'Technical complexity score (1-10) for migration planning.';
            END IF;
        END $$;
    """
    )


def downgrade():
    """Remove complexity_score column."""
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop complexity_score column if it exists
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'complexity_score'
            ) THEN
                ALTER TABLE migration.assets
                DROP COLUMN complexity_score;
            END IF;
        END $$;
    """
    )
