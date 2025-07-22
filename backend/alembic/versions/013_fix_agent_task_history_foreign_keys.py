"""Fix agent task history foreign keys

Revision ID: 013_fix_agent_task_history_foreign_keys
Revises: 012_agent_observability_enhancement
Create Date: 2025-01-21 04:20:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '013_fix_agent_task_history_foreign_keys'
down_revision = '012_agent_observability_enhancement'
branch_labels = None
depends_on = None


def upgrade():
    """Add foreign key constraints to agent_task_history table"""
    # Add foreign key constraints
    op.create_foreign_key(
        'fk_agent_task_history_client_account_id',
        'agent_task_history', 
        'client_accounts',
        ['client_account_id'], 
        ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_agent_task_history_engagement_id',
        'agent_task_history', 
        'engagements',
        ['engagement_id'], 
        ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_agent_task_history_flow_id',
        'agent_task_history', 
        'crewai_flow_state_extensions',
        ['flow_id'], 
        ['flow_id'],
        ondelete='CASCADE'
    )


def downgrade():
    """Remove foreign key constraints from agent_task_history table"""
    op.drop_constraint('fk_agent_task_history_flow_id', 'agent_task_history', type_='foreignkey')
    op.drop_constraint('fk_agent_task_history_engagement_id', 'agent_task_history', type_='foreignkey')
    op.drop_constraint('fk_agent_task_history_client_account_id', 'agent_task_history', type_='foreignkey')