"""fix_asset_schema_comprehensive

Revision ID: 83c1ba41e213
Revises: 5992adf19317
Create Date: 2025-05-31 18:37:49.982831

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '83c1ba41e213'
down_revision = '5992adf19317'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to assets table that our model expects
    # Only add columns that don't exist yet
    
    # Check current columns first to avoid conflicts
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('assets')]
    
    # Add missing identity and naming columns
    if 'asset_name' not in existing_columns:
        op.add_column('assets', sa.Column('asset_name', sa.String(255), nullable=True))
    
    if 'intelligent_asset_type' not in existing_columns:
        op.add_column('assets', sa.Column('intelligent_asset_type', sa.String(100), nullable=True))
    
    # Add missing infrastructure columns
    if 'hardware_type' not in existing_columns:
        op.add_column('assets', sa.Column('hardware_type', sa.String(100), nullable=True))
    
    # Add missing business context columns
    if 'business_owner' not in existing_columns:
        op.add_column('assets', sa.Column('business_owner', sa.String(100), nullable=True))
    
    if 'technical_owner' not in existing_columns:
        op.add_column('assets', sa.Column('technical_owner', sa.String(100), nullable=True))
    
    if 'department' not in existing_columns:
        op.add_column('assets', sa.Column('department', sa.String(100), nullable=True))
    
    # Add missing application context columns
    if 'application_id' not in existing_columns:
        op.add_column('assets', sa.Column('application_id', sa.String(100), nullable=True))
    
    if 'application_version' not in existing_columns:
        op.add_column('assets', sa.Column('application_version', sa.String(50), nullable=True))
    
    if 'programming_language' not in existing_columns:
        op.add_column('assets', sa.Column('programming_language', sa.String(100), nullable=True))
    
    if 'framework' not in existing_columns:
        op.add_column('assets', sa.Column('framework', sa.String(100), nullable=True))
    
    if 'database_type' not in existing_columns:
        op.add_column('assets', sa.Column('database_type', sa.String(100), nullable=True))
    
    # Add missing cloud readiness columns
    if 'cloud_readiness_score' not in existing_columns:
        op.add_column('assets', sa.Column('cloud_readiness_score', sa.Float(), nullable=True))
    
    if 'modernization_complexity' not in existing_columns:
        op.add_column('assets', sa.Column('modernization_complexity', sa.String(20), nullable=True))
    
    if 'tech_debt_score' not in existing_columns:
        op.add_column('assets', sa.Column('tech_debt_score', sa.Float(), nullable=True))
    
    # Add missing cost analysis columns
    if 'estimated_monthly_cost' not in existing_columns:
        op.add_column('assets', sa.Column('estimated_monthly_cost', sa.Float(), nullable=True))
    
    if 'license_cost' not in existing_columns:
        op.add_column('assets', sa.Column('license_cost', sa.Float(), nullable=True))
    
    if 'support_cost' not in existing_columns:
        op.add_column('assets', sa.Column('support_cost', sa.Float(), nullable=True))
    
    # Add missing security columns
    if 'security_classification' not in existing_columns:
        op.add_column('assets', sa.Column('security_classification', sa.String(50), nullable=True))
    
    if 'vulnerability_score' not in existing_columns:
        op.add_column('assets', sa.Column('vulnerability_score', sa.Float(), nullable=True))
    
    # Add missing 6R strategy columns
    if 'sixr_ready' not in existing_columns:
        op.add_column('assets', sa.Column('sixr_ready', sa.String(20), nullable=True))
    
    if 'estimated_migration_effort' not in existing_columns:
        op.add_column('assets', sa.Column('estimated_migration_effort', sa.String(20), nullable=True))
    
    if 'recommended_6r_strategy' not in existing_columns:
        op.add_column('assets', sa.Column('recommended_6r_strategy', sa.String(20), nullable=True))
    
    if 'strategy_confidence' not in existing_columns:
        op.add_column('assets', sa.Column('strategy_confidence', sa.Float(), nullable=True))
    
    if 'strategy_rationale' not in existing_columns:
        op.add_column('assets', sa.Column('strategy_rationale', sa.Text(), nullable=True))
    
    # Add missing AI analysis columns
    if 'ai_confidence_score' not in existing_columns:
        op.add_column('assets', sa.Column('ai_confidence_score', sa.Float(), nullable=True))
    
    if 'last_ai_analysis' not in existing_columns:
        op.add_column('assets', sa.Column('last_ai_analysis', sa.DateTime(timezone=True), nullable=True))
    
    # Add missing import tracking columns
    if 'source_file' not in existing_columns:
        op.add_column('assets', sa.Column('source_file', sa.String(255), nullable=True))
    
    if 'import_batch_id' not in existing_columns:
        op.add_column('assets', sa.Column('import_batch_id', sa.String(100), nullable=True))
    
    if 'created_by' not in existing_columns:
        op.add_column('assets', sa.Column('created_by', sa.String(100), nullable=True))
    
    if 'updated_by' not in existing_columns:
        op.add_column('assets', sa.Column('updated_by', sa.String(100), nullable=True))
    
    print("✅ Successfully added missing asset inventory columns")


def downgrade() -> None:
    # Remove added columns
    columns_to_remove = [
        'asset_name', 'intelligent_asset_type', 'hardware_type',
        'business_owner', 'technical_owner', 'department',
        'application_id', 'application_version', 'programming_language', 'framework', 'database_type',
        'cloud_readiness_score', 'modernization_complexity', 'tech_debt_score',
        'estimated_monthly_cost', 'license_cost', 'support_cost',
        'security_classification', 'vulnerability_score',
        'sixr_ready', 'estimated_migration_effort', 'recommended_6r_strategy', 'strategy_confidence', 'strategy_rationale',
        'ai_confidence_score', 'last_ai_analysis',
        'source_file', 'import_batch_id', 'created_by', 'updated_by'
    ]
    
    for column_name in columns_to_remove:
        try:
            op.drop_column('assets', column_name)
        except:
            # Ignore if column doesn't exist
            pass 