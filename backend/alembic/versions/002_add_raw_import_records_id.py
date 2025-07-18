"""add raw_import_records_id to assets

Revision ID: 002_add_raw_import_records_id
Revises: 001_initial_schema
Create Date: 2025-07-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_raw_import_records_id'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column already exists before adding it
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'assets' AND column_name = 'raw_import_records_id'
    """))
    
    if not result.fetchone():
        # Add raw_import_records_id column to assets table
        op.add_column('assets', sa.Column('raw_import_records_id', postgresql.UUID(as_uuid=True), nullable=True, comment='The raw import record this asset was created from.'))
        
        # Create foreign key constraint
        op.create_foreign_key('fk_assets_raw_import_records', 'assets', 'raw_import_records', ['raw_import_records_id'], ['id'])
    else:
        # Column already exists, check if foreign key constraint exists
        fk_result = connection.execute(sa.text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'assets' AND constraint_name = 'fk_assets_raw_import_records'
        """))
        
        if not fk_result.fetchone():
            # Create foreign key constraint if it doesn't exist
            op.create_foreign_key('fk_assets_raw_import_records', 'assets', 'raw_import_records', ['raw_import_records_id'], ['id'])


def downgrade():
    # Check if foreign key constraint exists before removing it
    connection = op.get_bind()
    fk_result = connection.execute(sa.text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name = 'assets' AND constraint_name = 'fk_assets_raw_import_records'
    """))
    
    if fk_result.fetchone():
        # Remove foreign key constraint
        op.drop_constraint('fk_assets_raw_import_records', 'assets', type_='foreignkey')
    
    # Check if column exists before removing it
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'assets' AND column_name = 'raw_import_records_id'
    """))
    
    if result.fetchone():
        # Remove column
        op.drop_column('assets', 'raw_import_records_id')