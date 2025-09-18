"""add_missing_cfse_fields_if_needed

Add missing fields to crewai_flow_state_extensions table if they don't exist.
Part of Schema Consolidation Plan - Migration 3/3.

Fields to add (idempotent):
- collection_flow_id UUID
- automation_tier VARCHAR(50)
- collection_quality_score FLOAT
- data_collection_metadata JSONB DEFAULT '{}'

Revision ID: 070_add_missing_cfse_fields_if_needed
Revises: 069_fix_discovery_master_fk_swap
Create Date: 2025-09-18 00:02:00.000000

"""

from alembic import op
from sqlalchemy import text, Float, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
import logging

# revision identifiers, used by Alembic.
revision = "070_add_missing_cfse_fields_if_needed"
down_revision = "069_fix_discovery_master_fk_swap"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def upgrade() -> None:
    """Add missing fields to crewai_flow_state_extensions - idempotent"""

    print("🔧 Migration 070: Add missing CFSE fields if needed...")

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    conn = op.get_bind()

    # Check what columns already exist
    column_check_sql = text(
        """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'crewai_flow_state_extensions'
        AND column_name IN (
            'collection_flow_id',
            'automation_tier',
            'collection_quality_score',
            'data_collection_metadata'
        )
        ORDER BY column_name
    """
    )

    existing_columns = {
        row[0]: row for row in conn.execute(column_check_sql).fetchall()
    }
    print(f"   📋 Existing columns: {list(existing_columns.keys())}")

    # Define required columns with their specifications
    required_columns = {
        "collection_flow_id": {
            "type": UUID(),
            "nullable": True,
            "description": "Foreign key to collection_flows.id",
        },
        "automation_tier": {
            "type": String(50),
            "nullable": True,
            "description": "Automation tier classification",
        },
        "collection_quality_score": {
            "type": Float,
            "nullable": True,
            "description": "Quality score for data collection",
        },
        "data_collection_metadata": {
            "type": JSONB,
            "nullable": True,
            "server_default": text("'{}'::jsonb"),
            "description": "Metadata for data collection processes",
        },
    }

    # Add missing columns
    columns_added = []
    for col_name, col_spec in required_columns.items():
        if col_name not in existing_columns:
            print(f"   ➕ Adding column: {col_name}")

            # Handle server_default parameter
            if "server_default" in col_spec:
                op.add_column(
                    "crewai_flow_state_extensions",
                    op.Column(
                        col_name,
                        col_spec["type"],
                        nullable=col_spec["nullable"],
                        server_default=col_spec["server_default"],
                        comment=col_spec["description"],
                    ),
                    schema="migration",
                )
            else:
                op.add_column(
                    "crewai_flow_state_extensions",
                    op.Column(
                        col_name,
                        col_spec["type"],
                        nullable=col_spec["nullable"],
                        comment=col_spec["description"],
                    ),
                    schema="migration",
                )

            columns_added.append(col_name)
        else:
            existing_info = existing_columns[col_name]
            print(
                f"   ✅ Column {col_name} already exists: {existing_info[1]} (nullable: {existing_info[2]})"
            )

    # Add indexes for performance if columns were added
    if "collection_flow_id" in columns_added:
        print("   🔍 Adding index on collection_flow_id...")
        try:
            op.create_index(
                "ix_crewai_flow_state_extensions_collection_flow_id",
                "crewai_flow_state_extensions",
                ["collection_flow_id"],
                schema="migration",
                if_not_exists=True,
            )
        except Exception as e:
            if "already exists" not in str(e).lower():
                print(f"     ⚠️  Index creation warning: {e}")

    if "automation_tier" in columns_added:
        print("   🔍 Adding index on automation_tier...")
        try:
            op.create_index(
                "ix_crewai_flow_state_extensions_automation_tier",
                "crewai_flow_state_extensions",
                ["automation_tier"],
                schema="migration",
                if_not_exists=True,
            )
        except Exception as e:
            if "already exists" not in str(e).lower():
                print(f"     ⚠️  Index creation warning: {e}")

    # Add FK constraint for collection_flow_id if column was added and collection_flows table exists
    if "collection_flow_id" in columns_added:
        print("   🔗 Checking if collection_flows table exists for FK constraint...")

        table_exists_sql = text(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'migration'
            AND table_name = 'collection_flows'
        """
        )

        if conn.execute(table_exists_sql).fetchone():
            print("   🔗 Adding FK constraint to collection_flows...")
            try:
                op.create_foreign_key(
                    "fk_crewai_flow_ext_collection_flow_id",
                    "crewai_flow_state_extensions",
                    "collection_flows",
                    ["collection_flow_id"],
                    ["id"],
                    ondelete="SET NULL",
                    schema="migration",
                )
                print("     ✅ FK constraint added successfully")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"     ⚠️  FK constraint warning: {e}")
        else:
            print(
                "   ⚠️  collection_flows table does not exist - skipping FK constraint"
            )

    if columns_added:
        print(f"   ✅ Added {len(columns_added)} columns: {', '.join(columns_added)}")
    else:
        print("   ✅ All required columns already exist - no changes needed")

    print("   ✅ Migration 070 completed successfully")


def downgrade() -> None:
    """Remove the added columns and constraints"""

    print("🔄 Downgrading Migration 070: Removing added CFSE fields...")

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # List of columns to remove
    columns_to_remove = [
        "collection_flow_id",
        "automation_tier",
        "collection_quality_score",
        "data_collection_metadata",
    ]

    # Drop FK constraint first
    print("   🗑️  Dropping FK constraint...")
    try:
        op.drop_constraint(
            "fk_crewai_flow_ext_collection_flow_id",
            "crewai_flow_state_extensions",
            schema="migration",
        )
    except Exception as e:
        print(f"     ⚠️  FK constraint drop warning: {e}")

    # Drop indexes
    indexes_to_drop = [
        "ix_crewai_flow_state_extensions_collection_flow_id",
        "ix_crewai_flow_state_extensions_automation_tier",
    ]

    for index_name in indexes_to_drop:
        print(f"   🗑️  Dropping index: {index_name}")
        try:
            op.drop_index(index_name, schema="migration", if_exists=True)
        except Exception as e:
            print(f"     ⚠️  Index drop warning: {e}")

    # Drop columns
    for col_name in columns_to_remove:
        print(f"   🗑️  Dropping column: {col_name}")
        try:
            op.drop_column("crewai_flow_state_extensions", col_name, schema="migration")
        except Exception as e:
            print(f"     ⚠️  Column drop warning: {e}")

    print("   ✅ Migration 070 downgrade completed")
