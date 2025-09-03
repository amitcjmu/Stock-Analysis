"""Add collection_flow_applications table for Discovery to Collection bridge

Revision ID: 049_add_collection_flow_applications_table
Revises: 048_add_technical_details_to_assets
Create Date: 2025-09-03 03:35:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "049_add_collection_flow_applications_table"
down_revision = "048_add_technical_details_to_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create collection_flow_applications table to track selected applications for collection"""

    # Check if table already exists
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'migration'
            AND table_name = 'collection_flow_applications'
        """
        )
    )
    if result.fetchone():
        # Table already exists, skip creation
        return

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

    from sqlalchemy import text

    conn = op.get_bind()

    # Check which indexes exist before dropping
    result = conn.execute(
        text(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'migration'
            AND tablename = 'collection_flow_applications'
            AND indexname IN ('idx_collection_flow_apps_status', 'idx_collection_flow_apps')
        """
        )
    )
    existing_indexes = [row[0] for row in result]

    if "idx_collection_flow_apps_status" in existing_indexes:
        op.drop_index(
            "idx_collection_flow_apps_status",
            table_name="collection_flow_applications",
            schema="migration",
        )
        print("✅ Dropped index idx_collection_flow_apps_status")
    else:
        print("⚠️ Index idx_collection_flow_apps_status does not exist, skipping")

    if "idx_collection_flow_apps" in existing_indexes:
        op.drop_index(
            "idx_collection_flow_apps",
            table_name="collection_flow_applications",
            schema="migration",
        )
        print("✅ Dropped index idx_collection_flow_apps")
    else:
        print("⚠️ Index idx_collection_flow_apps does not exist, skipping")

    # Check if table exists before dropping
    result = conn.execute(
        text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'collection_flow_applications'
            )
        """
        )
    )
    table_exists = result.scalar()

    if table_exists:
        op.drop_table("collection_flow_applications", schema="migration")
        print("✅ Dropped table collection_flow_applications")
    else:
        print("⚠️ Table collection_flow_applications does not exist, skipping")
