"""Add wave_planning_optimization pattern type to patterntype enum

Revision ID: 141_add_wave_planning_optimization_pattern_type
Revises: 140_add_missing_sixr_decisions_columns
Create Date: 2025-11-26

This migration adds WAVE_PLANNING_OPTIMIZATION enum value to support wave planning
agent learnings storage via TenantMemoryManager (ADR-024).

Used by wave_planning_specialist agent to store optimization patterns:
- Dependency grouping strategies
- Wave sizing and duration insights
- Risk mitigation patterns
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "141_add_wave_planning_optimization_pattern_type"
down_revision = "140_add_sixr_cols"
branch_labels = None
depends_on = None


def upgrade():
    """Add WAVE_PLANNING_OPTIMIZATION to patterntype enum."""

    op.execute(
        """
        DO $$
        BEGIN
            -- WAVE_PLANNING_OPTIMIZATION: For wave_planning_specialist agent
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'WAVE_PLANNING_OPTIMIZATION'
                AND enumtypid = 'migration.patterntype'::regtype
            ) THEN
                ALTER TYPE migration.patterntype ADD VALUE 'WAVE_PLANNING_OPTIMIZATION';
            END IF;

        END $$;
    """
    )


def downgrade():
    """
    Cannot remove enum values in PostgreSQL without recreating the entire type.
    See migration 097 for explanation.
    """
    pass
