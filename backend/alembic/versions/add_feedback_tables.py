"""Add feedback tables for database storage

Revision ID: add_feedback_tables_001
Revises: learning_fields_001
Create Date: 2025-05-31 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_feedback_tables_001'
down_revision = 'learning_fields_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create feedback table
    op.create_table('feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_type', sa.String(length=50), nullable=False),
        sa.Column('page', sa.String(length=255), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('breadcrumb', sa.String(length=500), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('original_analysis', sa.JSON(), nullable=True),
        sa.Column('user_corrections', sa.JSON(), nullable=True),
        sa.Column('asset_type_override', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('user_timestamp', sa.String(length=50), nullable=True),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('learning_patterns_extracted', sa.JSON(), nullable=True),
        sa.Column('confidence_impact', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_feedback_type'), 'feedback', ['feedback_type'], unique=False)
    op.create_index(op.f('ix_feedback_id'), 'feedback', ['id'], unique=False)
    op.create_index(op.f('ix_feedback_page'), 'feedback', ['page'], unique=False)

    # Create feedback_summaries table
    op.create_table('feedback_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_type', sa.String(length=50), nullable=False),
        sa.Column('page', sa.String(length=255), nullable=True),
        sa.Column('time_period', sa.String(length=20), nullable=True),
        sa.Column('total_feedback', sa.Integer(), nullable=True),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('status_counts', sa.JSON(), nullable=True),
        sa.Column('rating_distribution', sa.JSON(), nullable=True),
        sa.Column('category_counts', sa.JSON(), nullable=True),
        sa.Column('feedback_trend', sa.JSON(), nullable=True),
        sa.Column('rating_trend', sa.JSON(), nullable=True),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_calculated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('calculation_duration_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['client_account_id'], ['client_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_summaries_feedback_type'), 'feedback_summaries', ['feedback_type'], unique=False)
    op.create_index(op.f('ix_feedback_summaries_id'), 'feedback_summaries', ['id'], unique=False)
    op.create_index(op.f('ix_feedback_summaries_page'), 'feedback_summaries', ['page'], unique=False)


def downgrade() -> None:
    # Drop feedback tables
    op.drop_index(op.f('ix_feedback_summaries_page'), table_name='feedback_summaries')
    op.drop_index(op.f('ix_feedback_summaries_id'), table_name='feedback_summaries')
    op.drop_index(op.f('ix_feedback_summaries_feedback_type'), table_name='feedback_summaries')
    op.drop_table('feedback_summaries')
    
    op.drop_index(op.f('ix_feedback_page'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_id'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_feedback_type'), table_name='feedback')
    op.drop_table('feedback') 