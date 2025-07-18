"""Add performance indexes for asset queries

Revision ID: add_asset_performance_indexes
Revises: 
Create Date: 2025-01-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'add_asset_performance_indexes'
down_revision = '003_add_assessment_flow_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Add indexes to improve asset query performance"""
    
    # Composite index for multitenancy filtering
    op.create_index(
        'idx_assets_client_engagement',
        'assets',
        ['client_account_id', 'engagement_id'],
        if_not_exists=True
    )
    
    # Index for created_at ordering (used in paginated queries)
    op.create_index(
        'idx_assets_created_at_desc',
        'assets',
        [sa.text('created_at DESC')],
        if_not_exists=True
    )
    
    # Index for asset_type filtering
    op.create_index(
        'idx_assets_type',
        'assets',
        ['asset_type'],
        if_not_exists=True
    )
    
    # Index for status filtering
    op.create_index(
        'idx_assets_status',
        'assets',
        ['status'],
        if_not_exists=True
    )
    
    # Composite index for multitenancy + created_at (covering index)
    op.create_index(
        'idx_assets_client_engagement_created',
        'assets',
        ['client_account_id', 'engagement_id', sa.text('created_at DESC')],
        if_not_exists=True
    )


def downgrade():
    """Remove performance indexes"""
    op.drop_index('idx_assets_client_engagement_created', table_name='assets')
    op.drop_index('idx_assets_status', table_name='assets')
    op.drop_index('idx_assets_type', table_name='assets')
    op.drop_index('idx_assets_created_at_desc', table_name='assets')
    op.drop_index('idx_assets_client_engagement', table_name='assets')