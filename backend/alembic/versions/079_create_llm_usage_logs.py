"""Create LLM usage tracking tables

Revision ID: 079_create_llm_usage_logs
Revises: 078_add_updated_at_to_name_variants
Create Date: 2025-10-01 22:05:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "079_create_llm_usage_logs"
down_revision = "078_add_updated_at_to_name_variants"
branch_labels = None
depends_on = None


def table_exists(table_name: str, schema: str = "migration") -> bool:
    """Check if table exists."""
    bind = op.get_bind()
    try:
        stmt = sa.text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema
                  AND table_name = :table_name
            )
        """
        )
        result = bind.execute(
            stmt, {"schema": schema, "table_name": table_name}
        ).scalar()
        return bool(result)
    except Exception:
        return False


def upgrade() -> None:
    """Create LLM usage tracking tables."""

    # Create llm_usage_logs table if it doesn't exist
    if not table_exists("llm_usage_logs"):
        op.create_table(
            "llm_usage_logs",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("client_account_id", sa.UUID(), nullable=True),
            sa.Column("engagement_id", sa.UUID(), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("username", sa.String(length=255), nullable=True),
            sa.Column("flow_id", sa.String(length=255), nullable=True),
            sa.Column("request_id", sa.String(length=255), nullable=True),
            sa.Column("endpoint", sa.String(length=500), nullable=True),
            sa.Column("page_context", sa.String(length=255), nullable=True),
            sa.Column("feature_context", sa.String(length=255), nullable=True),
            sa.Column("llm_provider", sa.String(length=100), nullable=False),
            sa.Column("model_name", sa.String(length=255), nullable=False),
            sa.Column("model_version", sa.String(length=100), nullable=True),
            sa.Column("input_tokens", sa.Integer(), nullable=True),
            sa.Column("output_tokens", sa.Integer(), nullable=True),
            sa.Column("total_tokens", sa.Integer(), nullable=True),
            sa.Column("input_cost", sa.Numeric(precision=10, scale=6), nullable=True),
            sa.Column("output_cost", sa.Numeric(precision=10, scale=6), nullable=True),
            sa.Column("total_cost", sa.Numeric(precision=10, scale=6), nullable=True),
            sa.Column("cost_currency", sa.String(length=10), nullable=False),
            sa.Column("response_time_ms", sa.Integer(), nullable=True),
            sa.Column("success", sa.Boolean(), nullable=False),
            sa.Column("error_type", sa.String(length=255), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column(
                "request_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
            ),
            sa.Column(
                "response_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
            ),
            sa.Column(
                "additional_metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.ForeignKeyConstraint(
                ["client_account_id"],
                ["migration.client_accounts.id"],
            ),
            sa.ForeignKeyConstraint(
                ["engagement_id"],
                ["migration.engagements.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            schema="migration",
        )

        # Create indexes for llm_usage_logs
        op.create_index(
            "idx_llm_usage_client_account",
            "llm_usage_logs",
            ["client_account_id"],
            unique=False,
            schema="migration",
        )
        op.create_index(
            "idx_llm_usage_cost_analysis",
            "llm_usage_logs",
            ["client_account_id", "llm_provider", "model_name", "created_at"],
            unique=False,
            schema="migration",
        )
        op.create_index(
            "idx_llm_usage_created_at",
            "llm_usage_logs",
            ["created_at"],
            unique=False,
            schema="migration",
        )
        op.create_index(
            "idx_llm_usage_engagement",
            "llm_usage_logs",
            ["engagement_id"],
            unique=False,
            schema="migration",
        )
        op.create_index(
            "idx_llm_usage_feature_context",
            "llm_usage_logs",
            ["feature_context"],
            unique=False,
            schema="migration",
        )
        op.create_index(
            "idx_llm_usage_page_context",
            "llm_usage_logs",
            ["page_context"],
            unique=False,
            schema="migration",
        )
        op.create_index(
            "idx_llm_usage_provider_model",
            "llm_usage_logs",
            ["llm_provider", "model_name"],
            unique=False,
            schema="migration",
        )
        op.create_index(
            "idx_llm_usage_reporting",
            "llm_usage_logs",
            ["client_account_id", "created_at", "success"],
            unique=False,
            schema="migration",
        )
        op.create_index(
            "idx_llm_usage_success",
            "llm_usage_logs",
            ["success"],
            unique=False,
            schema="migration",
        )
        op.create_index(
            "idx_llm_usage_user",
            "llm_usage_logs",
            ["user_id"],
            unique=False,
            schema="migration",
        )

    # Create llm_usage_summary table if it doesn't exist
    if not table_exists("llm_usage_summary"):
        op.create_table(
            "llm_usage_summary",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("period_type", sa.String(length=20), nullable=False),
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("client_account_id", sa.UUID(), nullable=True),
            sa.Column("engagement_id", sa.UUID(), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("llm_provider", sa.String(length=100), nullable=True),
            sa.Column("model_name", sa.String(length=255), nullable=True),
            sa.Column("page_context", sa.String(length=255), nullable=True),
            sa.Column("feature_context", sa.String(length=255), nullable=True),
            sa.Column("total_requests", sa.Integer(), nullable=False),
            sa.Column("successful_requests", sa.Integer(), nullable=False),
            sa.Column("failed_requests", sa.Integer(), nullable=False),
            sa.Column("total_input_tokens", sa.BigInteger(), nullable=False),
            sa.Column("total_output_tokens", sa.BigInteger(), nullable=False),
            sa.Column("total_tokens", sa.BigInteger(), nullable=False),
            sa.Column("total_cost", sa.Numeric(precision=12, scale=6), nullable=False),
            sa.Column("avg_response_time_ms", sa.Integer(), nullable=True),
            sa.Column("min_response_time_ms", sa.Integer(), nullable=True),
            sa.Column("max_response_time_ms", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(
                ["client_account_id"],
                ["migration.client_accounts.id"],
            ),
            sa.ForeignKeyConstraint(
                ["engagement_id"],
                ["migration.engagements.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "period_type",
                "period_start",
                "client_account_id",
                "engagement_id",
                "user_id",
                "llm_provider",
                "model_name",
                "page_context",
                "feature_context",
                name="uq_usage_summary_period_context",
            ),
            schema="migration",
        )

        # Create indexes for llm_usage_summary
        op.create_index(
            "idx_usage_summary_client",
            "llm_usage_summary",
            ["client_account_id", "period_start"],
            unique=False,
            schema="migration",
        )
        op.create_index(
            "idx_usage_summary_model",
            "llm_usage_summary",
            ["llm_provider", "model_name", "period_start"],
            unique=False,
            schema="migration",
        )
        op.create_index(
            "idx_usage_summary_period",
            "llm_usage_summary",
            ["period_type", "period_start", "period_end"],
            unique=False,
            schema="migration",
        )

    # Create llm_model_pricing table if it doesn't exist
    if not table_exists("llm_model_pricing"):
        op.create_table(
            "llm_model_pricing",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("provider", sa.String(length=100), nullable=False),
            sa.Column("model_name", sa.String(length=255), nullable=False),
            sa.Column("model_version", sa.String(length=100), nullable=True),
            sa.Column(
                "input_cost_per_1k_tokens",
                sa.Numeric(precision=10, scale=6),
                nullable=False,
            ),
            sa.Column(
                "output_cost_per_1k_tokens",
                sa.Numeric(precision=10, scale=6),
                nullable=False,
            ),
            sa.Column("currency", sa.String(length=10), nullable=False),
            sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
            sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("source", sa.String(length=255), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "provider",
                "model_name",
                "model_version",
                "effective_from",
                name="uq_model_pricing_version_date",
            ),
            schema="migration",
        )

        # Create indexes for llm_model_pricing
        op.create_index(
            "idx_model_pricing_provider_model",
            "llm_model_pricing",
            ["provider", "model_name"],
            unique=False,
            schema="migration",
        )
        op.create_index(
            "idx_model_pricing_active",
            "llm_model_pricing",
            ["is_active", "effective_from", "effective_to"],
            unique=False,
            schema="migration",
        )


def downgrade() -> None:
    """Drop LLM usage tracking tables."""

    # Drop llm_model_pricing table if it exists
    if table_exists("llm_model_pricing"):
        op.drop_index(
            "idx_model_pricing_active",
            table_name="llm_model_pricing",
            schema="migration",
        )
        op.drop_index(
            "idx_model_pricing_provider_model",
            table_name="llm_model_pricing",
            schema="migration",
        )
        op.drop_table("llm_model_pricing", schema="migration")

    # Drop llm_usage_summary table if it exists
    if table_exists("llm_usage_summary"):
        op.drop_index(
            "idx_usage_summary_period",
            table_name="llm_usage_summary",
            schema="migration",
        )
        op.drop_index(
            "idx_usage_summary_model",
            table_name="llm_usage_summary",
            schema="migration",
        )
        op.drop_index(
            "idx_usage_summary_client",
            table_name="llm_usage_summary",
            schema="migration",
        )
        op.drop_table("llm_usage_summary", schema="migration")

    # Drop llm_usage_logs table if it exists
    if table_exists("llm_usage_logs"):
        op.drop_index(
            "idx_llm_usage_user", table_name="llm_usage_logs", schema="migration"
        )
        op.drop_index(
            "idx_llm_usage_success", table_name="llm_usage_logs", schema="migration"
        )
        op.drop_index(
            "idx_llm_usage_reporting", table_name="llm_usage_logs", schema="migration"
        )
        op.drop_index(
            "idx_llm_usage_provider_model",
            table_name="llm_usage_logs",
            schema="migration",
        )
        op.drop_index(
            "idx_llm_usage_page_context",
            table_name="llm_usage_logs",
            schema="migration",
        )
        op.drop_index(
            "idx_llm_usage_feature_context",
            table_name="llm_usage_logs",
            schema="migration",
        )
        op.drop_index(
            "idx_llm_usage_engagement", table_name="llm_usage_logs", schema="migration"
        )
        op.drop_index(
            "idx_llm_usage_created_at", table_name="llm_usage_logs", schema="migration"
        )
        op.drop_index(
            "idx_llm_usage_cost_analysis",
            table_name="llm_usage_logs",
            schema="migration",
        )
        op.drop_index(
            "idx_llm_usage_client_account",
            table_name="llm_usage_logs",
            schema="migration",
        )
        op.drop_table("llm_usage_logs", schema="migration")
