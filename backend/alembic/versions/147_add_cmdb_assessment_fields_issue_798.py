"""Add CMDB assessment fields for issue 798

Adds 8 new columns to assets table for enhanced CMDB assessment capabilities:
- virtualization_platform, virtualization_type, data_volume_characteristics,
- user_load_patterns, business_logic_complexity, configuration_complexity,
- change_tolerance, eol_technology_assessment

Revision ID: 147_add_cmdb_assessment_fields_issue_798
Revises: 146_add_additional_cmdb_fields_to_assets
Create Date: 2025-12-05
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "147_add_cmdb_assessment_fields_issue_798"
down_revision = "146_add_additional_cmdb_fields_to_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add 8 new CMDB assessment columns with CHECK constraints."""

    # Add virtualization_platform column
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'virtualization_platform'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN virtualization_platform VARCHAR(255);

                CREATE INDEX IF NOT EXISTS ix_assets_virtualization_platform
                ON migration.assets(virtualization_platform);

                COMMENT ON COLUMN migration.assets.virtualization_platform IS
                    'Virtualization platform: VMware, Hyper-V, KVM, etc.';
            END IF;
        END $$;
        """
    )

    # Add virtualization_type column (VARCHAR with CHECK constraint)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'virtualization_type'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN virtualization_type VARCHAR(20);

                CREATE INDEX IF NOT EXISTS ix_assets_virtualization_type
                ON migration.assets(virtualization_type);

                ALTER TABLE migration.assets
                ADD CONSTRAINT chk_assets_virtualization_type
                CHECK (
                    virtualization_type IN ('virtual', 'physical', 'container', 'other')
                    OR virtualization_type IS NULL
                );

                COMMENT ON COLUMN migration.assets.virtualization_type IS
                    'Virtualization type: virtual, physical, container, other';
            END IF;
        END $$;
        """
    )

    # Add data_volume_characteristics column
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'data_volume_characteristics'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN data_volume_characteristics TEXT;

                COMMENT ON COLUMN migration.assets.data_volume_characteristics IS
                    'Data volume characteristics and patterns';
            END IF;
        END $$;
        """
    )

    # Add user_load_patterns column
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'user_load_patterns'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN user_load_patterns TEXT;

                COMMENT ON COLUMN migration.assets.user_load_patterns IS
                    'User load patterns and traffic characteristics';
            END IF;
        END $$;
        """
    )

    # Add business_logic_complexity column (VARCHAR with CHECK constraint)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'business_logic_complexity'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN business_logic_complexity VARCHAR(50);

                CREATE INDEX IF NOT EXISTS ix_assets_business_logic_complexity
                ON migration.assets(business_logic_complexity);

                ALTER TABLE migration.assets
                ADD CONSTRAINT chk_assets_business_logic_complexity
                CHECK (
                    business_logic_complexity IN ('low', 'medium', 'high', 'critical')
                    OR business_logic_complexity IS NULL
                );

                COMMENT ON COLUMN migration.assets.business_logic_complexity IS
                    'Business logic complexity: low, medium, high, critical';
            END IF;
        END $$;
        """
    )

    # Add configuration_complexity column (VARCHAR with CHECK constraint)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'configuration_complexity'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN configuration_complexity VARCHAR(50);

                CREATE INDEX IF NOT EXISTS ix_assets_configuration_complexity
                ON migration.assets(configuration_complexity);

                ALTER TABLE migration.assets
                ADD CONSTRAINT chk_assets_configuration_complexity
                CHECK (
                    configuration_complexity IN ('low', 'medium', 'high', 'critical')
                    OR configuration_complexity IS NULL
                );

                COMMENT ON COLUMN migration.assets.configuration_complexity IS
                    'Configuration complexity: low, medium, high, critical';
            END IF;
        END $$;
        """
    )

    # Add change_tolerance column (VARCHAR with CHECK constraint)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'change_tolerance'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN change_tolerance VARCHAR(50);

                CREATE INDEX IF NOT EXISTS ix_assets_change_tolerance
                ON migration.assets(change_tolerance);

                ALTER TABLE migration.assets
                ADD CONSTRAINT chk_assets_change_tolerance
                CHECK (change_tolerance IN ('low', 'medium', 'high') OR change_tolerance IS NULL);

                COMMENT ON COLUMN migration.assets.change_tolerance IS
                    'Change tolerance level: low, medium, high';
            END IF;
        END $$;
        """
    )

    # Add eol_technology_assessment column
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'eol_technology_assessment'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN eol_technology_assessment TEXT;

                COMMENT ON COLUMN migration.assets.eol_technology_assessment IS
                    'End-of-life technology assessment details';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Remove 8 CMDB assessment columns."""
    # Drop columns
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'eol_technology_assessment'
            ) THEN
                ALTER TABLE migration.assets
                DROP COLUMN eol_technology_assessment;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'change_tolerance'
            ) THEN
                ALTER TABLE migration.assets
                DROP CONSTRAINT IF EXISTS chk_assets_change_tolerance;
                DROP INDEX IF EXISTS migration.ix_assets_change_tolerance;
                ALTER TABLE migration.assets
                DROP COLUMN change_tolerance;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'configuration_complexity'
            ) THEN
                ALTER TABLE migration.assets
                DROP CONSTRAINT IF EXISTS chk_assets_configuration_complexity;
                DROP INDEX IF EXISTS migration.ix_assets_configuration_complexity;
                ALTER TABLE migration.assets
                DROP COLUMN configuration_complexity;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'business_logic_complexity'
            ) THEN
                ALTER TABLE migration.assets
                DROP CONSTRAINT IF EXISTS chk_assets_business_logic_complexity;
                DROP INDEX IF EXISTS migration.ix_assets_business_logic_complexity;
                ALTER TABLE migration.assets
                DROP COLUMN business_logic_complexity;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'user_load_patterns'
            ) THEN
                ALTER TABLE migration.assets
                DROP COLUMN user_load_patterns;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'data_volume_characteristics'
            ) THEN
                ALTER TABLE migration.assets
                DROP COLUMN data_volume_characteristics;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'virtualization_type'
            ) THEN
                ALTER TABLE migration.assets
                DROP CONSTRAINT IF EXISTS chk_assets_virtualization_type;
                DROP INDEX IF EXISTS migration.ix_assets_virtualization_type;
                ALTER TABLE migration.assets
                DROP COLUMN virtualization_type;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'assets'
                  AND column_name = 'virtualization_platform'
            ) THEN
                DROP INDEX IF EXISTS migration.ix_assets_virtualization_platform;
                ALTER TABLE migration.assets
                DROP COLUMN virtualization_platform;
            END IF;
        END $$;
        """
    )
