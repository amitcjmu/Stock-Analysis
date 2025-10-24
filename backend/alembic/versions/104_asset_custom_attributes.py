"""asset_custom_attributes

Create asset_custom_attributes table for unmapped import fields.
Stores flexible schema attributes from bulk imports.

Revision ID: 104_asset_custom_attributes
Revises: 103_collection_answer_history
Create Date: 2025-10-23 21:32:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "104_asset_custom_attributes"
down_revision = "103_collection_answer_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create asset_custom_attributes table with indexes.

    IDEMPOTENT: Uses IF NOT EXISTS checks for table and index creation.
    """
    # Create table (idempotent)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'asset_custom_attributes'
            ) THEN
                CREATE TABLE migration.asset_custom_attributes (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    client_account_id UUID NOT NULL,
                    engagement_id UUID NOT NULL,

                    -- Asset reference
                    asset_id UUID NOT NULL,
                    asset_type VARCHAR(100) NOT NULL,

                    -- Custom attribute data
                    attributes JSONB NOT NULL,

                    -- Import tracking
                    source VARCHAR(100),
                    import_batch_id UUID,
                    import_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

                    -- Pattern analysis (for future agent suggestions)
                    pattern_detected BOOLEAN DEFAULT FALSE,
                    suggested_standard_field VARCHAR(255),

                    -- Metadata
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

                    CONSTRAINT fk_custom_attrs_client FOREIGN KEY (client_account_id)
                        REFERENCES migration.client_accounts(id),
                    CONSTRAINT fk_custom_attrs_engagement FOREIGN KEY (engagement_id)
                        REFERENCES migration.engagements(id),
                    CONSTRAINT unique_asset_custom_attrs UNIQUE (asset_id, client_account_id, engagement_id)
                );
            END IF;
        END $$;
        """
    )

    # Create indexes (idempotent)
    op.execute(
        """
        DO $$
        BEGIN
            -- Index for asset-based lookups
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'asset_custom_attributes'
                AND indexname = 'idx_custom_attrs_asset'
            ) THEN
                CREATE INDEX idx_custom_attrs_asset
                ON migration.asset_custom_attributes(asset_id, client_account_id, engagement_id);
            END IF;

            -- Partial index for pattern detection
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'asset_custom_attributes'
                AND indexname = 'idx_custom_attrs_pattern'
            ) THEN
                CREATE INDEX idx_custom_attrs_pattern
                ON migration.asset_custom_attributes(pattern_detected)
                WHERE pattern_detected = TRUE;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """
    Drop asset_custom_attributes table and indexes.

    IDEMPOTENT: Uses IF EXISTS checks for cleanup.
    """
    # Drop table (cascades to indexes)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'asset_custom_attributes'
            ) THEN
                DROP TABLE migration.asset_custom_attributes CASCADE;
            END IF;
        END $$;
        """
    )
