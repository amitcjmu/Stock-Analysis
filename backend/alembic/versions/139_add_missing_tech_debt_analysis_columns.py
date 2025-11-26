"""Add missing columns to tech_debt_analysis table.

Revision ID: 139_add_tech_debt_cols
Revises: 138_add_missing_cols
Create Date: 2025-11-26

The SQLAlchemy TechDebtAnalysis model defines columns that were never
migrated to the database table. This migration adds them using idempotent
patterns per CLAUDE.md.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "139_add_tech_debt_cols"
down_revision = "138_add_missing_cols"
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to tech_debt_analysis table."""
    # Use idempotent pattern per CLAUDE.md
    op.execute(
        """
        DO $$
        BEGIN
            -- Add assessment_flow_id column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'assessment_flow_id'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN assessment_flow_id UUID REFERENCES migration.assessment_flows(id);

                COMMENT ON COLUMN migration.tech_debt_analysis.assessment_flow_id
                IS 'Reference to the assessment flow that performed this analysis';
            END IF;

            -- Add application_id column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'application_id'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN application_id UUID;

                COMMENT ON COLUMN migration.tech_debt_analysis.application_id
                IS 'Reference to the application being analyzed';
            END IF;

            -- Add component_id column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'component_id'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN component_id UUID;

                COMMENT ON COLUMN migration.tech_debt_analysis.component_id
                IS 'Optional reference to a specific component';
            END IF;

            -- Add debt_type column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'debt_type'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN debt_type VARCHAR(100);
            END IF;

            -- Add debt_category column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'debt_category'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN debt_category VARCHAR(100);
            END IF;

            -- Add severity column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'severity'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN severity VARCHAR(50) DEFAULT 'medium';
            END IF;

            -- Add description column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'description'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN description TEXT;
            END IF;

            -- Add root_cause column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'root_cause'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN root_cause TEXT;
            END IF;

            -- Add impact_analysis column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'impact_analysis'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN impact_analysis JSONB DEFAULT '{}'::jsonb;
            END IF;

            -- Add score columns if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'debt_score'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN debt_score FLOAT,
                ADD COLUMN impact_score FLOAT,
                ADD COLUMN effort_score FLOAT,
                ADD COLUMN priority_score FLOAT;
            END IF;

            -- Add remediation columns if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'remediation_strategy'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN remediation_strategy TEXT,
                ADD COLUMN estimated_effort VARCHAR(100),
                ADD COLUMN recommended_timeline VARCHAR(100),
                ADD COLUMN prerequisites JSONB DEFAULT '[]'::jsonb;
            END IF;

            -- Add risk columns if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'risk_factors'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN risk_factors JSONB DEFAULT '[]'::jsonb,
                ADD COLUMN dependencies JSONB DEFAULT '[]'::jsonb,
                ADD COLUMN affected_components JSONB DEFAULT '[]'::jsonb;
            END IF;

            -- Add analysis metadata columns if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'analysis_method'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN analysis_method VARCHAR(100),
                ADD COLUMN confidence_level FLOAT,
                ADD COLUMN evidence JSONB DEFAULT '[]'::jsonb;
            END IF;

            -- Add status columns if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'status'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN status VARCHAR(50) DEFAULT 'identified',
                ADD COLUMN resolution_status VARCHAR(50);
            END IF;

            -- Add risk_metadata column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'risk_metadata'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN risk_metadata JSONB DEFAULT '{}'::jsonb;
            END IF;

            -- Add resolved_at column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'tech_debt_analysis'
                AND column_name = 'resolved_at'
            ) THEN
                ALTER TABLE migration.tech_debt_analysis
                ADD COLUMN resolved_at TIMESTAMP WITH TIME ZONE;
            END IF;
        END
        $$;
    """
    )

    # Create index on assessment_flow_id for performance
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tech_debt_analysis_assessment_flow_id
        ON migration.tech_debt_analysis(assessment_flow_id);
    """
    )

    # Create index on application_id for performance
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tech_debt_analysis_application_id
        ON migration.tech_debt_analysis(application_id);
    """
    )


def downgrade():
    """Remove added indexes (columns retained to preserve data)."""
    op.execute(
        "DROP INDEX IF EXISTS migration.idx_tech_debt_analysis_assessment_flow_id;"
    )
    op.execute("DROP INDEX IF EXISTS migration.idx_tech_debt_analysis_application_id;")
