"""add_asset_inventory_enhancements_manual

Revision ID: 5992adf19317
Revises: 43d83e459875
Create Date: 2025-05-31 17:42:54.718094

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5992adf19317'
down_revision = '43d83e459875'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to assets table for comprehensive asset inventory
    
    # Multi-tenant support
    op.add_column('assets', sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('assets', sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Core Asset Information
    op.add_column('assets', sa.Column('asset_name', sa.String(255), nullable=True, index=True))
    op.add_column('assets', sa.Column('intelligent_asset_type', sa.String(100), nullable=True, index=True))
    
    # Infrastructure Details
    op.add_column('assets', sa.Column('hardware_type', sa.String(100), nullable=True))
    
    # Migration Critical Attributes
    op.add_column('assets', sa.Column('business_owner', sa.String(255), nullable=True))
    op.add_column('assets', sa.Column('technical_owner', sa.String(255), nullable=True))
    op.add_column('assets', sa.Column('department', sa.String(100), nullable=True, index=True))
    
    # Application Specific
    op.add_column('assets', sa.Column('application_id', sa.String(255), nullable=True, index=True))
    op.add_column('assets', sa.Column('application_version', sa.String(100), nullable=True))
    op.add_column('assets', sa.Column('programming_language', sa.String(100), nullable=True))
    op.add_column('assets', sa.Column('framework', sa.String(100), nullable=True))
    op.add_column('assets', sa.Column('database_type', sa.String(100), nullable=True))
    
    # Cloud Readiness Assessment
    op.add_column('assets', sa.Column('cloud_readiness_score', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('modernization_complexity', sa.String(50), nullable=True))
    op.add_column('assets', sa.Column('tech_debt_score', sa.Float(), nullable=True))
    
    # Enhanced Dependencies
    op.add_column('assets', sa.Column('server_dependencies', sa.JSON(), nullable=True))
    op.add_column('assets', sa.Column('application_dependencies', sa.JSON(), nullable=True))
    op.add_column('assets', sa.Column('database_dependencies', sa.JSON(), nullable=True))
    op.add_column('assets', sa.Column('network_dependencies', sa.JSON(), nullable=True))
    
    # Financial Information
    op.add_column('assets', sa.Column('estimated_monthly_cost', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('license_cost', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('support_cost', sa.Float(), nullable=True))
    
    # Security & Compliance
    op.add_column('assets', sa.Column('security_classification', sa.String(50), nullable=True))
    op.add_column('assets', sa.Column('compliance_frameworks', sa.JSON(), nullable=True))
    op.add_column('assets', sa.Column('vulnerability_score', sa.Float(), nullable=True))
    
    # Migration details (enhanced)
    op.add_column('assets', sa.Column('sixr_ready', sa.String(50), nullable=True))
    op.add_column('assets', sa.Column('estimated_migration_effort', sa.String(100), nullable=True))
    
    # 6R Strategy Assessment
    op.add_column('assets', sa.Column('recommended_6r_strategy', sa.String(50), nullable=True))
    op.add_column('assets', sa.Column('strategy_confidence', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('strategy_rationale', sa.Text(), nullable=True))
    
    # Workflow Status Tracking
    op.add_column('assets', sa.Column('discovery_status', sa.String(50), default='discovered', index=True))
    op.add_column('assets', sa.Column('mapping_status', sa.String(50), default='pending', index=True))
    op.add_column('assets', sa.Column('cleanup_status', sa.String(50), default='pending', index=True))
    op.add_column('assets', sa.Column('assessment_readiness', sa.String(50), default='not_ready', index=True))
    
    # Data Quality Metrics
    op.add_column('assets', sa.Column('completeness_score', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('quality_score', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('missing_critical_fields', sa.JSON(), nullable=True))
    op.add_column('assets', sa.Column('data_quality_issues', sa.JSON(), nullable=True))
    
    # AI insights (enhanced)
    op.add_column('assets', sa.Column('ai_analysis_result', sa.JSON(), nullable=True))
    op.add_column('assets', sa.Column('ai_confidence_score', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('last_ai_analysis', sa.DateTime(), nullable=True))
    
    # Source Information
    op.add_column('assets', sa.Column('source_system', sa.String(100), nullable=True))
    op.add_column('assets', sa.Column('source_file', sa.String(255), nullable=True))
    op.add_column('assets', sa.Column('import_batch_id', sa.String(255), nullable=True, index=True))
    
    # Custom Attributes and Audit
    op.add_column('assets', sa.Column('custom_attributes', sa.JSON(), nullable=True))
    op.add_column('assets', sa.Column('created_by', sa.String(255), nullable=True))
    op.add_column('assets', sa.Column('updated_by', sa.String(255), nullable=True))
    
    # Update existing field types for compatibility
    op.alter_column('assets', 'asset_id', type_=sa.String(255), nullable=True)
    op.alter_column('assets', 'migration_id', nullable=True)
    op.alter_column('assets', 'operating_system', type_=sa.String(255), nullable=True)
    op.alter_column('assets', 'os_version', type_=sa.String(100), nullable=True)
    op.alter_column('assets', 'business_criticality', type_=sa.String(50), nullable=True, index=True)
    op.alter_column('assets', 'compliance_requirements', type_=sa.Text(), nullable=True)
    op.alter_column('assets', 'migration_priority', type_=sa.String(50), nullable=True)
    op.alter_column('assets', 'migration_complexity', type_=sa.String(50), nullable=True)
    op.alter_column('assets', 'environment', type_=sa.String(50), nullable=True, index=True)
    op.alter_column('assets', 'hostname', nullable=True, index=True)
    op.alter_column('assets', 'ip_address', nullable=True)
    
    # Add foreign key constraints
    op.create_foreign_key('fk_assets_client_account', 'assets', 'client_accounts', ['client_account_id'], ['id'])
    op.create_foreign_key('fk_assets_engagement', 'assets', 'engagements', ['engagement_id'], ['id'])
    
    # Enhance asset_dependencies table
    op.add_column('asset_dependencies', sa.Column('dependency_strength', sa.String(50), nullable=True))
    op.add_column('asset_dependencies', sa.Column('port_number', sa.Integer(), nullable=True))
    op.add_column('asset_dependencies', sa.Column('protocol', sa.String(50), nullable=True))
    op.add_column('asset_dependencies', sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('asset_dependencies', sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('asset_dependencies', sa.Column('created_by', sa.String(255), nullable=True))
    
    # Update asset_dependencies dependency_type field
    op.alter_column('asset_dependencies', 'dependency_type', type_=sa.String(100), nullable=False)
    
    # Add foreign key constraints for asset_dependencies
    op.create_foreign_key('fk_asset_dependencies_client_account', 'asset_dependencies', 'client_accounts', ['client_account_id'], ['id'])
    op.create_foreign_key('fk_asset_dependencies_engagement', 'asset_dependencies', 'engagements', ['engagement_id'], ['id'])
    
    # Create workflow_progress table
    op.create_table('workflow_progress',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('asset_id', sa.Integer(), sa.ForeignKey('assets.id'), nullable=False),
        sa.Column('phase', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('progress_percentage', sa.Float(), default=0.0),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id']),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id']),
    )


def downgrade() -> None:
    # Drop workflow_progress table
    op.drop_table('workflow_progress')
    
    # Remove foreign key constraints from asset_dependencies
    op.drop_constraint('fk_asset_dependencies_engagement', 'asset_dependencies', type_='foreignkey')
    op.drop_constraint('fk_asset_dependencies_client_account', 'asset_dependencies', type_='foreignkey')
    
    # Remove added columns from asset_dependencies
    op.drop_column('asset_dependencies', 'created_by')
    op.drop_column('asset_dependencies', 'engagement_id')
    op.drop_column('asset_dependencies', 'client_account_id')
    op.drop_column('asset_dependencies', 'protocol')
    op.drop_column('asset_dependencies', 'port_number')
    op.drop_column('asset_dependencies', 'dependency_strength')
    
    # Remove foreign key constraints from assets
    op.drop_constraint('fk_assets_engagement', 'assets', type_='foreignkey')
    op.drop_constraint('fk_assets_client_account', 'assets', type_='foreignkey')
    
    # Remove all added columns from assets
    op.drop_column('assets', 'updated_by')
    op.drop_column('assets', 'created_by')
    op.drop_column('assets', 'custom_attributes')
    op.drop_column('assets', 'import_batch_id')
    op.drop_column('assets', 'source_file')
    op.drop_column('assets', 'source_system')
    op.drop_column('assets', 'last_ai_analysis')
    op.drop_column('assets', 'ai_confidence_score')
    op.drop_column('assets', 'ai_analysis_result')
    op.drop_column('assets', 'data_quality_issues')
    op.drop_column('assets', 'missing_critical_fields')
    op.drop_column('assets', 'quality_score')
    op.drop_column('assets', 'completeness_score')
    op.drop_column('assets', 'assessment_readiness')
    op.drop_column('assets', 'cleanup_status')
    op.drop_column('assets', 'mapping_status')
    op.drop_column('assets', 'discovery_status')
    op.drop_column('assets', 'strategy_rationale')
    op.drop_column('assets', 'strategy_confidence')
    op.drop_column('assets', 'recommended_6r_strategy')
    op.drop_column('assets', 'estimated_migration_effort')
    op.drop_column('assets', 'sixr_ready')
    op.drop_column('assets', 'vulnerability_score')
    op.drop_column('assets', 'compliance_frameworks')
    op.drop_column('assets', 'security_classification')
    op.drop_column('assets', 'support_cost')
    op.drop_column('assets', 'license_cost')
    op.drop_column('assets', 'estimated_monthly_cost')
    op.drop_column('assets', 'network_dependencies')
    op.drop_column('assets', 'database_dependencies')
    op.drop_column('assets', 'application_dependencies')
    op.drop_column('assets', 'server_dependencies')
    op.drop_column('assets', 'tech_debt_score')
    op.drop_column('assets', 'modernization_complexity')
    op.drop_column('assets', 'cloud_readiness_score')
    op.drop_column('assets', 'database_type')
    op.drop_column('assets', 'framework')
    op.drop_column('assets', 'programming_language')
    op.drop_column('assets', 'application_version')
    op.drop_column('assets', 'application_id')
    op.drop_column('assets', 'department')
    op.drop_column('assets', 'technical_owner')
    op.drop_column('assets', 'business_owner')
    op.drop_column('assets', 'hardware_type')
    op.drop_column('assets', 'intelligent_asset_type')
    op.drop_column('assets', 'asset_name')
    op.drop_column('assets', 'engagement_id')
    op.drop_column('assets', 'client_account_id') 