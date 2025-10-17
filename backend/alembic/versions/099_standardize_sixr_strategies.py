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

    Strategy:
    1. Create new enum type with 6 strategies
    2. Add temporary columns with new enum type
    3. Migrate data with mapping
    4. Drop old columns
    5. Rename new columns to original names
    6. Drop old enum type
    """

    # Step 1: Create new enum type with 6 strategies
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sixr_strategy_new') THEN
                CREATE TYPE sixr_strategy_new AS ENUM (
                    'rehost',
                    'replatform',
                    'refactor',
                    'rearchitect',
                    'replace',
                    'retire'
                );
            END IF;
        END $$;
    """
    )

    # Step 2: Add temporary columns with new enum type
    op.execute(
        """
        ALTER TABLE migration.sixr_analyses
        ADD COLUMN IF NOT EXISTS final_recommendation_new sixr_strategy_new;

        ALTER TABLE migration.sixr_recommendations
        ADD COLUMN IF NOT EXISTS recommended_strategy_new sixr_strategy_new;
    """
    )

    # Step 3: Migrate data with strategy mapping
    # Map old strategies to new:
    # - rewrite → replace (custom app rewrites)
    # - repurchase → replace (COTS replacements)
    # - retain → rehost (keep as-is for now, but in migration scope)
    # - retire → retire (keep as-is)
    op.execute(
        """
        -- Migrate sixr_analyses.final_recommendation
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
            ELSE 'rehost'::sixr_strategy_new  -- fallback to safe default
        END
        WHERE final_recommendation IS NOT NULL;

        -- Migrate sixr_recommendations.recommended_strategy
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
            ELSE 'rehost'::sixr_strategy_new  -- fallback to safe default
        END
        WHERE recommended_strategy IS NOT NULL;
    """
    )

    # Step 4: Drop old columns (this also removes foreign key constraints if any)
    op.execute(
        """
        ALTER TABLE migration.sixr_analyses
        DROP COLUMN IF EXISTS final_recommendation;

        ALTER TABLE migration.sixr_recommendations
        DROP COLUMN IF EXISTS recommended_strategy;
    """
    )

    # Step 5: Rename new columns to original names
    op.execute(
        """
        ALTER TABLE migration.sixr_analyses
        RENAME COLUMN final_recommendation_new TO final_recommendation;

        ALTER TABLE migration.sixr_recommendations
        RENAME COLUMN recommended_strategy_new TO recommended_strategy;
    """
    )

    # Step 6: Drop old enum type
    op.execute(
        """
        DROP TYPE IF EXISTS sixr_strategy;
    """
    )

    # Step 7: Rename new enum type to original name
    op.execute(
        """
        ALTER TYPE sixr_strategy_new RENAME TO sixr_strategy;
    """
    )

    # Step 8: Update assets.six_r_strategy VARCHAR values to match new framework
    # (This column is VARCHAR, not enum, so we update the string values)
    op.execute(
        """
        UPDATE migration.assets
        SET six_r_strategy = CASE six_r_strategy
            WHEN 'rewrite' THEN 'replace'
            WHEN 'repurchase' THEN 'replace'
            WHEN 'retain' THEN 'rehost'
            WHEN 'retire' THEN 'retire'
            ELSE six_r_strategy  -- keep existing values
        END
        WHERE six_r_strategy IN ('rewrite', 'repurchase', 'retain', 'retire');
    """
    )


def downgrade() -> None:
    """
    Downgrade not supported - this is a breaking change.

    Attempting to downgrade would require:
    1. Recreating the old 8-strategy enum
    2. Reverse-mapping strategies (lossy - can't distinguish rewrite from replace)
    3. Recreating old columns

    This is not feasible without data loss. If rollback is needed,
    restore from database backup taken before migration.
    """
    raise NotImplementedError(
        "Downgrade not supported for 6R standardization migration. "
        "This is a breaking change. Restore from backup if rollback needed."
    )
