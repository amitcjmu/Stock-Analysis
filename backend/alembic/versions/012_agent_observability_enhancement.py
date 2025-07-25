"""Agent observability enhancement - add tracking tables for agent performance

Revision ID: 012_agent_observability_enhancement
Revises: 011_add_updated_at_to_collection_data_gaps
Create Date: 2025-07-21 08:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "012_agent_observability_enhancement"
down_revision = "011_add_updated_at_to_collection_data_gaps"
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if a table exists in the database"""
    bind = op.get_bind()
    try:
        # Use parameterized query with proper escaping
        # Note: table_name is a string literal value, not an identifier
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'migration'
                    AND table_name = :table_name
                )
            """
            ).bindparams(table_name=table_name)
        ).scalar()
        return result
    except Exception as e:
        print(f"Error checking if table {table_name} exists: {e}")
        # If we get an error, assume table exists to avoid trying to create it
        return True


def create_table_if_not_exists(table_name, *columns, **kwargs):
    """Create a table only if it doesn't already exist"""
    if not table_exists(table_name):
        op.create_table(table_name, *columns, **kwargs)
    else:
        print(f"Table {table_name} already exists, skipping creation")


def index_exists(index_name, table_name):
    """Check if an index exists in the database"""
    bind = op.get_bind()
    try:
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE schemaname = 'migration'
                    AND tablename = :table_name
                    AND indexname = :index_name
                )
            """
            ).bindparams(table_name=table_name, index_name=index_name)
        ).scalar()
        return result
    except Exception as e:
        print(f"Error checking if index {index_name} exists: {e}")
        # If we get an error, assume index exists to avoid trying to create it
        return True


def create_index_if_not_exists(index_name, table_name, columns, **kwargs):
    """Create an index only if it doesn't already exist"""
    if not index_exists(index_name, table_name):
        op.create_index(index_name, table_name, columns, **kwargs)
    else:
        print(f"Index {index_name} on {table_name} already exists, skipping creation")


def upgrade():
    """Create agent observability tables for enhanced monitoring and performance tracking"""

    # Create agent_task_history table for detailed task tracking
    create_table_if_not_exists(
        "agent_task_history",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            comment="Unique identifier for the agent task history record",
        ),
        sa.Column(
            "flow_id",
            sa.UUID(),
            nullable=False,
            comment="Reference to the CrewAI flow this task belongs to",
        ),
        sa.Column(
            "agent_name",
            sa.VARCHAR(length=100),
            nullable=False,
            comment="Name of the agent that executed the task",
        ),
        sa.Column(
            "agent_type",
            sa.VARCHAR(length=50),
            nullable=False,
            comment="Type of agent: individual or crew_member",
        ),
        sa.Column(
            "task_id",
            sa.VARCHAR(length=255),
            nullable=False,
            comment="Unique identifier for the task within the flow",
        ),
        sa.Column(
            "task_name",
            sa.VARCHAR(length=255),
            nullable=False,
            comment="Human-readable name of the task",
        ),
        sa.Column(
            "task_description",
            sa.TEXT(),
            nullable=True,
            comment="Detailed description of what the task accomplished",
        ),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            comment="When the task execution started",
        ),
        sa.Column(
            "completed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="When the task execution completed (null if still running)",
        ),
        sa.Column(
            "status",
            sa.VARCHAR(length=50),
            nullable=False,
            comment="Current status of the task execution",
        ),
        sa.Column(
            "duration_seconds",
            sa.DECIMAL(precision=10, scale=3),
            nullable=True,
            comment="Total execution time in seconds",
        ),
        sa.Column(
            "success",
            sa.BOOLEAN(),
            nullable=True,
            comment="Whether the task completed successfully",
        ),
        sa.Column(
            "result_preview",
            sa.TEXT(),
            nullable=True,
            comment="Preview of the task result (truncated for large outputs)",
        ),
        sa.Column(
            "error_message",
            sa.TEXT(),
            nullable=True,
            comment="Error message if the task failed",
        ),
        sa.Column(
            "llm_calls_count",
            sa.INTEGER(),
            nullable=False,
            server_default="0",
            comment="Number of LLM API calls made during task execution",
        ),
        sa.Column(
            "thinking_phases_count",
            sa.INTEGER(),
            nullable=False,
            server_default="0",
            comment="Number of thinking/reasoning phases during execution",
        ),
        sa.Column(
            "token_usage",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Detailed token usage: {input_tokens, output_tokens, total_tokens}",
        ),
        sa.Column(
            "memory_usage_mb",
            sa.DECIMAL(precision=8, scale=2),
            nullable=True,
            comment="Peak memory usage during task execution in MB",
        ),
        sa.Column(
            "confidence_score",
            sa.DECIMAL(precision=3, scale=2),
            nullable=True,
            comment="Agent confidence score for the task result (0-1)",
        ),
        sa.Column(
            "client_account_id",
            sa.UUID(),
            nullable=False,
            comment="Client account this task belongs to",
        ),
        sa.Column(
            "engagement_id",
            sa.UUID(),
            nullable=False,
            comment="Engagement this task is part of",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="When this record was created",
        ),
        # Primary key
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_task_history")),
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ["flow_id"],
            ["crewai_flow_state_extensions.flow_id"],
            name=op.f("fk_agent_task_history_flow_id_crewai_flow_state_extensions"),
        ),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_agent_task_history_client_account_id_client_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
            name=op.f("fk_agent_task_history_engagement_id_engagements"),
        ),
        # Check constraints
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="chk_agent_task_history_confidence_score",
        ),
        sa.CheckConstraint(
            "duration_seconds >= 0", name="chk_agent_task_history_duration_seconds"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'starting', 'running', 'thinking', 'waiting_llm', "
            "'processing_response', 'completed', 'failed', 'timeout')",
            name="chk_agent_task_history_status",
        ),
        sa.CheckConstraint(
            "agent_type IN ('individual', 'crew_member')",
            name="chk_agent_task_history_agent_type",
        ),
    )

    # Create indexes for agent_task_history
    create_index_if_not_exists(
        op.f("ix_agent_task_history_agent_name"),
        "agent_task_history",
        ["agent_name", sa.text("created_at DESC")],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_agent_task_history_flow_id"),
        "agent_task_history",
        ["flow_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_agent_task_history_status"),
        "agent_task_history",
        ["status", sa.text("created_at DESC")],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_agent_task_history_client"),
        "agent_task_history",
        ["client_account_id", "engagement_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_agent_task_history_task_id"),
        "agent_task_history",
        ["task_id"],
        unique=False,
    )

    # Create agent_performance_daily table for aggregated metrics
    create_table_if_not_exists(
        "agent_performance_daily",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            comment="Unique identifier for the daily performance record",
        ),
        sa.Column(
            "agent_name",
            sa.VARCHAR(length=100),
            nullable=False,
            comment="Name of the agent",
        ),
        sa.Column(
            "date_recorded",
            sa.DATE(),
            nullable=False,
            comment="Date for which metrics are aggregated",
        ),
        sa.Column(
            "tasks_attempted",
            sa.INTEGER(),
            nullable=False,
            server_default="0",
            comment="Total number of tasks attempted",
        ),
        sa.Column(
            "tasks_completed",
            sa.INTEGER(),
            nullable=False,
            server_default="0",
            comment="Number of successfully completed tasks",
        ),
        sa.Column(
            "tasks_failed",
            sa.INTEGER(),
            nullable=False,
            server_default="0",
            comment="Number of failed tasks",
        ),
        sa.Column(
            "avg_duration_seconds",
            sa.DECIMAL(precision=10, scale=3),
            nullable=True,
            comment="Average task duration in seconds",
        ),
        sa.Column(
            "avg_confidence_score",
            sa.DECIMAL(precision=3, scale=2),
            nullable=True,
            comment="Average confidence score across all tasks",
        ),
        sa.Column(
            "total_llm_calls",
            sa.INTEGER(),
            nullable=False,
            server_default="0",
            comment="Total LLM API calls made",
        ),
        sa.Column(
            "total_tokens_used",
            sa.INTEGER(),
            nullable=False,
            server_default="0",
            comment="Total tokens consumed",
        ),
        sa.Column(
            "success_rate",
            sa.DECIMAL(precision=5, scale=2),
            nullable=True,
            comment="Success rate percentage (0-100)",
        ),
        sa.Column(
            "client_account_id",
            sa.UUID(),
            nullable=False,
            comment="Client account these metrics belong to",
        ),
        sa.Column(
            "engagement_id",
            sa.UUID(),
            nullable=False,
            comment="Engagement these metrics are part of",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="When this record was created",
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="When this record was last updated",
        ),
        # Primary key
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_performance_daily")),
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_agent_performance_daily_client_account_id_client_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
            name=op.f("fk_agent_performance_daily_engagement_id_engagements"),
        ),
        # Unique constraint to prevent duplicate daily records
        sa.UniqueConstraint(
            "agent_name",
            "date_recorded",
            "client_account_id",
            "engagement_id",
            name="uq_agent_performance_daily_agent_date_client_engagement",
        ),
        # Check constraint
        sa.CheckConstraint(
            "success_rate >= 0 AND success_rate <= 100",
            name="chk_agent_performance_daily_success_rate",
        ),
    )

    # Create indexes for agent_performance_daily
    create_index_if_not_exists(
        op.f("ix_agent_performance_daily_agent"),
        "agent_performance_daily",
        ["agent_name", sa.text("date_recorded DESC")],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_agent_performance_daily_client"),
        "agent_performance_daily",
        ["client_account_id", "engagement_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_agent_performance_daily_date"),
        "agent_performance_daily",
        ["date_recorded"],
        unique=False,
    )

    # Create agent_discovered_patterns table (new table as it doesn't exist)
    create_table_if_not_exists(
        "agent_discovered_patterns",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            comment="Unique identifier for the discovered pattern",
        ),
        sa.Column(
            "pattern_id",
            sa.VARCHAR(length=255),
            nullable=False,
            comment="Unique identifier for the pattern",
        ),
        sa.Column(
            "pattern_type",
            sa.VARCHAR(length=100),
            nullable=False,
            comment="Type of pattern discovered",
        ),
        sa.Column(
            "pattern_name",
            sa.VARCHAR(length=255),
            nullable=False,
            comment="Human-readable name of the pattern",
        ),
        sa.Column(
            "pattern_description",
            sa.TEXT(),
            nullable=True,
            comment="Detailed description of the pattern",
        ),
        sa.Column(
            "discovered_by_agent",
            sa.VARCHAR(length=100),
            nullable=False,
            comment="Agent that discovered this pattern",
        ),
        sa.Column(
            "confidence_score",
            sa.DECIMAL(precision=3, scale=2),
            nullable=False,
            comment="Confidence score of the pattern (0-1)",
        ),
        sa.Column(
            "evidence_count",
            sa.INTEGER(),
            nullable=False,
            server_default="1",
            comment="Number of instances supporting this pattern",
        ),
        sa.Column(
            "times_referenced",
            sa.INTEGER(),
            nullable=False,
            server_default="0",
            comment="Number of times this pattern has been referenced",
        ),
        sa.Column(
            "pattern_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Detailed pattern data and parameters",
        ),
        sa.Column(
            "task_id",
            sa.VARCHAR(length=255),
            nullable=True,
            comment="Task ID where pattern was discovered",
        ),
        sa.Column(
            "execution_context",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Context in which pattern was discovered",
        ),
        sa.Column(
            "user_feedback_given",
            sa.BOOLEAN(),
            nullable=False,
            server_default="false",
            comment="Whether user has provided feedback on this pattern",
        ),
        sa.Column(
            "pattern_effectiveness_score",
            sa.DECIMAL(precision=3, scale=2),
            nullable=True,
            comment="Effectiveness score based on usage and feedback (0-1)",
        ),
        sa.Column(
            "last_used_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="Last time this pattern was used",
        ),
        sa.Column(
            "client_account_id",
            sa.UUID(),
            nullable=False,
            comment="Client account this pattern belongs to",
        ),
        sa.Column(
            "engagement_id",
            sa.UUID(),
            nullable=False,
            comment="Engagement this pattern is part of",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="When this pattern was discovered",
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="When this record was last updated",
        ),
        # Primary key
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_discovered_patterns")),
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_agent_discovered_patterns_client_account_id_client_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
            name=op.f("fk_agent_discovered_patterns_engagement_id_engagements"),
        ),
        # Unique constraint to prevent duplicate patterns
        sa.UniqueConstraint(
            "pattern_id",
            "client_account_id",
            "engagement_id",
            name="uq_agent_discovered_patterns_pattern_client_engagement",
        ),
        # Check constraints
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="chk_agent_discovered_patterns_confidence_score",
        ),
        sa.CheckConstraint(
            "pattern_effectiveness_score >= 0 AND pattern_effectiveness_score <= 1",
            name="chk_agent_discovered_patterns_effectiveness_score",
        ),
    )

    # Create indexes for agent_discovered_patterns
    create_index_if_not_exists(
        op.f("ix_agent_discovered_patterns_agent"),
        "agent_discovered_patterns",
        ["discovered_by_agent"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_agent_discovered_patterns_pattern_id"),
        "agent_discovered_patterns",
        ["pattern_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_agent_discovered_patterns_pattern_type"),
        "agent_discovered_patterns",
        ["pattern_type"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_agent_discovered_patterns_client"),
        "agent_discovered_patterns",
        ["client_account_id", "engagement_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_agent_discovered_patterns_confidence"),
        "agent_discovered_patterns",
        [sa.text("confidence_score DESC")],
        unique=False,
    )

    # Create trigger function for updating updated_at timestamps
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_agent_observability_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """
    )

    # Create triggers for updated_at on agent_performance_daily
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.triggers
                WHERE trigger_schema = 'migration'
                AND event_object_schema = 'migration'
                AND event_object_table = 'agent_performance_daily'
                AND trigger_name = 'update_agent_performance_daily_updated_at'
            ) THEN
                CREATE TRIGGER update_agent_performance_daily_updated_at
                BEFORE UPDATE ON agent_performance_daily
                FOR EACH ROW
                EXECUTE FUNCTION update_agent_observability_updated_at();
            END IF;
        END $$;
    """
    )

    # Create triggers for updated_at on agent_discovered_patterns
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.triggers
                WHERE trigger_schema = 'migration'
                AND event_object_schema = 'migration'
                AND event_object_table = 'agent_discovered_patterns'
                AND trigger_name = 'update_agent_discovered_patterns_updated_at'
            ) THEN
                CREATE TRIGGER update_agent_discovered_patterns_updated_at
                BEFORE UPDATE ON agent_discovered_patterns
                FOR EACH ROW
                EXECUTE FUNCTION update_agent_observability_updated_at();
            END IF;
        END $$;
    """
    )

    # Add comment to tables
    op.execute(
        "COMMENT ON TABLE agent_task_history IS "
        "'Detailed history of all agent task executions for performance tracking and analysis';"
    )
    op.execute(
        "COMMENT ON TABLE agent_performance_daily IS 'Daily aggregated performance metrics for each agent';"
    )
    op.execute(
        "COMMENT ON TABLE agent_discovered_patterns IS "
        "'Patterns discovered by agents during task execution for learning and optimization';"
    )


def downgrade():
    """Remove agent observability tables"""

    # Drop triggers first
    op.execute(
        "DROP TRIGGER IF EXISTS update_agent_discovered_patterns_updated_at ON agent_discovered_patterns;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS update_agent_performance_daily_updated_at ON agent_performance_daily;"
    )

    # Drop the trigger function
    op.execute("DROP FUNCTION IF EXISTS update_agent_observability_updated_at();")

    # Drop indexes for agent_discovered_patterns
    op.drop_index(
        op.f("ix_agent_discovered_patterns_confidence"),
        table_name="agent_discovered_patterns",
    )
    op.drop_index(
        op.f("ix_agent_discovered_patterns_client"),
        table_name="agent_discovered_patterns",
    )
    op.drop_index(
        op.f("ix_agent_discovered_patterns_pattern_type"),
        table_name="agent_discovered_patterns",
    )
    op.drop_index(
        op.f("ix_agent_discovered_patterns_pattern_id"),
        table_name="agent_discovered_patterns",
    )
    op.drop_index(
        op.f("ix_agent_discovered_patterns_agent"),
        table_name="agent_discovered_patterns",
    )

    # Drop agent_discovered_patterns table
    op.drop_table("agent_discovered_patterns")

    # Drop indexes for agent_performance_daily
    op.drop_index(
        op.f("ix_agent_performance_daily_date"), table_name="agent_performance_daily"
    )
    op.drop_index(
        op.f("ix_agent_performance_daily_client"), table_name="agent_performance_daily"
    )
    op.drop_index(
        op.f("ix_agent_performance_daily_agent"), table_name="agent_performance_daily"
    )

    # Drop agent_performance_daily table
    op.drop_table("agent_performance_daily")

    # Drop indexes for agent_task_history
    op.drop_index(
        op.f("ix_agent_task_history_task_id"), table_name="agent_task_history"
    )
    op.drop_index(op.f("ix_agent_task_history_client"), table_name="agent_task_history")
    op.drop_index(op.f("ix_agent_task_history_status"), table_name="agent_task_history")
    op.drop_index(
        op.f("ix_agent_task_history_flow_id"), table_name="agent_task_history"
    )
    op.drop_index(
        op.f("ix_agent_task_history_agent_name"), table_name="agent_task_history"
    )

    # Drop agent_task_history table
    op.drop_table("agent_task_history")
