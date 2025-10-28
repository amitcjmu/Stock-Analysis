"""Add tier1_gaps_by_asset and retry_after_inline to sixr_analyses table

Revision ID: 109_add_sixr_blocked_status
Revises: 108_add_complexity_score
Create Date: 2025-10-27

PR #816: Two-Tier Inline Gap-Filling Design (October 2025)
Add columns to persist blocked status and gap data for inline gap-filling workflow.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "109_add_sixr_blocked_status"
down_revision = "108_add_complexity_score"
branch_labels = None
depends_on = None


def upgrade():
    """Add tier1_gaps_by_asset and retry_after_inline columns for PR #816."""
    # Use PostgreSQL DO block for idempotent migration
    op.execute(
        """
        DO $$
        BEGIN
            -- Add tier1_gaps_by_asset column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'sixr_analyses'
                  AND column_name = 'tier1_gaps_by_asset'
            ) THEN
                ALTER TABLE migration.sixr_analyses
                ADD COLUMN tier1_gaps_by_asset JSONB;

                COMMENT ON COLUMN migration.sixr_analyses.tier1_gaps_by_asset IS
                    'Tier 1 (blocking) gaps by asset UUID. '
                    'Format: {''asset-uuid'': [{''field_name'': ''criticality'', ...}]}. '
                    'Present when status=''requires_input''.';
            END IF;

            -- Add retry_after_inline column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'sixr_analyses'
                  AND column_name = 'retry_after_inline'
            ) THEN
                ALTER TABLE migration.sixr_analyses
                ADD COLUMN retry_after_inline BOOLEAN DEFAULT FALSE;

                COMMENT ON COLUMN migration.sixr_analyses.retry_after_inline IS
                    'If True, analysis is blocked and will resume after inline answers '
                    'submitted via POST /api/v1/sixr-analyses/{id}/inline-answers.';
            END IF;
        END $$;
    """
    )


def downgrade():
    """Remove tier1_gaps_by_asset and retry_after_inline columns."""
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop tier1_gaps_by_asset column if it exists
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'sixr_analyses'
                  AND column_name = 'tier1_gaps_by_asset'
            ) THEN
                ALTER TABLE migration.sixr_analyses
                DROP COLUMN tier1_gaps_by_asset;
            END IF;

            -- Drop retry_after_inline column if it exists
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'sixr_analyses'
                  AND column_name = 'retry_after_inline'
            ) THEN
                ALTER TABLE migration.sixr_analyses
                DROP COLUMN retry_after_inline;
            END IF;
        END $$;
    """
    )
