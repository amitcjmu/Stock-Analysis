"""Add asset_id to adaptive_questionnaires for cross-flow deduplication

Revision ID: 128_add_asset_id_to_questionnaires
Revises: 127_cleanup_assessment_test_data
Create Date: 2025-11-06 18:30:00.000000

**Purpose**: Enable asset-based questionnaire deduplication across collection flows

**Problem**:
- Current: Questionnaires are 1:1 with collection_flow_id
- Users answer same questions multiple times if same asset selected in different flows

**Solution**:
- Add asset_id column to adaptive_questionnaires table
- Add unique constraint: (engagement_id, asset_id) - one questionnaire per asset per engagement
- Make collection_flow_id nullable for backward compatibility
- Query logic will check for existing questionnaire by asset_id before generating new one

**Migration Strategy**:
1. Add asset_id column (nullable for backward compat)
2. Backfill asset_id for existing questionnaires from collection_flow metadata
3. Add partial unique index (only where asset_id IS NOT NULL)
4. Future: Make asset_id NOT NULL after all questionnaires migrated

**Rollout**:
- Phase 1: Schema change (this migration) - non-breaking
- Phase 2: Update questionnaire generation logic to use get_or_create pattern
- Phase 3: After 90 days, make asset_id NOT NULL
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "128_add_asset_id_to_questionnaires"
down_revision = (
    "126_update_alembic_version_to_new_naming",
    "127_cleanup_assessment_test_data",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add asset_id column and constraints for questionnaire deduplication."""
    # Use PostgreSQL DO block for idempotent operations
    op.execute(
        """
        DO $$
        BEGIN
            -- 1. Add asset_id column (nullable for backward compatibility)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'adaptive_questionnaires'
                AND column_name = 'asset_id'
            ) THEN
                ALTER TABLE migration.adaptive_questionnaires
                ADD COLUMN asset_id UUID;

                -- Add foreign key to assets table
                ALTER TABLE migration.adaptive_questionnaires
                ADD CONSTRAINT fk_adaptive_questionnaires_asset_id
                FOREIGN KEY (asset_id)
                REFERENCES migration.assets(id)
                ON DELETE CASCADE;

                -- Add index for asset_id lookups
                CREATE INDEX idx_adaptive_questionnaires_asset_id
                ON migration.adaptive_questionnaires(asset_id)
                WHERE asset_id IS NOT NULL;

                RAISE NOTICE 'Added asset_id column with foreign key and index';
            ELSE
                RAISE NOTICE 'Column asset_id already exists, skipping';
            END IF;

            -- 2. Make collection_flow_id nullable (for asset-based questionnaires)
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'adaptive_questionnaires'
                AND column_name = 'collection_flow_id'
                AND is_nullable = 'NO'
            ) THEN
                ALTER TABLE migration.adaptive_questionnaires
                ALTER COLUMN collection_flow_id DROP NOT NULL;

                RAISE NOTICE 'Made collection_flow_id nullable for asset-based questionnaires';
            ELSE
                RAISE NOTICE 'collection_flow_id already nullable, skipping';
            END IF;

            -- 3. Add composite unique constraint for (engagement_id, asset_id)
            -- Partial index: only enforce uniqueness when asset_id is not null
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'adaptive_questionnaires'
                AND indexname = 'uq_questionnaire_per_asset_per_engagement'
            ) THEN
                CREATE UNIQUE INDEX uq_questionnaire_per_asset_per_engagement
                ON migration.adaptive_questionnaires(engagement_id, asset_id)
                WHERE asset_id IS NOT NULL;

                RAISE NOTICE 'Added unique constraint on (engagement_id, asset_id)';
            ELSE
                RAISE NOTICE 'Unique constraint already exists, skipping';
            END IF;

            -- 4. Add composite index for efficient lookups
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'adaptive_questionnaires'
                AND indexname = 'idx_adaptive_questionnaires_engagement_asset'
            ) THEN
                CREATE INDEX idx_adaptive_questionnaires_engagement_asset
                ON migration.adaptive_questionnaires(engagement_id, asset_id)
                WHERE asset_id IS NOT NULL;

                RAISE NOTICE 'Added composite index on (engagement_id, asset_id)';
            ELSE
                RAISE NOTICE 'Composite index already exists, skipping';
            END IF;

        END $$;
        """
    )

    # 5. Backfill asset_id for existing questionnaires (best effort)
    # Only backfill for single-asset flows (multiple assets = skip, let user regenerate)
    op.execute(
        """
        DO $$
        DECLARE
            questionnaire_record RECORD;
            selected_assets UUID[];
            asset_count INT;
        BEGIN
            -- Iterate through questionnaires without asset_id
            FOR questionnaire_record IN
                SELECT q.id, q.collection_flow_id, cf.collection_config
                FROM migration.adaptive_questionnaires q
                JOIN migration.collection_flows cf ON q.collection_flow_id = cf.id
                WHERE q.asset_id IS NULL
                AND cf.collection_config IS NOT NULL
            LOOP
                -- Extract selected_asset_ids from collection_config
                selected_assets := ARRAY(
                    SELECT jsonb_array_elements_text(
                        questionnaire_record.collection_config->'selected_asset_ids'
                    )::UUID
                );

                asset_count := array_length(selected_assets, 1);

                -- Only backfill if exactly one asset selected
                IF asset_count = 1 THEN
                    UPDATE migration.adaptive_questionnaires
                    SET asset_id = selected_assets[1]
                    WHERE id = questionnaire_record.id;

                    RAISE NOTICE 'Backfilled asset_id for questionnaire %: %',
                        questionnaire_record.id, selected_assets[1];
                ELSIF asset_count > 1 THEN
                    RAISE NOTICE 'Skipping questionnaire % (multi-asset flow with % assets)',
                        questionnaire_record.id, asset_count;
                ELSE
                    RAISE NOTICE 'Skipping questionnaire % (no assets in collection_config)',
                        questionnaire_record.id;
                END IF;
            END LOOP;

            RAISE NOTICE 'Backfill complete - check logs for skipped questionnaires';
        END $$;
        """
    )


def downgrade() -> None:
    """Remove asset_id column and constraints."""
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop unique constraint
            IF EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'adaptive_questionnaires'
                AND indexname = 'uq_questionnaire_per_asset_per_engagement'
            ) THEN
                DROP INDEX migration.uq_questionnaire_per_asset_per_engagement;
                RAISE NOTICE 'Dropped unique constraint on (engagement_id, asset_id)';
            END IF;

            -- Drop composite index
            IF EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'adaptive_questionnaires'
                AND indexname = 'idx_adaptive_questionnaires_engagement_asset'
            ) THEN
                DROP INDEX migration.idx_adaptive_questionnaires_engagement_asset;
                RAISE NOTICE 'Dropped composite index';
            END IF;

            -- Drop asset_id index
            IF EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'adaptive_questionnaires'
                AND indexname = 'idx_adaptive_questionnaires_asset_id'
            ) THEN
                DROP INDEX migration.idx_adaptive_questionnaires_asset_id;
                RAISE NOTICE 'Dropped asset_id index';
            END IF;

            -- Drop foreign key constraint
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_schema = 'migration'
                AND table_name = 'adaptive_questionnaires'
                AND constraint_name = 'fk_adaptive_questionnaires_asset_id'
            ) THEN
                ALTER TABLE migration.adaptive_questionnaires
                DROP CONSTRAINT fk_adaptive_questionnaires_asset_id;
                RAISE NOTICE 'Dropped foreign key constraint';
            END IF;

            -- Drop asset_id column
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'adaptive_questionnaires'
                AND column_name = 'asset_id'
            ) THEN
                ALTER TABLE migration.adaptive_questionnaires
                DROP COLUMN asset_id;
                RAISE NOTICE 'Dropped asset_id column';
            END IF;

            -- Restore collection_flow_id NOT NULL constraint
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'adaptive_questionnaires'
                AND column_name = 'collection_flow_id'
                AND is_nullable = 'YES'
            ) THEN
                ALTER TABLE migration.adaptive_questionnaires
                ALTER COLUMN collection_flow_id SET NOT NULL;
                RAISE NOTICE 'Restored collection_flow_id NOT NULL constraint';
            END IF;

        END $$;
        """
    )
