"""Rename source_filename to filename in data_imports table

Revision ID: rename_source_filename
Revises: fix_database_state
Create Date: 2025-06-30 23:45:00.000000

This migration renames source_filename to filename to match the model definition.
"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "rename_source_filename"
down_revision = "fix_database_state"
branch_labels = None
depends_on = None


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
    """Rename source_filename to filename in data_imports table."""
    connection = op.get_bind()

    # Check if source_filename exists and filename doesn't
    if column_exists(
        connection, "data_imports", "source_filename"
    ) and not column_exists(connection, "data_imports", "filename"):
        print("Renaming column source_filename to filename in data_imports table")
        op.alter_column("data_imports", "source_filename", new_column_name="filename")
    else:
        print("Column already renamed or doesn't need renaming")

    # Also check and rename file_size_bytes to file_size if needed
    if column_exists(
        connection, "data_imports", "file_size_bytes"
    ) and not column_exists(connection, "data_imports", "file_size"):
        print("Renaming column file_size_bytes to file_size in data_imports table")
        op.alter_column("data_imports", "file_size_bytes", new_column_name="file_size")

    # Check and rename file_type to mime_type if needed
    if column_exists(connection, "data_imports", "file_type") and not column_exists(
        connection, "data_imports", "mime_type"
    ):
        print("Renaming column file_type to mime_type in data_imports table")
        op.alter_column("data_imports", "file_type", new_column_name="mime_type")


def downgrade():
    """Revert column names back to original."""
    connection = op.get_bind()

    if column_exists(connection, "data_imports", "filename") and not column_exists(
        connection, "data_imports", "source_filename"
    ):
        op.alter_column("data_imports", "filename", new_column_name="source_filename")

    if column_exists(connection, "data_imports", "file_size") and not column_exists(
        connection, "data_imports", "file_size_bytes"
    ):
        op.alter_column("data_imports", "file_size", new_column_name="file_size_bytes")

    if column_exists(connection, "data_imports", "mime_type") and not column_exists(
        connection, "data_imports", "file_type"
    ):
        op.alter_column("data_imports", "mime_type", new_column_name="file_type")
