# Alembic Migration Analysis Report
==================================================

## Summary
- Total migrations: 58
- Numbered migrations: 43
- Hash-named migrations: 12
- Missing proper downgrade: 20

## Hash-Named Migrations (Need Renumbering)
- 2ae8940123e6_add_analysis_queue_tables.py (revision: 2ae8940123e6)
- 51470c6d6288_merge_collection_apps_with_timestamp_fix.py (revision: 51470c6d6288)
- 595ea1f47121_add_auto_generated_uuid_to_raw_import_.py (revision: 595ea1f47121)
- 7cc356fcc04a_add_technical_details_to_assets.py (revision: 7cc356fcc04a)
- 951b58543ba5_add_confidence_score_to_assets.py (revision: 951b58543ba5)
- add_canonical_application_identity.py (revision: canonical_apps_001)
- add_collection_flow_applications_table.py (revision: add_collection_apps_001)
- b75f619e44dc_fix_application_name_variants_timestamps.py (revision: b75f619e44dc)
- c279c3c0699d_fix_timestamp_mixin_timezone_issues.py (revision: c279c3c0699d)
- cb5aa7ecb987_merge_heads_for_attribute_mapping_fix.py (revision: cb5aa7ecb987)
- cef530e273d4_merge_heads_fix_questionnaire_asset_.py (revision: cef530e273d4)
- dc3417edf498_fix_platform_admin_is_admin_flag_after_.py (revision: dc3417edf498)

## Missing Proper Downgrade Functions
- 006_add_collection_flow_next_phase.py
- 007_add_missing_collection_flow_columns.py
- 008_update_flow_type_constraint.py
- 011_add_updated_at_to_collection_data_gaps.py
- 012_agent_observability_enhancement.py
- 013_fix_agent_task_history_foreign_keys.py
- 014_fix_remaining_agent_foreign_keys.py
- 020_merge_heads.py
- 024_add_cache_metadata_tables.py
- 033_merge_all_heads.py
- 038_add_agent_pattern_learning_columns.py
- 039_create_pattern_type_enum.py
- 040_add_missing_field_mapping_columns.py
- 043_merge_migration_heads.py
- 044_merge_036_and_questionnaire_asset_heads.py
- 045_merge_cache_and_platform_admin.py
- 51470c6d6288_merge_collection_apps_with_timestamp_fix.py
- cb5aa7ecb987_merge_heads_for_attribute_mapping_fix.py
- cef530e273d4_merge_heads_fix_questionnaire_asset_.py
- merge_mfo_testing_heads.py

## Migration Dependency Chain
  1. 001_comprehensive_initial_schema.py (001_comprehensive_initial_schema)
  2. 002_add_security_audit_tables.py (002_add_security_audit_tables)
  3. 003_add_collection_flow_tables.py (003_add_collection_flow_tables)
  4. 004_add_platform_credentials_tables.py (004_add_platform_credentials_tables)
  5. 005_add_gap_analysis_and_questionnaire_tables.py (005_add_gap_analysis_and_questionnaire_tables)
  6. 006_add_collection_flow_next_phase.py (006_add_collection_flow_next_phase)
  7. 007_add_missing_collection_flow_columns.py (007_add_missing_collection_flow_columns)
  8. 008_update_flow_type_constraint.py (008_update_flow_type_constraint)
  9. 009_add_collection_flow_id_to_questionnaires.py (009_add_collection_flow_id_to_questionnaires)
 10. 010_add_timestamp_columns_to_collected_data_inventory.py (010_add_timestamp_columns_to_collected_data_inventory)
 11. 011_add_updated_at_to_collection_data_gaps.py (011_add_updated_at_to_collection_data_gaps)
 12. 012_agent_observability_enhancement.py (012_agent_observability_enhancement)
 13. 013_fix_agent_task_history_foreign_keys.py (013_fix_agent_task_history_foreign_keys)
 14. 014_fix_remaining_agent_foreign_keys.py (014_fix_remaining_agent_foreign_keys)

## Orphaned Migrations (Not in Chain)
- add_collection_flow_applications_table.py (add_collection_apps_001)
- 027_add_indexes_and_failure_journal.py (027_add_indexes_and_failure_journal)
- 51470c6d6288_merge_collection_apps_with_timestamp_fix.py (51470c6d6288)
- 040_add_missing_field_mapping_columns.py (040_add_missing_field_mapping_columns)
- dc3417edf498_fix_platform_admin_is_admin_flag_after_.py (dc3417edf498)
- 034_add_client_account_id_to_engagement_standards.py (034_add_client_account_id_to_engagement_standards)
- migrate_existing_collection_applications.py (migrate_collection_apps_001)
- 033_merge_all_heads.py (033_merge_all_heads)
- 042_add_vector_search_to_agent_patterns.py (042_add_vector_search_to_agent_patterns)
- optimize_application_indexes.py (optimize_app_indexes_001)
- 022_add_is_admin_to_users.py (022_add_is_admin_to_users)
- cb5aa7ecb987_merge_heads_for_attribute_mapping_fix.py (cb5aa7ecb987)
- 7cc356fcc04a_add_technical_details_to_assets.py (7cc356fcc04a)
- 016_add_security_constraints.py (016_add_security_constraints)
- 043_merge_migration_heads.py (043_merge_migration_heads)
- add_canonical_application_identity.py (canonical_apps_001)
- 037_add_missing_audit_log_columns.py (037_add_missing_audit_log_columns)
- 019_implement_row_level_security.py (019_implement_row_level_security)
- 595ea1f47121_add_auto_generated_uuid_to_raw_import_.py (595ea1f47121)
- 036_rename_metadata_columns.py (036_rename_metadata_columns)
- c279c3c0699d_fix_timestamp_mixin_timezone_issues.py (c279c3c0699d)
- 031_add_flow_deletion_audit_table.py (031_add_flow_deletion_audit_table)
- 015_add_asset_dependencies_table.py (015_add_asset_dependencies)
- 038_add_agent_pattern_learning_columns.py (038_add_agent_pattern_learning_columns)
- 020_merge_heads.py (None)
- 030_add_sixr_analysis_tables.py (030_add_sixr_analysis_tables)
- 025_migrate_8r_to_5r_strategies.py (025_migrate_8r_to_5r_strategies)
- b75f619e44dc_fix_application_name_variants_timestamps.py (b75f619e44dc)
- 045_merge_cache_and_platform_admin.py (045_merge_cache_and_platform_admin)
- 026_add_assessment_readiness_fields_to_assets.py (026_add_assessment_readiness_fields_to_assets)
- 951b58543ba5_add_confidence_score_to_assets.py (951b58543ba5)
- 035_fix_engagement_architecture_standards_schema.py (035_fix_engagement_architecture_standards_schema)
- 018b_fix_long_constraint_names.py (018b_fix_long_constraint_names)
- cef530e273d4_merge_heads_fix_questionnaire_asset_.py (cef530e273d4)
- 032_add_master_flow_id_to_assessment_flows.py (032_add_master_flow_id_to_assessment_flows)
- 039_create_pattern_type_enum.py (039_create_pattern_type_enum)
- 028_add_updated_at_trigger_for_failure_journal.py (028_add_updated_at_trigger_for_failure_journal)
- merge_mfo_testing_heads.py (merge_mfo_testing_heads)
- 021_fix_import_field_mappings_id_default.py (021_fix_import_field_mappings_id_default)
- 029_complete_assessment_flows_schema.py (029_complete_assessment_flows_schema)
- 2ae8940123e6_add_analysis_queue_tables.py (2ae8940123e6)
- 044_merge_036_and_questionnaire_asset_heads.py (044_merge_036_and_questionnaire_asset_heads)
- 023_fix_data_imports_foreign_key_constraint.py (023_fix_data_imports_foreign_key_constraint)
- 024_add_cache_metadata_tables.py (024_add_cache_metadata_tables)

## All Migrations (Detailed)
### 001_comprehensive_initial_schema.py
- Revision: 001_comprehensive_initial_schema
- Down revision: None
- Has downgrade: ✓
- Type: Numbered
- Number: 001

### 002_add_security_audit_tables.py
- Revision: 002_add_security_audit_tables
- Down revision: 001_comprehensive_initial_schema
- Has downgrade: ✓
- Type: Numbered
- Number: 002

### 003_add_collection_flow_tables.py
- Revision: 003_add_collection_flow_tables
- Down revision: 002_add_security_audit_tables
- Has downgrade: ✓
- Type: Numbered
- Number: 003

### 004_add_platform_credentials_tables.py
- Revision: 004_add_platform_credentials_tables
- Down revision: 003_add_collection_flow_tables
- Has downgrade: ✓
- Type: Numbered
- Number: 004

### 005_add_gap_analysis_and_questionnaire_tables.py
- Revision: 005_add_gap_analysis_and_questionnaire_tables
- Down revision: 004_add_platform_credentials_tables
- Has downgrade: ✓
- Type: Numbered
- Number: 005

### 006_add_collection_flow_next_phase.py
- Revision: 006_add_collection_flow_next_phase
- Down revision: 005_add_gap_analysis_and_questionnaire_tables
- Has downgrade: ✗
- Type: Numbered
- Number: 006

### 007_add_missing_collection_flow_columns.py
- Revision: 007_add_missing_collection_flow_columns
- Down revision: 006_add_collection_flow_next_phase
- Has downgrade: ✗
- Type: Numbered
- Number: 007

### 008_update_flow_type_constraint.py
- Revision: 008_update_flow_type_constraint
- Down revision: 007_add_missing_collection_flow_columns
- Has downgrade: ✗
- Type: Numbered
- Number: 008

### 009_add_collection_flow_id_to_questionnaires.py
- Revision: 009_add_collection_flow_id_to_questionnaires
- Down revision: 008_update_flow_type_constraint
- Has downgrade: ✓
- Type: Numbered
- Number: 009

### 010_add_timestamp_columns_to_collected_data_inventory.py
- Revision: 010_add_timestamp_columns_to_collected_data_inventory
- Down revision: 009_add_collection_flow_id_to_questionnaires
- Has downgrade: ✓
- Type: Numbered
- Number: 010

### 011_add_updated_at_to_collection_data_gaps.py
- Revision: 011_add_updated_at_to_collection_data_gaps
- Down revision: 010_add_timestamp_columns_to_collected_data_inventory
- Has downgrade: ✗
- Type: Numbered
- Number: 011

### 012_agent_observability_enhancement.py
- Revision: 012_agent_observability_enhancement
- Down revision: 011_add_updated_at_to_collection_data_gaps
- Has downgrade: ✗
- Type: Numbered
- Number: 012

### 013_fix_agent_task_history_foreign_keys.py
- Revision: 013_fix_agent_task_history_foreign_keys
- Down revision: 012_agent_observability_enhancement
- Has downgrade: ✗
- Type: Numbered
- Number: 013

### 014_fix_remaining_agent_foreign_keys.py
- Revision: 014_fix_remaining_agent_foreign_keys
- Down revision: 013_fix_agent_task_history_foreign_keys
- Has downgrade: ✗
- Type: Numbered
- Number: 014

### 015_add_asset_dependencies_table.py
- Revision: 015_add_asset_dependencies
- Down revision: None
- Has downgrade: ✓
- Type: Numbered
- Number: 015

### 016_add_security_constraints.py
- Revision: 016_add_security_constraints
- Down revision: 015_add_asset_dependencies
- Has downgrade: ✓
- Type: Numbered
- Number: 016

### 018b_fix_long_constraint_names.py
- Revision: 018b_fix_long_constraint_names
- Down revision: 018_add_agent_execution_history
- Has downgrade: ✓
- Type: Numbered
- Number: 018b

### 019_implement_row_level_security.py
- Revision: 019_implement_row_level_security
- Down revision: 018b_fix_long_constraint_names
- Has downgrade: ✓
- Type: Numbered
- Number: 019

### 020_merge_heads.py
- Revision: None
- Down revision: None
- Has downgrade: ✗
- Type: Numbered
- Number: 020

### 021_fix_import_field_mappings_id_default.py
- Revision: 021_fix_import_field_mappings_id_default
- Down revision: 595ea1f47121
- Has downgrade: ✓
- Type: Numbered
- Number: 021

### 022_add_is_admin_to_users.py
- Revision: 022_add_is_admin_to_users
- Down revision: 021_fix_import_field_mappings_id_default
- Has downgrade: ✓
- Type: Numbered
- Number: 022

### 023_fix_data_imports_foreign_key_constraint.py
- Revision: 023_fix_data_imports_foreign_key_constraint
- Down revision: 022_add_is_admin_to_users
- Has downgrade: ✓
- Type: Numbered
- Number: 023

### 024_add_cache_metadata_tables.py
- Revision: 024_add_cache_metadata_tables
- Down revision: 023_fix_data_imports_foreign_key_constraint
- Has downgrade: ✗
- Type: Numbered
- Number: 024

### 025_migrate_8r_to_5r_strategies.py
- Revision: 025_migrate_8r_to_5r_strategies
- Down revision: 2ae8940123e6
- Has downgrade: ✓
- Type: Numbered
- Number: 025

### 026_add_assessment_readiness_fields_to_assets.py
- Revision: 026_add_assessment_readiness_fields_to_assets
- Down revision: 025_migrate_8r_to_5r_strategies
- Has downgrade: ✓
- Type: Numbered
- Number: 026

### 027_add_indexes_and_failure_journal.py
- Revision: 027_add_indexes_and_failure_journal
- Down revision: 026_add_assessment_readiness_fields_to_assets
- Has downgrade: ✓
- Type: Numbered
- Number: 027

### 028_add_updated_at_trigger_for_failure_journal.py
- Revision: 028_add_updated_at_trigger_for_failure_journal
- Down revision: 027_add_indexes_and_failure_journal
- Has downgrade: ✓
- Type: Numbered
- Number: 028

### 029_complete_assessment_flows_schema.py
- Revision: 029_complete_assessment_flows_schema
- Down revision: 028_add_updated_at_trigger_for_failure_journal
- Has downgrade: ✓
- Type: Numbered
- Number: 029

### 030_add_sixr_analysis_tables.py
- Revision: 030_add_sixr_analysis_tables
- Down revision: 029_complete_assessment_flows_schema
- Has downgrade: ✓
- Type: Numbered
- Number: 030

### 031_add_flow_deletion_audit_table.py
- Revision: 031_add_flow_deletion_audit_table
- Down revision: 030_add_sixr_analysis_tables
- Has downgrade: ✓
- Type: Numbered
- Number: 031

### 032_add_master_flow_id_to_assessment_flows.py
- Revision: 032_add_master_flow_id_to_assessment_flows
- Down revision: 031_add_flow_deletion_audit_table
- Has downgrade: ✓
- Type: Numbered
- Number: 032

### 033_merge_all_heads.py
- Revision: 033_merge_all_heads
- Down revision: None
- Down revisions: ['032b_rename_metadata_columns', 'merge_mfo_testing_heads']
- Has downgrade: ✗
- Type: Numbered
- Number: 033

### 034_add_client_account_id_to_engagement_standards.py
- Revision: 034_add_client_account_id_to_engagement_standards
- Down revision: 033_merge_all_heads
- Has downgrade: ✓
- Type: Numbered
- Number: 034

### 035_fix_engagement_architecture_standards_schema.py
- Revision: 035_fix_engagement_architecture_standards_schema
- Down revision: 034_add_client_account_id_to_engagement_standards
- Has downgrade: ✓
- Type: Numbered
- Number: 035

### 036_rename_metadata_columns.py
- Revision: 036_rename_metadata_columns
- Down revision: 035_fix_engagement_architecture_standards_schema
- Has downgrade: ✓
- Type: Numbered
- Number: 036

### 037_add_missing_audit_log_columns.py
- Revision: 037_add_missing_audit_log_columns
- Down revision: 64630c6d6a9a
- Has downgrade: ✓
- Type: Numbered
- Number: 037

### 038_add_agent_pattern_learning_columns.py
- Revision: 038_add_agent_pattern_learning_columns
- Down revision: 037_add_missing_audit_log_columns
- Has downgrade: ✗
- Type: Numbered
- Number: 038

### 039_create_pattern_type_enum.py
- Revision: 039_create_pattern_type_enum
- Down revision: 038_add_agent_pattern_learning_columns
- Has downgrade: ✗
- Type: Numbered
- Number: 039

### 040_add_missing_field_mapping_columns.py
- Revision: 040_add_missing_field_mapping_columns
- Down revision: 039_create_pattern_type_enum
- Has downgrade: ✗
- Type: Numbered
- Number: 040

### 042_add_vector_search_to_agent_patterns.py
- Revision: 042_add_vector_search_to_agent_patterns
- Down revision: 041_add_hybrid_properties_collected_data_inventory
- Has downgrade: ✓
- Type: Numbered
- Number: 042

### 043_merge_migration_heads.py
- Revision: 043_merge_migration_heads
- Down revision: None
- Down revisions: ['035_fix_engagement_architecture_standards_schema', 'optimize_app_indexes_001']
- Has downgrade: ✗
- Type: Numbered
- Number: 043

### 044_merge_036_and_questionnaire_asset_heads.py
- Revision: 044_merge_036_and_questionnaire_asset_heads
- Down revision: None
- Down revisions: ['036_fix_null_master_flow_ids', 'cef530e273d4']
- Has downgrade: ✗
- Type: Numbered
- Number: 044

### 045_merge_cache_and_platform_admin.py
- Revision: 045_merge_cache_and_platform_admin
- Down revision: None
- Down revisions: ['024_add_cache_metadata_tables', 'dc3417edf498']
- Has downgrade: ✗
- Type: Numbered
- Number: 045

### 2ae8940123e6_add_analysis_queue_tables.py
- Revision: 2ae8940123e6
- Down revision: fcacece8fa7b
- Has downgrade: ✓
- Type: Hash-named

### 51470c6d6288_merge_collection_apps_with_timestamp_fix.py
- Revision: 51470c6d6288
- Down revision: None
- Down revisions: ['add_collection_apps_001', 'c279c3c0699d']
- Has downgrade: ✗
- Type: Hash-named

### 595ea1f47121_add_auto_generated_uuid_to_raw_import_.py
- Revision: 595ea1f47121
- Down revision: 019_implement_row_level_security
- Has downgrade: ✓
- Type: Hash-named

### 7cc356fcc04a_add_technical_details_to_assets.py
- Revision: 7cc356fcc04a
- Down revision: 951b58543ba5
- Has downgrade: ✓
- Type: Hash-named

### 951b58543ba5_add_confidence_score_to_assets.py
- Revision: 951b58543ba5
- Down revision: 029_complete_assessment_flows_schema
- Has downgrade: ✓
- Type: Hash-named

### add_canonical_application_identity.py
- Revision: canonical_apps_001
- Down revision: add_collection_apps_001
- Has downgrade: ✓
- Type: Hash-named

### add_collection_flow_applications_table.py
- Revision: add_collection_apps_001
- Down revision: fcacece8fa7b
- Has downgrade: ✓
- Type: Hash-named

### b75f619e44dc_fix_application_name_variants_timestamps.py
- Revision: b75f619e44dc
- Down revision: 041_add_hybrid_properties
- Has downgrade: ✓
- Type: Hash-named

### c279c3c0699d_fix_timestamp_mixin_timezone_issues.py
- Revision: c279c3c0699d
- Down revision: 7cc356fcc04a
- Has downgrade: ✓
- Type: Hash-named

### cb5aa7ecb987_merge_heads_for_attribute_mapping_fix.py
- Revision: cb5aa7ecb987
- Down revision: None
- Down revisions: ['020_merge_heads', '030_add_sixr_analysis_tables']
- Has downgrade: ✗
- Type: Hash-named

### cef530e273d4_merge_heads_fix_questionnaire_asset_.py
- Revision: cef530e273d4
- Down revision: None
- Down revisions: ['017_add_asset_id_to_questionnaire_responses', '1687c833bfcc']
- Has downgrade: ✗
- Type: Hash-named

### dc3417edf498_fix_platform_admin_is_admin_flag_after_.py
- Revision: dc3417edf498
- Down revision: 023_fix_data_imports_foreign_key_constraint
- Has downgrade: ✓
- Type: Hash-named

### merge_mfo_testing_heads.py
- Revision: merge_mfo_testing_heads
- Down revision: None
- Down revisions: ['032_add_master_flow_id_to_assessment_flows', 'cb5aa7ecb987']
- Has downgrade: ✗
- Type: Other

### migrate_existing_collection_applications.py
- Revision: migrate_collection_apps_001
- Down revision: canonical_apps_001
- Has downgrade: ✓
- Type: Other

### optimize_application_indexes.py
- Revision: optimize_app_indexes_001
- Down revision: migrate_collection_apps_001
- Has downgrade: ✓
- Type: Other
