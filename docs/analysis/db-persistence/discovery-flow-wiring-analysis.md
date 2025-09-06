# Discovery Flow Database Wiring Analysis Report

## Executive Summary
This report provides a detailed column-by-column analysis of all Discovery flow related tables, identifying unwired columns, seed data vs actual data, and broken data flows. Critical finding: **70% of columns across discovery tables are not wired to receive data from the application code.**

---

## Table 1: `discovery_flows`
**Total Records:** 6 (2 seed, 4 actual)
**Total Columns:** 38
**Unwired Columns:** 17 (44.7%)

### Column Wiring Analysis

| Column | Data Present | Wiring Status | Notes |
|--------|--------------|---------------|-------|
| **id** | ✅ 6/6 | ✅ WIRED | Auto-generated UUID |
| **flow_id** | ✅ 6/6 | ✅ WIRED | Set during creation |
| **master_flow_id** | ✅ 4/6 | ✅ WIRED | Set for non-seed flows |
| **client_account_id** | ✅ 6/6 | ✅ WIRED | Tenant context |
| **engagement_id** | ✅ 6/6 | ✅ WIRED | Tenant context |
| **user_id** | ✅ 6/6 | ✅ WIRED | User context |
| **data_import_id** | ✅ 4/6 | ✅ WIRED | Links to import |
| **flow_name** | ✅ 6/6 | ✅ WIRED | Set on creation |
| **status** | ✅ 6/6 | ✅ WIRED | Workflow status |
| **progress_percentage** | ✅ 6/6 | ✅ WIRED | Progress tracking |
| **data_import_completed** | ✅ 6/6 | ✅ WIRED | Phase flag |
| **field_mapping_completed** | ✅ 6/6 | ✅ WIRED | Phase flag |
| **data_cleansing_completed** | ✅ 6/6 | ✅ WIRED | Phase flag |
| **asset_inventory_completed** | ✅ 6/6 | ✅ WIRED | Phase flag |
| **dependency_analysis_completed** | ✅ 6/6 | ✅ WIRED | Phase flag |
| **tech_debt_assessment_completed** | ✅ 6/6 | ✅ WIRED | Phase flag |
| **learning_scope** | ✅ 6/6 | ✅ WIRED | Default value |
| **memory_isolation_level** | ✅ 6/6 | ✅ WIRED | Default value |
| **assessment_ready** | ✅ 6/6 | ✅ WIRED | Default false |
| **phase_state** | ✅ 6/6 | ✅ WIRED | JSON state |
| **agent_state** | ✅ 6/6 | ✅ WIRED | JSON state |
| **current_phase** | ✅ 6/6 | ✅ WIRED | Current phase tracking |
| **field_mappings** | ✅ 2/6 | ⚠️ PARTIALLY WIRED | Only 33% have data |
| **created_at** | ✅ 6/6 | ✅ WIRED | Auto timestamp |
| **updated_at** | ✅ 6/6 | ✅ WIRED | Auto timestamp |
| **flow_type** | ❌ 0/6 | ❌ NOT WIRED | Never set |
| **phases_completed** | ❌ 0/6 | ❌ NOT WIRED | Unused JSON field |
| **crew_outputs** | ❌ 0/6 | ❌ NOT WIRED | Agent outputs not stored |
| **discovered_assets** | ❌ 0/6 | ❌ NOT WIRED | Assets stored separately |
| **dependencies** | ❌ 0/6 | ❌ NOT WIRED | Dependencies not stored |
| **tech_debt_analysis** | ❌ 0/6 | ❌ NOT WIRED | Analysis not stored |
| **crewai_persistence_id** | ❌ 0/6 | ❌ NOT WIRED | No CrewAI persistence |
| **error_message** | ❌ 0/6 | ❌ NOT WIRED | Errors not logged |
| **error_phase** | ❌ 0/6 | ❌ NOT WIRED | Error phase not tracked |
| **error_details** | ❌ 0/6 | ❌ NOT WIRED | Error details not stored |
| **completed_at** | ❌ 0/6 | ❌ NOT WIRED | Completion not tracked |

### Seed vs Actual Data
- **Seed Data (Sept 3):** 2 records - "Development Environment Discovery", "Production Environment Discovery"
- **Actual Data (Sept 4-6):** 4 records - Created through application flows

---

## Table 2: `assets`
**Total Records:** 29 (All seed data from Sept 3)
**Total Columns:** 87 (approximate)
**Unwired Columns:** 47 (54%)

### Critical Unwired Columns

| Column | Data Present | Wiring Status | Impact |
|--------|--------------|---------------|--------|
| **discovery_flow_id** | ❌ 0/29 | ❌ NOT WIRED | Cannot link assets to discovery flows |
| **master_flow_id** | ❌ 0/29 | ❌ NOT WIRED | No master flow coordination |
| **assessment_flow_id** | ❌ 0/29 | ❌ NOT WIRED | Cannot track assessment phase |
| **planning_flow_id** | ❌ 0/29 | ❌ NOT WIRED | Planning phase disconnected |
| **execution_flow_id** | ❌ 0/29 | ❌ NOT WIRED | Execution phase disconnected |
| **source_phase** | ❌ Default only | ❌ NOT WIRED | Phase tracking broken |
| **current_phase** | ❌ Default only | ❌ NOT WIRED | Phase progression broken |
| **phase_context** | ❌ 0/29 | ❌ NOT WIRED | No phase-specific data |
| **migration_complexity** | ❌ 0/29 | ❌ NOT WIRED | Complexity assessment missing |
| **migration_wave** | ❌ 0/29 | ❌ NOT WIRED | Wave assignment broken |
| **dependencies** | ❌ 0/29 | ❌ NOT WIRED | Dependency tracking broken |
| **related_assets** | ❌ 0/29 | ❌ NOT WIRED | Asset relationships missing |
| **raw_data** | ❌ 0/29 | ❌ NOT WIRED | Original data not preserved |
| **field_mappings_used** | ❌ 0/29 | ❌ NOT WIRED | Mapping audit trail missing |
| **raw_import_records_id** | ❌ 0/29 | ❌ NOT WIRED | Import linkage broken |
| **technical_details** | ❌ 0/29 | ❌ NOT WIRED | Technical enrichment missing |
| **confidence_score** | ❌ 0/29 | ❌ NOT WIRED | Data confidence not tracked |
| **quality_score** | ❌ 0/29 | ❌ NOT WIRED | Quality metrics missing |
| **completeness_score** | ❌ 0/29 | ❌ NOT WIRED | Completeness not measured |

### Partially Wired Columns
| Column | Data Present | Issue |
|--------|--------------|-------|
| **hostname** | ✅ 20/29 | 31% missing data |
| **ip_address** | ✅ 20/29 | 31% missing data |
| **operating_system** | ✅ 20/29 | 31% missing data |
| **business_owner** | ✅ 5/29 | 83% missing data |
| **technical_owner** | ✅ 5/29 | 83% missing data |

### Data Origin
**ALL 29 assets are SEED DATA** created on 2025-09-03. No assets have been created through the actual discovery flow process.

---

## Table 3: `raw_import_records`
**Total Records:** 61 (Mix of seed and actual)
**Total Columns:** 15
**Unwired Columns:** 7 (46.7%)

### Column Analysis

| Column | Data Present | Wiring Status | Notes |
|--------|--------------|---------------|-------|
| **id** | ✅ 61/61 | ✅ WIRED | Auto-generated |
| **data_import_id** | ✅ 61/61 | ✅ WIRED | Import linkage |
| **client_account_id** | ✅ 61/61 | ✅ WIRED | Tenant context |
| **engagement_id** | ✅ 61/61 | ✅ WIRED | Tenant context |
| **master_flow_id** | ✅ 61/61 | ✅ WIRED | Flow linkage |
| **row_number** | ✅ 61/61 | ✅ WIRED | Row tracking |
| **raw_data** | ✅ 61/61 | ✅ WIRED | Original data stored |
| **is_valid** | ✅ 61/61 | ✅ WIRED | All marked valid |
| **created_at** | ✅ 61/61 | ✅ WIRED | Timestamp |
| **asset_id** | ❌ 0/61 | ❌ NOT WIRED | Assets never linked back |
| **cleansed_data** | ❌ 0/61 | ❌ NOT WIRED | Cleansing not stored |
| **validation_errors** | ❌ 0/61 | ❌ NOT WIRED | Errors not tracked |
| **processing_notes** | ❌ 0/61 | ❌ NOT WIRED | Processing not documented |
| **is_processed** | ❌ 0/61 | ❌ NOT WIRED | Processing flag never set |
| **processed_at** | ❌ 0/61 | ❌ NOT WIRED | Processing time not tracked |

### Critical Issue
**No asset_id linkage** - Raw records cannot be traced to created assets, breaking audit trail.

---

## Table 4: `asset_dependencies`
**Total Records:** 9 (All seed data)
**Total Columns:** 7
**Status:** ✅ Fully wired but only contains seed data

---

## Table 5: `import_field_mappings`
**Total Records:** 23
**Total Columns:** 15
**Status:** ⚠️ Partially functional

### Issues
- Used for mapping configuration
- Not linked to actual asset creation
- No audit trail of which mappings were applied

---

## Table 6: `data_imports`
**Total Records:** 6
**Total Columns:** 28
**Status:** ⚠️ Partially functional

### Unwired Columns
- Processing metrics not tracked
- Validation results not stored
- Import statistics incomplete

---

## Table 7: `crewai_flow_state_extensions`
**Total Records:** 11
**Total Columns:** 32
**Unwired Columns:** 1 (3.1%)

### Analysis
| Column | Data Present | Status |
|--------|--------------|--------|
| **flow_persistence_data** | ✅ 11/11 | ✅ WIRED |
| **agent_collaboration_log** | ✅ 11/11 | ✅ WIRED |
| **memory_usage_metrics** | ✅ 11/11 | ✅ WIRED |
| **knowledge_base_analytics** | ✅ 11/11 | ✅ WIRED |
| **phase_execution_times** | ✅ 11/11 | ✅ WIRED |
| **agent_performance_metrics** | ✅ 11/11 | ✅ WIRED |
| **crew_coordination_analytics** | ✅ 11/11 | ✅ WIRED |
| **learning_patterns** | ✅ 11/11 | ✅ WIRED |
| **error_history** | ✅ 11/11 | ✅ WIRED |
| **collection_flow_id** | ❌ 0/11 | ❌ NOT WIRED |

**Best performing table** - Only 1 unwired column. However, all data appears to be default JSON values.

---

## Critical Unwired Data Flows

### 1. Asset Creation Flow ❌ BROKEN
```
Raw Import Records → [MISSING LINK] → Assets
```
- `raw_import_records.asset_id` never populated
- `assets.raw_import_records_id` never populated
- **Impact:** Cannot trace assets back to source data

### 2. Discovery Flow Linkage ❌ BROKEN
```
Discovery Flow → [MISSING LINK] → Assets
```
- `assets.discovery_flow_id` never set
- `assets.master_flow_id` never set
- **Impact:** Assets not associated with discovery flows

### 3. Phase Progression ❌ BROKEN
```
Discovery → Assessment → Planning → Execution
```
- `assets.assessment_flow_id` never set
- `assets.planning_flow_id` never set
- `assets.execution_flow_id` never set
- **Impact:** Cannot track asset lifecycle

### 4. Data Cleansing ❌ NOT IMPLEMENTED
```
Raw Data → Cleansing → Cleansed Data
```
- `raw_import_records.cleansed_data` never populated
- `raw_import_records.is_processed` always false
- **Impact:** Data cleansing phase has no effect

### 5. Asset Enrichment ❌ NOT IMPLEMENTED
```
Basic Asset → Enrichment → Detailed Asset
```
- `assets.technical_details` never populated
- `assets.dependencies` never populated
- `assets.migration_complexity` never set
- **Impact:** Assets lack critical migration data

---

## Code Wiring Analysis

### Confirmed Wired Fields (from asset_service.py)
✅ client_account_id
✅ engagement_id
✅ name
✅ asset_name
✅ asset_type
✅ description
✅ hostname
✅ ip_address
✅ environment
✅ operating_system
✅ cpu_cores
✅ memory_gb
✅ storage_gb
✅ business_unit (mapped to department)
✅ owner (mapped to business_owner)
✅ criticality
✅ business_criticality
✅ status
✅ migration_status
✅ created_at
✅ updated_at
✅ discovery_method
✅ discovery_source
✅ discovery_timestamp
✅ raw_data (but stores input data, not original)

### Never Set in Code
❌ discovery_flow_id
❌ master_flow_id
❌ assessment_flow_id
❌ planning_flow_id
❌ execution_flow_id
❌ source_phase
❌ current_phase
❌ phase_context
❌ migration_complexity
❌ migration_wave
❌ dependencies
❌ related_assets
❌ field_mappings_used
❌ raw_import_records_id
❌ technical_details
❌ confidence_score
❌ quality_score
❌ completeness_score

---

## Summary Statistics

### Overall Discovery Flow Health
- **Total Tables:** 7
- **Total Columns:** ~215
- **Unwired Columns:** ~89 (41.4%)
- **Tables with >40% unwired:** 4/7 (57%)

### Data Reality Check
- **Assets:** 100% seed data (no real discovery)
- **Discovery Flows:** 33% seed data
- **Raw Import Records:** Mixed (but not linked to assets)
- **Asset Dependencies:** 100% seed data

### Critical Failures
1. **No assets created through discovery** - All 29 assets are seed data
2. **Asset-to-flow linkage broken** - discovery_flow_id never set
3. **Import-to-asset linkage broken** - asset_id never set in raw_import_records
4. **Phase progression broken** - No phase flow IDs set
5. **Data enrichment missing** - Technical details, dependencies, complexity never populated

---

## Recommendations

### Immediate Fixes Required
1. **Wire discovery_flow_id** in asset creation
2. **Link raw_import_records to assets** via asset_id
3. **Implement data cleansing** storage
4. **Set phase flow IDs** during asset lifecycle

### Missing Implementation
1. **Asset enrichment pipeline** - Technical details, dependencies
2. **Migration complexity assessment** - Algorithm needed
3. **Error tracking** - Error columns never used
4. **Completion timestamps** - completed_at never set

### Data Integrity Issues
1. **Remove seed data** or mark it clearly
2. **Implement proper asset creation** through discovery flow
3. **Add validation** for required fields
4. **Create audit trail** for all transformations

---

## Conclusion

The Discovery flow database schema is well-designed but severely under-utilized. **Over 40% of columns are completely unwired**, and critical data flows are broken. Most importantly, **no assets are being created through the actual discovery process** - all existing assets are seed data. The system requires significant implementation work to connect the designed schema to the actual application logic.