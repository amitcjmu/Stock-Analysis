"""Add unified discovery flow columns to workflow_states

Revision ID: 9d6b856ba8a7
Revises: 118ea9101cec
Create Date: 2025-06-22 13:53:21.175005

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9d6b856ba8a7'
down_revision = '118ea9101cec'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns for unified discovery flow
    
    # Flow identification
    op.add_column('workflow_states', sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('workflow_states', sa.Column('user_id', sa.String(), nullable=True))
    
    # Progress tracking
    op.add_column('workflow_states', sa.Column('progress_percentage', sa.Float(), nullable=False, server_default='0.0'))
    
    # Phase and crew tracking
    op.add_column('workflow_states', sa.Column('phase_completion', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('workflow_states', sa.Column('crew_status', sa.JSON(), nullable=False, server_default='{}'))
    
    # Results storage
    op.add_column('workflow_states', sa.Column('field_mappings', sa.JSON(), nullable=True))
    op.add_column('workflow_states', sa.Column('cleaned_data', sa.JSON(), nullable=True))
    op.add_column('workflow_states', sa.Column('asset_inventory', sa.JSON(), nullable=True))
    op.add_column('workflow_states', sa.Column('dependencies', sa.JSON(), nullable=True))
    op.add_column('workflow_states', sa.Column('technical_debt', sa.JSON(), nullable=True))
    
    # Quality and metrics
    op.add_column('workflow_states', sa.Column('data_quality_metrics', sa.JSON(), nullable=True))
    op.add_column('workflow_states', sa.Column('agent_insights', sa.JSON(), nullable=True))
    op.add_column('workflow_states', sa.Column('success_criteria', sa.JSON(), nullable=True))
    
    # Error tracking
    op.add_column('workflow_states', sa.Column('errors', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('workflow_states', sa.Column('warnings', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('workflow_states', sa.Column('workflow_log', sa.JSON(), nullable=False, server_default='[]'))
    
    # Final results
    op.add_column('workflow_states', sa.Column('discovery_summary', sa.JSON(), nullable=True))
    op.add_column('workflow_states', sa.Column('assessment_flow_package', sa.JSON(), nullable=True))
    
    # Database integration tracking
    op.add_column('workflow_states', sa.Column('database_assets_created', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('workflow_states', sa.Column('database_integration_status', sa.String(), nullable=False, server_default="'pending'"))
    
    # Enterprise features
    op.add_column('workflow_states', sa.Column('learning_scope', sa.String(), nullable=False, server_default="'engagement'"))
    op.add_column('workflow_states', sa.Column('memory_isolation_level', sa.String(), nullable=False, server_default="'strict'"))
    op.add_column('workflow_states', sa.Column('shared_memory_id', sa.String(), nullable=True))
    
    # Additional timestamps
    op.add_column('workflow_states', sa.Column('started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('workflow_states', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create indexes for new columns
    op.create_index('ix_workflow_states_flow_id', 'workflow_states', ['flow_id'])
    op.create_index('ix_workflow_states_user_id', 'workflow_states', ['user_id'])
    op.create_index('ix_workflow_states_current_phase', 'workflow_states', ['current_phase'])
    op.create_index('ix_workflow_states_progress_percentage', 'workflow_states', ['progress_percentage'])
    op.create_index('ix_workflow_states_database_integration_status', 'workflow_states', ['database_integration_status'])
    
    # Update existing records to have flow_id = session_id where flow_id is null
    op.execute("UPDATE migration.workflow_states SET flow_id = session_id WHERE flow_id IS NULL")
    
    # Update existing records to have user_id = 'system' where user_id is null
    op.execute("UPDATE migration.workflow_states SET user_id = 'system' WHERE user_id IS NULL")
    
    # Make flow_id and user_id non-nullable after setting default values
    op.alter_column('workflow_states', 'flow_id', nullable=False)
    op.alter_column('workflow_states', 'user_id', nullable=False)


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_workflow_states_database_integration_status', 'workflow_states')
    op.drop_index('ix_workflow_states_progress_percentage', 'workflow_states')
    op.drop_index('ix_workflow_states_current_phase', 'workflow_states')
    op.drop_index('ix_workflow_states_user_id', 'workflow_states')
    op.drop_index('ix_workflow_states_flow_id', 'workflow_states')
    
    # Remove columns in reverse order
    op.drop_column('workflow_states', 'completed_at')
    op.drop_column('workflow_states', 'started_at')
    op.drop_column('workflow_states', 'shared_memory_id')
    op.drop_column('workflow_states', 'memory_isolation_level')
    op.drop_column('workflow_states', 'learning_scope')
    op.drop_column('workflow_states', 'database_integration_status')
    op.drop_column('workflow_states', 'database_assets_created')
    op.drop_column('workflow_states', 'assessment_flow_package')
    op.drop_column('workflow_states', 'discovery_summary')
    op.drop_column('workflow_states', 'workflow_log')
    op.drop_column('workflow_states', 'warnings')
    op.drop_column('workflow_states', 'errors')
    op.drop_column('workflow_states', 'success_criteria')
    op.drop_column('workflow_states', 'agent_insights')
    op.drop_column('workflow_states', 'data_quality_metrics')
    op.drop_column('workflow_states', 'technical_debt')
    op.drop_column('workflow_states', 'dependencies')
    op.drop_column('workflow_states', 'asset_inventory')
    op.drop_column('workflow_states', 'cleaned_data')
    op.drop_column('workflow_states', 'field_mappings')
    op.drop_column('workflow_states', 'crew_status')
    op.drop_column('workflow_states', 'phase_completion')
    op.drop_column('workflow_states', 'progress_percentage')
    op.drop_column('workflow_states', 'user_id')
    op.drop_column('workflow_states', 'flow_id') 