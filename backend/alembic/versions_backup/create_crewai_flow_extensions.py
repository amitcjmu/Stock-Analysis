"""Create CrewAI flow state extensions table

Revision ID: create_crewai_flow_extensions
Revises: create_flow_deletion_audit
Create Date: 2025-01-27 21:47:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = 'create_crewai_flow_extensions'
down_revision = 'create_flow_deletion_audit'
branch_labels = None
depends_on = None


def upgrade():
    """Create extended table for CrewAI-specific flow state data."""
    
    op.create_table(
        'crewai_flow_state_extensions',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('flow_id', sa.UUID(), nullable=False),
        
        # CrewAI Flow persistence data
        sa.Column('flow_persistence_data', postgresql.JSONB(astext_type=sa.Text()), 
                 nullable=False, server_default='{}',
                 comment='CrewAI Flow @persist() decorator data'),
        sa.Column('agent_collaboration_log', postgresql.JSONB(astext_type=sa.Text()), 
                 nullable=False, server_default='[]',
                 comment='Log of agent interactions and collaborations'),
        sa.Column('memory_usage_metrics', postgresql.JSONB(astext_type=sa.Text()), 
                 nullable=False, server_default='{}',
                 comment='Memory usage tracking for agents'),
        sa.Column('knowledge_base_analytics', postgresql.JSONB(astext_type=sa.Text()), 
                 nullable=False, server_default='{}',
                 comment='Knowledge base usage and effectiveness metrics'),
        
        # Flow performance metrics
        sa.Column('phase_execution_times', postgresql.JSONB(astext_type=sa.Text()), 
                 nullable=False, server_default='{}',
                 comment='Execution time for each flow phase'),
        sa.Column('agent_performance_metrics', postgresql.JSONB(astext_type=sa.Text()), 
                 nullable=False, server_default='{}',
                 comment='Individual agent performance data'),
        sa.Column('crew_coordination_analytics', postgresql.JSONB(astext_type=sa.Text()), 
                 nullable=False, server_default='{}',
                 comment='Crew coordination and efficiency metrics'),
        
        # Learning and adaptation data
        sa.Column('learning_patterns', postgresql.JSONB(astext_type=sa.Text()), 
                 nullable=False, server_default='[]',
                 comment='Patterns learned during flow execution'),
        sa.Column('user_feedback_history', postgresql.JSONB(astext_type=sa.Text()), 
                 nullable=False, server_default='[]',
                 comment='User feedback and corrections'),
        sa.Column('adaptation_metrics', postgresql.JSONB(astext_type=sa.Text()), 
                 nullable=False, server_default='{}',
                 comment='How the flow adapted based on feedback'),
        
        # Flow resumption support
        sa.Column('resumption_checkpoints', postgresql.JSONB(astext_type=sa.Text()), 
                 nullable=False, server_default='[]',
                 comment='Checkpoints for flow resumption'),
        sa.Column('state_snapshots', postgresql.JSONB(astext_type=sa.Text()), 
                 nullable=False, server_default='[]',
                 comment='Periodic state snapshots for recovery'),
        
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add foreign key constraint to workflow_states
    op.create_foreign_key(
        'fk_crewai_flow_extensions_session_id',
        'crewai_flow_state_extensions', 
        'workflow_states',
        ['session_id'], 
        ['session_id'],
        ondelete='CASCADE'
    )
    
    # Create indexes for CrewAI flow queries
    op.create_index(
        'idx_crewai_flow_extensions_session', 
        'crewai_flow_state_extensions', 
        ['session_id']
    )
    
    op.create_index(
        'idx_crewai_flow_extensions_flow', 
        'crewai_flow_state_extensions', 
        ['flow_id']
    )
    
    op.create_index(
        'idx_crewai_flow_extensions_updated', 
        'crewai_flow_state_extensions', 
        ['updated_at']
    )


def downgrade():
    """Drop CrewAI flow state extensions table."""
    
    # Drop indexes
    op.drop_index('idx_crewai_flow_extensions_updated', table_name='crewai_flow_state_extensions')
    op.drop_index('idx_crewai_flow_extensions_flow', table_name='crewai_flow_state_extensions')
    op.drop_index('idx_crewai_flow_extensions_session', table_name='crewai_flow_state_extensions')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_crewai_flow_extensions_session_id', 'crewai_flow_state_extensions', type_='foreignkey')
    
    # Drop table
    op.drop_table('crewai_flow_state_extensions') 