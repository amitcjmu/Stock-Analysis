"""Add flow management columns to workflow_states

Revision ID: add_flow_management_columns
Revises: 305c091bd5bf
Create Date: 2025-01-27 21:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_flow_management_columns'
down_revision = '9d6b856ba8a7'
branch_labels = None
depends_on = None


def upgrade():
    """Add flow management columns to workflow_states table."""
    
    # Add new columns for flow management
    op.add_column('workflow_states', 
        sa.Column('expiration_date', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('workflow_states', 
        sa.Column('auto_cleanup_eligible', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('workflow_states', 
        sa.Column('deletion_scheduled_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('workflow_states', 
        sa.Column('last_user_activity', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')))
    op.add_column('workflow_states', 
        sa.Column('flow_resumption_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'))
    op.add_column('workflow_states', 
        sa.Column('agent_memory_refs', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'))
    op.add_column('workflow_states', 
        sa.Column('knowledge_base_refs', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'))

    # Create indexes for flow management queries
    op.create_index(
        'idx_workflow_states_expiration', 
        'workflow_states', 
        ['expiration_date'], 
        postgresql_where=sa.text("status IN ('running', 'paused')")
    )
    
    op.create_index(
        'idx_workflow_states_cleanup', 
        'workflow_states', 
        ['auto_cleanup_eligible', 'expiration_date']
    )
    
    op.create_index(
        'idx_workflow_states_activity', 
        'workflow_states', 
        ['last_user_activity', 'client_account_id', 'engagement_id']
    )
    
    # Add index for incomplete flow detection (primary query)
    op.create_index(
        'idx_workflow_states_incomplete', 
        'workflow_states', 
        ['client_account_id', 'engagement_id', 'status'], 
        postgresql_where=sa.text("status IN ('running', 'paused', 'failed')")
    )


def downgrade():
    """Remove flow management columns from workflow_states table."""
    
    # Drop indexes
    op.drop_index('idx_workflow_states_incomplete', table_name='workflow_states')
    op.drop_index('idx_workflow_states_activity', table_name='workflow_states')
    op.drop_index('idx_workflow_states_cleanup', table_name='workflow_states')
    op.drop_index('idx_workflow_states_expiration', table_name='workflow_states')
    
    # Drop columns
    op.drop_column('workflow_states', 'knowledge_base_refs')
    op.drop_column('workflow_states', 'agent_memory_refs')
    op.drop_column('workflow_states', 'flow_resumption_data')
    op.drop_column('workflow_states', 'last_user_activity')
    op.drop_column('workflow_states', 'deletion_scheduled_at')
    op.drop_column('workflow_states', 'auto_cleanup_eligible')
    op.drop_column('workflow_states', 'expiration_date') 