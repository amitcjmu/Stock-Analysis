#!/usr/bin/env python3

# Get model tables
import subprocess
import re

# Get tables from models  
model_tables_raw = subprocess.run(['grep', '-h', '__tablename__', 'app/models/*.py'], capture_output=True, text=True, shell=True).stdout
model_tables = []
for line in model_tables_raw.split('\n'):
    if '__tablename__ =' in line:
        match = re.search(r'__tablename__ = ["\']([^"\']+)["\']', line)
        if match:
            model_tables.append(match.group(1))

model_tables = sorted(set(model_tables))

# Get tables from database
db_tables_raw = """access_audit_log
alembic_version
assessments
asset_dependencies
asset_embeddings
asset_tags
assets
client_access
client_accounts
cmdb_sixr_analyses
crewai_flow_state_extensions
custom_target_fields
data_import_sessions
data_imports
discovery_flows
engagement_access
engagements
enhanced_access_audit_log
enhanced_user_profiles
feedback
feedback_summaries
flow_deletion_audit
import_field_mappings
import_processing_steps
llm_model_pricing
llm_usage_logs
llm_usage_summary
migration_logs
migration_waves
migrations
raw_import_records
role_change_approvals
role_permissions
security_audit_logs
sixr_analyses
sixr_analysis_parameters
sixr_iterations
sixr_parameters
sixr_question_responses
sixr_questions
sixr_recommendations
soft_deleted_items
tags
user_account_associations
user_profiles
user_roles
users
wave_plans
workflow_progress"""

db_tables = sorted([t.strip() for t in db_tables_raw.split('\n') if t.strip()])

print(f"Model tables: {len(model_tables)}")
print(f"Database tables: {len(db_tables)} (including alembic_version)")
print(f"Database tables (excluding alembic): {len(db_tables) - 1}")

print("\n=== TABLES IN DATABASE BUT NOT IN MODELS ===")
for table in db_tables:
    if table not in model_tables and table != 'alembic_version':
        print(f"❌ {table}")

print("\n=== TABLES IN MODELS BUT NOT IN DATABASE ===")  
for table in model_tables:
    if table not in db_tables:
        print(f"❌ {table}")

print("\n=== COMMON TABLES ===")
common = set(model_tables) & set(db_tables)
print(f"✅ {len(common)} tables match")

# Check if the difference is explained by missing models
print(f"\nAnalysis:")
print(f"Models define: {len(model_tables)} tables")
print(f"Database has: {len(db_tables) - 1} tables (excluding alembic_version)")
print(f"Difference: {len(db_tables) - 1 - len(model_tables)} extra tables in database")