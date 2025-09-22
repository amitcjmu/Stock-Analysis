"""Add asset field conflicts table for asset-agnostic collection

Revision ID: 074_add_asset_field_conflicts
Revises: 073_add_timestamp_columns_collection_gaps
Create Date: 2025-01-21

This migration creates the asset_field_conflicts table to track and resolve
conflicts across multiple data sources during asset-agnostic collection.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "074_add_asset_field_conflicts"
down_revision = "073_add_timestamp_columns_collection_gaps"
branch_labels = None
depends_on = None


def table_exists(table_name: str, schema: str = "migration") -> bool:
    """Check if a table exists."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.tables "
            "WHERE table_schema = :schema AND table_name = :table_name)"
        ),
        {"schema": schema, "table_name": table_name},
    )
    return result.scalar()


def upgrade():
    """Create asset_field_conflicts table."""
    # Skip if table already exists (idempotent)
    if table_exists("asset_field_conflicts"):
        print("✅ Table asset_field_conflicts already exists, skipping creation")
        return

    # Create enum for resolution status
    resolution_status_enum = postgresql.ENUM(
        "pending",
        "auto_resolved",
        "manual_resolved",
        name="resolution_status_enum",
        create_type=False,
    )
    resolution_status_enum.create(op.get_bind(), checkfirst=True)

    # Create asset_field_conflicts table
    op.create_table(
        "asset_field_conflicts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("conflicting_values", postgresql.JSONB, nullable=False),
        sa.Column(
            "resolution_status",
            resolution_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("resolved_value", sa.Text, nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolution_rationale", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        schema="migration",
    )

    # Add foreign key constraint to assets table
    op.create_foreign_key(
        "fk_asset_field_conflicts_asset_id",
        "asset_field_conflicts",
        "assets",
        ["asset_id"],
        ["id"],
        source_schema="migration",
        referent_schema="migration",
        ondelete="CASCADE",
    )

    # Add unique constraint for asset + field + tenant combination
    op.create_unique_constraint(
        "uq_conflict_asset_field_tenant",
        "asset_field_conflicts",
        ["asset_id", "field_name", "client_account_id", "engagement_id"],
        schema="migration",
    )

    # Create indexes for performance
    op.create_index(
        "idx_conflicts_asset_field",
        "asset_field_conflicts",
        ["asset_id", "field_name"],
        schema="migration",
    )

    op.create_index(
        "idx_conflicts_tenant",
        "asset_field_conflicts",
        ["client_account_id", "engagement_id"],
        schema="migration",
    )

    op.create_index(
        "idx_conflicts_status",
        "asset_field_conflicts",
        ["resolution_status"],
        schema="migration",
    )

    print("✅ Created asset_field_conflicts table with UUID tenant IDs")


def downgrade():
    """Drop asset_field_conflicts table."""
    if table_exists("asset_field_conflicts"):
        # Drop indexes first
        op.drop_index("idx_conflicts_status", schema="migration")
        op.drop_index("idx_conflicts_tenant", schema="migration")
        op.drop_index("idx_conflicts_asset_field", schema="migration")

        # Drop unique constraint
        op.drop_constraint(
            "uq_conflict_asset_field_tenant",
            "asset_field_conflicts",
            schema="migration",
        )

        # Drop foreign key constraint
        op.drop_constraint(
            "fk_asset_field_conflicts_asset_id",
            "asset_field_conflicts",
            schema="migration",
        )

        # Drop table
        op.drop_table("asset_field_conflicts", schema="migration")

        # Drop enum (only if no other tables use it)
        try:
            op.execute("DROP TYPE IF EXISTS migration.resolution_status_enum")
        except Exception:
            pass  # Ignore errors if enum is still in use

        print("✅ Dropped asset_field_conflicts table")
