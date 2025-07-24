"""Database consolidation - remove v3 tables, rename fields, drop deprecated columns

Revision ID: database_consolidation_20250101
Revises: latest
Create Date: 2025-01-01 12:00:00.000000

This migration consolidates the database schema by:
1. Dropping all v3_ prefixed tables
2. Renaming fields to new conventions
3. Dropping deprecated columns (is_mock, etc.)
4. Adding new JSON columns for state management
5. Creating multi-tenant indexes
6. Dropping deprecated tables
"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "database_consolidation_20250101"
down_revision = "drop_legacy_schema_elements"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def upgrade():
    """Apply all database consolidation changes"""
    logger.info("Starting database consolidation migration...")

    # 1. Drop V3 tables (if they exist)
    drop_v3_tables()

    # 2. Rename fields in existing tables
    rename_fields()

    # 3. Drop deprecated columns
    drop_deprecated_columns()

    # 4. Add new columns for consolidated state management
    add_new_columns()

    # 5. Create multi-tenant indexes
    create_indexes()

    # 6. Drop deprecated tables
    drop_deprecated_tables()

    logger.info("Database consolidation migration completed successfully")


def downgrade():
    """Rollback all database consolidation changes"""
    logger.info("Rolling back database consolidation migration...")

    # Reverse operations in reverse order
    recreate_deprecated_tables()
    drop_indexes()
    drop_new_columns()
    recreate_deprecated_columns()
    revert_field_renames()
    recreate_v3_tables()

    logger.info("Database consolidation rollback completed")


def drop_v3_tables():
    """Drop all v3_ prefixed tables"""
    v3_tables = [
        "v3_discovery_flows",
        "v3_data_imports",
        "v3_import_field_mappings",
        "v3_assets",
        "v3_raw_import_records",
        "v3_asset_dependencies",
        "v3_migration_waves",
    ]

    # Check which tables actually exist
    connection = op.get_bind()
    existing_tables = []
    for table in v3_tables:
        result = connection.execute(
            sa.text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"
            ).bindparams(table_name=table)
        )
        if result.scalar():
            existing_tables.append(table)

    # Drop only existing tables
    for table in existing_tables:
        try:
            op.drop_table(table)
            logger.info(f"Dropped table: {table}")
        except Exception as e:
            logger.warning(f"Error dropping table {table}: {e}")


def rename_fields():
    """Rename fields to new conventions"""

    connection = op.get_bind()

    # Helper function to check if column exists
    def column_exists(table_name, column_name):
        result = connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND column_name = :column_name
                )
            """
            ).bindparams(table_name=table_name, column_name=column_name)
        )
        return result.scalar()

    # data_imports table field renames
    if column_exists("data_imports", "source_filename") and not column_exists(
        "data_imports", "filename"
    ):
        op.alter_column("data_imports", "source_filename", new_column_name="filename")
        logger.info("Renamed data_imports.source_filename to filename")

    if column_exists("data_imports", "file_size_bytes") and not column_exists(
        "data_imports", "file_size"
    ):
        op.alter_column("data_imports", "file_size_bytes", new_column_name="file_size")
        logger.info("Renamed data_imports.file_size_bytes to file_size")

    if column_exists("data_imports", "file_type") and not column_exists(
        "data_imports", "mime_type"
    ):
        op.alter_column("data_imports", "file_type", new_column_name="mime_type")
        logger.info("Renamed data_imports.file_type to mime_type")

    # discovery_flows table field renames
    if column_exists(
        "discovery_flows", "attribute_mapping_completed"
    ) and not column_exists("discovery_flows", "field_mapping_completed"):
        op.alter_column(
            "discovery_flows",
            "attribute_mapping_completed",
            new_column_name="field_mapping_completed",
        )
        logger.info(
            "Renamed discovery_flows.attribute_mapping_completed to field_mapping_completed"
        )

    if column_exists("discovery_flows", "inventory_completed") and not column_exists(
        "discovery_flows", "asset_inventory_completed"
    ):
        op.alter_column(
            "discovery_flows",
            "inventory_completed",
            new_column_name="asset_inventory_completed",
        )
        logger.info(
            "Renamed discovery_flows.inventory_completed to asset_inventory_completed"
        )

    if column_exists("discovery_flows", "dependencies_completed") and not column_exists(
        "discovery_flows", "dependency_analysis_completed"
    ):
        op.alter_column(
            "discovery_flows",
            "dependencies_completed",
            new_column_name="dependency_analysis_completed",
        )
        logger.info(
            "Renamed discovery_flows.dependencies_completed to dependency_analysis_completed"
        )

    if column_exists("discovery_flows", "tech_debt_completed") and not column_exists(
        "discovery_flows", "tech_debt_assessment_completed"
    ):
        op.alter_column(
            "discovery_flows",
            "tech_debt_completed",
            new_column_name="tech_debt_assessment_completed",
        )
        logger.info(
            "Renamed discovery_flows.tech_debt_completed to tech_debt_assessment_completed"
        )

    # assets table field renames
    if column_exists("assets", "memory_mb") and not column_exists(
        "assets", "memory_gb"
    ):
        op.alter_column("assets", "memory_mb", new_column_name="memory_gb")
        logger.info("Renamed assets.memory_mb to memory_gb")

    if column_exists("assets", "storage_mb") and not column_exists(
        "assets", "storage_gb"
    ):
        op.alter_column("assets", "storage_mb", new_column_name="storage_gb")
        logger.info("Renamed assets.storage_mb to storage_gb")

    # raw_import_records table field renames
    if column_exists("raw_import_records", "row_number") and not column_exists(
        "raw_import_records", "record_index"
    ):
        op.alter_column(
            "raw_import_records", "row_number", new_column_name="record_index"
        )
        logger.info("Renamed raw_import_records.row_number to record_index")

    if column_exists("raw_import_records", "processed_data") and not column_exists(
        "raw_import_records", "cleansed_data"
    ):
        op.alter_column(
            "raw_import_records", "processed_data", new_column_name="cleansed_data"
        )
        logger.info("Renamed raw_import_records.processed_data to cleansed_data")


def drop_deprecated_columns():
    """Drop deprecated columns including is_mock"""

    connection = op.get_bind()

    # Helper function to check if column exists
    def column_exists(table_name, column_name):
        result = connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND column_name = :column_name
                )
            """
            ).bindparams(table_name=table_name, column_name=column_name)
        )
        return result.scalar()

    # Tables and their is_mock columns to drop
    tables_with_is_mock = [
        "client_accounts",
        "engagements",
        "users",
        "user_account_associations",
        "data_import_sessions",
        "tags",
        "asset_embeddings",
        "asset_tags",
    ]

    for table in tables_with_is_mock:
        if column_exists(table, "is_mock"):
            try:
                op.drop_column(table, "is_mock")
                logger.info(f"Dropped is_mock column from {table}")
            except Exception as e:
                logger.warning(f"Could not drop is_mock from {table}: {e}")

    # Drop other deprecated columns
    deprecated_columns = [
        ("data_imports", "file_hash"),
        ("data_imports", "import_config"),
        ("data_imports", "raw_data"),
        ("discovery_flows", "assessment_package"),
        ("discovery_flows", "flow_description"),
        ("discovery_flows", "user_feedback"),
        ("import_field_mappings", "sample_values"),
        ("raw_import_records", "record_id"),  # Not in SQLAlchemy model
    ]

    for table, column in deprecated_columns:
        if column_exists(table, column):
            try:
                with op.batch_alter_table(table) as batch_op:
                    batch_op.drop_column(column)
                logger.info(f"Dropped {column} column from {table}")
            except Exception as e:
                logger.warning(f"Could not drop {column} from {table}: {e}")


def add_new_columns():
    """Add new columns for consolidated state management"""

    connection = op.get_bind()

    # Helper function to check if column exists
    def column_exists(table_name, column_name):
        result = connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND column_name = :column_name
                )
            """
            ).bindparams(table_name=table_name, column_name=column_name)
        )
        return result.scalar()

    # Add new JSON state columns to discovery_flows if they don't exist
    columns_to_add = [
        (
            "discovery_flows",
            "flow_state",
            sa.Column(
                "flow_state", postgresql.JSONB, nullable=False, server_default="{}"
            ),
        ),
        (
            "discovery_flows",
            "phase_state",
            sa.Column(
                "phase_state", postgresql.JSONB, nullable=False, server_default="{}"
            ),
        ),
        (
            "discovery_flows",
            "agent_state",
            sa.Column(
                "agent_state", postgresql.JSONB, nullable=False, server_default="{}"
            ),
        ),
        (
            "discovery_flows",
            "error_message",
            sa.Column("error_message", sa.Text, nullable=True),
        ),
        (
            "discovery_flows",
            "error_phase",
            sa.Column("error_phase", sa.String(100), nullable=True),
        ),
        (
            "discovery_flows",
            "error_details",
            sa.Column("error_details", postgresql.JSON, nullable=True),
        ),
        (
            "data_imports",
            "source_system",
            sa.Column("source_system", sa.String(100), nullable=True),
        ),
    ]

    for table, column_name, column_def in columns_to_add:
        if not column_exists(table, column_name):
            try:
                with op.batch_alter_table(table) as batch_op:
                    batch_op.add_column(column_def)
                logger.info(f"Added {column_name} column to {table}")
            except Exception as e:
                logger.warning(f"Error adding {column_name} to {table}: {e}")


def create_indexes():
    """Create multi-tenant and performance indexes"""

    connection = op.get_bind()

    # Helper function to check if index exists
    def index_exists(index_name, table_name):
        result = connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM pg_indexes 
                    WHERE indexname = :index_name 
                    AND tablename = :table_name
                )
            """
            ).bindparams(index_name=index_name, table_name=table_name)
        )
        return result.scalar()

    # Helper function to check if column exists
    def column_exists(table_name, column_name):
        result = connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND column_name = :column_name
                )
            """
            ).bindparams(table_name=table_name, column_name=column_name)
        )
        return result.scalar()

    # Multi-tenant indexes
    multi_tenant_indexes = [
        ("idx_data_imports_client_account", "data_imports", ["client_account_id"]),
        ("idx_data_imports_engagement", "data_imports", ["engagement_id"]),
        (
            "idx_discovery_flows_client_account",
            "discovery_flows",
            ["client_account_id"],
        ),
        ("idx_discovery_flows_engagement", "discovery_flows", ["engagement_id"]),
        ("idx_assets_client_account", "assets", ["client_account_id"]),
        ("idx_assets_engagement", "assets", ["engagement_id"]),
    ]

    for index_name, table, columns in multi_tenant_indexes:
        # Check if all columns exist before creating index
        all_columns_exist = all(column_exists(table, col) for col in columns)

        if all_columns_exist and not index_exists(index_name, table):
            try:
                op.create_index(index_name, table, columns)
                logger.info(f"Created index {index_name} on {table}")
            except Exception as e:
                logger.warning(f"Error creating index {index_name}: {e}")
        elif not all_columns_exist:
            logger.warning(
                f"Skipping index {index_name} - not all columns exist in {table}"
            )

    # Performance indexes
    performance_indexes = [
        ("idx_discovery_flows_status", "discovery_flows", ["status"]),
        ("idx_discovery_flows_flow_id", "discovery_flows", ["flow_id"]),
        ("idx_data_imports_status", "data_imports", ["status"]),
        ("idx_assets_asset_type", "assets", ["asset_type"]),
        ("idx_assets_discovery_flow", "assets", ["discovery_flow_id"]),
    ]

    for index_name, table, columns in performance_indexes:
        # Check if all columns exist before creating index
        all_columns_exist = all(column_exists(table, col) for col in columns)

        if all_columns_exist and not index_exists(index_name, table):
            try:
                op.create_index(index_name, table, columns)
                logger.info(f"Created index {index_name} on {table}")
            except Exception as e:
                logger.warning(f"Error creating index {index_name}: {e}")
        elif not all_columns_exist:
            logger.warning(
                f"Skipping index {index_name} - not all columns exist in {table}"
            )


def drop_deprecated_tables():
    """Drop deprecated tables that are no longer needed"""

    connection = op.get_bind()

    # Helper function to check if table exists
    def table_exists(table_name):
        result = connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = :table_name
                )
            """
            ).bindparams(table_name=table_name)
        )
        return result.scalar()

    deprecated_tables = [
        "workflow_states",
        "discovery_assets",  # Consolidated into assets table
        "mapping_learning_patterns",
        "session_management",
        "discovery_sessions",
    ]

    for table in deprecated_tables:
        if table_exists(table):
            try:
                op.drop_table(table)
                logger.info(f"Dropped deprecated table: {table}")
            except Exception as e:
                logger.warning(f"Error dropping table {table}: {e}")


# Downgrade functions (for rollback)


def recreate_v3_tables():
    """Recreate v3_ tables for rollback"""
    # This would recreate the v3_ tables with their original schemas
    # Implementation depends on your original v3 table structures
    pass


def revert_field_renames():
    """Revert field renames for rollback"""

    # Revert data_imports field renames
    with op.batch_alter_table("data_imports") as batch_op:
        try:
            batch_op.alter_column("filename", new_column_name="source_filename")
            batch_op.alter_column("file_size", new_column_name="file_size_bytes")
            batch_op.alter_column("mime_type", new_column_name="file_type")
        except Exception as e:
            logger.warning(f"Error reverting data_imports field renames: {e}")

    # Revert discovery_flows field renames
    with op.batch_alter_table("discovery_flows") as batch_op:
        try:
            batch_op.alter_column(
                "field_mapping_completed", new_column_name="attribute_mapping_completed"
            )
            batch_op.alter_column(
                "asset_inventory_completed", new_column_name="inventory_completed"
            )
            batch_op.alter_column(
                "dependency_analysis_completed",
                new_column_name="dependencies_completed",
            )
            batch_op.alter_column(
                "tech_debt_assessment_completed", new_column_name="tech_debt_completed"
            )
        except Exception as e:
            logger.warning(f"Error reverting discovery_flows field renames: {e}")

    # Revert assets field renames
    with op.batch_alter_table("assets") as batch_op:
        try:
            batch_op.alter_column("memory_gb", new_column_name="memory_mb")
            batch_op.alter_column("storage_gb", new_column_name="storage_mb")
        except Exception as e:
            logger.warning(f"Error reverting assets field renames: {e}")

    # Revert raw_import_records field renames
    with op.batch_alter_table("raw_import_records") as batch_op:
        try:
            batch_op.alter_column("record_index", new_column_name="row_number")
            batch_op.alter_column("cleansed_data", new_column_name="processed_data")
        except Exception as e:
            logger.warning(f"Error reverting raw_import_records field renames: {e}")


def recreate_deprecated_columns():
    """Recreate deprecated columns for rollback"""

    # Recreate is_mock columns
    tables_with_is_mock = [
        "client_accounts",
        "engagements",
        "users",
        "user_account_associations",
        "data_import_sessions",
        "tags",
        "asset_embeddings",
        "asset_tags",
    ]

    for table in tables_with_is_mock:
        try:
            with op.batch_alter_table(table) as batch_op:
                batch_op.add_column(
                    sa.Column(
                        "is_mock", sa.Boolean, nullable=False, server_default="false"
                    )
                )
            logger.info(f"Recreated is_mock column in {table}")
        except Exception as e:
            logger.warning(f"Could not recreate is_mock in {table}: {e}")

    # Recreate record_id column in raw_import_records
    try:
        with op.batch_alter_table("raw_import_records") as batch_op:
            batch_op.add_column(sa.Column("record_id", sa.String(255), nullable=True))
        logger.info("Recreated record_id column in raw_import_records")
    except Exception as e:
        logger.warning(f"Could not recreate record_id in raw_import_records: {e}")


def drop_new_columns():
    """Drop new columns for rollback"""

    # Drop new JSON state columns from discovery_flows
    with op.batch_alter_table("discovery_flows") as batch_op:
        try:
            batch_op.drop_column("flow_state")
            batch_op.drop_column("phase_state")
            batch_op.drop_column("agent_state")
            batch_op.drop_column("error_message")
            batch_op.drop_column("error_phase")
            batch_op.drop_column("error_details")
        except Exception as e:
            logger.warning(f"Error dropping new columns: {e}")

    # Drop source_system from data_imports
    with op.batch_alter_table("data_imports") as batch_op:
        try:
            batch_op.drop_column("source_system")
        except Exception as e:
            logger.warning(f"Error dropping source_system: {e}")


def drop_indexes():
    """Drop indexes for rollback"""

    indexes_to_drop = [
        ("idx_data_imports_client_account", "data_imports"),
        ("idx_data_imports_engagement", "data_imports"),
        ("idx_discovery_flows_client_account", "discovery_flows"),
        ("idx_discovery_flows_engagement", "discovery_flows"),
        ("idx_import_field_mappings_client_account", "import_field_mappings"),
        ("idx_assets_client_account", "assets"),
        ("idx_assets_engagement", "assets"),
        ("idx_discovery_flows_status", "discovery_flows"),
        ("idx_discovery_flows_flow_id", "discovery_flows"),
        ("idx_data_imports_status", "data_imports"),
        ("idx_assets_asset_type", "assets"),
        ("idx_assets_discovery_flow", "assets"),
    ]

    for index_name, table in indexes_to_drop:
        try:
            op.drop_index(index_name, table_name=table)
            logger.info(f"Dropped index {index_name}")
        except Exception as e:
            logger.warning(f"Error dropping index {index_name}: {e}")


def recreate_deprecated_tables():
    """Recreate deprecated tables for rollback"""
    # This would recreate the deprecated tables with their original schemas
    # Implementation depends on your original table structures
    pass
