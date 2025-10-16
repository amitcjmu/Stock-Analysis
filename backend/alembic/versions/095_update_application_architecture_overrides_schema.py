"""Update application_architecture_overrides schema to match October 2025 refactor

Revision ID: 095_update_application_architecture_overrides_schema
Revises: 094_add_architecture_standards_unique_constraint
Create Date: 2025-10-16

SCHEMA ALIGNMENT: Updates table from migration 001 schema to modern model schema.
The model was refactored in October 2025 with enterprise-grade fields:
- Expanded justification (business + technical)
- Full approval workflow (approved, approved_by, approved_at)
- Impact assessment tracking
- Risk level categorization
- Extensible metadata

Table is EMPTY (0 rows) - safe to drop/add columns.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "095_update_application_architecture_overrides_schema"
down_revision = "094_add_architecture_standards_unique_constraint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update application_architecture_overrides schema"""

    op.execute(
        """
        DO $$
        BEGIN
            -- Drop old columns (from migration 001)
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'standard_id'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                DROP COLUMN standard_id;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'override_type'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                DROP COLUMN override_type;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'override_details'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                DROP COLUMN override_details;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'rationale'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                DROP COLUMN rationale;
            END IF;

            -- Add new columns (from October 2025 model refactor)

            -- Core override definition
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'requirement_type'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN requirement_type VARCHAR(100) NOT NULL DEFAULT 'custom';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'original_value'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN original_value JSONB NOT NULL DEFAULT '{}'::jsonb;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'override_value'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN override_value JSONB NOT NULL DEFAULT '{}'::jsonb;
            END IF;

            -- Justification (expanded from single 'rationale' field)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'reason'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN reason TEXT;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'business_justification'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN business_justification TEXT;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'technical_justification'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN technical_justification TEXT;
            END IF;

            -- Approval tracking (expanded)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'approved'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN approved BOOLEAN NOT NULL DEFAULT FALSE;
            END IF;

            -- Update approved_by to allow longer names (was VARCHAR(100), now VARCHAR(255))
            ALTER TABLE migration.application_architecture_overrides
            ALTER COLUMN approved_by TYPE VARCHAR(255);

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'approved_at'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN approved_at TIMESTAMP WITH TIME ZONE;
            END IF;

            -- Impact and risk assessment
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'impact_assessment'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN impact_assessment JSONB NOT NULL DEFAULT '{}'::jsonb;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'risk_level'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN risk_level VARCHAR(50) NOT NULL DEFAULT 'medium';
            END IF;

            -- Metadata
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'override_metadata'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN override_metadata JSONB NOT NULL DEFAULT '{}'::jsonb;
            END IF;

        END $$;
    """
    )


def downgrade() -> None:
    """Revert to migration 001 schema (if needed for rollback)"""

    op.execute(
        """
        DO $$
        BEGIN
            -- Add back old columns
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'standard_id'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN standard_id UUID;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'override_type'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN override_type VARCHAR(100) NOT NULL DEFAULT 'custom';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'override_details'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN override_details JSONB;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'application_architecture_overrides'
                AND column_name = 'rationale'
            ) THEN
                ALTER TABLE migration.application_architecture_overrides
                ADD COLUMN rationale TEXT;
            END IF;

            -- Drop new columns
            ALTER TABLE migration.application_architecture_overrides
            DROP COLUMN IF EXISTS requirement_type,
            DROP COLUMN IF EXISTS original_value,
            DROP COLUMN IF EXISTS override_value,
            DROP COLUMN IF EXISTS reason,
            DROP COLUMN IF EXISTS business_justification,
            DROP COLUMN IF EXISTS technical_justification,
            DROP COLUMN IF EXISTS approved,
            DROP COLUMN IF EXISTS approved_at,
            DROP COLUMN IF EXISTS impact_assessment,
            DROP COLUMN IF EXISTS risk_level,
            DROP COLUMN IF EXISTS override_metadata;

            -- Revert approved_by to VARCHAR(100)
            ALTER TABLE migration.application_architecture_overrides
            ALTER COLUMN approved_by TYPE VARCHAR(100);

        END $$;
    """
    )
