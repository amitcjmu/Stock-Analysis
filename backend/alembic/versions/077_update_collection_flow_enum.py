"""Update collection flow enum to include asset_selection

Revision ID: 077_update_collection_flow_enum
Revises: 076_remap_collection_flow_phases
Create Date: 2025-09-25 01:40:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "077_update_collection_flow_enum"
down_revision = "076_remap_collection_flow_phases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Update the collectionflowstatus enum to include asset_selection
    and remove platform_detection and automated_collection
    """

    # PostgreSQL doesn't allow direct modification of enums, so we need to:
    # 1. Create a new enum type
    # 2. Update the column to use the new enum
    # 3. Drop the old enum

    # Create new enum type with updated values
    op.execute(
        """
        CREATE TYPE collectionflowstatus_new AS ENUM (
            'initialized',
            'asset_selection',
            'gap_analysis',
            'manual_collection',
            'completed',
            'failed',
            'cancelled'
        )
    """
    )

    # Update the column to use the new enum type
    # First, cast the column to text temporarily
    op.execute(
        """
        ALTER TABLE migration.collection_flows
        ALTER COLUMN status TYPE text
    """
    )

    # Drop the old enum type
    op.execute("DROP TYPE IF EXISTS collectionflowstatus CASCADE")

    # Rename the new enum to the original name
    op.execute("ALTER TYPE collectionflowstatus_new RENAME TO collectionflowstatus")

    # Update the column to use the renamed enum
    op.execute(
        """
        ALTER TABLE migration.collection_flows
        ALTER COLUMN status TYPE collectionflowstatus
        USING status::collectionflowstatus
    """
    )

    print("✅ Updated collectionflowstatus enum to include asset_selection")


def downgrade() -> None:
    """
    Revert the enum changes
    """

    # Create old enum type
    op.execute(
        """
        CREATE TYPE collectionflowstatus_old AS ENUM (
            'initialized',
            'platform_detection',
            'automated_collection',
            'gap_analysis',
            'manual_collection',
            'completed',
            'failed',
            'cancelled'
        )
    """
    )

    # Update the column to use text temporarily
    op.execute(
        """
        ALTER TABLE migration.collection_flows
        ALTER COLUMN status TYPE text
    """
    )

    # Map asset_selection back to platform_detection
    op.execute(
        """
        UPDATE migration.collection_flows
        SET status = 'platform_detection'
        WHERE status = 'asset_selection'
    """
    )

    # Drop the current enum
    op.execute("DROP TYPE IF EXISTS collectionflowstatus CASCADE")

    # Rename old enum back
    op.execute("ALTER TYPE collectionflowstatus_old RENAME TO collectionflowstatus")

    # Update column to use the old enum
    op.execute(
        """
        ALTER TABLE migration.collection_flows
        ALTER COLUMN status TYPE collectionflowstatus
        USING status::collectionflowstatus
    """
    )

    print("✅ Reverted collectionflowstatus enum to original values")
