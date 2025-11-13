"""add refresh tokens table

Revision ID: 122_add_refresh_tokens_table
Revises: 121_backfill_assessment_source_collection
Create Date: 2025-10-30

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "122_add_refresh_tokens_table"
down_revision: Union[str, None] = "121_backfill_assessment_source_collection"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add refresh_tokens table for JWT token rotation."""

    # Check if table exists before creating
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'refresh_tokens'
            ) THEN
                CREATE TABLE migration.refresh_tokens (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    token VARCHAR(500) NOT NULL UNIQUE,
                    user_id UUID NOT NULL REFERENCES migration.users(id) ON DELETE CASCADE,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
                    revoked_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    last_used_at TIMESTAMP WITH TIME ZONE,
                    user_agent VARCHAR(500),
                    ip_address VARCHAR(45)
                );

                -- Create indexes for performance
                CREATE INDEX IF NOT EXISTS ix_refresh_tokens_id ON migration.refresh_tokens(id);
                CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token ON migration.refresh_tokens(token);
                CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON migration.refresh_tokens(user_id);
                CREATE INDEX IF NOT EXISTS ix_refresh_tokens_is_revoked ON migration.refresh_tokens(is_revoked);

                -- Add comments
                COMMENT ON TABLE migration.refresh_tokens IS
                    'Stores refresh tokens for JWT token rotation';
                COMMENT ON COLUMN migration.refresh_tokens.id IS
                    'Unique identifier for the refresh token';
                COMMENT ON COLUMN migration.refresh_tokens.token IS
                    'The actual refresh token string (hashed)';
                COMMENT ON COLUMN migration.refresh_tokens.user_id IS
                    'The user this refresh token belongs to';
                COMMENT ON COLUMN migration.refresh_tokens.expires_at IS
                    'When this refresh token expires';
                COMMENT ON COLUMN migration.refresh_tokens.is_revoked IS
                    'Whether this token has been revoked (for token rotation)';
                COMMENT ON COLUMN migration.refresh_tokens.revoked_at IS
                    'When this token was revoked';
                COMMENT ON COLUMN migration.refresh_tokens.created_at IS
                    'When this token was created';
                COMMENT ON COLUMN migration.refresh_tokens.last_used_at IS
                    'When this token was last used to refresh access token';
                COMMENT ON COLUMN migration.refresh_tokens.user_agent IS
                    'User agent of client that created token (security tracking)';
                COMMENT ON COLUMN migration.refresh_tokens.ip_address IS
                    'IP address of client that created token (security tracking)';

                RAISE NOTICE 'Created refresh_tokens table successfully';
            ELSE
                RAISE NOTICE 'Table refresh_tokens already exists, skipping creation';
            END IF;
        END
        $$;
    """
    )


def downgrade() -> None:
    """Remove refresh_tokens table."""

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'refresh_tokens'
            ) THEN
                DROP TABLE IF EXISTS migration.refresh_tokens CASCADE;
                RAISE NOTICE 'Dropped refresh_tokens table successfully';
            ELSE
                RAISE NOTICE 'Table refresh_tokens does not exist, skipping drop';
            END IF;
        END
        $$;
    """
    )
