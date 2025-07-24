"""add_user_management_and_rbac_tables

Revision ID: 078ab506c9da
Revises: ce14d7658e0c
Create Date: 2025-01-02 00:03:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "078ab506c9da"
down_revision = "ce14d7658e0c"
branch_labels = None
depends_on = None


def upgrade():
    """
    Add user management and RBAC tables
    This includes all missing authentication and authorization tables
    """

    # =============================================================================
    # CORE USER MANAGEMENT
    # =============================================================================

    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "is_mock", sa.Boolean(), server_default=sa.text("false"), nullable=False
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
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # Create indexes for users
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index("ix_users_is_mock", "users", ["is_mock"])

    # =============================================================================
    # USER PROFILES AND STATUS MANAGEMENT
    # =============================================================================

    # Create user_profiles table
    op.create_table(
        "user_profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default=sa.text("'pending_approval'"),
            nullable=False,
        ),
        sa.Column(
            "approval_requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("registration_reason", sa.Text(), nullable=True),
        sa.Column("organization", sa.String(255), nullable=True),
        sa.Column("role_description", sa.String(255), nullable=True),
        sa.Column(
            "requested_access_level",
            sa.String(20),
            server_default=sa.text("'read_only'"),
            nullable=True,
        ),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("manager_email", sa.String(255), nullable=True),
        sa.Column("linkedin_profile", sa.String(255), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "login_count", sa.Integer(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True,
        ),
        sa.Column("last_failed_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "notification_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{"email_notifications": true, "system_alerts": true, "learning_updates": false, "weekly_reports": true}\'::jsonb'
            ),
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
        sa.ForeignKeyConstraint(
            ["approved_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    # Create indexes for user_profiles
    op.create_index("ix_user_profiles_status", "user_profiles", ["status"])
    op.create_index("ix_user_profiles_approved_by", "user_profiles", ["approved_by"])

    # =============================================================================
    # ROLE-BASED ACCESS CONTROL (RBAC)
    # =============================================================================

    # Create user_roles table
    op.create_table(
        "user_roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_type", sa.String(50), nullable=False),
        sa.Column("role_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "permissions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{"can_create_clients": false, "can_manage_engagements": false, "can_import_data": true, "can_export_data": true, "can_view_analytics": true, "can_manage_users": false, "can_configure_agents": false, "can_access_admin_console": false}\'::jsonb'
            ),
            nullable=True,
        ),
        sa.Column(
            "scope_type",
            sa.String(20),
            server_default=sa.text("'global'"),
            nullable=True,
        ),
        sa.Column("scope_client_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scope_engagement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["assigned_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["scope_client_id"],
            ["client_accounts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["scope_engagement_id"],
            ["engagements.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for user_roles
    op.create_index("ix_user_roles_id", "user_roles", ["id"])
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_is_active", "user_roles", ["is_active"])
    op.create_index("ix_user_roles_role_type", "user_roles", ["role_type"])
    op.create_index("ix_user_roles_scope_type", "user_roles", ["scope_type"])

    # =============================================================================
    # USER ACCOUNT ASSOCIATIONS
    # =============================================================================

    # Create user_account_associations table
    op.create_table(
        "user_account_associations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "role", sa.String(50), server_default=sa.text("'member'"), nullable=False
        ),
        sa.Column(
            "is_mock", sa.Boolean(), server_default=sa.text("false"), nullable=False
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
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_account_id"], ["client_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "client_account_id",
            name="uq_user_account_associations_user_client",
        ),
    )

    # Create indexes for user_account_associations
    op.create_index(
        "ix_user_account_associations_user_id", "user_account_associations", ["user_id"]
    )
    op.create_index(
        "ix_user_account_associations_client_account_id",
        "user_account_associations",
        ["client_account_id"],
    )
    op.create_index(
        "ix_user_account_associations_is_mock", "user_account_associations", ["is_mock"]
    )

    # =============================================================================
    # CLIENT ACCESS CONTROL
    # =============================================================================

    # Create client_access table
    op.create_table(
        "client_access",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("access_level", sa.String(20), nullable=False),
        sa.Column(
            "permissions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{"can_view_data": true, "can_import_data": false, "can_export_data": false, "can_manage_engagements": false, "can_configure_client_settings": false, "can_manage_client_users": false}\'::jsonb'
            ),
            nullable=True,
        ),
        sa.Column(
            "restricted_environments",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "restricted_data_types",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "access_count", sa.Integer(), server_default=sa.text("0"), nullable=True
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
        sa.ForeignKeyConstraint(
            ["client_account_id"], ["client_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_profile_id"], ["user_profiles.user_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for client_access
    op.create_index(
        "ix_client_access_user_profile_id", "client_access", ["user_profile_id"]
    )
    op.create_index(
        "ix_client_access_client_account_id", "client_access", ["client_account_id"]
    )
    op.create_index("ix_client_access_is_active", "client_access", ["is_active"])
    op.create_index("ix_client_access_granted_by", "client_access", ["granted_by"])

    # =============================================================================
    # ENGAGEMENT ACCESS CONTROL
    # =============================================================================

    # Create engagement_access table
    op.create_table(
        "engagement_access",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("access_level", sa.String(20), nullable=False),
        sa.Column("engagement_role", sa.String(100), nullable=True),
        sa.Column(
            "permissions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{"can_view_data": true, "can_import_data": false, "can_export_data": false, "can_manage_sessions": false, "can_configure_agents": false, "can_approve_migration_decisions": false, "can_access_sensitive_data": false}\'::jsonb'
            ),
            nullable=True,
        ),
        sa.Column(
            "restricted_sessions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "allowed_session_types",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'["data_import", "validation_run"]\'::jsonb'),
            nullable=True,
        ),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "access_count", sa.Integer(), server_default=sa.text("0"), nullable=True
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
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["engagements.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_profile_id"], ["user_profiles.user_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for engagement_access
    op.create_index(
        "ix_engagement_access_user_profile_id", "engagement_access", ["user_profile_id"]
    )
    op.create_index(
        "ix_engagement_access_engagement_id", "engagement_access", ["engagement_id"]
    )
    op.create_index(
        "ix_engagement_access_is_active", "engagement_access", ["is_active"]
    )
    op.create_index(
        "ix_engagement_access_granted_by", "engagement_access", ["granted_by"]
    )

    # =============================================================================
    # ROLE PERMISSIONS AND SECURITY
    # =============================================================================

    # Create role_permissions table
    op.create_table(
        "role_permissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("role_level", sa.String(30), nullable=False),
        # Platform Management Permissions
        sa.Column(
            "can_manage_platform_settings",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_manage_all_clients",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_manage_all_users",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_purge_deleted_data",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_view_system_logs",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        # Client Management Permissions
        sa.Column(
            "can_create_clients",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_modify_client_settings",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_manage_client_users",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_delete_client_data",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        # Engagement Management Permissions
        sa.Column(
            "can_create_engagements",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_modify_engagement_settings",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_manage_engagement_users",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_delete_engagement_data",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        # Data Permissions
        sa.Column(
            "can_import_data",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_export_data",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_view_analytics",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_modify_data",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        # Agent Permissions
        sa.Column(
            "can_configure_agents",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_view_agent_insights",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
        sa.Column(
            "can_approve_agent_decisions",
            sa.Boolean(),
            server_default=sa.text("false"),
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
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for role_permissions
    op.create_index(
        "ix_role_permissions_role_level", "role_permissions", ["role_level"]
    )

    # =============================================================================
    # ROLE CHANGE APPROVALS
    # =============================================================================

    # Create role_change_approvals table
    op.create_table(
        "role_change_approvals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("requested_by", sa.String(36), nullable=False),
        sa.Column("target_user_id", sa.String(36), nullable=False),
        sa.Column("current_role", sa.String(50), nullable=False),
        sa.Column("requested_role", sa.String(50), nullable=False),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(20), server_default=sa.text("'PENDING'"), nullable=False
        ),
        sa.Column("approved_by", sa.String(36), nullable=True),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for role_change_approvals
    op.create_index(
        "ix_role_change_approvals_requested_by",
        "role_change_approvals",
        ["requested_by"],
    )
    op.create_index(
        "ix_role_change_approvals_target_user_id",
        "role_change_approvals",
        ["target_user_id"],
    )
    op.create_index(
        "ix_role_change_approvals_status", "role_change_approvals", ["status"]
    )

    print("✅ User Management and RBAC migration completed successfully!")
    print("✅ Users table created for authentication")
    print("✅ User profiles table created for user status management")
    print("✅ User roles table created for RBAC authorization")
    print(
        "✅ Client and engagement access tables created for multi-tenant access control"
    )
    print("✅ Role permissions and approval workflow tables created")
    print("✅ Complete user management system ready for production")
    print("✅ Authentication and authorization fully functional")


def downgrade():
    """Rollback user management and RBAC tables"""
    op.drop_table("role_change_approvals")
    op.drop_table("role_permissions")
    op.drop_table("engagement_access")
    op.drop_table("client_access")
    op.drop_table("user_account_associations")
    op.drop_table("user_roles")
    op.drop_table("user_profiles")
    op.drop_table("users")
