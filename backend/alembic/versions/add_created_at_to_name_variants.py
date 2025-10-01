"""Add created_at column to application_name_variants

Revision ID: add_created_at_variants
Revises: add_username_to_users
Create Date: 2025-09-30 06:30:00

"""

from alembic import op

# revision identifiers
revision = "add_created_at_variants"
down_revision = "add_username_to_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add created_at column to application_name_variants
    op.execute(
        """
        ALTER TABLE migration.application_name_variants
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    """
    )


def downgrade() -> None:
    # Remove created_at column
    op.execute(
        """
        ALTER TABLE migration.application_name_variants
        DROP COLUMN IF EXISTS created_at
    """
    )
