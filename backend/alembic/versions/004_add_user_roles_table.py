"""Add user_roles table

Revision ID: 004_add_user_roles_table
Revises: 20250117_unique_assets
Create Date: 2025-07-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_user_roles_table'
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
    
    # Create indexes
    op.create_index(op.f('ix_user_roles_id'), 'user_roles', ['id'], unique=False)
    op.create_index(op.f('ix_user_roles_user_id'), 'user_roles', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_roles_is_active'), 'user_roles', ['is_active'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_user_roles_is_active'), table_name='user_roles')
    op.drop_index(op.f('ix_user_roles_user_id'), table_name='user_roles')
    op.drop_index(op.f('ix_user_roles_id'), table_name='user_roles')
    
    # Drop table
    op.drop_table('user_roles')