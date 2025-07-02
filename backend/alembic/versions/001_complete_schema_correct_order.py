"""Complete database schema from all models - correct dependency order

Revision ID: 001_complete_schema
Revises: 
Create Date: 2025-07-01 19:30:00.000000

This migration creates ALL tables from all model files with:
- Complete field definitions matching SQLAlchemy models exactly
- All foreign key relationships
- All indexes and constraints
- All enum types
- Tables created in dependency order to avoid foreign key errors
- pgvector extension for vector embeddings
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001_complete_schema'
down_revision = '000_ensure_migration_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pgvector extension first
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Note: Using string types with check constraints for better migration compatibility
    # Enums can be added later via separate migrations if needed
    
    # === CORE FOUNDATION TABLES (No dependencies) ===
    
    # 1. Client Accounts table - COMPLETE (foundation table)
    op.create_table('client_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('industry', sa.String(100)),
        sa.Column('company_size', sa.String(50)),
        sa.Column('headquarters_location', sa.String(255)),
        sa.Column('primary_contact_name', sa.String(255)),
        sa.Column('primary_contact_email', sa.String(255)),
        sa.Column('primary_contact_phone', sa.String(50)),
        sa.Column('contact_email', sa.String(255)),
        sa.Column('contact_phone', sa.String(50)),
        sa.Column('address', sa.Text()),
        sa.Column('timezone', sa.String(50)),
        sa.Column('subscription_tier', sa.String(50), server_default='standard'),
        sa.Column('billing_contact_email', sa.String(255)),
        sa.Column('subscription_start_date', sa.DateTime(timezone=True)),
        sa.Column('subscription_end_date', sa.DateTime(timezone=True)),
        sa.Column('max_users', sa.Integer()),
        sa.Column('max_engagements', sa.Integer()),
        sa.Column('features_enabled', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('agent_configuration', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('storage_quota_gb', sa.Integer()),
        sa.Column('api_quota_monthly', sa.Integer()),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('branding', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('business_objectives', postgresql.JSON(astext_type=sa.Text()), 
                  server_default='{"primary_goals": [], "timeframe": "", "success_metrics": [], "constraints": []}'),
        sa.Column('agent_preferences', postgresql.JSON(astext_type=sa.Text()), 
                  server_default='{"discovery_depth": "comprehensive", "automation_level": "assisted", "risk_tolerance": "moderate", "preferred_clouds": [], "compliance_requirements": [], "custom_rules": []}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    )
    op.create_index('ix_client_accounts_id', 'client_accounts', ['id'])
    op.create_index('ix_client_accounts_slug', 'client_accounts', ['slug'])
    op.create_index('ix_client_accounts_is_active', 'client_accounts', ['is_active'])
    
    # 2. Users table - COMPLETE (foundation table)
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(100)),
        sa.Column('last_name', sa.String(100)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_verified', sa.Boolean(), server_default='false'),
        sa.Column('default_client_id', postgresql.UUID(as_uuid=True), nullable=True),  # FK added later
        sa.Column('default_engagement_id', postgresql.UUID(as_uuid=True), nullable=True),  # FK added later
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login', sa.DateTime(timezone=True))
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    
    # 3. LLM Model Pricing table - COMPLETE (no dependencies)
    op.create_table('llm_model_pricing',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('model_name', sa.String(255), nullable=False),
        sa.Column('model_version', sa.String(100)),
        sa.Column('input_cost_per_1k_tokens', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('output_cost_per_1k_tokens', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='USD'),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('source', sa.String(255)),
        sa.Column('notes', sa.Text()),
        sa.UniqueConstraint('provider', 'model_name', 'model_version', 'effective_from', name='uq_model_pricing_version_date')
    )
    op.create_index('idx_model_pricing_provider_model', 'llm_model_pricing', ['provider', 'model_name'])
    op.create_index('idx_model_pricing_active', 'llm_model_pricing', ['is_active', 'effective_from', 'effective_to'])
    
    # === SECOND LEVEL TABLES (Depend on client_accounts and/or users) ===
    
    # 4. Engagements table - COMPLETE
    op.create_table('engagements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('engagement_type', sa.String(50), server_default='migration'),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('priority', sa.String(20), server_default='medium'),
        sa.Column('start_date', sa.DateTime(timezone=True)),
        sa.Column('target_completion_date', sa.DateTime(timezone=True)),
        sa.Column('actual_completion_date', sa.DateTime(timezone=True)),
        sa.Column('engagement_lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('client_contact_name', sa.String(255)),
        sa.Column('client_contact_email', sa.String(255)),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('migration_scope', postgresql.JSON(astext_type=sa.Text()), 
                  server_default='{"target_clouds": [], "migration_strategies": [], "excluded_systems": [], "included_environments": [], "business_units": [], "geographic_scope": [], "timeline_constraints": {}}'),
        sa.Column('team_preferences', postgresql.JSON(astext_type=sa.Text()), 
                  server_default='{"stakeholders": [], "decision_makers": [], "technical_leads": [], "communication_style": "formal", "reporting_frequency": "weekly", "preferred_meeting_times": [], "escalation_contacts": [], "project_methodology": "agile"}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true')
    )
    op.create_index('ix_engagements_id', 'engagements', ['id'])
    op.create_index('ix_engagements_client_account_id', 'engagements', ['client_account_id'])
    op.create_index('ix_engagements_status', 'engagements', ['status'])
    op.create_index('ix_engagements_is_active', 'engagements', ['is_active'])
    
    # 5. User Account Associations table
    op.create_table('user_account_associations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.UniqueConstraint('user_id', 'client_account_id', name='_user_client_account_uc')
    )
    op.create_index('ix_user_account_associations_user_id', 'user_account_associations', ['user_id'])
    op.create_index('ix_user_account_associations_client_account_id', 'user_account_associations', ['client_account_id'])
    
    # 6. CrewAI Flow State Extensions table (master flow coordination table)
    op.create_table('crewai_flow_state_extensions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('flow_type', sa.String(50), nullable=False),
        sa.Column('flow_name', sa.String(255)),
        sa.Column('flow_status', sa.String(50), nullable=False, server_default='initialized'),
        sa.Column('flow_configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('flow_persistence_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('agent_collaboration_log', postgresql.JSONB(astext_type=sa.Text()), server_default='[]'),
        sa.Column('memory_usage_metrics', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('knowledge_base_analytics', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('phase_execution_times', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('agent_performance_metrics', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('crew_coordination_analytics', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('learning_patterns', postgresql.JSONB(astext_type=sa.Text()), server_default='[]'),
        sa.Column('user_feedback_history', postgresql.JSONB(astext_type=sa.Text()), server_default='[]'),
        sa.Column('adaptation_metrics', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('ix_crewai_flow_state_extensions_flow_id', 'crewai_flow_state_extensions', ['flow_id'])
    op.create_index('ix_crewai_flow_state_extensions_client_account_id', 'crewai_flow_state_extensions', ['client_account_id'])
    op.create_index('ix_crewai_flow_state_extensions_engagement_id', 'crewai_flow_state_extensions', ['engagement_id'])
    
    # 7. Data Import Sessions table
    op.create_table('data_import_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_name', sa.String(255), nullable=False),
        sa.Column('session_display_name', sa.String(255)),
        sa.Column('description', sa.Text()),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('parent_session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_import_sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('session_type', sa.String(50), nullable=False, server_default='DATA_IMPORT'),
        sa.Column('auto_created', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('source_filename', sa.String(255)),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('progress_percentage', sa.Integer(), server_default='0'),
        sa.Column('total_imports', sa.Integer(), server_default='0'),
        sa.Column('total_assets_processed', sa.Integer(), server_default='0'),
        sa.Column('total_records_imported', sa.Integer(), server_default='0'),
        sa.Column('data_quality_score', sa.Integer(), server_default='0'),
        sa.Column('session_config', postgresql.JSON(astext_type=sa.Text()), 
                  server_default='{"deduplication_strategy": "engagement_level", "quality_thresholds": {"minimum_completeness": 0.7, "minimum_accuracy": 0.8}, "processing_preferences": {"auto_classify": true, "auto_deduplicate": true, "require_manual_review": false}}'),
        sa.Column('business_context', postgresql.JSON(astext_type=sa.Text()), 
                  server_default='{"import_purpose": "", "data_source_description": "", "expected_changes": [], "validation_notes": []}'),
        sa.Column('agent_insights', postgresql.JSON(astext_type=sa.Text()), 
                  server_default='{"classification_confidence": 0.0, "data_quality_issues": [], "recommendations": [], "learning_outcomes": []}'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_data_import_sessions_id', 'data_import_sessions', ['id'])
    op.create_index('ix_data_import_sessions_client_account_id', 'data_import_sessions', ['client_account_id'])
    op.create_index('ix_data_import_sessions_engagement_id', 'data_import_sessions', ['engagement_id'])
    op.create_index('ix_data_import_sessions_session_name', 'data_import_sessions', ['session_name'])
    op.create_index('ix_data_import_sessions_is_default', 'data_import_sessions', ['is_default'])
    op.create_index('ix_data_import_sessions_status', 'data_import_sessions', ['status'])
    
    # 8. Migrations table
    op.create_table('migrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(50), server_default='PLANNING'),
        sa.Column('current_phase', sa.String(50), server_default='DISCOVERY'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('start_date', sa.DateTime(timezone=True)),
        sa.Column('target_completion_date', sa.DateTime(timezone=True)),
        sa.Column('actual_completion_date', sa.DateTime(timezone=True)),
        sa.Column('source_environment', sa.String(100)),
        sa.Column('target_environment', sa.String(100)),
        sa.Column('migration_strategy', sa.String(50)),
        sa.Column('progress_percentage', sa.Integer(), server_default='0'),
        sa.Column('total_assets', sa.Integer(), server_default='0'),
        sa.Column('migrated_assets', sa.Integer(), server_default='0'),
        sa.Column('ai_recommendations', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('risk_assessment', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('cost_estimates', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()))
    )
    op.create_index('ix_migrations_id', 'migrations', ['id'])
    op.create_index('ix_migrations_name', 'migrations', ['name'])
    
    # 9. Discovery Flows table
    op.create_table('discovery_flows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), unique=True, nullable=False),
        sa.Column('master_flow_id', postgresql.UUID(as_uuid=True)),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('import_session_id', postgresql.UUID(as_uuid=True)),
        sa.Column('data_import_id', postgresql.UUID(as_uuid=True), nullable=True),  # FK added later
        sa.Column('flow_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('progress_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('data_import_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('field_mapping_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('data_cleansing_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('asset_inventory_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('dependency_analysis_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tech_debt_assessment_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('learning_scope', sa.String(50), nullable=False, server_default='engagement'),
        sa.Column('memory_isolation_level', sa.String(20), nullable=False, server_default='strict'),
        sa.Column('assessment_ready', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('phase_state', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('agent_state', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('flow_type', sa.String(100)),
        sa.Column('current_phase', sa.String(100)),
        sa.Column('phases_completed', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('flow_state', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('crew_outputs', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('field_mappings', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('discovered_assets', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('dependencies', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('tech_debt_analysis', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('crewai_persistence_id', postgresql.UUID(as_uuid=True)),
        sa.Column('crewai_state_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('error_message', sa.Text()),
        sa.Column('error_phase', sa.String(100)),
        sa.Column('error_details', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True))
    )
    op.create_index('ix_discovery_flows_id', 'discovery_flows', ['id'])
    op.create_index('ix_discovery_flows_flow_id', 'discovery_flows', ['flow_id'])
    op.create_index('ix_discovery_flows_client_account_id', 'discovery_flows', ['client_account_id'])
    op.create_index('ix_discovery_flows_engagement_id', 'discovery_flows', ['engagement_id'])
    op.create_index('ix_discovery_flows_master_flow_id', 'discovery_flows', ['master_flow_id'])
    op.create_index('ix_discovery_flows_status', 'discovery_flows', ['status'])
    
    # 10. Data Imports table
    op.create_table('data_imports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id', ondelete='CASCADE'), nullable=True),
        sa.Column('master_flow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crewai_flow_state_extensions.id', ondelete='CASCADE'), nullable=True),
        sa.Column('import_name', sa.String(255), nullable=False),
        sa.Column('import_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer()),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('source_system', sa.String(100)),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('progress_percentage', sa.Float(), server_default='0.0'),
        sa.Column('total_records', sa.Integer()),
        sa.Column('processed_records', sa.Integer(), server_default='0'),
        sa.Column('failed_records', sa.Integer(), server_default='0'),
        sa.Column('imported_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('error_message', sa.Text()),
        sa.Column('error_details', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_data_imports_id', 'data_imports', ['id'])
    op.create_index('ix_data_imports_client_account_id', 'data_imports', ['client_account_id'])
    op.create_index('ix_data_imports_engagement_id', 'data_imports', ['engagement_id'])
    
    # 11. Assets table
    op.create_table('assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('discovery_flows.flow_id', ondelete='CASCADE'), nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_import_sessions.id', ondelete='CASCADE'), nullable=True),
        sa.Column('migration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('migrations.id'), nullable=True),
        sa.Column('master_flow_id', postgresql.UUID(as_uuid=True)),
        sa.Column('discovery_flow_id', postgresql.UUID(as_uuid=True)),
        sa.Column('assessment_flow_id', postgresql.UUID(as_uuid=True)),
        sa.Column('planning_flow_id', postgresql.UUID(as_uuid=True)),
        sa.Column('execution_flow_id', postgresql.UUID(as_uuid=True)),
        sa.Column('source_phase', sa.String(50), server_default='discovery'),
        sa.Column('current_phase', sa.String(50), server_default='discovery'),
        sa.Column('phase_context', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('asset_name', sa.String(255)),
        sa.Column('hostname', sa.String(255)),
        sa.Column('asset_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('fqdn', sa.String(255)),
        sa.Column('mac_address', sa.String(17)),
        sa.Column('environment', sa.String(50)),
        sa.Column('location', sa.String(100)),
        sa.Column('datacenter', sa.String(100)),
        sa.Column('rack_location', sa.String(50)),
        sa.Column('availability_zone', sa.String(50)),
        sa.Column('operating_system', sa.String(100)),
        sa.Column('os_version', sa.String(50)),
        sa.Column('cpu_cores', sa.Integer()),
        sa.Column('memory_gb', sa.Float()),
        sa.Column('storage_gb', sa.Float()),
        sa.Column('business_owner', sa.String(255)),
        sa.Column('technical_owner', sa.String(255)),
        sa.Column('department', sa.String(100)),
        sa.Column('application_name', sa.String(255)),
        sa.Column('technology_stack', sa.String(255)),
        sa.Column('criticality', sa.String(20)),
        sa.Column('business_criticality', sa.String(20)),
        sa.Column('custom_attributes', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('six_r_strategy', sa.String(50)),
        sa.Column('mapping_status', sa.String(20)),
        sa.Column('migration_priority', sa.Integer(), server_default='5'),
        sa.Column('migration_complexity', sa.String(20)),
        sa.Column('migration_wave', sa.Integer()),
        sa.Column('sixr_ready', sa.String(50)),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('migration_status', sa.String(50), server_default='DISCOVERED'),
        sa.Column('dependencies', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('related_assets', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('discovery_method', sa.String(50)),
        sa.Column('discovery_source', sa.String(100)),
        sa.Column('discovery_timestamp', sa.DateTime(timezone=True)),
        sa.Column('cpu_utilization_percent', sa.Float()),
        sa.Column('memory_utilization_percent', sa.Float()),
        sa.Column('disk_iops', sa.Float()),
        sa.Column('network_throughput_mbps', sa.Float()),
        sa.Column('completeness_score', sa.Float()),
        sa.Column('quality_score', sa.Float()),
        sa.Column('current_monthly_cost', sa.Float()),
        sa.Column('estimated_cloud_cost', sa.Float()),
        sa.Column('imported_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('imported_at', sa.DateTime(timezone=True)),
        sa.Column('source_filename', sa.String(255)),
        sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('field_mappings_used', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True)
    )
    op.create_index('ix_assets_id', 'assets', ['id'])
    op.create_index('ix_assets_client_account_id', 'assets', ['client_account_id'])
    op.create_index('ix_assets_engagement_id', 'assets', ['engagement_id'])
    op.create_index('ix_assets_name', 'assets', ['name'])
    op.create_index('ix_assets_asset_type', 'assets', ['asset_type'])
    op.create_index('ix_assets_environment', 'assets', ['environment'])
    op.create_index('ix_assets_hostname', 'assets', ['hostname'])
    op.create_index('ix_assets_mapping_status', 'assets', ['mapping_status'])
    op.create_index('ix_assets_status', 'assets', ['status'])
    op.create_index('ix_assets_migration_status', 'assets', ['migration_status'])
    op.create_index('ix_assets_source_phase', 'assets', ['source_phase'])
    op.create_index('ix_assets_current_phase', 'assets', ['current_phase'])
    op.create_index('ix_assets_flow_id', 'assets', ['flow_id'])
    op.create_index('ix_assets_master_flow_id', 'assets', ['master_flow_id'])
    op.create_index('ix_assets_discovery_flow_id', 'assets', ['discovery_flow_id'])
    op.create_index('ix_assets_assessment_flow_id', 'assets', ['assessment_flow_id'])
    op.create_index('ix_assets_planning_flow_id', 'assets', ['planning_flow_id'])
    op.create_index('ix_assets_execution_flow_id', 'assets', ['execution_flow_id'])
    
    # 12. Raw Import Records table
    op.create_table('raw_import_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('data_import_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_imports.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id'), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id'), nullable=True),
        sa.Column('master_flow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crewai_flow_state_extensions.id'), nullable=True),
        sa.Column('row_number', sa.Integer(), nullable=False),
        sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('cleansed_data', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('validation_errors', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('processing_notes', sa.Text()),
        sa.Column('is_processed', sa.Boolean(), server_default='false'),
        sa.Column('is_valid', sa.Boolean(), server_default='true'),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True))
    )
    op.create_index('ix_raw_import_records_id', 'raw_import_records', ['id'])
    op.create_index('ix_raw_import_records_data_import_id', 'raw_import_records', ['data_import_id'])
    
    # 13. Import Field Mappings table
    op.create_table('import_field_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('data_import_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_imports.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('master_flow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crewai_flow_state_extensions.id'), nullable=True),
        sa.Column('source_field', sa.String(255), nullable=False),
        sa.Column('target_field', sa.String(255), nullable=False),
        sa.Column('match_type', sa.String(50), nullable=False, server_default='direct'),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('status', sa.String(20), server_default='suggested'),
        sa.Column('suggested_by', sa.String(50), server_default='ai_mapper'),
        sa.Column('approved_by', sa.String(255)),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('transformation_rules', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('ix_import_field_mappings_id', 'import_field_mappings', ['id'])
    op.create_index('ix_import_field_mappings_data_import_id', 'import_field_mappings', ['data_import_id'])
    
    # 14. Import Processing Steps table
    op.create_table('import_processing_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('data_import_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_imports.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_name', sa.String(100), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('description', sa.Text()),
        sa.Column('input_data', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('output_data', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('error_details', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('records_processed', sa.Integer()),
        sa.Column('duration_seconds', sa.Float()),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True))
    )
    
    # 15. Custom Target Fields table
    op.create_table('custom_target_fields',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id'), nullable=False),
        sa.Column('field_name', sa.String(), nullable=False),
        sa.Column('field_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('is_required', sa.Boolean(), server_default='false'),
        sa.Column('is_critical', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('validation_schema', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('default_value', sa.String()),
        sa.Column('allowed_values', postgresql.JSON(astext_type=sa.Text()))
    )
    
    # 16. Assessments table
    op.create_table('assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('migration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('migrations.id'), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id'), nullable=True),
        sa.Column('assessment_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), server_default='PENDING'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('overall_score', sa.Float()),
        sa.Column('risk_level', sa.String(20)),
        sa.Column('confidence_level', sa.Float()),
        sa.Column('recommended_strategy', sa.String(50)),
        sa.Column('alternative_strategies', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('strategy_rationale', sa.Text()),
        sa.Column('current_cost', sa.Float()),
        sa.Column('estimated_migration_cost', sa.Float()),
        sa.Column('estimated_target_cost', sa.Float()),
        sa.Column('cost_savings_potential', sa.Float()),
        sa.Column('roi_months', sa.Integer()),
        sa.Column('identified_risks', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('risk_mitigation', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('blockers', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('dependencies_impact', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('technical_complexity', sa.String(20)),
        sa.Column('compatibility_score', sa.Float()),
        sa.Column('modernization_opportunities', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('performance_impact', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('business_criticality', sa.String(20)),
        sa.Column('downtime_requirements', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('user_impact', sa.Text()),
        sa.Column('compliance_considerations', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('ai_insights', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('ai_confidence', sa.Float()),
        sa.Column('ai_model_version', sa.String(50)),
        sa.Column('estimated_effort_hours', sa.Integer()),
        sa.Column('estimated_duration_days', sa.Integer()),
        sa.Column('recommended_wave', sa.Integer()),
        sa.Column('prerequisites', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('assessor', sa.String(100)),
        sa.Column('assessment_date', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('review_date', sa.DateTime(timezone=True)),
        sa.Column('approval_date', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_assessments_id', 'assessments', ['id'])
    op.create_index('ix_assessments_client_account_id', 'assessments', ['client_account_id'])
    op.create_index('ix_assessments_engagement_id', 'assessments', ['engagement_id'])
    
    # 17. Wave Plans table
    op.create_table('wave_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('migration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('migrations.id'), nullable=False),
        sa.Column('wave_number', sa.Integer(), nullable=False),
        sa.Column('wave_name', sa.String(255)),
        sa.Column('description', sa.Text()),
        sa.Column('planned_start_date', sa.DateTime(timezone=True)),
        sa.Column('planned_end_date', sa.DateTime(timezone=True)),
        sa.Column('actual_start_date', sa.DateTime(timezone=True)),
        sa.Column('actual_end_date', sa.DateTime(timezone=True)),
        sa.Column('total_assets', sa.Integer(), server_default='0'),
        sa.Column('completed_assets', sa.Integer(), server_default='0'),
        sa.Column('estimated_effort_hours', sa.Integer()),
        sa.Column('estimated_cost', sa.Float()),
        sa.Column('prerequisites', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('dependencies', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('constraints', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('overall_risk_level', sa.String(20)),
        sa.Column('complexity_score', sa.Float()),
        sa.Column('success_criteria', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('status', sa.String(50), server_default='planned'),
        sa.Column('progress_percentage', sa.Float(), server_default='0.0'),
        sa.Column('ai_recommendations', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('optimization_score', sa.Float()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_wave_plans_id', 'wave_plans', ['id'])
    op.create_index('ix_wave_plans_client_account_id', 'wave_plans', ['client_account_id'])
    op.create_index('ix_wave_plans_engagement_id', 'wave_plans', ['engagement_id'])
    
    # 18. Asset Dependencies table
    op.create_table('asset_dependencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('depends_on_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dependency_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # 19. Workflow Progress table
    op.create_table('workflow_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stage', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('notes', sa.Text()),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True))
    )
    
    # 20. CMDB SixR Analyses table
    op.create_table('cmdb_sixr_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analysis_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(50), server_default='in_progress'),
        sa.Column('total_assets', sa.Integer(), server_default='0'),
        sa.Column('rehost_count', sa.Integer(), server_default='0'),
        sa.Column('replatform_count', sa.Integer(), server_default='0'),
        sa.Column('refactor_count', sa.Integer(), server_default='0'),
        sa.Column('rearchitect_count', sa.Integer(), server_default='0'),
        sa.Column('retire_count', sa.Integer(), server_default='0'),
        sa.Column('retain_count', sa.Integer(), server_default='0'),
        sa.Column('total_current_cost', sa.Float()),
        sa.Column('total_estimated_cost', sa.Float()),
        sa.Column('potential_savings', sa.Float()),
        sa.Column('analysis_results', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('recommendations', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True)
    )
    op.create_index('ix_cmdb_sixr_analyses_id', 'cmdb_sixr_analyses', ['id'])
    op.create_index('ix_cmdb_sixr_analyses_client_account_id', 'cmdb_sixr_analyses', ['client_account_id'])
    op.create_index('ix_cmdb_sixr_analyses_engagement_id', 'cmdb_sixr_analyses', ['engagement_id'])
    
    # 21. Migration Waves table
    op.create_table('migration_waves',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('wave_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(50), server_default='planned'),
        sa.Column('planned_start_date', sa.DateTime(timezone=True)),
        sa.Column('planned_end_date', sa.DateTime(timezone=True)),
        sa.Column('actual_start_date', sa.DateTime(timezone=True)),
        sa.Column('actual_end_date', sa.DateTime(timezone=True)),
        sa.Column('total_assets', sa.Integer(), server_default='0'),
        sa.Column('completed_assets', sa.Integer(), server_default='0'),
        sa.Column('failed_assets', sa.Integer(), server_default='0'),
        sa.Column('estimated_cost', sa.Float()),
        sa.Column('actual_cost', sa.Float()),
        sa.Column('estimated_effort_hours', sa.Float()),
        sa.Column('actual_effort_hours', sa.Float()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True)
    )
    op.create_index('ix_migration_waves_id', 'migration_waves', ['id'])
    op.create_index('ix_migration_waves_client_account_id', 'migration_waves', ['client_account_id'])
    op.create_index('ix_migration_waves_engagement_id', 'migration_waves', ['engagement_id'])
    op.create_index('ix_migration_waves_wave_number', 'migration_waves', ['wave_number'])
    op.create_index('ix_migration_waves_status', 'migration_waves', ['status'])
    
    # 22. Migration Logs table
    op.create_table('migration_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('migration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('migrations.id'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('level', sa.String(20), server_default='INFO'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('phase', sa.String(50)),
        sa.Column('user_id', sa.String(100)),
        sa.Column('action', sa.String(100))
    )
    op.create_index('ix_migration_logs_id', 'migration_logs', ['id'])
    
    # 23. SixR Analyses table
    op.create_table('sixr_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('migration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('migrations.id'), nullable=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(50), server_default='PENDING', nullable=False),
        sa.Column('priority', sa.Integer(), server_default='3'),
        sa.Column('application_ids', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('application_data', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('current_iteration', sa.Integer(), server_default='1'),
        sa.Column('progress_percentage', sa.Float(), server_default='0.0'),
        sa.Column('estimated_completion', sa.DateTime(timezone=True)),
        sa.Column('final_recommendation', sa.String(50)),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('created_by', sa.String(100)),
        sa.Column('updated_by', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('analysis_config', postgresql.JSON(astext_type=sa.Text()))
    )
    op.create_index('ix_sixr_analyses_id', 'sixr_analyses', ['id'])
    op.create_index('ix_sixr_analyses_name', 'sixr_analyses', ['name'])
    op.create_index('ix_sixr_analyses_client_account_id', 'sixr_analyses', ['client_account_id'])
    op.create_index('ix_sixr_analyses_engagement_id', 'sixr_analyses', ['engagement_id'])
    
    # 24. SixR Iterations table
    op.create_table('sixr_iterations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sixr_analyses.id'), nullable=False),
        sa.Column('iteration_number', sa.Integer(), nullable=False),
        sa.Column('iteration_name', sa.String(255)),
        sa.Column('iteration_reason', sa.Text()),
        sa.Column('stakeholder_feedback', sa.Text()),
        sa.Column('parameter_changes', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('question_responses', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('recommendation_data', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('analysis_duration', sa.Float()),
        sa.Column('agent_insights', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('error_details', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('created_by', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True))
    )
    op.create_index('ix_sixr_iterations_id', 'sixr_iterations', ['id'])
    
    # 25. SixR Recommendations table
    op.create_table('sixr_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sixr_analyses.id'), nullable=False),
        sa.Column('iteration_number', sa.Integer(), server_default='1'),
        sa.Column('recommended_strategy', sa.String(50), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('strategy_scores', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('key_factors', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('assumptions', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('next_steps', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('estimated_effort', sa.String(50)),
        sa.Column('estimated_timeline', sa.String(100)),
        sa.Column('estimated_cost_impact', sa.String(50)),
        sa.Column('risk_factors', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('business_benefits', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('technical_benefits', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(100))
    )
    
    # 26. SixR Questions table
    op.create_table('sixr_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('question_id', sa.String(100), unique=True, nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(50), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='1'),
        sa.Column('required', sa.Boolean(), server_default='false'),
        sa.Column('active', sa.Boolean(), server_default='true'),
        sa.Column('options', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('validation_rules', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('help_text', sa.Text()),
        sa.Column('depends_on', sa.String(100)),
        sa.Column('show_conditions', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('skip_conditions', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('created_by', sa.String(100)),
        sa.Column('updated_by', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('version', sa.String(20), server_default='1.0'),
        sa.Column('parent_question_id', sa.String(100))
    )
    op.create_index('ix_sixr_questions_id', 'sixr_questions', ['id'])
    op.create_index('ix_sixr_questions_question_id', 'sixr_questions', ['question_id'])
    
    # 27. SixR Analysis Parameters table
    op.create_table('sixr_analysis_parameters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sixr_analyses.id'), nullable=False),
        sa.Column('iteration_number', sa.Integer(), nullable=False),
        sa.Column('business_value', sa.Float(), nullable=False, server_default='3'),
        sa.Column('technical_complexity', sa.Float(), nullable=False, server_default='3'),
        sa.Column('migration_urgency', sa.Float(), nullable=False, server_default='3'),
        sa.Column('compliance_requirements', sa.Float(), nullable=False, server_default='3'),
        sa.Column('cost_sensitivity', sa.Float(), nullable=False, server_default='3'),
        sa.Column('risk_tolerance', sa.Float(), nullable=False, server_default='3'),
        sa.Column('innovation_priority', sa.Float(), nullable=False, server_default='3'),
        sa.Column('application_type', sa.String(20), server_default='custom'),
        sa.Column('parameter_source', sa.String(50), server_default='initial'),
        sa.Column('confidence_level', sa.Float(), server_default='1.0'),
        sa.Column('created_by', sa.String(100)),
        sa.Column('updated_by', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('parameter_notes', sa.Text()),
        sa.Column('validation_status', sa.String(20), server_default='valid')
    )
    op.create_index('ix_sixr_analysis_parameters_id', 'sixr_analysis_parameters', ['id'])
    
    # 28. SixR Parameters table
    op.create_table('sixr_parameters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('parameter_key', sa.String(255), unique=True, nullable=False),
        sa.Column('value', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_sixr_parameters_parameter_key', 'sixr_parameters', ['parameter_key'])
    
    # 29. SixR Question Responses table
    op.create_table('sixr_question_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sixr_analyses.id'), nullable=False),
        sa.Column('iteration_number', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.String(100), sa.ForeignKey('sixr_questions.question_id'), nullable=False),
        sa.Column('response_value', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('response_text', sa.Text()),
        sa.Column('confidence', sa.Float(), server_default='1.0'),
        sa.Column('source', sa.String(50), server_default='user'),
        sa.Column('response_time', sa.Float()),
        sa.Column('validation_status', sa.String(20), server_default='pending'),
        sa.Column('validation_errors', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('created_by', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_sixr_question_responses_id', 'sixr_question_responses', ['id'])
    
    # 30. Tags table
    op.create_table('tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('reference_embedding', sa.Text()),  # Will be vector(1536) when pgvector available
        sa.Column('confidence_threshold', sa.Float(), server_default='0.7'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('usage_count', sa.Integer(), server_default='0'),
        sa.Column('last_used', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_tags_id', 'tags', ['id'])
    op.create_index('ix_tags_client_account_id', 'tags', ['client_account_id'])
    op.create_index('ix_tags_name', 'tags', ['name'])
    op.create_index('ix_tags_category', 'tags', ['category'])
    op.create_index('ix_tags_is_active', 'tags', ['is_active'])
    
    # 31. Asset Embeddings table
    op.create_table('asset_embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('embedding', sa.Text()),  # Will be vector(1536) when pgvector available
        sa.Column('source_text', sa.Text()),
        sa.Column('embedding_model', sa.String(100), server_default='text-embedding-ada-002'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_asset_embeddings_id', 'asset_embeddings', ['id'])
    op.create_index('ix_asset_embeddings_asset_id', 'asset_embeddings', ['asset_id'])
    op.create_index('ix_asset_embeddings_client_account_id', 'asset_embeddings', ['client_account_id'])
    op.create_index('ix_asset_embeddings_engagement_id', 'asset_embeddings', ['engagement_id'])
    
    # 32. Asset Tags table
    op.create_table('asset_tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tags.id', ondelete='CASCADE'), nullable=False),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('assigned_method', sa.String(50)),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('is_validated', sa.Boolean(), server_default='false'),
        sa.Column('validated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_asset_tags_asset_id', 'asset_tags', ['asset_id'])
    op.create_index('ix_asset_tags_tag_id', 'asset_tags', ['tag_id'])
    
    # 33. LLM Usage Logs table
    op.create_table('llm_usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id'), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id'), nullable=True),
        sa.Column('user_id', sa.Integer()),
        sa.Column('username', sa.String(255)),
        sa.Column('session_id', sa.String(255)),
        sa.Column('request_id', sa.String(255)),
        sa.Column('endpoint', sa.String(500)),
        sa.Column('page_context', sa.String(255)),
        sa.Column('feature_context', sa.String(255)),
        sa.Column('llm_provider', sa.String(100), nullable=False),
        sa.Column('model_name', sa.String(255), nullable=False),
        sa.Column('model_version', sa.String(100)),
        sa.Column('input_tokens', sa.Integer()),
        sa.Column('output_tokens', sa.Integer()),
        sa.Column('total_tokens', sa.Integer()),
        sa.Column('input_cost', sa.Numeric(precision=10, scale=6)),
        sa.Column('output_cost', sa.Numeric(precision=10, scale=6)),
        sa.Column('total_cost', sa.Numeric(precision=10, scale=6)),
        sa.Column('cost_currency', sa.String(10), nullable=False, server_default='USD'),
        sa.Column('response_time_ms', sa.Integer()),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_type', sa.String(255)),
        sa.Column('error_message', sa.Text()),
        sa.Column('request_data', postgresql.JSONB(astext_type=sa.Text())),
        sa.Column('response_data', postgresql.JSONB(astext_type=sa.Text())),
        sa.Column('additional_metadata', postgresql.JSONB(astext_type=sa.Text())),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500))
    )
    op.create_index('idx_llm_usage_client_account', 'llm_usage_logs', ['client_account_id'])
    op.create_index('idx_llm_usage_engagement', 'llm_usage_logs', ['engagement_id'])
    op.create_index('idx_llm_usage_user', 'llm_usage_logs', ['user_id'])
    op.create_index('idx_llm_usage_created_at', 'llm_usage_logs', ['created_at'])
    op.create_index('idx_llm_usage_provider_model', 'llm_usage_logs', ['llm_provider', 'model_name'])
    op.create_index('idx_llm_usage_success', 'llm_usage_logs', ['success'])
    op.create_index('idx_llm_usage_page_context', 'llm_usage_logs', ['page_context'])
    op.create_index('idx_llm_usage_feature_context', 'llm_usage_logs', ['feature_context'])
    op.create_index('idx_llm_usage_reporting', 'llm_usage_logs', ['client_account_id', 'created_at', 'success'])
    op.create_index('idx_llm_usage_cost_analysis', 'llm_usage_logs', ['client_account_id', 'llm_provider', 'model_name', 'created_at'])
    
    # 34. LLM Usage Summary table
    op.create_table('llm_usage_summary',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id'), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id'), nullable=True),
        sa.Column('user_id', sa.Integer()),
        sa.Column('llm_provider', sa.String(100)),
        sa.Column('model_name', sa.String(255)),
        sa.Column('page_context', sa.String(255)),
        sa.Column('feature_context', sa.String(255)),
        sa.Column('total_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_input_tokens', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_output_tokens', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_cost', sa.Numeric(precision=12, scale=6), nullable=False, server_default='0'),
        sa.Column('avg_response_time_ms', sa.Integer()),
        sa.Column('min_response_time_ms', sa.Integer()),
        sa.Column('max_response_time_ms', sa.Integer()),
        sa.UniqueConstraint('period_type', 'period_start', 'client_account_id', 'engagement_id', 'user_id', 'llm_provider', 'model_name', 'page_context', 'feature_context', name='uq_usage_summary_period_context')
    )
    op.create_index('idx_usage_summary_period', 'llm_usage_summary', ['period_type', 'period_start', 'period_end'])
    op.create_index('idx_usage_summary_client', 'llm_usage_summary', ['client_account_id', 'period_start'])
    op.create_index('idx_usage_summary_model', 'llm_usage_summary', ['llm_provider', 'model_name', 'period_start'])
    
    # 35. Feedback table
    op.create_table('feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('page', sa.String(255)),
        sa.Column('rating', sa.Integer()),
        sa.Column('comment', sa.Text()),
        sa.Column('category', sa.String(50), server_default='general'),
        sa.Column('breadcrumb', sa.String(500)),
        sa.Column('filename', sa.String(255)),
        sa.Column('original_analysis', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('user_corrections', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('asset_type_override', sa.String(100)),
        sa.Column('status', sa.String(20), server_default='new'),
        sa.Column('processed', sa.Boolean(), server_default='false'),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('user_timestamp', sa.String(50)),
        sa.Column('client_ip', sa.String(45)),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id', ondelete='CASCADE'), nullable=True),
        sa.Column('learning_patterns_extracted', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('confidence_impact', sa.Float(), server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True))
    )
    op.create_index('ix_feedback_id', 'feedback', ['id'])
    op.create_index('ix_feedback_feedback_type', 'feedback', ['feedback_type'])
    op.create_index('ix_feedback_page', 'feedback', ['page'])
    
    # 36. Feedback Summaries table
    op.create_table('feedback_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('page', sa.String(255)),
        sa.Column('time_period', sa.String(20), server_default='all_time'),
        sa.Column('total_feedback', sa.Integer(), server_default='0'),
        sa.Column('average_rating', sa.Float(), server_default='0.0'),
        sa.Column('status_counts', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('rating_distribution', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('category_counts', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('feedback_trend', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('rating_trend', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE')),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id', ondelete='CASCADE')),
        sa.Column('last_calculated', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('calculation_duration_ms', sa.Integer())
    )
    op.create_index('ix_feedback_summaries_id', 'feedback_summaries', ['id'])
    op.create_index('ix_feedback_summaries_feedback_type', 'feedback_summaries', ['feedback_type'])
    op.create_index('ix_feedback_summaries_page', 'feedback_summaries', ['page'])
    
    # 37. Flow Deletion Audit table
    op.create_table('flow_deletion_audit',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('deletion_type', sa.String(), nullable=False),
        sa.Column('deletion_reason', sa.Text()),
        sa.Column('deletion_method', sa.String(), nullable=False),
        sa.Column('data_deleted', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('deletion_impact', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('cleanup_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('shared_memory_cleaned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('knowledge_base_refs_cleaned', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('agent_memory_cleaned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_by', sa.String(), nullable=False),
        sa.Column('deletion_duration_ms', sa.Integer()),
        sa.Column('recovery_possible', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('recovery_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}')
    )
    op.create_index('ix_flow_deletion_audit_flow_id', 'flow_deletion_audit', ['flow_id'])
    op.create_index('ix_flow_deletion_audit_session_id', 'flow_deletion_audit', ['session_id'])
    op.create_index('ix_flow_deletion_audit_client_account_id', 'flow_deletion_audit', ['client_account_id'])
    op.create_index('ix_flow_deletion_audit_engagement_id', 'flow_deletion_audit', ['engagement_id'])
    op.create_index('ix_flow_deletion_audit_deletion_type', 'flow_deletion_audit', ['deletion_type'])
    op.create_index('ix_flow_deletion_audit_deleted_at', 'flow_deletion_audit', ['deleted_at'])
    
    # 38. Security Audit Logs table
    op.create_table('security_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_category', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='INFO'),
        sa.Column('actor_user_id', sa.String(36), nullable=False),
        sa.Column('actor_email', sa.String(255)),
        sa.Column('actor_role', sa.String(50)),
        sa.Column('target_user_id', sa.String(36)),
        sa.Column('target_email', sa.String(255)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text()),
        sa.Column('request_path', sa.String(500)),
        sa.Column('request_method', sa.String(10)),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text())),
        sa.Column('is_suspicious', sa.Boolean(), server_default='false'),
        sa.Column('requires_review', sa.Boolean(), server_default='false'),
        sa.Column('is_blocked', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('reviewed_by', sa.String(36))
    )
    op.create_index('ix_security_audit_logs_event_type', 'security_audit_logs', ['event_type'])
    op.create_index('ix_security_audit_logs_event_category', 'security_audit_logs', ['event_category'])
    op.create_index('ix_security_audit_logs_actor_user_id', 'security_audit_logs', ['actor_user_id'])
    op.create_index('ix_security_audit_logs_target_user_id', 'security_audit_logs', ['target_user_id'])
    op.create_index('ix_security_audit_logs_is_suspicious', 'security_audit_logs', ['is_suspicious'])
    op.create_index('ix_security_audit_logs_requires_review', 'security_audit_logs', ['requires_review'])
    op.create_index('ix_security_audit_logs_created_at', 'security_audit_logs', ['created_at'])
    
    # 39. Role Change Approvals table
    op.create_table('role_change_approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('requested_by', sa.String(36), nullable=False),
        sa.Column('target_user_id', sa.String(36), nullable=False),
        sa.Column('current_role', sa.String(50), nullable=False),
        sa.Column('requested_role', sa.String(50), nullable=False),
        sa.Column('justification', sa.Text()),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('approved_by', sa.String(36)),
        sa.Column('approval_notes', sa.Text()),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True))
    )
    op.create_index('ix_role_change_approvals_requested_by', 'role_change_approvals', ['requested_by'])
    op.create_index('ix_role_change_approvals_target_user_id', 'role_change_approvals', ['target_user_id'])
    
    # 40. RBAC tables
    op.create_table('user_profiles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING_APPROVAL'),
        sa.Column('approval_requested_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('registration_reason', sa.Text()),
        sa.Column('organization', sa.String(255)),
        sa.Column('role_description', sa.String(255)),
        sa.Column('requested_access_level', sa.String(20), server_default='READ_ONLY'),
        sa.Column('phone_number', sa.String(20)),
        sa.Column('manager_email', sa.String(255)),
        sa.Column('linkedin_profile', sa.String(255)),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('login_count', sa.Integer(), server_default='0'),
        sa.Column('failed_login_attempts', sa.Integer(), server_default='0'),
        sa.Column('last_failed_login', sa.DateTime(timezone=True)),
        sa.Column('notification_preferences', postgresql.JSON(astext_type=sa.Text()), 
                  server_default='{"email_notifications": true, "system_alerts": true, "learning_updates": false, "weekly_reports": true}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('ix_user_profiles_status', 'user_profiles', ['status'])
    
    # 41. Enhanced User Profiles table
    op.create_table('enhanced_user_profiles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING_APPROVAL'),
        sa.Column('role_level', sa.String(30), nullable=False, server_default='VIEWER'),
        sa.Column('data_scope', sa.String(20), nullable=False, server_default='DEMO_ONLY'),
        sa.Column('scope_client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id'), nullable=True),
        sa.Column('scope_engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id'), nullable=True),
        sa.Column('registration_reason', sa.Text()),
        sa.Column('organization', sa.String(255)),
        sa.Column('role_description', sa.String(255)),
        sa.Column('phone_number', sa.String(20)),
        sa.Column('manager_email', sa.String(255)),
        sa.Column('approval_requested_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('login_count', sa.Integer(), server_default='0'),
        sa.Column('failed_login_attempts', sa.Integer(), server_default='0'),
        sa.Column('is_deleted', sa.Boolean(), server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('delete_reason', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_enhanced_user_profiles_status', 'enhanced_user_profiles', ['status'])
    op.create_index('ix_enhanced_user_profiles_role_level', 'enhanced_user_profiles', ['role_level'])
    op.create_index('ix_enhanced_user_profiles_data_scope', 'enhanced_user_profiles', ['data_scope'])
    op.create_index('ix_enhanced_user_profiles_is_deleted', 'enhanced_user_profiles', ['is_deleted'])
    
    # 42. User Roles table
    op.create_table('user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_type', sa.String(50), nullable=False),
        sa.Column('role_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('permissions', postgresql.JSON(astext_type=sa.Text()), 
                  server_default='{"can_create_clients": false, "can_manage_engagements": false, "can_import_data": true, "can_export_data": true, "can_view_analytics": true, "can_manage_users": false, "can_configure_agents": false, "can_access_admin_console": false}'),
        sa.Column('scope_type', sa.String(20), server_default='global'),
        sa.Column('scope_client_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id'), nullable=True),
        sa.Column('scope_engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('ix_user_roles_id', 'user_roles', ['id'])
    op.create_index('ix_user_roles_user_id', 'user_roles', ['user_id'])
    op.create_index('ix_user_roles_is_active', 'user_roles', ['is_active'])
    
    # 43. Role Permissions table
    op.create_table('role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('role_level', sa.String(30), nullable=False),
        sa.Column('can_manage_platform_settings', sa.Boolean(), server_default='false'),
        sa.Column('can_manage_all_clients', sa.Boolean(), server_default='false'),
        sa.Column('can_manage_all_users', sa.Boolean(), server_default='false'),
        sa.Column('can_purge_deleted_data', sa.Boolean(), server_default='false'),
        sa.Column('can_view_system_logs', sa.Boolean(), server_default='false'),
        sa.Column('can_create_clients', sa.Boolean(), server_default='false'),
        sa.Column('can_modify_client_settings', sa.Boolean(), server_default='false'),
        sa.Column('can_manage_client_users', sa.Boolean(), server_default='false'),
        sa.Column('can_delete_client_data', sa.Boolean(), server_default='false'),
        sa.Column('can_create_engagements', sa.Boolean(), server_default='false'),
        sa.Column('can_modify_engagement_settings', sa.Boolean(), server_default='false'),
        sa.Column('can_manage_engagement_users', sa.Boolean(), server_default='false'),
        sa.Column('can_delete_engagement_data', sa.Boolean(), server_default='false'),
        sa.Column('can_import_data', sa.Boolean(), server_default='false'),
        sa.Column('can_export_data', sa.Boolean(), server_default='false'),
        sa.Column('can_view_analytics', sa.Boolean(), server_default='false'),
        sa.Column('can_modify_data', sa.Boolean(), server_default='false'),
        sa.Column('can_configure_agents', sa.Boolean(), server_default='false'),
        sa.Column('can_view_agent_insights', sa.Boolean(), server_default='false'),
        sa.Column('can_approve_agent_decisions', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_role_permissions_role_level', 'role_permissions', ['role_level'])
    
    # 44. Client Access table
    op.create_table('client_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_profiles.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('access_level', sa.String(20), nullable=False),
        sa.Column('permissions', postgresql.JSON(astext_type=sa.Text()), 
                  server_default='{"can_view_data": true, "can_import_data": false, "can_export_data": false, "can_manage_engagements": false, "can_configure_client_settings": false, "can_manage_client_users": false}'),
        sa.Column('restricted_environments', postgresql.JSON(astext_type=sa.Text()), server_default='[]'),
        sa.Column('restricted_data_types', postgresql.JSON(astext_type=sa.Text()), server_default='[]'),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True)),
        sa.Column('access_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('ix_client_access_id', 'client_access', ['id'])
    op.create_index('ix_client_access_user_profile_id', 'client_access', ['user_profile_id'])
    op.create_index('ix_client_access_client_account_id', 'client_access', ['client_account_id'])
    op.create_index('ix_client_access_is_active', 'client_access', ['is_active'])
    
    # 45. Engagement Access table
    op.create_table('engagement_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_profiles.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('access_level', sa.String(20), nullable=False),
        sa.Column('engagement_role', sa.String(100)),
        sa.Column('permissions', postgresql.JSON(astext_type=sa.Text()), 
                  server_default='{"can_view_data": true, "can_import_data": false, "can_export_data": false, "can_manage_sessions": false, "can_configure_agents": false, "can_approve_migration_decisions": false, "can_access_sensitive_data": false}'),
        sa.Column('restricted_sessions', postgresql.JSON(astext_type=sa.Text()), server_default='[]'),
        sa.Column('allowed_session_types', postgresql.JSON(astext_type=sa.Text()), server_default='["data_import", "validation_run"]'),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True)),
        sa.Column('access_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('ix_engagement_access_id', 'engagement_access', ['id'])
    op.create_index('ix_engagement_access_user_profile_id', 'engagement_access', ['user_profile_id'])
    op.create_index('ix_engagement_access_engagement_id', 'engagement_access', ['engagement_id'])
    op.create_index('ix_engagement_access_is_active', 'engagement_access', ['is_active'])
    
    # 46. Access Audit Log table
    op.create_table('access_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50)),
        sa.Column('resource_id', sa.String(255)),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id'), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id'), nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_import_sessions.id'), nullable=True),
        sa.Column('result', sa.String(20), nullable=False),
        sa.Column('reason', sa.Text()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text()),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('ix_access_audit_log_id', 'access_audit_log', ['id'])
    op.create_index('ix_access_audit_log_user_id', 'access_audit_log', ['user_id'])
    op.create_index('ix_access_audit_log_action_type', 'access_audit_log', ['action_type'])
    op.create_index('ix_access_audit_log_created_at', 'access_audit_log', ['created_at'])
    
    # 47. Enhanced Access Audit Log table
    op.create_table('enhanced_access_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50)),
        sa.Column('resource_id', sa.String(255)),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id'), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id'), nullable=True),
        sa.Column('result', sa.String(20), nullable=False),
        sa.Column('reason', sa.Text()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text()),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('user_role_level', sa.String(30)),
        sa.Column('user_data_scope', sa.String(20)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('ix_enhanced_access_audit_log_user_id', 'enhanced_access_audit_log', ['user_id'])
    op.create_index('ix_enhanced_access_audit_log_action_type', 'enhanced_access_audit_log', ['action_type'])
    op.create_index('ix_enhanced_access_audit_log_created_at', 'enhanced_access_audit_log', ['created_at'])
    
    # 48. Soft Deleted Items table
    op.create_table('soft_deleted_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('item_type', sa.String(30), nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_name', sa.String(255)),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_accounts.id'), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('engagements.id'), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('delete_reason', sa.Text()),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('review_decision', sa.String(20)),
        sa.Column('review_notes', sa.Text()),
        sa.Column('purged_at', sa.DateTime(timezone=True)),
        sa.Column('purged_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending_review'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_soft_deleted_items_item_type', 'soft_deleted_items', ['item_type'])
    op.create_index('ix_soft_deleted_items_item_id', 'soft_deleted_items', ['item_id'])
    op.create_index('ix_soft_deleted_items_status', 'soft_deleted_items', ['status'])
    
    # Now add foreign key constraints for users table self-references
    op.create_foreign_key('fk_users_default_client_id', 'users', 'client_accounts', ['default_client_id'], ['id'])
    op.create_foreign_key('fk_users_default_engagement_id', 'users', 'engagements', ['default_engagement_id'], ['id'])
    
    # Add foreign key for data_imports.data_import_id reference in discovery_flows
    op.create_foreign_key('fk_discovery_flows_data_import_id', 'discovery_flows', 'data_imports', ['data_import_id'], ['id'])


def downgrade() -> None:
    # Drop all tables in reverse dependency order
    op.drop_table('soft_deleted_items')
    op.drop_table('enhanced_access_audit_log')
    op.drop_table('access_audit_log')
    op.drop_table('engagement_access')
    op.drop_table('client_access')
    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    op.drop_table('enhanced_user_profiles')
    op.drop_table('user_profiles')
    op.drop_table('role_change_approvals')
    op.drop_table('security_audit_logs')
    op.drop_table('flow_deletion_audit')
    op.drop_table('feedback_summaries')
    op.drop_table('feedback')
    op.drop_table('llm_usage_summary')
    op.drop_table('llm_usage_logs')
    op.drop_table('asset_tags')
    op.drop_table('asset_embeddings')
    op.drop_table('tags')
    op.drop_table('sixr_question_responses')
    op.drop_table('sixr_parameters')
    op.drop_table('sixr_analysis_parameters')
    op.drop_table('sixr_questions')
    op.drop_table('sixr_recommendations')
    op.drop_table('sixr_iterations')
    op.drop_table('sixr_analyses')
    op.drop_table('migration_logs')
    op.drop_table('migration_waves')
    op.drop_table('cmdb_sixr_analyses')
    op.drop_table('workflow_progress')
    op.drop_table('asset_dependencies')
    op.drop_table('wave_plans')
    op.drop_table('assessments')
    op.drop_table('custom_target_fields')
    op.drop_table('import_processing_steps')
    op.drop_table('import_field_mappings')
    op.drop_table('raw_import_records')
    op.drop_table('assets')
    op.drop_table('data_imports')
    op.drop_table('discovery_flows')
    op.drop_table('migrations')
    op.drop_table('data_import_sessions')
    op.drop_table('crewai_flow_state_extensions')
    op.drop_table('user_account_associations')
    op.drop_table('engagements')
    op.drop_table('llm_model_pricing')
    op.drop_table('users')
    op.drop_table('client_accounts')
    
    # Note: No custom enum types to drop since we used string types
    
    # Drop pgvector extension
    op.execute('DROP EXTENSION IF EXISTS vector')