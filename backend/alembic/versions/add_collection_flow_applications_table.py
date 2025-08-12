"""Add collection_flow_applications table for Discovery to Collection bridge

Revision ID: add_collection_apps_001
Revises: fcacece8fa7b
Create Date: 2025-08-12 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_collection_apps_001"
down_revision = "fcacece8fa7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create collection_flow_applications table to track selected applications for collection"""

    # Create the collection_flow_applications table
    # Note: Using asset_id instead of application_id since applications table doesn't exist yet
    op.create_table(
        "collection_flow_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("collection_flow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "asset_id", postgresql.UUID(as_uuid=True), nullable=True
        ),  # Made nullable as it might not always have an asset
        sa.Column(
            "application_name", sa.String(255), nullable=False
        ),  # Store app name directly
        sa.Column(
            "discovery_data_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "gap_analysis_result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "collection_status", sa.String(50), nullable=False, server_default="pending"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"], ["migration.assets.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["collection_flow_id"],
            ["migration.collection_flows.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="migration",
    )

    # Create indexes for performance
    op.create_index(
        "idx_collection_flow_apps",
        "collection_flow_applications",
        ["collection_flow_id", "application_name"],
        unique=False,  # Not unique since we're tracking by name
        schema="migration",
    )

    op.create_index(
        "idx_collection_flow_apps_status",
        "collection_flow_applications",
        ["collection_status"],
        schema="migration",
    )

    # Add comment to table
    op.execute(
        """
        COMMENT ON TABLE migration.collection_flow_applications IS
        'Links Collection flows to selected applications from Discovery, tracking per-app collection status';
    """
    )

    # Add comments to columns
    op.execute(
        """
        COMMENT ON COLUMN migration.collection_flow_applications.discovery_data_snapshot IS
        'Snapshot of Discovery data at the time of Collection flow creation';
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN migration.collection_flow_applications.gap_analysis_result IS
        'Result of gap analysis for this specific application';
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN migration.collection_flow_applications.collection_status IS
        'Status of data collection for this application: pending, in_progress, completed, failed';
    """
    )


def downgrade() -> None:
    """Drop collection_flow_applications table"""

    # Drop indexes
    op.drop_index(
        "idx_collection_flow_apps_status",
        table_name="collection_flow_applications",
        schema="migration",
    )
    op.drop_index(
        "idx_collection_flow_apps",
        table_name="collection_flow_applications",
        schema="migration",
    )

    # Drop table
    op.drop_table("collection_flow_applications", schema="migration")
