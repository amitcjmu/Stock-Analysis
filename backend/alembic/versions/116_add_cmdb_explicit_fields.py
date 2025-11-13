"""Add CMDB explicit fields to assets table

Adds 24 high-value explicit columns for enhanced CMDB support.
Supports Issue #833 hybrid architecture approach.

Revision ID: 116_add_cmdb_explicit_fields
Revises: 111_remove_sixr_analysis_tables
Create Date: 2025-10-28 14:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "116_add_cmdb_explicit_fields"
down_revision = "111_remove_sixr_analysis_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add 24 explicit columns to assets table.

    IDEMPOTENT: Uses IF NOT EXISTS checks for all additions.
    """
    op.execute(
        """
        DO $$
        BEGIN
            -- Business/Organizational Fields
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'business_unit'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN business_unit VARCHAR(100);

                COMMENT ON COLUMN migration.assets.business_unit IS
                'Business unit owning the asset';

                CREATE INDEX idx_assets_business_unit
                ON migration.assets(business_unit);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'vendor'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN vendor VARCHAR(255);

                COMMENT ON COLUMN migration.assets.vendor IS
                'Vendor or manufacturer name';

                CREATE INDEX idx_assets_vendor
                ON migration.assets(vendor);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'application_type'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN application_type VARCHAR(20);

                COMMENT ON COLUMN migration.assets.application_type IS
                'Application type: cots, custom, custom_cots, other';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'lifecycle'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN lifecycle VARCHAR(20);

                COMMENT ON COLUMN migration.assets.lifecycle IS
                'Asset lifecycle status: retire, replace, retain, invest';

                CREATE INDEX idx_assets_lifecycle
                ON migration.assets(lifecycle);
            END IF;

            -- Infrastructure Fields
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'hosting_model'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN hosting_model VARCHAR(20);

                COMMENT ON COLUMN migration.assets.hosting_model IS
                'Hosting model: on_prem, cloud, hybrid, colo';

                CREATE INDEX idx_assets_hosting_model
                ON migration.assets(hosting_model);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'server_role'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN server_role VARCHAR(20);

                COMMENT ON COLUMN migration.assets.server_role IS
                'Server role: web, db, app, citrix, file, email, other';

                CREATE INDEX idx_assets_server_role
                ON migration.assets(server_role);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'security_zone'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN security_zone VARCHAR(50);

                COMMENT ON COLUMN migration.assets.security_zone IS
                'Network security zone or segment';
            END IF;

            -- Database Fields
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'database_type'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN database_type VARCHAR(100);

                COMMENT ON COLUMN migration.assets.database_type IS
                'Primary database platform name';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'database_version'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN database_version VARCHAR(50);

                COMMENT ON COLUMN migration.assets.database_version IS
                'Database version string';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'database_size_gb'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN database_size_gb DOUBLE PRECISION;

                COMMENT ON COLUMN migration.assets.database_size_gb IS
                'Database size in gigabytes';
            END IF;

            -- Performance/Capacity Fields
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'cpu_utilization_percent_max'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN cpu_utilization_percent_max DOUBLE PRECISION;

                COMMENT ON COLUMN migration.assets.cpu_utilization_percent_max IS
                'Peak CPU utilization percentage';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'memory_utilization_percent_max'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN memory_utilization_percent_max DOUBLE PRECISION;

                COMMENT ON COLUMN migration.assets.memory_utilization_percent_max IS
                'Peak memory utilization percentage';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'storage_free_gb'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN storage_free_gb DOUBLE PRECISION;

                COMMENT ON COLUMN migration.assets.storage_free_gb IS
                'Available storage in gigabytes';
            END IF;

            -- Compliance/Security Fields
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'pii_flag'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN pii_flag BOOLEAN DEFAULT false;

                COMMENT ON COLUMN migration.assets.pii_flag IS
                'Contains Personally Identifiable Information';

                CREATE INDEX idx_assets_pii_flag
                ON migration.assets(pii_flag);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'application_data_classification'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN application_data_classification VARCHAR(50);

                COMMENT ON COLUMN migration.assets.application_data_classification IS
                'Data sensitivity classification level';
            END IF;

            -- Migration Planning Fields
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'has_saas_replacement'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN has_saas_replacement BOOLEAN;

                COMMENT ON COLUMN migration.assets.has_saas_replacement IS
                'SaaS alternative available for this asset';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'risk_level'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN risk_level VARCHAR(20);

                COMMENT ON COLUMN migration.assets.risk_level IS
                'Migration risk level: low, medium, high, critical';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'tshirt_size'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN tshirt_size VARCHAR(10);

                COMMENT ON COLUMN migration.assets.tshirt_size IS
                'Complexity sizing: xs, s, m, l, xl, xxl';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'proposed_treatmentplan_rationale'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN proposed_treatmentplan_rationale TEXT;

                COMMENT ON COLUMN migration.assets.proposed_treatmentplan_rationale IS
                'Rationale for proposed migration treatment plan';
            END IF;

            -- Financial/Operational Fields
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'annual_cost_estimate'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN annual_cost_estimate DOUBLE PRECISION;

                COMMENT ON COLUMN migration.assets.annual_cost_estimate IS
                'Estimated annual operational cost';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'backup_policy'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN backup_policy TEXT;

                COMMENT ON COLUMN migration.assets.backup_policy IS
                'Backup and recovery policy details';
            END IF;

            -- Metadata Fields
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'asset_tags'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN asset_tags JSONB DEFAULT '[]'::jsonb;

                COMMENT ON COLUMN migration.assets.asset_tags IS
                'Asset tags and labels as JSONB array';

                -- GIN index for JSONB queries
                CREATE INDEX idx_assets_asset_tags_gin
                ON migration.assets USING GIN (asset_tags);
            END IF;

        END $$;
        """
    )


def downgrade() -> None:
    """
    Remove added columns.

    WARNING: This drops columns and loses data!
    """
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop indexes first
            DROP INDEX IF EXISTS migration.idx_assets_business_unit;
            DROP INDEX IF EXISTS migration.idx_assets_vendor;
            DROP INDEX IF EXISTS migration.idx_assets_lifecycle;
            DROP INDEX IF EXISTS migration.idx_assets_hosting_model;
            DROP INDEX IF EXISTS migration.idx_assets_server_role;
            DROP INDEX IF EXISTS migration.idx_assets_pii_flag;
            DROP INDEX IF EXISTS migration.idx_assets_asset_tags_gin;

            -- Drop columns
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS business_unit;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS vendor;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS application_type;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS lifecycle;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS hosting_model;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS server_role;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS security_zone;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS database_type;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS database_version;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS database_size_gb;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS cpu_utilization_percent_max;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS memory_utilization_percent_max;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS storage_free_gb;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS pii_flag;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS application_data_classification;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS has_saas_replacement;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS risk_level;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS tshirt_size;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS proposed_treatmentplan_rationale;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS annual_cost_estimate;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS backup_policy;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS asset_tags;
        END $$;
        """
    )
