"""
Add indexes for readiness/status fields and failure journal table

Revision ID: 027_add_indexes_and_failure_journal
Revises: 026_add_assessment_readiness_fields_to_assets
Create Date: 2025-08-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "027_add_indexes_and_failure_journal"
down_revision = "026_add_assessment_readiness_fields_to_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = op.get_context().version_table_schema or "migration"

    # Indexes to accelerate readiness queries
    op.create_index(
        "ix_assets_client_engagement_readiness",
        "assets",
        ["client_account_id", "engagement_id", "assessment_readiness"],
        unique=False,
        schema=schema,
    )
    op.create_index(
        "ix_assets_discovery_status",
        "assets",
        ["discovery_status"],
        unique=False,
        schema=schema,
    )

    # Failure journal for collection write-backs and readiness computation
    op.create_table(
        "failure_journal",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "engagement_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("operation", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("trace", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
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
        schema=schema,
    )
    op.create_index(
        "ix_failure_journal_engagement_op",
        "failure_journal",
        ["engagement_id", "operation"],
        unique=False,
        schema=schema,
    )


def downgrade() -> None:
    schema = op.get_context().version_table_schema or "migration"
    op.drop_index(
        "ix_failure_journal_engagement_op", table_name="failure_journal", schema=schema
    )
    op.drop_table("failure_journal", schema=schema)
    op.drop_index("ix_assets_discovery_status", table_name="assets", schema=schema)
    op.drop_index(
        "ix_assets_client_engagement_readiness", table_name="assets", schema=schema
    )
