"""Synchronize current_phase and phase_state.current_phase (Bug #648 fix)

Revision ID: 100
Revises: 099
Create Date: 2025-10-18

Bug #648 Fix: This migration resolves data divergence between the current_phase
column and phase_state.current_phase JSONB field in collection_flows table.

Root Cause:
- Code was updating only one field at a time, causing inconsistencies
- Frontend queries phase_state.current_phase, backend queries current_phase
- Led to UI showing wrong phase and breaking workflow progression

Migration Strategy:
1. Use phase_state.current_phase as source of truth if it exists (more recent)
2. Backfill phase_state.current_phase from column if JSONB field is missing
3. Future code changes enforce atomic updates via _set_current_phase() helper

Affected Files:
- backend/app/services/collection_flow/state_management/commands.py
- backend/app/services/integration/discovery_collection_bridge.py
- backend/app/services/unified_discovery/workflow_phase_manager.py
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "100"
down_revision = "099_standardize_sixr_strategies"
branch_labels = None
depends_on = None


def upgrade():
    """
    Synchronize current_phase column and phase_state.current_phase JSONB field.
    """
    # Step 1: Update current_phase column from phase_state where JSONB has value
    # This handles cases where phase_state.current_phase was updated but column wasn't
    op.execute(
        """
        UPDATE migration.collection_flows
        SET current_phase = phase_state->>'current_phase'
        WHERE phase_state IS NOT NULL
          AND phase_state->>'current_phase' IS NOT NULL
          AND current_phase IS DISTINCT FROM phase_state->>'current_phase'
    """
    )

    # Step 2: Backfill phase_state.current_phase from column where JSONB is missing
    # This handles cases where column was updated but phase_state wasn't
    op.execute(
        """
        UPDATE migration.collection_flows
        SET phase_state = jsonb_set(
            COALESCE(phase_state, '{}'::jsonb),
            '{current_phase}',
            to_jsonb(current_phase)
        )
        WHERE current_phase IS NOT NULL
          AND (
              phase_state IS NULL
              OR phase_state->>'current_phase' IS NULL
              OR phase_state->>'current_phase' != current_phase
          )
    """
    )


def downgrade():
    """
    No downgrade needed - data synchronization is safe and non-destructive.

    The migration only ensures consistency between two fields that should always
    have the same value. Reverting this would re-introduce the divergence bug.
    """
    pass
