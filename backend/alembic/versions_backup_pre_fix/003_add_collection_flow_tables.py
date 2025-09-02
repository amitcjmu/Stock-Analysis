"""Add Collection Flow tables for ADCS

Revision ID: 003_add_collection_flow_tables
Revises: 002_add_security_audit_tables
Create Date: 2025-07-19

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "003_add_collection_flow_tables"
down_revision = "002_add_security_audit_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create automation tier enum if it doesn't exist
    bind = op.get_bind()
    result = bind.execute(
        sa.text("SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'automationtier')")
    ).scalar()
    if not result:
        sa.Enum("tier_1", "tier_2", "tier_3", "tier_4", name="automationtier").create(
            bind
        )

    # Create collection flow status enum if it doesn't exist
    result = bind.execute(
        sa.text(
            "SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'collectionflowstatus')"
        )
    ).scalar()
    if not result:
        sa.Enum(
            "initialized",
            "platform_detection",
            "automated_collection",
            "gap_analysis",
            "manual_collection",
            "completed",
            "failed",
            "cancelled",
            name="collectionflowstatus",
        ).create(bind)

    # Create adapter status enum if it doesn't exist
    result = bind.execute(
        sa.text("SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'adapterstatus')")
    ).scalar()
    if not result:
        sa.Enum(
            "active", "inactive", "error", "deprecated", name="adapterstatus"
        ).create(bind)

    # Helper functions
    def table_exists(table_name):
        """Check if a table exists in the database"""
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

    # Create collection_flows table (A1.1)
    create_table_if_not_exists(
        "collection_flows",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("flow_id", sa.UUID(), nullable=False),
        sa.Column("master_flow_id", sa.UUID(), nullable=True),
        sa.Column("discovery_flow_id", sa.UUID(), nullable=True),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("flow_name", sa.VARCHAR(length=255), nullable=False),
        sa.Column(
            "automation_tier",
            postgresql.ENUM(
                "tier_1",
                "tier_2",
                "tier_3",
                "tier_4",
                name="automationtier",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "initialized",
                "platform_detection",
                "automated_collection",
                "gap_analysis",
                "manual_collection",
                "completed",
                "failed",
                "cancelled",
                name="collectionflowstatus",
                create_type=False,
            ),
            server_default="initialized",
            nullable=False,
        ),
        sa.Column("current_phase", sa.VARCHAR(length=100), nullable=True),
        sa.Column(
            "progress_percentage",
            sa.DOUBLE_PRECISION(precision=53),
            server_default=sa.text("0.0"),
            nullable=False,
        ),
        sa.Column(
            "collection_quality_score", sa.DOUBLE_PRECISION(precision=53), nullable=True
        ),
        sa.Column("confidence_score", sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "collection_config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "phase_state",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("error_message", sa.TEXT(), nullable=True),
        sa.Column(
            "error_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True
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
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_collection_flows_client_account_id_client_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["discovery_flow_id"],
            ["discovery_flows.id"],
            name=op.f("fk_collection_flows_discovery_flow_id_discovery_flows"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
            name=op.f("fk_collection_flows_engagement_id_engagements"),
        ),
        sa.ForeignKeyConstraint(
            ["master_flow_id"],
            ["crewai_flow_state_extensions.flow_id"],
            name=op.f(
                "fk_collection_flows_master_flow_id_crewai_flow_state_extensions"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_collection_flows_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collection_flows")),
        sa.UniqueConstraint("flow_id", name=op.f("uq_collection_flows_flow_id")),
    )
    create_index_if_not_exists(
        op.f("ix_collection_flows_id"), "collection_flows", ["id"], unique=False
    )
    create_index_if_not_exists(
        op.f("ix_collection_flows_flow_id"),
        "collection_flows",
        ["flow_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_flows_master_flow_id"),
        "collection_flows",
        ["master_flow_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_flows_client_account_id"),
        "collection_flows",
        ["client_account_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_flows_engagement_id"),
        "collection_flows",
        ["engagement_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_flows_status"), "collection_flows", ["status"], unique=False
    )
    create_index_if_not_exists(
        op.f("ix_collection_flows_automation_tier"),
        "collection_flows",
        ["automation_tier"],
        unique=False,
    )

    # Create platform_adapters table (A1.2)
    create_table_if_not_exists(
        "platform_adapters",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("adapter_name", sa.VARCHAR(length=100), nullable=False),
        sa.Column("adapter_type", sa.VARCHAR(length=50), nullable=False),
        sa.Column("version", sa.VARCHAR(length=20), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active",
                "inactive",
                "error",
                "deprecated",
                name="adapterstatus",
                create_type=False,
            ),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "capabilities",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "configuration_schema",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "supported_platforms",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "required_credentials",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_platform_adapters")),
        sa.UniqueConstraint("adapter_name", "version", name="_adapter_name_version_uc"),
    )
    create_index_if_not_exists(
        op.f("ix_platform_adapters_adapter_name"),
        "platform_adapters",
        ["adapter_name"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_platform_adapters_adapter_type"),
        "platform_adapters",
        ["adapter_type"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_platform_adapters_status"),
        "platform_adapters",
        ["status"],
        unique=False,
    )

    # Create collected_data_inventory table (A1.2)
    create_table_if_not_exists(
        "collected_data_inventory",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("collection_flow_id", sa.UUID(), nullable=False),
        sa.Column("adapter_id", sa.UUID(), nullable=True),
        sa.Column("platform", sa.VARCHAR(length=50), nullable=False),
        sa.Column("collection_method", sa.VARCHAR(length=50), nullable=False),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "normalized_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("data_type", sa.VARCHAR(length=100), nullable=False),
        sa.Column(
            "resource_count", sa.INTEGER(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("quality_score", sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column(
            "validation_status",
            sa.VARCHAR(length=20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "validation_errors", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "collected_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["adapter_id"],
            ["platform_adapters.id"],
            name=op.f("fk_collected_data_inventory_adapter_id_platform_adapters"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["collection_flow_id"],
            ["collection_flows.id"],
            name=op.f(
                "fk_collected_data_inventory_collection_flow_id_collection_flows"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collected_data_inventory")),
    )
    create_index_if_not_exists(
        op.f("ix_collected_data_inventory_collection_flow_id"),
        "collected_data_inventory",
        ["collection_flow_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collected_data_inventory_platform"),
        "collected_data_inventory",
        ["platform"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collected_data_inventory_data_type"),
        "collected_data_inventory",
        ["data_type"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collected_data_inventory_validation_status"),
        "collected_data_inventory",
        ["validation_status"],
        unique=False,
    )

    # Create collection_data_gaps table (A1.2)
    create_table_if_not_exists(
        "collection_data_gaps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("collection_flow_id", sa.UUID(), nullable=False),
        sa.Column("gap_type", sa.VARCHAR(length=100), nullable=False),
        sa.Column("gap_category", sa.VARCHAR(length=50), nullable=False),
        sa.Column("field_name", sa.VARCHAR(length=255), nullable=False),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("impact_on_sixr", sa.VARCHAR(length=20), nullable=False),
        sa.Column(
            "priority", sa.INTEGER(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("suggested_resolution", sa.TEXT(), nullable=True),
        sa.Column(
            "resolution_status",
            sa.VARCHAR(length=20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.VARCHAR(length=50), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["collection_flow_id"],
            ["collection_flows.id"],
            name=op.f("fk_collection_data_gaps_collection_flow_id_collection_flows"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collection_data_gaps")),
    )
    create_index_if_not_exists(
        op.f("ix_collection_data_gaps_collection_flow_id"),
        "collection_data_gaps",
        ["collection_flow_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_data_gaps_gap_type"),
        "collection_data_gaps",
        ["gap_type"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_data_gaps_gap_category"),
        "collection_data_gaps",
        ["gap_category"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_data_gaps_resolution_status"),
        "collection_data_gaps",
        ["resolution_status"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_data_gaps_priority"),
        "collection_data_gaps",
        ["priority"],
        unique=False,
    )

    # Create collection_questionnaire_responses table (A1.2)
    create_table_if_not_exists(
        "collection_questionnaire_responses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("collection_flow_id", sa.UUID(), nullable=False),
        sa.Column("gap_id", sa.UUID(), nullable=True),
        sa.Column("questionnaire_type", sa.VARCHAR(length=50), nullable=False),
        sa.Column("question_category", sa.VARCHAR(length=50), nullable=False),
        sa.Column("question_id", sa.VARCHAR(length=100), nullable=False),
        sa.Column("question_text", sa.TEXT(), nullable=False),
        sa.Column("response_type", sa.VARCHAR(length=50), nullable=False),
        sa.Column(
            "response_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("confidence_score", sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column(
            "validation_status",
            sa.VARCHAR(length=20),
            server_default="pending",
            nullable=True,
        ),
        sa.Column("responded_by", sa.UUID(), nullable=True),
        sa.Column("responded_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
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
        sa.ForeignKeyConstraint(
            ["collection_flow_id"],
            ["collection_flows.id"],
            name=op.f(
                "fk_collection_questionnaire_responses_collection_flow_id_collection_flows"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["gap_id"],
            ["collection_data_gaps.id"],
            name=op.f(
                "fk_collection_questionnaire_responses_gap_id_collection_data_gaps"
            ),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["responded_by"],
            ["users.id"],
            name=op.f("fk_collection_questionnaire_responses_responded_by_users"),
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("pk_collection_questionnaire_responses")
        ),
    )
    create_index_if_not_exists(
        op.f("ix_collection_questionnaire_responses_collection_flow_id"),
        "collection_questionnaire_responses",
        ["collection_flow_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_questionnaire_responses_gap_id"),
        "collection_questionnaire_responses",
        ["gap_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_questionnaire_responses_questionnaire_type"),
        "collection_questionnaire_responses",
        ["questionnaire_type"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_questionnaire_responses_question_category"),
        "collection_questionnaire_responses",
        ["question_category"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_questionnaire_responses_validation_status"),
        "collection_questionnaire_responses",
        ["validation_status"],
        unique=False,
    )

    # Helper function to check if column exists
    def column_exists(table_name, column_name):
        """Check if a column exists in a table"""
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = 'migration'
                    AND table_name = :table_name
                    AND column_name = :column_name
                )
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        ).scalar()
        return result

    # Add Collection Flow reference to crewai_flow_state_extensions (A1.3)
    if table_exists("crewai_flow_state_extensions"):
        if not column_exists("crewai_flow_state_extensions", "collection_flow_id"):
            op.add_column(
                "crewai_flow_state_extensions",
                sa.Column("collection_flow_id", sa.UUID(), nullable=True),
            )
        if not column_exists("crewai_flow_state_extensions", "automation_tier"):
            op.add_column(
                "crewai_flow_state_extensions",
                sa.Column("automation_tier", sa.VARCHAR(length=20), nullable=True),
            )
        if not column_exists(
            "crewai_flow_state_extensions", "collection_quality_score"
        ):
            op.add_column(
                "crewai_flow_state_extensions",
                sa.Column(
                    "collection_quality_score",
                    sa.DOUBLE_PRECISION(precision=53),
                    nullable=True,
                ),
            )
        if not column_exists(
            "crewai_flow_state_extensions", "data_collection_metadata"
        ):
            op.add_column(
                "crewai_flow_state_extensions",
                sa.Column(
                    "data_collection_metadata",
                    postgresql.JSONB(astext_type=sa.Text()),
                    server_default=sa.text("'{}'::jsonb"),
                    nullable=True,
                ),
            )

    # Helper function to check if foreign key exists
    def foreign_key_exists(constraint_name, table_name):
        """Check if a foreign key constraint exists"""
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.table_constraints
                    WHERE table_schema = 'migration'
            AND constraint_schema = 'migration'
                    AND table_name = :table_name
                    AND constraint_name = :constraint_name
                    AND constraint_type = 'FOREIGN KEY'
                )
                """
            ),
            {"table_name": table_name, "constraint_name": constraint_name},
        ).scalar()
        return result

    # Add foreign key constraint for collection_flow_id
    if table_exists("crewai_flow_state_extensions") and table_exists(
        "collection_flows"
    ):
        constraint_name = "fk_crewai_flow_ext_collection_flow_id"
        if not foreign_key_exists(constraint_name, "crewai_flow_state_extensions"):
            op.create_foreign_key(
                op.f(constraint_name),
                "crewai_flow_state_extensions",
                "collection_flows",
                ["collection_flow_id"],
                ["id"],
                ondelete="SET NULL",
            )

    # Add indexes for new columns (A1.4)
    create_index_if_not_exists(
        op.f("ix_crewai_flow_state_extensions_collection_flow_id"),
        "crewai_flow_state_extensions",
        ["collection_flow_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_crewai_flow_state_extensions_automation_tier"),
        "crewai_flow_state_extensions",
        ["automation_tier"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes from crewai_flow_state_extensions
    op.drop_index(
        op.f("ix_crewai_flow_state_extensions_automation_tier"),
        table_name="crewai_flow_state_extensions",
    )
    op.drop_index(
        op.f("ix_crewai_flow_state_extensions_collection_flow_id"),
        table_name="crewai_flow_state_extensions",
    )

    # Drop foreign key and columns from crewai_flow_state_extensions
    op.drop_constraint(
        op.f("fk_crewai_flow_ext_collection_flow_id"),
        "crewai_flow_state_extensions",
        type_="foreignkey",
    )
    op.drop_column("crewai_flow_state_extensions", "data_collection_metadata")
    op.drop_column("crewai_flow_state_extensions", "collection_quality_score")
    op.drop_column("crewai_flow_state_extensions", "automation_tier")
    op.drop_column("crewai_flow_state_extensions", "collection_flow_id")

    # Drop collection_questionnaire_responses indexes and table
    op.drop_index(
        op.f("ix_collection_questionnaire_responses_validation_status"),
        table_name="collection_questionnaire_responses",
    )
    op.drop_index(
        op.f("ix_collection_questionnaire_responses_question_category"),
        table_name="collection_questionnaire_responses",
    )
    op.drop_index(
        op.f("ix_collection_questionnaire_responses_questionnaire_type"),
        table_name="collection_questionnaire_responses",
    )
    op.drop_index(
        op.f("ix_collection_questionnaire_responses_gap_id"),
        table_name="collection_questionnaire_responses",
    )
    op.drop_index(
        op.f("ix_collection_questionnaire_responses_collection_flow_id"),
        table_name="collection_questionnaire_responses",
    )
    op.drop_table("collection_questionnaire_responses")

    # Drop collection_data_gaps indexes and table
    op.drop_index(
        op.f("ix_collection_data_gaps_priority"), table_name="collection_data_gaps"
    )
    op.drop_index(
        op.f("ix_collection_data_gaps_resolution_status"),
        table_name="collection_data_gaps",
    )
    op.drop_index(
        op.f("ix_collection_data_gaps_gap_category"), table_name="collection_data_gaps"
    )
    op.drop_index(
        op.f("ix_collection_data_gaps_gap_type"), table_name="collection_data_gaps"
    )
    op.drop_index(
        op.f("ix_collection_data_gaps_collection_flow_id"),
        table_name="collection_data_gaps",
    )
    op.drop_table("collection_data_gaps")

    # Drop collected_data_inventory indexes and table
    op.drop_index(
        op.f("ix_collected_data_inventory_validation_status"),
        table_name="collected_data_inventory",
    )
    op.drop_index(
        op.f("ix_collected_data_inventory_data_type"),
        table_name="collected_data_inventory",
    )
    op.drop_index(
        op.f("ix_collected_data_inventory_platform"),
        table_name="collected_data_inventory",
    )
    op.drop_index(
        op.f("ix_collected_data_inventory_collection_flow_id"),
        table_name="collected_data_inventory",
    )
    op.drop_table("collected_data_inventory")

    # Drop platform_adapters indexes and table
    op.drop_index(op.f("ix_platform_adapters_status"), table_name="platform_adapters")
    op.drop_index(
        op.f("ix_platform_adapters_adapter_type"), table_name="platform_adapters"
    )
    op.drop_index(
        op.f("ix_platform_adapters_adapter_name"), table_name="platform_adapters"
    )
    op.drop_table("platform_adapters")

    # Drop collection_flows indexes and table
    op.drop_index(
        op.f("ix_collection_flows_automation_tier"), table_name="collection_flows"
    )
    op.drop_index(op.f("ix_collection_flows_status"), table_name="collection_flows")
    op.drop_index(
        op.f("ix_collection_flows_engagement_id"), table_name="collection_flows"
    )
    op.drop_index(
        op.f("ix_collection_flows_client_account_id"), table_name="collection_flows"
    )
    op.drop_index(
        op.f("ix_collection_flows_master_flow_id"), table_name="collection_flows"
    )
    op.drop_index(op.f("ix_collection_flows_flow_id"), table_name="collection_flows")
    op.drop_index(op.f("ix_collection_flows_id"), table_name="collection_flows")
    op.drop_table("collection_flows")

    # Drop enums
    sa.Enum(name="adapterstatus").drop(op.get_bind())
    sa.Enum(name="collectionflowstatus").drop(op.get_bind())
    sa.Enum(name="automationtier").drop(op.get_bind())
