"""Add missing columns to application_components table.

Revision ID: 138_add_missing_cols
Revises: 137_add_data_cleansing_recommendations_table
Create Date: 2025-11-26

The SQLAlchemy ApplicationComponent model defines several columns that
were never migrated to the database table. This migration adds them.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "138_add_missing_cols"
down_revision = "137_add_data_cleansing_recommendations_table"
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to application_components table."""
    # Use idempotent pattern per CLAUDE.md
    op.execute(
        """
        DO $$
        BEGIN
            -- Add assessment_flow_id column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'assessment_flow_id'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN assessment_flow_id UUID;

                -- Add foreign key constraint
                ALTER TABLE migration.application_components
                ADD CONSTRAINT fk_app_components_assessment_flow
                FOREIGN KEY (assessment_flow_id)
                REFERENCES migration.assessment_flows(id)
                ON DELETE CASCADE;

                COMMENT ON COLUMN migration.application_components.assessment_flow_id
                IS 'Reference to the assessment flow that identified this component';
            END IF;

            -- Add application_id column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'application_id'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN application_id UUID;

                COMMENT ON COLUMN migration.application_components.application_id
                IS 'Reference to the canonical application this component belongs to';
            END IF;

            -- Add client_account_id column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'client_account_id'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN client_account_id UUID;

                COMMENT ON COLUMN migration.application_components.client_account_id
                IS 'Multi-tenant scoping - client account identifier';
            END IF;

            -- Add description column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'description'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN description TEXT;
            END IF;

            -- Add current_technology column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'current_technology'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN current_technology VARCHAR(255);
            END IF;

            -- Add version column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'version'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN version VARCHAR(100);
            END IF;

            -- Add configuration column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'configuration'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN configuration JSONB DEFAULT '{}'::jsonb;
            END IF;

            -- Add dependencies column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'dependencies'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN dependencies JSONB DEFAULT '[]'::jsonb;
            END IF;

            -- Add complexity_score column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'complexity_score'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN complexity_score FLOAT;
            END IF;

            -- Add business_criticality column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'business_criticality'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN business_criticality VARCHAR(50) DEFAULT 'medium';
            END IF;

            -- Add technical_debt_score column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'technical_debt_score'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN technical_debt_score FLOAT;
            END IF;

            -- Add migration_readiness column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'migration_readiness'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN migration_readiness VARCHAR(50);
            END IF;

            -- Add recommended_approach column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'recommended_approach'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN recommended_approach TEXT;
            END IF;

            -- Add estimated_effort column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'estimated_effort'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN estimated_effort VARCHAR(100);
            END IF;

            -- Add assessment_status column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'assessment_status'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN assessment_status VARCHAR(50) DEFAULT 'pending';
            END IF;

            -- Add assessment_progress column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'assessment_progress'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN assessment_progress FLOAT DEFAULT 0.0;
            END IF;

            -- Add discovered_by column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'discovered_by'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN discovered_by VARCHAR(100);

                COMMENT ON COLUMN migration.application_components.discovered_by
                IS 'How the component was discovered (automated, manual, etc.)';
            END IF;

            -- Add discovery_metadata column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'discovery_metadata'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN discovery_metadata JSONB DEFAULT '{}'::jsonb;
            END IF;

            -- Add component_metadata column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_components'
                AND column_name = 'component_metadata'
            ) THEN
                ALTER TABLE migration.application_components
                ADD COLUMN component_metadata JSONB DEFAULT '{}'::jsonb;
            END IF;
        END
        $$;
    """
    )

    # Create index on assessment_flow_id for performance
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_app_components_assessment_flow_id
        ON migration.application_components(assessment_flow_id);
    """
    )

    # Create index on application_id for performance
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_app_components_application_id
        ON migration.application_components(application_id);
    """
    )

    # Create index on client_account_id for multi-tenant queries
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_app_components_client_account_id
        ON migration.application_components(client_account_id);
    """
    )


def downgrade():
    """Remove added columns (only if they were added by this migration)."""
    # Drop indexes first
    op.execute("DROP INDEX IF EXISTS migration.idx_app_components_assessment_flow_id;")
    op.execute("DROP INDEX IF EXISTS migration.idx_app_components_application_id;")
    op.execute("DROP INDEX IF EXISTS migration.idx_app_components_client_account_id;")

    # Note: We don't drop columns in downgrade as they may contain data
    # and this follows the principle of not losing data on rollback.
    # Manual intervention would be required to remove columns if needed.
    pass
