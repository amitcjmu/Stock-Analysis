"""Add source_system column to data_imports table

Revision ID: add_source_system_column
Revises: rename_source_filename
Create Date: 2025-06-30 23:50:00.000000

This migration adds the missing source_system column to data_imports table.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_source_system_column'
down_revision = 'rename_source_filename'
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
    """Add source_system column to data_imports table."""
    connection = op.get_bind()
    
    # Check if source_system column doesn't exist
    if not column_exists(connection, 'data_imports', 'source_system'):
        print("Adding source_system column to data_imports table")
        op.add_column('data_imports', sa.Column('source_system', sa.String(100), nullable=True))
    else:
        print("source_system column already exists")


def downgrade():
    """Remove source_system column from data_imports table."""
    connection = op.get_bind()
    
    if column_exists(connection, 'data_imports', 'source_system'):
        op.drop_column('data_imports', 'source_system')