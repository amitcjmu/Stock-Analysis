"""fix_asset_conflict_action_constraint

Revision ID: 090_fix_asset_conflict_action_constraint
Revises: 089_add_asset_conflict_resolution
Create Date: 2025-10-13 01:03:10.925635

CC: Fix CHECK constraint to use 'replace_with_new' instead of 'replace'
to match frontend API contract (ResolutionAction type)
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "090_fix_asset_conflict_action_constraint"
down_revision = "089_add_asset_conflict_resolution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix resolution_action CHECK constraint to allow 'replace_with_new'"""

    # Drop old constraint if it exists (idempotent)
    op.execute(
        """
        ALTER TABLE migration.asset_conflict_resolutions
        DROP CONSTRAINT IF EXISTS ck_asset_conflicts_action
        """
    )

    # Create new constraint with correct value
    op.create_check_constraint(
        "ck_asset_conflicts_action",
        "asset_conflict_resolutions",
        "resolution_action IN ('keep_existing', 'replace_with_new', 'merge') OR resolution_action IS NULL",
        schema="migration",
    )


def downgrade() -> None:
    """Revert to original constraint with 'replace'"""

    # Drop new constraint if it exists (idempotent)
    op.execute(
        """
        ALTER TABLE migration.asset_conflict_resolutions
        DROP CONSTRAINT IF EXISTS ck_asset_conflicts_action
        """
    )

    # Restore old constraint
    op.create_check_constraint(
        "ck_asset_conflicts_action",
        "asset_conflict_resolutions",
        "resolution_action IN ('keep_existing', 'replace', 'merge') OR resolution_action IS NULL",
        schema="migration",
    )
