-- Test script to verify engagement_id fix
-- This will show the current state of import_field_mappings

\echo '=========================================='
\echo 'BEFORE FIX: Current state of import_field_mappings'
\echo '=========================================='
\echo ''

SELECT 
    id,
    source_field,
    target_field,
    engagement_id,
    master_flow_id,
    status,
    data_import_id
FROM migration.import_field_mappings
ORDER BY created_at DESC
LIMIT 10;

\echo ''
\echo '=========================================='
\echo 'Checking related data_imports table'
\echo '=========================================='
\echo ''

SELECT 
    di.id as data_import_id,
    di.engagement_id,
    di.master_flow_id,
    COUNT(ifm.id) as mapping_count
FROM migration.data_imports di
LEFT JOIN migration.import_field_mappings ifm ON di.id = ifm.data_import_id
GROUP BY di.id, di.engagement_id, di.master_flow_id;

\echo ''
\echo '=========================================='
\echo 'Summary: Field mappings missing engagement_id'
\echo '=========================================='
\echo ''

SELECT 
    COUNT(*) FILTER (WHERE engagement_id IS NULL) as null_engagement_id,
    COUNT(*) FILTER (WHERE engagement_id IS NOT NULL) as has_engagement_id,
    COUNT(*) FILTER (WHERE master_flow_id IS NULL) as null_master_flow_id,
    COUNT(*) FILTER (WHERE master_flow_id IS NOT NULL) as has_master_flow_id,
    COUNT(*) as total
FROM migration.import_field_mappings;

