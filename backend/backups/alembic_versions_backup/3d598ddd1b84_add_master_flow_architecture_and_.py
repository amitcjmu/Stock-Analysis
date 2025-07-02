"""add_master_flow_architecture_and_discovery_flows

Revision ID: 3d598ddd1b84
Revises: 02a9d3783de8
Create Date: 2025-01-02 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3d598ddd1b84'
down_revision = '02a9d3783de8'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add master flow architecture and discovery flows
    This builds on the core tables to add flow coordination
    """
    
    # =============================================================================
    # MASTER FLOW ARCHITECTURE: CrewAI Flow State Extensions
    # =============================================================================
    
    # Create crewai_flow_state_extensions table as master flow coordinator
    op.create_table('crewai_flow_state_extensions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Master Flow Coordination Fields
        sa.Column('current_phase', sa.String(100), nullable=True),
        sa.Column('phase_flow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('phase_progression', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('cross_phase_context', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        
        # Phase-specific flow IDs
        sa.Column('discovery_flow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assessment_flow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('planning_flow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('execution_flow_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # CrewAI Flow persistence data
        sa.Column('flow_persistence_data', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('agent_collaboration_log', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('memory_usage_metrics', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('knowledge_base_analytics', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        
        # Flow performance metrics
        sa.Column('phase_execution_times', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('agent_performance_metrics', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('crew_coordination_analytics', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        
        # Flow metadata
        sa.Column('flow_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        
        # Learning and adaptation data
        sa.Column('learning_patterns', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('user_feedback_history', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=True),
        sa.Column('adaptation_metrics', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('flow_id', name='uq_crewai_extensions_flow_id')
    )
    
    # Create indexes for crewai_flow_state_extensions
    op.create_index('idx_crewai_extensions_master_flow_id', 'crewai_flow_state_extensions', ['flow_id'])
    op.create_index('idx_crewai_extensions_current_phase', 'crewai_flow_state_extensions', ['current_phase'])
    op.create_index('idx_crewai_extensions_phase_flow_id', 'crewai_flow_state_extensions', ['phase_flow_id'])

    # =============================================================================
    # DISCOVERY FLOWS (Multi-Phase Architecture)
    # =============================================================================
    
    # Create discovery_flows table
    op.create_table('discovery_flows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_id', sa.String(length=255), nullable=False),
        sa.Column('master_flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_phase', sa.String(length=100), nullable=False),
        sa.Column('progress_percentage', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('crewai_flow_state', sa.JSON(), nullable=True),
        sa.Column('crewai_persistence_id', sa.String(length=255), nullable=True),
        sa.Column('import_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('field_mappings', sa.JSON(), nullable=True),
        sa.Column('cleaned_data', sa.JSON(), nullable=True),
        sa.Column('asset_inventory', sa.JSON(), nullable=True),
        sa.Column('dependencies', sa.JSON(), nullable=True),
        sa.Column('tech_debt', sa.JSON(), nullable=True),
        sa.Column('data_import_completed', sa.Boolean(), nullable=False),
        sa.Column('attribute_mapping_completed', sa.Boolean(), nullable=False),
        sa.Column('data_cleansing_completed', sa.Boolean(), nullable=False),
        sa.Column('inventory_completed', sa.Boolean(), nullable=False),
        sa.Column('dependencies_completed', sa.Boolean(), nullable=False),
        sa.Column('tech_debt_completed', sa.Boolean(), nullable=False),
        sa.Column('crew_status', sa.JSON(), nullable=True),
        sa.Column('agent_insights', sa.JSON(), nullable=True),
        sa.Column('crew_performance_metrics', sa.JSON(), nullable=True),
        sa.Column('learning_scope', sa.String(length=50), nullable=False),
        sa.Column('memory_isolation_level', sa.String(length=20), nullable=False),
        sa.Column('shared_memory_refs', sa.JSON(), nullable=True),
        sa.Column('knowledge_base_refs', sa.JSON(), nullable=True),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('warnings', sa.JSON(), nullable=True),
        sa.Column('workflow_log', sa.JSON(), nullable=True),
        sa.Column('assessment_ready', sa.Boolean(), nullable=False),
        sa.Column('assessment_package', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['master_flow_id'], ['crewai_flow_state_extensions.flow_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discovery_flows_client_account_id'), 'discovery_flows', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_discovery_flows_crewai_persistence_id'), 'discovery_flows', ['crewai_persistence_id'], unique=False)
    op.create_index(op.f('ix_discovery_flows_engagement_id'), 'discovery_flows', ['engagement_id'], unique=False)
    op.create_index(op.f('ix_discovery_flows_flow_id'), 'discovery_flows', ['flow_id'], unique=True)
    op.create_index(op.f('ix_discovery_flows_import_session_id'), 'discovery_flows', ['import_session_id'], unique=False)
    op.create_index(op.f('ix_discovery_flows_user_id'), 'discovery_flows', ['user_id'], unique=False)
    op.create_index('idx_discovery_flows_master_flow_id', 'discovery_flows', ['master_flow_id'])

    # =============================================================================
    # ENHANCE ASSETS TABLE WITH MASTER FLOW SUPPORT
    # =============================================================================
    
    # Add master flow columns to existing assets table
    op.add_column('assets', sa.Column('master_flow_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('assets', sa.Column('discovery_flow_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('assets', sa.Column('assessment_flow_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('assets', sa.Column('planning_flow_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('assets', sa.Column('execution_flow_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('assets', sa.Column('source_phase', sa.String(50), nullable=True))
    op.add_column('assets', sa.Column('current_phase', sa.String(50), nullable=True))
    op.add_column('assets', sa.Column('phase_progression', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True))
    
    # Add foreign key constraints for master flow references
    op.create_foreign_key('fk_assets_master_flow_id', 'assets', 'crewai_flow_state_extensions', ['master_flow_id'], ['flow_id'])
    op.create_foreign_key('fk_assets_discovery_flow_id', 'assets', 'discovery_flows', ['discovery_flow_id'], ['id'])
    
    # Create indexes for master flow references
    op.create_index('idx_assets_master_flow_id', 'assets', ['master_flow_id'])
    op.create_index('idx_assets_source_phase', 'assets', ['source_phase'])
    op.create_index('idx_assets_current_phase', 'assets', ['current_phase'])
    op.create_index('idx_assets_discovery_flow_id', 'assets', ['discovery_flow_id'])

    # =============================================================================
    # DATA INTEGRATION TABLES
    # =============================================================================
    
    # Create data_imports table
    op.create_table('data_imports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('master_flow_id', postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(['master_flow_id'], ['crewai_flow_state_extensions.flow_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_imports_client_account_id'), 'data_imports', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_data_imports_engagement_id'), 'data_imports', ['engagement_id'], unique=False)
    op.create_index(op.f('ix_data_imports_filename'), 'data_imports', ['filename'], unique=False)
    op.create_index(op.f('ix_data_imports_id'), 'data_imports', ['id'], unique=False)
    op.create_index(op.f('ix_data_imports_status'), 'data_imports', ['status'], unique=False)
    op.create_index(op.f('ix_data_imports_user_id'), 'data_imports', ['user_id'], unique=False)
    op.create_index('idx_data_imports_master_flow_id', 'data_imports', ['master_flow_id'])

    # Create supporting data integration tables
    op.create_table('import_field_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('master_flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_field', sa.String(), nullable=False),
        sa.Column('target_field', sa.String(), nullable=False),
        sa.Column('mapping_confidence', sa.Float(), nullable=True),
        sa.Column('validation_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['master_flow_id'], ['crewai_flow_state_extensions.flow_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_import_field_mappings_master_flow_id', 'import_field_mappings', ['master_flow_id'])

    op.create_table('raw_import_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('master_flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('row_index', sa.Integer(), nullable=False),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('validation_status', sa.String(), nullable=False),
        sa.Column('validation_errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processed_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['master_flow_id'], ['crewai_flow_state_extensions.flow_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_raw_import_records_master_flow_id', 'raw_import_records', ['master_flow_id'])

    op.create_table('workflow_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('master_flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phase', sa.String(), nullable=False),
        sa.Column('step', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        sa.Column('step_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['master_flow_id'], ['crewai_flow_state_extensions.flow_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_workflow_progress_master_flow_id', 'workflow_progress', ['master_flow_id'])

    print("✅ Master Flow Architecture migration completed successfully!")
    print("✅ CrewAI Flow State Extensions established as master coordinator")
    print("✅ Discovery flows with master flow coordination created")
    print("✅ Assets table enhanced with multi-phase support")
    print("✅ Data integration tables added with master flow references")
    print("✅ Ready for audit tables migration")


def downgrade():
    """Rollback master flow architecture"""
    op.drop_table('workflow_progress')
    op.drop_table('raw_import_records')
    op.drop_table('import_field_mappings')
    op.drop_table('data_imports')
    
    # Remove master flow columns from assets
    op.drop_constraint('fk_assets_discovery_flow_id', 'assets', type_='foreignkey')
    op.drop_constraint('fk_assets_master_flow_id', 'assets', type_='foreignkey')
    op.drop_column('assets', 'phase_progression')
    op.drop_column('assets', 'current_phase')
    op.drop_column('assets', 'source_phase')
    op.drop_column('assets', 'execution_flow_id')
    op.drop_column('assets', 'planning_flow_id')
    op.drop_column('assets', 'assessment_flow_id')
    op.drop_column('assets', 'discovery_flow_id')
    op.drop_column('assets', 'master_flow_id')
    
    op.drop_table('discovery_flows')
    op.drop_table('crewai_flow_state_extensions') 