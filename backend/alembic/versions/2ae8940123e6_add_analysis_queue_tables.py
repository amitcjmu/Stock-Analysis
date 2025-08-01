"""Add analysis queue tables

Revision ID: 2ae8940123e6
Revises: fcacece8fa7b
Create Date: 2025-08-01 02:06:02.041970

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2ae8940123e6"
down_revision = "fcacece8fa7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create analysis_queues table
    op.create_table(
        "analysis_queues",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "processing",
                "paused",
                "completed",
                "cancelled",
                "failed",
                name="queuestatus",
            ),
            nullable=False,
        ),
        sa.Column("client_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index on client_id and engagement_id for faster queries
    op.create_index(
        "idx_analysis_queues_context", "analysis_queues", ["client_id", "engagement_id"]
    )

    # Create analysis_queue_items table
    op.create_table(
        "analysis_queue_items",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("queue_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "processing",
                "completed",
                "failed",
                "cancelled",
                name="itemstatus",
            ),
            nullable=False,
        ),
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

    # Create index on queue_id for faster queries
    op.create_index("idx_queue_items_queue_id", "analysis_queue_items", ["queue_id"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_queue_items_queue_id", table_name="analysis_queue_items")
    op.drop_index("idx_analysis_queues_context", table_name="analysis_queues")

    # Drop tables
    op.drop_table("analysis_queue_items")
    op.drop_table("analysis_queues")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS itemstatus")
    op.execute("DROP TYPE IF EXISTS queuestatus")
