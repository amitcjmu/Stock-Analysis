"""Add composite indexes for asset deduplication

Revision ID: 088_asset_dedup_indexes
Revises: 086_fix_collection_flow_status_adr012
Create Date: 2025-10-08 23:14:19

Note: Migration 087 was consolidated into 086. This migration now directly
follows the consolidated migration 086 which handles both phase value migration
and paused status addition.

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "088_asset_dedup_indexes"
down_revision = "086_fix_collection_flow_status_adr012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add composite indexes to optimize hierarchical asset deduplication queries.

    Indexes support the 4-level deduplication hierarchy:
    1. name + asset_type + tenant
    2. hostname/fqdn/ip_address + tenant
    3. Tenant-scoped lookups

    All indexes include client_account_id and engagement_id for multi-tenant isolation.
    """

    # Priority 1: name + asset_type deduplication
    # Supports: WHERE name = ? AND asset_type = ? AND client_account_id = ? AND engagement_id = ?
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_asset_dedup_name_type_tenant
        ON migration.assets (name, asset_type, client_account_id, engagement_id)
        WHERE name IS NOT NULL AND asset_type IS NOT NULL
        """
    )

    # Priority 2a: hostname deduplication
    # Supports: WHERE hostname = ? AND client_account_id = ? AND engagement_id = ?
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_asset_dedup_hostname_tenant
        ON migration.assets (hostname, client_account_id, engagement_id)
        WHERE hostname IS NOT NULL
        """
    )

    # Priority 2b: fqdn deduplication
    # Supports: WHERE fqdn = ? AND client_account_id = ? AND engagement_id = ?
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_asset_dedup_fqdn_tenant
        ON migration.assets (fqdn, client_account_id, engagement_id)
        WHERE fqdn IS NOT NULL
        """
    )

    # Priority 2c: ip_address deduplication
    # Supports: WHERE ip_address = ? AND client_account_id = ? AND engagement_id = ?
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_asset_dedup_ip_tenant
        ON migration.assets (ip_address, client_account_id, engagement_id)
        WHERE ip_address IS NOT NULL
        """
    )

    # Batch prefetch optimization: IN clause lookups
    # Supports: WHERE name IN (...) AND client_account_id = ? AND engagement_id = ?
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_asset_dedup_batch_name_tenant
        ON migration.assets (client_account_id, engagement_id, name)
        WHERE name IS NOT NULL
        """
    )

    # Batch prefetch for hostnames
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_asset_dedup_batch_hostname_tenant
        ON migration.assets (client_account_id, engagement_id, hostname)
        WHERE hostname IS NOT NULL
        """
    )


def downgrade() -> None:
    """Remove composite indexes for asset deduplication."""

    op.execute("DROP INDEX IF EXISTS migration.idx_asset_dedup_name_type_tenant")
    op.execute("DROP INDEX IF EXISTS migration.idx_asset_dedup_hostname_tenant")
    op.execute("DROP INDEX IF EXISTS migration.idx_asset_dedup_fqdn_tenant")
    op.execute("DROP INDEX IF EXISTS migration.idx_asset_dedup_ip_tenant")
    op.execute("DROP INDEX IF EXISTS migration.idx_asset_dedup_batch_name_tenant")
    op.execute("DROP INDEX IF EXISTS migration.idx_asset_dedup_batch_hostname_tenant")
