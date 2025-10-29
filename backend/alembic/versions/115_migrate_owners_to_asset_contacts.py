"""Migrate business_owner and technical_owner to asset_contacts table

Migrates existing business_owner and technical_owner text fields to
normalized asset_contacts table (keeps original columns for backward compatibility).

Revision ID: 113_migrate_owners_to_asset_contacts
Revises: 112_enhance_asset_dependencies_network_discovery
Create Date: 2025-10-28 15:30:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "115_migrate_owners_to_asset_contacts"
down_revision = "114_enhance_asset_dependencies_network_discovery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Migrate business_owner and technical_owner data to asset_contacts table,
    then drop the old columns.

    IDEMPOTENT: Checks for column existence before operations.
    """
    op.execute(
        """
        DO $$
        BEGIN
            -- Step 1: Migrate existing business_owner data to asset_contacts
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'business_owner'
            ) THEN
                -- Insert business owners as contacts (skip if null or empty)
                INSERT INTO migration.asset_contacts (
                    client_account_id,
                    engagement_id,
                    asset_id,
                    contact_type,
                    name,
                    email,
                    created_at,
                    updated_at
                )
                SELECT
                    client_account_id,
                    engagement_id,
                    id as asset_id,
                    'business_owner' as contact_type,
                    business_owner as name,
                    'migrated-contact@placeholder.local' as email,
                    NOW() as created_at,
                    NOW() as updated_at
                FROM migration.assets
                WHERE business_owner IS NOT NULL
                AND TRIM(business_owner) != ''
                AND NOT EXISTS (
                    SELECT 1 FROM migration.asset_contacts ac
                    WHERE ac.asset_id = assets.id
                    AND ac.contact_type = 'business_owner'
                );

                -- Keep the column for backward compatibility
                RAISE NOTICE 'Migrated business_owner data to asset_contacts (keeping original column)';
            END IF;

            -- Step 2: Migrate existing technical_owner data to asset_contacts
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'technical_owner'
            ) THEN
                -- Insert technical owners as contacts (skip if null or empty)
                INSERT INTO migration.asset_contacts (
                    client_account_id,
                    engagement_id,
                    asset_id,
                    contact_type,
                    name,
                    email,
                    created_at,
                    updated_at
                )
                SELECT
                    client_account_id,
                    engagement_id,
                    id as asset_id,
                    'technical_owner' as contact_type,
                    technical_owner as name,
                    'migrated-contact@placeholder.local' as email,
                    NOW() as created_at,
                    NOW() as updated_at
                FROM migration.assets
                WHERE technical_owner IS NOT NULL
                AND TRIM(technical_owner) != ''
                AND NOT EXISTS (
                    SELECT 1 FROM migration.asset_contacts ac
                    WHERE ac.asset_id = assets.id
                    AND ac.contact_type = 'technical_owner'
                );

                -- Keep the column for backward compatibility
                RAISE NOTICE 'Migrated technical_owner data to asset_contacts (keeping original column)';
            END IF;

        END $$;
        """
    )


def downgrade() -> None:
    """
    Restore business_owner and technical_owner columns.

    WARNING: This will restore columns but may lose contact data not migrated back!
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

                -- Migrate back from asset_contacts
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

                -- Migrate back from asset_contacts
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
