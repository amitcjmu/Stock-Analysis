"""Add additional CMDB fields to assets table

Adds serial_number, architecture_type, and asset_status columns for enhanced CMDB support.

Revision ID: 146_add_additional_cmdb_fields_to_assets
Revises: 144_add_feedback_user_tracking
Create Date: 2025-12-05
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "146_add_additional_cmdb_fields_to_assets"
down_revision = "144_add_feedback_user_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add serial_number, architecture_type, and asset_status columns."""
    op.execute(
        """
        DO $$
        BEGIN
            -- Add serial_number column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'serial_number'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN serial_number VARCHAR(100);

                CREATE INDEX IF NOT EXISTS ix_assets_serial_number
                ON migration.assets(serial_number);

                COMMENT ON COLUMN migration.assets.serial_number IS
                    'Serial number or unique identifier for the asset';
            END IF;

            -- Add architecture_type column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'architecture_type'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN architecture_type VARCHAR(20);

                CREATE INDEX IF NOT EXISTS ix_assets_architecture_type
                ON migration.assets(architecture_type);

                COMMENT ON COLUMN migration.assets.architecture_type IS
                    'Application architecture type: monolithic, microservices, serverless, hybrid';
            END IF;

            -- Add asset_status column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'asset_status'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN asset_status VARCHAR(50);

                CREATE INDEX IF NOT EXISTS ix_assets_asset_status
                ON migration.assets(asset_status);

                COMMENT ON COLUMN migration.assets.asset_status IS
                    'Current operational status of the asset '
                    '(e.g., ''active'', ''inactive'', ''maintenance'', ''decommissioned'')';
            END IF;
        END $$;
    """
    )


def downgrade() -> None:
    """Remove serial_number, architecture_type, and asset_status columns."""
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop asset_status column if it exists
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'asset_status'
            ) THEN
                DROP INDEX IF EXISTS migration.ix_assets_asset_status;
                ALTER TABLE migration.assets
                DROP COLUMN asset_status;
            END IF;

            -- Drop architecture_type column if it exists
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'architecture_type'
            ) THEN
                DROP INDEX IF EXISTS migration.ix_assets_architecture_type;
                ALTER TABLE migration.assets
                DROP COLUMN architecture_type;
            END IF;

            -- Drop serial_number column if it exists
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'serial_number'
            ) THEN
                DROP INDEX IF EXISTS migration.ix_assets_serial_number;
                ALTER TABLE migration.assets
                DROP COLUMN serial_number;
            END IF;
        END $$;
    """
    )
