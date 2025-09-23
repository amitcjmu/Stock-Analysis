"""Add database indexes for asset listing endpoint optimization

Revision ID: 075_add_assets_listing_indexes
Revises: 074_add_asset_field_conflicts
Create Date: 2025-01-21

This migration adds indexes to optimize the /available assets endpoint
for Collection Gaps Phase 2, improving query performance for pagination,
filtering, and search operations.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "075_add_assets_listing_indexes"
down_revision = "074_add_asset_field_conflicts"
branch_labels = None
depends_on = None


def index_exists(index_name: str, table_name: str, schema: str = "migration") -> bool:
    """Check if an index exists."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT FROM pg_indexes "
            "WHERE schemaname = :schema AND tablename = :table_name AND indexname = :index_name)"
        ),
        {"schema": schema, "table_name": table_name, "index_name": index_name},
    )
    return result.scalar()


def upgrade():
    """Add indexes for asset listing optimization."""

    # 1. Compound index for engagement, asset type, and active status
    # This optimizes the main query filter in the /available endpoint
    index_name = "idx_assets_engagement_type_active"
    if not index_exists(index_name, "assets"):
        op.create_index(
            index_name,
            "assets",
            ["engagement_id", "asset_type"],
            schema="migration",
            postgresql_where=sa.text("status != 'decommissioned'"),
        )
        print(f"✅ Created index {index_name}")
    else:
        print(f"✅ Index {index_name} already exists")

    # 2. Text search index for name, application_name, and hostname
    # This optimizes the search functionality
    index_name = "idx_assets_search_fields"
    if not index_exists(index_name, "assets"):
        op.create_index(
            index_name,
            "assets",
            ["name", "application_name", "hostname"],
            schema="migration",
        )
        print(f"✅ Created index {index_name}")
    else:
        print(f"✅ Index {index_name} already exists")

    # 3. Index for ordering by created_at (pagination)
    # This optimizes the ORDER BY clause in pagination
    index_name = "idx_assets_created_at_desc"
    if not index_exists(index_name, "assets"):
        op.create_index(
            index_name, "assets", [sa.text("created_at DESC")], schema="migration"
        )
        print(f"✅ Created index {index_name}")
    else:
        print(f"✅ Index {index_name} already exists")

    # 4. Compound index for tenant-scoped queries with asset type filter
    # This optimizes queries with both tenant scoping and asset type filtering
    index_name = "idx_assets_tenant_type_filter"
    if not index_exists(index_name, "assets"):
        op.create_index(
            index_name,
            "assets",
            ["client_account_id", "engagement_id", "asset_type"],
            schema="migration",
        )
        print(f"✅ Created index {index_name}")
    else:
        print(f"✅ Index {index_name} already exists")


def downgrade():
    """Remove asset listing optimization indexes."""

    # Drop indexes in reverse order
    indexes_to_drop = [
        "idx_assets_tenant_type_filter",
        "idx_assets_created_at_desc",
        "idx_assets_search_fields",
        "idx_assets_engagement_type_active",
    ]

    for index_name in indexes_to_drop:
        if index_exists(index_name, "assets"):
            op.drop_index(index_name, "assets", schema="migration")
            print(f"✅ Dropped index {index_name}")
        else:
            print(f"✅ Index {index_name} does not exist")
