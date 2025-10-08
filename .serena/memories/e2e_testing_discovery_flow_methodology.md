# E2E Testing: Discovery Flow Sequential Phase Requirements

## Critical Rule: Cannot Skip Phases
Discovery flow MUST progress sequentially through phases. Attempting to skip phases results in errors.

## Phase Sequence (MANDATORY Order)

### 1. Data Upload
```bash
# Upload CSV via UI or API
POST /api/v1/data-import/upload
→ Creates: raw_import_records with data_import_id
```

### 2. Start Discovery Flow
```bash
POST /api/v1/master-flows
→ Creates: discovery_flows with master_flow_id AND data_import_id
→ Creates: crewai_flow_state_extensions with flow orchestration state
```

### 3. Field Mapping Generation
```bash
# Auto-generated on flow start
→ Creates: import_field_mappings (status='suggested')
→ Sets: field_mapping_completed=false
```

### 4. Field Mapping Approval
```bash
# User approves mappings via UI
PUT /api/v1/data-import/field-mappings/bulk-approve
→ Updates: import_field_mappings (status='approved')
→ Requires: ≥60% approval (configurable via FIELD_MAPPING_APPROVAL_THRESHOLD)
→ Sets: field_mapping_completed=true
```

### 5. Data Cleansing Phase
```bash
# Executes after field mappings approved
POST /api/v1/unified-discovery/flows/{flow_id}/execute-phase
→ Phase: data_cleansing
→ Sets: data_cleansing_completed=true
→ Updates: current_phase='data_cleansing'
```

### 6. Asset Inventory Phase
```bash
# Can ONLY execute after data_cleansing_completed=true
POST /api/v1/unified-discovery/flows/{flow_id}/execute-phase
→ Phase: asset_inventory
→ Creates: assets in assets table
→ Sets: asset_inventory_completed=true
```

## Common E2E Test Mistakes

### ❌ WRONG: Skipping Phases
```python
# This FAILS - data cleansing not completed
await executor.execute_asset_inventory(phase_input)
# Error: "Auto-execution is waiting for data cleansing to complete"
```

### ✅ CORRECT: Sequential Execution
```python
# 1. Approve field mappings
await approve_mappings(flow_id)

# 2. Execute data cleansing
await execute_phase(flow_id, "data_cleansing")

# 3. Verify cleansing completed
assert flow.data_cleansing_completed == True

# 4. NOW execute asset inventory
await execute_phase(flow_id, "asset_inventory")
```

## Verification Checklist

### After Each Phase
```sql
-- Check phase completion flags
SELECT 
    current_phase,
    field_mapping_completed,
    data_cleansing_completed,
    asset_inventory_completed
FROM migration.discovery_flows
WHERE master_flow_id = 'flow-id';
```

### data_import_id Propagation
```sql
-- Verify data_import_id carried through
SELECT data_import_id 
FROM migration.discovery_flows 
WHERE master_flow_id = 'flow-id';

-- Verify raw records exist
SELECT COUNT(*) 
FROM migration.raw_import_records 
WHERE data_import_id = 'data-import-id';
```

## Field Mapping Approval Threshold

### Configuration
```bash
# Default: 60% (was 80% pre-issue #521)
export FIELD_MAPPING_APPROVAL_THRESHOLD=60
```

### File Location
`backend/app/utils/flow_constants/thresholds.py:21-29`

### Why Lowered
- Issue #521: 80% was too strict
- Flows with 75% approval were blocked
- 60% provides better balance

## Test Data Example
```csv
app_id,application_name,version,criticality,environment
APP001,Customer Portal,2.5.0,High,Production
APP002,Payment Gateway,1.8.2,Critical,Production
```

→ Creates 5 raw_import_records
→ Generates 8 field mappings (7 auto-mapped + 1 needs review)
→ After approval & phases: Creates 5 assets with names from CSV
