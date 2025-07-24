"""Add security audit and access audit tables

Revision ID: 002_add_security_audit_tables
Revises: 001_comprehensive_initial_schema
Create Date: 2025-07-19

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002_add_security_audit_tables"
down_revision = "001_comprehensive_initial_schema"
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if a table exists in the database"""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'migration' 
                AND table_name = :table_name
            )
            """
        ),
        {"table_name": table_name},
    ).scalar()
    return result


def create_table_if_not_exists(table_name, *columns, **kwargs):
    """Create a table only if it doesn't already exist"""
    if not table_exists(table_name):
        op.create_table(table_name, *columns, **kwargs)
    else:
        print(f"Table {table_name} already exists, skipping creation")


def index_exists(index_name, table_name):
    """Check if an index exists on a table"""
    bind = op.get_bind()
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
        ),
        {"table_name": table_name, "index_name": index_name},
    ).scalar()
    return result


def create_index_if_not_exists(index_name, table_name, columns, **kwargs):
    """Create an index only if it doesn't already exist"""
    if table_exists(table_name) and not index_exists(index_name, table_name):
        op.create_index(index_name, table_name, columns, **kwargs)
    else:
        print(
            f"Index {index_name} already exists or table doesn't exist, skipping creation"
        )


def upgrade() -> None:
    """
    Add security audit and admin functionality tables
    This includes all missing audit tables needed for admin features
    """

    # =============================================================================
    # SECURITY AUDIT SYSTEM
    # =============================================================================

    # Create security_audit_logs table (matching SecurityAuditLog model exactly)
    create_table_if_not_exists(
        "security_audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_category", sa.String(50), nullable=False),
        sa.Column(
            "severity", sa.String(20), server_default=sa.text("'INFO'"), nullable=False
        ),
        sa.Column("actor_user_id", sa.String(36), nullable=False),
        sa.Column("actor_email", sa.String(255), nullable=True),
        sa.Column("actor_role", sa.String(50), nullable=True),
        sa.Column("target_user_id", sa.String(36), nullable=True),
        sa.Column("target_email", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("request_path", sa.String(500), nullable=True),
        sa.Column("request_method", sa.String(10), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "is_suspicious",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "requires_review",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_blocked", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(36), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for security_audit_logs
    create_index_if_not_exists(
        "idx_security_audit_logs_actor_user_id",
        "security_audit_logs",
        ["actor_user_id"],
    )
    create_index_if_not_exists(
        "idx_security_audit_logs_target_user_id",
        "security_audit_logs",
        ["target_user_id"],
    )
    create_index_if_not_exists(
        "idx_security_audit_logs_event_type", "security_audit_logs", ["event_type"]
    )
    create_index_if_not_exists(
        "idx_security_audit_logs_severity", "security_audit_logs", ["severity"]
    )
    create_index_if_not_exists(
        "idx_security_audit_logs_created_at", "security_audit_logs", ["created_at"]
    )
    create_index_if_not_exists(
        "idx_security_audit_logs_is_suspicious",
        "security_audit_logs",
        ["is_suspicious"],
    )

    # =============================================================================
    # ACCESS AUDIT SYSTEM
    # =============================================================================

    # Create access_audit_log table (matching AccessAuditLog model exactly)
    create_table_if_not_exists(
        "access_audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for access_audit_log
    create_index_if_not_exists(
        "idx_access_audit_log_user_id", "access_audit_log", ["user_id"]
    )
    create_index_if_not_exists(
        "idx_access_audit_log_action_type", "access_audit_log", ["action_type"]
    )
    create_index_if_not_exists(
        "idx_access_audit_log_resource_type", "access_audit_log", ["resource_type"]
    )
    create_index_if_not_exists(
        "idx_access_audit_log_result", "access_audit_log", ["result"]
    )
    create_index_if_not_exists(
        "idx_access_audit_log_created_at", "access_audit_log", ["created_at"]
    )
    create_index_if_not_exists(
        "idx_access_audit_log_client_account_id",
        "access_audit_log",
        ["client_account_id"],
    )
    create_index_if_not_exists(
        "idx_access_audit_log_engagement_id", "access_audit_log", ["engagement_id"]
    )

    # =============================================================================
    # ENHANCED ACCESS AUDIT SYSTEM
    # =============================================================================

    # Create enhanced_access_audit_log table
    create_table_if_not_exists(
        "enhanced_access_audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "request_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "performance_metrics",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "security_context", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for enhanced_access_audit_log
    create_index_if_not_exists(
        "idx_enhanced_access_audit_log_user_id",
        "enhanced_access_audit_log",
        ["user_id"],
    )
    create_index_if_not_exists(
        "idx_enhanced_access_audit_log_action_type",
        "enhanced_access_audit_log",
        ["action_type"],
    )
    create_index_if_not_exists(
        "idx_enhanced_access_audit_log_resource_type",
        "enhanced_access_audit_log",
        ["resource_type"],
    )
    create_index_if_not_exists(
        "idx_enhanced_access_audit_log_result", "enhanced_access_audit_log", ["result"]
    )
    create_index_if_not_exists(
        "idx_enhanced_access_audit_log_created_at",
        "enhanced_access_audit_log",
        ["created_at"],
    )
    create_index_if_not_exists(
        "idx_enhanced_access_audit_log_client_account_id",
        "enhanced_access_audit_log",
        ["client_account_id"],
    )
    create_index_if_not_exists(
        "idx_enhanced_access_audit_log_engagement_id",
        "enhanced_access_audit_log",
        ["engagement_id"],
    )


def downgrade() -> None:
    """Remove all audit tables"""

    # Drop enhanced_access_audit_log
    op.drop_table("enhanced_access_audit_log")

    # Drop access_audit_log
    op.drop_table("access_audit_log")

    # Drop security_audit_logs
    op.drop_table("security_audit_logs")
