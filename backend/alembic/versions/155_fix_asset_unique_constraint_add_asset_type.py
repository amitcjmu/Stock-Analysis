"""Remove overly restrictive name-based unique constraint from assets

Revision ID: 155
Revises: 154_add_password_reset_columns
Create Date: 2025-12-09

This migration removes the name-based unique constraint because:

1. A Server and Application can have the same name (e.g., "Itron Performance Manager")
2. The same application can exist in multiple environments (Prod, Staging, Dev)
   with the same name but different hostnames

The application's hierarchical deduplication logic already handles matching
intelligently using multiple criteria:
- Priority 1: name + asset_type
- Priority 2: hostname OR fqdn OR ip_address
- Priority 3: Normalized name fuzzy match
- Priority 4: External/import IDs

We retain the hostname and IP-based unique constraints since those ARE
legitimate unique identifiers per tenant context.

Previous constraint: (client_account_id, engagement_id, name) - too restrictive
New state: No name-based unique constraint, rely on deduplication logic

NOTE: The original 001_comprehensive_initial_schema.py has also been fixed
for new environments. This migration fixes existing production databases.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "155_fix_asset_unique_constraint_add_asset_type"
down_revision = "154_add_password_reset_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove overly restrictive name-based unique constraints.

    This migration is idempotent - safe to run on both:
    - Existing production databases (has ix_assets_unique_name_per_context)
    - New environments (001_ already creates ix_assets_name_per_context)
    """
    # Drop any unique name constraints that may exist
    # These use IF EXISTS so they're safe if already dropped or never existed
    op.execute(
        """
        DROP INDEX IF EXISTS migration.ix_assets_unique_name_per_context;
    """
    )
    op.execute(
        """
        DROP INDEX IF EXISTS migration.ix_assets_unique_name_type_per_context;
    """
    )

    # Create non-unique index for query performance
    # Uses IF NOT EXISTS so it's safe if 001_ already created it
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_assets_name_per_context
        ON migration.assets (client_account_id, engagement_id, name)
        WHERE name IS NOT NULL AND name <> '';
    """
    )


def downgrade() -> None:
    """Restore name-only unique constraint (NOT RECOMMENDED)."""
    # Drop the non-unique performance index
    op.execute(
        """
        DROP INDEX IF EXISTS migration.ix_assets_name_per_context;
    """
    )

    # Recreate the old name-only unique index
    # WARNING: This may fail if duplicate names exist
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_assets_unique_name_per_context
        ON migration.assets (client_account_id, engagement_id, name)
        WHERE name IS NOT NULL AND name <> '';
    """
    )
