"""Add user_name field to feedback table for displaying who submitted feedback

Revision ID: 144_add_feedback_user_tracking
Revises: 143_create_feedback_tables
Create Date: 2025-12-04
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "144_add_feedback_user_tracking"
down_revision = "143_create_feedback_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user_name column to feedback table."""
    op.execute(
        """
        DO $$
        BEGIN
            -- Add user_name column if not exists (display name only for privacy)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'feedback'
                AND column_name = 'user_name'
            ) THEN
                ALTER TABLE migration.feedback ADD COLUMN user_name VARCHAR(255);
                RAISE NOTICE 'Added user_name column to feedback table';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Remove user_name column."""
    op.execute(
        """
        ALTER TABLE migration.feedback DROP COLUMN IF EXISTS user_name;
        """
    )
