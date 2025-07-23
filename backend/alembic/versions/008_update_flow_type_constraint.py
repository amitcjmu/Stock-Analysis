"""update flow type constraint to include collection

Revision ID: 008_update_flow_type_constraint
Revises: 007_add_missing_collection_flow_columns
Create Date: 2025-01-20

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '008_update_flow_type_constraint'
down_revision = '007_add_missing_collection_flow_columns'
branch_labels = None
depends_on = None


def upgrade():
    # Check if constraint exists first
    conn = op.get_bind()
    result = conn.execute(text("""
        SELECT COUNT(*) 
        FROM pg_constraint 
        WHERE conname = 'chk_valid_flow_type'
    """))
    constraint_exists = result.scalar() > 0
    
    # Drop the old constraint if it exists
    if constraint_exists:
        op.drop_constraint('chk_valid_flow_type', 'crewai_flow_state_extensions', type_='check')
    
    # Create new constraint with collection included
    op.create_check_constraint(
        'chk_valid_flow_type',
        'crewai_flow_state_extensions',
        "flow_type IN ('discovery', 'assessment', 'collection', 'planning', 'execution', 'modernize', 'finops', 'observability', 'decommission')"
    )


def downgrade():
    # Drop the new constraint
    op.drop_constraint('chk_valid_flow_type', 'crewai_flow_state_extensions', type_='check')
    
    # Recreate old constraint without collection
    op.create_check_constraint(
        'chk_valid_flow_type',
        'crewai_flow_state_extensions',
        "flow_type IN ('discovery', 'assessment', 'planning', 'execution', 'modernize', 'finops', 'observability', 'decommission')"
    )