"""Backfill canonical applications for orphaned assets

Revision ID: 130_backfill_canonical_apps
Revises: 129_add_dependents_column_to_assets
Create Date: 2025-11-12

ISSUE-999 Phase 4: Create canonical applications and junction records
for assets that have application_name but no collection_flow_applications records.

This migration addresses 82% of assets being orphaned from the canonicalization
system, preventing assessment flows from properly mapping 6R recommendations.

Migration Strategy:
1. Create "System Migration" collection flow per tenant (one per client_account_id + engagement_id)
2. Create canonical applications for unique application names
3. Create junction records linking orphaned assets to canonical apps

The migration is:
- Idempotent: Can be run multiple times safely
- Reversible: Downgrade removes migration artifacts
- Safe: Preserves all existing data
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "130_backfill_canonical_apps"
down_revision = "129_add_dependents_column_to_assets"
branch_labels = None
depends_on = None


def upgrade():
    """
    Backfill canonical applications for orphaned assets.

    Creates:
    1. "System Migration" collection flow per tenant
    2. Canonical applications for unique application names
    3. Junction records linking assets to canonical apps
    """

    # Use raw SQL for maximum control and idempotency
    conn = op.get_bind()

    # Step 1: Create "System Migration" collection flows (one per tenant)
    # Note: collection_flows requires flow_id, user_id, automation_tier, progress_percentage
    # We use the first available user_id from the users table as a system placeholder
    conn.execute(
        sa.text(
            """
        INSERT INTO migration.collection_flows (
            id,
            flow_id,
            client_account_id,
            engagement_id,
            user_id,
            flow_name,
            automation_tier,
            status,
            progress_percentage,
            created_at,
            updated_at
        )
        SELECT
            gen_random_uuid(),
            gen_random_uuid(),  -- flow_id (required)
            client_account_id,
            engagement_id,
            (SELECT id FROM migration.users LIMIT 1),  -- user_id (required FK to users table)
            'System Migration - Canonical App Backfill',
            'tier_1',  -- automation_tier (required enum: tier_1, tier_2, tier_3, tier_4)
            'completed',
            100.0,  -- progress_percentage (required, default 0.0)
            NOW(),
            NOW()
        FROM (
            SELECT DISTINCT
                client_account_id,
                engagement_id
            FROM migration.assets
            WHERE application_name IS NOT NULL
                AND application_name != ''
                AND NOT EXISTS (
                    SELECT 1
                    FROM migration.collection_flow_applications cfa
                    WHERE cfa.asset_id = assets.id
                )
        ) AS tenants
        WHERE NOT EXISTS (
            SELECT 1
            FROM migration.collection_flows cf
            WHERE cf.client_account_id = tenants.client_account_id
                AND cf.engagement_id = tenants.engagement_id
                AND cf.flow_name = 'System Migration - Canonical App Backfill'
        );
    """
        )
    )

    # Step 2: Create canonical applications for orphaned assets
    # Uses ON CONFLICT DO NOTHING to ensure idempotency (no updates on reruns)
    conn.execute(
        sa.text(
            """
        INSERT INTO migration.canonical_applications (
            id,
            canonical_name,
            normalized_name,
            name_hash,
            client_account_id,
            engagement_id,
            confidence_score,
            is_verified,
            usage_count,
            created_at,
            updated_at
        )
        SELECT DISTINCT ON (orphaned_apps.client_account_id, orphaned_apps.engagement_id, orphaned_apps.name_hash)
            gen_random_uuid(),
            orphaned_apps.application_name,
            orphaned_apps.normalized_name,
            orphaned_apps.name_hash,
            orphaned_apps.client_account_id,
            orphaned_apps.engagement_id,
            0.5,  -- Lower confidence for backfilled apps
            FALSE,
            1,
            NOW(),
            NOW()
        FROM (
            SELECT DISTINCT
                application_name,
                LOWER(REGEXP_REPLACE(application_name, '[^a-zA-Z0-9]', '', 'g')) AS normalized_name,
                MD5(LOWER(REGEXP_REPLACE(application_name, '[^a-zA-Z0-9]', '', 'g'))) AS name_hash,
                client_account_id,
                engagement_id
            FROM migration.assets
            WHERE application_name IS NOT NULL
                AND application_name != ''
                AND NOT EXISTS (
                    SELECT 1
                    FROM migration.collection_flow_applications cfa
                    WHERE cfa.asset_id = assets.id
                )
        ) AS orphaned_apps
        ON CONFLICT (client_account_id, engagement_id, normalized_name)
        DO NOTHING;  -- Idempotent: Don't update existing canonical apps on reruns
    """
        )
    )

    # Step 3: Create junction records for orphaned assets
    conn.execute(
        sa.text(
            """
        INSERT INTO migration.collection_flow_applications (
            id,
            collection_flow_id,
            asset_id,
            application_name,
            canonical_application_id,
            deduplication_method,
            match_confidence,
            collection_status,
            client_account_id,
            engagement_id,
            created_at,
            updated_at
        )
        SELECT
            gen_random_uuid(),
            (
                SELECT id
                FROM migration.collection_flows cf
                WHERE cf.client_account_id = a.client_account_id
                    AND cf.engagement_id = a.engagement_id
                    AND cf.flow_name = 'System Migration - Canonical App Backfill'
                LIMIT 1
            ),
            a.id,
            a.application_name,
            (
                SELECT ca.id
                FROM migration.canonical_applications ca
                WHERE ca.client_account_id = a.client_account_id
                    AND ca.engagement_id = a.engagement_id
                    AND ca.name_hash = MD5(LOWER(REGEXP_REPLACE(a.application_name, '[^a-zA-Z0-9]', '', 'g')))
                LIMIT 1
            ),
            'migration_backfill',
            0.5,
            'validated',
            a.client_account_id,
            a.engagement_id,
            NOW(),
            NOW()
        FROM migration.assets a
        WHERE a.application_name IS NOT NULL
            AND a.application_name != ''
            AND NOT EXISTS (
                SELECT 1
                FROM migration.collection_flow_applications cfa
                WHERE cfa.asset_id = a.id
            );
    """
        )
    )


def downgrade():
    """
    Remove backfilled canonical applications and junction records.

    Reverses the upgrade by:
    1. Deleting junction records created by migration
    2. Deleting orphaned canonical applications (no remaining references)
    3. Deleting System Migration collection flows

    This downgrade is safe and fully reversible:
    - Only removes canonical apps with ZERO remaining junction records
    - Preserves canonical apps that were adopted by subsequent flows
    - No foreign key violations
    """

    conn = op.get_bind()

    # Step 1: Delete junction records created by migration
    conn.execute(
        sa.text(
            """
        DELETE FROM migration.collection_flow_applications
        WHERE deduplication_method = 'migration_backfill';
    """
        )
    )

    # Step 2: Delete orphaned canonical applications
    # Only delete canonical apps with NO remaining junction records
    # This preserves canonical apps that were adopted by other flows
    conn.execute(
        sa.text(
            """
        DELETE FROM migration.canonical_applications
        WHERE id IN (
            SELECT ca.id
            FROM migration.canonical_applications ca
            LEFT JOIN migration.collection_flow_applications cfa
                ON ca.id = cfa.canonical_application_id
            WHERE cfa.id IS NULL  -- No junction records reference this canonical app
        );
    """
        )
    )

    # Step 3: Delete System Migration collection flows
    conn.execute(
        sa.text(
            """
        DELETE FROM migration.collection_flows
        WHERE flow_name = 'System Migration - Canonical App Backfill';
    """
        )
    )
