"""Remove data_import_sessions table

Revision ID: remove_sessions_table
Revises: 20250107_fix_master_flow_relationships
Create Date: 2025-01-08 01:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'remove_sessions_table'
down_revision = '20250107_fix_master_flow_relationships'
branch_labels = None
depends_on = None


def upgrade():
    """Drop the data_import_sessions table as it's legacy and no longer used."""
    
    # Drop the table if it exists
    op.execute("""
        DROP TABLE IF EXISTS data_import_sessions CASCADE;
    """)
    
    print("✅ Removed data_import_sessions table")


def downgrade():
    """Recreate data_import_sessions table structure if needed for rollback."""
    
    # Note: This is a simplified recreation - full structure would be more complex
    # In practice, this table should not be recreated as it's legacy
    op.create_table('data_import_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    print("⚠️ Recreated data_import_sessions table (legacy)")