"""Consolidated Schema Migration - Complete Database Setup

Revision ID: 001_consolidated_schema
Revises:
Create Date: 2025-06-30 10:00:00.000000

This migration creates the entire database schema from scratch with:
- No v3_* tables
- No 'is_mock' fields
- Proper field naming conventions (filename, file_size, mime_type)
- Hybrid state tracking in discovery_flows
- Master flow orchestration support
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "001_consolidated_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create complete consolidated schema."""

    # =============================================================================
    # ENUM TYPES
    # =============================================================================

    # Create asset_type enum
    op.execute(
        """
        CREATE TYPE asset_type AS ENUM (
            'server', 'database', 'application', 'network', 'load_balancer',
            'storage', 'security_group', 'virtual_machine', 'container', 'other'
        )
    """
    )

    # Create asset_status enum
    op.execute(
        """
        CREATE TYPE asset_status AS ENUM (
            'discovered', 'assessed', 'planned', 'migrating',
            'migrated', 'failed', 'excluded'
        )
    """
    )

    # Create sixr_strategy enum
    op.execute(
        """
        CREATE TYPE sixr_strategy AS ENUM (
            'rehost', 'replatform', 'refactor', 'rearchitect',
            'replace', 'repurchase', 'retire', 'retain'
        )
    """
    )

    # Create import_status enum
    op.execute(
        """
        CREATE TYPE import_status AS ENUM (
            'pending', 'uploading', 'uploaded', 'processing', 'validating',
            'processed', 'completed', 'failed', 'cancelled', 'archived'
        )
    """
    )

    # Create flow_status enum
    op.execute(
        """
        CREATE TYPE flow_status AS ENUM (
            'initialized', 'running', 'paused', 'completed',
            'failed', 'cancelled', 'pending'
        )
    """
    )

    # =============================================================================
    # CORE FOUNDATION TABLES
    # =============================================================================

    # Create client_accounts table
    op.create_table(
        "client_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_client_accounts_id"), "client_accounts", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_client_accounts_name"), "client_accounts", ["name"], unique=True
    )

    # Create users table (needed for foreign keys)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("full_name", sa.String(100), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "default_client_account_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "default_engagement_id", postgresql.UUID(as_uuid=True), nullable=True
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
            ["default_client_account_id"],
            ["client_accounts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    # Create engagements table
    op.create_table(
        "engagements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_engagements_client_account_id"),
        "engagements",
        ["client_account_id"],
        unique=False,
    )
    op.create_index(op.f("ix_engagements_id"), "engagements", ["id"], unique=False)
    op.create_index(op.f("ix_engagements_name"), "engagements", ["name"], unique=False)

    # Update users table with engagement foreign key
    op.add_column(
        "users",
        sa.Column(
            "default_engagement_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
    )
    op.create_foreign_key(
        "fk_users_default_engagement_id",
        "users",
        "engagements",
        ["default_engagement_id"],
        ["id"],
    )

    # =============================================================================
    # MASTER FLOW ARCHITECTURE
    # =============================================================================

    # Create crewai_flow_state_extensions table (master flow coordinator)
    op.create_table(
        "crewai_flow_state_extensions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("flow_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Multi-tenant fields
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        # Flow metadata
        sa.Column(
            "flow_type", sa.String(50), nullable=False, server_default="'discovery'"
        ),
        sa.Column("flow_name", sa.String(255), nullable=True),
        sa.Column(
            "flow_status", sa.String(50), nullable=False, server_default="'initialized'"
        ),
        sa.Column(
            "flow_configuration",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        # Master Flow Coordination Fields
        sa.Column("current_phase", sa.String(100), nullable=True),
        sa.Column("phase_flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "phase_progression",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "cross_phase_context",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        # Phase-specific flow IDs
        sa.Column("discovery_flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assessment_flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("planning_flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("execution_flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        # CrewAI Flow persistence data
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
        # Flow performance metrics
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
        # Flow metadata
        sa.Column(
            "flow_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        # Learning and adaptation data
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
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
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
        sa.UniqueConstraint("flow_id", name="uq_crewai_extensions_flow_id"),
    )

    # Create indexes for crewai_flow_state_extensions
    op.create_index(
        "idx_crewai_extensions_master_flow_id",
        "crewai_flow_state_extensions",
        ["flow_id"],
    )
    op.create_index(
        "idx_crewai_extensions_current_phase",
        "crewai_flow_state_extensions",
        ["current_phase"],
    )
    op.create_index(
        "idx_crewai_extensions_phase_flow_id",
        "crewai_flow_state_extensions",
        ["phase_flow_id"],
    )
    op.create_index(
        "ix_crewai_flow_state_extensions_client_account_id",
        "crewai_flow_state_extensions",
        ["client_account_id"],
    )
    op.create_index(
        "ix_crewai_flow_state_extensions_engagement_id",
        "crewai_flow_state_extensions",
        ["engagement_id"],
    )

    # =============================================================================
    # DISCOVERY FLOWS (Hybrid State Management)
    # =============================================================================

    # Create discovery_flows table
    op.create_table(
        "discovery_flows",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flow_id", sa.String(length=255), nullable=False),
        sa.Column("master_flow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_phase", sa.String(length=100), nullable=False),
        sa.Column(
            "progress_percentage", sa.Float(), nullable=False, server_default="0"
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        # CrewAI state management
        sa.Column("crewai_flow_state", sa.JSON(), nullable=True),
        sa.Column("crewai_persistence_id", sa.String(length=255), nullable=True),
        # Import reference
        sa.Column("import_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        # JSON fields for flexible state storage
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column("field_mappings", sa.JSON(), nullable=True),
        sa.Column("cleaned_data", sa.JSON(), nullable=True),
        sa.Column("asset_inventory", sa.JSON(), nullable=True),
        sa.Column("dependencies", sa.JSON(), nullable=True),
        sa.Column("tech_debt", sa.JSON(), nullable=True),
        # Boolean completion flags for hybrid tracking
        sa.Column(
            "data_import_completed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "attribute_mapping_completed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "data_cleansing_completed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "inventory_completed", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "dependencies_completed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "tech_debt_completed", sa.Boolean(), nullable=False, server_default="false"
        ),
        # Crew and agent tracking
        sa.Column("crew_status", sa.JSON(), nullable=True),
        sa.Column("agent_insights", sa.JSON(), nullable=True),
        sa.Column("crew_performance_metrics", sa.JSON(), nullable=True),
        # Learning and memory configuration
        sa.Column(
            "learning_scope",
            sa.String(length=50),
            nullable=False,
            server_default="'engagement'",
        ),
        sa.Column(
            "memory_isolation_level",
            sa.String(length=20),
            nullable=False,
            server_default="'engagement'",
        ),
        sa.Column("shared_memory_refs", sa.JSON(), nullable=True),
        sa.Column("knowledge_base_refs", sa.JSON(), nullable=True),
        # Error and warning tracking
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=True),
        sa.Column("workflow_log", sa.JSON(), nullable=True),
        # Assessment readiness
        sa.Column(
            "assessment_ready", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("assessment_package", sa.JSON(), nullable=True),
        # Timestamps
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for discovery_flows
    op.create_index(
        op.f("ix_discovery_flows_client_account_id"),
        "discovery_flows",
        ["client_account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_discovery_flows_crewai_persistence_id"),
        "discovery_flows",
        ["crewai_persistence_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_discovery_flows_engagement_id"),
        "discovery_flows",
        ["engagement_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_discovery_flows_flow_id"), "discovery_flows", ["flow_id"], unique=True
    )
    op.create_index(
        op.f("ix_discovery_flows_import_session_id"),
        "discovery_flows",
        ["import_session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_discovery_flows_user_id"), "discovery_flows", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_discovery_flows_status"), "discovery_flows", ["status"], unique=False
    )
    op.create_index(
        "idx_discovery_flows_master_flow_id", "discovery_flows", ["master_flow_id"]
    )

    # =============================================================================
    # MIGRATION MANAGEMENT
    # =============================================================================

    # Create migrations table
    op.create_table(
        "migrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="'planning'"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
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
            ["client_account_id"],
            ["client_accounts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_migrations_id"), "migrations", ["id"], unique=False)
    op.create_index(
        op.f("ix_migrations_client_account_id"),
        "migrations",
        ["client_account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_migrations_engagement_id"),
        "migrations",
        ["engagement_id"],
        unique=False,
    )

    # =============================================================================
    # DATA IMPORT SESSIONS
    # =============================================================================

    # Create data_import_sessions table
    op.create_table(
        "data_import_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_name", sa.String(255), nullable=False),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="'active'"),
        sa.Column("total_imports", sa.Integer(), nullable=True, server_default="0"),
        sa.Column(
            "successful_imports", sa.Integer(), nullable=True, server_default="0"
        ),
        sa.Column("failed_imports", sa.Integer(), nullable=True, server_default="0"),
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
            ["client_account_id"],
            ["client_accounts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_data_import_sessions_id"), "data_import_sessions", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_data_import_sessions_client_account_id"),
        "data_import_sessions",
        ["client_account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_data_import_sessions_engagement_id"),
        "data_import_sessions",
        ["engagement_id"],
        unique=False,
    )

    # =============================================================================
    # ASSETS TABLE (Complete Infrastructure and Business Fields)
    # =============================================================================

    # Create assets table
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("asset_name", sa.String(255), nullable=True),
        sa.Column("hostname", sa.String(255), nullable=True),
        sa.Column(
            "asset_type",
            sa.Enum(
                "server",
                "database",
                "application",
                "network",
                "load_balancer",
                "storage",
                "security_group",
                "virtual_machine",
                "container",
                "other",
                name="asset_type",
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Multi-tenant isolation
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Flow tracking
        sa.Column("flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("migration_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Master Flow Coordination
        sa.Column("master_flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("discovery_flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assessment_flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("planning_flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("execution_flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "source_phase", sa.String(50), nullable=True, server_default="'discovery'"
        ),
        sa.Column(
            "current_phase", sa.String(50), nullable=True, server_default="'discovery'"
        ),
        sa.Column(
            "phase_progression",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        # Network information
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("fqdn", sa.String(255), nullable=True),
        sa.Column("mac_address", sa.String(17), nullable=True),
        # Location and environment
        sa.Column("environment", sa.String(50), nullable=True),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column("datacenter", sa.String(100), nullable=True),
        sa.Column("rack_location", sa.String(50), nullable=True),
        sa.Column("availability_zone", sa.String(50), nullable=True),
        # Technical specifications
        sa.Column("operating_system", sa.String(100), nullable=True),
        sa.Column("os_version", sa.String(50), nullable=True),
        sa.Column("cpu_cores", sa.Integer(), nullable=True),
        sa.Column("memory_gb", sa.Float(), nullable=True),
        sa.Column("storage_gb", sa.Float(), nullable=True),
        # Business information
        sa.Column("business_owner", sa.String(255), nullable=True),
        sa.Column("technical_owner", sa.String(255), nullable=True),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("application_name", sa.String(255), nullable=True),
        sa.Column("technology_stack", sa.String(255), nullable=True),
        sa.Column("criticality", sa.String(20), nullable=True),
        sa.Column("business_criticality", sa.String(20), nullable=True),
        sa.Column(
            "custom_attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        # Migration assessment
        sa.Column(
            "six_r_strategy",
            sa.Enum(
                "rehost",
                "replatform",
                "refactor",
                "rearchitect",
                "replace",
                "repurchase",
                "retire",
                "retain",
                name="sixr_strategy",
            ),
            nullable=True,
        ),
        sa.Column("mapping_status", sa.String(20), nullable=True),
        sa.Column(
            "migration_priority", sa.Integer(), nullable=True, server_default="5"
        ),
        sa.Column("migration_complexity", sa.String(20), nullable=True),
        sa.Column("migration_wave", sa.Integer(), nullable=True),
        sa.Column("sixr_ready", sa.String(50), nullable=True),
        # Status fields
        sa.Column("status", sa.String(50), nullable=True, server_default="'active'"),
        sa.Column(
            "migration_status",
            sa.Enum(
                "discovered",
                "assessed",
                "planned",
                "migrating",
                "migrated",
                "failed",
                "excluded",
                name="asset_status",
            ),
            nullable=True,
            server_default="'discovered'",
        ),
        # Dependencies and relationships
        sa.Column(
            "dependencies", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "related_assets", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        # Discovery metadata
        sa.Column("discovery_method", sa.String(50), nullable=True),
        sa.Column("discovery_source", sa.String(100), nullable=True),
        sa.Column("discovery_timestamp", sa.DateTime(timezone=True), nullable=True),
        # Performance metrics
        sa.Column("cpu_utilization_percent", sa.Float(), nullable=True),
        sa.Column("memory_utilization_percent", sa.Float(), nullable=True),
        sa.Column("disk_iops", sa.Float(), nullable=True),
        sa.Column("network_throughput_mbps", sa.Float(), nullable=True),
        # Data quality
        sa.Column("completeness_score", sa.Float(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        # Cost information
        sa.Column("current_monthly_cost", sa.Float(), nullable=True),
        sa.Column("estimated_cloud_cost", sa.Float(), nullable=True),
        # Import metadata
        sa.Column("imported_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_filename", sa.String(255), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "field_mappings_used",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["client_accounts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
        ),
        sa.ForeignKeyConstraint(
            ["imported_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["master_flow_id"],
            ["crewai_flow_state_extensions.flow_id"],
        ),
        sa.ForeignKeyConstraint(
            ["migration_id"],
            ["migrations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["data_import_sessions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for assets
    op.create_index(
        op.f("ix_assets_client_account_id"),
        "assets",
        ["client_account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assets_engagement_id"), "assets", ["engagement_id"], unique=False
    )
    op.create_index(op.f("ix_assets_id"), "assets", ["id"], unique=False)
    op.create_index(op.f("ix_assets_name"), "assets", ["name"], unique=False)
    op.create_index(op.f("ix_assets_flow_id"), "assets", ["flow_id"], unique=False)
    op.create_index("idx_assets_master_flow_id", "assets", ["master_flow_id"])
    op.create_index("idx_assets_source_phase", "assets", ["source_phase"])
    op.create_index("idx_assets_current_phase", "assets", ["current_phase"])
    op.create_index("idx_assets_discovery_flow_id", "assets", ["discovery_flow_id"])

    # =============================================================================
    # DATA IMPORTS TABLE
    # =============================================================================

    # Create data_imports table
    op.create_table(
        "data_imports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "filename", sa.String(), nullable=False
        ),  # Using 'filename' not 'source_filename'
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "uploading",
                "uploaded",
                "processing",
                "validating",
                "processed",
                "completed",
                "failed",
                "cancelled",
                "archived",
                name="import_status",
            ),
            nullable=False,
        ),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("master_flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column(
            "file_size", sa.Integer(), nullable=True
        ),  # Using 'file_size' not 'file_size_bytes'
        sa.Column(
            "mime_type", sa.String(), nullable=True
        ),  # Using 'mime_type' not 'file_type'
        sa.Column("total_rows", sa.Integer(), nullable=True),
        sa.Column("processed_rows", sa.Integer(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=True),
        sa.Column(
            "validation_results", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "field_mappings", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "processing_log", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "agent_insights", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
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

    # Create indexes for data_imports
    op.create_index(
        op.f("ix_data_imports_client_account_id"),
        "data_imports",
        ["client_account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_data_imports_engagement_id"),
        "data_imports",
        ["engagement_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_data_imports_filename"), "data_imports", ["filename"], unique=False
    )
    op.create_index(op.f("ix_data_imports_id"), "data_imports", ["id"], unique=False)
    op.create_index(
        op.f("ix_data_imports_status"), "data_imports", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_data_imports_user_id"), "data_imports", ["user_id"], unique=False
    )
    op.create_index(
        "idx_data_imports_master_flow_id", "data_imports", ["master_flow_id"]
    )

    # =============================================================================
    # SUPPORTING TABLES
    # =============================================================================

    # Create asset_dependencies table
    op.create_table(
        "asset_dependencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("depends_on_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dependency_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["depends_on_asset_id"], ["assets.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_asset_dependencies_asset_id",
        "asset_dependencies",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        "ix_asset_dependencies_depends_on_asset_id",
        "asset_dependencies",
        ["depends_on_asset_id"],
        unique=False,
    )

    # Create import_field_mappings table
    op.create_table(
        "import_field_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("master_flow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_field", sa.String(), nullable=False),
        sa.Column("target_field", sa.String(), nullable=False),
        sa.Column("mapping_confidence", sa.Float(), nullable=True),
        sa.Column(
            "validation_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["master_flow_id"],
            ["crewai_flow_state_extensions.flow_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_import_field_mappings_master_flow_id",
        "import_field_mappings",
        ["master_flow_id"],
    )

    # Create raw_import_records table
    op.create_table(
        "raw_import_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("master_flow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("validation_status", sa.String(), nullable=False),
        sa.Column(
            "validation_errors", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "processed_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["master_flow_id"],
            ["crewai_flow_state_extensions.flow_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_raw_import_records_master_flow_id",
        "raw_import_records",
        ["master_flow_id"],
    )

    # Create migration_waves table
    op.create_table(
        "migration_waves",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("wave_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=True, server_default="'planned'"),
        sa.Column("planned_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_assets", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("completed_assets", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("failed_assets", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("actual_cost", sa.Float(), nullable=True),
        sa.Column("estimated_effort_hours", sa.Float(), nullable=True),
        sa.Column("actual_effort_hours", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_account_id"], ["client_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["engagements.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_migration_waves_client_account_id",
        "migration_waves",
        ["client_account_id"],
        unique=False,
    )
    op.create_index(
        "ix_migration_waves_engagement_id",
        "migration_waves",
        ["engagement_id"],
        unique=False,
    )
    op.create_index(
        "ix_migration_waves_wave_number",
        "migration_waves",
        ["wave_number"],
        unique=False,
    )

    # Create cmdb_sixr_analyses table
    op.create_table(
        "cmdb_sixr_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(50), nullable=True, server_default="'in_progress'"
        ),
        sa.Column("total_assets", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("rehost_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("replatform_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("refactor_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("rearchitect_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("retire_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("retain_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("total_current_cost", sa.Float(), nullable=True),
        sa.Column("total_estimated_cost", sa.Float(), nullable=True),
        sa.Column("potential_savings", sa.Float(), nullable=True),
        sa.Column(
            "analysis_results", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_account_id"], ["client_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["engagements.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cmdb_sixr_analyses_client_account_id",
        "cmdb_sixr_analyses",
        ["client_account_id"],
        unique=False,
    )
    op.create_index(
        "ix_cmdb_sixr_analyses_engagement_id",
        "cmdb_sixr_analyses",
        ["engagement_id"],
        unique=False,
    )

    # =============================================================================
    # SECURITY AND AUDIT TABLES
    # =============================================================================

    # Create security_audit_logs table
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

    # Create access_audit_log table
    op.create_table(
        "access_audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
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
    # LLM USAGE TRACKING
    # =============================================================================

    # Create llm_usage_tracking table
    op.create_table(
        "llm_usage_tracking",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_name", sa.String(100), nullable=True),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("endpoint", sa.String(200), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for llm_usage_tracking
    op.create_index("ix_llm_usage_tracking_user_id", "llm_usage_tracking", ["user_id"])
    op.create_index(
        "ix_llm_usage_tracking_client_account_id",
        "llm_usage_tracking",
        ["client_account_id"],
    )
    op.create_index(
        "ix_llm_usage_tracking_agent_name", "llm_usage_tracking", ["agent_name"]
    )
    op.create_index(
        "ix_llm_usage_tracking_created_at", "llm_usage_tracking", ["created_at"]
    )

    # =============================================================================
    # FEEDBACK AND LEARNING
    # =============================================================================

    # Create user_feedback table
    op.create_table(
        "user_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("flow_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("feedback_type", sa.String(50), nullable=False),
        sa.Column("context", sa.String(100), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("is_positive", sa.Boolean(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for user_feedback
    op.create_index("ix_user_feedback_user_id", "user_feedback", ["user_id"])
    op.create_index(
        "ix_user_feedback_client_account_id", "user_feedback", ["client_account_id"]
    )
    op.create_index("ix_user_feedback_flow_id", "user_feedback", ["flow_id"])
    op.create_index("ix_user_feedback_created_at", "user_feedback", ["created_at"])

    print("✅ Consolidated schema migration completed successfully!")
    print("✅ All tables, enums, and indexes created")
    print("✅ Multi-tenant isolation configured")
    print("✅ Master flow orchestration ready")
    print("✅ No v3_* tables or is_mock fields included")


def downgrade():
    """Drop all tables and enums in reverse order."""

    # Drop tables in reverse dependency order
    op.drop_table("user_feedback")
    op.drop_table("llm_usage_tracking")
    op.drop_table("access_audit_log")
    op.drop_table("security_audit_logs")
    op.drop_table("cmdb_sixr_analyses")
    op.drop_table("migration_waves")
    op.drop_table("raw_import_records")
    op.drop_table("import_field_mappings")
    op.drop_table("asset_dependencies")
    op.drop_table("data_imports")
    op.drop_table("assets")
    op.drop_table("data_import_sessions")
    op.drop_table("migrations")
    op.drop_table("discovery_flows")
    op.drop_table("crewai_flow_state_extensions")
    op.drop_table("engagements")
    op.drop_table("users")
    op.drop_table("client_accounts")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS flow_status")
    op.execute("DROP TYPE IF EXISTS import_status")
    op.execute("DROP TYPE IF EXISTS sixr_strategy")
    op.execute("DROP TYPE IF EXISTS asset_status")
    op.execute("DROP TYPE IF EXISTS asset_type")
