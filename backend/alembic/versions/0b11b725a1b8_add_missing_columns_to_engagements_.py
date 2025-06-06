"""Add missing columns to engagements table for production

Revision ID: 0b11b725a1b8
Revises: 5d1d0ff2e410
Create Date: 2025-06-06 01:51:33.085324

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b11b725a1b8'
down_revision = '5d1d0ff2e410'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to engagements table that exist in the model but not in production
    # Use conditional logic to only add columns if they don't already exist
    
    from sqlalchemy import text
    bind = op.get_bind()
    
    # Check if migration_scope column exists
    result = bind.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'engagements' 
        AND column_name = 'migration_scope'
    """))
    
    if not result.fetchone():
        # Add migration_scope column only if it doesn't exist
        op.add_column('engagements', sa.Column('migration_scope', sa.JSON(), nullable=True))
        
        # Set default values for existing records
        op.execute(text("""
            UPDATE engagements 
            SET migration_scope = '{
                "target_clouds": [],
                "migration_strategies": [],
                "excluded_systems": [],
                "included_environments": [],
                "business_units": [],
                "geographic_scope": [],
                "timeline_constraints": {}
            }'::json
            WHERE migration_scope IS NULL
        """))
    
    # Check if team_preferences column exists
    result = bind.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'engagements' 
        AND column_name = 'team_preferences'
    """))
    
    if not result.fetchone():
        # Add team_preferences column only if it doesn't exist
        op.add_column('engagements', sa.Column('team_preferences', sa.JSON(), nullable=True))
        
        # Set default values for existing records
        op.execute(text("""
            UPDATE engagements 
            SET team_preferences = '{
                "stakeholders": [],
                "decision_makers": [],
                "technical_leads": [],
                "communication_style": "formal",
                "reporting_frequency": "weekly",
                "preferred_meeting_times": [],
                "escalation_contacts": [],
                "project_methodology": "agile"
            }'::json
            WHERE team_preferences IS NULL
        """))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('engagements', 'team_preferences')
    op.drop_column('engagements', 'migration_scope') 