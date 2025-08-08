-- Rollback script for data import migration
-- Generated: 2025-07-07T23:45:31.837209

-- Rollback DataImport linkages
UPDATE migration.data_imports
SET master_flow_id = NULL
WHERE master_flow_id IS NOT NULL;

-- Rollback RawImportRecord linkages
UPDATE migration.raw_import_records
SET master_flow_id = NULL
WHERE master_flow_id IS NOT NULL;

-- Verification queries
SELECT COUNT(*) AS orphaned_data_imports FROM migration.data_imports
WHERE master_flow_id IS NULL;
SELECT COUNT(*) AS orphaned_raw_records FROM migration.raw_import_records
WHERE master_flow_id IS NULL;
