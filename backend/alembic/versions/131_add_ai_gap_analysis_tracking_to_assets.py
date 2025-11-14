"""Add AI gap analysis tracking columns to assets table

Revision ID: 131_ai_gap_tracking
Revises: 130_backfill_canonical_apps
Create Date: 2025-01-13

Adds:
- ai_gap_analysis_status: Track completion status (0=not started, 1=in progress, 2=completed)
- ai_gap_analysis_timestamp: Track when analysis completed (for stale detection)

Purpose:
- Prevent redundant AI analysis calls for assets that already have AI-enhanced gaps
- Enable cost savings by caching AI analysis results
- Support stale detection by comparing ai_gap_analysis_timestamp with asset.updated_at
- Per-asset tracking (not per-flow) to share results across multiple collection flows
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "131_ai_gap_tracking"
down_revision: Union[str, None] = "130_backfill_canonical_apps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add AI gap analysis tracking columns to assets table."""

    op.execute(
        """
        DO $$
        BEGIN
            -- Add ai_gap_analysis_status column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'ai_gap_analysis_status'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN ai_gap_analysis_status INTEGER NOT NULL DEFAULT 0;

                -- Add comment explaining status codes
                COMMENT ON COLUMN migration.assets.ai_gap_analysis_status IS
                'AI gap analysis status: 0 = not started, 1 = in progress, '
                '2 = completed. Per-asset, shared across all collection flows.';
            END IF;

            -- Add ai_gap_analysis_timestamp column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'ai_gap_analysis_timestamp'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN ai_gap_analysis_timestamp TIMESTAMP WITH TIME ZONE;

                -- Add comment explaining timestamp purpose
                COMMENT ON COLUMN migration.assets.ai_gap_analysis_timestamp IS
                'Timestamp when AI gap analysis completed (status = 2). '
                'Used to detect stale analysis when compared with asset.updated_at.';
            END IF;

            -- Create partial index for fast lookups (only active statuses)
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assets'
                AND indexname = 'idx_assets_ai_analysis_status'
            ) THEN
                CREATE INDEX idx_assets_ai_analysis_status
                ON migration.assets(ai_gap_analysis_status)
                WHERE ai_gap_analysis_status IN (1, 2);  -- Partial index for active statuses
            END IF;
        END $$;
    """
    )


def downgrade() -> None:
    """Remove AI gap analysis tracking columns from assets table."""

    op.execute(
        """
        DO $$
        BEGIN
            -- Drop index if exists
            IF EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assets'
                AND indexname = 'idx_assets_ai_analysis_status'
            ) THEN
                DROP INDEX migration.idx_assets_ai_analysis_status;
            END IF;

            -- Drop ai_gap_analysis_timestamp column if exists
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'ai_gap_analysis_timestamp'
            ) THEN
                ALTER TABLE migration.assets
                DROP COLUMN ai_gap_analysis_timestamp;
            END IF;

            -- Drop ai_gap_analysis_status column if exists
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'ai_gap_analysis_status'
            ) THEN
                ALTER TABLE migration.assets
                DROP COLUMN ai_gap_analysis_status;
            END IF;
        END $$;
    """
    )
