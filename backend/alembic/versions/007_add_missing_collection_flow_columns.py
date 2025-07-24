"""add missing collection flow columns

Revision ID: 007_add_missing_collection_flow_columns
Revises: 006_add_collection_flow_next_phase
Create Date: 2025-01-20

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "007_add_missing_collection_flow_columns"
down_revision = "006_add_collection_flow_next_phase"
branch_labels = None
depends_on = None


def upgrade():
    # Add only the missing columns to collection_flows table
    op.add_column(
        "collection_flows", sa.Column("pause_points", postgresql.JSONB, nullable=True)
    )
    op.add_column(
        "collection_flows", sa.Column("user_inputs", postgresql.JSONB, nullable=True)
    )
    op.add_column(
        "collection_flows", sa.Column("phase_results", postgresql.JSONB, nullable=True)
    )
    op.add_column(
        "collection_flows", sa.Column("agent_insights", postgresql.JSONB, nullable=True)
    )
    op.add_column(
        "collection_flows",
        sa.Column("collected_platforms", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "collection_flows",
        sa.Column("collection_results", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "collection_flows",
        sa.Column("gap_analysis_results", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "collection_flows",
        sa.Column(
            "assessment_ready", sa.Boolean(), nullable=True, server_default="false"
        ),
    )
    op.add_column(
        "collection_flows",
        sa.Column(
            "apps_ready_for_assessment", sa.Integer(), nullable=True, server_default="0"
        ),
    )
    op.add_column(
        "collection_flows",
        sa.Column("last_user_interaction", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "collection_flows",
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Note: error_message, error_details, confidence_score, collection_quality_score already exist
    # Note: progress_percentage already exists (was already renamed)


def downgrade():
    # Remove only the columns we added
    op.drop_column("collection_flows", "created_by")
    op.drop_column("collection_flows", "last_user_interaction")
    op.drop_column("collection_flows", "apps_ready_for_assessment")
    op.drop_column("collection_flows", "assessment_ready")
    op.drop_column("collection_flows", "gap_analysis_results")
    op.drop_column("collection_flows", "collection_results")
    op.drop_column("collection_flows", "collected_platforms")
    op.drop_column("collection_flows", "agent_insights")
    op.drop_column("collection_flows", "phase_results")
    op.drop_column("collection_flows", "user_inputs")
    op.drop_column("collection_flows", "pause_points")
