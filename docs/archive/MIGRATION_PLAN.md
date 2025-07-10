# Complete Migration Redesign Plan

## Problem
The current migrations were created with simplified schemas that don't match the models, leading to multiple patch migrations. This is not suitable for fresh environment deployments.

## Solution
Create a clean, logical sequence of migrations that include ALL fields from the start.

## New Migration Sequence

### 001_core_tables.py
- client_accounts (with ALL fields including agent_preferences)
- users (complete)
- engagements (complete)
- user_account_associations (complete)

### 002_rbac_tables.py  
- user_profiles (complete RBAC profile)
- user_roles (complete with scope fields)
- client_access (complete with user_profile_id FK)
- engagement_access (complete)
- access_audit_log (complete)
- enhanced_user_profiles
- role_permissions
- soft_deleted_items

### 003_discovery_flow_tables.py
- discovery_flows (with ALL fields including learning_scope, etc.)
- crewai_flow_state_extensions (complete)
- data_import_sessions (complete)

### 004_asset_tables.py
- assets (with ALL 90+ fields from the model)
- asset_dependencies (correct field names)
- workflow_progress
- tags, asset_tags

### 005_data_import_tables.py
- data_imports (complete)
- raw_import_records (complete)
- import_field_mappings (complete)
- import_processing_steps (complete)

### 006_analytics_tables.py
- assessments, sixr_analysis, cmdb_sixr_analyses
- migrations, migration_waves, wave_plans
- agent_questions, agent_insights, data_items
- feedback, flow_deletion_audit

### 007_observability_tables.py
- llm_usage_log, llm_usage_summary
- security_audit_log, role_change_approval

This approach:
1. Groups related tables logically
2. Handles dependencies correctly
3. Includes ALL fields from models from the start
4. No patch migrations needed
5. Clean for fresh deployments

## Next Steps
1. Remove existing migrations 002-008
2. Create the new sequence
3. Test on fresh database
4. Verify all models work