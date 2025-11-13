"""collection_question_rules

Create collection_question_rules table for adaptive questionnaire enhancements.
Maps questions to asset types and defines inheritance rules.

Revision ID: 102_collection_question_rules
Revises: 101_eliminate_collection_phase_state
Create Date: 2025-10-23 21:30:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "102_collection_question_rules"
down_revision = "101_eliminate_collection_phase_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create collection_question_rules table with indexes.

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
                AND table_name = 'collection_question_rules'
            ) THEN
                CREATE TABLE migration.collection_question_rules (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    client_account_id UUID NOT NULL,
                    engagement_id UUID NOT NULL,

                    -- Question identification
                    question_id VARCHAR(255) NOT NULL,
                    question_text TEXT NOT NULL,
                    question_type VARCHAR(50) NOT NULL,

                    -- Asset type applicability
                    asset_type VARCHAR(100) NOT NULL,
                    is_applicable BOOLEAN NOT NULL DEFAULT TRUE,

                    -- Inheritance rules
                    inherits_from_parent BOOLEAN DEFAULT TRUE,
                    override_parent BOOLEAN DEFAULT FALSE,

                    -- Answer options (for dropdowns)
                    answer_options JSONB,

                    -- Display configuration
                    display_order INTEGER,
                    section VARCHAR(100),
                    weight INTEGER DEFAULT 40,
                    is_required BOOLEAN DEFAULT FALSE,

                    -- Agent generation hints
                    generation_hint TEXT,

                    -- Metadata
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    created_by VARCHAR(255),

                    CONSTRAINT fk_question_rules_client FOREIGN KEY (client_account_id)
                        REFERENCES migration.client_accounts(id),
                    CONSTRAINT fk_question_rules_engagement FOREIGN KEY (engagement_id)
                        REFERENCES migration.engagements(id),
                    CONSTRAINT unique_question_asset_type UNIQUE (
                        client_account_id, engagement_id, question_id, asset_type
                    )
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
            -- Index for asset type lookups
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_question_rules'
                AND indexname = 'idx_question_rules_asset_type'
            ) THEN
                CREATE INDEX idx_question_rules_asset_type
                ON migration.collection_question_rules(asset_type, client_account_id, engagement_id);
            END IF;

            -- Index for applicability filtering
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_question_rules'
                AND indexname = 'idx_question_rules_applicable'
            ) THEN
                CREATE INDEX idx_question_rules_applicable
                ON migration.collection_question_rules(is_applicable, client_account_id, engagement_id);
            END IF;

            -- Composite index for high-frequency lookups (per GPT-5 suggestion)
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_question_rules'
                AND indexname = 'idx_question_rules_composite'
            ) THEN
                CREATE INDEX idx_question_rules_composite
                ON migration.collection_question_rules(client_account_id, engagement_id, question_id);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """
    Drop collection_question_rules table and indexes.

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
                AND table_name = 'collection_question_rules'
            ) THEN
                DROP TABLE migration.collection_question_rules CASCADE;
            END IF;
        END $$;
        """
    )
