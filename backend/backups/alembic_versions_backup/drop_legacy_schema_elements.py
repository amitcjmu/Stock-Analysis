"""Drop legacy schema elements - V3 tables and is_mock columns

Revision ID: drop_legacy_schema_elements
Revises: add_error_handling_columns
Create Date: 2025-07-01 00:05:00.000000

This migration drops all V3 prefixed tables and removes is_mock columns from all tables
as we're using multi-tenancy (clientID/engagementID) to handle mock data separation.
"""

from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision = "drop_legacy_schema_elements"
down_revision = "add_error_handling_columns"
branch_labels = None
depends_on = None


def table_exists(connection, table_name):
    result = connection.execute(
        text(
            """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = :table_name
        )
    """
        ),
        {"table_name": table_name},
    )
    return result.scalar()


def column_exists(connection, table_name, column_name):
    result = connection.execute(
        text(
            """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = :table_name
            AND column_name = :column_name
        )
    """
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    return result.scalar()


def upgrade():
    """Drop V3 tables and is_mock columns."""
    connection = op.get_bind()

    print("=== Dropping V3 prefixed tables ===")

    # List of V3 tables to drop
    v3_tables = [
        "v3_raw_import_records",
        "v3_field_mappings",
        "v3_discovery_flows",
        "v3_data_imports",
    ]

    # Drop V3 tables in correct order (dependencies first)
    for table in v3_tables:
        if table_exists(connection, table):
            print(f"Dropping table: {table}")
            op.drop_table(table)
        else:
            print(f"Table {table} doesn't exist, skipping")

    print("\n=== Removing is_mock columns ===")

    # List of tables that might have is_mock column
    tables_with_is_mock = [
        "asset_dependencies",
        "asset_embeddings",
        "asset_tags",
        "assets",
        "client_accounts",
        "cmdb_sixr_analyses",
        "data_import_sessions",
        "data_imports",
        "discovery_assets",
        "discovery_flows",
        "engagements",
        "migration_waves",
        "tags",
        "user_account_associations",
        "users",
        "workflow_progress",
    ]

    # Remove is_mock column from each table if it exists
    for table in tables_with_is_mock:
        if table_exists(connection, table) and column_exists(
            connection, table, "is_mock"
        ):
            print(f"Removing is_mock column from {table}")
            try:
                op.drop_column(table, "is_mock")
            except Exception as e:
                print(f"  Warning: Could not drop is_mock from {table}: {e}")
        else:
            print(f"Table {table} doesn't have is_mock column, skipping")

    print("\n✅ Legacy schema elements cleanup completed")


def downgrade():
    """Downgrade not supported for this migration."""
    # We don't want to recreate V3 tables or is_mock columns
    raise NotImplementedError(
        "Downgrade not supported - legacy schema elements should not be restored"
    )
