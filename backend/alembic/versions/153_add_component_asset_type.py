"""Add component asset type to CHECK constraint

Revision ID: 153_add_component_asset_type
Revises: 152_add_bug_report_fields_to_feedback
Create Date: 2025-12-08 15:10:44.759618

Adds 'component' and 'Component' to the asset_type CHECK constraint
to support component asset types in the system.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "153_add_component_asset_type"
down_revision = "152_add_bug_report_fields_to_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add component to asset_type CHECK constraint."""
    # Drop existing constraint
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'chk_assets_asset_type'
            ) THEN
                ALTER TABLE migration.assets
                DROP CONSTRAINT chk_assets_asset_type;
            END IF;
        END $$;
        """
    )

    # Recreate constraint with component added
    op.execute(
        """
        ALTER TABLE migration.assets
        ADD CONSTRAINT chk_assets_asset_type
        CHECK (asset_type IN (
            'server', 'database', 'application', 'component',
            'network', 'storage', 'security_group', 'load_balancer',
            'virtual_machine', 'container', 'other',
            'Server', 'Database', 'Application', 'Component',
            'Network', 'Storage', 'Security_Group', 'Load_Balancer',
            'Virtual_Machine', 'Container', 'Other'
        ) OR asset_type IS NULL);
        """
    )


def downgrade() -> None:
    """Remove component from asset_type CHECK constraint."""
    # Drop existing constraint
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'chk_assets_asset_type'
            ) THEN
                ALTER TABLE migration.assets
                DROP CONSTRAINT chk_assets_asset_type;
            END IF;
        END $$;
        """
    )

    # Recreate constraint without component
    op.execute(
        """
        ALTER TABLE migration.assets
        ADD CONSTRAINT chk_assets_asset_type
        CHECK (asset_type IN (
            'server', 'database', 'application',
            'network', 'storage', 'security_group', 'load_balancer',
            'virtual_machine', 'container', 'other',
            'Server', 'Database', 'Application',
            'Network', 'Storage', 'Security_Group', 'Load_Balancer',
            'Virtual_Machine', 'Container', 'Other'
        ) OR asset_type IS NULL);
        """
    )
