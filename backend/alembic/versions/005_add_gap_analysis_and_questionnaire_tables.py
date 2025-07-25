"""Add Gap Analysis and Adaptive Questionnaire tables for ADCS

Revision ID: 005_add_gap_analysis_and_questionnaire_tables
Revises: 004_add_platform_credentials_tables
Create Date: 2025-07-20

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "005_add_gap_analysis_and_questionnaire_tables"
down_revision = "004_add_platform_credentials_tables"
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
    """Check if an index exists on a table"""
    bind = op.get_bind()
    try:
        # Use parameterized query with proper escaping
        # Note: table_name and index_name are string literal values, not identifiers
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
        print(f"Error checking if index {index_name} exists on table {table_name}: {e}")
        # If we get an error, assume index exists to avoid trying to create it
        return True


def create_index_if_not_exists(index_name, table_name, columns, **kwargs):
    """Create an index only if it doesn't already exist"""
    if table_exists(table_name) and not index_exists(index_name, table_name):
        op.create_index(index_name, table_name, columns, **kwargs)
    else:
        print(
            f"Index {index_name} already exists or table doesn't exist, skipping creation"
        )


def upgrade() -> None:
    # Create collection_gap_analysis table
    create_table_if_not_exists(
        "collection_gap_analysis",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("collection_flow_id", sa.UUID(), nullable=False),
        sa.Column(
            "total_fields_required",
            sa.INTEGER(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "fields_collected",
            sa.INTEGER(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "fields_missing", sa.INTEGER(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "completeness_percentage",
            sa.DOUBLE_PRECISION(precision=53),
            server_default=sa.text("0.0"),
            nullable=False,
        ),
        sa.Column(
            "data_quality_score", sa.DOUBLE_PRECISION(precision=53), nullable=True
        ),
        sa.Column("confidence_level", sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column(
            "automation_coverage", sa.DOUBLE_PRECISION(precision=53), nullable=True
        ),
        sa.Column(
            "critical_gaps",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "optional_gaps",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "gap_categories",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "recommended_actions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "questionnaire_requirements",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "analyzed_at",
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
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_collection_gap_analysis_client_account_id_client_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
            name=op.f("fk_collection_gap_analysis_engagement_id_engagements"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["collection_flow_id"],
            ["collection_flows.id"],
            name=op.f("fk_collection_gap_analysis_collection_flow_id_collection_flows"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collection_gap_analysis")),
    )

    # Create indexes for collection_gap_analysis
    create_index_if_not_exists(
        op.f("ix_collection_gap_analysis_id"),
        "collection_gap_analysis",
        ["id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_gap_analysis_client_account_id"),
        "collection_gap_analysis",
        ["client_account_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_gap_analysis_engagement_id"),
        "collection_gap_analysis",
        ["engagement_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_collection_gap_analysis_collection_flow_id"),
        "collection_gap_analysis",
        ["collection_flow_id"],
        unique=False,
    )

    # Create adaptive_questionnaires table
    create_table_if_not_exists(
        "adaptive_questionnaires",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("engagement_id", sa.UUID(), nullable=False),
        sa.Column("template_name", sa.VARCHAR(length=255), nullable=False),
        sa.Column("template_type", sa.VARCHAR(length=100), nullable=False),
        sa.Column(
            "version", sa.VARCHAR(length=20), server_default="1.0", nullable=False
        ),
        sa.Column(
            "applicable_tiers",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "question_set", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "question_count", sa.INTEGER(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("estimated_completion_time", sa.INTEGER(), nullable=True),
        sa.Column(
            "gap_categories",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "platform_types",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "data_domains",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "scoring_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "validation_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "usage_count", sa.INTEGER(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("success_rate", sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column(
            "is_active", sa.BOOLEAN(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "is_template", sa.BOOLEAN(), server_default=sa.text("true"), nullable=False
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
            ["client_account_id"],
            ["client_accounts.id"],
            name=op.f("fk_adaptive_questionnaires_client_account_id_client_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["engagements.id"],
            name=op.f("fk_adaptive_questionnaires_engagement_id_engagements"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_adaptive_questionnaires")),
    )

    # Create indexes for adaptive_questionnaires
    create_index_if_not_exists(
        op.f("ix_adaptive_questionnaires_id"),
        "adaptive_questionnaires",
        ["id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_adaptive_questionnaires_client_account_id"),
        "adaptive_questionnaires",
        ["client_account_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_adaptive_questionnaires_engagement_id"),
        "adaptive_questionnaires",
        ["engagement_id"],
        unique=False,
    )
    create_index_if_not_exists(
        op.f("ix_adaptive_questionnaires_template_type"),
        "adaptive_questionnaires",
        ["template_type"],
        unique=False,
    )


def downgrade() -> None:
    # Drop adaptive_questionnaires indexes and table
    op.drop_index(
        op.f("ix_adaptive_questionnaires_template_type"),
        table_name="adaptive_questionnaires",
    )
    op.drop_index(
        op.f("ix_adaptive_questionnaires_engagement_id"),
        table_name="adaptive_questionnaires",
    )
    op.drop_index(
        op.f("ix_adaptive_questionnaires_client_account_id"),
        table_name="adaptive_questionnaires",
    )
    op.drop_index(
        op.f("ix_adaptive_questionnaires_id"), table_name="adaptive_questionnaires"
    )
    op.drop_table("adaptive_questionnaires")

    # Drop collection_gap_analysis indexes and table
    op.drop_index(
        op.f("ix_collection_gap_analysis_collection_flow_id"),
        table_name="collection_gap_analysis",
    )
    op.drop_index(
        op.f("ix_collection_gap_analysis_engagement_id"),
        table_name="collection_gap_analysis",
    )
    op.drop_index(
        op.f("ix_collection_gap_analysis_client_account_id"),
        table_name="collection_gap_analysis",
    )
    op.drop_index(
        op.f("ix_collection_gap_analysis_id"), table_name="collection_gap_analysis"
    )
    op.drop_table("collection_gap_analysis")
