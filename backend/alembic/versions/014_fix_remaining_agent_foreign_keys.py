"""Fix remaining agent table foreign keys

Revision ID: 014_fix_remaining_agent_foreign_keys
Revises: 013_fix_agent_task_history_foreign_keys
Create Date: 2025-01-21 04:26:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "014_fix_remaining_agent_foreign_keys"
down_revision = "013_fix_agent_task_history_foreign_keys"
branch_labels = None
depends_on = None


def constraint_exists(constraint_name, table_name):
    """Check if a constraint exists"""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_schema = 'migration'
                AND constraint_schema = 'migration'
                AND table_name = :table_name
                AND constraint_name = :constraint_name
            )
        """
        ).bindparams(table_name=table_name, constraint_name=constraint_name)
    ).scalar()
    return result


def upgrade():
    """Add foreign key constraints to agent_performance_daily and agent_discovered_patterns tables"""

    # Add foreign key constraints for agent_performance_daily
    if not constraint_exists(
        "fk_agent_performance_daily_client_account_id", "agent_performance_daily"
    ):
        op.create_foreign_key(
            "fk_agent_performance_daily_client_account_id",
            "agent_performance_daily",
            "client_accounts",
            ["client_account_id"],
            ["id"],
            ondelete="CASCADE",
        )

    if not constraint_exists(
        "fk_agent_performance_daily_engagement_id", "agent_performance_daily"
    ):
        op.create_foreign_key(
            "fk_agent_performance_daily_engagement_id",
            "agent_performance_daily",
            "engagements",
            ["engagement_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # Add foreign key constraints for agent_discovered_patterns
    if not constraint_exists(
        "fk_agent_discovered_patterns_client_account_id", "agent_discovered_patterns"
    ):
        op.create_foreign_key(
            "fk_agent_discovered_patterns_client_account_id",
            "agent_discovered_patterns",
            "client_accounts",
            ["client_account_id"],
            ["id"],
            ondelete="CASCADE",
        )

    if not constraint_exists(
        "fk_agent_discovered_patterns_engagement_id", "agent_discovered_patterns"
    ):
        op.create_foreign_key(
            "fk_agent_discovered_patterns_engagement_id",
            "agent_discovered_patterns",
            "engagements",
            ["engagement_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade():
    """Remove foreign key constraints from agent tables"""
    op.drop_constraint(
        "fk_agent_discovered_patterns_engagement_id",
        "agent_discovered_patterns",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_agent_discovered_patterns_client_account_id",
        "agent_discovered_patterns",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_agent_performance_daily_engagement_id",
        "agent_performance_daily",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_agent_performance_daily_client_account_id",
        "agent_performance_daily",
        type_="foreignkey",
    )
