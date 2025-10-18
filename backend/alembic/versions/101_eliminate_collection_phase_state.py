"""Eliminate collection flow phase_state duplication (ADR-028)

Revision ID: 101
Revises: 100
Create Date: 2025-10-18

ADR-028 Decision: Use Master Flow's phase_transitions as single source of truth.

This migration eliminates architectural debt by removing the duplicated phase_state
column from collection_flows table. Phase tracking is consolidated to Master Flow's
phase_transitions array in crewai_flow_state_extensions table.

Root Cause of Duplication:
- Collection flow was built before ADR-006 established Master Flow pattern
- phase_state JSONB was added for rich tracking, but Master Flow already provides this
- Discovery and Assessment flows don't have this duplication - only Collection does
- Bug #648: Caused data divergence between current_phase and phase_state.current_phase

Migration Strategy:
1. Copy existing phase_state.phase_history to master flow's phase_transitions
2. Synchronize current_phase column from phase_state for final consistency
3. Drop phase_state column entirely
4. All operations are idempotent and safe to re-run

Architecture After Migration:
- Master Flow: Single source of truth (phase_transitions, error_history)
- Child Flow: Denormalized current_phase column for query performance only
- Aligned with Discovery/Assessment flow patterns

References:
- ADR-028: Eliminate Collection Flow Phase State Duplication
- ADR-006: Master Flow Orchestrator as single source of truth
- Bug #648: Phase state inconsistency in collection_flows
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "101"
down_revision = "100"
branch_labels = None
depends_on = None


def upgrade():
    """
    Eliminate phase_state column and consolidate to master flow.

    All operations are idempotent and safe to run multiple times.
    """
    # Step 1: Migrate phase_state.phase_history to master flow's phase_transitions
    # Only updates master flows that don't already have phase_transitions
    # Idempotent: Won't duplicate if master flow already has transitions
    op.execute(
        """
        UPDATE migration.crewai_flow_state_extensions mf
        SET phase_transitions = COALESCE(
            mf.phase_transitions,
            (
                SELECT cf.phase_state->'phase_history'
                FROM migration.collection_flows cf
                WHERE cf.master_flow_id = mf.flow_id
                  AND cf.phase_state IS NOT NULL
                  AND cf.phase_state ? 'phase_history'
                LIMIT 1
            ),
            '[]'::jsonb
        )
        WHERE mf.flow_type = 'collection'
          AND (
              mf.phase_transitions IS NULL
              OR mf.phase_transitions = '[]'::jsonb
          )
          AND EXISTS (
              SELECT 1 FROM migration.collection_flows cf
              WHERE cf.master_flow_id = mf.flow_id
                AND cf.phase_state IS NOT NULL
                AND cf.phase_state ? 'phase_history'
          );
    """
    )

    # Step 2: Final synchronization of current_phase from phase_state
    # Ensures current_phase matches phase_state.current_phase before dropping column
    # Idempotent: Only updates rows where values differ
    op.execute(
        """
        UPDATE migration.collection_flows
        SET current_phase = phase_state->>'current_phase'
        WHERE phase_state IS NOT NULL
          AND phase_state ? 'current_phase'
          AND current_phase IS DISTINCT FROM phase_state->>'current_phase';
    """
    )

    # Step 3: Drop phase_state column
    # Idempotent: Uses IF EXISTS, safe to run even if column already dropped
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'collection_flows'
                  AND column_name = 'phase_state'
            ) THEN
                ALTER TABLE migration.collection_flows
                DROP COLUMN phase_state;

                RAISE NOTICE 'Dropped phase_state column from collection_flows';
            ELSE
                RAISE NOTICE 'Column phase_state already dropped, skipping';
            END IF;
        END
        $$;
    """
    )


def downgrade():
    """
    Recreate phase_state column if needed (not recommended).

    Idempotent: Only adds column if it doesn't exist.
    """
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'collection_flows'
                  AND column_name = 'phase_state'
            ) THEN
                ALTER TABLE migration.collection_flows
                ADD COLUMN phase_state JSONB NOT NULL DEFAULT '{}'::jsonb;

                RAISE NOTICE 'Recreated phase_state column';
            ELSE
                RAISE NOTICE 'Column phase_state already exists, skipping';
            END IF;
        END
        $$;
    """
    )

    # Backfill phase_state from master flow (best effort)
    op.execute(
        """
        UPDATE migration.collection_flows cf
        SET phase_state = jsonb_build_object(
            'current_phase', cf.current_phase,
            'phase_history', COALESCE(mf.phase_transitions, '[]'::jsonb),
            'phase_metadata', '{}'::jsonb
        )
        FROM migration.crewai_flow_state_extensions mf
        WHERE cf.master_flow_id = mf.flow_id
          AND cf.phase_state = '{}'::jsonb;
    """
    )
