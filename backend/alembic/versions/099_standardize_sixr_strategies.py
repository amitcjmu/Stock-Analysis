"""Standardize 6R strategies to platform-aligned framework

Revision ID: 099_standardize_sixr_strategies
Revises: 098_add_enrichment_performance_indexes
Create Date: 2025-10-17

This migration standardizes the 6R strategy framework to align with the platform's
business logic for migration and modernization:

BEFORE (8 strategies):
- rehost, replatform, refactor, rearchitect, replace, rewrite, retire, retain

AFTER (6 strategies - platform-aligned):
- rehost: Lift and shift (minimal changes)
- replatform: Reconfigure as PaaS
- refactor: Modify code for cloud deployment
- rearchitect: Microservices/cloud-native transformation
- replace: Replace with COTS/SaaS OR rewrite custom apps (consolidates "rewrite" + "repurchase")
- retire: Decommission/sunset assets

REMOVED:
- "rewrite" → mapped to "replace" (for custom app rewrites)
- "repurchase" → mapped to "replace" (for COTS replacements)
- "retain" → mapped to "rehost" (keep as-is until migration, but IN SCOPE)

RATIONALE:
- "retain" (keep as-is permanently) is OUT OF SCOPE for a migration platform
- "replace" consolidates both COTS purchases and custom rewrites
- Platform focuses on assets being migrated/modernized, not assets staying behind

This is a breaking change that requires application code updates.
"""

from alembic import op

# revision identifiers
revision = "099_standardize_sixr_strategies"
down_revision = "098_add_enrichment_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Migrate from 8-strategy framework to 6-strategy framework.

    IDEMPOTENT: This migration checks current state and only applies necessary changes.
    Safe to run multiple times.

    Strategy:
    1. Check if migration already applied (sixr_strategy has 6 values)
    2. If not applied: Create new enum type with 6 strategies
    3. Add temporary columns with new enum type
    4. Migrate data with mapping
    5. Drop old columns and rename new columns
    6. Drop old enum type and rename new enum
    """

    # Check if migration already applied by checking enum values
    op.execute(
        """
        DO $$
        DECLARE
            strategy_count INTEGER;
            has_rewrite BOOLEAN;
        BEGIN
            -- Check if sixr_strategy enum exists and count its values
            SELECT COUNT(*) INTO strategy_count
            FROM pg_enum
            WHERE enumtypid = (
                SELECT oid FROM pg_type WHERE typname = 'sixr_strategy'
            );

            -- Check if old 'rewrite' value exists (indicator migration not done)
            SELECT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'sixr_strategy')
                  AND enumlabel = 'rewrite'
            ) INTO has_rewrite;

            -- If enum already has 6 values and no 'rewrite', migration is complete
            IF strategy_count = 6 AND NOT has_rewrite THEN
                RAISE NOTICE 'Migration already applied: sixr_strategy has 6 strategies without legacy values';
                RETURN;
            END IF;

            -- Migration needs to run - proceed with transformation
            RAISE NOTICE 'Applying 6R strategy standardization migration';

            -- Step 1: Create new enum type with 6 strategies (if not exists)
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sixr_strategy_new') THEN
                CREATE TYPE sixr_strategy_new AS ENUM (
                    'rehost',
                    'replatform',
                    'refactor',
                    'rearchitect',
                    'replace',
                    'retire'
                );
                RAISE NOTICE 'Created sixr_strategy_new enum type';
            END IF;

            -- Step 2: Add temporary columns with new enum type (if not exists)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'sixr_analyses'
                  AND column_name = 'final_recommendation_new'
            ) THEN
                ALTER TABLE migration.sixr_analyses
                ADD COLUMN final_recommendation_new sixr_strategy_new;
                RAISE NOTICE 'Added final_recommendation_new column';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'sixr_recommendations'
                  AND column_name = 'recommended_strategy_new'
            ) THEN
                ALTER TABLE migration.sixr_recommendations
                ADD COLUMN recommended_strategy_new sixr_strategy_new;
                RAISE NOTICE 'Added recommended_strategy_new column';
            END IF;

            -- Step 3: Migrate data with strategy mapping
            -- Only migrate if old column exists and new column is empty
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'sixr_analyses'
                  AND column_name = 'final_recommendation'
            ) THEN
                UPDATE migration.sixr_analyses
                SET final_recommendation_new = CASE final_recommendation::text
                    WHEN 'rewrite' THEN 'replace'::sixr_strategy_new
                    WHEN 'repurchase' THEN 'replace'::sixr_strategy_new
                    WHEN 'retain' THEN 'rehost'::sixr_strategy_new
                    WHEN 'rehost' THEN 'rehost'::sixr_strategy_new
                    WHEN 'replatform' THEN 'replatform'::sixr_strategy_new
                    WHEN 'refactor' THEN 'refactor'::sixr_strategy_new
                    WHEN 'rearchitect' THEN 'rearchitect'::sixr_strategy_new
                    WHEN 'replace' THEN 'replace'::sixr_strategy_new
                    WHEN 'retire' THEN 'retire'::sixr_strategy_new
                    ELSE 'rehost'::sixr_strategy_new
                END
                WHERE final_recommendation IS NOT NULL
                  AND final_recommendation_new IS NULL;

                RAISE NOTICE 'Migrated sixr_analyses.final_recommendation data';
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'sixr_recommendations'
                  AND column_name = 'recommended_strategy'
            ) THEN
                UPDATE migration.sixr_recommendations
                SET recommended_strategy_new = CASE recommended_strategy::text
                    WHEN 'rewrite' THEN 'replace'::sixr_strategy_new
                    WHEN 'repurchase' THEN 'replace'::sixr_strategy_new
                    WHEN 'retain' THEN 'rehost'::sixr_strategy_new
                    WHEN 'rehost' THEN 'rehost'::sixr_strategy_new
                    WHEN 'replatform' THEN 'replatform'::sixr_strategy_new
                    WHEN 'refactor' THEN 'refactor'::sixr_strategy_new
                    WHEN 'rearchitect' THEN 'rearchitect'::sixr_strategy_new
                    WHEN 'replace' THEN 'replace'::sixr_strategy_new
                    WHEN 'retire' THEN 'retire'::sixr_strategy_new
                    ELSE 'rehost'::sixr_strategy_new
                END
                WHERE recommended_strategy IS NOT NULL
                  AND recommended_strategy_new IS NULL;

                RAISE NOTICE 'Migrated sixr_recommendations.recommended_strategy data';
            END IF;

            -- Step 4: Drop old columns (if they exist)
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'sixr_analyses'
                  AND column_name = 'final_recommendation'
            ) THEN
                ALTER TABLE migration.sixr_analyses DROP COLUMN final_recommendation;
                RAISE NOTICE 'Dropped old final_recommendation column';
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'sixr_recommendations'
                  AND column_name = 'recommended_strategy'
            ) THEN
                ALTER TABLE migration.sixr_recommendations DROP COLUMN recommended_strategy;
                RAISE NOTICE 'Dropped old recommended_strategy column';
            END IF;

            -- Step 5: Rename new columns to original names (if not already renamed)
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'sixr_analyses'
                  AND column_name = 'final_recommendation_new'
            ) THEN
                ALTER TABLE migration.sixr_analyses
                RENAME COLUMN final_recommendation_new TO final_recommendation;
                RAISE NOTICE 'Renamed final_recommendation_new to final_recommendation';
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = 'sixr_recommendations'
                  AND column_name = 'recommended_strategy_new'
            ) THEN
                ALTER TABLE migration.sixr_recommendations
                RENAME COLUMN recommended_strategy_new TO recommended_strategy;
                RAISE NOTICE 'Renamed recommended_strategy_new to recommended_strategy';
            END IF;

            -- Step 6: Drop old enum type (if it still exists as separate type)
            -- Note: Can't drop if columns still reference it
            IF EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'sixr_strategy'
            ) AND EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'sixr_strategy_new'
            ) THEN
                DROP TYPE sixr_strategy;
                RAISE NOTICE 'Dropped old sixr_strategy enum type';
            END IF;

            -- Step 7: Rename new enum type to original name (if not already renamed)
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sixr_strategy_new') THEN
                ALTER TYPE sixr_strategy_new RENAME TO sixr_strategy;
                RAISE NOTICE 'Renamed sixr_strategy_new to sixr_strategy';
            END IF;

            -- Step 8: Update assets.six_r_strategy VARCHAR values (idempotent)
            UPDATE migration.assets
            SET six_r_strategy = CASE six_r_strategy
                WHEN 'rewrite' THEN 'replace'
                WHEN 'repurchase' THEN 'replace'
                WHEN 'retain' THEN 'rehost'
                WHEN 'retire' THEN 'retire'
                ELSE six_r_strategy
            END
            WHERE six_r_strategy IN ('rewrite', 'repurchase', 'retain', 'retire');

            RAISE NOTICE 'Migration 099 completed successfully';
        END $$;
    """
    )


def downgrade() -> None:
    """
    Downgrade NOT SUPPORTED - this is a BREAKING CHANGE with data loss.

    WHY DOWNGRADE IS IMPOSSIBLE:
    ============================

    This migration consolidates 8 strategies into 6 strategies:
    - OLD (8): rehost, replatform, refactor, rearchitect, replace, rewrite, retire, retain
    - NEW (6): rehost, replatform, refactor, rearchitect, replace, retire

    The migration performs LOSSY MAPPINGS:
    - rewrite → replace (custom app rewrites)
    - repurchase → replace (COTS replacements)
    - retain → rehost (keep as-is until migration)

    DOWNGRADE PROBLEMS:
    ===================

    1. LOSSY DATA MAPPING:
       After migration, all "rewrite" and "repurchase" values become "replace".
       You cannot distinguish which "replace" came from which source.
       Example:
         - Before: App A = "rewrite", App B = "repurchase"
         - After:  App A = "replace", App B = "replace"
         - Downgrade: App A = ??? (could be rewrite OR repurchase)

    2. BUSINESS LOGIC CHANGE:
       "retain" (keep permanently, out-of-scope) mapped to "rehost" (migrate later).
       Original business context is lost - we don't know which "rehost" values
       were originally "retain" vs actual rehost strategies.

    3. POSTGRESQL ENUM CONSTRAINTS:
       The old enum type is DESTROYED during migration. PostgreSQL doesn't allow
       adding values to enums that are referenced by existing columns, so we use
       a "create new type, migrate data, drop old type" pattern that is irreversible.

    4. POTENTIAL DATA CORRUPTION:
       Attempting reverse mapping would require guessing original values, which
       could corrupt business decisions recorded in the database.

    ROLLBACK STRATEGY:
    ==================

    If you need to rollback this migration:

    1. **STOP THE APPLICATION** - Prevent new writes during rollback
    2. **RESTORE FROM BACKUP** - Use database backup taken BEFORE this migration:
       ```bash
       # PostgreSQL restore example
       pg_restore -U postgres -d migration_db backup_before_099.dump
       ```
    3. **VERIFY DATA INTEGRITY** - Check that strategy values are correct:
       ```sql
       SELECT six_r_strategy, COUNT(*)
       FROM migration.assets
       GROUP BY six_r_strategy;
       ```
    4. **ROLLBACK CODE** - Deploy application code that expects 8 strategies
    5. **UPDATE ALEMBIC VERSION** - Set version back to previous migration:
       ```sql
       UPDATE alembic_version
       SET version_num = '098_add_enrichment_performance_indexes';
       ```

    ALTERNATIVE (if backup unavailable):
    ====================================

    If no backup exists and you MUST rollback, you'll need to:
    1. Manually recreate the 8-strategy enum
    2. Manually review each "replace" value and determine original intent
       (contact business stakeholders to determine which should be rewrite/repurchase)
    3. Accept that some data will be incorrect and plan for manual corrections

    This is error-prone and NOT RECOMMENDED. Always maintain backups before
    running breaking change migrations.

    FOR FUTURE MIGRATION CONSOLIDATION:
    ===================================

    When consolidating multiple migrations in the future, preserve this
    downgrade documentation to help future engineers understand why rollback
    is not possible and what the alternatives are.
    """
    raise NotImplementedError(
        "Downgrade not supported for 6R standardization migration (099). "
        "This is a BREAKING CHANGE with lossy data mapping. "
        "Reverse mapping would cause data corruption. "
        "To rollback: restore from database backup taken before this migration. "
        "See downgrade() docstring for detailed explanation and rollback procedure."
    )
