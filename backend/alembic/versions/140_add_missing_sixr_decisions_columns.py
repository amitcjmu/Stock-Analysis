"""Add missing columns to sixr_decisions table.

Revision ID: 140_add_sixr_cols
Revises: 139_add_tech_debt_cols
Create Date: 2025-11-26

The SQLAlchemy SixRDecision model defines columns that were never
migrated to the database table. This migration adds them using idempotent
patterns per CLAUDE.md.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "140_add_sixr_cols"
down_revision = "139_add_tech_debt_cols"
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to sixr_decisions table."""
    # Use idempotent pattern per CLAUDE.md
    op.execute(
        """
        DO $$
        BEGIN
            -- Add assessment_flow_id column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'assessment_flow_id'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN assessment_flow_id UUID REFERENCES migration.assessment_flows(id);

                COMMENT ON COLUMN migration.sixr_decisions.assessment_flow_id
                IS 'Reference to the assessment flow that generated this decision';
            END IF;

            -- Add application_id column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'application_id'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN application_id UUID;

                COMMENT ON COLUMN migration.sixr_decisions.application_id
                IS 'Reference to the application this decision applies to';
            END IF;

            -- Add component_id column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'component_id'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN component_id UUID;

                COMMENT ON COLUMN migration.sixr_decisions.component_id
                IS 'Optional reference to a specific component';
            END IF;

            -- Add sixr_strategy column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'sixr_strategy'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN sixr_strategy VARCHAR(50);

                COMMENT ON COLUMN migration.sixr_decisions.sixr_strategy
                IS '6R strategy: rehost, refactor, rearchitect, rebuild, replace, retain';
            END IF;

            -- Add decision_rationale column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'decision_rationale'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN decision_rationale TEXT;
            END IF;

            -- Add alternative_strategies column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'alternative_strategies'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN alternative_strategies JSONB DEFAULT '[]'::jsonb;
            END IF;

            -- Add analysis_details column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'analysis_details'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN analysis_details JSONB DEFAULT '{}'::jsonb;
            END IF;

            -- Add confidence_score column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'confidence_score'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN confidence_score FLOAT;
            END IF;

            -- Add risk_assessment column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'risk_assessment'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN risk_assessment JSONB DEFAULT '{}'::jsonb;
            END IF;

            -- Add implementation columns if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'implementation_approach'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN implementation_approach TEXT,
                ADD COLUMN estimated_effort VARCHAR(100),
                ADD COLUMN estimated_duration VARCHAR(100),
                ADD COLUMN estimated_cost FLOAT;
            END IF;

            -- Add dependency columns if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'dependencies'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN dependencies JSONB DEFAULT '[]'::jsonb,
                ADD COLUMN constraints JSONB DEFAULT '[]'::jsonb,
                ADD COLUMN assumptions JSONB DEFAULT '[]'::jsonb;
            END IF;

            -- Add success criteria columns if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'success_criteria'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN success_criteria JSONB DEFAULT '[]'::jsonb,
                ADD COLUMN validation_plan JSONB DEFAULT '{}'::jsonb,
                ADD COLUMN rollback_plan TEXT;
            END IF;

            -- Add business alignment columns if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'business_value'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN business_value TEXT,
                ADD COLUMN business_priority INTEGER,
                ADD COLUMN stakeholder_alignment JSONB DEFAULT '{}'::jsonb;
            END IF;

            -- Add status columns if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'decision_status'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN decision_status VARCHAR(50) DEFAULT 'recommended',
                ADD COLUMN implementation_status VARCHAR(50) DEFAULT 'not_started',
                ADD COLUMN approval_status VARCHAR(50) DEFAULT 'pending';
            END IF;

            -- Add decision tracking columns if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'decision_date'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN decision_date TIMESTAMP WITH TIME ZONE DEFAULT now(),
                ADD COLUMN decided_by VARCHAR(255),
                ADD COLUMN approved_by VARCHAR(255),
                ADD COLUMN approved_at TIMESTAMP WITH TIME ZONE;
            END IF;

            -- Add decision_metadata column if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_decisions'
                AND column_name = 'decision_metadata'
            ) THEN
                ALTER TABLE migration.sixr_decisions
                ADD COLUMN decision_metadata JSONB DEFAULT '{}'::jsonb;
            END IF;
        END
        $$;
    """
    )

    # Create index on assessment_flow_id for performance
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sixr_decisions_assessment_flow_id
        ON migration.sixr_decisions(assessment_flow_id);
    """
    )

    # Create index on application_id for performance
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sixr_decisions_application_id
        ON migration.sixr_decisions(application_id);
    """
    )


def downgrade():
    """Remove added indexes (columns retained to preserve data)."""
    op.execute("DROP INDEX IF EXISTS migration.idx_sixr_decisions_assessment_flow_id;")
    op.execute("DROP INDEX IF EXISTS migration.idx_sixr_decisions_application_id;")
