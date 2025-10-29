"""Enhance asset_dependencies for network discovery

Adds network flow metadata columns for network discovery integration.
Supports Issue #833 hybrid architecture approach.

Revision ID: 112_enhance_asset_dependencies_network_discovery
Revises: 111_create_cmdb_specialized_tables
Create Date: 2025-10-28 15:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "114_enhance_asset_dependencies_network_discovery"
down_revision = "113_create_cmdb_specialized_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add network discovery columns to asset_dependencies.

    IDEMPOTENT: Uses IF NOT EXISTS for column additions.
    """
    op.execute(
        """
        DO $$
        BEGIN
            -- Add port column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'port'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                ADD COLUMN port INTEGER;

                COMMENT ON COLUMN migration.asset_dependencies.port IS
                'Network port for connection';
            END IF;

            -- Add protocol_name column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'protocol_name'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                ADD COLUMN protocol_name VARCHAR(50);

                COMMENT ON COLUMN migration.asset_dependencies.protocol_name IS
                'Protocol name (TCP, UDP, HTTP, etc.)';
            END IF;

            -- Add conn_count column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'conn_count'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                ADD COLUMN conn_count INTEGER;

                COMMENT ON COLUMN migration.asset_dependencies.conn_count IS
                'Number of connections observed';
            END IF;

            -- Add bytes_total column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'bytes_total'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                ADD COLUMN bytes_total BIGINT;

                COMMENT ON COLUMN migration.asset_dependencies.bytes_total IS
                'Total bytes transferred';
            END IF;

            -- Add first_seen column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'first_seen'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                ADD COLUMN first_seen TIMESTAMP WITH TIME ZONE;

                COMMENT ON COLUMN migration.asset_dependencies.first_seen IS
                'First detection timestamp';
            END IF;

            -- Add last_seen column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'asset_dependencies'
                AND column_name = 'last_seen'
            ) THEN
                ALTER TABLE migration.asset_dependencies
                ADD COLUMN last_seen TIMESTAMP WITH TIME ZONE;

                COMMENT ON COLUMN migration.asset_dependencies.last_seen IS
                'Last detection timestamp';

                CREATE INDEX idx_asset_dependencies_last_seen
                ON migration.asset_dependencies(last_seen);
            END IF;

        END $$;
        """
    )


def downgrade() -> None:
    """
    Remove network discovery columns.

    WARNING: This drops columns and loses data!
    """
    op.execute(
        """
        DO $$
        BEGIN
            DROP INDEX IF EXISTS migration.idx_asset_dependencies_last_seen;

            ALTER TABLE migration.asset_dependencies DROP COLUMN IF EXISTS port;
            ALTER TABLE migration.asset_dependencies DROP COLUMN IF EXISTS protocol_name;
            ALTER TABLE migration.asset_dependencies DROP COLUMN IF EXISTS conn_count;
            ALTER TABLE migration.asset_dependencies DROP COLUMN IF EXISTS bytes_total;
            ALTER TABLE migration.asset_dependencies DROP COLUMN IF EXISTS first_seen;
            ALTER TABLE migration.asset_dependencies DROP COLUMN IF EXISTS last_seen;
        END $$;
        """
    )
