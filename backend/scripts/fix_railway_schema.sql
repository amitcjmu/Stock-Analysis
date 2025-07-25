-- Direct SQL fix for Railway production database missing columns
-- This script adds missing columns to client_accounts table if they don't exist

-- Add missing columns to client_accounts table
ALTER TABLE client_accounts ADD COLUMN IF NOT EXISTS headquarters_location VARCHAR(255);
ALTER TABLE client_accounts ADD COLUMN IF NOT EXISTS primary_contact_name VARCHAR(255);
ALTER TABLE client_accounts ADD COLUMN IF NOT EXISTS primary_contact_email VARCHAR(255);
ALTER TABLE client_accounts ADD COLUMN IF NOT EXISTS primary_contact_phone VARCHAR(50);
ALTER TABLE client_accounts ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50);
ALTER TABLE client_accounts ADD COLUMN IF NOT EXISTS billing_contact_email VARCHAR(255);
ALTER TABLE client_accounts ADD COLUMN IF NOT EXISTS settings JSON;
ALTER TABLE client_accounts ADD COLUMN IF NOT EXISTS branding JSON;
ALTER TABLE client_accounts ADD COLUMN IF NOT EXISTS business_objectives JSON;
ALTER TABLE client_accounts ADD COLUMN IF NOT EXISTS it_guidelines JSON;
ALTER TABLE client_accounts ADD COLUMN IF NOT EXISTS decision_criteria JSON;
ALTER TABLE client_accounts ADD COLUMN IF NOT EXISTS agent_preferences JSON;

-- Add missing columns to engagements table
ALTER TABLE engagements ADD COLUMN IF NOT EXISTS migration_scope JSON;
ALTER TABLE engagements ADD COLUMN IF NOT EXISTS team_preferences JSON;

-- Set default values for existing records
UPDATE client_accounts SET subscription_tier = 'standard' WHERE subscription_tier IS NULL;
UPDATE client_accounts SET settings = '{}'::json WHERE settings IS NULL;
UPDATE client_accounts SET branding = '{}'::json WHERE branding IS NULL;
UPDATE client_accounts SET business_objectives = '{
    "primary_goals": [],
    "timeframe": "",
    "success_metrics": [],
    "budget_constraints": "",
    "compliance_requirements": []
}'::json WHERE business_objectives IS NULL;
UPDATE client_accounts SET it_guidelines = '{
    "architecture_patterns": [],
    "security_requirements": [],
    "compliance_standards": [],
    "technology_preferences": [],
    "cloud_strategy": "",
    "data_governance": {}
}'::json WHERE it_guidelines IS NULL;
UPDATE client_accounts SET decision_criteria = '{
    "risk_tolerance": "medium",
    "cost_sensitivity": "medium",
    "innovation_appetite": "moderate",
    "timeline_pressure": "medium",
    "quality_vs_speed": "balanced",
    "technical_debt_tolerance": "low"
}'::json WHERE decision_criteria IS NULL;
UPDATE client_accounts SET agent_preferences = '{
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
}'::json WHERE agent_preferences IS NULL;

UPDATE engagements SET migration_scope = '{
    "target_clouds": [],
    "migration_strategies": [],
    "excluded_systems": [],
    "included_environments": [],
    "business_units": [],
    "geographic_scope": [],
    "timeline_constraints": {}
}'::json WHERE migration_scope IS NULL;

UPDATE engagements SET team_preferences = '{
    "stakeholders": [],
    "decision_makers": [],
    "technical_leads": [],
    "communication_style": "formal",
    "reporting_frequency": "weekly",
    "preferred_meeting_times": [],
    "escalation_contacts": [],
    "project_methodology": "agile"
}'::json WHERE team_preferences IS NULL;
