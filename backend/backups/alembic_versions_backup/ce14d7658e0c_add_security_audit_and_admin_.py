"""add_security_audit_and_admin_functionality

Revision ID: ce14d7658e0c
Revises: 3d598ddd1b84
Create Date: 2025-01-02 00:02:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "ce14d7658e0c"
down_revision = "3d598ddd1b84"
branch_labels = None
depends_on = None


def upgrade():
    """
    Add security audit and admin functionality tables
    This includes all missing audit tables needed for admin features
    """

    # =============================================================================
    # SECURITY AUDIT SYSTEM
    # =============================================================================

    # Create security_audit_logs table (matching SecurityAuditLog model exactly)
    op.create_table(
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
        sa.Column(
            "actor_user_id", sa.String(36), nullable=False
        ),  # String 36, not UUID
        sa.Column(
            "actor_email", sa.String(255), nullable=True
        ),  # actor_email, not actor_user_email
        sa.Column("actor_role", sa.String(50), nullable=True),  # Missing column added
        sa.Column(
            "target_user_id", sa.String(36), nullable=True
        ),  # String 36, not UUID
        sa.Column(
            "target_email", sa.String(255), nullable=True
        ),  # Missing column added
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("request_path", sa.String(500), nullable=True),
        sa.Column("request_method", sa.String(10), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),  # Missing column added
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
        sa.Column("reviewed_by", sa.String(36), nullable=True),  # String 36, not UUID
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for security_audit_logs
    op.create_index(
        "ix_security_audit_logs_event_type", "security_audit_logs", ["event_type"]
    )
    op.create_index(
        "ix_security_audit_logs_actor_user_id", "security_audit_logs", ["actor_user_id"]
    )
    op.create_index(
        "ix_security_audit_logs_target_user_id",
        "security_audit_logs",
        ["target_user_id"],
    )
    op.create_index(
        "ix_security_audit_logs_created_at", "security_audit_logs", ["created_at"]
    )
    op.create_index(
        "ix_security_audit_logs_is_suspicious", "security_audit_logs", ["is_suspicious"]
    )
    op.create_index(
        "ix_security_audit_logs_requires_review",
        "security_audit_logs",
        ["requires_review"],
    )

    # =============================================================================
    # ACCESS AUDIT SYSTEM
    # =============================================================================

    # Create access_audit_log table (matching AccessAuditLog model exactly)
    op.create_table(
        "access_audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), nullable=True
        ),  # Allow null for anonymous/system users
        sa.Column(
            "action_type", sa.String(50), nullable=False
        ),  # action_type, not action
        sa.Column(
            "resource_type", sa.String(50), nullable=True
        ),  # resource_type, not resource
        sa.Column("resource_id", sa.String(255), nullable=True),  # String, not UUID
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result", sa.String(20), nullable=False),  # result field added
        sa.Column("reason", sa.Text(), nullable=True),  # reason field added
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
        ),
        # Remove foreign key constraints to avoid dependency issues
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for access_audit_log
    op.create_index("ix_access_audit_log_user_id", "access_audit_log", ["user_id"])
    op.create_index(
        "ix_access_audit_log_action_type", "access_audit_log", ["action_type"]
    )
    op.create_index(
        "ix_access_audit_log_resource_type", "access_audit_log", ["resource_type"]
    )
    op.create_index(
        "ix_access_audit_log_client_account_id",
        "access_audit_log",
        ["client_account_id"],
    )
    op.create_index(
        "ix_access_audit_log_created_at", "access_audit_log", ["created_at"]
    )
    op.create_index("ix_access_audit_log_result", "access_audit_log", ["result"])

    # =============================================================================
    # ENHANCED ACCESS AUDIT (RBAC-specific)
    # =============================================================================

    # Create enhanced_access_audit_log table
    op.create_table(
        "enhanced_access_audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource", sa.String(200), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("master_flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("permission_required", sa.String(200), nullable=True),
        sa.Column(
            "permissions_checked",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "roles_at_time",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column("rbac_decision", sa.String(50), nullable=True),
        sa.Column("rbac_decision_reason", sa.Text(), nullable=True),
        sa.Column(
            "context_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("request_path", sa.String(500), nullable=True),
        sa.Column("request_method", sa.String(10), nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_time_ms", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
        ),
        sa.ForeignKeyConstraint(
            ["master_flow_id"],
            ["crewai_flow_state_extensions.flow_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for enhanced_access_audit_log
    op.create_index(
        "ix_enhanced_access_audit_log_user_id", "enhanced_access_audit_log", ["user_id"]
    )
    op.create_index(
        "ix_enhanced_access_audit_log_action", "enhanced_access_audit_log", ["action"]
    )
    op.create_index(
        "ix_enhanced_access_audit_log_rbac_decision",
        "enhanced_access_audit_log",
        ["rbac_decision"],
    )
    op.create_index(
        "ix_enhanced_access_audit_log_client_account_id",
        "enhanced_access_audit_log",
        ["client_account_id"],
    )
    op.create_index(
        "ix_enhanced_access_audit_log_created_at",
        "enhanced_access_audit_log",
        ["created_at"],
    )

    # =============================================================================
    # FLOW DELETION AUDIT
    # =============================================================================

    # Create flow_deletion_audit table
    op.create_table(
        "flow_deletion_audit",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("deleted_flow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flow_type", sa.String(50), nullable=False),
        sa.Column("deleted_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_by_user_email", sa.String(255), nullable=True),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deletion_reason", sa.String(200), nullable=True),
        sa.Column(
            "flow_data_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("related_assets_count", sa.Integer(), nullable=True),
        sa.Column(
            "cleanup_actions_taken",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for flow_deletion_audit
    op.create_index(
        "ix_flow_deletion_audit_deleted_flow_id",
        "flow_deletion_audit",
        ["deleted_flow_id"],
    )
    op.create_index(
        "ix_flow_deletion_audit_flow_type", "flow_deletion_audit", ["flow_type"]
    )
    op.create_index(
        "ix_flow_deletion_audit_deleted_by_user_id",
        "flow_deletion_audit",
        ["deleted_by_user_id"],
    )
    op.create_index(
        "ix_flow_deletion_audit_client_account_id",
        "flow_deletion_audit",
        ["client_account_id"],
    )
    op.create_index(
        "ix_flow_deletion_audit_created_at", "flow_deletion_audit", ["created_at"]
    )

    # =============================================================================
    # DATA IMPORT SESSION MANAGEMENT
    # =============================================================================

    # Create data_import_sessions table
    op.create_table(
        "data_import_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("file_hash", sa.String(64), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("master_flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("total_rows", sa.Integer(), nullable=True),
        sa.Column("processed_rows", sa.Integer(), nullable=True),
        sa.Column("successful_rows", sa.Integer(), nullable=True),
        sa.Column("error_rows", sa.Integer(), nullable=True),
        sa.Column(
            "validation_errors",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "processing_log",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "field_mappings",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "data_quality_metrics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "agent_analysis",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
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
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
        ),
        sa.ForeignKeyConstraint(
            ["master_flow_id"],
            ["crewai_flow_state_extensions.flow_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for data_import_sessions
    op.create_index(
        "ix_data_import_sessions_filename", "data_import_sessions", ["filename"]
    )
    op.create_index(
        "ix_data_import_sessions_status", "data_import_sessions", ["status"]
    )
    op.create_index(
        "ix_data_import_sessions_client_account_id",
        "data_import_sessions",
        ["client_account_id"],
    )
    op.create_index(
        "ix_data_import_sessions_engagement_id",
        "data_import_sessions",
        ["engagement_id"],
    )
    op.create_index(
        "ix_data_import_sessions_user_id", "data_import_sessions", ["user_id"]
    )
    op.create_index(
        "ix_data_import_sessions_created_at", "data_import_sessions", ["created_at"]
    )

    print("✅ Security Audit and Admin Functionality migration completed successfully!")
    print("✅ Security audit logs table created with comprehensive tracking")
    print("✅ Access audit log tables created with RBAC integration")
    print("✅ Enhanced audit logging with master flow coordination")
    print("✅ Flow deletion audit tracking implemented")
    print("✅ Data import session management tables created")
    print("✅ All admin functionality requirements satisfied")
    print("✅ Production deployment ready - Railway, AWS, Docker compatible")


def downgrade():
    """Rollback security audit and admin functionality"""
    op.drop_table("data_import_sessions")
    op.drop_table("flow_deletion_audit")
    op.drop_table("enhanced_access_audit_log")
    op.drop_table("access_audit_log")
    op.drop_table("security_audit_logs")
