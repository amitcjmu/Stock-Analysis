"""initial_core_tables_and_base_models

Revision ID: 02a9d3783de8
Revises: 
Create Date: 2025-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '02a9d3783de8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Initial migration with core tables for fresh deployments
    This ensures Railway, AWS, and other deployments have base tables
    """
    
    # =============================================================================
    # CORE FOUNDATION TABLES
    # =============================================================================
    
    # Create client_accounts table
    op.create_table('client_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_client_accounts_id'), 'client_accounts', ['id'], unique=False)
    op.create_index(op.f('ix_client_accounts_name'), 'client_accounts', ['name'], unique=True)

    # Create engagements table
    op.create_table('engagements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_engagements_client_account_id'), 'engagements', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_engagements_id'), 'engagements', ['id'], unique=False)
    op.create_index(op.f('ix_engagements_name'), 'engagements', ['name'], unique=False)

    # Create basic assets table (will be enhanced in later migration)
    op.create_table('assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('asset_type', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assets_client_account_id'), 'assets', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_assets_engagement_id'), 'assets', ['engagement_id'], unique=False)
    op.create_index(op.f('ix_assets_id'), 'assets', ['id'], unique=False)
    op.create_index(op.f('ix_assets_name'), 'assets', ['name'], unique=False)

    print("✅ Core tables migration completed successfully!")
    print("✅ Client accounts, engagements, and basic assets tables created")
    print("✅ Ready for master flow architecture enhancement")


def downgrade():
    """Rollback core tables"""
    op.drop_table('assets')
    op.drop_table('engagements')
    op.drop_table('client_accounts') 