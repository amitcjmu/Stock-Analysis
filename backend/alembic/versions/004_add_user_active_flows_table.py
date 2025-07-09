"""Add user_active_flows table for user flow tracking

Revision ID: 004_add_user_active_flows
Revises: 13b95eacf168
Create Date: 2025-07-09 14:30:00.000000

This migration creates the user_active_flows table to track which flows
are currently active for each user. This is part of the session-to-flow
refactor plan to enable proper user flow context management.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text
import uuid

# revision identifiers, used by Alembic.
revision = '004_add_user_active_flows'
down_revision = '13b95eacf168'
branch_labels = None
depends_on = None


def upgrade():
    """Create user_active_flows table for user flow tracking"""
    
    # Create the user_active_flows table
    op.create_table('user_active_flows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('activated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_current', sa.Boolean, default=False, nullable=False),
        
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create indexes for performance
    op.create_index('idx_user_active_flows_user_id', 'user_active_flows', ['user_id'])
    op.create_index('idx_user_active_flows_flow_id', 'user_active_flows', ['flow_id'])
    op.create_index('idx_user_active_flows_engagement_id', 'user_active_flows', ['engagement_id'])
    op.create_index('idx_user_active_flows_is_current', 'user_active_flows', ['is_current'])
    op.create_index('idx_user_active_flows_user_engagement', 'user_active_flows', ['user_id', 'engagement_id'])
    op.create_index('idx_user_active_flows_activated_at', 'user_active_flows', [sa.text('activated_at DESC')])
    
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
    
    # Create unique constraint to prevent duplicate user-flow combinations
    op.create_unique_constraint('uq_user_active_flows_user_flow',
                               'user_active_flows',
                               ['user_id', 'flow_id'])
    
    # Note: CHECK constraint with subquery is not supported in PostgreSQL
    # The constraint to ensure only one current flow per user per engagement
    # will be enforced at the application level in the UserActiveFlow model
    
    # Migrate existing user flow data from defaults
    migrate_existing_user_flows()


def migrate_existing_user_flows():
    """Migrate existing user flow data from user defaults and active flows"""
    connection = op.get_bind()
    
    # Get all users with default engagement and active flows
    result = connection.execute(text("""
        SELECT u.id as user_id, u.default_engagement_id, u.created_at
        FROM users u
        WHERE u.default_engagement_id IS NOT NULL
        AND u.is_active = true
    """))
    
    for row in result:
        user_id = row.user_id
        engagement_id = row.default_engagement_id
        created_at = row.created_at
        
        # Find active flows for this user's engagement
        flows_result = connection.execute(text("""
            SELECT DISTINCT cfs.flow_id, cfs.flow_type, cfs.created_at, cfs.flow_status
            FROM crewai_flow_state_extensions cfs
            WHERE cfs.engagement_id = :engagement_id
            AND cfs.flow_status IN ('active', 'processing', 'paused')
            ORDER BY cfs.created_at DESC
            LIMIT 3
        """), {'engagement_id': str(engagement_id)})
        
        flows = list(flows_result)
        
        # Insert user active flows
        for idx, flow in enumerate(flows):
            # First flow is current, others are just active
            is_current = (idx == 0)
            
            connection.execute(text("""
                INSERT INTO user_active_flows (
                    id, user_id, flow_id, engagement_id, 
                    activated_at, is_current, created_at, updated_at
                ) VALUES (
                    :id, :user_id, :flow_id, :engagement_id,
                    :activated_at, :is_current, :created_at, :updated_at
                )
            """), {
                'id': str(uuid.uuid4()),
                'user_id': str(user_id),
                'flow_id': str(flow.flow_id),
                'engagement_id': str(engagement_id),
                'activated_at': flow.created_at,
                'is_current': is_current,
                'created_at': flow.created_at,
                'updated_at': flow.created_at
            })
    
    print(f"✅ Migrated active flows for users")


def downgrade():
    """Remove user_active_flows table"""
    
    # Note: CHECK constraint was not created due to PostgreSQL limitations
    
    # Drop unique constraint
    op.drop_constraint('uq_user_active_flows_user_flow', 'user_active_flows')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_user_active_flows_engagement', 'user_active_flows')
    op.drop_constraint('fk_user_active_flows_user', 'user_active_flows')
    
    # Drop indexes
    op.drop_index('idx_user_active_flows_activated_at', 'user_active_flows')
    op.drop_index('idx_user_active_flows_user_engagement', 'user_active_flows')
    op.drop_index('idx_user_active_flows_is_current', 'user_active_flows')
    op.drop_index('idx_user_active_flows_engagement_id', 'user_active_flows')
    op.drop_index('idx_user_active_flows_flow_id', 'user_active_flows')
    op.drop_index('idx_user_active_flows_user_id', 'user_active_flows')
    
    # Drop table
    op.drop_table('user_active_flows')
    
    print("⚠️ Removed user_active_flows table")