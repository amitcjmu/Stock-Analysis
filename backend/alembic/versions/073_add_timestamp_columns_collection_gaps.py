"""Add timestamp columns to collection gaps tables

Revision ID: 073_add_timestamp_columns_collection_gaps
Revises: 072_collection_gaps_phase1_schema
Create Date: 2025-01-21

This migration adds missing created_at and updated_at columns to tables
that inherit from TimestampMixin but were created without these columns.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "073_add_timestamp_columns_collection_gaps"
down_revision = (
    "072_collection_gaps_phase1_schema",
    "066_add_master_flow_id_to_discovery_flows",
)
branch_labels = None
depends_on = None


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


def upgrade():
    """Add created_at and updated_at columns to tables that need them."""

    # Tables that need timestamp columns (inherit from TimestampMixin)
    tables_needing_timestamps = [
        "vendor_products_catalog",
        "tenant_vendor_products",
        "maintenance_windows",
        "blackout_periods",
        "approval_requests",
        "migration_exceptions",
        "asset_resilience",
        "asset_compliance_flags",
        "asset_vulnerabilities",
        "asset_product_links",
        "lifecycle_milestones",
        "product_versions_catalog",
        "tenant_product_versions",
        "asset_licenses",
    ]

    for table_name in tables_needing_timestamps:
        if not table_exists(table_name):
            print(f"Table '{table_name}' does not exist, skipping timestamp columns")
            continue

        # Add created_at column if missing
        if not column_exists(table_name, "created_at"):
            op.add_column(
                table_name,
                sa.Column(
                    "created_at",
                    sa.DateTime(timezone=True),
                    nullable=False,
                    server_default=sa.text("now()"),
                ),
                schema="migration",
            )
            print(f"Added 'created_at' column to {table_name}")
        else:
            print(f"Column 'created_at' already exists in {table_name}")

        # Add updated_at column if missing
        if not column_exists(table_name, "updated_at"):
            op.add_column(
                table_name,
                sa.Column(
                    "updated_at",
                    sa.DateTime(timezone=True),
                    nullable=False,
                    server_default=sa.text("now()"),
                ),
                schema="migration",
            )
            print(f"Added 'updated_at' column to {table_name}")
        else:
            print(f"Column 'updated_at' already exists in {table_name}")

    # Create function and trigger for auto-updating updated_at
    op.execute(
        """
        CREATE OR REPLACE FUNCTION migration.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
    )
    print("Created update_updated_at_column() function")

    # Add triggers for auto-updating updated_at on each table
    for table_name in tables_needing_timestamps:
        if table_exists(table_name) and column_exists(table_name, "updated_at"):
            trigger_name = f"update_{table_name}_updated_at"
            op.execute(
                f"""
                DROP TRIGGER IF EXISTS {trigger_name} ON migration.{table_name};
                CREATE TRIGGER {trigger_name}
                    BEFORE UPDATE ON migration.{table_name}
                    FOR EACH ROW
                    EXECUTE FUNCTION migration.update_updated_at_column();
                """
            )
            print(f"Created trigger '{trigger_name}' on {table_name}")


def downgrade():
    """Remove timestamp columns and triggers."""

    tables_with_timestamps = [
        "vendor_products_catalog",
        "tenant_vendor_products",
        "maintenance_windows",
        "blackout_periods",
        "approval_requests",
        "migration_exceptions",
        "asset_resilience",
        "asset_compliance_flags",
        "asset_vulnerabilities",
        "asset_product_links",
        "lifecycle_milestones",
        "product_versions_catalog",
        "tenant_product_versions",
        "asset_licenses",
    ]

    # Drop triggers
    for table_name in tables_with_timestamps:
        if table_exists(table_name):
            trigger_name = f"update_{table_name}_updated_at"
            op.execute(
                f"DROP TRIGGER IF EXISTS {trigger_name} ON migration.{table_name}"
            )
            print(f"Dropped trigger '{trigger_name}' from {table_name}")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS migration.update_updated_at_column()")
    print("Dropped update_updated_at_column() function")

    # Drop timestamp columns
    for table_name in tables_with_timestamps:
        if table_exists(table_name):
            if column_exists(table_name, "updated_at"):
                op.drop_column(table_name, "updated_at", schema="migration")
                print(f"Dropped 'updated_at' column from {table_name}")

            if column_exists(table_name, "created_at"):
                op.drop_column(table_name, "created_at", schema="migration")
                print(f"Dropped 'created_at' column from {table_name}")
