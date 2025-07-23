"""Add asset_dependencies table

Revision ID: 015_add_asset_dependencies
Revises: 014_fix_remaining_agent_foreign_keys
Create Date: 2025-01-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '015_add_asset_dependencies'
down_revision: Union[str, None] = '014_fix_remaining_agent_foreign_keys'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create asset_dependencies table
    op.create_table('asset_dependencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('depends_on_asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dependency_type', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['depends_on_asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='migration'
    )
    
    # Create indexes for better query performance
    op.create_index('idx_asset_dependencies_asset_id', 'asset_dependencies', ['asset_id'], schema='migration')
    op.create_index('idx_asset_dependencies_depends_on_asset_id', 'asset_dependencies', ['depends_on_asset_id'], schema='migration')
    op.create_index('idx_asset_dependencies_type', 'asset_dependencies', ['dependency_type'], schema='migration')
    
    # Create unique constraint to prevent duplicate dependencies
    op.create_unique_constraint(
        'uq_asset_dependencies_asset_depends_on',
        'asset_dependencies',
        ['asset_id', 'depends_on_asset_id'],
        schema='migration'
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_asset_dependencies_type', table_name='asset_dependencies', schema='migration')
    op.drop_index('idx_asset_dependencies_depends_on_asset_id', table_name='asset_dependencies', schema='migration')
    op.drop_index('idx_asset_dependencies_asset_id', table_name='asset_dependencies', schema='migration')
    
    # Drop table
    op.drop_table('asset_dependencies', schema='migration')