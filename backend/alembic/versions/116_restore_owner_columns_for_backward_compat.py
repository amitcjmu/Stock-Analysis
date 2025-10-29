"""Restore business_owner and technical_owner columns for backward compatibility

Adds back business_owner and technical_owner columns to assets table
for backward compatibility while keeping asset_contacts for normalized access.

Revision ID: 114_restore_owner_columns_for_backward_compat
Revises: 113_migrate_owners_to_asset_contacts
Create Date: 2025-10-28 16:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "116_restore_owner_columns_for_backward_compat"
down_revision = "115_migrate_owners_to_asset_contacts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Restore business_owner and technical_owner columns for backward compatibility.

    IDEMPOTENT: Uses IF NOT EXISTS checks.
    """
    op.execute(
        """
        DO $$
        BEGIN
            -- Restore business_owner column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'business_owner'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN business_owner VARCHAR(255);

                COMMENT ON COLUMN migration.assets.business_owner IS
                'Business owner name (legacy field, use asset_contacts for normalized data)';

                -- Backfill from asset_contacts
                UPDATE migration.assets a
                SET business_owner = ac.name
                FROM migration.asset_contacts ac
                WHERE ac.asset_id = a.id
                AND ac.contact_type = 'business_owner'
                AND ac.name IS NOT NULL;
            END IF;

            -- Restore technical_owner column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'technical_owner'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN technical_owner VARCHAR(255);

                COMMENT ON COLUMN migration.assets.technical_owner IS
                'Technical owner name (legacy field, use asset_contacts for normalized data)';

                -- Backfill from asset_contacts
                UPDATE migration.assets a
                SET technical_owner = ac.name
                FROM migration.asset_contacts ac
                WHERE ac.asset_id = a.id
                AND ac.contact_type = 'technical_owner'
                AND ac.name IS NOT NULL;
            END IF;

        END $$;
        """
    )


def downgrade() -> None:
    """
    Remove business_owner and technical_owner columns.

    WARNING: This drops columns and loses data!
    """
    op.execute(
        """
        DO $$
        BEGIN
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS business_owner;
            ALTER TABLE migration.assets DROP COLUMN IF EXISTS technical_owner;
        END $$;
        """
    )
