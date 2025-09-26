# Bug #430: Discovery Flow Complete Fix - September 2025

## Summary
Fixed critical discovery flow issues where assets were incorrectly classified as "device" type, flow phases weren't advancing properly, and data cleansing wasn't executing.

## Root Causes & Solutions

### 1. Invalid "device" Asset Type Creation
**Root Cause**: Multiple pipeline issues creating invalid asset types
**Solution Applied**:
- `/backend/app/services/flow_orchestration/execution_engine_crew_discovery/data_normalization.py`:
  - Changed device mapping: "device" → "server"
  - Fixed Service → "application", Cache → "database", External → "other"
- `/backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor.py`:
  - Removed "device" from network patterns (line 421)
  - Changed "network_device" → "network", "infrastructure" → "other"

### 2. Data Cleansing Phase Not Populating cleansed_data
**Root Cause**: Missing data_import_id in phase state
**Solution Applied**:
- `/backend/app/services/flow_orchestration/execution_engine_crew_discovery/phase_orchestration.py`:
  - Made `_prepare_phase_input` async
  - Added fallback to retrieve data_import_id from discovery_flows table

### 3. Flow Not Advancing from Field Mapping to Data Cleansing
**Root Cause**: Flow stuck in "paused" status after approval
**Solution Applied**:
- `/backend/app/api/v1/endpoints/flow_processing.py`:
  - Added flow resumption logic for paused flows
  - Updates both discovery_flows AND crewai_flow_state_extensions tables
  - Disabled fast path for discovery flows
  - Fixed data cleansing execution timing

### 4. Import Path Errors
**Solution Applied**:
- `/backend/app/services/crewai_flows/unified_discovery_flow/base_flow/base.py`:
  - Fixed imports: `..handlers` → `...handlers`

### 5. Tool Validation Errors
**Solution Applied**:
- `/backend/app/services/crewai_flows/tools/data_validation/base_tools.py`:
  - Made BaseFieldSuggestionTool accept flexible **kwargs input

## Valid AssetType Enum Values
From `/backend/app/models/asset/enums.py`:
- server, database, application, network, load_balancer
- storage, security_group, virtual_machine, container, other

## Database Verification Queries
```sql
-- Check flow status
SELECT flow_id, current_phase, status, data_import_id
FROM migration.discovery_flows
WHERE flow_id = 'fb362f44-5d2f-4702-90c8-780544cd7b7e';

-- Check cleansed data population
SELECT COUNT(*) as total, COUNT(cleansed_data) as cleansed
FROM migration.raw_import_records
WHERE data_import_id = 'cb9a773b-3ed8-424a-835b-1cabd8f82440';

-- Verify asset types
SELECT cleansed_data->>'asset_type' as type, COUNT(*)
FROM migration.raw_import_records
WHERE data_import_id = 'cb9a773b-3ed8-424a-835b-1cabd8f82440'
GROUP BY cleansed_data->>'asset_type';
```

## Key Learnings
1. **Multi-Table State Management**: Always update both discovery_flows and crewai_flow_state_extensions
2. **Phase Context**: Each executor needs proper context (data_import_id, flow_id)
3. **Asset Type Validation**: Strict validation against AssetType enum prevents invalid types
4. **Data Pipeline**: Asset creation should always use cleansed_data when available
5. **Defensive Programming**: Always provide fallbacks for missing context data

## Files Modified Summary
- data_normalization.py - Fixed asset type mappings
- asset_inventory_executor.py - Removed invalid asset types
- phase_orchestration.py - Added data_import_id retrieval
- flow_processing.py - Flow resumption and phase transitions (NOW MODULARIZED)
- base.py - Import fixes
- base_tools.py - Tool validation flexibility

## Status: COMPLETE
All issues resolved. Assets now created with correct types, flow phases advance properly, and data cleansing executes successfully.
