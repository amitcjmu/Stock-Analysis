"""Add V3 API persistence tables

Revision ID: add_v3_persistence_001
Revises: c85140124625
Create Date: 2024-06-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'add_v3_persistence_001'
down_revision = 'c85140124625'
branch_labels = None
depends_on = None

def upgrade():
    """Create V3 tables"""
    
    # Create v3_data_imports table
    op.create_table(
        'v3_data_imports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer()),
        sa.Column('mime_type', sa.String()),
        sa.Column('source_system', sa.String()),
        sa.Column('status', sa.String(), nullable=False, default='pending'),
        sa.Column('total_records', sa.Integer(), default=0),
        sa.Column('processed_records', sa.Integer(), default=0),
        sa.Column('failed_records', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('error_message', sa.String()),
        sa.Column('error_details', sa.JSON())
    )
    
    # Create indexes for v3_data_imports
    op.create_index('idx_v3_imports_client_status', 'v3_data_imports', ['client_account_id', 'status'])
    op.create_index('idx_v3_imports_created', 'v3_data_imports', ['created_at'])
    
    # Create v3_discovery_flows table
    op.create_table(
        'v3_discovery_flows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_name', sa.String()),
        sa.Column('flow_type', sa.String(), default='unified_discovery'),
        sa.Column('data_import_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('v3_data_imports.id')),
        sa.Column('status', sa.String(), nullable=False, default='initializing'),
        sa.Column('current_phase', sa.String()),
        sa.Column('phases_completed', sa.JSON(), default=sa.text("'[]'")),
        sa.Column('progress_percentage', sa.Float(), default=0.0),
        sa.Column('flow_state', sa.JSON(), default=sa.text("'{}'")),
        sa.Column('crew_outputs', sa.JSON(), default=sa.text("'{}'")),
        sa.Column('field_mappings', sa.JSON()),
        sa.Column('discovered_assets', sa.JSON()),
        sa.Column('dependencies', sa.JSON()),
        sa.Column('tech_debt_analysis', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('error_message', sa.String()),
        sa.Column('error_phase', sa.String()),
        sa.Column('error_details', sa.JSON())
    )
    
    # Create indexes for v3_discovery_flows
    op.create_index('idx_v3_flows_client_status', 'v3_discovery_flows', ['client_account_id', 'status'])
    op.create_index('idx_v3_flows_import', 'v3_discovery_flows', ['data_import_id'])
    
    # Create v3_raw_import_records table
    op.create_table(
        'v3_raw_import_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('data_import_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('v3_data_imports.id'), nullable=False),
        sa.Column('record_index', sa.Integer(), nullable=False),
        sa.Column('raw_data', sa.JSON(), nullable=False),
        sa.Column('is_processed', sa.Boolean(), default=False),
        sa.Column('is_valid', sa.Boolean()),
        sa.Column('validation_errors', sa.JSON()),
        sa.Column('cleansed_data', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime())
    )
    
    # Create indexes for v3_raw_import_records
    op.create_index('idx_v3_records_import', 'v3_raw_import_records', ['data_import_id'])
    op.create_index('idx_v3_records_processed', 'v3_raw_import_records', ['is_processed'])
    
    # Create v3_field_mappings table
    op.create_table(
        'v3_field_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('data_import_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('v3_data_imports.id'), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_field', sa.String(), nullable=False),
        sa.Column('target_field', sa.String(), nullable=False),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('match_type', sa.String()),
        sa.Column('suggested_by', sa.String(), default='ai_agent'),
        sa.Column('status', sa.String(), nullable=False, default='suggested'),
        sa.Column('approved_by', sa.String()),
        sa.Column('approved_at', sa.DateTime()),
        sa.Column('transformation_rules', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now())
    )
    
    # Create indexes for v3_field_mappings
    op.create_index('idx_v3_mappings_import', 'v3_field_mappings', ['data_import_id'])
    op.create_index('idx_v3_mappings_source', 'v3_field_mappings', ['source_field'])
    op.create_index('idx_v3_mappings_status', 'v3_field_mappings', ['status'])

def downgrade():
    """Drop V3 tables"""
    op.drop_table('v3_field_mappings')
    op.drop_table('v3_raw_import_records')
    op.drop_table('v3_discovery_flows')
    op.drop_table('v3_data_imports')