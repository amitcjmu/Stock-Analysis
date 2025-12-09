"""Add password reset columns to users table.

Revision ID: 154_add_password_reset_columns
Revises: 153_add_component_asset_type
Create Date: 2025-12-08

Adds columns for password reset functionality:
- password_reset_token: Hashed token for password reset (indexed)
- password_reset_token_expires_at: Expiration timestamp for the token
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "154_add_password_reset_columns"
down_revision = "153_add_component_asset_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add password reset columns to users table."""
    # Use DO block for idempotent column addition
    op.execute(
        """
        DO $$
        BEGIN
            -- Add password_reset_token column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'users'
                AND column_name = 'password_reset_token'
            ) THEN
                ALTER TABLE migration.users
                ADD COLUMN password_reset_token VARCHAR(255);

                COMMENT ON COLUMN migration.users.password_reset_token IS
                    'Hashed token for password reset. Expires after 15 minutes.';
            END IF;

            -- Add password_reset_token_expires_at column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'users'
                AND column_name = 'password_reset_token_expires_at'
            ) THEN
                ALTER TABLE migration.users
                ADD COLUMN password_reset_token_expires_at TIMESTAMP WITH TIME ZONE;

                COMMENT ON COLUMN migration.users.password_reset_token_expires_at IS
                    'Expiration timestamp for the password reset token.';
            END IF;
        END $$;
        """
    )

    # Create index on password_reset_token for fast lookups (idempotent)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_users_password_reset_token
        ON migration.users (password_reset_token)
        WHERE password_reset_token IS NOT NULL;
        """
    )


def downgrade() -> None:
    """Remove password reset columns from users table."""
    op.execute(
        """
        DROP INDEX IF EXISTS migration.ix_users_password_reset_token;
        """
    )
    op.execute(
        """
        ALTER TABLE migration.users
        DROP COLUMN IF EXISTS password_reset_token_expires_at;
        """
    )
    op.execute(
        """
        ALTER TABLE migration.users
        DROP COLUMN IF EXISTS password_reset_token;
        """
    )
