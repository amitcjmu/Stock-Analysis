"""Fix agent task history foreign keys

Revision ID: 013_fix_agent_task_history_foreign_keys
Revises: 012_agent_observability_enhancement
Create Date: 2025-01-21 04:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "013_fix_agent_task_history_foreign_keys"
down_revision = "012_agent_observability_enhancement"
branch_labels = None
depends_on = None


def constraint_exists(constraint_name, table_name):
    """Check if a constraint exists"""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_schema = 'migration'
                AND constraint_schema = 'migration'
                AND table_name = :table_name
                AND constraint_name = :constraint_name
            )
        """).bindparams(table_name=table_name, constraint_name=constraint_name)
    ).scalar()
    return result


def upgrade():
    """Add foreign key constraints to agent_task_history table"""
    # Add foreign key constraints only if they don't exist
    if not constraint_exists("fk_agent_task_history_client_account_id", "agent_task_history"):
        op.create_foreign_key(
            "fk_agent_task_history_client_account_id",
            "agent_task_history",
            "client_accounts",
            ["client_account_id"],
            ["id"],
            ondelete="CASCADE",
        )

    if not constraint_exists("fk_agent_task_history_engagement_id", "agent_task_history"):
        op.create_foreign_key(
            "fk_agent_task_history_engagement_id",
            "agent_task_history",
            "engagements",
            ["engagement_id"],
            ["id"],
            ondelete="CASCADE",
        )

    if not constraint_exists("fk_agent_task_history_flow_id", "agent_task_history"):
        op.create_foreign_key(
            "fk_agent_task_history_flow_id",
            "agent_task_history",
            "crewai_flow_state_extensions",
            ["flow_id"],
            ["flow_id"],
            ondelete="CASCADE",
        )


def downgrade():
    """Remove foreign key constraints from agent_task_history table"""
    op.drop_constraint(
        "fk_agent_task_history_flow_id", "agent_task_history", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_agent_task_history_engagement_id", "agent_task_history", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_agent_task_history_client_account_id",
        "agent_task_history",
        type_="foreignkey",
    )
