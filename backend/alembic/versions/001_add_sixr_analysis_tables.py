"""Add 6R analysis tables

Revision ID: 001_add_sixr_analysis_tables
Revises: 
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_sixr_analysis_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    sixr_strategy_enum = postgresql.ENUM(
        'rehost', 'replatform', 'refactor', 'rearchitect', 'rewrite', 'replace', 'retire',
        name='sixrstrategy'
    )
    sixr_strategy_enum.create(op.get_bind())
    
    analysis_status_enum = postgresql.ENUM(
        'pending', 'in_progress', 'completed', 'failed', 'requires_input',
        name='analysisstatus'
    )
    analysis_status_enum.create(op.get_bind())
    
    question_type_enum = postgresql.ENUM(
        'text', 'select', 'multiselect', 'file_upload', 'boolean', 'numeric',
        name='questiontype'
    )
    question_type_enum.create(op.get_bind())
    
    # Create sixr_analyses table
    op.create_table(
        'sixr_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('migration_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', analysis_status_enum, nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('application_ids', sa.JSON(), nullable=True),
        sa.Column('application_data', sa.JSON(), nullable=True),
        sa.Column('current_iteration', sa.Integer(), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        sa.Column('estimated_completion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('final_recommendation', sixr_strategy_enum, nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('analysis_config', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['migration_id'], ['migrations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sixr_analyses_id'), 'sixr_analyses', ['id'], unique=False)
    op.create_index(op.f('ix_sixr_analyses_name'), 'sixr_analyses', ['name'], unique=False)
    
    # Create sixr_parameters table
    op.create_table(
        'sixr_parameters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('iteration_number', sa.Integer(), nullable=False),
        sa.Column('business_value', sa.Float(), nullable=False),
        sa.Column('technical_complexity', sa.Float(), nullable=False),
        sa.Column('migration_urgency', sa.Float(), nullable=False),
        sa.Column('compliance_requirements', sa.Float(), nullable=False),
        sa.Column('cost_sensitivity', sa.Float(), nullable=False),
        sa.Column('risk_tolerance', sa.Float(), nullable=False),
        sa.Column('innovation_priority', sa.Float(), nullable=False),
        sa.Column('application_type', sa.String(length=20), nullable=True),
        sa.Column('parameter_source', sa.String(length=50), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('parameter_notes', sa.Text(), nullable=True),
        sa.Column('validation_status', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['sixr_analyses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sixr_parameters_id'), 'sixr_parameters', ['id'], unique=False)
    
    # Create sixr_iterations table
    op.create_table(
        'sixr_iterations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('iteration_number', sa.Integer(), nullable=False),
        sa.Column('iteration_name', sa.String(length=255), nullable=True),
        sa.Column('iteration_reason', sa.Text(), nullable=True),
        sa.Column('stakeholder_feedback', sa.Text(), nullable=True),
        sa.Column('parameter_changes', sa.JSON(), nullable=True),
        sa.Column('question_responses', sa.JSON(), nullable=True),
        sa.Column('recommendation_data', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('analysis_duration', sa.Float(), nullable=True),
        sa.Column('agent_insights', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['sixr_analyses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sixr_iterations_id'), 'sixr_iterations', ['id'], unique=False)
    
    # Create sixr_recommendations table
    op.create_table(
        'sixr_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('iteration_number', sa.Integer(), nullable=False),
        sa.Column('recommended_strategy', sixr_strategy_enum, nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('strategy_scores', sa.JSON(), nullable=False),
        sa.Column('key_factors', sa.JSON(), nullable=True),
        sa.Column('assumptions', sa.JSON(), nullable=True),
        sa.Column('next_steps', sa.JSON(), nullable=True),
        sa.Column('estimated_effort', sa.String(length=50), nullable=True),
        sa.Column('estimated_timeline', sa.String(length=100), nullable=True),
        sa.Column('estimated_cost_impact', sa.String(length=50), nullable=True),
        sa.Column('risk_factors', sa.JSON(), nullable=True),
        sa.Column('mitigation_strategies', sa.JSON(), nullable=True),
        sa.Column('business_benefits', sa.JSON(), nullable=True),
        sa.Column('technical_benefits', sa.JSON(), nullable=True),
        sa.Column('validation_status', sa.String(length=20), nullable=True),
        sa.Column('validation_notes', sa.Text(), nullable=True),
        sa.Column('validated_by', sa.String(length=100), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ai_agent_insights', sa.JSON(), nullable=True),
        sa.Column('analysis_methodology', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['sixr_analyses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sixr_recommendations_id'), 'sixr_recommendations', ['id'], unique=False)
    
    # Create sixr_questions table
    op.create_table(
        'sixr_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.String(length=100), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', question_type_enum, nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('required', sa.Boolean(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('validation_rules', sa.JSON(), nullable=True),
        sa.Column('help_text', sa.Text(), nullable=True),
        sa.Column('depends_on', sa.String(length=100), nullable=True),
        sa.Column('show_conditions', sa.JSON(), nullable=True),
        sa.Column('skip_conditions', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=True),
        sa.Column('parent_question_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('question_id')
    )
    op.create_index(op.f('ix_sixr_questions_id'), 'sixr_questions', ['id'], unique=False)
    op.create_index(op.f('ix_sixr_questions_question_id'), 'sixr_questions', ['question_id'], unique=False)
    
    # Create sixr_question_responses table
    op.create_table(
        'sixr_question_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('iteration_number', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.String(length=100), nullable=False),
        sa.Column('response_value', sa.JSON(), nullable=True),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('response_time', sa.Float(), nullable=True),
        sa.Column('validation_status', sa.String(length=20), nullable=True),
        sa.Column('validation_errors', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['sixr_analyses.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['sixr_questions.question_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sixr_question_responses_id'), 'sixr_question_responses', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_sixr_question_responses_id'), table_name='sixr_question_responses')
    op.drop_table('sixr_question_responses')
    
    op.drop_index(op.f('ix_sixr_questions_question_id'), table_name='sixr_questions')
    op.drop_index(op.f('ix_sixr_questions_id'), table_name='sixr_questions')
    op.drop_table('sixr_questions')
    
    op.drop_index(op.f('ix_sixr_recommendations_id'), table_name='sixr_recommendations')
    op.drop_table('sixr_recommendations')
    
    op.drop_index(op.f('ix_sixr_iterations_id'), table_name='sixr_iterations')
    op.drop_table('sixr_iterations')
    
    op.drop_index(op.f('ix_sixr_parameters_id'), table_name='sixr_parameters')
    op.drop_table('sixr_parameters')
    
    op.drop_index(op.f('ix_sixr_analyses_name'), table_name='sixr_analyses')
    op.drop_index(op.f('ix_sixr_analyses_id'), table_name='sixr_analyses')
    op.drop_table('sixr_analyses')
    
    # Drop enum types
    sa.Enum(name='questiontype').drop(op.get_bind())
    sa.Enum(name='analysisstatus').drop(op.get_bind())
    sa.Enum(name='sixrstrategy').drop(op.get_bind()) 