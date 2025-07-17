"""add asset uniqueness constraints

Revision ID: 20250117_unique_assets
Revises: latest
Create Date: 2025-01-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250117_unique_assets'
down_revision = 'add_asset_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add unique constraints to prevent duplicate assets"""
    
    # Create unique index on hostname within client/engagement context
    # This ensures no duplicate hostnames for the same client/engagement
    op.create_index(
        'ix_assets_unique_hostname_per_context',
        'assets',
        ['client_account_id', 'engagement_id', 'hostname'],
        unique=True,
        postgresql_where=sa.text("hostname IS NOT NULL AND hostname != ''")
    )
    
    # Create unique index on name within client/engagement context
    # This ensures no duplicate names for the same client/engagement
    op.create_index(
        'ix_assets_unique_name_per_context',
        'assets',
        ['client_account_id', 'engagement_id', 'name'],
        unique=True,
        postgresql_where=sa.text("name IS NOT NULL AND name != ''")
    )
    
    # Create unique index on ip_address within client/engagement context
    # This ensures no duplicate IP addresses for the same client/engagement
    op.create_index(
        'ix_assets_unique_ip_per_context',
        'assets',
        ['client_account_id', 'engagement_id', 'ip_address'],
        unique=True,
        postgresql_where=sa.text("ip_address IS NOT NULL AND ip_address != ''")
    )
    
    # Add check constraint to ensure at least one identifier is present
    op.create_check_constraint(
        'ck_assets_has_identifier',
        'assets',
        sa.text("hostname IS NOT NULL OR name IS NOT NULL OR ip_address IS NOT NULL")
    )


def downgrade() -> None:
    """Remove unique constraints"""
    
    # Drop check constraint
    op.drop_constraint('ck_assets_has_identifier', 'assets')
    
    # Drop unique indexes
    op.drop_index('ix_assets_unique_ip_per_context', table_name='assets')
    op.drop_index('ix_assets_unique_name_per_context', table_name='assets')
    op.drop_index('ix_assets_unique_hostname_per_context', table_name='assets')