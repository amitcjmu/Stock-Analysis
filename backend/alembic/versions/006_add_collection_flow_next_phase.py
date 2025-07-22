"""add collection flow next phase column

Revision ID: 006_add_collection_flow_next_phase
Revises: 005_add_gap_analysis_and_questionnaire_tables
Create Date: 2025-01-20

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '006_add_collection_flow_next_phase'
down_revision = '005_add_gap_analysis_and_questionnaire_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add next_phase column to collection_flows table
    op.add_column('collection_flows', sa.Column('next_phase', sa.String(100), nullable=True))


def downgrade():
    # Remove next_phase column
    op.drop_column('collection_flows', 'next_phase')