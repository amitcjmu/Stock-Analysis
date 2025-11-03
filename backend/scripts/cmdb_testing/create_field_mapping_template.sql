-- Field Mapping Template for CMDB Fields
-- This creates a reusable mapping template to avoid manual mapping every time
--
-- Usage: Run this ONCE, then use /api/v1/data-import/field-mapping/apply-template
--        to auto-apply these mappings to new imports

-- IMPORTANT: Replace these UUIDs with your actual values:
-- - <DATA_IMPORT_ID>: Get from data_imports table
-- - <CLIENT_ID>: 11111111-1111-1111-1111-111111111111
-- - <ENGAGEMENT_ID>: 22222222-2222-2222-2222-222222222222

BEGIN;

-- Delete existing mappings for this import (optional, if re-running)
-- DELETE FROM migration.import_field_mappings WHERE data_import_id = '<DATA_IMPORT_ID>';

-- Core identification fields
INSERT INTO migration.import_field_mappings
    (id, data_import_id, client_account_id, engagement_id, source_field, target_field, status, confidence_score, created_at, updated_at)
VALUES
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'asset_id', 'asset_id', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'asset_type', 'asset_type', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'application_name', 'application_name', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'server_hostname', 'hostname', 'approved', 1.0, NOW(), NOW()),

    -- CMDB Business/Org fields
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'business_unit', 'business_unit', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'vendor', 'vendor', 'approved', 1.0, NOW(), NOW()),

    -- CMDB Application fields
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'application_type', 'application_type', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'lifecycle', 'lifecycle', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'hosting_model', 'hosting_model', 'approved', 1.0, NOW(), NOW()),

    -- CMDB Server fields
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'role', 'server_role', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'security_zone', 'security_zone', 'approved', 1.0, NOW(), NOW()),

    -- CMDB Database fields
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'primary_database_type', 'database_type', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'primary_database_version', 'database_version', 'approved', 1.0, NOW(), NOW()),

    -- CMDB Compliance fields
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'pii_flag', 'pii_flag', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'data_classification', 'application_data_classification', 'approved', 1.0, NOW(), NOW()),

    -- CMDB Performance fields
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'cpu_max_percent', 'cpu_utilization_percent_max', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'memory_max_percent', 'memory_utilization_percent_max', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'storage_free_gb', 'storage_free_gb', 'approved', 1.0, NOW(), NOW()),

    -- CMDB Migration fields
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'has_saas_replacement', 'has_saas_replacement', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'risk_level', 'risk_level', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'tshirt_size', 'tshirt_size', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'proposed_rationale', 'proposed_treatmentplan_rationale', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'annual_cost_estimate', 'annual_cost_estimate', 'approved', 1.0, NOW(), NOW()),

    -- EOL fields (for child table)
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'eol_date', 'eol_date', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'eol_risk_level', 'eol_risk_level', 'approved', 1.0, NOW(), NOW()),

    -- Contact fields (for child table)
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'business_owner_name', 'business_owner_name', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'business_owner_email', 'business_owner_email', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'technical_owner_name', 'technical_owner_name', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'technical_owner_email', 'technical_owner_email', 'approved', 1.0, NOW(), NOW()),

    -- Environment and other core fields
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'environment', 'environment', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'business_criticality', 'business_criticality', 'approved', 1.0, NOW(), NOW()),
    (gen_random_uuid(), '<DATA_IMPORT_ID>', '<CLIENT_ID>', '<ENGAGEMENT_ID>', 'proposed_6r', 'six_r_strategy', 'approved', 1.0, NOW(), NOW());

COMMIT;

-- Verify mappings created
SELECT COUNT(*) as total_mappings FROM migration.import_field_mappings WHERE data_import_id = '<DATA_IMPORT_ID>';
