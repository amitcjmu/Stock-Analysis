"""collection_background_tasks

Create collection_background_tasks table for persistent task state.
Persists background task state to database for resume/retry and status polling.

Revision ID: 105_collection_background_tasks
Revises: 104_asset_custom_attributes
Create Date: 2025-10-23 21:33:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "105_collection_background_tasks"
down_revision = "104_asset_custom_attributes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create collection_background_tasks table with indexes.

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
                AND table_name = 'collection_background_tasks'
            ) THEN
                CREATE TABLE migration.collection_background_tasks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    client_account_id UUID NOT NULL,
                    engagement_id UUID NOT NULL,
                    child_flow_id UUID NOT NULL,

                    -- Task identification
                    task_type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,

                    -- Progress tracking
                    progress_percent INTEGER DEFAULT 0,
                    current_stage VARCHAR(100),
                    rows_processed INTEGER DEFAULT 0,
                    total_rows INTEGER,

                    -- Task data
                    input_params JSONB NOT NULL,
                    result_data JSONB,
                    error_message TEXT,

                    -- Cancellation support
                    is_cancellable BOOLEAN DEFAULT FALSE,
                    cancelled_at TIMESTAMP WITH TIME ZONE,
                    cancelled_by VARCHAR(255),

                    -- Idempotency and retry
                    idempotency_key VARCHAR(255),
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,

                    -- Timestamps
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

                    CONSTRAINT fk_tasks_client FOREIGN KEY (client_account_id)
                        REFERENCES migration.client_accounts(id),
                    CONSTRAINT fk_tasks_engagement FOREIGN KEY (engagement_id)
                        REFERENCES migration.engagements(id),
                    CONSTRAINT unique_idempotency_key UNIQUE (
                        client_account_id, engagement_id, idempotency_key
                    ) DEFERRABLE INITIALLY DEFERRED
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
            -- Index for status-based filtering
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_background_tasks'
                AND indexname = 'idx_tasks_status'
            ) THEN
                CREATE INDEX idx_tasks_status
                ON migration.collection_background_tasks(status, client_account_id, engagement_id);
            END IF;

            -- Index for child flow lookups
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_background_tasks'
                AND indexname = 'idx_tasks_child_flow'
            ) THEN
                CREATE INDEX idx_tasks_child_flow
                ON migration.collection_background_tasks(child_flow_id);
            END IF;

            -- Index for task type filtering
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_background_tasks'
                AND indexname = 'idx_tasks_type'
            ) THEN
                CREATE INDEX idx_tasks_type
                ON migration.collection_background_tasks(task_type, status);
            END IF;

            -- Index for temporal queries
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'collection_background_tasks'
                AND indexname = 'idx_tasks_created'
            ) THEN
                CREATE INDEX idx_tasks_created
                ON migration.collection_background_tasks(created_at DESC);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """
    Drop collection_background_tasks table and indexes.

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
                AND table_name = 'collection_background_tasks'
            ) THEN
                DROP TABLE migration.collection_background_tasks CASCADE;
            END IF;
        END $$;
        """
    )
