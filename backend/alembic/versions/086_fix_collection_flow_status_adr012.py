"""Fix CollectionFlowStatus enum to lifecycle-only values per ADR-012

Revision ID: 086_fix_collection_flow_status_adr012
Revises: 085_fix_vector_column_type
Create Date: 2025-10-07

This migration consolidates the collection flow status migration per ADR-012:
Flow Status Management Separation. It performs three critical operations:

1. Migrates phase-based status values to 'running' (asset_selection, gap_analysis, manual_collection → running)
2. Adds 'paused' status for user input wait states
3. Removes deprecated phase values from enum, leaving only 6 lifecycle states

Root Cause: CollectionFlowStatus enum was incorrectly using phase values
(asset_selection, gap_analysis, manual_collection) instead of lifecycle states.
Additionally, the 'paused' status was missing for flows waiting on user input.

Fix:
- Map all phase-based status values to 'running' status
- Add 'paused' to enum for flows waiting on user input
- Final enum: initialized, running, paused, completed, failed, cancelled

Note: This migration is idempotent and can be safely re-run. The downgrade is
not implemented because we cannot reliably reconstruct which phase-based status
each flow originally had. Phase information is preserved in current_phase column.

Reference:
- ADR-012: Flow Status Management Separation
- COLLECTION_FLOW_STATUS_REMEDIATION_PLAN.md (Phases 8-9)
- Consolidates original migrations 086 and 087
"""

import logging
import sqlalchemy as sa

from alembic import op

logger = logging.getLogger("alembic.runtime.migration")

# revision identifiers, used by Alembic.
revision = "086_fix_collection_flow_status_adr012"
down_revision = "085_fix_vector_column_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update collection flows to lifecycle-only status values per ADR-012

    This migration is idempotent and handles all edge cases:
    - Migrates phase values to 'running' (if they exist)
    - Adds 'paused' status to enum
    - Removes phase values from enum
    - Works correctly whether run once or multiple times

    PostgreSQL requires a multi-step process to modify enum values:
    1. Convert column to VARCHAR temporarily
    2. Migrate phase-based values to 'running'
    3. Drop old enum and create new enum with lifecycle values only + 'paused'
    4. Convert column back to enum type
    5. Recreate index
    """

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Step 1: Convert status column from enum to VARCHAR temporarily
    logger.info("Step 1: Converting status column to VARCHAR...")
    op.execute(
        """
        ALTER TABLE migration.collection_flows
        ALTER COLUMN status TYPE VARCHAR(50)
        USING status::text
    """
    )

    # Step 2: Count and migrate phase-based values (safe to query now that it's VARCHAR)
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
        logger.info(
            f"Step 2: Found {phase_status_count} flows with phase-based status values"
        )
        logger.info(f"Migrating {phase_status_count} flows to 'running' status...")

        # Migrate phase-based status values to 'running'
        op.execute(
            """
            UPDATE migration.collection_flows
            SET status = 'running'
            WHERE status IN ('asset_selection', 'gap_analysis', 'manual_collection')
        """
        )

        # Verify migration succeeded
        result = op.get_bind().execute(
            sa.text(
                """
                SELECT COUNT(*) as count
                FROM migration.collection_flows
                WHERE status IN ('asset_selection', 'gap_analysis', 'manual_collection')
            """
            )
        )
        remaining = result.scalar()

        if remaining > 0:
            raise Exception(
                f"Migration failed: {remaining} flows still have phase-based status values"
            )

        logger.info(f"✅ Migrated {phase_status_count} flows to 'running' status")
    else:
        logger.info(
            "Step 2: No phase-based status values found (idempotent check passed)"
        )

    # Step 3: Drop old enum type and create new one with lifecycle states + 'paused' (NO phase values)
    logger.info(
        "Step 3: Recreating CollectionFlowStatus enum with lifecycle states only "
        "(initialized, running, paused, completed, failed, cancelled)..."
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

    # Step 4: Convert status column back to enum type
    logger.info("Step 4: Converting status column back to enum...")
    op.execute(
        """
        ALTER TABLE migration.collection_flows
        ALTER COLUMN status TYPE migration.collectionflowstatus
        USING status::migration.collectionflowstatus
    """
    )

    # Step 5: Recreate the index that was dropped with CASCADE
    logger.info("Step 5: Recreating status index...")
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
    logger.info("✅ CollectionFlowStatus enum updated successfully")
    logger.info(f"   New enum values: {', '.join(enum_values)}")

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
    logger.info(f"✅ Total flows with valid status: {total_flows}")

    # Final summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ Migration 086 completed successfully per ADR-012")
    logger.info("=" * 80)
    logger.info(
        f"   • Migrated {phase_status_count} flows from phase-based to 'running' status"
    )
    logger.info("   • Added 'paused' status for user input wait states")
    logger.info(
        "   • Removed deprecated phase values (asset_selection, gap_analysis, manual_collection)"
    )
    logger.info("   • Database enum now matches Python model (6 lifecycle states only)")
    logger.info(
        "   • Enum values: initialized, running, paused, completed, failed, cancelled"
    )
    logger.info("=" * 80)


def downgrade() -> None:
    """Cannot reliably downgrade - phase information lost

    Downgrade is not implemented because we cannot reliably reconstruct
    which phase-based status each flow originally had. The phase information
    is preserved in the current_phase column, but mapping lifecycle status
    back to phase-based status would be ambiguous and error-prone.

    If downgrade is needed, it would require manual intervention based on
    the current_phase column values.
    """
    logger.warning("=" * 80)
    logger.warning(
        "⚠️  Downgrade not implemented - phase-based status information was lost during upgrade"
    )
    logger.warning("=" * 80)
    logger.info("   Phase information is preserved in current_phase column if needed")
    logger.info("   Manual intervention required for downgrade:")
    logger.info("   1. Recreate enum with phase values")
    logger.info("   2. Map flows back to phase status using current_phase column")
    logger.info("   3. Convert column back to enum")
    logger.warning("=" * 80)
