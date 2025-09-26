"""Add username to users table

Revision ID: add_username_to_users
Revises: 077_update_collection_flow_enum
Create Date: 2025-01-26

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "add_username_to_users"
down_revision = "077_update_collection_flow_enum"
branch_labels = None
depends_on = None


def upgrade():
    # Add username column to users table if it doesn't exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                         WHERE table_schema = 'migration'
                         AND table_name = 'users'
                         AND column_name = 'username') THEN
                ALTER TABLE migration.users
                ADD COLUMN username VARCHAR(50) UNIQUE;

                CREATE INDEX IF NOT EXISTS ix_migration_users_username
                ON migration.users(username);
            END IF;
        END $$;
    """
    )


def downgrade():
    # Remove username column from users table
    op.execute(
        """
        ALTER TABLE migration.users
        DROP COLUMN IF EXISTS username;
    """
    )
