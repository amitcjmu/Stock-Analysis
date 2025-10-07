"""Add paused status and remove deprecated phase values from CollectionFlowStatus enum

Revision ID: 087_add_paused_remove_phase_values
Revises: 086_fix_collection_flow_status_adr012
Create Date: 2025-10-07

This migration completes ADR-012 compliance by:
1. Adding missing 'paused' status for user input wait states
2. Removing deprecated phase values (asset_selection, gap_analysis, manual_collection)

Root Cause: QA agent discovered CollectionFlowStatus enum in database was missing
'paused' status and still contained deprecated phase values that should have been
removed in migration 086. This causes runtime errors when flows transition to
asset_selection phase and attempt to set status to 'paused'.

Fix: Align database enum with Python model (lines 20-28 of collection_flow/schemas.py):
- Add 'paused' status value
- Remove phase-based values (asset_selection, gap_analysis, manual_collection)
- Result: 6 lifecycle states only (initialized, running, paused, completed, failed, cancelled)

Note: Uses same multi-step approach as migration 086 to safely modify PostgreSQL enums.
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "087_add_paused_remove_phase_values"
down_revision = "086_fix_collection_flow_status_adr012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add 'paused' status and remove deprecated phase values from enum

    PostgreSQL requires a multi-step process to modify enum values:
    1. Convert column to VARCHAR temporarily
    2. Drop old enum and create new enum with correct values
    3. Convert column back to enum type
    4. Recreate index
    """

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Check for any flows currently using phase values as status
    result = op.get_bind().execute(
        sa.text(
            """
            SELECT COUNT(*) as count
            FROM migration.collection_flows
            WHERE status IN ('asset_selection', 'gap_analysis', 'manual_collection')
        """
        )
    )
    phase_status_count = result.scalar()

    if phase_status_count > 0:
        print(
            f"⚠️  WARNING: Found {phase_status_count} flows with phase-based status values"
        )
        print(
            "   These will be migrated to 'running' status (phase preserved in current_phase column)"
        )

        # Migrate phase-based status values to 'running'
        op.execute(
            """
            UPDATE migration.collection_flows
            SET status = 'running'
            WHERE status IN ('asset_selection', 'gap_analysis', 'manual_collection')
        """
        )
        print(f"   ✅ Migrated {phase_status_count} flows to 'running' status")

    # Step 1: Convert status column from enum to VARCHAR temporarily
    print("Step 1: Converting status column to VARCHAR...")
    op.execute(
        """
        ALTER TABLE migration.collection_flows
        ALTER COLUMN status TYPE VARCHAR(50)
        USING status::text
    """
    )

    # Step 2: Drop old enum type and create new one with 'paused' (without phase values)
    print(
        "Step 2: Recreating CollectionFlowStatus enum with 'paused' and removing phase values..."
    )
    op.execute("DROP TYPE IF EXISTS migration.collectionflowstatus CASCADE")
    op.execute(
        """
        CREATE TYPE migration.collectionflowstatus AS ENUM (
            'initialized',
            'running',
            'paused',
            'completed',
            'failed',
            'cancelled'
        )
    """
    )

    # Step 3: Convert status column back to enum type
    print("Step 3: Converting status column back to enum...")
    op.execute(
        """
        ALTER TABLE migration.collection_flows
        ALTER COLUMN status TYPE migration.collectionflowstatus
        USING status::migration.collectionflowstatus
    """
    )

    # Step 4: Recreate the index that was dropped with CASCADE
    print("Step 4: Recreating status index...")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_collection_flows_status
        ON migration.collection_flows(status)
    """
    )

    # Verification: Check enum values
    result = op.get_bind().execute(
        sa.text(
            """
            SELECT unnest(enum_range(NULL::migration.collectionflowstatus))
        """
        )
    )
    enum_values = [row[0] for row in result]
    print("\n✅ CollectionFlowStatus enum updated successfully!")
    print(f"   New values: {', '.join(enum_values)}")

    # Verify all flows have valid status
    result = op.get_bind().execute(
        sa.text(
            """
            SELECT COUNT(*) as count
            FROM migration.collection_flows
        """
        )
    )
    total_flows = result.scalar()
    print(f"   Total flows with valid status: {total_flows}")

    print("\n✅ Migration 087 completed successfully!")
    print("   - Added 'paused' status for user input wait states")
    print(
        "   - Removed deprecated phase values (asset_selection, gap_analysis, manual_collection)"
    )
    print("   - Database enum now matches Python model (6 lifecycle states)")


def downgrade() -> None:
    """Cannot reliably downgrade - phase information lost

    Downgrade is not implemented because:
    1. We removed phase-based status values that were deprecated per ADR-012
    2. Cannot reliably reconstruct which flows had phase-based status
    3. Phase information is still preserved in current_phase column

    If downgrade is needed, it would require manual intervention based on
    the current_phase column values.
    """
    print(
        "⚠️  Downgrade not implemented - phase-based status values were removed per ADR-012"
    )
    print("   Status information is preserved in current_phase column")
    print("   Manual intervention required if downgrade is necessary")
