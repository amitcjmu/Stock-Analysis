# Flow Analysis Summary for 1e640262-4332-4087-ac4e-1674b08cd8f2

## Current Status

Based on the database analysis, here's the complete picture of flow data storage:

### 1. **Tables Where Flow Data is Stored**

#### **discovery_flows** (Child Table - Source of Truth)
- **Status**: `running` (incorrect - should be `waiting_for_approval`)
- **Current Phase**: `attribute_mapping`
- **Progress**: 0.0%
- **Field Mappings**: ✅ Present (stored here)
- **Data Import Completed**: ✅ True
- **Field Mapping Completed**: ❌ False
- **Last Updated**: 2025-07-05 17:41:20

#### **crewai_flow_state_extensions** (Master Table)
- **Flow Status**: `initialization` (incorrect - out of sync)
- **Flow Type**: `discovery`
- **Field Mappings**: ✅ Present (in flow_persistence_data)
- **Last Updated**: 2025-07-05 17:41:19

#### **data_imports**
- ❌ No records found with master_flow_id = flow_id
- This explains why the API couldn't find import data

### 2. **Key Issues Identified**

1. **Status Mismatch**: 
   - Discovery flow shows `running` but should be `waiting_for_approval`
   - Master flow shows `initialization` which is completely wrong

2. **Field Mappings Location**:
   - ✅ Exist in both tables (discovery_flows and master)
   - Frontend checks discovery_flows first (correct location)

3. **Missing Data Import Link**:
   - No data_imports record linked to this flow
   - Raw data likely exists but not properly linked

### 3. **What's Persisted vs Processed**

#### **Persisted**:
- ✅ Flow records in both master and child tables
- ✅ Field mappings (13 mappings found)
- ✅ Phase completion flags
- ❓ Raw data (exists but not linked properly)

#### **Processed**:
- ✅ Data Import phase (marked complete)
- ⏸️ Field Mapping phase (waiting for approval)
- ❌ Subsequent phases not started

### 4. **Resume Capability**

The flow CAN be resumed intelligently:

1. **Immediate Fix**: Update status to `waiting_for_approval`
2. **Field Mapping Approval**: Approve existing mappings or regenerate
3. **Continue Processing**: Resume from data_cleansing phase

### 5. **API Endpoints for Resume**

#### **Standard Resume** (existing):
```
POST /api/v1/discovery/flow/{flow_id}/resume
Body: {
  "field_mappings": {...},
  "approval": true
}
```

#### **Intelligent Resume** (new):
```
POST /api/v1/discovery/flow/{flow_id}/resume-intelligent
Body: {
  "action": "auto",  // or "approve", "regenerate"
  "force_restart": false
}
```

### 6. **Recommended Actions**

1. **Fix Status**: Update discovery_flows.status to `waiting_for_approval`
2. **Sync Master**: Update master flow status to match child
3. **Link Data**: Find and link the data_import record
4. **Resume Flow**: Use intelligent resume endpoint to continue

The intelligent resume endpoint will:
- Detect current state
- Find available raw data
- Resume from appropriate point
- Handle approval workflows

## Summary

The flow is stuck because:
1. Status is incorrectly set to `running` instead of `waiting_for_approval`
2. Field mappings exist but flow is waiting for approval
3. Data import records are not properly linked

All data needed to resume exists - just needs proper status updates and linking.