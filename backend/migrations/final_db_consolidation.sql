-- Final Database Consolidation Script
-- Based on corrected architectural understanding

-- =====================================================
-- SAFETY: CREATE COMPLETE BACKUP
-- =====================================================

CREATE SCHEMA IF NOT EXISTS backup_final_consolidation;

-- Backup all affected tables
DO $$ 
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN 
        SELECT unnest(ARRAY[
            'data_imports', 'v3_data_imports',
            'discovery_flows', 'v3_discovery_flows', 
            'import_field_mappings', 'v3_field_mappings',
            'raw_import_records', 'v3_raw_import_records',
            'assets', 'workflow_states', 'discovery_assets',
            'mapping_learning_patterns', 'data_quality_issues',
            'workflow_progress', 'import_processing_steps',
            'crewai_flow_state_extensions'
        ])
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = tbl) THEN
            EXECUTE format('CREATE TABLE backup_final_consolidation.%I AS SELECT * FROM public.%I', tbl, tbl);
            RAISE NOTICE 'Backed up table: %', tbl;
        END IF;
    END LOOP;
END $$;

-- =====================================================
-- STEP 1: CONSOLIDATE DATA_IMPORTS
-- =====================================================

-- Add V3 fields that provide value
ALTER TABLE data_imports 
ADD COLUMN IF NOT EXISTS source_system VARCHAR,
ADD COLUMN IF NOT EXISTS error_message VARCHAR,
ADD COLUMN IF NOT EXISTS error_details JSON,
ADD COLUMN IF NOT EXISTS failed_records INTEGER DEFAULT 0;

-- Rename columns for consistency
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_imports' AND column_name='source_filename') THEN
        ALTER TABLE data_imports RENAME COLUMN source_filename TO filename;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_imports' AND column_name='file_size_bytes') THEN
        ALTER TABLE data_imports RENAME COLUMN file_size_bytes TO file_size;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_imports' AND column_name='file_type') THEN
        ALTER TABLE data_imports RENAME COLUMN file_type TO mime_type;
    END IF;
END $$;

-- Migrate V3 data
INSERT INTO data_imports (
    id, client_account_id, engagement_id, filename, 
    file_size, mime_type, source_system, status,
    total_records, processed_records, failed_records,
    created_at, updated_at, completed_at,
    error_message, error_details,
    import_name, import_type, imported_by
)
SELECT 
    v3.id, v3.client_account_id, v3.engagement_id, v3.filename,
    v3.file_size, v3.mime_type, v3.source_system, 
    COALESCE(v3.status, 'pending'),
    v3.total_records, v3.processed_records, v3.failed_records,
    v3.created_at AT TIME ZONE 'UTC', 
    v3.updated_at AT TIME ZONE 'UTC', 
    v3.completed_at AT TIME ZONE 'UTC',
    v3.error_message, v3.error_details,
    COALESCE(v3.filename, 'V3 Import'),
    'v3_migration',
    '00000000-0000-0000-0000-000000000000'::uuid
FROM v3_data_imports v3
WHERE NOT EXISTS (
    SELECT 1 FROM data_imports di WHERE di.id = v3.id
);

-- Drop only truly unused fields
ALTER TABLE data_imports
DROP COLUMN IF EXISTS file_hash,      -- Never implemented
DROP COLUMN IF EXISTS import_config,  -- Over-engineered
DROP COLUMN IF EXISTS is_mock;        -- Use multi-tenancy

-- KEEP master_flow_id - it's architecturally important!

-- =====================================================
-- STEP 2: CONSOLIDATE DISCOVERY_FLOWS (Hybrid)
-- =====================================================

-- Add V3 JSON fields alongside V1 boolean flags
ALTER TABLE discovery_flows
ADD COLUMN IF NOT EXISTS flow_type VARCHAR DEFAULT 'unified_discovery',
ADD COLUMN IF NOT EXISTS current_phase VARCHAR,
ADD COLUMN IF NOT EXISTS phases_completed JSON DEFAULT '[]',
ADD COLUMN IF NOT EXISTS flow_state JSON DEFAULT '{}',
ADD COLUMN IF NOT EXISTS crew_outputs JSON DEFAULT '{}',
ADD COLUMN IF NOT EXISTS field_mappings JSON,
ADD COLUMN IF NOT EXISTS discovered_assets JSON,
ADD COLUMN IF NOT EXISTS dependencies JSON,
ADD COLUMN IF NOT EXISTS tech_debt_analysis JSON,
ADD COLUMN IF NOT EXISTS error_message VARCHAR,
ADD COLUMN IF NOT EXISTS error_phase VARCHAR,
ADD COLUMN IF NOT EXISTS error_details JSON;

-- Update current_phase from boolean flags
UPDATE discovery_flows
SET current_phase = CASE
    WHEN tech_debt_assessment_completed = true THEN 'completed'
    WHEN dependency_analysis_completed = true THEN 'tech_debt_assessment'  
    WHEN asset_inventory_completed = true THEN 'dependency_analysis'
    WHEN data_cleansing_completed = true THEN 'asset_inventory'
    WHEN field_mapping_completed = true THEN 'data_cleansing'
    WHEN data_validation_completed = true THEN 'field_mapping'
    ELSE 'data_validation'
END
WHERE current_phase IS NULL;

-- Build phases_completed from boolean flags
UPDATE discovery_flows
SET phases_completed = 
    array_to_json(
        array_remove(ARRAY[
            CASE WHEN data_validation_completed THEN 'data_validation' END,
            CASE WHEN field_mapping_completed THEN 'field_mapping' END,
            CASE WHEN data_cleansing_completed THEN 'data_cleansing' END,
            CASE WHEN asset_inventory_completed THEN 'asset_inventory' END,
            CASE WHEN dependency_analysis_completed THEN 'dependency_analysis' END,
            CASE WHEN tech_debt_assessment_completed THEN 'tech_debt_assessment' END
        ], NULL)
    )
WHERE phases_completed = '[]';

-- Migrate V3 flows
INSERT INTO discovery_flows (
    id, client_account_id, engagement_id, flow_name,
    flow_type, data_import_id, status, current_phase,
    phases_completed, progress_percentage, flow_state,
    crew_outputs, field_mappings, discovered_assets,
    dependencies, tech_debt_analysis, created_at, updated_at,
    error_message, error_phase, error_details,
    user_id, learning_scope, memory_isolation_level, 
    is_mock, flow_id,
    data_import_completed, attribute_mapping_completed,
    data_cleansing_completed, inventory_completed,
    dependencies_completed, tech_debt_completed
)
SELECT 
    v3.id, v3.client_account_id, v3.engagement_id, 
    COALESCE(v3.flow_name, 'V3 Flow'),
    v3.flow_type, v3.data_import_id, 
    COALESCE(v3.status, 'pending'),
    v3.current_phase, v3.phases_completed, 
    COALESCE(v3.progress_percentage, 0.0),
    v3.flow_state, v3.crew_outputs, v3.field_mappings, 
    v3.discovered_assets, v3.dependencies, v3.tech_debt_analysis, 
    v3.created_at AT TIME ZONE 'UTC',
    v3.updated_at AT TIME ZONE 'UTC',
    v3.error_message, v3.error_phase, v3.error_details,
    'system', 'flow', 'flow', false, 
    COALESCE(v3.id, gen_random_uuid()),
    v3.phases_completed::text LIKE '%data_validation%',
    v3.phases_completed::text LIKE '%field_mapping%',
    v3.phases_completed::text LIKE '%data_cleansing%',
    v3.phases_completed::text LIKE '%asset_inventory%',
    v3.phases_completed::text LIKE '%dependency_analysis%',
    v3.phases_completed::text LIKE '%tech_debt_assessment%'
FROM v3_discovery_flows v3
WHERE NOT EXISTS (
    SELECT 1 FROM discovery_flows df WHERE df.id = v3.id
);

-- Drop only truly unused fields
ALTER TABLE discovery_flows
DROP COLUMN IF EXISTS assessment_package,     -- Never used
DROP COLUMN IF EXISTS flow_description,       -- Redundant
DROP COLUMN IF EXISTS assessment_ready,       -- Redundant with phases
DROP COLUMN IF EXISTS is_mock,               -- Use multi-tenancy
DROP COLUMN IF EXISTS learning_scope,        -- Over-engineered
DROP COLUMN IF EXISTS memory_isolation_level, -- Over-engineered
DROP COLUMN IF EXISTS crewai_persistence_id, -- Barely used
DROP COLUMN IF EXISTS flow_id;               -- Redundant with id

-- KEEP master_flow_id - it's for orchestration!

-- =====================================================
-- STEP 3: CONSOLIDATE IMPORT_FIELD_MAPPINGS
-- =====================================================

-- Add client_account_id if missing
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='import_field_mappings' 
                   AND column_name='client_account_id') THEN
        ALTER TABLE import_field_mappings ADD COLUMN client_account_id UUID;
        
        UPDATE import_field_mappings fm
        SET client_account_id = di.client_account_id
        FROM data_imports di
        WHERE fm.data_import_id = di.id;
        
        ALTER TABLE import_field_mappings
        ALTER COLUMN client_account_id SET NOT NULL;
    END IF;
END $$;

-- Add useful V3 fields
ALTER TABLE import_field_mappings
ADD COLUMN IF NOT EXISTS match_type VARCHAR,
ADD COLUMN IF NOT EXISTS approved_by VARCHAR,
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS transformation_rules JSON,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Migrate field values
UPDATE import_field_mappings
SET match_type = COALESCE(match_type, mapping_type)
WHERE match_type IS NULL;

-- Migrate V3 mappings
INSERT INTO import_field_mappings (
    id, data_import_id, client_account_id,
    source_field, target_field, confidence_score,
    match_type, suggested_by, status,
    approved_by, approved_at, transformation_rules,
    created_at, updated_at, mapping_type
)
SELECT 
    v3.id, v3.data_import_id, v3.client_account_id,
    v3.source_field, v3.target_field, v3.confidence_score,
    v3.match_type, v3.suggested_by, v3.status,
    v3.approved_by, v3.approved_at AT TIME ZONE 'UTC', 
    v3.transformation_rules,
    v3.created_at AT TIME ZONE 'UTC',
    v3.updated_at AT TIME ZONE 'UTC',
    COALESCE(v3.match_type, 'auto')
FROM v3_field_mappings v3
WHERE NOT EXISTS (
    SELECT 1 FROM import_field_mappings fm WHERE fm.id = v3.id
);

-- Drop over-engineered validation fields
ALTER TABLE import_field_mappings
DROP COLUMN IF EXISTS validation_rules,       -- Never used
DROP COLUMN IF EXISTS validation_method,      -- Over-complex
DROP COLUMN IF EXISTS user_feedback,          -- Use status
DROP COLUMN IF EXISTS original_ai_suggestion, -- Redundant
DROP COLUMN IF EXISTS correction_reason,      -- Over-engineered
DROP COLUMN IF EXISTS transformation_logic,   -- Use transformation_rules
DROP COLUMN IF EXISTS sample_values,          -- Never used
DROP COLUMN IF EXISTS validated_by,           -- Use approved_by
DROP COLUMN IF EXISTS validated_at,           -- Use approved_at
DROP COLUMN IF EXISTS mapping_type;           -- Replaced by match_type

-- KEEP master_flow_id if it exists!

-- =====================================================
-- STEP 4: CONSOLIDATE RAW_IMPORT_RECORDS
-- =====================================================

-- Rename columns
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='raw_import_records' AND column_name='row_number') THEN
        ALTER TABLE raw_import_records RENAME COLUMN row_number TO record_index;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='raw_import_records' AND column_name='processed_data') THEN
        ALTER TABLE raw_import_records RENAME COLUMN processed_data TO cleansed_data;
    END IF;
END $$;

-- Migrate V3 records
INSERT INTO raw_import_records (
    id, data_import_id, record_index, raw_data,
    is_processed, is_valid, validation_errors,
    cleansed_data, created_at, processed_at
)
SELECT 
    v3.id, v3.data_import_id, v3.record_index, v3.raw_data,
    v3.is_processed, v3.is_valid, v3.validation_errors,
    v3.cleansed_data, 
    v3.created_at AT TIME ZONE 'UTC',
    v3.processed_at AT TIME ZONE 'UTC'
FROM v3_raw_import_records v3
WHERE NOT EXISTS (
    SELECT 1 FROM raw_import_records rr WHERE rr.id = v3.id
);

-- Drop redundant fields
ALTER TABLE raw_import_records
DROP COLUMN IF EXISTS client_account_id,  -- Get from parent
DROP COLUMN IF EXISTS engagement_id,      -- Get from parent
DROP COLUMN IF EXISTS record_id,          -- Unnecessary
DROP COLUMN IF EXISTS processing_notes,   -- Use validation_errors
DROP COLUMN IF EXISTS asset_id;           -- Wrong level

-- KEEP master_flow_id - it's important!

-- =====================================================
-- STEP 5: CLEAN UP ASSETS TABLE
-- =====================================================

-- Only drop fields that are truly never needed
ALTER TABLE assets
DROP COLUMN IF EXISTS is_mock,              -- Use multi-tenancy
DROP COLUMN IF EXISTS field_mappings_used,  -- Redundant
DROP COLUMN IF EXISTS source_filename,      -- Get from import
DROP COLUMN IF EXISTS raw_data;             -- Too large

-- KEEP ALL OTHER FIELDS - they're mapping targets!
-- Infrastructure fields: hostname, ip_address, etc. - KEEP for mapping
-- Business fields: owners, department - KEEP for mapping
-- Migration fields: six_r_strategy, wave - KEEP for planning
-- Performance fields: utilization metrics - KEEP for analysis
-- Cost fields: monthly costs - KEEP for TCO
-- Flow references: master_flow_id, phase flow IDs - KEEP for orchestration

-- =====================================================
-- STEP 6: DROP V3 TABLES
-- =====================================================

DROP TABLE IF EXISTS v3_field_mappings CASCADE;
DROP TABLE IF EXISTS v3_raw_import_records CASCADE;
DROP TABLE IF EXISTS v3_discovery_flows CASCADE;
DROP TABLE IF EXISTS v3_data_imports CASCADE;

DROP TYPE IF EXISTS flowstatus CASCADE;
DROP TYPE IF EXISTS importstatus CASCADE;
DROP TYPE IF EXISTS mappingstatus CASCADE;

-- =====================================================
-- STEP 7: DELETE TRULY UNUSED TABLES
-- =====================================================

DROP TABLE IF EXISTS workflow_states CASCADE;         -- Deprecated
DROP TABLE IF EXISTS discovery_assets CASCADE;        -- Redundant with assets
DROP TABLE IF EXISTS mapping_learning_patterns CASCADE; -- Failed experiment
DROP TABLE IF EXISTS data_quality_issues CASCADE;     -- Use validation_errors
DROP TABLE IF EXISTS workflow_progress CASCADE;       -- Redundant with flows
DROP TABLE IF EXISTS import_processing_steps CASCADE; -- Over-engineered

-- =====================================================
-- STEP 8: ENSURE PROPER INDEXES
-- =====================================================

-- Multi-tenant indexes
CREATE INDEX IF NOT EXISTS idx_data_imports_client_status 
ON data_imports(client_account_id, status);

CREATE INDEX IF NOT EXISTS idx_discovery_flows_client_status 
ON discovery_flows(client_account_id, status);

CREATE INDEX IF NOT EXISTS idx_field_mappings_client_import
ON import_field_mappings(client_account_id, data_import_id);

CREATE INDEX IF NOT EXISTS idx_assets_client_engagement
ON assets(client_account_id, engagement_id);

-- Orchestration indexes
CREATE INDEX IF NOT EXISTS idx_discovery_flows_master_flow
ON discovery_flows(master_flow_id) WHERE master_flow_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_assets_master_flow
ON assets(master_flow_id) WHERE master_flow_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_data_imports_master_flow
ON data_imports(master_flow_id) WHERE master_flow_id IS NOT NULL;

-- Phase tracking indexes
CREATE INDEX IF NOT EXISTS idx_assets_discovery_flow
ON assets(discovery_flow_id) WHERE discovery_flow_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_assets_current_phase
ON assets(current_phase);

-- =====================================================
-- STEP 9: FINAL VERIFICATION
-- =====================================================

DO $$ 
DECLARE
    v_count INTEGER;
    v_master_flows INTEGER;
    v_asset_columns INTEGER;
BEGIN
    -- Count records
    SELECT COUNT(*) INTO v_count FROM data_imports;
    RAISE NOTICE 'data_imports: % records', v_count;
    
    SELECT COUNT(*) INTO v_count FROM discovery_flows;
    RAISE NOTICE 'discovery_flows: % records', v_count;
    
    SELECT COUNT(*) INTO v_count FROM import_field_mappings;
    RAISE NOTICE 'import_field_mappings: % records', v_count;
    
    -- Check master flow usage
    SELECT COUNT(*) INTO v_master_flows 
    FROM crewai_flow_state_extensions;
    RAISE NOTICE 'Master flows defined: %', v_master_flows;
    
    -- Count asset columns preserved
    SELECT COUNT(*) INTO v_asset_columns
    FROM information_schema.columns
    WHERE table_name = 'assets';
    RAISE NOTICE 'Asset columns preserved: %', v_asset_columns;
    
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ CONSOLIDATION COMPLETE';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ V3 tables consolidated into originals';
    RAISE NOTICE '✅ master_flow_id preserved for orchestration';
    RAISE NOTICE '✅ Asset fields preserved for mapping';
    RAISE NOTICE '✅ 6 truly unused tables deleted';
    RAISE NOTICE '✅ is_mock fields removed (use multi-tenancy)';
    RAISE NOTICE '✅ All data backed up in backup_final_consolidation';
    RAISE NOTICE '========================================';
END $$;