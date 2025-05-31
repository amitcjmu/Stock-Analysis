"""Add learning fields to field mappings

Revision ID: learning_fields_001
Revises: f802528ca6c1
Create Date: 2025-01-27 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'learning_fields_001'
down_revision = 'f802528ca6c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new fields to import_field_mappings table
    op.add_column('import_field_mappings', sa.Column('is_user_defined', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('import_field_mappings', sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'))
    op.add_column('import_field_mappings', sa.Column('user_feedback', sa.Text(), nullable=True))
    op.add_column('import_field_mappings', sa.Column('original_ai_suggestion', sa.String(length=255), nullable=True))
    op.add_column('import_field_mappings', sa.Column('correction_reason', sa.Text(), nullable=True))
    op.add_column('import_field_mappings', sa.Column('validation_rules', sa.JSON(), nullable=True))
    
    # Rename transformation_rule to transformation_logic
    op.alter_column('import_field_mappings', 'transformation_rule', new_column_name='transformation_logic')


def downgrade() -> None:
    # Remove added columns
    op.drop_column('import_field_mappings', 'validation_rules')
    op.drop_column('import_field_mappings', 'correction_reason')
    op.drop_column('import_field_mappings', 'original_ai_suggestion')
    op.drop_column('import_field_mappings', 'user_feedback')
    op.drop_column('import_field_mappings', 'status')
    op.drop_column('import_field_mappings', 'is_user_defined')
    
    # Rename back
    op.alter_column('import_field_mappings', 'transformation_logic', new_column_name='transformation_rule') 