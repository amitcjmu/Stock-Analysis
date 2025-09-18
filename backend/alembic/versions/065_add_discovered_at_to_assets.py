"""Add discovered_at column to assets table

Revision ID: 065_add_discovered_at_to_assets
Revises: 064_add_analysis_queue_tables
Create Date: 2025-09-17

"""

import sqlalchemy as sa
from sqlalchemy.sql import func
from alembic import op

# revision identifiers, used by Alembic.
revision = "065_add_discovered_at_to_assets"
down_revision = "064_add_analysis_queue_tables"
branch_labels = None
depends_on = None


def column_exists(table_name, column_name, schema="migration"):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    try:
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = :schema
                    AND table_name = :table_name
                    AND column_name = :column_name
                )
                """
            ).bindparams(schema=schema, table_name=table_name, column_name=column_name)
        ).scalar()
        return result
    except Exception as e:
        print(
            f"Error checking if column {column_name} exists in table {table_name}: {e}"
        )
        # If we get an error, assume column exists to avoid trying to create it
        return True


def upgrade():
    """Add discovered_at column to assets table if it doesn't exist"""

    # Check if discovered_at column already exists
    if not column_exists("assets", "discovered_at"):
        print("Adding discovered_at column to assets table...")

        # Add the discovered_at column with proper timezone and default
        op.add_column(
            "assets",
            sa.Column(
                "discovered_at",
                sa.TIMESTAMP(timezone=True),
                server_default=func.now(),
                nullable=True,
                comment="Timestamp when the asset was first discovered",
            ),
            schema="migration",
        )

        # Update existing records to set discovered_at from discovery_timestamp if available
        bind = op.get_bind()
        bind.execute(
            sa.text(
                """
                UPDATE migration.assets
                SET discovered_at = discovery_timestamp
                WHERE discovered_at IS NULL
                AND discovery_timestamp IS NOT NULL
                """
            )
        )

        # If discovery_timestamp is null, use created_at as fallback
        bind.execute(
            sa.text(
                """
                UPDATE migration.assets
                SET discovered_at = created_at
                WHERE discovered_at IS NULL
                AND created_at IS NOT NULL
                """
            )
        )

        print("Successfully added discovered_at column to assets table")
    else:
        print("discovered_at column already exists in assets table, skipping...")


def downgrade():
    """Remove discovered_at column from assets table"""

    if column_exists("assets", "discovered_at"):
        print("Removing discovered_at column from assets table...")
        op.drop_column("assets", "discovered_at", schema="migration")
        print("Successfully removed discovered_at column from assets table")
    else:
        print("discovered_at column does not exist in assets table, skipping...")
