"""Fix CollectionFlowStatus enum values per ADR-012

Revision ID: 086_fix_collection_flow_status_adr012
Revises: 085_fix_vector_column_type
Create Date: 2025-10-07

This migration updates collection_flows.status from phase-based values to
lifecycle-based values per ADR-012: Flow Status Management Separation.

Root Cause: CollectionFlowStatus enum was incorrectly using phase values
(asset_selection, gap_analysis, manual_collection) instead of lifecycle states.

Fix: Map all phase-based status values to 'running' status:
- asset_selection → running
- gap_analysis → running
- manual_collection → running

Note: This migration is irreversible because we cannot reliably reconstruct
which phase-based status each flow had. The downgrade is not implemented.

Reference: COLLECTION_FLOW_STATUS_REMEDIATION_PLAN.md (Phase 8)
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "086_fix_collection_flow_status_adr012"
down_revision = "085_fix_vector_column_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update collection flows from phase-based to lifecycle-based status

    PostgreSQL requires a multi-step process to modify enum values:
    1. Convert column to VARCHAR temporarily
    2. Update the values
    3. Drop old enum and create new enum with updated values
    4. Convert column back to enum type
    """

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Count flows to be updated
    result = op.get_bind().execute(
        sa.text(
            """
            SELECT COUNT(*) as count
            FROM migration.collection_flows
            WHERE status IN ('asset_selection', 'gap_analysis', 'manual_collection')
        """
        )
    )
    count = result.scalar()

    print(f"Found {count} collection flows with phase-based status values")

    # Step 1: Convert status column from enum to VARCHAR temporarily
    print("Step 1: Converting status column to VARCHAR...")
    op.execute(
        """
        ALTER TABLE migration.collection_flows
        ALTER COLUMN status TYPE VARCHAR(50)
        USING status::text
    """
    )

    # Step 2: Update flows with phase values to 'running'
    print(f"Step 2: Updating {count} flows to 'running' status...")
    op.execute(
        """
        UPDATE migration.collection_flows
        SET status = CASE
            WHEN status = 'asset_selection' THEN 'running'
            WHEN status = 'gap_analysis' THEN 'running'
            WHEN status = 'manual_collection' THEN 'running'
            ELSE status
        END
        WHERE status IN ('asset_selection', 'gap_analysis', 'manual_collection')
    """
    )

    # Step 3: Verify no phase-based values remain
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

    # Step 4: Drop old enum type and create new one with 'running' value
    print("Step 3: Recreating CollectionFlowStatus enum with 'running' value...")
    op.execute("DROP TYPE IF EXISTS migration.collectionflowstatus CASCADE")
    op.execute(
        """
        CREATE TYPE migration.collectionflowstatus AS ENUM (
            'initialized',
            'running',
            'asset_selection',
            'gap_analysis',
            'manual_collection',
            'completed',
            'failed',
            'cancelled'
        )
    """
    )

    # Step 5: Convert status column back to enum type
    print("Step 4: Converting status column back to enum...")
    op.execute(
        """
        ALTER TABLE migration.collection_flows
        ALTER COLUMN status TYPE migration.collectionflowstatus
        USING status::migration.collectionflowstatus
    """
    )

    # Recreate the index that was dropped with CASCADE
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_collection_flows_status
        ON migration.collection_flows(status)
    """
    )

    print(
        f"✅ Successfully migrated {count} collection flows from phase-based to lifecycle-based status per ADR-012"
    )
    print(
        "✅ Old enum values (asset_selection, gap_analysis, manual_collection) retained for backward compatibility"
    )


def downgrade() -> None:
    """Cannot reliably downgrade - phase information lost

    Downgrade is not implemented because we cannot reliably reconstruct
    which phase-based status each flow originally had. The phase information
    is preserved in the current_phase column, but mapping lifecycle status
    back to phase-based status would be ambiguous and error-prone.

    If downgrade is needed, it would require manual intervention based on
    the current_phase column values.
    """
    print(
        "⚠️  Downgrade not implemented - phase-based status information was lost during upgrade"
    )
    print(
        "   Original status values can be inferred from current_phase column if needed"
    )
