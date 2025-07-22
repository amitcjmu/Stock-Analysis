"""Add error handling columns to data_imports table

Revision ID: add_error_handling_columns
Revises: add_source_system_column
Create Date: 2025-06-30 23:55:00.000000

This migration adds the missing error_message and error_details columns to data_imports table.
"""
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_error_handling_columns'
down_revision = 'add_source_system_column'
branch_labels = None
depends_on = None


def column_exists(connection, table_name, column_name):
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = :table_name 
            AND column_name = :column_name
        )
    """), {"table_name": table_name, "column_name": column_name})
    return result.scalar()


def upgrade():
    """Add error handling columns to data_imports table."""
    connection = op.get_bind()
    
    # Add error_message column if it doesn't exist
    if not column_exists(connection, 'data_imports', 'error_message'):
        print("Adding error_message column to data_imports table")
        op.add_column('data_imports', sa.Column('error_message', sa.Text(), nullable=True))
    else:
        print("error_message column already exists")
    
    # Add error_details column if it doesn't exist
    if not column_exists(connection, 'data_imports', 'error_details'):
        print("Adding error_details column to data_imports table")
        op.add_column('data_imports', sa.Column('error_details', sa.JSON(), nullable=True))
    else:
        print("error_details column already exists")


def downgrade():
    """Remove error handling columns from data_imports table."""
    connection = op.get_bind()
    
    if column_exists(connection, 'data_imports', 'error_message'):
        op.drop_column('data_imports', 'error_message')
    
    if column_exists(connection, 'data_imports', 'error_details'):
        op.drop_column('data_imports', 'error_details')