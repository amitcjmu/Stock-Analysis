"""Comprehensive initial schema with all tables

Revision ID: 001_comprehensive_initial_schema
Revises:
Create Date: 2025-07-18

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "001_comprehensive_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if a table exists in the database"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def create_table_if_not_exists(table_name, *columns, **kwargs):
    """Create a table only if it doesn't already exist"""
    if not table_exists(table_name):
        op.create_table(table_name, *columns, **kwargs)
    else:
        print(f"Table {table_name} already exists, skipping creation")


def index_exists(index_name, table_name):
    """Check if an index exists on a table"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def create_index_if_not_exists(index_name, table_name, columns, **kwargs):
    """Create an index only if it doesn't already exist"""
    if table_exists(table_name) and not index_exists(index_name, table_name):
        op.create_index(index_name, table_name, columns, **kwargs)
    else:
        print(
            f"Index {index_name} already exists or table doesn't exist, skipping creation"
        )


def upgrade() -> None:
    # Create assessment and risk level enums (conditionally)
    bind = op.get_bind()

    # Check if enum types already exist and create only if they don't
    try:
        result = bind.execute(
            sa.text(
                """
            SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'assessmenttype')
        """
            )
        ).scalar()
        if not result:
            sa.Enum(
                "TECHNICAL",
                "BUSINESS",
                "SECURITY",
                "COMPLIANCE",
                "PERFORMANCE",
                name="assessmenttype",
            ).create(bind)
    except Exception:
        # If query fails, assume enum doesn't exist and try to create it
        try:
            sa.Enum(
                "TECHNICAL",
                "BUSINESS",
                "SECURITY",
                "COMPLIANCE",
                "PERFORMANCE",
                name="assessmenttype",
            ).create(bind)
        except Exception:
            pass  # Enum probably already exists

    try:
        result = bind.execute(
            sa.text(
                """
            SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'assessmentstatus')
        """
            )
        ).scalar()
        if not result:
            sa.Enum(
                "PENDING",
                "IN_PROGRESS",
                "COMPLETED",
                "REVIEWED",
                "APPROVED",
                "REJECTED",
                name="assessmentstatus",
            ).create(bind)
    except Exception:
        try:
            sa.Enum(
                "PENDING",
                "IN_PROGRESS",
                "COMPLETED",
                "REVIEWED",
                "APPROVED",
                "REJECTED",
                name="assessmentstatus",
            ).create(bind)
        except Exception:
            pass

    try:
        result = bind.execute(
            sa.text(
                """
            SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'risklevel')
        """
            )
        ).scalar()
        if not result:
            sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="risklevel").create(bind)
    except Exception:
        try:
            sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="risklevel").create(bind)
        except Exception:
            pass

    # Create client_accounts table
    create_table_if_not_exists(
        "client_accounts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.VARCHAR(length=255), nullable=False),
        sa.Column("slug", sa.VARCHAR(length=100), nullable=False),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("industry", sa.VARCHAR(length=100), nullable=True),
        sa.Column("company_size", sa.VARCHAR(length=50), nullable=True),
        sa.Column("headquarters_location", sa.VARCHAR(length=255), nullable=True),
        sa.Column("primary_contact_name", sa.VARCHAR(length=255), nullable=True),
        sa.Column("primary_contact_email", sa.VARCHAR(length=255), nullable=True),
        sa.Column("primary_contact_phone", sa.VARCHAR(length=50), nullable=True),
        sa.Column("contact_email", sa.VARCHAR(length=255), nullable=True),
        sa.Column("contact_phone", sa.VARCHAR(length=50), nullable=True),
        sa.Column("address", sa.TEXT(), nullable=True),
        sa.Column("timezone", sa.VARCHAR(length=50), nullable=True),
        sa.Column(
            "subscription_tier",
            sa.VARCHAR(length=50),
            server_default="standard",
            nullable=True,
        ),
        sa.Column("billing_contact_email", sa.VARCHAR(length=255), nullable=True),
        sa.Column(
            "subscription_start_date", sa.TIMESTAMP(timezone=True), nullable=True
        ),
        sa.Column("subscription_end_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("max_users", sa.INTEGER(), nullable=True),
        sa.Column("max_engagements", sa.INTEGER(), nullable=True),
        sa.Column(
            "features_enabled",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'{}'::json"),
            nullable=True,
        ),
        sa.Column(
            "agent_configuration",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'{}'::json"),
            nullable=True,
        ),
        sa.Column("storage_quota_gb", sa.INTEGER(), nullable=True),
        sa.Column("api_quota_monthly", sa.INTEGER(), nullable=True),
        sa.Column(
            "settings",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'{}'::json"),
            nullable=True,
        ),
        sa.Column(
            "branding",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'{}'::json"),
            nullable=True,
        ),
        sa.Column(
            "business_objectives",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{"primary_goals": [], "timeframe": "", "success_metrics": [], "constraints": []}\'::json'
            ),
            nullable=True,
        ),
        sa.Column(
            "it_guidelines", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "decision_criteria", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "agent_preferences",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{"discovery_depth": "comprehensive", "automation_level": "assisted", "risk_tolerance": "moderate", "preferred_clouds": [], "compliance_requirements": [], "custom_rules": []}\'::json'
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column(
            "is_active", sa.BOOLEAN(), server_default=sa.text("true"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client_accounts")),
        sa.UniqueConstraint("slug", name=op.f("uq_client_accounts_slug")),
    )

    # Create users table
    create_table_if_not_exists(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.VARCHAR(length=255), nullable=False),
        sa.Column("password_hash", sa.VARCHAR(length=255), nullable=True),
        sa.Column("first_name", sa.VARCHAR(length=100), nullable=True),
        sa.Column("last_name", sa.VARCHAR(length=100), nullable=True),
        sa.Column(
            "is_active", sa.BOOLEAN(), server_default=sa.text("true"), nullable=True
        ),
        sa.Column(
            "is_verified", sa.BOOLEAN(), server_default=sa.text("false"), nullable=True
        ),
        sa.Column("default_client_id", sa.UUID(), nullable=True),
        sa.Column("default_engagement_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("last_login", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["default_client_id"],
            ["client_accounts.id"],
            name=op.f("fk_users_default_client_id_client_accounts"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    # Create engagements table
    create_table_if_not_exists(
        "engagements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.VARCHAR(length=255), nullable=False),
        sa.Column("slug", sa.VARCHAR(length=100), nullable=False),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column(
            "engagement_type",
            sa.VARCHAR(length=50),
            server_default="migration",
            nullable=True,
        ),
        sa.Column(
            "status", sa.VARCHAR(length=50), server_default="active", nullable=True
        ),
        sa.Column(
            "priority", sa.VARCHAR(length=20), server_default="medium", nullable=True
        ),
        sa.Column("start_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("target_completion_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("actual_completion_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("engagement_lead_id", sa.UUID(), nullable=True),
        sa.Column("client_contact_name", sa.VARCHAR(length=255), nullable=True),
        sa.Column("client_contact_email", sa.VARCHAR(length=255), nullable=True),
        sa.Column(
            "settings",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'{}'::json"),
            nullable=True,
        ),
        sa.Column(
            "migration_scope",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{"target_clouds": [], "migration_strategies": [], "excluded_systems": [], "included_environments": [], "business_units": [], "geographic_scope": [], "timeline_constraints": {}}\'::json'
            ),
            nullable=True,
        ),
        sa.Column(
            "team_preferences",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{"stakeholders": [], "decision_makers": [], "technical_leads": [], "communication_style": "formal", "reporting_frequency": "weekly", "preferred_meeting_times": [], "escalation_contacts": [], "project_methodology": "agile"}\'::json'
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column(
            "is_active", sa.BOOLEAN(), server_default=sa.text("true"), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_engagements_client_account_id_client_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["engagement_lead_id"],
            ["users.id"],
            name=op.f("fk_engagements_engagement_lead_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_engagements")),
    )

    # Create user_profiles table
    create_table_if_not_exists(
        "user_profiles",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.VARCHAR(length=20),
            server_default="PENDING_APPROVAL",
            nullable=False,
        ),
        sa.Column(
            "approval_requested_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("approved_by", sa.UUID(), nullable=True),
        sa.Column("registration_reason", sa.TEXT(), nullable=True),
        sa.Column("organization", sa.VARCHAR(length=255), nullable=True),
        sa.Column("role_description", sa.VARCHAR(length=255), nullable=True),
        sa.Column(
            "requested_access_level",
            sa.VARCHAR(length=20),
            server_default="READ_ONLY",
            nullable=True,
        ),
        sa.Column("phone_number", sa.VARCHAR(length=20), nullable=True),
        sa.Column("manager_email", sa.VARCHAR(length=255), nullable=True),
        sa.Column("linkedin_profile", sa.VARCHAR(length=255), nullable=True),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "login_count", sa.INTEGER(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column(
            "failed_login_attempts",
            sa.INTEGER(),
            server_default=sa.text("0"),
            nullable=True,
        ),
        sa.Column("last_failed_login", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "notification_preferences",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{"email_notifications": true, "system_alerts": true, "learning_updates": false, "weekly_reports": true}\'::json'
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["approved_by"],
            ["users.id"],
            name=op.f("fk_user_profiles_approved_by_users"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_profiles_user_id_users")
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_user_profiles")),
    )

    # Create RBAC tables
    create_table_if_not_exists(
        "user_roles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role_type", sa.VARCHAR(length=50), nullable=False),
        sa.Column("role_name", sa.VARCHAR(length=100), nullable=False),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("permissions", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("scope_type", sa.VARCHAR(length=20), nullable=True),
        sa.Column("scope_client_id", sa.UUID(), nullable=True),
        sa.Column("scope_engagement_id", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.BOOLEAN(), nullable=True),
        sa.Column(
            "assigned_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("assigned_by", sa.UUID(), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by"], ["users.id"], name=op.f("fk_user_roles_assigned_by_users")
        ),
        sa.ForeignKeyConstraint(
            ["scope_client_id"],
            ["client_accounts.id"],
            name=op.f("fk_user_roles_scope_client_id_client_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["scope_engagement_id"],
            ["engagements.id"],
            name=op.f("fk_user_roles_scope_engagement_id_engagements"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_roles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_roles")),
    )
    create_index_if_not_exists(
        op.f("ix_user_roles_id"), "user_roles", ["id"], unique=False
    )
    create_index_if_not_exists(
        op.f("ix_user_roles_user_id"), "user_roles", ["user_id"], unique=False
    )
    create_index_if_not_exists(
        op.f("ix_user_roles_is_active"), "user_roles", ["is_active"], unique=False
    )

    create_table_if_not_exists(
        "user_account_associations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.VARCHAR(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_user_account_associations_client_account_id_client_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_user_account_associations_created_by_users"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_account_associations_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_account_associations")),
        sa.UniqueConstraint(
            "user_id", "client_account_id", name="_user_client_account_uc"
        ),
    )
    create_index_if_not_exists(
        op.f("ix_user_account_associations_user_id"),
        "user_account_associations",
        ["user_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_user_account_associations_client_account_id"),
        "user_account_associations",
        ["client_account_id"],
        unique=False,
    )

    # Create client_access table
    create_table_if_not_exists(
        "client_access",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_profile_id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("access_level", sa.VARCHAR(length=20), nullable=False),
        sa.Column(
            "permissions",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{"can_view_data": true, "can_import_data": false, "can_export_data": false, "can_manage_engagements": false, "can_configure_client_settings": false, "can_manage_client_users": false}\'::json'
            ),
            nullable=True,
        ),
        sa.Column(
            "restricted_environments",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'[]'::json"),
            nullable=True,
        ),
        sa.Column(
            "restricted_data_types",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'[]'::json"),
            nullable=True,
        ),
        sa.Column(
            "granted_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("granted_by", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "is_active", sa.BOOLEAN(), server_default=sa.text("true"), nullable=True
        ),
        sa.Column("last_accessed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "access_count", sa.INTEGER(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_client_access_client_account_id_client_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"], ["users.id"], name=op.f("fk_client_access_granted_by_users")
        ),
        sa.ForeignKeyConstraint(
            ["user_profile_id"],
            ["user_profiles.user_id"],
            name=op.f("fk_client_access_user_profile_id_user_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client_access")),
    )

    # Create engagement_access table
    create_table_if_not_exists(
        "engagement_access",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_profile_id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("access_level", sa.VARCHAR(length=20), nullable=False),
        sa.Column("engagement_role", sa.VARCHAR(length=100), nullable=True),
        sa.Column(
            "permissions",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{"can_view_data": true, "can_import_data": false, "can_export_data": false, "can_manage_sessions": false, "can_configure_agents": false, "can_approve_migration_decisions": false, "can_access_sensitive_data": false}\'::json'
            ),
            nullable=True,
        ),
        sa.Column(
            "restricted_sessions",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'[]'::json"),
            nullable=True,
        ),
        sa.Column(
            "allowed_session_types",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text('\'["data_import", "validation_run"]\'::json'),
            nullable=True,
        ),
        sa.Column(
            "granted_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("granted_by", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "is_active", sa.BOOLEAN(), server_default=sa.text("true"), nullable=True
        ),
        sa.Column("last_accessed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "access_count", sa.INTEGER(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
            name=op.f("fk_engagement_access_engagement_id_engagements"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"],
            ["users.id"],
            name=op.f("fk_engagement_access_granted_by_users"),
        ),
        sa.ForeignKeyConstraint(
            ["user_profile_id"],
            ["user_profiles.user_id"],
            name=op.f("fk_engagement_access_user_profile_id_user_profiles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_engagement_access")),
    )
    create_index_if_not_exists(
        op.f("ix_engagement_access_id"), "engagement_access", ["id"], unique=False
    )
    create_index_if_not_exists(
        op.f("ix_engagement_access_user_profile_id"),
        "engagement_access",
        ["user_profile_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_engagement_access_engagement_id"),
        "engagement_access",
        ["engagement_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_engagement_access_is_active"),
        "engagement_access",
        ["is_active"],
        unique=False,
    )

    # Create crewai_flow_state_extensions table
    create_table_if_not_exists(
        "crewai_flow_state_extensions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("flow_id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.VARCHAR(length=255), nullable=False),
        sa.Column("flow_type", sa.VARCHAR(length=50), nullable=False),
        sa.Column("flow_name", sa.VARCHAR(length=255), nullable=True),
        sa.Column(
            "flow_status",
            sa.VARCHAR(length=50),
            server_default="initialized",
            nullable=False,
        ),
        sa.Column(
            "flow_configuration",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "flow_persistence_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "agent_collaboration_log",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "memory_usage_metrics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "knowledge_base_analytics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "phase_execution_times",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "agent_performance_metrics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "crew_coordination_analytics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "learning_patterns",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "user_feedback_history",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "adaptation_metrics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "phase_transitions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "error_history",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "retry_count", sa.INTEGER(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("parent_flow_id", sa.UUID(), nullable=True),
        sa.Column(
            "child_flow_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "flow_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f(
                "fk_crewai_flow_state_extensions_client_account_id_client_accounts"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
            name=op.f("fk_crewai_flow_state_extensions_engagement_id_engagements"),
        ),
        sa.ForeignKeyConstraint(
            ["parent_flow_id"],
            ["crewai_flow_state_extensions.flow_id"],
            name="fk_crewai_flow_state_parent",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_crewai_flow_state_extensions")),
        sa.UniqueConstraint(
            "flow_id", name=op.f("uq_crewai_flow_state_extensions_flow_id")
        ),
    )

    # Create data_imports table
    create_table_if_not_exists(
        "data_imports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=True),
        sa.Column("engagement_id", sa.UUID(), nullable=True),
        sa.Column("master_flow_id", sa.UUID(), nullable=True),
        sa.Column("import_name", sa.VARCHAR(length=255), nullable=False),
        sa.Column("import_type", sa.VARCHAR(length=50), nullable=False),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("filename", sa.VARCHAR(length=255), nullable=False),
        sa.Column("file_size", sa.INTEGER(), nullable=True),
        sa.Column("mime_type", sa.VARCHAR(length=100), nullable=True),
        sa.Column("source_system", sa.VARCHAR(length=100), nullable=True),
        sa.Column(
            "status", sa.VARCHAR(length=20), server_default="pending", nullable=False
        ),
        sa.Column(
            "progress_percentage",
            sa.DOUBLE_PRECISION(precision=53),
            server_default=sa.text("'0'::double precision"),
            nullable=True,
        ),
        sa.Column("total_records", sa.INTEGER(), nullable=True),
        sa.Column(
            "processed_records",
            sa.INTEGER(),
            server_default=sa.text("0"),
            nullable=True,
        ),
        sa.Column(
            "failed_records", sa.INTEGER(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column("imported_by", sa.UUID(), nullable=False),
        sa.Column("error_message", sa.TEXT(), nullable=True),
        sa.Column(
            "error_details", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_data_imports_client_account_id_client_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
            name=op.f("fk_data_imports_engagement_id_engagements"),
        ),
        sa.ForeignKeyConstraint(
            ["imported_by"],
            ["users.id"],
            name=op.f("fk_data_imports_imported_by_users"),
        ),
        sa.ForeignKeyConstraint(
            ["master_flow_id"],
            ["crewai_flow_state_extensions.flow_id"],
            name=op.f("fk_data_imports_master_flow_id_crewai_flow_state_extensions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_data_imports")),
    )

    # Create discovery_flows table
    create_table_if_not_exists(
        "discovery_flows",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("flow_id", sa.UUID(), nullable=False),
        sa.Column("master_flow_id", sa.UUID(), nullable=True),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.VARCHAR(), nullable=False),
        sa.Column("data_import_id", sa.UUID(), nullable=True),
        sa.Column("flow_name", sa.VARCHAR(length=255), nullable=False),
        sa.Column(
            "status", sa.VARCHAR(length=20), server_default="active", nullable=False
        ),
        sa.Column(
            "progress_percentage",
            sa.FLOAT(),
            server_default=sa.text("0.0"),
            nullable=False,
        ),
        sa.Column(
            "data_import_completed",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "field_mapping_completed",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "data_cleansing_completed",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "asset_inventory_completed",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "dependency_analysis_completed",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "tech_debt_assessment_completed",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "learning_scope",
            sa.VARCHAR(length=50),
            server_default="engagement",
            nullable=False,
        ),
        sa.Column(
            "memory_isolation_level",
            sa.VARCHAR(length=20),
            server_default="strict",
            nullable=False,
        ),
        sa.Column(
            "assessment_ready",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "phase_state",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "agent_state",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("flow_type", sa.VARCHAR(length=100), nullable=True),
        sa.Column("current_phase", sa.VARCHAR(length=100), nullable=True),
        sa.Column(
            "phases_completed", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "flow_state",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'{}'::json"),
            nullable=True,
        ),
        sa.Column(
            "crew_outputs", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "field_mappings", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "discovered_assets", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "dependencies", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "tech_debt_analysis", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("crewai_persistence_id", sa.UUID(), nullable=True),
        sa.Column(
            "crewai_state_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("error_message", sa.TEXT(), nullable=True),
        sa.Column("error_phase", sa.VARCHAR(length=100), nullable=True),
        sa.Column(
            "error_details", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["data_import_id"],
            ["data_imports.id"],
            name=op.f("fk_discovery_flows_data_import_id_data_imports"),
        ),
        sa.ForeignKeyConstraint(
            ["master_flow_id"],
            ["crewai_flow_state_extensions.flow_id"],
            name=op.f("fk_discovery_flows_master_flow_id_crewai_flow_state_extensions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_discovery_flows")),
        sa.UniqueConstraint("flow_id", name=op.f("uq_discovery_flows_flow_id")),
    )
    create_index_if_not_exists(
        op.f("ix_discovery_flows_id"), "discovery_flows", ["id"], unique=False
    )
    create_index_if_not_exists(
        op.f("ix_discovery_flows_flow_id"), "discovery_flows", ["flow_id"], unique=False
    )
    create_index_if_not_exists(
        op.f("ix_discovery_flows_master_flow_id"),
        "discovery_flows",
        ["master_flow_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_discovery_flows_client_account_id"),
        "discovery_flows",
        ["client_account_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_discovery_flows_engagement_id"),
        "discovery_flows",
        ["engagement_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_discovery_flows_data_import_id"),
        "discovery_flows",
        ["data_import_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_discovery_flows_status"), "discovery_flows", ["status"], unique=False
    )

    # Create raw_import_records table
    create_table_if_not_exists(
        "raw_import_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("data_import_id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=True),
        sa.Column("engagement_id", sa.UUID(), nullable=True),
        sa.Column("master_flow_id", sa.UUID(), nullable=True),
        sa.Column("row_number", sa.INTEGER(), nullable=False),
        sa.Column("raw_data", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "cleansed_data", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "validation_errors", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("processing_notes", sa.TEXT(), nullable=True),
        sa.Column(
            "is_processed", sa.BOOLEAN(), server_default=sa.text("false"), nullable=True
        ),
        sa.Column(
            "is_valid", sa.BOOLEAN(), server_default=sa.text("true"), nullable=True
        ),
        sa.Column("asset_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("processed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_raw_import_records_client_account_id_client_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["data_import_id"],
            ["data_imports.id"],
            name=op.f("fk_raw_import_records_data_import_id_data_imports"),
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
            name=op.f("fk_raw_import_records_engagement_id_engagements"),
        ),
        sa.ForeignKeyConstraint(
            ["master_flow_id"],
            ["crewai_flow_state_extensions.flow_id"],
            name=op.f(
                "fk_raw_import_records_master_flow_id_crewai_flow_state_extensions"
            ),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_raw_import_records")),
    )

    # Create import_field_mappings table
    create_table_if_not_exists(
        "import_field_mappings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("data_import_id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("master_flow_id", sa.UUID(), nullable=True),
        sa.Column("source_field", sa.VARCHAR(length=255), nullable=False),
        sa.Column("target_field", sa.VARCHAR(length=255), nullable=False),
        sa.Column(
            "match_type", sa.VARCHAR(length=50), server_default="direct", nullable=False
        ),
        sa.Column("confidence_score", sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column(
            "status", sa.VARCHAR(length=20), server_default="suggested", nullable=True
        ),
        sa.Column(
            "suggested_by",
            sa.VARCHAR(length=50),
            server_default="ai_mapper",
            nullable=True,
        ),
        sa.Column("approved_by", sa.VARCHAR(length=255), nullable=True),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "transformation_rules",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_import_field_mappings_client_account_id_client_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["data_import_id"],
            ["data_imports.id"],
            name=op.f("fk_import_field_mappings_data_import_id_data_imports"),
        ),
        sa.ForeignKeyConstraint(
            ["master_flow_id"],
            ["crewai_flow_state_extensions.flow_id"],
            name=op.f(
                "fk_import_field_mappings_master_flow_id_crewai_flow_state_extensions"
            ),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_import_field_mappings")),
    )

    # Create assessments table
    create_table_if_not_exists(
        "assessments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column(
            "assessment_type",
            postgresql.ENUM(
                "TECHNICAL",
                "BUSINESS",
                "SECURITY",
                "COMPLIANCE",
                "PERFORMANCE",
                name="assessmenttype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING",
                "IN_PROGRESS",
                "COMPLETED",
                "REVIEWED",
                "APPROVED",
                "REJECTED",
                name="assessmentstatus",
                create_type=False,
            ),
            server_default="PENDING",
            nullable=True,
        ),
        sa.Column(
            "risk_level",
            postgresql.ENUM(
                "LOW", "MEDIUM", "HIGH", "CRITICAL", name="risklevel", create_type=False
            ),
            nullable=True,
        ),
        sa.Column("summary", sa.TEXT(), nullable=True),
        sa.Column("recommendations", sa.TEXT(), nullable=True),
        sa.Column("report_url", sa.VARCHAR(length=255), nullable=True),
        sa.Column("master_flow_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_assessments_client_account_id_client_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
            name=op.f("fk_assessments_engagement_id_engagements"),
        ),
        sa.ForeignKeyConstraint(
            ["master_flow_id"],
            ["crewai_flow_state_extensions.flow_id"],
            name=op.f("fk_assessments_master_flow_id_crewai_flow_state_extensions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assessments")),
    )

    # Create assets table with all columns including raw_import_records_id
    create_table_if_not_exists(
        "assets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("flow_id", sa.UUID(), nullable=True),
        sa.Column("migration_id", sa.UUID(), nullable=True),
        sa.Column("master_flow_id", sa.UUID(), nullable=True),
        sa.Column("discovery_flow_id", sa.UUID(), nullable=True),
        sa.Column("assessment_flow_id", sa.UUID(), nullable=True),
        sa.Column("planning_flow_id", sa.UUID(), nullable=True),
        sa.Column("execution_flow_id", sa.UUID(), nullable=True),
        sa.Column("source_phase", sa.VARCHAR(length=50), nullable=True),
        sa.Column("current_phase", sa.VARCHAR(length=50), nullable=True),
        sa.Column(
            "phase_context", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("name", sa.VARCHAR(length=255), nullable=False),
        sa.Column("asset_name", sa.VARCHAR(length=255), nullable=True),
        sa.Column("hostname", sa.VARCHAR(length=255), nullable=True),
        sa.Column("asset_type", sa.VARCHAR(length=50), nullable=False),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("ip_address", sa.VARCHAR(length=45), nullable=True),
        sa.Column("fqdn", sa.VARCHAR(length=255), nullable=True),
        sa.Column("mac_address", sa.VARCHAR(length=17), nullable=True),
        sa.Column("environment", sa.VARCHAR(length=50), nullable=True),
        sa.Column("location", sa.VARCHAR(length=100), nullable=True),
        sa.Column("datacenter", sa.VARCHAR(length=100), nullable=True),
        sa.Column("rack_location", sa.VARCHAR(length=50), nullable=True),
        sa.Column("availability_zone", sa.VARCHAR(length=50), nullable=True),
        sa.Column("operating_system", sa.VARCHAR(length=100), nullable=True),
        sa.Column("os_version", sa.VARCHAR(length=50), nullable=True),
        sa.Column("cpu_cores", sa.INTEGER(), nullable=True),
        sa.Column("memory_gb", sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column("storage_gb", sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column("business_owner", sa.VARCHAR(length=255), nullable=True),
        sa.Column("technical_owner", sa.VARCHAR(length=255), nullable=True),
        sa.Column("department", sa.VARCHAR(length=100), nullable=True),
        sa.Column("application_name", sa.VARCHAR(length=255), nullable=True),
        sa.Column("technology_stack", sa.VARCHAR(length=255), nullable=True),
        sa.Column("criticality", sa.VARCHAR(length=20), nullable=True),
        sa.Column("business_criticality", sa.VARCHAR(length=20), nullable=True),
        sa.Column(
            "custom_attributes", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("six_r_strategy", sa.VARCHAR(length=50), nullable=True),
        sa.Column("mapping_status", sa.VARCHAR(length=20), nullable=True),
        sa.Column("migration_priority", sa.INTEGER(), nullable=True),
        sa.Column("migration_complexity", sa.VARCHAR(length=20), nullable=True),
        sa.Column("migration_wave", sa.INTEGER(), nullable=True),
        sa.Column("sixr_ready", sa.VARCHAR(length=50), nullable=True),
        sa.Column("status", sa.VARCHAR(length=50), nullable=True),
        sa.Column("migration_status", sa.VARCHAR(length=50), nullable=True),
        sa.Column(
            "dependencies", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "related_assets", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("discovery_method", sa.VARCHAR(length=50), nullable=True),
        sa.Column("discovery_source", sa.VARCHAR(length=100), nullable=True),
        sa.Column("discovery_timestamp", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "cpu_utilization_percent", sa.DOUBLE_PRECISION(precision=53), nullable=True
        ),
        sa.Column(
            "memory_utilization_percent",
            sa.DOUBLE_PRECISION(precision=53),
            nullable=True,
        ),
        sa.Column("disk_iops", sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column(
            "network_throughput_mbps", sa.DOUBLE_PRECISION(precision=53), nullable=True
        ),
        sa.Column(
            "completeness_score", sa.DOUBLE_PRECISION(precision=53), nullable=True
        ),
        sa.Column("quality_score", sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column(
            "current_monthly_cost", sa.DOUBLE_PRECISION(precision=53), nullable=True
        ),
        sa.Column(
            "estimated_cloud_cost", sa.DOUBLE_PRECISION(precision=53), nullable=True
        ),
        sa.Column("imported_by", sa.UUID(), nullable=True),
        sa.Column("imported_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("source_filename", sa.VARCHAR(length=255), nullable=True),
        sa.Column("raw_data", sa.TEXT(), nullable=True),
        sa.Column(
            "field_mappings_used", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("raw_import_records_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_assets_client_account_id_client_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
            name=op.f("fk_assets_engagement_id_engagements"),
        ),
        sa.ForeignKeyConstraint(
            ["raw_import_records_id"],
            ["raw_import_records.id"],
            name=op.f("fk_assets_raw_import_records_id_raw_import_records"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assets")),
    )

    # Create performance indexes for assets
    create_index_if_not_exists(
        "idx_assets_client_engagement",
        "assets",
        ["client_account_id", "engagement_id"],
        unique=False,
    )
    create_index_if_not_exists(
        "idx_assets_created_at_desc",
        "assets",
        [sa.text("created_at DESC")],
        unique=False,
    )
    create_index_if_not_exists(
        "idx_assets_type", "assets", ["asset_type"], unique=False
    )
    create_index_if_not_exists("idx_assets_status", "assets", ["status"], unique=False)
    create_index_if_not_exists(
        "idx_assets_client_engagement_created",
        "assets",
        ["client_account_id", "engagement_id", sa.text("created_at DESC")],
        unique=False,
    )

    # Create uniqueness constraints for assets
    create_index_if_not_exists(
        "ix_assets_unique_hostname_per_context",
        "assets",
        ["client_account_id", "engagement_id", "hostname"],
        unique=True,
        postgresql_where=sa.text("hostname IS NOT NULL AND hostname != ''"),
    )
    create_index_if_not_exists(
        "ix_assets_unique_name_per_context",
        "assets",
        ["client_account_id", "engagement_id", "name"],
        unique=True,
        postgresql_where=sa.text("name IS NOT NULL AND name != ''"),
    )
    create_index_if_not_exists(
        "ix_assets_unique_ip_per_context",
        "assets",
        ["client_account_id", "engagement_id", "ip_address"],
        unique=True,
        postgresql_where=sa.text("ip_address IS NOT NULL AND ip_address != ''"),
    )

    # Check constraint - only create if table exists
    if table_exists("assets"):
        try:
            op.create_check_constraint(
                "ck_assets_has_identifier",
                "assets",
                sa.text(
                    "hostname IS NOT NULL OR name IS NOT NULL OR ip_address IS NOT NULL"
                ),
            )
        except Exception as e:
            print(
                f"Check constraint ck_assets_has_identifier already exists or error: {e}"
            )

    # Create migration_waves table
    create_table_if_not_exists(
        "migration_waves",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("wave_number", sa.INTEGER(), nullable=False),
        sa.Column("name", sa.VARCHAR(length=255), nullable=False),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column(
            "status", sa.VARCHAR(length=50), server_default="planned", nullable=True
        ),
        sa.Column("planned_start_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("planned_end_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("actual_start_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("actual_end_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "total_assets", sa.INTEGER(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column(
            "completed_assets", sa.INTEGER(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column(
            "failed_assets", sa.INTEGER(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column("estimated_cost", sa.FLOAT(), nullable=True),
        sa.Column("actual_cost", sa.FLOAT(), nullable=True),
        sa.Column("estimated_effort_hours", sa.FLOAT(), nullable=True),
        sa.Column("actual_effort_hours", sa.FLOAT(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_migration_waves_client_account_id_client_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
            name=op.f("fk_migration_waves_engagement_id_engagements"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_migration_waves_created_by_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_migration_waves")),
    )
    create_index_if_not_exists(
        op.f("ix_migration_waves_id"), "migration_waves", ["id"], unique=False
    )
    create_index_if_not_exists(
        op.f("ix_migration_waves_client_account_id"),
        "migration_waves",
        ["client_account_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_migration_waves_engagement_id"),
        "migration_waves",
        ["engagement_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_migration_waves_wave_number"),
        "migration_waves",
        ["wave_number"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_migration_waves_status"), "migration_waves", ["status"], unique=False
    )

    # Create assessment flow tables (from migration 003)
    create_table_if_not_exists(
        "assessment_flows",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("flow_name", sa.String(length=255), nullable=False),
        sa.Column("flow_status", sa.String(length=50), nullable=False),
        sa.Column("flow_configuration", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
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

    create_table_if_not_exists(
        "engagement_architecture_standards",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("requirement_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "mandatory", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "supported_versions", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "requirement_details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["engagements.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "application_architecture_overrides",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("assessment_flow_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("standard_id", sa.UUID(), nullable=True),
        sa.Column("override_type", sa.String(length=100), nullable=False),
        sa.Column(
            "override_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["assessment_flow_id"], ["assessment_flows.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["standard_id"],
            ["engagement_architecture_standards.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_index_if_not_exists(
        op.f("ix_application_architecture_overrides_assessment_flow_id"),
        "application_architecture_overrides",
        ["assessment_flow_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_application_architecture_overrides_application_id"),
        "application_architecture_overrides",
        ["application_id"],
        unique=False,
    )

    create_table_if_not_exists(
        "application_components",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("component_name", sa.String(length=255), nullable=False),
        sa.Column("component_type", sa.String(length=100), nullable=False),
        sa.Column("component_config", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "tech_debt_analysis",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("analysis_type", sa.String(length=100), nullable=False),
        sa.Column("analysis_results", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "component_treatments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("component_id", sa.UUID(), nullable=False),
        sa.Column("treatment_type", sa.String(length=100), nullable=False),
        sa.Column("treatment_config", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["component_id"],
            ["application_components.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "sixr_decisions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("decision_type", sa.String(length=100), nullable=False),
        sa.Column("decision_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "assessment_learning_feedback",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("feedback_type", sa.String(length=100), nullable=False),
        sa.Column("feedback_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # Drop assessment flow tables
    op.drop_table("assessment_learning_feedback")
    op.drop_table("sixr_decisions")
    op.drop_table("component_treatments")
    op.drop_table("tech_debt_analysis")
    op.drop_table("application_components")
    op.drop_table("application_architecture_overrides")
    op.drop_table("engagement_architecture_standards")
    op.drop_table("assessment_flows")

    # Drop asset constraints and indexes
    op.drop_constraint("ck_assets_has_identifier", "assets")
    op.drop_index("ix_assets_unique_ip_per_context", table_name="assets")
    op.drop_index("ix_assets_unique_name_per_context", table_name="assets")
    op.drop_index("ix_assets_unique_hostname_per_context", table_name="assets")
    op.drop_index("idx_assets_client_engagement_created", table_name="assets")
    op.drop_index("idx_assets_status", table_name="assets")
    op.drop_index("idx_assets_type", table_name="assets")
    op.drop_index("idx_assets_created_at_desc", table_name="assets")
    op.drop_index("idx_assets_client_engagement", table_name="assets")

    # Drop main tables
    op.drop_table("assets")

    # Drop migration_waves table
    op.drop_index(op.f("ix_migration_waves_status"), table_name="migration_waves")
    op.drop_index(op.f("ix_migration_waves_wave_number"), table_name="migration_waves")
    op.drop_index(
        op.f("ix_migration_waves_engagement_id"), table_name="migration_waves"
    )
    op.drop_index(
        op.f("ix_migration_waves_client_account_id"), table_name="migration_waves"
    )
    op.drop_index(op.f("ix_migration_waves_id"), table_name="migration_waves")
    op.drop_table("migration_waves")
    op.drop_table("assessments")
    op.drop_table("import_field_mappings")
    op.drop_table("raw_import_records")
    op.drop_table("data_imports")

    # Drop discovery_flows table
    op.drop_index(op.f("ix_discovery_flows_status"), table_name="discovery_flows")
    op.drop_index(
        op.f("ix_discovery_flows_data_import_id"), table_name="discovery_flows"
    )
    op.drop_index(
        op.f("ix_discovery_flows_engagement_id"), table_name="discovery_flows"
    )
    op.drop_index(
        op.f("ix_discovery_flows_client_account_id"), table_name="discovery_flows"
    )
    op.drop_index(
        op.f("ix_discovery_flows_master_flow_id"), table_name="discovery_flows"
    )
    op.drop_index(op.f("ix_discovery_flows_flow_id"), table_name="discovery_flows")
    op.drop_index(op.f("ix_discovery_flows_id"), table_name="discovery_flows")
    op.drop_table("discovery_flows")

    op.drop_table("crewai_flow_state_extensions")
    op.drop_table("client_access")

    # Drop engagement_access table
    op.drop_index(
        op.f("ix_engagement_access_is_active"), table_name="engagement_access"
    )
    op.drop_index(
        op.f("ix_engagement_access_engagement_id"), table_name="engagement_access"
    )
    op.drop_index(
        op.f("ix_engagement_access_user_profile_id"), table_name="engagement_access"
    )
    op.drop_index(op.f("ix_engagement_access_id"), table_name="engagement_access")
    op.drop_table("engagement_access")

    # Drop RBAC tables
    op.drop_index(
        op.f("ix_user_account_associations_client_account_id"),
        table_name="user_account_associations",
    )
    op.drop_index(
        op.f("ix_user_account_associations_user_id"),
        table_name="user_account_associations",
    )
    op.drop_table("user_account_associations")
    op.drop_index(op.f("ix_user_roles_is_active"), table_name="user_roles")
    op.drop_index(op.f("ix_user_roles_user_id"), table_name="user_roles")
    op.drop_index(op.f("ix_user_roles_id"), table_name="user_roles")
    op.drop_table("user_roles")

    # Drop core tables
    op.drop_table("user_profiles")
    op.drop_table("engagements")
    op.drop_table("users")
    op.drop_table("client_accounts")

    # Drop enums (conditionally)
    bind = op.get_bind()

    # Check if enum types exist and drop only if they do
    try:
        result = bind.execute(
            sa.text(
                """
            SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'risklevel')
        """
            )
        ).scalar()
        if result:
            sa.Enum(name="risklevel").drop(bind)
    except Exception:
        pass

    try:
        result = bind.execute(
            sa.text(
                """
            SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'assessmentstatus')
        """
            )
        ).scalar()
        if result:
            sa.Enum(name="assessmentstatus").drop(bind)
    except Exception:
        pass

    try:
        result = bind.execute(
            sa.text(
                """
            SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'assessmenttype')
        """
            )
        ).scalar()
        if result:
            sa.Enum(name="assessmenttype").drop(bind)
    except Exception:
        pass
