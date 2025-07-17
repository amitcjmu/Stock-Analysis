"""add_assessment_flow_tables

Revision ID: 003_add_assessment_flow_tables
Revises: 002_add_raw_import_records_id
Create Date: 2025-01-17 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_assessment_flow_tables'
down_revision = '002_add_raw_import_records_id'
branch_labels = None
depends_on = None


def upgrade():
    # Create assessment_flows table
    op.create_table('assessment_flows',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('client_account_id', sa.UUID(), nullable=False),
        sa.Column('engagement_id', sa.UUID(), nullable=False),
        sa.Column('flow_name', sa.String(length=255), nullable=False),
        sa.Column('flow_status', sa.String(length=50), nullable=False),
        sa.Column('flow_configuration', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create engagement_architecture_standards table
    op.create_table('engagement_architecture_standards',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('engagement_id', sa.UUID(), nullable=False),
        sa.Column('standard_name', sa.String(length=255), nullable=False),
        sa.Column('standard_description', sa.Text(), nullable=True),
        sa.Column('standard_config', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create application_architecture_overrides table
    op.create_table('application_architecture_overrides',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('engagement_id', sa.UUID(), nullable=False),
        sa.Column('application_name', sa.String(length=255), nullable=False),
        sa.Column('override_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create application_components table
    op.create_table('application_components',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('engagement_id', sa.UUID(), nullable=False),
        sa.Column('component_name', sa.String(length=255), nullable=False),
        sa.Column('component_type', sa.String(length=100), nullable=False),
        sa.Column('component_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create tech_debt_analysis table
    op.create_table('tech_debt_analysis',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('engagement_id', sa.UUID(), nullable=False),
        sa.Column('analysis_type', sa.String(length=100), nullable=False),
        sa.Column('analysis_results', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create component_treatments table
    op.create_table('component_treatments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('component_id', sa.UUID(), nullable=False),
        sa.Column('treatment_type', sa.String(length=100), nullable=False),
        sa.Column('treatment_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['component_id'], ['application_components.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create sixr_decisions table
    op.create_table('sixr_decisions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('engagement_id', sa.UUID(), nullable=False),
        sa.Column('decision_type', sa.String(length=100), nullable=False),
        sa.Column('decision_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create assessment_learning_feedback table
    op.create_table('assessment_learning_feedback',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('engagement_id', sa.UUID(), nullable=False),
        sa.Column('feedback_type', sa.String(length=100), nullable=False),
        sa.Column('feedback_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('assessment_learning_feedback')
    op.drop_table('sixr_decisions')
    op.drop_table('component_treatments')
    op.drop_table('tech_debt_analysis')
    op.drop_table('application_components')
    op.drop_table('application_architecture_overrides')
    op.drop_table('engagement_architecture_standards')
    op.drop_table('assessment_flows')