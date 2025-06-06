"""Add missing columns to client_accounts table for production

Revision ID: fa1e81c600b0
Revises: 0b11b725a1b8
Create Date: 2025-06-06 01:58:26.267816

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa1e81c600b0'
down_revision = '0b11b725a1b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to client_accounts table that exist in the model but not in production
    # Use conditional logic to only add columns if they don't already exist
    
    from sqlalchemy import text
    bind = op.get_bind()
    
    # List of columns to check and add if missing
    columns_to_add = [
        ('headquarters_location', sa.String(255)),
        ('primary_contact_name', sa.String(255)),
        ('primary_contact_email', sa.String(255)),
        ('primary_contact_phone', sa.String(50)),
        ('subscription_tier', sa.String(50)),
        ('billing_contact_email', sa.String(255)),
        ('settings', sa.JSON()),
        ('branding', sa.JSON()),
        ('business_objectives', sa.JSON()),
        ('it_guidelines', sa.JSON()),
        ('decision_criteria', sa.JSON()),
        ('agent_preferences', sa.JSON()),
    ]
    
    for column_name, column_type in columns_to_add:
        # Check if column exists
        result = bind.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'client_accounts' 
            AND column_name = '{column_name}'
        """))
        
        if not result.fetchone():
            # Add column only if it doesn't exist
            op.add_column('client_accounts', sa.Column(column_name, column_type, nullable=True))
    
    # Set default values for JSON columns that were just added
    json_defaults = {
        'settings': '{}',
        'branding': '{}',
        'business_objectives': '''{
            "primary_goals": [],
            "timeframe": "",
            "success_metrics": [],
            "budget_constraints": "",
            "compliance_requirements": []
        }''',
        'it_guidelines': '''{
            "architecture_patterns": [],
            "security_requirements": [],
            "compliance_standards": [],
            "technology_preferences": [],
            "cloud_strategy": "",
            "data_governance": {}
        }''',
        'decision_criteria': '''{
            "risk_tolerance": "medium",
            "cost_sensitivity": "medium",
            "innovation_appetite": "moderate",
            "timeline_pressure": "medium",
            "quality_vs_speed": "balanced",
            "technical_debt_tolerance": "low"
        }''',
        'agent_preferences': '''{
            "confidence_thresholds": {
                "field_mapping": 0.8,
                "data_classification": 0.75,
                "risk_assessment": 0.85,
                "migration_strategy": 0.9
            },
            "learning_preferences": ["conservative", "accuracy_focused"],
            "custom_prompts": {},
            "notification_preferences": {
                "confidence_alerts": true,
                "learning_updates": false,
                "error_notifications": true
            }
        }'''
    }
    
    # Update existing records with default values
    for column_name, default_value in json_defaults.items():
        op.execute(text(f"""
            UPDATE client_accounts 
            SET {column_name} = '{default_value}'::json
            WHERE {column_name} IS NULL
        """))
    
    # Set default values for string columns
    string_defaults = {
        'subscription_tier': 'standard'
    }
    
    for column_name, default_value in string_defaults.items():
        op.execute(text(f"""
            UPDATE client_accounts 
            SET {column_name} = '{default_value}'
            WHERE {column_name} IS NULL
        """))


def downgrade() -> None:
    # Remove the added columns in reverse order
    columns_to_remove = [
        'agent_preferences',
        'decision_criteria', 
        'it_guidelines',
        'business_objectives',
        'branding',
        'settings',
        'billing_contact_email',
        'subscription_tier',
        'primary_contact_phone',
        'primary_contact_email',
        'primary_contact_name',
        'headquarters_location'
    ]
    
    for column_name in columns_to_remove:
        op.drop_column('client_accounts', column_name) 