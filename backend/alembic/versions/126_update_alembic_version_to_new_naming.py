"""Update alembic_version to new naming convention

Revision ID: 126_update_alembic_version_to_new_naming
Revises: e8443d30bda9, 125_merge_heads
Create Date: 2025-11-04

Description:
    This is a merge migration that can run from EITHER:
    - e8443d30bda9 (old hash - Railway databases)
    - 125_merge_heads (new naming - local databases)

    It updates the alembic_version table to use the standardized naming.

    Railway: e8443d30bda9 → This migration updates DB to 125_merge_heads → Then to 126
    Local: 125_merge_heads → Already correct → Proceeds to 126

    This is a ONE-TIME transition migration.
"""

# No imports needed for bridge migration

# revision identifiers, used by Alembic.
revision = "126_update_alembic_version_to_new_naming"
down_revision = ("e8443d30bda9", "125_merge_heads")  # Merge: accepts both paths
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Bridge migration for Railway transition from hash to numbered naming.

    This migration creates a path from BOTH:
    - e8443d30bda9 (old hash naming - Railway production)
    - 125_merge_heads (new numbered naming - local dev)

    Alembic automatically manages the alembic_version table, so this
    migration is intentionally empty (no-op). Its only purpose is to
    exist as a merge point in the migration graph.

    After this migration runs, Alembic will update alembic_version to:
    126_update_alembic_version_to_new_naming
    """
    # Intentionally empty - this is a bridge migration
    pass


def downgrade() -> None:
    """
    No-op downgrade (bridge migration).

    Alembic manages the alembic_version table automatically.
    """
    pass
