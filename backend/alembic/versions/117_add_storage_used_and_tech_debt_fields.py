"""Add storage_used_gb and tech_debt_flags fields

Revision ID: 117_add_storage_used_and_tech_debt_fields
Revises: 116_restore_owner_columns_for_backward_compat
Create Date: 2025-10-29

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "117_add_storage_used_and_tech_debt_fields"
down_revision = "116_restore_owner_columns_for_backward_compat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add storage_used_gb and tech_debt_flags to assets table."""

    # Add storage_used_gb column
    op.execute(
        """
        ALTER TABLE migration.assets
        ADD COLUMN IF NOT EXISTS storage_used_gb FLOAT8;
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN migration.assets.storage_used_gb IS
        'Used storage space in GB (calculated or imported from CMDB)';
    """
    )

    # Add tech_debt_flags column
    op.execute(
        """
        ALTER TABLE migration.assets
        ADD COLUMN IF NOT EXISTS tech_debt_flags TEXT;
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN migration.assets.tech_debt_flags IS
        'Technical debt indicators and flags from CMDB assessment';
    """
    )

    # Add indexes for potential filtering
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_assets_tech_debt_flags
        ON migration.assets(tech_debt_flags)
        WHERE tech_debt_flags IS NOT NULL;
    """
    )


def downgrade() -> None:
    """Remove storage_used_gb and tech_debt_flags columns."""

    op.execute("DROP INDEX IF EXISTS migration.idx_assets_tech_debt_flags;")
    op.execute("ALTER TABLE migration.assets DROP COLUMN IF EXISTS tech_debt_flags;")
    op.execute("ALTER TABLE migration.assets DROP COLUMN IF EXISTS storage_used_gb;")
