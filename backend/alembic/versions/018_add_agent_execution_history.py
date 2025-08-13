"""Add agent execution history table

Revision ID: 018_add_agent_execution_history
Revises: 017_add_vector_search_to_agent_patterns
Create Date: 2025-01-12 15:55:00.000000

CC: Create table for tracking agent execution history for observability
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "018_add_agent_execution_history"
down_revision: Union[str, None] = "017_add_vector_search_to_agent_patterns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create agent_execution_history table"""

    # Check if table already exists
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'agent_execution_history'
            )
        """
        )
    )
    table_exists = result.scalar()

    if not table_exists:
        op.create_table(
            "agent_execution_history",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "client_account_id", postgresql.UUID(as_uuid=True), nullable=False
            ),
            sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("flow_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("agent_name", sa.String(length=255), nullable=False),
            sa.Column("agent_type", sa.String(length=100), nullable=True),
            sa.Column("agent_phase", sa.String(length=100), nullable=True),
            sa.Column("task_id", sa.String(length=255), nullable=True),
            sa.Column("task_name", sa.String(length=255), nullable=True),
            sa.Column("task_type", sa.String(length=100), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("start_time", sa.DateTime(), nullable=True),
            sa.Column("end_time", sa.DateTime(), nullable=True),
            sa.Column("duration_seconds", sa.Float(), nullable=True),
            sa.Column("memory_usage_mb", sa.Float(), nullable=True),
            sa.Column("cpu_usage_percent", sa.Float(), nullable=True),
            sa.Column("llm_calls_count", sa.Integer(), nullable=True),
            sa.Column("confidence_score", sa.Float(), nullable=True),
            sa.Column("result", sa.JSON(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("error_details", sa.JSON(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
            schema="migration",
        )

        # Create indexes for performance
        op.create_index(
            "ix_agent_execution_history_client_account_id",
            "agent_execution_history",
            ["client_account_id"],
            schema="migration",
        )
        op.create_index(
            "ix_agent_execution_history_engagement_id",
            "agent_execution_history",
            ["engagement_id"],
            schema="migration",
        )
        op.create_index(
            "ix_agent_execution_history_agent_name",
            "agent_execution_history",
            ["agent_name"],
            schema="migration",
        )
        op.create_index(
            "ix_agent_execution_history_task_id",
            "agent_execution_history",
            ["task_id"],
            schema="migration",
        )
        op.create_index(
            "ix_agent_execution_history_created_at",
            "agent_execution_history",
            ["created_at"],
            schema="migration",
        )

        # Create composite index for common queries
        op.create_index(
            "ix_agent_execution_history_composite",
            "agent_execution_history",
            ["client_account_id", "engagement_id", "agent_name", "created_at"],
            schema="migration",
        )


def downgrade() -> None:
    """Drop agent_execution_history table"""

    # Drop indexes first
    op.drop_index(
        "ix_agent_execution_history_composite",
        table_name="agent_execution_history",
        schema="migration",
    )
    op.drop_index(
        "ix_agent_execution_history_created_at",
        table_name="agent_execution_history",
        schema="migration",
    )
    op.drop_index(
        "ix_agent_execution_history_task_id",
        table_name="agent_execution_history",
        schema="migration",
    )
    op.drop_index(
        "ix_agent_execution_history_agent_name",
        table_name="agent_execution_history",
        schema="migration",
    )
    op.drop_index(
        "ix_agent_execution_history_engagement_id",
        table_name="agent_execution_history",
        schema="migration",
    )
    op.drop_index(
        "ix_agent_execution_history_client_account_id",
        table_name="agent_execution_history",
        schema="migration",
    )

    # Drop table
    op.drop_table("agent_execution_history", schema="migration")
