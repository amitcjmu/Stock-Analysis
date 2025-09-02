"""fix_application_name_variants_timestamps

Revision ID: 042_fix_application_name_variants_timestamps
Revises: 041_add_hybrid_properties
Create Date: 2025-09-02 21:59:59.015918

CC: Targeted migration to add missing timestamp columns to application_name_variants table.
This replaces the dangerous auto-generated migration that would have dropped production tables.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "042_fix_application_name_variants_timestamps"
down_revision = "041_add_hybrid_properties"
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if a table exists"""
    bind = op.get_bind()
    try:
        # Check public schema by default
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = :table_name
                )
            """
            ).bindparams(table_name=table_name)
        ).scalar()
        return result
    except Exception as e:
        print(f"Error checking if table {table_name} exists: {e}")
        # If we get an error, assume table exists to avoid trying to create it
        return True


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    try:
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = :table_name
                    AND column_name = :column_name
                )
            """
            ).bindparams(table_name=table_name, column_name=column_name)
        ).scalar()
        return result
    except Exception as e:
        print(
            f"Error checking if column {column_name} exists in table {table_name}: {e}"
        )
        return True


def upgrade() -> None:
    """Add missing timestamp columns to application_name_variants table"""

    # Only add columns if the table exists and columns don't already exist
    if table_exists("application_name_variants"):
        if not column_exists("application_name_variants", "created_at"):
            op.add_column(
                "application_name_variants",
                sa.Column(
                    "created_at",
                    sa.DateTime(timezone=True),
                    server_default=sa.text("now()"),
                    nullable=False,
                ),
            )
            print("Added created_at column to application_name_variants")
        else:
            print("created_at column already exists in application_name_variants")

        if not column_exists("application_name_variants", "updated_at"):
            op.add_column(
                "application_name_variants",
                sa.Column(
                    "updated_at",
                    sa.DateTime(timezone=True),
                    server_default=sa.text("now()"),
                    nullable=False,
                ),
            )
            print("Added updated_at column to application_name_variants")
        else:
            print("updated_at column already exists in application_name_variants")

        # Backfill any NULL values (shouldn't be any with server_default, but just in case)
        op.execute(
            """
            UPDATE application_name_variants
            SET created_at = NOW()
            WHERE created_at IS NULL;
            """
        )
        op.execute(
            """
            UPDATE application_name_variants
            SET updated_at = NOW()
            WHERE updated_at IS NULL;
            """
        )
    else:
        print(
            "Table application_name_variants does not exist, skipping column additions"
        )


def downgrade() -> None:
    """Remove timestamp columns from application_name_variants table"""

    if table_exists("application_name_variants"):
        if column_exists("application_name_variants", "updated_at"):
            op.drop_column("application_name_variants", "updated_at")
            print("Dropped updated_at column from application_name_variants")

        if column_exists("application_name_variants", "created_at"):
            op.drop_column("application_name_variants", "created_at")
            print("Dropped created_at column from application_name_variants")
    else:
        print("Table application_name_variants does not exist, skipping column drops")
