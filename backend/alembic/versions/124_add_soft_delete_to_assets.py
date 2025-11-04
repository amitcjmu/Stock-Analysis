"""add_soft_delete_to_assets

Add soft delete support to assets table with deleted_at, deleted_by columns
and indexes for efficient trash view and filtering.

Revision ID: 124_add_soft_delete_to_assets
Revises: 123_add_confidence_score_to_asset_dependencies
Create Date: 2025-11-04 00:00:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "124_add_soft_delete_to_assets"
down_revision = "123_add_confidence_score_to_asset_dependencies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add soft delete support to assets table.

    IDEMPOTENT: Uses IF NOT EXISTS checks for column and index additions.
    """
    # Add deleted_at column
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'deleted_at'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
            END IF;
        END $$;
        """
    )

    # Add deleted_by column
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'deleted_by'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN deleted_by UUID DEFAULT NULL;
            END IF;
        END $$;
        """
    )

    # Add index for active (non-deleted) assets
    # This is a partial index for efficient filtering of active assets
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assets'
                AND indexname = 'idx_assets_active'
            ) THEN
                CREATE INDEX idx_assets_active ON migration.assets (client_account_id, engagement_id)
                WHERE deleted_at IS NULL;
            END IF;
        END $$;
        """
    )

    # Add index for deleted assets (trash view)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assets'
                AND indexname = 'idx_assets_deleted'
            ) THEN
                CREATE INDEX idx_assets_deleted ON migration.assets (client_account_id, engagement_id, deleted_at)
                WHERE deleted_at IS NOT NULL;
            END IF;
        END $$;
        """
    )

    # Add foreign key constraint for deleted_by referencing users table
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE constraint_schema = 'migration'
                AND table_name = 'assets'
                AND constraint_name = 'fk_assets_deleted_by_users'
            ) THEN
                ALTER TABLE migration.assets
                ADD CONSTRAINT fk_assets_deleted_by_users
                FOREIGN KEY (deleted_by) REFERENCES migration.users(id) ON DELETE SET NULL;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """
    Remove soft delete support from assets table.

    IDEMPOTENT: Uses IF EXISTS checks for constraint, index, and column removal.
    """
    # Drop foreign key constraint
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE constraint_schema = 'migration'
                AND table_name = 'assets'
                AND constraint_name = 'fk_assets_deleted_by_users'
            ) THEN
                ALTER TABLE migration.assets
                DROP CONSTRAINT fk_assets_deleted_by_users;
            END IF;
        END $$;
        """
    )

    # Drop deleted assets index
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assets'
                AND indexname = 'idx_assets_deleted'
            ) THEN
                DROP INDEX migration.idx_assets_deleted;
            END IF;
        END $$;
        """
    )

    # Drop active assets index
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assets'
                AND indexname = 'idx_assets_active'
            ) THEN
                DROP INDEX migration.idx_assets_active;
            END IF;
        END $$;
        """
    )

    # Drop deleted_by column
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'deleted_by'
            ) THEN
                ALTER TABLE migration.assets
                DROP COLUMN deleted_by;
            END IF;
        END $$;
        """
    )

    # Drop deleted_at column
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'deleted_at'
            ) THEN
                ALTER TABLE migration.assets
                DROP COLUMN deleted_at;
            END IF;
        END $$;
        """
    )
