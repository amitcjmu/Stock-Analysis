"""Add Gap Analysis and Adaptive Questionnaire tables for ADCS

Revision ID: 005_add_gap_analysis_and_questionnaire_tables
Revises: 004_add_platform_credentials_tables
Create Date: 2025-07-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '005_add_gap_analysis_and_questionnaire_tables'
down_revision = '004_add_platform_credentials_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create collection_gap_analysis table
    op.create_table('collection_gap_analysis',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('client_account_id', sa.UUID(), nullable=False),
        sa.Column('engagement_id', sa.UUID(), nullable=False),
        sa.Column('collection_flow_id', sa.UUID(), nullable=False),
        sa.Column('total_fields_required', sa.INTEGER(), server_default=sa.text('0'), nullable=False),
        sa.Column('fields_collected', sa.INTEGER(), server_default=sa.text('0'), nullable=False),
        sa.Column('fields_missing', sa.INTEGER(), server_default=sa.text('0'), nullable=False),
        sa.Column('completeness_percentage', sa.DOUBLE_PRECISION(precision=53), server_default=sa.text('0.0'), nullable=False),
        sa.Column('data_quality_score', sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column('confidence_level', sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column('automation_coverage', sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column('critical_gaps', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('optional_gaps', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('gap_categories', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('recommended_actions', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('questionnaire_requirements', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('analyzed_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], name=op.f('fk_collection_gap_analysis_client_account_id_client_accounts'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], name=op.f('fk_collection_gap_analysis_engagement_id_engagements'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['collection_flow_id'], ['collection_flows.id'], name=op.f('fk_collection_gap_analysis_collection_flow_id_collection_flows'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_collection_gap_analysis'))
    )
    
    # Create indexes for collection_gap_analysis
    op.create_index(op.f('ix_collection_gap_analysis_id'), 'collection_gap_analysis', ['id'], unique=False)
    op.create_index(op.f('ix_collection_gap_analysis_client_account_id'), 'collection_gap_analysis', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_collection_gap_analysis_engagement_id'), 'collection_gap_analysis', ['engagement_id'], unique=False)
    op.create_index(op.f('ix_collection_gap_analysis_collection_flow_id'), 'collection_gap_analysis', ['collection_flow_id'], unique=False)
    
    # Create adaptive_questionnaires table
    op.create_table('adaptive_questionnaires',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('client_account_id', sa.UUID(), nullable=False),
        sa.Column('engagement_id', sa.UUID(), nullable=False),
        sa.Column('template_name', sa.VARCHAR(length=255), nullable=False),
        sa.Column('template_type', sa.VARCHAR(length=100), nullable=False),
        sa.Column('version', sa.VARCHAR(length=20), server_default='1.0', nullable=False),
        sa.Column('applicable_tiers', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('question_set', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('question_count', sa.INTEGER(), server_default=sa.text('0'), nullable=False),
        sa.Column('estimated_completion_time', sa.INTEGER(), nullable=True),
        sa.Column('gap_categories', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('platform_types', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('data_domains', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('scoring_rules', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('validation_rules', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('usage_count', sa.INTEGER(), server_default=sa.text('0'), nullable=False),
        sa.Column('success_rate', sa.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_template', sa.BOOLEAN(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], name=op.f('fk_adaptive_questionnaires_client_account_id_client_accounts'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], name=op.f('fk_adaptive_questionnaires_engagement_id_engagements'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_adaptive_questionnaires'))
    )
    
    # Create indexes for adaptive_questionnaires
    op.create_index(op.f('ix_adaptive_questionnaires_id'), 'adaptive_questionnaires', ['id'], unique=False)
    op.create_index(op.f('ix_adaptive_questionnaires_client_account_id'), 'adaptive_questionnaires', ['client_account_id'], unique=False)
    op.create_index(op.f('ix_adaptive_questionnaires_engagement_id'), 'adaptive_questionnaires', ['engagement_id'], unique=False)
    op.create_index(op.f('ix_adaptive_questionnaires_template_type'), 'adaptive_questionnaires', ['template_type'], unique=False)


def downgrade() -> None:
    # Drop adaptive_questionnaires indexes and table
    op.drop_index(op.f('ix_adaptive_questionnaires_template_type'), table_name='adaptive_questionnaires')
    op.drop_index(op.f('ix_adaptive_questionnaires_engagement_id'), table_name='adaptive_questionnaires')
    op.drop_index(op.f('ix_adaptive_questionnaires_client_account_id'), table_name='adaptive_questionnaires')
    op.drop_index(op.f('ix_adaptive_questionnaires_id'), table_name='adaptive_questionnaires')
    op.drop_table('adaptive_questionnaires')
    
    # Drop collection_gap_analysis indexes and table
    op.drop_index(op.f('ix_collection_gap_analysis_collection_flow_id'), table_name='collection_gap_analysis')
    op.drop_index(op.f('ix_collection_gap_analysis_engagement_id'), table_name='collection_gap_analysis')
    op.drop_index(op.f('ix_collection_gap_analysis_client_account_id'), table_name='collection_gap_analysis')
    op.drop_index(op.f('ix_collection_gap_analysis_id'), table_name='collection_gap_analysis')
    op.drop_table('collection_gap_analysis')