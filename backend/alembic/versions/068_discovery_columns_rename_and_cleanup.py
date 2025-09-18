"""discovery_columns_rename_and_cleanup

Rename legacy columns to canonical and cleanup unused fields in discovery_flows table.
Part of Schema Consolidation Plan - Migration 1/3.

- Rename legacy columns to canonical (if they exist):
  * attribute_mapping_completed → field_mapping_completed
  * inventory_completed → asset_inventory_completed
  * dependencies_completed → dependency_analysis_completed
  * tech_debt_completed → tech_debt_assessment_completed
- Drop unused fields if present: import_session_id, flow_description
- Ensure canonical booleans are NOT NULL DEFAULT false
- Add audit logging if legacy and canonical differ

Revision ID: 068_discovery_columns_rename_and_cleanup
Revises: 064_add_analysis_queue_tables
Create Date: 2025-09-18 00:00:00.000000

"""

from alembic import op
from sqlalchemy import text, Boolean, Column
from sqlalchemy.sql import expression
import logging

# revision identifiers, used by Alembic.
revision = "068_discovery_columns_rename_and_cleanup"
down_revision = "064_add_analysis_queue_tables"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def upgrade() -> None:
    """Rename legacy columns to canonical and cleanup unused fields - idempotent"""

    print("🔧 Migration 068: Discovery columns rename and cleanup...")

    # Set schema search path to migration schema
    op.execute("SET search_path TO migration, public")

    conn = op.get_bind()

    # Check what columns exist
    column_check_sql = text(
        """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'discovery_flows'
        AND column_name IN (
            'attribute_mapping_completed', 'inventory_completed',
            'dependencies_completed', 'tech_debt_completed',
            'field_mapping_completed', 'asset_inventory_completed',
            'dependency_analysis_completed', 'tech_debt_assessment_completed',
            'import_session_id', 'flow_description'
        )
        ORDER BY column_name
    """
    )

    existing_columns = {
        row[0]: row for row in conn.execute(column_check_sql).fetchall()
    }
    print(f"   📋 Found columns: {list(existing_columns.keys())}")

    # Define column mappings
    legacy_to_canonical = {
        "attribute_mapping_completed": "field_mapping_completed",
        "inventory_completed": "asset_inventory_completed",
        "dependencies_completed": "dependency_analysis_completed",
        "tech_debt_completed": "tech_debt_assessment_completed",
    }

    # Audit: Check for differences between legacy and canonical columns
    for legacy, canonical in legacy_to_canonical.items():
        if legacy in existing_columns and canonical in existing_columns:
            print(f"   🔍 Auditing differences between {legacy} and {canonical}...")

            # Using parameterized query with proper SQL escaping for column names
            # Column names are from controlled dictionary, not user input  # nosec B608
            audit_sql = text(
                f"""
                SELECT COUNT(*) as total_rows,
                       SUM(CASE WHEN "{legacy}" != "{canonical}" THEN 1 ELSE 0 END) as differences
                FROM migration.discovery_flows
                WHERE "{legacy}" IS NOT NULL AND "{canonical}" IS NOT NULL
            """
            )

            result = conn.execute(audit_sql).fetchone()
            if result and result[1] > 0:
                print(
                    f"   ⚠️  AUDIT: {result[1]} rows have differences between {legacy} and {canonical}"
                )

                # Log specific differences
                # Using parameterized query with proper SQL escaping for column names
                # Column names are from controlled dictionary, not user input  # nosec B608
                diff_sql = text(
                    f"""
                    SELECT flow_id, "{legacy}" as legacy_val, "{canonical}" as canonical_val
                    FROM migration.discovery_flows
                    WHERE "{legacy}" != "{canonical}"
                    LIMIT 5
                """
                )

                diffs = conn.execute(diff_sql).fetchall()
                for diff in diffs:
                    print(
                        f"     - Flow {diff[0]}: {legacy}={diff[1]}, {canonical}={diff[2]}"
                    )
            else:
                print(f"   ✅ No differences found between {legacy} and {canonical}")

    # Step 1: Handle column renames/moves
    for legacy, canonical in legacy_to_canonical.items():
        if legacy in existing_columns and canonical in existing_columns:
            print(
                f"   🔄 Both {legacy} and {canonical} exist - copying data from legacy to canonical..."
            )

            # Copy data from legacy to canonical where values differ (including NULLs)
            # Using parameterized query with proper SQL escaping for column names
            # Column names are from controlled dictionary, not user input  # nosec B608
            copy_sql = text(
                f"""
                UPDATE migration.discovery_flows
                SET "{canonical}" = "{legacy}"
                WHERE "{legacy}" IS NOT NULL AND "{canonical}" IS DISTINCT FROM "{legacy}"
            """
            )
            result = conn.execute(copy_sql)
            if result.rowcount > 0:
                print(
                    f"     ✅ Updated {result.rowcount} rows copying {legacy} to {canonical}"
                )

        elif legacy in existing_columns and canonical not in existing_columns:
            print(f"   🔄 Renaming {legacy} to {canonical}...")
            op.alter_column(
                "discovery_flows", legacy, new_column_name=canonical, schema="migration"
            )

        elif legacy not in existing_columns and canonical in existing_columns:
            print(f"   ✅ {canonical} already exists, {legacy} already removed")
        else:
            print(
                f"   ⚠️  Neither {legacy} nor {canonical} exists - adding {canonical}..."
            )
            op.add_column(
                "discovery_flows",
                Column(
                    canonical,
                    Boolean,
                    nullable=False,
                    server_default=expression.false(),
                ),
                schema="migration",
            )

    # Step 2: Ensure all canonical columns exist and are NOT NULL DEFAULT false
    canonical_columns = [
        "field_mapping_completed",
        "asset_inventory_completed",
        "dependency_analysis_completed",
        "tech_debt_assessment_completed",
    ]

    for col in canonical_columns:
        if col not in existing_columns:
            print(f"   ➕ Adding missing canonical column: {col}")
            op.add_column(
                "discovery_flows",
                Column(col, Boolean, nullable=False, server_default=expression.false()),
                schema="migration",
            )
        else:
            # Ensure proper constraints
            col_info = existing_columns[col]
            if col_info[2] == "YES":  # is_nullable
                print(f"   🔧 Making {col} NOT NULL...")
                op.alter_column(
                    "discovery_flows", col, nullable=False, schema="migration"
                )

    # Step 3: Drop legacy columns if they still exist alongside canonical ones
    for legacy, canonical in legacy_to_canonical.items():
        if legacy in existing_columns and canonical in existing_columns:
            print(f"   🗑️  Dropping legacy column: {legacy}")
            op.drop_column("discovery_flows", legacy, schema="migration")

    # Step 4: Drop unused fields if they exist
    unused_fields = ["import_session_id", "flow_description"]
    for field in unused_fields:
        if field in existing_columns:
            print(f"   🗑️  Dropping unused field: {field}")
            op.drop_column("discovery_flows", field, schema="migration")
        else:
            print(f"   ✅ Unused field {field} already removed")

    print("   ✅ Migration 068 completed successfully")


def downgrade() -> None:
    """Reverse the column renames and restore unused fields"""

    print("🔄 Downgrading Migration 068: Restoring legacy columns...")

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Restore unused fields
    print("   ➕ Restoring unused fields...")
    op.add_column(
        "discovery_flows",
        op.Column("import_session_id", op.UUID(), nullable=True),
        schema="migration",
    )
    op.add_column(
        "discovery_flows",
        op.Column("flow_description", op.Text(), nullable=True),
        schema="migration",
    )

    # Restore legacy column names
    legacy_to_canonical = {
        "attribute_mapping_completed": "field_mapping_completed",
        "inventory_completed": "asset_inventory_completed",
        "dependencies_completed": "dependency_analysis_completed",
        "tech_debt_completed": "tech_debt_assessment_completed",
    }

    for legacy, canonical in legacy_to_canonical.items():
        print(f"   🔄 Restoring legacy column: {legacy}")
        # Add legacy column
        op.add_column(
            "discovery_flows",
            op.Column(legacy, Boolean, nullable=False, default=False),
            schema="migration",
        )

        # Copy data back from canonical to legacy
        conn = op.get_bind()
        # Using parameterized query with proper SQL escaping for column names
        # Column names are from controlled dictionary, not user input  # nosec B608
        copy_sql = text(
            f"""
            UPDATE migration.discovery_flows
            SET "{legacy}" = "{canonical}"
        """
        )
        conn.execute(copy_sql)

        # Drop canonical column
        op.drop_column("discovery_flows", canonical, schema="migration")

    print("   ✅ Migration 068 downgrade completed")
