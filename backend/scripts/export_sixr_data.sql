-- Export 6R Analysis Data for Migration Reference
-- Purpose: Archive legacy 6R Analysis data before migration to Assessment Flow
-- Issue: #837 - Phase 1 of Assessment Flow MFO Migration
-- Date: October 2025
--
-- USAGE:
-- From Docker container:
--   docker exec -it migration_postgres psql -U postgres -d migration_db -f /path/to/export_sixr_data.sql
--
-- From host (with psql installed):
--   psql -h localhost -p 5433 -U postgres -d migration_db -f backend/scripts/export_sixr_data.sql
--
-- This script exports data to CSV files in /tmp/ directory
-- Files will be created in the container's /tmp/ directory

\echo '========================================='
\echo 'Exporting 6R Analysis Data for Archive'
\echo 'Issue #837 - Assessment Flow MFO Migration'
\echo '========================================='
\echo ''

-- Set output directory (inside container)
\set output_dir '/tmp/sixr_export_' :DATE

\echo 'Output directory: ' :output_dir
\echo ''

-- Export sixr_analyses table
\echo 'Exporting sixr_analyses table...'
\copy (SELECT * FROM migration.sixr_analyses ORDER BY created_at) TO '/tmp/sixr_analyses_export.csv' WITH CSV HEADER;

-- Export sixr_iterations table
\echo 'Exporting sixr_iterations table...'
\copy (SELECT * FROM migration.sixr_iterations ORDER BY created_at) TO '/tmp/sixr_iterations_export.csv' WITH CSV HEADER;

-- Export sixr_recommendations table
\echo 'Exporting sixr_recommendations table...'
\copy (SELECT * FROM migration.sixr_recommendations ORDER BY created_at) TO '/tmp/sixr_recommendations_export.csv' WITH CSV HEADER;

-- Export sixr_analysis_parameters table
\echo 'Exporting sixr_analysis_parameters table...'
\copy (SELECT * FROM migration.sixr_analysis_parameters ORDER BY analysis_id) TO '/tmp/sixr_analysis_parameters_export.csv' WITH CSV HEADER;

-- Export sixr_qualifying_questions table (if exists)
\echo 'Exporting sixr_qualifying_questions table...'
\copy (SELECT * FROM migration.sixr_qualifying_questions ORDER BY id) TO '/tmp/sixr_qualifying_questions_export.csv' WITH CSV HEADER;

\echo ''
\echo '========================================='
\echo 'Export Statistics'
\echo '========================================='

-- Show record counts
SELECT
    'sixr_analyses' AS table_name,
    COUNT(*) AS record_count,
    MIN(created_at) AS earliest_record,
    MAX(created_at) AS latest_record
FROM migration.sixr_analyses
UNION ALL
SELECT
    'sixr_iterations' AS table_name,
    COUNT(*) AS record_count,
    MIN(created_at) AS earliest_record,
    MAX(created_at) AS latest_record
FROM migration.sixr_iterations
UNION ALL
SELECT
    'sixr_recommendations' AS table_name,
    COUNT(*) AS record_count,
    MIN(created_at) AS earliest_record,
    MAX(created_at) AS latest_record
FROM migration.sixr_recommendations
ORDER BY table_name;

\echo ''
\echo 'Export complete! Files created in /tmp/ directory:'
\echo '  - sixr_analyses_export.csv'
\echo '  - sixr_iterations_export.csv'
\echo '  - sixr_recommendations_export.csv'
\echo '  - sixr_analysis_parameters_export.csv'
\echo '  - sixr_qualifying_questions_export.csv'
\echo ''
\echo 'To copy files from container to host:'
\echo '  docker cp migration_postgres:/tmp/sixr_analyses_export.csv .'
\echo '  docker cp migration_postgres:/tmp/sixr_iterations_export.csv .'
\echo '  docker cp migration_postgres:/tmp/sixr_recommendations_export.csv .'
\echo '  docker cp migration_postgres:/tmp/sixr_analysis_parameters_export.csv .'
\echo '  docker cp migration_postgres:/tmp/sixr_qualifying_questions_export.csv .'
\echo ''
\echo '========================================='
\echo 'Archive data has been preserved for historical reference'
\echo 'These tables will be dropped in Phase 4 of the migration'
\echo 'See: docs/planning/ASSESSMENT_FLOW_MFO_MIGRATION_PLAN.md'
\echo '========================================='
