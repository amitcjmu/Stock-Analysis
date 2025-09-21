"""Collection gaps Phase 1 schema changes

Revision ID: 072_collection_gaps_phase1_schema
Revises: 071_fix_assets_table_missing_columns
Create Date: 2025-01-21

This migration adds all collection gaps Phase 1 tables for:
- Global vendor/product catalog with tenant overrides
- Lifecycle milestones tracking
- Asset resilience and compliance
- Maintenance windows and blackout periods
- Governance (approvals and exceptions)
- Enhanced asset-product relationships
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID, TEXT

# revision identifiers, used by Alembic.
revision = "072_collection_gaps_phase1_schema"
down_revision = "071_fix_assets_table_missing_columns"
branch_labels = None
depends_on = None


def table_exists(table_name: str, schema: str = "migration") -> bool:
    """Check if table exists."""
    bind = op.get_bind()
    try:
        stmt = sa.text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema
                  AND table_name = :table_name
            )
        """
        )
        result = bind.execute(
            stmt, {"schema": schema, "table_name": table_name}
        ).scalar()
        return bool(result)
    except Exception:
        return False


def column_exists(table_name: str, column_name: str, schema: str = "migration") -> bool:
    """Check if column exists in table."""
    bind = op.get_bind()
    try:
        stmt = sa.text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = :schema
                  AND table_name = :table_name
                  AND column_name = :column_name
            )
        """
        )
        result = bind.execute(
            stmt,
            {"schema": schema, "table_name": table_name, "column_name": column_name},
        ).scalar()
        return bool(result)
    except Exception:
        return False


def index_exists(index_name: str, schema: str = "migration") -> bool:
    """Check if index exists."""
    bind = op.get_bind()
    try:
        stmt = sa.text(
            """
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = :schema
                  AND indexname = :index_name
            )
        """
        )
        result = bind.execute(
            stmt, {"schema": schema, "index_name": index_name}
        ).scalar()
        return bool(result)
    except Exception:
        return False


def upgrade():
    """Add all collection gaps Phase 1 tables and constraints."""

    # 1. Global Vendor Products Catalog
    if not table_exists("vendor_products_catalog"):
        op.create_table(
            "vendor_products_catalog",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("vendor_name", sa.String(255), nullable=False),
            sa.Column("product_name", sa.String(255), nullable=False),
            sa.Column("normalized_key", sa.String(255), nullable=False),
            sa.Column(
                "is_global",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.UniqueConstraint(
                "vendor_name",
                "product_name",
                name="uq_vendor_products_catalog_vendor_product",
            ),
            schema="migration",
        )
        print("Created 'vendor_products_catalog' table")
    else:
        print("Table 'vendor_products_catalog' already exists, skipping")

    # 2. Product Versions Catalog
    if not table_exists("product_versions_catalog"):
        op.create_table(
            "product_versions_catalog",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("catalog_id", UUID(as_uuid=True), nullable=False),
            sa.Column("version_label", sa.String(100), nullable=False),
            sa.Column("version_semver", sa.String(100), nullable=True),
            sa.ForeignKeyConstraint(
                ["catalog_id"],
                ["migration.vendor_products_catalog.id"],
                ondelete="CASCADE",
            ),
            sa.UniqueConstraint(
                "catalog_id",
                "version_label",
                name="uq_product_versions_catalog_catalog_version",
            ),
            schema="migration",
        )
        print("Created 'product_versions_catalog' table")
    else:
        print("Table 'product_versions_catalog' already exists, skipping")

    # 3. Tenant Vendor Products (Tenant Overrides)
    if not table_exists("tenant_vendor_products"):
        op.create_table(
            "tenant_vendor_products",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("client_account_id", UUID(as_uuid=True), nullable=False),
            sa.Column("engagement_id", UUID(as_uuid=True), nullable=False),
            sa.Column("catalog_id", UUID(as_uuid=True), nullable=True),
            sa.Column("custom_vendor_name", sa.String(255), nullable=True),
            sa.Column("custom_product_name", sa.String(255), nullable=True),
            sa.Column("normalized_key", sa.String(255), nullable=True),
            sa.ForeignKeyConstraint(
                ["client_account_id"],
                ["migration.client_accounts.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["engagement_id"], ["migration.engagements.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["catalog_id"],
                ["migration.vendor_products_catalog.id"],
                ondelete="SET NULL",
            ),
            schema="migration",
        )

        # Add the complex unique index using COALESCE expressions
        op.execute(
            """
            CREATE UNIQUE INDEX idx_tenant_vendor_products_unique
            ON migration.tenant_vendor_products (
                client_account_id,
                engagement_id,
                COALESCE(catalog_id, '00000000-0000-0000-0000-000000000000'::uuid),
                COALESCE(custom_vendor_name, ''),
                COALESCE(custom_product_name, '')
            )
            """
        )
        print("Created 'tenant_vendor_products' table")
    else:
        print("Table 'tenant_vendor_products' already exists, skipping")

    # 4. Tenant Product Versions
    if not table_exists("tenant_product_versions"):
        op.create_table(
            "tenant_product_versions",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("tenant_product_id", UUID(as_uuid=True), nullable=True),
            sa.Column("catalog_version_id", UUID(as_uuid=True), nullable=True),
            sa.Column("version_label", sa.String(100), nullable=True),
            sa.Column("version_semver", sa.String(100), nullable=True),
            sa.ForeignKeyConstraint(
                ["tenant_product_id"],
                ["migration.tenant_vendor_products.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["catalog_version_id"],
                ["migration.product_versions_catalog.id"],
                ondelete="SET NULL",
            ),
            schema="migration",
        )
        print("Created 'tenant_product_versions' table")
    else:
        print("Table 'tenant_product_versions' already exists, skipping")

    # 5. Lifecycle Milestones
    if not table_exists("lifecycle_milestones"):
        op.create_table(
            "lifecycle_milestones",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("catalog_version_id", UUID(as_uuid=True), nullable=True),
            sa.Column("tenant_version_id", UUID(as_uuid=True), nullable=True),
            sa.Column("milestone_type", sa.String(50), nullable=False),
            sa.Column("milestone_date", sa.Date(), nullable=False),
            sa.Column("source", sa.String(255), nullable=True),
            sa.Column(
                "provenance",
                JSONB,
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["catalog_version_id"],
                ["migration.product_versions_catalog.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["tenant_version_id"],
                ["migration.tenant_product_versions.id"],
                ondelete="CASCADE",
            ),
            sa.CheckConstraint(
                "milestone_type IN ('release', 'end_of_support', 'end_of_life', 'extended_support_end')",
                name="ck_lifecycle_milestones_milestone_type",
            ),
            schema="migration",
        )
        print("Created 'lifecycle_milestones' table")
    else:
        print("Table 'lifecycle_milestones' already exists, skipping")

    # 6. Asset Product Links
    if not table_exists("asset_product_links"):
        op.create_table(
            "asset_product_links",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("asset_id", UUID(as_uuid=True), nullable=False),
            sa.Column("catalog_version_id", UUID(as_uuid=True), nullable=True),
            sa.Column("tenant_version_id", UUID(as_uuid=True), nullable=True),
            sa.Column("confidence_score", sa.Float(), nullable=True),
            sa.Column("matched_by", sa.String(50), nullable=True),
            sa.ForeignKeyConstraint(
                ["asset_id"], ["migration.assets.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["catalog_version_id"],
                ["migration.product_versions_catalog.id"],
                ondelete="SET NULL",
            ),
            sa.ForeignKeyConstraint(
                ["tenant_version_id"],
                ["migration.tenant_product_versions.id"],
                ondelete="SET NULL",
            ),
            sa.CheckConstraint(
                "confidence_score >= 0 AND confidence_score <= 1",
                name="ck_asset_product_links_confidence_score",
            ),
            schema="migration",
        )

        # Add the complex unique index using COALESCE expressions
        op.execute(
            """
            CREATE UNIQUE INDEX idx_asset_product_links_unique
            ON migration.asset_product_links (
                asset_id,
                COALESCE(catalog_version_id, '00000000-0000-0000-0000-000000000000'::uuid),
                COALESCE(tenant_version_id, '00000000-0000-0000-0000-000000000000'::uuid)
            )
            """
        )
        print("Created 'asset_product_links' table")
    else:
        print("Table 'asset_product_links' already exists, skipping")

    # 7. Asset Resilience
    if not table_exists("asset_resilience"):
        op.create_table(
            "asset_resilience",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("asset_id", UUID(as_uuid=True), nullable=False),
            sa.Column("rto_minutes", sa.Integer(), nullable=True),
            sa.Column("rpo_minutes", sa.Integer(), nullable=True),
            sa.Column(
                "sla_json", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
            ),
            sa.ForeignKeyConstraint(
                ["asset_id"], ["migration.assets.id"], ondelete="CASCADE"
            ),
            sa.CheckConstraint(
                "rto_minutes >= 0", name="ck_asset_resilience_rto_minutes"
            ),
            sa.CheckConstraint(
                "rpo_minutes >= 0", name="ck_asset_resilience_rpo_minutes"
            ),
            schema="migration",
        )
        print("Created 'asset_resilience' table")
    else:
        print("Table 'asset_resilience' already exists, skipping")

    # 8. Asset Compliance Flags
    if not table_exists("asset_compliance_flags"):
        op.create_table(
            "asset_compliance_flags",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("asset_id", UUID(as_uuid=True), nullable=False),
            sa.Column(
                "compliance_scopes",
                sa.ARRAY(TEXT),
                nullable=False,
                server_default=sa.text("'{}'"),
            ),
            sa.Column("data_classification", sa.String(50), nullable=True),
            sa.Column("residency", sa.String(50), nullable=True),
            sa.Column(
                "evidence_refs",
                JSONB,
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.ForeignKeyConstraint(
                ["asset_id"], ["migration.assets.id"], ondelete="CASCADE"
            ),
            schema="migration",
        )
        print("Created 'asset_compliance_flags' table")
    else:
        print("Table 'asset_compliance_flags' already exists, skipping")

    # 9. Asset Vulnerabilities
    if not table_exists("asset_vulnerabilities"):
        op.create_table(
            "asset_vulnerabilities",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("asset_id", UUID(as_uuid=True), nullable=False),
            sa.Column("cve_id", sa.String(50), nullable=True),
            sa.Column("severity", sa.String(10), nullable=True),
            sa.Column("detected_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("source", sa.String(255), nullable=True),
            sa.Column(
                "details", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
            ),
            sa.ForeignKeyConstraint(
                ["asset_id"], ["migration.assets.id"], ondelete="CASCADE"
            ),
            schema="migration",
        )
        print("Created 'asset_vulnerabilities' table")
    else:
        print("Table 'asset_vulnerabilities' already exists, skipping")

    # 10. Maintenance Windows
    if not table_exists("maintenance_windows"):
        op.create_table(
            "maintenance_windows",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("client_account_id", UUID(as_uuid=True), nullable=False),
            sa.Column("engagement_id", UUID(as_uuid=True), nullable=False),
            sa.Column("scope_type", sa.String(20), nullable=False),
            sa.Column("application_id", UUID(as_uuid=True), nullable=True),
            sa.Column("asset_id", UUID(as_uuid=True), nullable=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
            sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "recurring",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column("timezone", sa.String(50), nullable=True),
            sa.ForeignKeyConstraint(
                ["client_account_id"],
                ["migration.client_accounts.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["engagement_id"], ["migration.engagements.id"], ondelete="CASCADE"
            ),
            sa.CheckConstraint(
                "scope_type IN ('tenant', 'application', 'asset')",
                name="ck_maintenance_windows_scope_type",
            ),
            schema="migration",
        )
        print("Created 'maintenance_windows' table")
    else:
        print("Table 'maintenance_windows' already exists, skipping")

    # 11. Blackout Periods
    if not table_exists("blackout_periods"):
        op.create_table(
            "blackout_periods",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("client_account_id", UUID(as_uuid=True), nullable=False),
            sa.Column("engagement_id", UUID(as_uuid=True), nullable=False),
            sa.Column("scope_type", sa.String(20), nullable=False),
            sa.Column("application_id", UUID(as_uuid=True), nullable=True),
            sa.Column("asset_id", UUID(as_uuid=True), nullable=True),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=False),
            sa.Column("reason", TEXT, nullable=True),
            sa.ForeignKeyConstraint(
                ["client_account_id"],
                ["migration.client_accounts.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["engagement_id"], ["migration.engagements.id"], ondelete="CASCADE"
            ),
            sa.CheckConstraint(
                "scope_type IN ('tenant', 'application', 'asset')",
                name="ck_blackout_periods_scope_type",
            ),
            schema="migration",
        )
        print("Created 'blackout_periods' table")
    else:
        print("Table 'blackout_periods' already exists, skipping")

    # 12. Asset Licenses
    if not table_exists("asset_licenses"):
        op.create_table(
            "asset_licenses",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("asset_id", UUID(as_uuid=True), nullable=False),
            sa.Column("license_type", sa.String(100), nullable=True),
            sa.Column("renewal_date", sa.Date(), nullable=True),
            sa.Column("contract_reference", sa.String(255), nullable=True),
            sa.Column("support_tier", sa.String(50), nullable=True),
            sa.ForeignKeyConstraint(
                ["asset_id"], ["migration.assets.id"], ondelete="CASCADE"
            ),
            schema="migration",
        )
        print("Created 'asset_licenses' table")
    else:
        print("Table 'asset_licenses' already exists, skipping")

    # 13. Approval Requests
    if not table_exists("approval_requests"):
        op.create_table(
            "approval_requests",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("client_account_id", UUID(as_uuid=True), nullable=False),
            sa.Column("engagement_id", UUID(as_uuid=True), nullable=False),
            sa.Column("entity_type", sa.String(30), nullable=False),
            sa.Column("entity_id", UUID(as_uuid=True), nullable=True),
            sa.Column(
                "status", sa.String(20), nullable=False, server_default="PENDING"
            ),
            sa.Column("approver_id", UUID(as_uuid=True), nullable=True),
            sa.Column("notes", TEXT, nullable=True),
            sa.Column(
                "requested_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["client_account_id"],
                ["migration.client_accounts.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["engagement_id"], ["migration.engagements.id"], ondelete="CASCADE"
            ),
            sa.CheckConstraint(
                "entity_type IN ('strategy', 'wave', 'schedule', 'exception')",
                name="ck_approval_requests_entity_type",
            ),
            sa.CheckConstraint(
                "status IN ('PENDING', 'APPROVED', 'REJECTED')",
                name="ck_approval_requests_status",
            ),
            schema="migration",
        )
        print("Created 'approval_requests' table")
    else:
        print("Table 'approval_requests' already exists, skipping")

    # 14. Migration Exceptions
    if not table_exists("migration_exceptions"):
        op.create_table(
            "migration_exceptions",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("client_account_id", UUID(as_uuid=True), nullable=False),
            sa.Column("engagement_id", UUID(as_uuid=True), nullable=False),
            sa.Column("application_id", UUID(as_uuid=True), nullable=True),
            sa.Column("asset_id", UUID(as_uuid=True), nullable=True),
            sa.Column("exception_type", sa.String(50), nullable=True),
            sa.Column("rationale", TEXT, nullable=True),
            sa.Column("risk_level", sa.String(10), nullable=True),
            sa.Column("approval_request_id", UUID(as_uuid=True), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
            sa.ForeignKeyConstraint(
                ["client_account_id"],
                ["migration.client_accounts.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["engagement_id"], ["migration.engagements.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["approval_request_id"],
                ["migration.approval_requests.id"],
                ondelete="SET NULL",
            ),
            sa.CheckConstraint(
                "status IN ('OPEN', 'CLOSED')", name="ck_migration_exceptions_status"
            ),
            schema="migration",
        )
        print("Created 'migration_exceptions' table")
    else:
        print("Table 'migration_exceptions' already exists, skipping")

    # 15. Extend asset_dependencies table with new columns
    if table_exists("asset_dependencies"):
        if not column_exists("asset_dependencies", "relationship_nature"):
            op.add_column(
                "asset_dependencies",
                sa.Column("relationship_nature", sa.String(50), nullable=True),
                schema="migration",
            )
            print("Added 'relationship_nature' column to asset_dependencies")

        if not column_exists("asset_dependencies", "direction"):
            op.add_column(
                "asset_dependencies",
                sa.Column("direction", sa.String(10), nullable=True),
                schema="migration",
            )
            # Add check constraint for direction
            op.create_check_constraint(
                "ck_asset_dependencies_direction",
                "asset_dependencies",
                "direction IN ('upstream', 'downstream')",
                schema="migration",
            )
            print("Added 'direction' column to asset_dependencies")

        if not column_exists("asset_dependencies", "criticality"):
            op.add_column(
                "asset_dependencies",
                sa.Column("criticality", sa.String(10), nullable=True),
                schema="migration",
            )
            # Add check constraint for criticality
            op.create_check_constraint(
                "ck_asset_dependencies_criticality",
                "asset_dependencies",
                "criticality IN ('low', 'medium', 'high', 'critical')",
                schema="migration",
            )
            print("Added 'criticality' column to asset_dependencies")

        if not column_exists("asset_dependencies", "dataflow_type"):
            op.add_column(
                "asset_dependencies",
                sa.Column("dataflow_type", sa.String(20), nullable=True),
                schema="migration",
            )
            # Add check constraint for dataflow_type
            op.create_check_constraint(
                "ck_asset_dependencies_dataflow_type",
                "asset_dependencies",
                "dataflow_type IN ('batch', 'stream', 'sync', 'async')",
                schema="migration",
            )
            print("Added 'dataflow_type' column to asset_dependencies")

    # 16. Create Indexes
    indexes_to_create = [
        ("idx_asset_resilience_asset", "asset_resilience", ["asset_id"]),
        ("idx_asset_product_links_asset", "asset_product_links", ["asset_id"]),
        (
            "idx_lifecycle_milestones_catver",
            "lifecycle_milestones",
            ["catalog_version_id"],
        ),
        (
            "idx_lifecycle_milestones_tenver",
            "lifecycle_milestones",
            ["tenant_version_id"],
        ),
        (
            "idx_tenant_vendor_products_tenant",
            "tenant_vendor_products",
            ["client_account_id", "engagement_id"],
        ),
        (
            "idx_maintenance_windows_tenant",
            "maintenance_windows",
            ["client_account_id", "engagement_id"],
        ),
        (
            "idx_blackout_periods_tenant",
            "blackout_periods",
            ["client_account_id", "engagement_id"],
        ),
        (
            "idx_approval_requests_tenant",
            "approval_requests",
            ["client_account_id", "engagement_id"],
        ),
        (
            "idx_migration_exceptions_tenant",
            "migration_exceptions",
            ["client_account_id", "engagement_id"],
        ),
    ]

    for index_name, table_name, columns in indexes_to_create:
        if not index_exists(index_name):
            op.create_index(index_name, table_name, columns, schema="migration")
            print(f"Created index '{index_name}' on {table_name}")
        else:
            print(f"Index '{index_name}' already exists, skipping")

    # 17. Create Materialized View (Optional)
    # Check if view exists first
    try:
        bind = op.get_bind()
        view_exists = bind.execute(
            sa.text(
                """
            SELECT EXISTS (
                SELECT 1 FROM pg_matviews
                WHERE schemaname = 'migration'
                  AND matviewname = 'unified_vendor_products'
            )
            """
            )
        ).scalar()

        if not view_exists:
            op.execute(
                """
                CREATE MATERIALIZED VIEW migration.unified_vendor_products AS
                SELECT
                    COALESCE(tvp.id, vpc.id)               AS id,
                    tvp.client_account_id                  AS client_account_id,
                    tvp.engagement_id                      AS engagement_id,
                    COALESCE(tvp.custom_vendor_name, vpc.vendor_name)  AS vendor_name,
                    COALESCE(tvp.custom_product_name, vpc.product_name) AS product_name,
                    (tvp.id IS NOT NULL)                   AS is_tenant_override
                FROM migration.vendor_products_catalog vpc
                LEFT JOIN migration.tenant_vendor_products tvp
                  ON tvp.catalog_id = vpc.id
                """
            )
            print("Created 'unified_vendor_products' materialized view")
        else:
            print(
                "Materialized view 'unified_vendor_products' already exists, skipping"
            )
    except Exception as e:
        print(f"Could not create materialized view: {e}")


def downgrade():
    """Remove all collection gaps Phase 1 tables and constraints."""

    # Drop materialized view first
    try:
        op.execute("DROP MATERIALIZED VIEW IF EXISTS migration.unified_vendor_products")
        print("Dropped materialized view 'unified_vendor_products'")
    except Exception:
        pass

    # Drop indexes
    indexes_to_drop = [
        "idx_migration_exceptions_tenant",
        "idx_approval_requests_tenant",
        "idx_blackout_periods_tenant",
        "idx_maintenance_windows_tenant",
        "idx_tenant_vendor_products_tenant",
        "idx_lifecycle_milestones_tenver",
        "idx_lifecycle_milestones_catver",
        "idx_asset_product_links_asset",
        "idx_asset_resilience_asset",
    ]

    for index_name in indexes_to_drop:
        if index_exists(index_name):
            op.drop_index(index_name, schema="migration")
            print(f"Dropped index '{index_name}'")

    # Drop asset_dependencies column extensions
    if table_exists("asset_dependencies"):
        if column_exists("asset_dependencies", "dataflow_type"):
            op.drop_constraint(
                "ck_asset_dependencies_dataflow_type",
                "asset_dependencies",
                schema="migration",
            )
            op.drop_column("asset_dependencies", "dataflow_type", schema="migration")

        if column_exists("asset_dependencies", "criticality"):
            op.drop_constraint(
                "ck_asset_dependencies_criticality",
                "asset_dependencies",
                schema="migration",
            )
            op.drop_column("asset_dependencies", "criticality", schema="migration")

        if column_exists("asset_dependencies", "direction"):
            op.drop_constraint(
                "ck_asset_dependencies_direction",
                "asset_dependencies",
                schema="migration",
            )
            op.drop_column("asset_dependencies", "direction", schema="migration")

        if column_exists("asset_dependencies", "relationship_nature"):
            op.drop_column(
                "asset_dependencies", "relationship_nature", schema="migration"
            )

    # Drop custom unique indexes first before dropping tables
    try:
        op.execute("DROP INDEX IF EXISTS migration.idx_asset_product_links_unique")
        op.execute("DROP INDEX IF EXISTS migration.idx_tenant_vendor_products_unique")
    except Exception:
        pass  # Ignore if indexes don't exist

    # Drop tables in reverse dependency order
    tables_to_drop = [
        "migration_exceptions",
        "approval_requests",
        "asset_licenses",
        "blackout_periods",
        "maintenance_windows",
        "asset_vulnerabilities",
        "asset_compliance_flags",
        "asset_resilience",
        "asset_product_links",
        "lifecycle_milestones",
        "tenant_product_versions",
        "tenant_vendor_products",
        "product_versions_catalog",
        "vendor_products_catalog",
    ]

    for table_name in tables_to_drop:
        if table_exists(table_name):
            op.drop_table(table_name, schema="migration")
            print(f"Dropped table '{table_name}'")
