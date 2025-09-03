"""Add analysis queue tables

Revision ID: 2ae8940123e6
Revises: fcacece8fa7b
Create Date: 2025-08-01 02:06:02.041970

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2ae8940123e6"
down_revision = "fcacece8fa7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Complete migration using pure SQL for maximum compatibility
    op.execute(
        """
        -- Create enum types if they don't exist
        DO $$ BEGIN
            CREATE TYPE queuestatus AS ENUM ('pending', 'processing', 'paused', 'completed', 'cancelled', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE itemstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;

        -- Create analysis_queues table if it doesn't exist
        CREATE TABLE IF NOT EXISTS analysis_queues (
            id UUID NOT NULL,
            name VARCHAR(255) NOT NULL,
            status queuestatus NOT NULL,
            client_id UUID NOT NULL,
            engagement_id UUID NOT NULL,
            created_by UUID NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            started_at TIMESTAMP WITHOUT TIME ZONE,
            completed_at TIMESTAMP WITHOUT TIME ZONE,
            CONSTRAINT analysis_queues_pkey PRIMARY KEY (id)
        );

        -- Create analysis_queue_items table if it doesn't exist
        CREATE TABLE IF NOT EXISTS analysis_queue_items (
            id UUID NOT NULL,
            queue_id UUID NOT NULL,
            application_id VARCHAR(255) NOT NULL,
            status itemstatus NOT NULL,
            started_at TIMESTAMP WITHOUT TIME ZONE,
            completed_at TIMESTAMP WITHOUT TIME ZONE,
            error_message TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            CONSTRAINT analysis_queue_items_pkey PRIMARY KEY (id),
            CONSTRAINT analysis_queue_items_queue_id_fkey FOREIGN KEY (queue_id)
                REFERENCES analysis_queues (id) ON DELETE CASCADE
        );

        -- Create indexes if they don't exist
        CREATE INDEX IF NOT EXISTS idx_analysis_queues_context
            ON analysis_queues (client_id, engagement_id);

        CREATE INDEX IF NOT EXISTS idx_queue_items_queue_id
            ON analysis_queue_items (queue_id);
    """
    )


def downgrade() -> None:
    # Drop indexes if they exist
    try:
        op.drop_index("idx_queue_items_queue_id", table_name="analysis_queue_items")
    except Exception:
        pass  # Index may not exist

    try:
        op.drop_index("idx_analysis_queues_context", table_name="analysis_queues")
    except Exception:
        pass  # Index may not exist

    # Drop tables if they exist
    op.execute("DROP TABLE IF EXISTS analysis_queue_items CASCADE")
    op.execute("DROP TABLE IF EXISTS analysis_queues CASCADE")

    # Drop enums if they exist (only if not used by other tables)
    op.execute("DROP TYPE IF EXISTS itemstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS queuestatus CASCADE")
