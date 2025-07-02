-- AI Force Migration Platform - Database Validation Test Queries
-- Manual verification queries for seeded demo data
-- Execute these in PostgreSQL to manually verify data integrity

-- =============================================================================
-- BASIC DATA COUNTS
-- =============================================================================

-- Expected counts validation
SELECT 'Client Accounts' as entity, COUNT(*) as actual_count, 3 as expected_count 
FROM migration.client_accounts
UNION ALL
SELECT 'Engagements', COUNT(*), 6 FROM migration.engagements
UNION ALL
SELECT 'Users', COUNT(*), 12 FROM migration.users
UNION ALL
SELECT 'Assets', COUNT(*), 150 FROM migration.assets
UNION ALL
SELECT 'Discovery Flows', COUNT(*), 6 FROM migration.discovery_flows
UNION ALL
SELECT 'Data Imports', COUNT(*), 12 FROM migration.data_imports
UNION ALL
SELECT 'Field Mappings', COUNT(*), 24 FROM migration.import_field_mappings
UNION ALL
SELECT 'Assessments', COUNT(*), 18 FROM migration.assessments
UNION ALL
SELECT 'Migrations', COUNT(*), 8 FROM migration.migrations
UNION ALL
SELECT 'Wave Plans', COUNT(*), 12 FROM migration.wave_plans;

-- =============================================================================
-- CLIENT ACCOUNT VALIDATION
-- =============================================================================

-- Client account details
SELECT 
    id,
    company_name,
    industry,
    status,
    created_at
FROM migration.client_accounts
ORDER BY company_name;

-- Industry distribution
SELECT 
    industry,
    COUNT(*) as count
FROM migration.client_accounts
GROUP BY industry
ORDER BY count DESC;

-- =============================================================================
-- USER VALIDATION
-- =============================================================================

-- User role distribution
SELECT 
    ur.role,
    COUNT(*) as user_count
FROM migration.user_roles ur
GROUP BY ur.role
ORDER BY user_count DESC;

-- Users by client account
SELECT 
    ca.company_name,
    COUNT(DISTINCT uaa.user_id) as user_count
FROM migration.client_accounts ca
LEFT JOIN migration.user_account_associations uaa ON ca.id = uaa.client_account_id
GROUP BY ca.id, ca.company_name
ORDER BY user_count DESC;

-- Users without roles (should be empty)
SELECT 
    u.id,
    u.email,
    u.first_name,
    u.last_name
FROM migration.users u
LEFT JOIN migration.user_roles ur ON u.id = ur.user_id
WHERE ur.user_id IS NULL;

-- Duplicate emails (should be empty)
SELECT 
    email,
    COUNT(*) as count
FROM migration.users
GROUP BY email
HAVING COUNT(*) > 1;

-- =============================================================================
-- ENGAGEMENT VALIDATION
-- =============================================================================

-- Engagements by client and status
SELECT 
    ca.company_name,
    e.name as engagement_name,
    e.status,
    e.migration_type,
    e.start_date
FROM migration.engagements e
JOIN migration.client_accounts ca ON e.client_account_id = ca.id
ORDER BY ca.company_name, e.name;

-- Engagement status distribution
SELECT 
    status,
    COUNT(*) as count
FROM migration.engagements
GROUP BY status
ORDER BY count DESC;

-- Engagements without client accounts (should be empty)
SELECT 
    id,
    name,
    client_account_id
FROM migration.engagements
WHERE client_account_id IS NULL;

-- =============================================================================
-- ASSET VALIDATION
-- =============================================================================

-- Asset type distribution
SELECT 
    asset_type,
    COUNT(*) as count,
    AVG(cpu_utilization_percent) as avg_cpu,
    AVG(memory_utilization_percent) as avg_memory
FROM migration.assets
WHERE asset_type IS NOT NULL
GROUP BY asset_type
ORDER BY count DESC;

-- Assets by client account
SELECT 
    ca.company_name,
    COUNT(*) as asset_count,
    COUNT(DISTINCT a.asset_type) as unique_types
FROM migration.assets a
JOIN migration.client_accounts ca ON a.client_account_id = ca.id
GROUP BY ca.id, ca.company_name
ORDER BY asset_count DESC;

-- Assets with invalid utilization (should be empty)
SELECT 
    id,
    name,
    cpu_utilization_percent,
    memory_utilization_percent
FROM migration.assets
WHERE cpu_utilization_percent > 100 
   OR memory_utilization_percent > 100
   OR cpu_utilization_percent < 0
   OR memory_utilization_percent < 0;

-- High value assets for demo
SELECT 
    a.name,
    a.asset_type,
    a.current_monthly_cost,
    ca.company_name
FROM migration.assets a
JOIN migration.client_accounts ca ON a.client_account_id = ca.id
WHERE a.current_monthly_cost > 5000
ORDER BY a.current_monthly_cost DESC
LIMIT 10;

-- =============================================================================
-- DISCOVERY FLOW VALIDATION
-- =============================================================================

-- Discovery flows by phase
SELECT 
    current_phase,
    COUNT(*) as count
FROM migration.discovery_flows
GROUP BY current_phase
ORDER BY count DESC;

-- Discovery flows with progress
SELECT 
    df.id,
    df.flow_id,
    df.current_phase,
    df.progress_percentage,
    ca.company_name
FROM migration.discovery_flows df
JOIN migration.client_accounts ca ON df.client_account_id = ca.id
ORDER BY df.progress_percentage DESC;

-- =============================================================================
-- DATA IMPORT VALIDATION
-- =============================================================================

-- Data imports by status
SELECT 
    status,
    COUNT(*) as count
FROM migration.data_imports
GROUP BY status
ORDER BY count DESC;

-- Data imports with record counts
SELECT 
    di.id,
    di.file_name,
    di.status,
    COUNT(rir.id) as raw_record_count
FROM migration.data_imports di
LEFT JOIN migration.raw_import_records rir ON di.id = rir.data_import_id
GROUP BY di.id, di.file_name, di.status
ORDER BY raw_record_count DESC;

-- Data imports without raw records (potential issue)
SELECT 
    di.id,
    di.file_name,
    di.status
FROM migration.data_imports di
LEFT JOIN migration.raw_import_records rir ON di.id = rir.data_import_id
WHERE rir.id IS NULL;

-- =============================================================================
-- FIELD MAPPING VALIDATION
-- =============================================================================

-- Field mappings by approval status
SELECT 
    approval_status,
    COUNT(*) as count
FROM migration.import_field_mappings
GROUP BY approval_status
ORDER BY count DESC;

-- Field mappings by data import
SELECT 
    di.file_name,
    COUNT(ifm.id) as mapping_count,
    COUNT(CASE WHEN ifm.approval_status = 'approved' THEN 1 END) as approved_count
FROM migration.data_imports di
LEFT JOIN migration.import_field_mappings ifm ON di.id = ifm.data_import_id
GROUP BY di.id, di.file_name
ORDER BY mapping_count DESC;

-- =============================================================================
-- MULTI-TENANT ISOLATION VALIDATION
-- =============================================================================

-- Data distribution by client account
SELECT 
    ca.company_name,
    (SELECT COUNT(*) FROM migration.engagements WHERE client_account_id = ca.id) as engagements,
    (SELECT COUNT(*) FROM migration.assets WHERE client_account_id = ca.id) as assets,
    (SELECT COUNT(*) FROM migration.discovery_flows WHERE client_account_id = ca.id) as flows,
    (SELECT COUNT(*) FROM migration.data_imports WHERE client_account_id = ca.id) as imports
FROM migration.client_accounts ca
ORDER BY ca.company_name;

-- Cross-tenant data contamination check (should be empty)
-- Assets that don't belong to the same client as their engagement
SELECT 
    a.id as asset_id,
    a.name as asset_name,
    a.client_account_id as asset_client,
    e.client_account_id as engagement_client
FROM migration.assets a
JOIN migration.engagements e ON a.engagement_id = e.id
WHERE a.client_account_id != e.client_account_id;

-- =============================================================================
-- ASSESSMENT AND MIGRATION VALIDATION
-- =============================================================================

-- Assessments by type and status
SELECT 
    assessment_type,
    status,
    COUNT(*) as count
FROM migration.assessments
GROUP BY assessment_type, status
ORDER BY assessment_type, count DESC;

-- Migrations by phase
SELECT 
    current_phase,
    COUNT(*) as count,
    AVG(progress_percentage) as avg_progress
FROM migration.migrations
GROUP BY current_phase
ORDER BY count DESC;

-- Wave plans by status
SELECT 
    status,
    COUNT(*) as count,
    AVG(complexity_score) as avg_complexity
FROM migration.wave_plans
GROUP BY status
ORDER BY count DESC;

-- =============================================================================
-- ASSET DEPENDENCY VALIDATION
-- =============================================================================

-- Asset dependency statistics
SELECT 
    'Total Dependencies' as metric,
    COUNT(*) as value
FROM migration.asset_dependencies
UNION ALL
SELECT 
    'Assets with Dependencies',
    COUNT(DISTINCT asset_id)
FROM migration.asset_dependencies
UNION ALL
SELECT 
    'Assets Being Depended On',
    COUNT(DISTINCT depends_on_asset_id)
FROM migration.asset_dependencies;

-- Circular dependencies (should be empty)
SELECT 
    asset_id,
    depends_on_asset_id
FROM migration.asset_dependencies
WHERE asset_id = depends_on_asset_id;

-- Assets with most dependencies
SELECT 
    a.name,
    a.asset_type,
    COUNT(ad.depends_on_asset_id) as dependency_count
FROM migration.assets a
JOIN migration.asset_dependencies ad ON a.id = ad.asset_id
GROUP BY a.id, a.name, a.asset_type
ORDER BY dependency_count DESC
LIMIT 10;

-- =============================================================================
-- DATA QUALITY CHECKS
-- =============================================================================

-- NULL or empty critical fields (should be minimal)
SELECT 
    'Users with empty email' as check_name,
    COUNT(*) as issue_count
FROM migration.users 
WHERE email IS NULL OR email = ''
UNION ALL
SELECT 
    'Assets with empty name',
    COUNT(*)
FROM migration.assets 
WHERE name IS NULL OR name = ''
UNION ALL
SELECT 
    'Client Accounts with empty company name',
    COUNT(*)
FROM migration.client_accounts 
WHERE company_name IS NULL OR company_name = ''
UNION ALL
SELECT 
    'Engagements with empty name',
    COUNT(*)
FROM migration.engagements 
WHERE name IS NULL OR name = '';

-- Future dates where they shouldn't be (should be empty)
SELECT 
    'Assets with future discovery dates' as check_name,
    COUNT(*) as issue_count
FROM migration.assets
WHERE discovery_timestamp > NOW();

-- =============================================================================
-- PERFORMANCE TEST QUERIES
-- =============================================================================

-- Complex join query (test performance)
EXPLAIN ANALYZE
SELECT 
    a.name as asset_name,
    a.asset_type,
    ca.company_name,
    e.name as engagement_name,
    df.current_phase,
    m.current_phase as migration_phase
FROM migration.assets a
JOIN migration.client_accounts ca ON a.client_account_id = ca.id
JOIN migration.engagements e ON a.engagement_id = e.id
LEFT JOIN migration.discovery_flows df ON e.id = df.engagement_id
LEFT JOIN migration.migrations m ON a.migration_id = m.id
WHERE a.current_monthly_cost > 1000
ORDER BY a.current_monthly_cost DESC
LIMIT 50;

-- =============================================================================
-- DEMO USER SCENARIOS
-- =============================================================================

-- Test data for System Admin user (sees all data)
SELECT 
    'System Admin View' as scenario,
    COUNT(DISTINCT ca.id) as client_accounts,
    COUNT(DISTINCT e.id) as engagements,
    COUNT(DISTINCT a.id) as assets
FROM migration.client_accounts ca
LEFT JOIN migration.engagements e ON ca.id = e.client_account_id
LEFT JOIN migration.assets a ON ca.id = a.client_account_id;

-- Test data for specific client (TechCorp example)
SELECT 
    'TechCorp User View' as scenario,
    COUNT(DISTINCT e.id) as engagements,
    COUNT(DISTINCT a.id) as assets,
    COUNT(DISTINCT df.id) as discovery_flows
FROM migration.client_accounts ca
LEFT JOIN migration.engagements e ON ca.id = e.client_account_id
LEFT JOIN migration.assets a ON ca.id = a.client_account_id
LEFT JOIN migration.discovery_flows df ON ca.id = df.client_account_id
WHERE ca.company_name = 'TechCorp Solutions';

-- =============================================================================
-- SUMMARY VALIDATION
-- =============================================================================

-- Overall data health summary
SELECT 
    'TOTAL RECORDS' as category,
    (SELECT COUNT(*) FROM migration.client_accounts) + 
    (SELECT COUNT(*) FROM migration.engagements) + 
    (SELECT COUNT(*) FROM migration.users) + 
    (SELECT COUNT(*) FROM migration.assets) + 
    (SELECT COUNT(*) FROM migration.discovery_flows) + 
    (SELECT COUNT(*) FROM migration.data_imports) + 
    (SELECT COUNT(*) FROM migration.import_field_mappings) + 
    (SELECT COUNT(*) FROM migration.assessments) + 
    (SELECT COUNT(*) FROM migration.migrations) + 
    (SELECT COUNT(*) FROM migration.wave_plans) as count;

-- Schema information
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'migration'
  AND table_name IN ('client_accounts', 'users', 'assets', 'engagements')
ORDER BY table_name, ordinal_position;