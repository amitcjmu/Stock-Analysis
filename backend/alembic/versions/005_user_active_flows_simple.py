"""Add user_active_flows table - simplified version

Revision ID: 005_user_active_flows_simple
Revises: 13b95eacf168
Create Date: 2025-07-09 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '005_user_active_flows_simple'
down_revision = '13b95eacf168'
branch_labels = None
depends_on = None


def upgrade():
    """Create user_active_flows table"""
    
    # Create the user_active_flows table
    op.create_table('user_active_flows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('activated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_current', sa.Boolean, default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create indexes
    op.create_index('idx_user_active_flows_user_id', 'user_active_flows', ['user_id'])
    op.create_index('idx_user_active_flows_flow_id', 'user_active_flows', ['flow_id'])
    op.create_index('idx_user_active_flows_engagement_id', 'user_active_flows', ['engagement_id'])
    op.create_index('idx_user_active_flows_is_current', 'user_active_flows', ['is_current'])
    op.create_index('idx_user_active_flows_user_engagement', 'user_active_flows', ['user_id', 'engagement_id'])
    
    # Create foreign key constraints
    op.create_foreign_key('fk_user_active_flows_user',
                          'user_active_flows',
                          'users',
                          ['user_id'], ['id'],
                          ondelete='CASCADE')
    
    op.create_foreign_key('fk_user_active_flows_engagement',
                          'user_active_flows',
                          'engagements',
                          ['engagement_id'], ['id'],
                          ondelete='CASCADE')
    
    # Create unique constraint
    op.create_unique_constraint('uq_user_active_flows_user_flow',
                               'user_active_flows',
                               ['user_id', 'flow_id'])
    
    print("✅ user_active_flows table created successfully")


def downgrade():
    """Remove user_active_flows table"""
    
    # Drop foreign key constraints
    op.drop_constraint('fk_user_active_flows_engagement', 'user_active_flows', type_='foreignkey')
    op.drop_constraint('fk_user_active_flows_user', 'user_active_flows', type_='foreignkey')
    
    # Drop unique constraint
    op.drop_constraint('uq_user_active_flows_user_flow', 'user_active_flows', type_='unique')
    
    # Drop indexes
    op.drop_index('idx_user_active_flows_user_engagement', 'user_active_flows')
    op.drop_index('idx_user_active_flows_is_current', 'user_active_flows')
    op.drop_index('idx_user_active_flows_engagement_id', 'user_active_flows')
    op.drop_index('idx_user_active_flows_flow_id', 'user_active_flows')
    op.drop_index('idx_user_active_flows_user_id', 'user_active_flows')
    
    # Drop table
    op.drop_table('user_active_flows')
    
    print("⚠️ user_active_flows table removed")