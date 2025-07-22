"""Add collection_flow_id to adaptive_questionnaires table

Revision ID: 009_add_collection_flow_id_to_questionnaires
Revises: 008_update_flow_type_constraint
Create Date: 2025-07-20

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '009_add_collection_flow_id_to_questionnaires'
down_revision = '008_update_flow_type_constraint'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add collection_flow_id column to adaptive_questionnaires table
    op.add_column('adaptive_questionnaires', 
        sa.Column('collection_flow_id', sa.UUID(), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        op.f('fk_adaptive_questionnaires_collection_flow_id_collection_flows'),
        'adaptive_questionnaires', 
        'collection_flows',
        ['collection_flow_id'], 
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create index for better query performance
    op.create_index(
        op.f('ix_adaptive_questionnaires_collection_flow_id'), 
        'adaptive_questionnaires', 
        ['collection_flow_id'], 
        unique=False
    )
    
    # Add new columns for better questionnaire management
    op.add_column('adaptive_questionnaires',
        sa.Column('title', sa.VARCHAR(length=255), nullable=True)
    )
    
    op.add_column('adaptive_questionnaires',
        sa.Column('description', sa.TEXT(), nullable=True)
    )
    
    op.add_column('adaptive_questionnaires',
        sa.Column('target_gaps', postgresql.JSONB(astext_type=sa.Text()), 
                  server_default=sa.text("'[]'::jsonb"), nullable=False)
    )
    
    op.add_column('adaptive_questionnaires',
        sa.Column('questions', postgresql.JSONB(astext_type=sa.Text()), 
                  server_default=sa.text("'[]'::jsonb"), nullable=False)
    )
    
    op.add_column('adaptive_questionnaires',
        sa.Column('completion_status', sa.VARCHAR(length=50), 
                  server_default='pending', nullable=False)
    )
    
    op.add_column('adaptive_questionnaires',
        sa.Column('responses_collected', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=True)
    )
    
    op.add_column('adaptive_questionnaires',
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True)
    )


def downgrade() -> None:
    # Drop the new columns in reverse order
    op.drop_column('adaptive_questionnaires', 'completed_at')
    op.drop_column('adaptive_questionnaires', 'responses_collected')
    op.drop_column('adaptive_questionnaires', 'completion_status')
    op.drop_column('adaptive_questionnaires', 'questions')
    op.drop_column('adaptive_questionnaires', 'target_gaps')
    op.drop_column('adaptive_questionnaires', 'description')
    op.drop_column('adaptive_questionnaires', 'title')
    
    # Drop index
    op.drop_index(op.f('ix_adaptive_questionnaires_collection_flow_id'), 
                  table_name='adaptive_questionnaires')
    
    # Drop foreign key constraint
    op.drop_constraint(
        op.f('fk_adaptive_questionnaires_collection_flow_id_collection_flows'), 
        'adaptive_questionnaires', 
        type_='foreignkey'
    )
    
    # Drop column
    op.drop_column('adaptive_questionnaires', 'collection_flow_id')