"""Add component asset type to CHECK constraint

Revision ID: 153_add_component_asset_type
Revises: 152_add_bug_report_fields_to_feedback
Create Date: 2025-12-08 15:10:44.759618

Adds 'component' and 'Component' to the asset_type CHECK constraint
to support component asset types in the system.

NOTE: This migration dynamically includes any existing asset_type values
from the database to avoid CHECK violation errors.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "153_add_component_asset_type"
down_revision = "152_add_bug_report_fields_to_feedback"
branch_labels = None
depends_on = None

# Predefined asset types (including new 'component' type)
PREDEFINED_ASSET_TYPES = [
    "server",
    "database",
    "application",
    "component",
    "network",
    "storage",
    "security_group",
    "load_balancer",
    "virtual_machine",
    "container",
    "other",
    "Server",
    "Database",
    "Application",
    "Component",
    "Network",
    "Storage",
    "Security_Group",
    "Load_Balancer",
    "Virtual_Machine",
    "Container",
    "Other",
]


def upgrade() -> None:
    """Add component to asset_type CHECK constraint."""
    # Build the predefined values SQL string
    predefined_str = ", ".join(f"'{v}'" for v in PREDEFINED_ASSET_TYPES)

    op.execute(
        f"""
        DO $$
        DECLARE
            existing_vals TEXT[];
            all_vals TEXT[];
            val TEXT;
            vals_sql TEXT;
        BEGIN
            -- Skip if assets table doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
            ) THEN
                RAISE NOTICE 'Table migration.assets does not exist, skipping';
                RETURN;
            END IF;

            -- Drop existing constraint if it exists
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'chk_assets_asset_type'
            ) THEN
                ALTER TABLE migration.assets
                DROP CONSTRAINT chk_assets_asset_type;
            END IF;

            -- Get existing values from database not in predefined list
            SELECT ARRAY_AGG(DISTINCT asset_type)
            INTO existing_vals
            FROM migration.assets
            WHERE asset_type IS NOT NULL
            AND asset_type NOT IN ({predefined_str});

            -- Start with predefined values
            all_vals := ARRAY[{predefined_str}];

            -- Add any existing values not in predefined list
            IF existing_vals IS NOT NULL THEN
                FOREACH val IN ARRAY existing_vals LOOP
                    IF val IS NOT NULL AND NOT (val = ANY(all_vals)) THEN
                        all_vals := array_append(all_vals, val);
                        RAISE NOTICE 'Including existing asset_type: %', val;
                    END IF;
                END LOOP;
            END IF;

            -- Build the VALUES clause
            SELECT string_agg('''' || replace(v, '''', '''''') || '''', ', ')
            INTO vals_sql
            FROM unnest(all_vals) AS v;

            -- Add the CHECK constraint with all values
            EXECUTE format(
                'ALTER TABLE migration.assets ADD CONSTRAINT %I CHECK (%I IN (%s) OR %I IS NULL)',
                'chk_assets_asset_type', 'asset_type', vals_sql, 'asset_type'
            );
            RAISE NOTICE 'Added constraint chk_assets_asset_type with component';
        END $$;
        """
    )


def downgrade() -> None:
    """Remove component from asset_type CHECK constraint."""
    # Predefined asset types WITHOUT component
    predefined_no_component = [
        v for v in PREDEFINED_ASSET_TYPES if v.lower() != "component"
    ]
    predefined_str = ", ".join(f"'{v}'" for v in predefined_no_component)

    op.execute(
        f"""
        DO $$
        DECLARE
            existing_vals TEXT[];
            all_vals TEXT[];
            val TEXT;
            vals_sql TEXT;
        BEGIN
            -- Skip if assets table doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
            ) THEN
                RAISE NOTICE 'Table migration.assets does not exist, skipping';
                RETURN;
            END IF;

            -- Drop existing constraint if it exists
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'chk_assets_asset_type'
            ) THEN
                ALTER TABLE migration.assets
                DROP CONSTRAINT chk_assets_asset_type;
            END IF;

            -- Get existing values from database not in predefined list
            SELECT ARRAY_AGG(DISTINCT asset_type)
            INTO existing_vals
            FROM migration.assets
            WHERE asset_type IS NOT NULL
            AND asset_type NOT IN ({predefined_str});

            -- Start with predefined values
            all_vals := ARRAY[{predefined_str}];

            -- Add any existing values not in predefined list
            IF existing_vals IS NOT NULL THEN
                FOREACH val IN ARRAY existing_vals LOOP
                    IF val IS NOT NULL AND NOT (val = ANY(all_vals)) THEN
                        all_vals := array_append(all_vals, val);
                        RAISE NOTICE 'Including existing asset_type: %', val;
                    END IF;
                END LOOP;
            END IF;

            -- Build the VALUES clause
            SELECT string_agg('''' || replace(v, '''', '''''') || '''', ', ')
            INTO vals_sql
            FROM unnest(all_vals) AS v;

            -- Add the CHECK constraint with all values
            EXECUTE format(
                'ALTER TABLE migration.assets ADD CONSTRAINT %I CHECK (%I IN (%s) OR %I IS NULL)',
                'chk_assets_asset_type', 'asset_type', vals_sql, 'asset_type'
            );
            RAISE NOTICE 'Removed component from chk_assets_asset_type';
        END $$;
        """
    )
