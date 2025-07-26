"""Add asset_dependencies table

Revision ID: 015_add_asset_dependencies
Revises: 014_fix_remaining_agent_foreign_keys
Create Date: 2025-01-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "015_add_asset_dependencies"
down_revision: Union[str, None] = "014_fix_remaining_agent_foreign_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name):
    """Check if a table exists in the database"""
    bind = op.get_bind()
    try:
        # Use parameterized query with proper escaping
        # Note: table_name is a string literal value, not an identifier
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'migration'
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


def create_table_if_not_exists(table_name, *columns, **kwargs):
    """Create a table only if it doesn't already exist"""
    if not table_exists(table_name):
        op.create_table(table_name, *columns, **kwargs)
    else:
        print(f"Table {table_name} already exists, skipping creation")


def index_exists(index_name, table_name):
    """Check if an index exists on a table"""
    bind = op.get_bind()
    try:
        # Use parameterized query with proper escaping
        # Note: table_name and index_name are string literal values, not identifiers
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE schemaname = 'migration'
                    AND tablename = :table_name
                    AND indexname = :index_name
                )
            """
            ).bindparams(table_name=table_name, index_name=index_name)
        ).scalar()
        return result
    except Exception as e:
        print(f"Error checking if index {index_name} exists on table {table_name}: {e}")
        # If we get an error, assume index exists to avoid trying to create it
        return True


def create_index_if_not_exists(index_name, table_name, columns, **kwargs):
    """Create an index only if it doesn't already exist"""
    if table_exists(table_name) and not index_exists(index_name, table_name):
        op.create_index(index_name, table_name, columns, **kwargs)
    else:
        print(
            f"Index {index_name} already exists or table doesn't exist, skipping creation"
        )


def constraint_exists(constraint_name, table_name):
    """Check if a constraint exists"""
    bind = op.get_bind()
    try:
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.table_constraints
                    WHERE table_schema = 'migration'
                    AND constraint_schema = 'migration'
                    AND table_name = :table_name
                    AND constraint_name = :constraint_name
                )
            """
            ).bindparams(table_name=table_name, constraint_name=constraint_name)
        ).scalar()
        return result
    except Exception as e:
        print(f"Error checking if constraint {constraint_name} exists: {e}")
        # If we get an error, assume constraint exists
        return True


def upgrade() -> None:
    # Create asset_dependencies table
    create_table_if_not_exists(
        "asset_dependencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("depends_on_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dependency_type", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["asset_id"], ["migration.assets.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["depends_on_asset_id"], ["migration.assets.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="migration",
    )

    # Create indexes for better query performance
    create_index_if_not_exists(
        "idx_asset_dependencies_asset_id",
        "asset_dependencies",
        ["asset_id"],
        schema="migration",
    )
    create_index_if_not_exists(
        "idx_asset_dependencies_depends_on_asset_id",
        "asset_dependencies",
        ["depends_on_asset_id"],
        schema="migration",
    )
    create_index_if_not_exists(
        "idx_asset_dependencies_type",
        "asset_dependencies",
        ["dependency_type"],
        schema="migration",
    )

    # Create unique constraint to prevent duplicate dependencies
    if not constraint_exists(
        "uq_asset_dependencies_asset_depends_on", "asset_dependencies"
    ):
        op.create_unique_constraint(
            "uq_asset_dependencies_asset_depends_on",
            "asset_dependencies",
            ["asset_id", "depends_on_asset_id"],
            schema="migration",
        )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        "idx_asset_dependencies_type",
        table_name="asset_dependencies",
        schema="migration",
    )
    op.drop_index(
        "idx_asset_dependencies_depends_on_asset_id",
        table_name="asset_dependencies",
        schema="migration",
    )
    op.drop_index(
        "idx_asset_dependencies_asset_id",
        table_name="asset_dependencies",
        schema="migration",
    )

    # Drop table
    op.drop_table("asset_dependencies", schema="migration")
