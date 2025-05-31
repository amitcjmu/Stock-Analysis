"""Add learning system tables

Revision ID: learning_system_001
Revises: learning_fields_001
Create Date: 2025-01-27 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'learning_system_001'
down_revision = 'learning_fields_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create custom_target_fields table
    op.create_table('custom_target_fields',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_name', sa.String(length=255), nullable=False),
        sa.Column('field_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.Column('is_searchable', sa.Boolean(), nullable=True),
        sa.Column('is_critical', sa.Boolean(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('validation_schema', sa.JSON(), nullable=True),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('allowed_values', sa.JSON(), nullable=True),
        sa.Column('common_source_patterns', sa.JSON(), nullable=True),
        sa.Column('sample_values', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('field_name')
    )
    op.create_index(op.f('ix_custom_target_fields_field_name'), 'custom_target_fields', ['field_name'], unique=False)
    op.create_index(op.f('ix_custom_target_fields_id'), 'custom_target_fields', ['id'], unique=False)

    # Create mapping_learning_patterns table
    op.create_table('mapping_learning_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_field_pattern', sa.String(length=255), nullable=False),
        sa.Column('content_pattern', sa.JSON(), nullable=True),
        sa.Column('target_field', sa.String(length=255), nullable=False),
        sa.Column('pattern_confidence', sa.Float(), nullable=True),
        sa.Column('success_count', sa.Integer(), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=True),
        sa.Column('learned_from_mapping_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('matching_rules', sa.JSON(), nullable=True),
        sa.Column('transformation_hints', sa.JSON(), nullable=True),
        sa.Column('quality_checks', sa.JSON(), nullable=True),
        sa.Column('times_applied', sa.Integer(), nullable=True),
        sa.Column('last_applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['learned_from_mapping_id'], ['import_field_mappings.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mapping_learning_patterns_id'), 'mapping_learning_patterns', ['id'], unique=False)
    op.create_index(op.f('ix_mapping_learning_patterns_source_field_pattern'), 'mapping_learning_patterns', ['source_field_pattern'], unique=False)
    op.create_index(op.f('ix_mapping_learning_patterns_target_field'), 'mapping_learning_patterns', ['target_field'], unique=False)


def downgrade() -> None:
    # Drop learning tables
    op.drop_index(op.f('ix_mapping_learning_patterns_target_field'), table_name='mapping_learning_patterns')
    op.drop_index(op.f('ix_mapping_learning_patterns_source_field_pattern'), table_name='mapping_learning_patterns')
    op.drop_index(op.f('ix_mapping_learning_patterns_id'), table_name='mapping_learning_patterns')
    op.drop_table('mapping_learning_patterns')
    
    op.drop_index(op.f('ix_custom_target_fields_id'), table_name='custom_target_fields')
    op.drop_index(op.f('ix_custom_target_fields_field_name'), table_name='custom_target_fields')
    op.drop_table('custom_target_fields') 