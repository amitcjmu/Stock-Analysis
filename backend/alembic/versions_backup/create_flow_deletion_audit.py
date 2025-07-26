"""Create flow deletion audit table

Revision ID: create_flow_deletion_audit
Revises: add_flow_management_columns
Create Date: 2025-01-27 21:46:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "create_flow_deletion_audit"
down_revision = "add_flow_management_columns"
branch_labels = None
depends_on = None


def upgrade():
    """Create comprehensive audit table for flow deletions."""

    op.create_table(
        "flow_deletion_audit",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("flow_id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column(
            "deletion_type",
            sa.String(),
            nullable=False,
            comment="user_requested, auto_cleanup, admin_action, batch_operation",
        ),
        sa.Column("deletion_reason", sa.Text(), nullable=True),
        sa.Column(
            "deletion_method",
            sa.String(),
            nullable=False,
            comment="manual, api, batch, scheduled",
        ),
        # Comprehensive data deletion summary
        sa.Column(
            "data_deleted",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
            comment="Summary of what was deleted",
        ),
        sa.Column(
            "deletion_impact",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
            comment="Impact analysis",
        ),
        sa.Column(
            "cleanup_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
            comment="Cleanup operation results",
        ),
        # CrewAI specific cleanup
        sa.Column(
            "shared_memory_cleaned",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "knowledge_base_refs_cleaned",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "agent_memory_cleaned", sa.Boolean(), nullable=False, server_default="false"
        ),
        # Audit trail
        sa.Column(
            "deleted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_by", sa.String(), nullable=False),
        sa.Column(
            "deletion_duration_ms",
            sa.Integer(),
            nullable=True,
            comment="How long the deletion took",
        ),
        # Recovery information (if applicable)
        sa.Column(
            "recovery_possible", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "recovery_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for audit queries
    op.create_index(
        "idx_flow_deletion_audit_client",
        "flow_deletion_audit",
        ["client_account_id", "engagement_id"],
    )

    op.create_index(
        "idx_flow_deletion_audit_date", "flow_deletion_audit", ["deleted_at"]
    )

    op.create_index(
        "idx_flow_deletion_audit_type",
        "flow_deletion_audit",
        ["deletion_type", "deleted_at"],
    )

    op.create_index(
        "idx_flow_deletion_audit_session", "flow_deletion_audit", ["session_id"]
    )


def downgrade():
    """Drop flow deletion audit table."""

    # Drop indexes
    op.drop_index("idx_flow_deletion_audit_session", table_name="flow_deletion_audit")
    op.drop_index("idx_flow_deletion_audit_type", table_name="flow_deletion_audit")
    op.drop_index("idx_flow_deletion_audit_date", table_name="flow_deletion_audit")
    op.drop_index("idx_flow_deletion_audit_client", table_name="flow_deletion_audit")

    # Drop table
    op.drop_table("flow_deletion_audit")
