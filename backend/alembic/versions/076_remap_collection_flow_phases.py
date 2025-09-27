"""Remap collection flow phases from platform_detection to asset_selection

Revision ID: 076_remap_collection_flow_phases
Revises: 075_add_assets_listing_indexes
Create Date: 2025-09-25 00:29:27.274663

"""

from alembic import op
from sqlalchemy import text


def table_exists(table_name: str, schema: str = "migration") -> bool:
    """Check if a table exists."""
    bind = op.get_bind()
    result = bind.execute(
        text(
            "SELECT EXISTS (SELECT FROM information_schema.tables "
            "WHERE table_schema = :schema AND table_name = :table_name)"
        ),
        {"schema": schema, "table_name": table_name},
    )
    return result.scalar()


# revision identifiers, used by Alembic.
revision = "076_remap_collection_flow_phases"
down_revision = "075_add_assets_listing_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Remap old collection flow phases to new asset_selection phase.

    This migration is idempotent - it can be run multiple times safely.

    Old phases being removed:
    - platform_detection
    - automated_collection

    New phase replacing them:
    - asset_selection
    """

    # Check if table exists, if not skip migration
    if not table_exists("collection_flows"):
        print("ℹ️ Table migration.collection_flows does not exist, skipping migration")
        return

    # Check if migration has already been applied
    bind = op.get_bind()
    already_applied = bind.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1 FROM migration.collection_flows
                WHERE metadata->>'phase_migration' = :revision_id
                LIMIT 1
            )
            """
        ),
        {"revision_id": revision},
    ).scalar()

    if already_applied:
        print("ℹ️ Migration 076_remap_collection_flow_phases already applied, skipping")
        return

    print("🔄 Applying phase remapping migration...")

    # Get count of rows that will be affected for logging
    rows_to_migrate = bind.execute(
        text(
            """
            SELECT COUNT(*) FROM migration.collection_flows
            WHERE current_phase IN ('platform_detection', 'automated_collection')
               OR next_phase IN ('platform_detection', 'automated_collection')
               OR status IN ('platform_detection', 'automated_collection')
               OR (phase_state IS NOT NULL AND
                   (phase_state ? 'platform_detection' OR phase_state ? 'automated_collection'))
            """
        )
    ).scalar()

    print(f"📊 Found {rows_to_migrate} rows to migrate")

    if rows_to_migrate == 0:
        print("✅ No rows need migration, marking as complete")
        return

    # Update current_phase field (idempotent - only affects rows that haven't been migrated)
    bind = op.get_bind()
    bind.execute(
        text(
            """
            UPDATE migration.collection_flows
            SET current_phase = 'asset_selection'
            WHERE current_phase IN ('platform_detection', 'automated_collection')
              AND (metadata->>'phase_migration' IS NULL OR metadata->>'phase_migration' != :revision_id)
            """
        ),
        {"revision_id": revision},
    )

    # Update next_phase field (idempotent)
    bind.execute(
        text(
            """
            UPDATE migration.collection_flows
            SET next_phase = 'asset_selection'
            WHERE next_phase IN ('platform_detection', 'automated_collection')
              AND (metadata->>'phase_migration' IS NULL OR metadata->>'phase_migration' != :revision_id)
            """
        ),
        {"revision_id": revision},
    )

    # Skip status field update - this is handled in migration 077 after enum is updated
    # The status column uses an enum that doesn't have 'asset_selection' yet

    # Update phase_state JSON field (idempotent - only process untouched rows)
    bind.execute(
        text(
            """
            UPDATE migration.collection_flows
            SET phase_state =
                CASE
                    WHEN phase_state ? 'platform_detection' OR phase_state ? 'automated_collection'
                    THEN jsonb_set(
                        phase_state - 'platform_detection' - 'automated_collection',
                        '{asset_selection}',
                        COALESCE(
                            phase_state->'platform_detection',
                            phase_state->'automated_collection',
                            '{}'::jsonb
                        )
                    )
                    ELSE phase_state
                END
            WHERE phase_state IS NOT NULL
              AND (phase_state ? 'platform_detection' OR phase_state ? 'automated_collection')
              AND (metadata->>'phase_migration' IS NULL OR metadata->>'phase_migration' != :revision_id)
            """
        ),
        {"revision_id": revision},
    )

    # Update metadata JSON field to track migration (only for affected rows)
    # Using simplified approach to avoid complex jsonb operations with parameters
    bind.execute(
        text(
            """
            UPDATE migration.collection_flows
            SET metadata =
                CASE
                    WHEN metadata IS NULL THEN
                        jsonb_build_object('phase_migration', :revision_id, 'migrated_at', now())
                    ELSE
                        metadata || jsonb_build_object('phase_migration', :revision_id, 'migrated_at', now())
                END
            WHERE (
                current_phase = 'asset_selection'
                OR next_phase = 'asset_selection'
                OR (phase_state IS NOT NULL AND phase_state ? 'asset_selection')
            )
            AND (metadata->>'phase_migration' IS NULL OR metadata->>'phase_migration' != :revision_id)
            """
        ),
        {"revision_id": revision},
    )

    print("✅ Phase remapping migration completed successfully")


def downgrade() -> None:
    """
    Revert phase remapping. This is a best-effort operation since we can't
    deterministically know which flows were in which old phase.

    This migration is idempotent - it can be run multiple times safely.

    Default behavior:
    - asset_selection -> platform_detection (for current_phase and status)
    - asset_selection -> automated_collection (for next_phase)
    """

    # Check if table exists, if not skip migration
    if not table_exists("collection_flows"):
        print("ℹ️ Table migration.collection_flows does not exist, skipping downgrade")
        return

    bind = op.get_bind()

    # Check if there are any rows that were migrated by this revision
    rows_to_revert = bind.execute(
        text(
            """
            SELECT COUNT(*) FROM migration.collection_flows
            WHERE metadata->>'phase_migration' = :revision_id
            """
        ),
        {"revision_id": revision},
    ).scalar()

    if rows_to_revert == 0:
        print(
            "ℹ️ No rows found that were migrated by 076_remap_collection_flow_phases, skipping downgrade"
        )
        return

    print(f"🔄 Reverting phase remapping migration for {rows_to_revert} rows...")

    # Revert flows in asset_selection to platform_detection as a safe default
    # (only revert rows that were migrated by this specific migration)
    current_phase_reverted = bind.execute(
        text(
            """
            UPDATE migration.collection_flows
            SET current_phase = 'platform_detection'
            WHERE current_phase = 'asset_selection'
              AND metadata->>'phase_migration' = :revision_id
            RETURNING id
            """
        ),
        {"revision_id": revision},
    ).rowcount

    next_phase_reverted = bind.execute(
        text(
            """
            UPDATE migration.collection_flows
            SET next_phase = 'automated_collection'
            WHERE next_phase = 'asset_selection'
              AND metadata->>'phase_migration' = :revision_id
            RETURNING id
            """
        ),
        {"revision_id": revision},
    ).rowcount

    # Skip status revert - this is handled in migration 077

    # Revert phase_state JSON (only for rows migrated by this migration)
    phase_state_reverted = bind.execute(
        text(
            """
            UPDATE migration.collection_flows
            SET phase_state =
                CASE
                    WHEN phase_state ? 'asset_selection'
                    THEN jsonb_set(
                        phase_state - 'asset_selection',
                        '{platform_detection}',
                        phase_state->'asset_selection'
                    )
                    ELSE phase_state
                END
            WHERE phase_state IS NOT NULL
              AND phase_state ? 'asset_selection'
              AND metadata->>'phase_migration' = :revision_id
            RETURNING id
            """
        ),
        {"revision_id": revision},
    ).rowcount

    # Remove migration tracking from metadata
    metadata_cleaned = bind.execute(
        text(
            """
            UPDATE migration.collection_flows
            SET metadata =
                CASE
                    WHEN metadata IS NOT NULL AND
                         jsonb_typeof(metadata) = 'object' AND
                         (metadata - 'phase_migration' - 'migrated_at')::text = '{}'
                    THEN NULL
                    ELSE metadata - 'phase_migration' - 'migrated_at'
                END
            WHERE metadata->>'phase_migration' = :revision_id
            RETURNING id
            """
        ),
        {"revision_id": revision},
    ).rowcount

    print("✅ Downgrade completed:")
    print(f"   - Current phase reverted: {current_phase_reverted} rows")
    print(f"   - Next phase reverted: {next_phase_reverted} rows")
    print("   - Status reverted: skipped (handled in migration 077)")
    print(f"   - Phase state reverted: {phase_state_reverted} rows")
    print(f"   - Metadata cleaned: {metadata_cleaned} rows")
