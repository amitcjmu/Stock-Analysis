"""Add master_flow_id to assessment_flows table for MFO architecture alignment

Revision ID: 032_add_master_flow_id_to_assessment_flows
Revises: 031_add_flow_deletion_audit_table
Create Date: 2025-08-23 10:00:00.000000

This migration adds the master_flow_id column to the assessment_flows table to align
with the Master Flow Orchestrator (MFO) architecture. This follows the same pattern
used in discovery_flows and collection_flows tables.

The master_flow_id column:
- Is nullable to support existing assessment flows
- Has a foreign key relationship to crewai_flow_state_extensions.flow_id
- Has an index for performance optimization
- Uses CASCADE delete to maintain referential integrity
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "032_add_master_flow_id_to_assessment_flows"
down_revision = "031_add_flow_deletion_audit_table"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str, schema: str = "migration") -> bool:
    """Check if a column exists in the specified table and schema."""
    bind = op.get_bind()
    try:
        stmt = sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = :schema
                AND table_name = :table_name
                AND column_name = :column_name
            )
            """
        )
        result = bind.execute(
            stmt,
            {
                "schema": schema,
                "table_name": table_name,
                "column_name": column_name,
            },
        )
        return result.scalar()
    except Exception:
        return False


def index_exists(index_name: str, table_name: str, schema: str = "migration") -> bool:
    """Check if an index exists in the specified table and schema."""
    bind = op.get_bind()
    try:
        stmt = sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = :schema
                AND tablename = :table_name
                AND indexname = :index_name
            )
            """
        )
        result = bind.execute(
            stmt,
            {
                "schema": schema,
                "table_name": table_name,
                "index_name": index_name,
            },
        )
        return result.scalar()
    except Exception:
        return False


def upgrade() -> None:
    """Add master_flow_id column to assessment_flows table"""

    print("🔄 Adding master_flow_id to assessment_flows table...")

    # Check if column already exists
    if column_exists("assessment_flows", "master_flow_id"):
        print("  ℹ️  Column master_flow_id already exists in assessment_flows")
        return

    # Add the master_flow_id column with foreign key constraint
    # This follows the exact same pattern as discovery_flows and collection_flows
    try:
        op.add_column(
            "assessment_flows",
            sa.Column(
                "master_flow_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,  # Nullable to support existing assessment flows
            ),
            schema="migration",
        )
        print("  ✅ Added master_flow_id column to assessment_flows")
    except Exception as e:
        print(f"  ❌ Failed to add master_flow_id column: {str(e)}")
        raise

    # Add foreign key constraint to crewai_flow_state_extensions.flow_id
    try:
        op.create_foreign_key(
            "fk_assessment_flows_master_flow_id",
            "assessment_flows",
            "crewai_flow_state_extensions",
            ["master_flow_id"],
            ["flow_id"],
            source_schema="migration",
            referent_schema="migration",
            ondelete="CASCADE",
        )
        print("  ✅ Added foreign key constraint for master_flow_id")
    except Exception as e:
        print(f"  ❌ Failed to add foreign key constraint: {str(e)}")
        raise

    # Add index for performance optimization
    index_name = "ix_assessment_flows_master_flow_id"
    if not index_exists(index_name, "assessment_flows"):
        try:
            op.create_index(
                index_name,
                "assessment_flows",
                ["master_flow_id"],
                schema="migration",
            )
            print("  ✅ Added index ix_assessment_flows_master_flow_id")
        except Exception as e:
            print(f"  ❌ Failed to add index: {str(e)}")
            raise
    else:
        print("  ℹ️  Index ix_assessment_flows_master_flow_id already exists")

    print("✅ Successfully added master_flow_id to assessment_flows table")


def downgrade() -> None:
    """Remove master_flow_id column and related constraints from assessment_flows table"""

    print("🔄 Removing master_flow_id from assessment_flows table...")

    # Drop index first
    index_name = "ix_assessment_flows_master_flow_id"
    if index_exists(index_name, "assessment_flows"):
        try:
            op.drop_index(index_name, "assessment_flows", schema="migration")
            print("  ✅ Dropped index ix_assessment_flows_master_flow_id")
        except Exception as e:
            print(f"  ⚠️  Could not drop index: {str(e)}")

    # Drop foreign key constraint
    try:
        op.drop_constraint(
            "fk_assessment_flows_master_flow_id",
            "assessment_flows",
            schema="migration",
            type_="foreignkey",
        )
        print("  ✅ Dropped foreign key constraint for master_flow_id")
    except Exception as e:
        print(f"  ⚠️  Could not drop foreign key constraint: {str(e)}")

    # Drop the column
    if column_exists("assessment_flows", "master_flow_id"):
        try:
            op.drop_column("assessment_flows", "master_flow_id", schema="migration")
            print("  ✅ Dropped master_flow_id column from assessment_flows")
        except Exception as e:
            print(f"  ⚠️  Could not drop column: {str(e)}")
    else:
        print("  ℹ️  Column master_flow_id does not exist in assessment_flows")

    print("✅ Successfully removed master_flow_id from assessment_flows table")
