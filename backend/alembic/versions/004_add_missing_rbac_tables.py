"""Add missing RBAC tables (user_roles and user_account_associations)

Revision ID: 004_add_missing_rbac_tables
Revises: 20250117_unique_assets
Create Date: 2025-07-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_missing_rbac_tables'
down_revision = '20250117_unique_assets'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_roles table
    op.create_table('user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_type', sa.String(length=50), nullable=False),
        sa.Column('role_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('scope_type', sa.String(length=20), nullable=True),
        sa.Column('scope_client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scope_engagement_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('assigned_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['scope_client_id'], ['client_accounts.id'], ),
        sa.ForeignKeyConstraint(['scope_engagement_id'], ['engagements.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_account_associations table
    op.create_table('user_account_associations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'client_account_id', name='_user_client_account_uc')
    )
    
    # Create indexes for user_roles
    op.create_index(op.f('ix_user_roles_id'), 'user_roles', ['id'], unique=False)
    op.create_index(op.f('ix_user_roles_user_id'), 'user_roles', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_roles_is_active'), 'user_roles', ['is_active'], unique=False)
    
    # Create indexes for user_account_associations
    op.create_index(op.f('ix_user_account_associations_user_id'), 'user_account_associations', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_account_associations_client_account_id'), 'user_account_associations', ['client_account_id'], unique=False)


def downgrade():
    # Drop indexes for user_account_associations
    op.drop_index(op.f('ix_user_account_associations_client_account_id'), table_name='user_account_associations')
    op.drop_index(op.f('ix_user_account_associations_user_id'), table_name='user_account_associations')
    
    # Drop indexes for user_roles
    op.drop_index(op.f('ix_user_roles_is_active'), table_name='user_roles')
    op.drop_index(op.f('ix_user_roles_user_id'), table_name='user_roles')
    op.drop_index(op.f('ix_user_roles_id'), table_name='user_roles')
    
    # Drop tables
    op.drop_table('user_account_associations')
    op.drop_table('user_roles')