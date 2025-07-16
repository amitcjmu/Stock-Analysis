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
    # Add raw_import_records_id column to assets table
    op.add_column('assets', sa.Column('raw_import_records_id', postgresql.UUID(as_uuid=True), nullable=True, comment='The raw import record this asset was created from.'))
    
    # Create foreign key constraint
    op.create_foreign_key('fk_assets_raw_import_records', 'assets', 'raw_import_records', ['raw_import_records_id'], ['id'])


def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_assets_raw_import_records', 'assets', type_='foreignkey')
    
    # Remove column
    op.drop_column('assets', 'raw_import_records_id')