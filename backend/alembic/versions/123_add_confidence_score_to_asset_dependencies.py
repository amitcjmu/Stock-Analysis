"""Add confidence_score to asset_dependencies

Revision ID: 123
Revises: 122
Create Date: 2025-11-03

Per Issue #910: Add confidence_score field to track manual vs. auto-detected dependencies.
Manual dependencies (user-created) will have confidence_score = 1.0.
Auto-detected dependencies will have values between 0.0 and 1.0.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "123"
down_revision = "122"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add confidence_score column to asset_dependencies table."""
    # Use PostgreSQL DO block for idempotent migration
    op.execute(
        """
        DO $$
        BEGIN
            -- Add confidence_score column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'confidence_score'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                ADD COLUMN confidence_score DOUBLE PRECISION NULL;

                COMMENT ON COLUMN migration.asset_dependencies.confidence_score
                IS 'Confidence score (0.0-1.0). 1.0 = manual, <1.0 = auto-detected';

                -- Create index for filtering by confidence
                CREATE INDEX IF NOT EXISTS idx_asset_dependencies_confidence_score
                ON migration.asset_dependencies(confidence_score)
                WHERE confidence_score IS NOT NULL;
            END IF;

            -- Update existing records to have NULL confidence_score
            -- This allows us to distinguish between:
            -- - NULL: Legacy dependencies (pre-#910)
            -- - 1.0: Manual dependencies (post-#910)
            -- - <1.0: Auto-detected dependencies (post-#910)
        END $$;
        """
    )


def downgrade() -> None:
    """Remove confidence_score column from asset_dependencies table."""
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop index if exists
            DROP INDEX IF EXISTS migration.idx_asset_dependencies_confidence_score;

            -- Drop column if exists
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'confidence_score'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                DROP COLUMN confidence_score;
            END IF;
        END $$;
        """
    )
