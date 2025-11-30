"""Fix critical constraint issues: Bug #1167 (conflict_type) and Bug #1168 (flow_id FK)

Bug #1167: Asset conflict resolution fails because 'environment' is used as conflict_type
           but the CHECK constraint only allows 'hostname', 'ip_address', 'name'.
           Fix: Add 'environment' to the allowed conflict types.

Bug #1168: 6R recommendation generation fails because agent_task_history.flow_id has a
           non-nullable FK to crewai_flow_state_extensions, but child flow IDs are being
           passed instead of master flow IDs.
           Fix: Make flow_id nullable to allow task history even when flow context is unclear.

Revision ID: 142_fix_critical_constraints_bugs_1167_1168
Revises: 141_add_wave_planning_optimization_pattern_type
Create Date: 2025-11-30
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "142_fix_critical_constraints_bugs_1167_1168"
down_revision = "141_add_wave_planning_optimization_pattern_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply fixes for Bug #1167 and Bug #1168."""

    # ==========================================================================
    # Bug #1167 Fix: Add 'environment' to asset conflict types
    # ==========================================================================
    # Drop old constraint and create new one with 'environment' included
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop existing constraint if it exists
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'ck_asset_conflicts_type'
                AND table_schema = 'migration'
            ) THEN
                ALTER TABLE migration.asset_conflict_resolutions
                DROP CONSTRAINT ck_asset_conflicts_type;
            END IF;

            -- Add new constraint with 'environment' included
            ALTER TABLE migration.asset_conflict_resolutions
            ADD CONSTRAINT ck_asset_conflicts_type
            CHECK (conflict_type IN ('hostname', 'ip_address', 'name', 'environment'));

            RAISE NOTICE 'Bug #1167 Fix: Updated ck_asset_conflicts_type to include environment';
        EXCEPTION
            WHEN undefined_table THEN
                RAISE NOTICE 'Table asset_conflict_resolutions does not exist, skipping constraint update';
        END $$;
        """
    )

    # ==========================================================================
    # Bug #1168 Fix: Make agent_task_history.flow_id nullable
    # ==========================================================================
    # This allows task history records to be created even when the flow context
    # is ambiguous (child flow ID vs master flow ID).
    op.execute(
        """
        DO $$
        BEGIN
            -- Make flow_id nullable
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'agent_task_history'
                AND column_name = 'flow_id'
                AND is_nullable = 'NO'
            ) THEN
                ALTER TABLE migration.agent_task_history
                ALTER COLUMN flow_id DROP NOT NULL;

                RAISE NOTICE 'Bug #1168 Fix: Made agent_task_history.flow_id nullable';
            ELSE
                RAISE NOTICE 'agent_task_history.flow_id is already nullable or does not exist';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Revert fixes for Bug #1167 and Bug #1168."""

    # Revert Bug #1167: Remove 'environment' from allowed conflict types
    # Per Qodo Bot: Delete records with conflict_type='environment' first to prevent
    # constraint violation during downgrade
    op.execute(
        """
        DO $$
        DECLARE
            deleted_count INTEGER;
        BEGIN
            -- Per Qodo Bot: Delete environment records before reverting constraint
            DELETE FROM migration.asset_conflict_resolutions
            WHERE conflict_type = 'environment';

            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            IF deleted_count > 0 THEN
                RAISE NOTICE 'Deleted % environment conflict records for downgrade', deleted_count;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'ck_asset_conflicts_type'
                AND table_schema = 'migration'
            ) THEN
                ALTER TABLE migration.asset_conflict_resolutions
                DROP CONSTRAINT ck_asset_conflicts_type;
            END IF;

            ALTER TABLE migration.asset_conflict_resolutions
            ADD CONSTRAINT ck_asset_conflicts_type
            CHECK (conflict_type IN ('hostname', 'ip_address', 'name'));
        EXCEPTION
            WHEN undefined_table THEN
                RAISE NOTICE 'Table asset_conflict_resolutions does not exist';
        END $$;
        """
    )

    # Revert Bug #1168: Make flow_id NOT NULL again
    # Note: This may fail if there are NULL values in the column
    op.execute(
        """
        DO $$
        BEGIN
            -- Only make NOT NULL if no NULL values exist
            IF NOT EXISTS (
                SELECT 1 FROM migration.agent_task_history
                WHERE flow_id IS NULL
            ) THEN
                ALTER TABLE migration.agent_task_history
                ALTER COLUMN flow_id SET NOT NULL;
            ELSE
                RAISE NOTICE 'Cannot revert: NULL values exist in flow_id column';
            END IF;
        EXCEPTION
            WHEN undefined_table THEN
                RAISE NOTICE 'Table agent_task_history does not exist';
        END $$;
        """
    )
