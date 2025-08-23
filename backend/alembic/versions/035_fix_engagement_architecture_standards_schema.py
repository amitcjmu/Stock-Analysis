"""Fix engagement_architecture_standards table schema to match model

Revision ID: 035_fix_engagement_architecture_standards_schema
Revises: 034_add_client_account_id_to_engagement_standards
Create Date: 2025-08-23 17:55:00.000000

This migration adds all missing columns to the engagement_architecture_standards
table to match the SQLAlchemy model definition.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "035_fix_engagement_architecture_standards_schema"
down_revision = "034_add_client_account_id_to_engagement_standards"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table within the 'migration' schema."""
    bind = op.get_bind()
    try:
        stmt = sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = :table_name
                  AND column_name = :column_name
            )
            """
        )
        result = bind.execute(
            stmt, {"table_name": table_name, "column_name": column_name}
        ).scalar()
        return bool(result)
    except Exception as e:
        print(f"Error checking if column {column_name} exists in {table_name}: {e}")
        return False


def upgrade() -> None:
    """Add missing columns to engagement_architecture_standards table"""

    print("🔄 Fixing engagement_architecture_standards table schema...")

    table_name = "engagement_architecture_standards"

    # Add missing columns
    columns_to_add = [
        (
            "standard_name",
            sa.Column(
                "standard_name",
                sa.String(255),
                nullable=False,
                server_default="Default Standard",
            ),
        ),
        (
            "minimum_requirements",
            sa.Column(
                "minimum_requirements",
                postgresql.JSONB,
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
        ),
        (
            "preferred_patterns",
            sa.Column(
                "preferred_patterns",
                postgresql.JSONB,
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
        ),
        (
            "constraints",
            sa.Column(
                "constraints",
                postgresql.JSONB,
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
        ),
        (
            "compliance_level",
            sa.Column(
                "compliance_level",
                sa.String(50),
                nullable=False,
                server_default="standard",
            ),
        ),
        (
            "priority",
            sa.Column("priority", sa.Integer, nullable=False, server_default="5"),
        ),
        (
            "business_impact",
            sa.Column(
                "business_impact",
                sa.String(50),
                nullable=False,
                server_default="medium",
            ),
        ),
        ("source", sa.Column("source", sa.String(255), nullable=True)),
        ("version", sa.Column("version", sa.String(50), nullable=True)),
        (
            "score_metadata",
            sa.Column(
                "score_metadata",
                postgresql.JSONB,
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
        ),
    ]

    for column_name, column_def in columns_to_add:
        if not column_exists(table_name, column_name):
            op.add_column(table_name, column_def, schema="migration")
            print(f"  ✅ Added column {column_name}")
        else:
            print(f"  ℹ️  Column {column_name} already exists")

    # Rename existing columns to match model
    column_renames = [
        ("mandatory", "is_mandatory"),
    ]

    for old_name, new_name in column_renames:
        if column_exists(table_name, old_name) and not column_exists(
            table_name, new_name
        ):
            op.alter_column(
                table_name, old_name, new_column_name=new_name, schema="migration"
            )
            print(f"  ✅ Renamed column {old_name} to {new_name}")
        elif column_exists(table_name, new_name):
            print(f"  ℹ️  Column {new_name} already exists")

    # Drop columns that don't belong in the model
    columns_to_drop = [
        "supported_versions",
        "requirement_details",
        "created_by",
    ]

    for column_name in columns_to_drop:
        if column_exists(table_name, column_name):
            try:
                op.drop_column(table_name, column_name, schema="migration")
                print(f"  ✅ Dropped unused column {column_name}")
            except Exception as e:
                print(f"  ⚠️  Could not drop column {column_name}: {e}")

    # Remove server defaults after data is populated
    try:
        op.alter_column(
            table_name, "standard_name", server_default=None, schema="migration"
        )
        op.alter_column(
            table_name, "compliance_level", server_default=None, schema="migration"
        )
        op.alter_column(table_name, "priority", server_default=None, schema="migration")
        op.alter_column(
            table_name, "business_impact", server_default=None, schema="migration"
        )
    except Exception:
        pass  # Server defaults might not exist

    print("✅ engagement_architecture_standards schema fixed successfully")


def downgrade() -> None:
    """Revert schema changes"""

    print("🔄 Reverting engagement_architecture_standards schema changes...")

    table_name = "engagement_architecture_standards"

    # Add back old columns
    columns_to_add_back = [
        (
            "supported_versions",
            sa.Column("supported_versions", postgresql.JSONB, nullable=True),
        ),
        (
            "requirement_details",
            sa.Column("requirement_details", postgresql.JSONB, nullable=True),
        ),
        ("created_by", sa.Column("created_by", sa.String(100), nullable=True)),
    ]

    for column_name, column_def in columns_to_add_back:
        if not column_exists(table_name, column_name):
            op.add_column(table_name, column_def, schema="migration")
            print(f"  ✅ Restored column {column_name}")

    # Rename columns back
    column_renames = [
        ("is_mandatory", "mandatory"),
    ]

    for new_name, old_name in column_renames:
        if column_exists(table_name, new_name):
            op.alter_column(
                table_name, new_name, new_column_name=old_name, schema="migration"
            )
            print(f"  ✅ Renamed column {new_name} back to {old_name}")

    # Drop added columns
    columns_to_drop = [
        "standard_name",
        "minimum_requirements",
        "preferred_patterns",
        "constraints",
        "compliance_level",
        "priority",
        "business_impact",
        "source",
        "version",
        "score_metadata",
    ]

    for column_name in columns_to_drop:
        if column_exists(table_name, column_name):
            try:
                op.drop_column(table_name, column_name, schema="migration")
                print(f"  ✅ Dropped column {column_name}")
            except Exception as e:
                print(f"  ⚠️  Could not drop column {column_name}: {e}")

    print("✅ Schema revert completed")
