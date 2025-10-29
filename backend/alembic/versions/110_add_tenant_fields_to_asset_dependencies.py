"""Add multi-tenant fields to asset_dependencies

Revision ID: 110_add_tenant_fields_to_asset_dependencies
Revises: 109_add_sixr_blocked_status
Create Date: 2025-10-28

SECURITY FIX: Add client_account_id and engagement_id to asset_dependencies
for proper multi-tenant isolation. This prevents cross-tenant data access.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision = "110_add_tenant_fields_to_asset_dependencies"
down_revision: Union[str, None] = "109_add_sixr_blocked_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add multi-tenant fields to asset_dependencies table"""

    # Use DO block for idempotency
    op.execute(
        """
        DO $$
        BEGIN
            -- Add client_account_id column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'client_account_id'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                ADD COLUMN client_account_id UUID;

                -- Backfill client_account_id from the asset table
                UPDATE migration.asset_dependencies ad
                SET client_account_id = a.client_account_id
                FROM migration.assets a
                WHERE ad.asset_id = a.id;

                -- Make it NOT NULL after backfill
                ALTER TABLE migration.asset_dependencies
                ALTER COLUMN client_account_id SET NOT NULL;

                -- Add foreign key constraint
                ALTER TABLE migration.asset_dependencies
                ADD CONSTRAINT fk_asset_dependencies_client_account
                FOREIGN KEY (client_account_id)
                REFERENCES migration.client_accounts(id)
                ON DELETE CASCADE;
            END IF;

            -- Add engagement_id column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'engagement_id'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                ADD COLUMN engagement_id UUID;

                -- Backfill engagement_id from the asset table
                UPDATE migration.asset_dependencies ad
                SET engagement_id = a.engagement_id
                FROM migration.assets a
                WHERE ad.asset_id = a.id;

                -- Make it NOT NULL after backfill
                ALTER TABLE migration.asset_dependencies
                ALTER COLUMN engagement_id SET NOT NULL;

                -- Add foreign key constraint
                ALTER TABLE migration.asset_dependencies
                ADD CONSTRAINT fk_asset_dependencies_engagement
                FOREIGN KEY (engagement_id)
                REFERENCES migration.engagements(id)
                ON DELETE CASCADE;
            END IF;

            -- Add criticality column if not exists (for dependency prioritization)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'criticality'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                ADD COLUMN criticality VARCHAR(20) DEFAULT 'medium';
            END IF;

            -- Create composite index for tenant scoping if not exists
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'asset_dependencies'
                AND indexname = 'idx_asset_dependencies_tenant_scoping'
            ) THEN
                CREATE INDEX idx_asset_dependencies_tenant_scoping
                ON migration.asset_dependencies(client_account_id, engagement_id);
            END IF;

            -- Create index on engagement_id if not exists
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'asset_dependencies'
                AND indexname = 'idx_asset_dependencies_engagement_id'
            ) THEN
                CREATE INDEX idx_asset_dependencies_engagement_id
                ON migration.asset_dependencies(engagement_id);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Remove multi-tenant fields from asset_dependencies table"""
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop indexes if they exist
            IF EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'asset_dependencies'
                AND indexname = 'idx_asset_dependencies_tenant_scoping'
            ) THEN
                DROP INDEX IF EXISTS migration.idx_asset_dependencies_tenant_scoping;
            END IF;

            IF EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'asset_dependencies'
                AND indexname = 'idx_asset_dependencies_engagement_id'
            ) THEN
                DROP INDEX IF EXISTS migration.idx_asset_dependencies_engagement_id;
            END IF;

            -- Drop columns if they exist
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'client_account_id'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                DROP COLUMN IF EXISTS client_account_id CASCADE;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'engagement_id'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                DROP COLUMN IF EXISTS engagement_id CASCADE;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'criticality'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                DROP COLUMN IF EXISTS criticality;
            END IF;
        END $$;
        """
    )
