"""collection_answer_history

Create collection_answer_history table for answer audit trail and re-emergence tracking.
Tracks answer changes for audit and re-emergence logic.

Revision ID: 103_collection_answer_history
Revises: 102_collection_question_rules
Create Date: 2025-10-23 21:31:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "103_collection_answer_history"
down_revision = "102_collection_question_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create collection_answer_history table with indexes.

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
                AND table_name = 'collection_answer_history'
            ) THEN
                CREATE TABLE migration.collection_answer_history (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    client_account_id UUID NOT NULL,
                    engagement_id UUID NOT NULL,

                    -- Reference to questionnaire and asset
                    questionnaire_id UUID NOT NULL,
                    asset_id UUID NOT NULL,
                    question_id VARCHAR(255) NOT NULL,

                    -- Answer data
                    answer_value TEXT,
                    answer_source VARCHAR(50) NOT NULL,
                    confidence_score DECIMAL(5,2),

                    -- Change tracking
                    previous_value TEXT,
                    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    changed_by VARCHAR(255),

                    -- Re-emergence tracking
                    reopened_at TIMESTAMP WITH TIME ZONE,
                    reopened_reason TEXT,
                    reopened_by VARCHAR(50),

                    -- Metadata
                    metadata JSONB,

                    CONSTRAINT fk_answer_history_questionnaire FOREIGN KEY (questionnaire_id)
                        REFERENCES migration.adaptive_questionnaires(id),
                    CONSTRAINT fk_answer_history_client FOREIGN KEY (client_account_id)
                        REFERENCES migration.client_accounts(id),
                    CONSTRAINT fk_answer_history_engagement FOREIGN KEY (engagement_id)
                        REFERENCES migration.engagements(id)
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
                AND tablename = 'collection_answer_history'
                AND indexname = 'idx_answer_history_asset'
            ) THEN
                CREATE INDEX idx_answer_history_asset
                ON migration.collection_answer_history(asset_id, client_account_id, engagement_id);
            END IF;

            -- Index for question-based lookups
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_answer_history'
                AND indexname = 'idx_answer_history_question'
            ) THEN
                CREATE INDEX idx_answer_history_question
                ON migration.collection_answer_history(question_id, asset_id);
            END IF;

            -- Index for reopened answers (partial index)
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_answer_history'
                AND indexname = 'idx_answer_history_reopened'
            ) THEN
                CREATE INDEX idx_answer_history_reopened
                ON migration.collection_answer_history(reopened_at)
                WHERE reopened_at IS NOT NULL;
            END IF;

            -- Composite index for timeline queries (per GPT-5 suggestion)
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_answer_history'
                AND indexname = 'idx_answer_history_timeline'
            ) THEN
                CREATE INDEX idx_answer_history_timeline
                ON migration.collection_answer_history(
                    client_account_id,
                    engagement_id,
                    questionnaire_id,
                    question_id,
                    changed_at DESC
                );
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """
    Drop collection_answer_history table and indexes.

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
                AND table_name = 'collection_answer_history'
            ) THEN
                DROP TABLE migration.collection_answer_history CASCADE;
            END IF;
        END $$;
        """
    )
