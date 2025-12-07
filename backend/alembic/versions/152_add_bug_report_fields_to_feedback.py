"""Add bug report fields to feedback table for enhanced triage (#739)

Revision ID: 152_add_bug_report_fields_to_feedback
Revises: 151_seed_eol_catalog_data_issue_1243
Create Date: 2025-12-07

Adds fields for detailed bug reports:
- severity (low/medium/high/critical)
- steps_to_reproduce
- expected_behavior
- actual_behavior
- screenshot_data (base64)
- browser_info (JSON)
- flow_context (JSON)
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "152_add_bug_report_fields_to_feedback"
down_revision = "151_seed_eol_catalog_data_issue_1243"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add bug report fields to feedback table."""
    op.execute(
        """
        DO $$
        BEGIN
            -- Add severity field
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'feedback'
                AND column_name = 'severity'
            ) THEN
                ALTER TABLE migration.feedback
                ADD COLUMN severity VARCHAR(20) DEFAULT 'medium';
            END IF;

            -- Add steps_to_reproduce field
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'feedback'
                AND column_name = 'steps_to_reproduce'
            ) THEN
                ALTER TABLE migration.feedback
                ADD COLUMN steps_to_reproduce TEXT;
            END IF;

            -- Add expected_behavior field
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'feedback'
                AND column_name = 'expected_behavior'
            ) THEN
                ALTER TABLE migration.feedback
                ADD COLUMN expected_behavior TEXT;
            END IF;

            -- Add actual_behavior field
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'feedback'
                AND column_name = 'actual_behavior'
            ) THEN
                ALTER TABLE migration.feedback
                ADD COLUMN actual_behavior TEXT;
            END IF;

            -- Add screenshot_data field (base64 encoded)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'feedback'
                AND column_name = 'screenshot_data'
            ) THEN
                ALTER TABLE migration.feedback
                ADD COLUMN screenshot_data TEXT;
            END IF;

            -- Add browser_info JSON field
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'feedback'
                AND column_name = 'browser_info'
            ) THEN
                ALTER TABLE migration.feedback
                ADD COLUMN browser_info JSONB;
            END IF;

            -- Add flow_context JSON field
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'feedback'
                AND column_name = 'flow_context'
            ) THEN
                ALTER TABLE migration.feedback
                ADD COLUMN flow_context JSONB;
            END IF;

            -- Add index for severity for filtering bug reports
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'feedback'
                AND indexname = 'ix_feedback_severity'
            ) THEN
                CREATE INDEX ix_feedback_severity ON migration.feedback(severity);
            END IF;
        END $$;
    """
    )


def downgrade() -> None:
    """Remove bug report fields from feedback table."""
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop index first
            DROP INDEX IF EXISTS migration.ix_feedback_severity;

            -- Drop columns
            ALTER TABLE migration.feedback
            DROP COLUMN IF EXISTS severity,
            DROP COLUMN IF EXISTS steps_to_reproduce,
            DROP COLUMN IF EXISTS expected_behavior,
            DROP COLUMN IF EXISTS actual_behavior,
            DROP COLUMN IF EXISTS screenshot_data,
            DROP COLUMN IF EXISTS browser_info,
            DROP COLUMN IF EXISTS flow_context;
        END $$;
    """
    )
