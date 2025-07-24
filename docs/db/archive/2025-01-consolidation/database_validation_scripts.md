# Database Validation Scripts

This document contains SQL scripts for validating database integrity and monitoring the health of the AI Modernize Migration Platform database.

## Quick Health Check Script

Run this script daily to check overall database health:

```sql
-- Database Health Dashboard
SELECT 
    'Database Health Check' as report_type,
    NOW() as check_time;

-- Core table counts
SELECT 
    'Table Counts' as section,
    'client_accounts' as table_name, 
    COUNT(*) as record_count
FROM client_accounts
UNION ALL
SELECT 'Table Counts', 'users', COUNT(*) FROM users
UNION ALL
SELECT 'Table Counts', 'engagements', COUNT(*) FROM engagements
UNION ALL
SELECT 'Table Counts', 'crewai_flow_state_extensions', COUNT(*) FROM crewai_flow_state_extensions
UNION ALL
SELECT 'Table Counts', 'discovery_flows', COUNT(*) FROM discovery_flows
UNION ALL
SELECT 'Table Counts', 'assets', COUNT(*) FROM assets
UNION ALL
SELECT 'Table Counts', 'data_imports', COUNT(*) FROM data_imports
ORDER BY section, table_name;
```

## Master Flow Integrity Check

Check for issues with master flow orchestration:

```sql
-- Master Flow Integrity Analysis
WITH integrity_issues AS (
    -- Orphaned discovery flows
    SELECT 
        'orphaned_discovery_flows' as issue_type,
        COUNT(*) as count,
        'HIGH' as severity
    FROM discovery_flows 
    WHERE master_flow_id IS NOT NULL 
    AND master_flow_id NOT IN (SELECT flow_id FROM crewai_flow_state_extensions)
    
    UNION ALL
    
    -- Assets without master flow linkage
    SELECT 
        'unlinked_assets',
        COUNT(*),
        'MEDIUM'
    FROM assets 
    WHERE master_flow_id IS NULL
    
    UNION ALL
    
    -- Discovery flows without master flows
    SELECT 
        'unlinked_discovery_flows',
        COUNT(*),
        'MEDIUM'
    FROM discovery_flows 
    WHERE master_flow_id IS NULL
    
    UNION ALL
    
    -- Field mappings without master flows
    SELECT 
        'unlinked_field_mappings',
        COUNT(*),
        'LOW'
    FROM import_field_mappings 
    WHERE master_flow_id IS NULL
    
    UNION ALL
    
    -- Raw import records without master flows  
    SELECT 
        'unlinked_raw_records',
        COUNT(*),
        'LOW'
    FROM raw_import_records 
    WHERE master_flow_id IS NULL
)
SELECT 
    issue_type,
    count,
    severity,
    CASE 
        WHEN count = 0 THEN '✅ OK'
        WHEN severity = 'HIGH' AND count > 0 THEN '❌ CRITICAL'
        WHEN severity = 'MEDIUM' AND count > 0 THEN '⚠️ WARNING'
        ELSE 'ℹ️ INFO'
    END as status
FROM integrity_issues
ORDER BY 
    CASE severity 
        WHEN 'HIGH' THEN 1 
        WHEN 'MEDIUM' THEN 2 
        WHEN 'LOW' THEN 3 
    END,
    count DESC;
```

## Multi-Tenant Isolation Validation

Verify multi-tenant data isolation:

```sql
-- Multi-Tenant Isolation Check
SELECT 'Multi-Tenant Validation' as check_type;

-- Check for tenant hierarchy consistency
SELECT 
    'assets_tenant_consistency' as check_name,
    COUNT(*) as violations,
    CASE WHEN COUNT(*) = 0 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM assets a
JOIN engagements e ON a.engagement_id = e.id
WHERE a.client_account_id <> e.client_account_id

UNION ALL

SELECT 
    'data_imports_tenant_consistency',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN '✅ PASS' ELSE '❌ FAIL' END
FROM data_imports di
JOIN engagements e ON di.engagement_id = e.id
WHERE di.client_account_id <> e.client_account_id

UNION ALL

SELECT 
    'discovery_flows_tenant_consistency',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN '✅ PASS' ELSE '❌ FAIL' END
FROM discovery_flows df
JOIN engagements e ON df.engagement_id = e.id
WHERE df.client_account_id <> e.client_account_id;

-- Check tenant distribution
SELECT 
    'Tenant Data Distribution' as section,
    ca.name as client_name,
    COUNT(DISTINCT e.id) as engagements,
    COUNT(DISTINCT a.id) as assets,
    COUNT(DISTINCT df.id) as discovery_flows,
    COUNT(DISTINCT di.id) as data_imports
FROM client_accounts ca
LEFT JOIN engagements e ON ca.id = e.client_account_id
LEFT JOIN assets a ON ca.id = a.client_account_id
LEFT JOIN discovery_flows df ON ca.id = df.client_account_id
LEFT JOIN data_imports di ON ca.id = di.client_account_id
GROUP BY ca.id, ca.name
ORDER BY ca.name;
```

## Foreign Key Integrity Validation

Check all foreign key relationships:

```sql
-- Foreign Key Integrity Check
SELECT 'Foreign Key Validation' as check_type;

-- Core foreign key integrity checks
WITH fk_checks AS (
    SELECT 
        'assets.client_account_id' as relationship,
        COUNT(*) as violations
    FROM assets 
    WHERE client_account_id IS NOT NULL 
    AND client_account_id NOT IN (SELECT id FROM client_accounts)
    
    UNION ALL
    
    SELECT 
        'assets.engagement_id',
        COUNT(*)
    FROM assets 
    WHERE engagement_id IS NOT NULL 
    AND engagement_id NOT IN (SELECT id FROM engagements)
    
    UNION ALL
    
    SELECT 
        'assets.flow_id',
        COUNT(*)
    FROM assets 
    WHERE flow_id IS NOT NULL 
    AND flow_id NOT IN (SELECT flow_id FROM discovery_flows)
    
    UNION ALL
    
    SELECT 
        'discovery_flows.data_import_id',
        COUNT(*)
    FROM discovery_flows 
    WHERE data_import_id IS NOT NULL 
    AND data_import_id NOT IN (SELECT id FROM data_imports)
    
    UNION ALL
    
    SELECT 
        'data_imports.imported_by',
        COUNT(*)
    FROM data_imports 
    WHERE imported_by IS NOT NULL 
    AND imported_by NOT IN (SELECT id FROM users)
)
SELECT 
    relationship,
    violations,
    CASE WHEN violations = 0 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM fk_checks
ORDER BY violations DESC;
```

## Flow State Analysis

Analyze the state of flows in the system:

```sql
-- Flow State Analysis
SELECT 'Flow State Analysis' as analysis_type;

-- Discovery flow status distribution
SELECT 
    'Discovery Flow Status' as category,
    status,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage
FROM discovery_flows
GROUP BY status
ORDER BY count DESC;

-- Master flow status distribution
SELECT 
    'Master Flow Status' as category,
    flow_status as status,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage
FROM crewai_flow_state_extensions
GROUP BY flow_status
ORDER BY count DESC;

-- Flow linkage summary
SELECT 
    'Flow Linkage Summary' as category,
    'discovery_flows_total' as metric,
    COUNT(*) as value
FROM discovery_flows
UNION ALL
SELECT 
    'Flow Linkage Summary',
    'discovery_flows_linked',
    COUNT(*)
FROM discovery_flows 
WHERE master_flow_id IS NOT NULL
UNION ALL
SELECT 
    'Flow Linkage Summary',
    'assets_total',
    COUNT(*)
FROM assets
UNION ALL
SELECT 
    'Flow Linkage Summary',
    'assets_linked_to_flows',
    COUNT(*)
FROM assets 
WHERE flow_id IS NOT NULL
UNION ALL
SELECT 
    'Flow Linkage Summary',
    'assets_linked_to_master',
    COUNT(*)
FROM assets 
WHERE master_flow_id IS NOT NULL;
```

## Data Quality Metrics

Check data quality across key tables:

```sql
-- Data Quality Assessment
SELECT 'Data Quality Metrics' as assessment_type;

-- Timestamp consistency check
SELECT 
    'Timestamp Consistency' as check_category,
    'discovery_flows' as table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE created_at > updated_at) as invalid_timestamps,
    CASE 
        WHEN COUNT(*) FILTER (WHERE created_at > updated_at) = 0 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as status
FROM discovery_flows 
WHERE created_at IS NOT NULL AND updated_at IS NOT NULL

UNION ALL

SELECT 
    'Timestamp Consistency',
    'assets',
    COUNT(*),
    COUNT(*) FILTER (WHERE created_at > updated_at),
    CASE 
        WHEN COUNT(*) FILTER (WHERE created_at > updated_at) = 0 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END
FROM assets 
WHERE created_at IS NOT NULL AND updated_at IS NOT NULL;

-- NULL value analysis for critical fields
SELECT 
    'Critical NULL Fields' as check_category,
    'discovery_flows.flow_name' as field,
    COUNT(*) FILTER (WHERE flow_name IS NULL) as null_count,
    COUNT(*) as total_count,
    CASE 
        WHEN COUNT(*) FILTER (WHERE flow_name IS NULL) = 0 THEN '✅ PASS'
        ELSE '⚠️ WARNING'
    END as status
FROM discovery_flows

UNION ALL

SELECT 
    'Critical NULL Fields',
    'assets.name',
    COUNT(*) FILTER (WHERE name IS NULL),
    COUNT(*),
    CASE 
        WHEN COUNT(*) FILTER (WHERE name IS NULL) = 0 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END
FROM assets;
```

## Performance Impact Analysis

Analyze potential performance issues:

```sql
-- Performance Impact Analysis
SELECT 'Performance Analysis' as analysis_type;

-- Large JSON field analysis
SELECT 
    'JSON Field Sizes' as category,
    'crewai_flow_state_extensions.flow_persistence_data' as field,
    COUNT(*) as records_with_data,
    ROUND(AVG(octet_length(flow_persistence_data::text))) as avg_size_bytes,
    MAX(octet_length(flow_persistence_data::text)) as max_size_bytes,
    CASE 
        WHEN MAX(octet_length(flow_persistence_data::text)) > 100000 THEN '⚠️ LARGE'
        ELSE '✅ OK'
    END as size_status
FROM crewai_flow_state_extensions
WHERE flow_persistence_data IS NOT NULL

UNION ALL

SELECT 
    'JSON Field Sizes',
    'assets.raw_data',
    COUNT(*),
    ROUND(AVG(octet_length(raw_data::text))),
    MAX(octet_length(raw_data::text)),
    CASE 
        WHEN MAX(octet_length(raw_data::text)) > 50000 THEN '⚠️ LARGE'
        ELSE '✅ OK'
    END
FROM assets
WHERE raw_data IS NOT NULL;

-- Table size estimates (PostgreSQL specific)
SELECT 
    'Table Sizes' as category,
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size
FROM pg_tables 
WHERE schemaname = 'public'
AND pg_total_relation_size(schemaname||'.'||tablename) > 1024  -- > 1KB
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

## Remediation Readiness Check

Check if the database is ready for remediation:

```sql
-- Remediation Readiness Assessment
SELECT 'Remediation Readiness' as assessment_type;

-- Check for backup tables (if any)
SELECT 
    'Backup Preparation' as category,
    COUNT(*) as backup_tables
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%_backup_%';

-- Check for active connections (be careful with this in production)
SELECT 
    'Active Connections' as category,
    COUNT(*) as connection_count,
    CASE 
        WHEN COUNT(*) < 10 THEN '✅ SAFE FOR MAINTENANCE'
        WHEN COUNT(*) < 50 THEN '⚠️ MODERATE ACTIVITY'
        ELSE '❌ HIGH ACTIVITY - WAIT'
    END as maintenance_status
FROM pg_stat_activity 
WHERE state = 'active' 
AND query NOT LIKE '%pg_stat_activity%';

-- Check for long-running transactions
SELECT 
    'Long Running Transactions' as category,
    COUNT(*) as long_transactions,
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ SAFE'
        ELSE '⚠️ WAIT FOR COMPLETION'
    END as safety_status
FROM pg_stat_activity 
WHERE state = 'active' 
AND query_start < NOW() - INTERVAL '5 minutes'
AND query NOT LIKE '%pg_stat_activity%';
```

## Automated Monitoring Script

For continuous monitoring, run this script every hour:

```sql
-- Automated Hourly Health Check
WITH health_metrics AS (
    SELECT 
        NOW() as check_time,
        
        -- Critical issues count
        (SELECT COUNT(*) FROM discovery_flows 
         WHERE master_flow_id IS NOT NULL 
         AND master_flow_id NOT IN (SELECT flow_id FROM crewai_flow_state_extensions)
        ) as orphaned_flows,
        
        -- Assets without master flow
        (SELECT COUNT(*) FROM assets WHERE master_flow_id IS NULL) as unlinked_assets,
        
        -- Total active flows
        (SELECT COUNT(*) FROM crewai_flow_state_extensions 
         WHERE flow_status IN ('active', 'processing')
        ) as active_flows,
        
        -- Recent flow activity (last 24 hours)
        (SELECT COUNT(*) FROM discovery_flows 
         WHERE created_at > NOW() - INTERVAL '24 hours'
        ) as recent_flows
)
SELECT 
    check_time,
    orphaned_flows,
    unlinked_assets,
    active_flows,
    recent_flows,
    CASE 
        WHEN orphaned_flows > 0 THEN 'CRITICAL'
        WHEN unlinked_assets > 50 THEN 'WARNING'
        ELSE 'HEALTHY'
    END as overall_status
FROM health_metrics;
```

## Usage Instructions

### Daily Monitoring
1. Run the **Quick Health Check Script** every morning
2. Review the **Master Flow Integrity Check** for any new issues
3. Check **Multi-Tenant Isolation Validation** weekly

### Before Maintenance
1. Run **Remediation Readiness Check**
2. Ensure all checks pass before proceeding with fixes
3. Create a full database backup

### After Remediation
1. Run all validation scripts to confirm fixes
2. Monitor for 24 hours using the **Automated Monitoring Script**
3. Update this document with any new checks needed

### Alerting Thresholds
- **CRITICAL**: orphaned_flows > 0
- **WARNING**: unlinked_assets > 25
- **INFO**: Recent activity patterns change significantly

---

*Database validation scripts for AI Modernize Migration Platform - January 2025*