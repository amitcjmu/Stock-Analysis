"""backfill_assessment_source_collection

Revision ID: 121_backfill_assessment_source_collection
Revises: 115_fix_planning_flows_tenant_columns
Create Date: 2025-10-29

Description:
    Backfills source_collection metadata for existing assessment flows (Issue #861).

    For each assessment flow without source_collection metadata:
    1. Find collection flow that contains matching applications via collection_flow_applications
    2. Update flow_metadata with source_collection information

    This enables assessment flows to load application data from their source collection.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "121_backfill_assessment_source_collection"
down_revision = "115_fix_planning_flows_tenant_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Backfill source_collection metadata for existing assessment flows.

    Strategy:
    1. Find assessment flows with NULL or empty flow_metadata
    2. For each flow, query collection_flow_applications to find source collection
    3. Update flow_metadata with source_collection.collection_flow_id
    """
    # Use PostgreSQL DO block for complex backfill logic
    op.execute(
        """
        DO $$
        DECLARE
            assessment_record RECORD;
            collection_flow_uuid UUID;
            updated_count INTEGER := 0;
        BEGIN
            -- Iterate through assessment flows needing backfill
            FOR assessment_record IN
                SELECT
                    af.id,
                    af.flow_id,
                    af.selected_asset_ids,
                    af.flow_metadata,
                    af.client_account_id,
                    af.engagement_id
                FROM migration.assessment_flows af
                WHERE af.flow_metadata IS NULL
                   OR NOT (af.flow_metadata ? 'source_collection')
                   OR (af.flow_metadata->'source_collection'->>'collection_flow_id') IS NULL
            LOOP
                -- Skip if no selected assets
                CONTINUE WHEN assessment_record.selected_asset_ids IS NULL
                           OR array_length(assessment_record.selected_asset_ids, 1) = 0;

                -- Find collection flow containing these assets
                -- Strategy: Find collection_flow_id that has ANY of these assets
                SELECT DISTINCT cfa.collection_flow_id
                INTO collection_flow_uuid
                FROM migration.collection_flow_applications cfa
                WHERE cfa.asset_id = ANY(
                    SELECT unnest(assessment_record.selected_asset_ids)::uuid
                )
                AND cfa.client_account_id = assessment_record.client_account_id
                AND cfa.engagement_id = assessment_record.engagement_id
                LIMIT 1;

                -- Update flow_metadata if collection flow found
                IF collection_flow_uuid IS NOT NULL THEN
                    UPDATE migration.assessment_flows
                    SET flow_metadata = COALESCE(flow_metadata, '{}'::jsonb) ||
                        jsonb_build_object(
                            'source_collection',
                            jsonb_build_object(
                                'collection_flow_id', collection_flow_uuid::text,
                                'linked_at', NOW()::text,
                                'backfilled', true,
                                'backfill_migration', '121_backfill_assessment_source_collection'
                            )
                        )
                    WHERE id = assessment_record.id;

                    updated_count := updated_count + 1;

                    RAISE NOTICE 'Backfilled assessment flow % with source collection %',
                                 assessment_record.flow_id,
                                 collection_flow_uuid;
                END IF;
            END LOOP;

            RAISE NOTICE 'Backfill complete: Updated % assessment flows with source_collection metadata',
                         updated_count;
        END $$;
    """
    )


def downgrade() -> None:
    """
    Remove backfilled source_collection metadata.

    Only removes entries marked as 'backfilled' to avoid removing manually created links.
    """
    op.execute(
        """
        UPDATE migration.assessment_flows
        SET flow_metadata = flow_metadata - 'source_collection'
        WHERE flow_metadata->'source_collection'->>'backfilled' = 'true'
          AND flow_metadata->'source_collection'->>'backfill_migration' = '121_backfill_assessment_source_collection';
    """
    )
