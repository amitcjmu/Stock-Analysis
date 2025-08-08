"""Add analysis queue tables

Revision ID: 2ae8940123e6
Revises: fcacece8fa7b
Create Date: 2025-08-01 02:06:02.041970

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2ae8940123e6"
down_revision = "fcacece8fa7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types if they don't exist
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE queuestatus AS ENUM ('pending', 'processing', 'paused', 'completed', 'cancelled', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )

    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE itemstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )

    # Create analysis_queues table (skip if exists)
    try:
        op.create_table(
            "analysis_queues",
            sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("client_id", sa.UUID(as_uuid=True), nullable=False),
            sa.Column("engagement_id", sa.UUID(as_uuid=True), nullable=False),
            sa.Column("created_by", sa.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    except Exception as e:
        print(f"Table analysis_queues may already exist: {e}")

    # Create index on client_id and engagement_id for faster queries
    try:
        op.create_index(
            "idx_analysis_queues_context",
            "analysis_queues",
            ["client_id", "engagement_id"],
        )
    except Exception as e:
        print(f"Index idx_analysis_queues_context may already exist: {e}")

    # Create analysis_queue_items table (skip if exists)
    try:
        op.create_table(
            "analysis_queue_items",
            sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
            sa.Column("queue_id", sa.UUID(as_uuid=True), nullable=False),
            sa.Column("application_id", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["queue_id"], ["analysis_queues.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
    except Exception as e:
        print(f"Table analysis_queue_items may already exist: {e}")

    # Create index on queue_id for faster queries
    try:
        op.create_index(
            "idx_queue_items_queue_id", "analysis_queue_items", ["queue_id"]
        )
    except Exception as e:
        print(f"Index idx_queue_items_queue_id may already exist: {e}")

    # Alter columns to use enum types (after tables are created)
    try:
        op.execute("ALTER TABLE analysis_queues ALTER COLUMN status TYPE queuestatus USING status::queuestatus")
    except Exception as e:
        print(f"Status column may already be queuestatus type: {e}")
    
    try:
        op.execute("ALTER TABLE analysis_queue_items ALTER COLUMN status TYPE itemstatus USING status::itemstatus")
    except Exception as e:
        print(f"Status column may already be itemstatus type: {e}")


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
