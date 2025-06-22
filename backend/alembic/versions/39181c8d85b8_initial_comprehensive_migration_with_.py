"""Initial comprehensive migration with all current models

Revision ID: 39181c8d85b8
Revises: 
Create Date: 2025-01-27 11:59:30.123456

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '39181c8d85b8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    sa.Enum('running', 'completed', 'failed', 'paused', 'archived', name='workflowstatus').create(op.get_bind())
    sa.Enum('field_mapping', 'data_cleansing', 'asset_inventory', 'dependency_analysis', 'tech_debt', name='workflowphase').create(op.get_bind())
    
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

    # Create workflow_states table with Phase 4 enhancements
    op.create_table('workflow_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('running', 'completed', 'failed', 'paused', 'archived', name='workflowstatus'), nullable=False),
        sa.Column('current_phase', sa.Enum('field_mapping', 'data_cleansing', 'asset_inventory', 'dependency_analysis', 'tech_debt', name='workflowphase'), nullable=False),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        sa.Column('phase_completion', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('crew_status', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('field_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('cleaned_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('asset_inventory', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('dependencies', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('technical_debt', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('agent_insights', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('success_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('warnings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('workflow_log', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('database_assets_created', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('database_integration_status', sa.String(), nullable=True),
        sa.Column('shared_memory_id', sa.String(), nullable=True),
        sa.Column('state_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        
        # Phase 4: Flow expiration and auto-cleanup columns
        sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auto_cleanup_eligible', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('deletion_scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_user_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('flow_resumption_data', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('agent_memory_refs', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('knowledge_base_refs', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for workflow_states
    op.create_index(op.f('ix_workflow_states_client_account_id'), 'workflow_states', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_workflow_states_current_phase'), 'workflow_states', ['current_phase'], unique=False)
    op.create_index(op.f('ix_workflow_states_engagement_id'), 'workflow_states', ['engagement_id'], unique=False)
    op.create_index(op.f('ix_workflow_states_flow_id'), 'workflow_states', ['flow_id'], unique=False)
    op.create_index(op.f('ix_workflow_states_id'), 'workflow_states', ['id'], unique=False)
    op.create_index(op.f('ix_workflow_states_session_id'), 'workflow_states', ['session_id'], unique=True)
    op.create_index(op.f('ix_workflow_states_status'), 'workflow_states', ['status'], unique=False)
    op.create_index(op.f('ix_workflow_states_user_id'), 'workflow_states', ['user_id'], unique=False)
    
    # Phase 4: Performance optimization indexes
    op.create_index('idx_workflow_states_incomplete_flows', 'workflow_states', 
                   ['client_account_id', 'engagement_id', 'status'], 
                   postgresql_where=sa.text("status IN ('running', 'paused', 'failed')"))
    
    op.create_index('idx_workflow_states_expiration', 'workflow_states', 
                   ['expiration_date'], 
                   postgresql_where=sa.text("status IN ('running', 'paused')"))
    
    op.create_index('idx_workflow_states_cleanup', 'workflow_states', 
                   ['auto_cleanup_eligible', 'expiration_date'])
    
    op.create_index('idx_workflow_states_activity', 'workflow_states', 
                   ['last_user_activity', 'client_account_id', 'engagement_id'])

    # Create flow_deletion_audit table (Phase 4)
    op.create_table('flow_deletion_audit',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('deletion_type', sa.String(), nullable=False),
        sa.Column('deletion_reason', sa.Text(), nullable=True),
        sa.Column('deletion_method', sa.String(), nullable=False),
        
        # Comprehensive data deletion summary
        sa.Column('data_deleted', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('deletion_impact', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('cleanup_summary', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        
        # CrewAI specific cleanup
        sa.Column('shared_memory_cleaned', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('knowledge_base_refs_cleaned', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('agent_memory_cleaned', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        
        # Audit trail
        sa.Column('deleted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('deleted_by', sa.String(), nullable=False),
        sa.Column('deletion_duration_ms', sa.Integer(), nullable=True),
        
        # Recovery information (if applicable)
        sa.Column('recovery_possible', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('recovery_data', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for flow_deletion_audit
    op.create_index('idx_flow_deletion_audit_client', 'flow_deletion_audit', 
                   ['client_account_id', 'engagement_id'])
    op.create_index('idx_flow_deletion_audit_date', 'flow_deletion_audit', ['deleted_at'])
    op.create_index('idx_flow_deletion_audit_type', 'flow_deletion_audit', 
                   ['deletion_type', 'deleted_at'])
    op.create_index('idx_flow_deletion_audit_session', 'flow_deletion_audit', ['session_id'])

    # Create crewai_flow_state_extensions table (Phase 4)
    op.create_table('crewai_flow_state_extensions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # CrewAI Flow persistence data
        sa.Column('flow_persistence_data', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('agent_collaboration_log', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('memory_usage_metrics', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('knowledge_base_analytics', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        
        # Flow performance metrics
        sa.Column('phase_execution_times', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('agent_performance_metrics', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('crew_coordination_analytics', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        
        # Learning and adaptation data
        sa.Column('learning_patterns', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('user_feedback_history', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('adaptation_metrics', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        
        sa.ForeignKeyConstraint(['session_id'], ['workflow_states.session_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for crewai_flow_state_extensions
    op.create_index('idx_crewai_flow_extensions_session', 'crewai_flow_state_extensions', ['session_id'])
    op.create_index('idx_crewai_flow_extensions_flow', 'crewai_flow_state_extensions', ['flow_id'])
    op.create_index('idx_crewai_flow_extensions_updated', 'crewai_flow_state_extensions', ['updated_at'])

    # Create other existing tables (assets, data_import_sessions, etc.)
    op.create_table('assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('asset_type', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
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
    op.create_index(op.f('ix_assets_session_id'), 'assets', ['session_id'], unique=False)

    # Create data_import_sessions table
    op.create_table('data_import_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('total_rows', sa.Integer(), nullable=True),
        sa.Column('processed_rows', sa.Integer(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=True),
        sa.Column('validation_results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('field_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processing_log', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('agent_insights', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_import_sessions_client_account_id'), 'data_import_sessions', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_data_import_sessions_engagement_id'), 'data_import_sessions', ['engagement_id'], unique=False)
    op.create_index(op.f('ix_data_import_sessions_filename'), 'data_import_sessions', ['filename'], unique=False)
    op.create_index(op.f('ix_data_import_sessions_id'), 'data_import_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_data_import_sessions_status'), 'data_import_sessions', ['status'], unique=False)
    op.create_index(op.f('ix_data_import_sessions_user_id'), 'data_import_sessions', ['user_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('data_import_sessions')
    op.drop_table('assets')
    op.drop_table('crewai_flow_state_extensions')
    op.drop_table('flow_deletion_audit')
    op.drop_table('workflow_states')
    op.drop_table('engagements')
    op.drop_table('client_accounts')
    
    # Drop enum types
    sa.Enum('running', 'completed', 'failed', 'paused', 'archived', name='workflowstatus').drop(op.get_bind())
    sa.Enum('field_mapping', 'data_cleansing', 'asset_inventory', 'dependency_analysis', 'tech_debt', name='workflowphase').drop(op.get_bind())