"""Ensure migration schema exists

Revision ID: 000_ensure_migration_schema
Revises: 
Create Date: 2025-01-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '000_ensure_migration_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create migration schema if it doesn't exist
    op.execute("CREATE SCHEMA IF NOT EXISTS migration")
    
    # Set search path for the database
    op.execute("ALTER DATABASE migration_db SET search_path TO migration, public")
    
    # Note: This migration should run FIRST before any other migrations
    # to ensure all tables are created in the migration schema


def downgrade():
    # We don't want to drop the schema on downgrade as it would drop all tables
    pass